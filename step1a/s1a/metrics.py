"""v2 scoring: lenient multi-label B-cubed, span matching to all verbatim mentions, span recall,
and a per-block report (visible / hidden attributes per TEAR level, per class, confusions).

Lenient B-cubed (label sets L): precision_i = mean over j in i's cluster of [L_i & L_j];
recall_i = mean over j with L_i & L_j of [same cluster]. Single labels give the usual B-cubed.
The old protocol is `single` (= hbe.metrics.external on one label per unit).
"""

from collections import Counter, defaultdict

import numpy as np

from . import paths  # noqa: F401
from hbe.metrics import external

LEVELS = (1, 2, 3)


def single(true, pred):
    """Old protocol: single-label external metrics."""
    return external(true, pred)


def _sets(true_sets):
    out = [frozenset([x]) if isinstance(x, str) else frozenset(x) for x in true_sets]
    if any(not s for s in out):
        raise ValueError("empty label set")
    return out


def bcubed_items(true_sets, pred):
    """Per-item lenient precision and recall arrays."""
    sets = _sets(true_sets)
    if not sets:
        return np.zeros(0), np.zeros(0)
    uniq = sorted(set(sets), key=lambda s: sorted(s))
    pos = {s: i for i, s in enumerate(uniq)}
    sid = np.array([pos[s] for s in sets])
    labs = sorted(set().union(*uniq))
    lid = {x: i for i, x in enumerate(labs)}
    m = np.zeros((len(uniq), len(labs)))
    for i, s in enumerate(uniq):
        m[i, [lid[x] for x in s]] = 1
    share = (m @ m.T > 0).astype(float)              # set x set
    _, cid = np.unique([str(p) for p in pred], return_inverse=True)
    counts = np.zeros((cid.max() + 1, len(uniq)))    # cluster x set
    np.add.at(counts, (cid, sid), 1)
    num = (counts @ share.T)[cid, sid]               # members of i's cluster sharing a label
    size = counts.sum(1)[cid]
    den = (share @ np.bincount(sid, minlength=len(uniq)))[sid]
    return num / size, num / den


def _prf(p, r):
    p, r = float(np.mean(p)) if len(p) else 0.0, float(np.mean(r)) if len(r) else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def bcubed_multi(true_sets, pred):
    return _prf(*bcubed_items(true_sets, pred))


def _overlap(a, b):
    return min(a.end, b.end) - max(a.start, b.start) > 0


def _by_doc(mentions):
    out = defaultdict(list)
    for i, m in enumerate(mentions):
        if m.verbatim:
            out[m.doc_id].append(i)
    return out


def match_all(spans, mentions):
    """Each span gets the union of labels of all verbatim mentions it overlaps."""
    by_doc, used = _by_doc(mentions), set()
    for u in spans:
        hit = [i for i in by_doc.get(u.doc_id, ()) if _overlap(u, mentions[i])]
        u.matched = hit
        u.labels = frozenset().union(*(mentions[i].labels for i in hit))
        u.raw_labels = frozenset().union(*(mentions[i].raw_labels for i in hit))
        u.label = "|".join(sorted(u.labels))
        ks = set().union(*(mentions[i].hidden for i in hit)) if hit else set()
        u.hidden = {k: any(mentions[i].hidden.get(k, False) for i in hit) for k in ks}
        used.update(hit)
    return used


def _rec(flags):
    return float(np.mean(flags)) if flags else 0.0


TIGHT_EXTRA = 4  # chars a span may exceed its mention by and still count as a tight match


def span_recall(spans, mentions, levels=LEVELS):
    """Recall of verbatim mentions (covered if a span overlaps) and of gold values
    (doc_id, value, labels): covered if one of its mentions is. "tight" counts only spans at
    most TIGHT_EXTRA chars longer than the mention, so long noun chunks get no credit."""
    sp = defaultdict(list)
    for u in spans:
        sp[u.doc_id].append(u)
    cov = {i: any(_overlap(u, m) for u in sp[m.doc_id]) for i, m in enumerate(mentions) if m.verbatim}
    tight = {i: any(_overlap(u, mentions[i]) and u.end - u.start <= mentions[i].end - mentions[i].start + TIGHT_EXTRA
                    for u in sp[mentions[i].doc_id]) for i in cov}
    groups = defaultdict(list)
    for i in cov:
        m = mentions[i]
        groups[(m.doc_id, m.value, m.labels)].append(i)
    vcov = {g: any(cov[i] for i in ix) for g, ix in groups.items()}

    def block(keep):
        mi = [i for i in cov if keep(mentions[i])]
        gs = [g for g, ix in groups.items() if keep(mentions[ix[0]])]
        return {"mention": _rec([cov[i] for i in mi]), "value": _rec([vcov[g] for g in gs]),
                "tight_mention": _rec([tight[i] for i in mi]),
                "n_mentions": len(mi), "n_values": len(gs)}

    allv = {(m.doc_id, m.value, m.labels) for m in mentions}
    nonv = {(m.doc_id, m.value, m.labels) for m in mentions if not m.verbatim}
    out = block(lambda m: True)
    out |= {"n_gold_values": len(allv), "n_verbatim_values": len(groups),
            "n_nonverbatim_values": len(nonv)}
    out["per_dialogue"] = {d: block(lambda m, d=d: m.doc_id == d)
                           for d in sorted({mentions[i].doc_id for i in cov})}
    out["per_class"] = {c: block(lambda m, c=c: c in m.labels)
                        for c in sorted(set().union(*(mentions[i].labels for i in cov)) if cov else [])}
    for k in levels:
        out[f"visible_L{k}"] = block(lambda m, k=k: not m.hidden.get(k, False))
        out[f"hidden_L{k}"] = block(lambda m, k=k: m.hidden.get(k, False))
    return out


def _hid(u, k):
    return bool(getattr(u, "hidden", {}).get(k, False))


def report_block(units, pred, levels=LEVELS, examples=10):
    """Lenient B-cubed on the labelled units; clusters come from all units. Visible/hidden
    subsets average the full-set per-item scores, so they are comparable with "all"."""
    pred = [str(p) for p in pred]
    lab = [i for i, u in enumerate(units) if u.labels]
    sets = [units[i].labels for i in lab]
    pl = [pred[i] for i in lab]
    prec, rec = bcubed_items(sets, pl)
    out = {"n": len(lab), "n_units": len(units), "K": len(set(pred))}
    out["all"] = dict(zip("prf", _prf(prec, rec)), n=len(lab))
    for k in levels:
        for name, want in ((f"visible_L{k}", False), (f"hidden_L{k}", True)):
            ix = [j for j, i in enumerate(lab) if _hid(units[i], k) == want]
            # per-item scores from the full clustering, averaged over the subset
            out[name] = dict(zip("prf", _prf(prec[ix], rec[ix])), n=len(ix))
    per = defaultdict(list)
    for s, r in zip(sets, rec):
        for c in s:
            per[c].append(r)
    out["per_class"] = {c: {"recall": float(np.mean(v)), "n": len(v)} for c, v in sorted(per.items())}
    members = defaultdict(list)
    for i, p in enumerate(pred):
        members[p].append(i)
    major = {}
    for p, ix in members.items():
        cnt = Counter(c for i in ix for c in units[i].labels)
        if cnt:
            major[p] = cnt.most_common(1)[0][0]
    conf = Counter()
    for i in lab:
        m = major[pred[i]]
        if m not in units[i].labels:
            conf[("|".join(sorted(units[i].labels)), m)] += 1
    out["confused"] = conf.most_common(10)
    ng = [(p, ix) for p, ix in members.items()
          if sum(not units[i].labels for i in ix) > len(ix) / 2]
    ng.sort(key=lambda x: -len(x[1]))
    out["nongold_clusters"] = [
        {"cluster": p, "size": len(ix), "n_unlabelled": sum(not units[i].labels for i in ix),
         "texts": [units[i].text.replace("\n", " ")[:80] for i in ix[:15]]} for p, ix in ng[:examples]]
    return out


def bootstrap_ci(units, pred, n_boot=1000, seed=0):
    """95% CI of lenient F1 over dialogues: per-item P/R are computed once on the full set,
    then dialogues are resampled (re-scoring a resample would count copied dialogues as
    agreeing with each other and inflate B-cubed)."""
    rng = np.random.RandomState(seed)
    ix = [i for i, u in enumerate(units) if u.labels]
    if not ix:
        return 0.0, 0.0
    p, r = bcubed_items([units[i].labels for i in ix], [str(pred[i]) for i in ix])
    by_doc = defaultdict(list)
    for k, i in enumerate(ix):
        by_doc[units[i].doc_id].append(k)
    docs = sorted(by_doc)
    f = []
    for _ in range(n_boot):
        sel = [k for d in rng.choice(docs, len(docs)) for k in by_doc[d]]
        f.append(_prf(p[sel], r[sel])[2])
    return float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))


def ent2_scores(units, groups_by_seed):
    """Mean over seeds of lenient B-cubed (P, R, F1) of units (.labels = entity-label sets) vs groups."""
    res = [bcubed_multi([u.labels for u in units], g) for g in groups_by_seed.values()]
    return tuple(float(np.mean([r[i] for r in res])) for i in range(3))


def ent2_ci(units, groups_by_seed, n_boot=1000, seed=0):
    """95% range of lenient F1 over all seeds: per-item P/R are averaged over the seeds, then
    dialogues are resampled, so the range matches the mean-over-seeds point."""
    sets = [u.labels for u in units]
    pr = [bcubed_items(sets, [str(x) for x in g]) for g in groups_by_seed.values()]
    p, r = np.mean([x[0] for x in pr], 0), np.mean([x[1] for x in pr], 0)
    by_doc = defaultdict(list)
    for i, u in enumerate(units):
        by_doc[u.doc_id].append(i)
    docs, rng, f = sorted(by_doc), np.random.RandomState(seed), []
    for _ in range(n_boot):
        sel = [i for d in rng.choice(docs, len(docs)) for i in by_doc[d]]
        f.append(_prf(p[sel], r[sel])[2])
    return float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))


def boundary_ci(docs, spans_by_doc, n_boot=1000, seed=0):
    """95% range of pooled exact (+-0) boundary F1: bootstrap over dialogues, re-pooling the
    per-dialogue tp / hyp / ref counts."""
    from chk.metrics import boundary_counts, cuts_to_gaps, prf
    c = np.array([boundary_counts(d.gold_gaps, cuts_to_gaps(d, spans_by_doc[i])[0], 0)
                  for i, d in docs.items()], float)
    rng = np.random.RandomState(seed)
    f = []
    for _ in range(n_boot):
        tp, hyp, ref = c[rng.randint(0, len(c), len(c))].sum(0)
        f.append(prf(tp, hyp, ref)[2])
    return float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))


def _f(x):
    return f"{x:.3f}"


def format_block(d, title):
    L = [f"### {title}", "",
         f"{d['n']} labelled of {d['n_units']} units, K = {d['K']}.", "",
         "| Subset | n | P | R | F1 |", "|---|---|---|---|---|"]
    for name in ["all"] + [k for k in d if k.startswith(("visible_L", "hidden_L"))]:
        b = d[name]
        L.append(f"| {name} | {b['n']} | {_f(b['p'])} | {_f(b['r'])} | {_f(b['f'])} |")
    L += ["", "Per-class recall: " + "; ".join(f"{c} {v['recall']:.2f} ({v['n']})"
                                              for c, v in d["per_class"].items()), ""]
    if d["confused"]:
        L += ["Most confused (gold -> cluster majority): "
              + "; ".join(f"{g} -> {m} {n}" for (g, m), n in d["confused"]), ""]
    if d["nongold_clusters"]:
        L += ["Largest mostly non-gold clusters:", ""]
        for c in d["nongold_clusters"]:
            L.append(f"- size {c['size']} ({c['n_unlabelled']} non-gold): "
                     + ", ".join(f'"{t}"' for t in c["texts"]))
        L.append("")
    return "\n".join(L)
