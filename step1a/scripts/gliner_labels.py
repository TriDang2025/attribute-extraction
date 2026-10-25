"""Track C: does the label set limit GLiNER? Three label sets (generic / hand / gold slot names),
one GLiNER pass per turn, scored with the v2 protocol and in the two-stage clustering.

python scripts/gliner_labels.py --limit 50 --out results/v3_n50 [--sets generic,hand,gold]
    [--extract-only] [--seg 25/100,0.45,on,on] [--step2 results/v2_n50/chosen_step2_joint.json]
  -> <out>/gliner_labels/gliner_turn_<set>.{jsonl,meta.json} (threshold 0.3 stored; 0.5 is a filter),
     <out>/gliner_labels.{md,csv}, gliner_labels_examples.md
Set "gold" uses the gold schema's slot names as labels, so its partitioned row is near-oracle.
"""

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from relabel import entity_groups, stage2  # noqa: E402
from run import build_units, encoder  # noqa: E402
from s1a import gold, paths  # noqa: E402
from s1a import metrics as M  # noqa: E402
from s1a import spans as SP  # noqa: E402
from s1a import step2 as S2  # noqa: E402
from s1a import units as U  # noqa: E402
import plug_in as PI  # noqa: E402
import spans_compare as SC  # noqa: E402

THRESHOLDS = (0.3, 0.5)
LEVELS = (1, 2, 3)
STAGE2_T = 0.4
BASE = ("generic", 0.5)


# ------------------------------------------------------------------ cache
def read_cache(path):
    have = {}
    if Path(path).exists():
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            have[r["doc_id"]] = r["spans"]
    return have


def append_cache(path, doc_id, spans):
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"doc_id": doc_id, "spans": spans}) + "\n")


def extract_set(model, docs, name, cache_dir):
    """Run (or resume) one label set over the docs; returns {doc_id: spans} and the metadata."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path, mpath = cache_dir / f"gliner_turn_{name}.jsonl", cache_dir / f"gliner_turn_{name}.meta.json"
    labels = SP.LABEL_SETS[name]
    have = read_cache(path)
    meta = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    if "max_words" not in meta:
        mw, bad, n = SP.fit_max_words(model, list(docs.values()), labels)
        meta |= dict(labels=labels, threshold=SP.THRESHOLD, max_words=mw, seconds=0.0,
                     overflow_at_default=bad, default_max_words=SP.MAX_WORDS, windows_checked=n)
    t0 = time.time()
    for did, doc in docs.items():
        if did not in have:
            us = SP.extract_windows(model, doc, SP.turn_windows(doc, meta["max_words"]), labels, SP.THRESHOLD)
            have[did] = [[u.start, u.end, u.tag, u.score] for u in us]
            append_cache(path, did, have[did])
    meta["seconds"] += time.time() - t0
    meta["n_docs"] = len(have)
    mpath.write_text(json.dumps(meta, indent=1), encoding="utf-8", newline="\n")
    print(f"{name}: {len(labels)} labels, max_words {meta['max_words']} (overflow at "
          f"{meta['default_max_words']}: {meta['overflow_at_default']}/{meta['windows_checked']}), "
          f"{time.time() - t0:.0f}s this run", flush=True)
    return have, meta


def to_units(have, docs, thr):
    out = []
    for did, doc in docs.items():
        for s, e, tag, score in have.get(did, []):
            if score >= thr:
                u = U.Unit("span", did, "", doc.text[s:e], s, e, U.turn_of(doc, s))
                u.tag, u.score = tag, float(score)
                out.append(u)
    return out


# ------------------------------------------------------------------ scoring
def boot_recall(sr, key, n_key, n_boot=1000, seed=0):
    """95% range of a recall over dialogue resamples (hits rebuilt from per-dialogue rates)."""
    pd_ = sr["per_dialogue"]
    ds = sorted(pd_)
    n = np.array([pd_[d][n_key] for d in ds], float)
    h = np.array([pd_[d][key] * pd_[d][n_key] for d in ds])
    rng = np.random.RandomState(seed)
    r = []
    for _ in range(n_boot):
        ix = rng.randint(0, len(ds), len(ds))
        r.append(h[ix].sum() / max(1, n[ix].sum()))
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def score_spans(spans, mentions, vkeys, n_docs):
    """Match and score one span set. Returns stats and the covered value keys."""
    matched = M.match_all(spans, mentions)
    sr = M.span_recall(spans, mentions)
    st = dict(spans_per_dlg=len(spans) / n_docs,
              span_precision=sum(bool(u.labels) for u in spans) / max(1, len(spans)),
              tight=sr["tight_mention"], mention=sr["mention"], value=sr["value"],
              tight_ci=boot_recall(sr, "tight_mention", "n_mentions"),
              value_ci=boot_recall(sr, "value", "n_values"),
              per_class={c: (b["n_values"], b["value"]) for c, b in sr["per_class"].items()})
    for k in LEVELS:
        for h in ("visible", "hidden"):
            b = sr[f"{h}_L{k}"]
            st[f"{h}_L{k}"] = b["value"] if b["n_values"] else float("nan")
    hit = {k for k, ix in vkeys.items() if any(i in matched for i in ix)}
    return st, hit


def cluster_span_set(spans, docs, segs, enc, cfg):
    """Two-stage clustering variants (mean over 3 seeds): original stage 2, chosen Step 2, and the
    LEAKY chosen Step 2 partitioned by GLiNER label inside each entity group."""
    xs = enc.encode([u.text for u in spans])
    piece = PI.piece_of(spans, segs)
    books = [(u.doc_id, p) for u, p in zip(spans, piece)]
    acc = defaultdict(list)
    for g in entity_groups(spans, segs, enc).values():
        leaky = [f"{x}|{u.tag}" for x, u in zip(g, spans)]
        for name, lab in (("original", stage2(xs, g, STAGE2_T)),
                          ("chosen", S2.run_best(spans, docs, g, books, enc, cfg)),
                          ("LEAKY: partition by GLiNER label",
                           S2.run_best(spans, docs, leaky, books, enc, cfg))):
            acc[name].append((M.report_block(spans, lab, levels=())["all"], len({str(x) for x in lab}), lab))
    out = {}
    for name, v in acc.items():
        out[name] = dict(P=np.mean([a["p"] for a, _, _ in v]), R=np.mean([a["r"] for a, _, _ in v]),
                         F1=np.mean([a["f"] for a, _, _ in v]), K=np.mean([k for _, k, _ in v]),
                         f1_ci=M.bootstrap_ci(spans, v[0][2]))
    return out


def group_hits(vkeys, mentions, hit, keys):
    """{group: (n keys, share hit)} for 'all classes' and each SC.GROUPS group."""
    out = {"all classes": (len(keys), sum(k in hit for k in keys) / max(1, len(keys)))}
    for g in SC.GROUPS:
        ks = [k for k in keys if g in SC.groups_of(mentions[vkeys[k][0]].labels)]
        out[g] = (len(ks), sum(k in hit for k in ks) / max(1, len(ks)))
    return out


# ------------------------------------------------------------------ verdict
def disjoint(a, b):
    return a[1] < b[0] or b[1] < a[0]


def verdict(res, thr):
    """Fixed rule at threshold thr; res[(set, thr)] holds stats and the chosen clustering."""
    g = res[("generic", thr)]
    lines, labels_bn, gliner_bn = [], False, False
    for s in ("hand", "gold"):
        if (s, thr) not in res:
            continue
        r = res[(s, thr)]
        dt = r["tight"] - g["tight"]
        dis_t, dis_e = disjoint(r["tight_ci"], g["tight_ci"]), disjoint(r["e2e_ci"], g["e2e_ci"])
        labels_bn |= (dt >= 0.10 and dis_t) or (r["e2e"] - g["e2e"] >= 0.05 and dis_e)
        lines.append(f"- {s} vs generic: tight recall {g['tight']:.3f} -> {r['tight']:.3f} ({dt:+.3f}, ranges "
                     f"{'disjoint' if dis_t else 'overlap'}); end to end {g['e2e']:.3f} -> {r['e2e']:.3f} "
                     f"({r['e2e'] - g['e2e']:+.3f}, ranges {'disjoint' if dis_e else 'overlap'}).")
    if ("gold", thr) in res:
        gliner_bn = res[("gold", thr)]["tight"] - g["tight"] < 0.03
    if labels_bn:
        return "labels are the bottleneck", lines
    return ("GLiNER is the bottleneck" if gliner_bn else "unclear"), lines


# ------------------------------------------------------------------ main
def fmt(x, d=3):
    return "-" if x != x else f"{x:.{d}f}"


def rng_(r):
    return f"{r[0]:.3f}-{r[1]:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", default="results/v3_n50")
    ap.add_argument("--sets", default="generic,hand,gold")
    ap.add_argument("--extract-only", action="store_true")
    ap.add_argument("--seg", default=PI.DEFAULT_SEG)
    ap.add_argument("--step2", default="results/v2_n50/chosen_step2_joint.json")
    args = ap.parse_args()
    out = paths.ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    sets = args.sets.split(",")
    t0 = time.time()
    docs, _, _ = build_units(args.limit)
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    docs = {d: v for d, v in docs.items() if d in tables}
    model = SP.load()
    have, metas = {}, {}
    for s in sets:
        have[s], metas[s] = extract_set(model, docs, s, out / "gliner_labels")
    if args.extract_only:
        return print(f"extraction done in {time.time() - t0:.0f}s")
    cfg = json.load(open(paths.ROOT / args.step2, encoding="utf-8"))
    mentions = gold.mentions_for(docs, tables)
    vkeys = SC.value_keys(mentions)
    enc = encoder()
    size, tau, snap, kw = PI.parse_seg(args.seg)
    segs = PI.segments(docs, enc, size, tau, snap, kw)
    res, hits, spanset = {}, {}, {}
    for s in sets:
        for thr in THRESHOLDS:
            spans = to_units(have[s], docs, thr)
            st, hit = score_spans(spans, mentions, vkeys, len(docs))
            st["cluster"] = cluster_span_set(spans, docs, segs, enc, cfg)
            for c in st["cluster"].values():
                c["e2e_value"], c["e2e_tight"] = st["value"] * c["F1"], st["tight"] * c["F1"]
                c["e2e_ci"] = (st["value_ci"][0] * c["f1_ci"][0], st["value_ci"][1] * c["f1_ci"][1])
            ch = st["cluster"]["chosen"]
            st["e2e"], st["e2e_ci"] = ch["e2e_value"], ch["e2e_ci"]
            res[(s, thr)], hits[(s, thr)], spanset[(s, thr)] = st, hit, spans
            print(f"{s} {thr}: {len(spans)} spans, tight {st['tight']:.3f}, value {st['value']:.3f}, "
                  f"chosen F1 {ch['F1']:.3f}, {time.time() - t0:.0f}s", flush=True)
    enc.save()
    write_outputs(out, args, docs, mentions, vkeys, sets, metas, res, hits, spanset, time.time() - t0)
    print(f"done in {time.time() - t0:.0f}s -> {out / 'gliner_labels.md'}")


def span_tables(L, sets, rows, res, args, metas):
    L += ["## Span finding", "",
          "| Set | Thr | Spans/dlg | Span precision | Tight recall (range) | Mention recall | Value recall (range) | "
          + " | ".join(f"L{k} vis / hid" for k in LEVELS) + " |", "|---|---|---|---|---|---|---|---|---|---|"]
    for key in rows:
        r = res[key]
        L.append(f"| {key[0]} | {key[1]} | {r['spans_per_dlg']:.1f} | {fmt(r['span_precision'])} | "
                 f"{fmt(r['tight'])} ({rng_(r['tight_ci'])}) | {fmt(r['mention'])} | "
                 f"{fmt(r['value'])} ({rng_(r['value_ci'])}) | " + " | ".join(
                     f"{fmt(r[f'visible_L{k}'], 2)} / {fmt(r[f'hidden_L{k}'], 2)}" for k in LEVELS) + " |")
    pc0 = res[(sets[0], 0.5)]["per_class"]
    L += ["", "Visible / hidden columns are value recall. Value recall by class at 0.5 (n = verbatim values):", "",
          "| Class | n | " + " | ".join(sets) + " |", "|---|---|" + "---|" * len(sets)]
    for c in sorted(pc0, key=lambda c: -pc0[c][0]):
        L.append(f"| {c} | {pc0[c][0]} | " + " | ".join(
            fmt(res[(s, 0.5)]["per_class"].get(c, (0, float("nan")))[1], 2) for s in sets) + " |")


def write_outputs(out, args, docs, mentions, vkeys, sets, metas, res, hits, spanset, secs):
    rows = [(s, t) for s in sets for t in THRESHOLDS]
    L = [f"# GLiNER label sets ({len(docs)} dialogues)", "",
         "One GLiNER pass per turn (speaker prefix removed). Sets: " + "; ".join(
             f"{s} ({len(SP.LABEL_SETS[s])} labels, windows of {metas[s]['max_words']} words, "
             f"{metas[s]['seconds']:.0f} s extraction)" for s in sets) + ". "
         f"Gold: {len(vkeys)} verbatim values. Segments {args.seg}; stage 1 k-means k=5 (3 seeds, mean); "
         f"stage 2 original (t {STAGE2_T}) or chosen Step 2 (`{args.step2}`, booking = (doc, segment)). "
         f"Run {secs / 60:.1f} min.", "",
         "Window check: " + "; ".join(
             f"{s} {metas[s]['overflow_at_default']} of {metas[s]['windows_checked']} windows over "
             f"{SP.PROMPT_LIMIT} subtokens at {metas[s]['default_max_words']} words" for s in sets) + ".", ""]
    span_tables(L, sets, rows, res, args, metas)

    L += ["", "## Values GLiNER generic 0.5 missed", ""]
    if BASE in hits:
        missed = [k for k in vkeys if k not in hits[BASE]]
        others = [k for k in rows if k != BASE]
        gh = {k: group_hits(vkeys, mentions, hits[k], missed) for k in others}
        base_n = group_hits(vkeys, mentions, set(), missed)
        L += [f"{len(missed)} of {len(vkeys)} values missed; share recovered by each set and threshold:", "",
              "| Group | Missed | " + " | ".join(f"{s} {t}" for s, t in others) + " |",
              "|---|---|" + "---|" * len(others)]
        for g in base_n:
            L.append(f"| {g} | {base_n[g][0]} | " + " | ".join(fmt(gh[k][g][1], 2) for k in others) + " |")

    L += ["", "## Two-stage clustering", "",
          "Attribute B-cubed (lenient) on matched spans; end to end = recall x F1. The LEAKY row runs stage 2 "
          "separately inside each (entity group, GLiNER label): the label becomes a clustering feature"
          + (", and for set gold the labels are the gold slot names, so it is near-oracle." if "gold" in sets else ".")
          + " Not a fair pipeline row.", "",
          "| Set | Thr | Stage 2 | P | R | F1 (range) | K | Value x F1 | Tight x F1 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for key in rows:
        for name, c in res[key]["cluster"].items():
            flag = "**LEAKY: partition by GLiNER label**" if name.startswith("LEAKY") else name
            L.append(f"| {key[0]} | {key[1]} | {flag} | {fmt(c['P'])} | {fmt(c['R'])} | **{fmt(c['F1'])}** "
                     f"({rng_(c['f1_ci'])}) | {c['K']:.0f} | {fmt(c['e2e_value'])} | {fmt(c['e2e_tight'])} |")

    L += ["", "## Verdict", "",
          "Rule, fixed in advance: labels are the bottleneck if set hand or gold gains >= 0.10 tight recall or "
          ">= 0.05 end to end (value recall x F1, chosen Step 2, not the leaky row) over generic and the "
          "bootstrap ranges (dialogue resamples; end-to-end range = product of the recall and F1 bounds) "
          "do not overlap; GLiNER is the bottleneck if gold beats generic by < 0.03 tight recall; otherwise "
          "unclear. The threshold 0.5 decides; 0.3 is shown for reference.", ""]
    if "generic" in sets:
        for thr in (0.5, 0.3):
            v, lines = verdict(res, thr)
            L += [f"**Threshold {thr}: {v}**" + (" (decisive)" if thr == 0.5 else ""), ""] + lines + [""]
            print(f"verdict at {thr}: {v}")
    (out / "gliner_labels.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    write_csv(out, rows, res)
    write_examples(out, sets, mentions, vkeys, hits, spanset)


def write_csv(out, rows, res):
    C = []
    for (s, t) in rows:
        r = res[(s, t)]
        C += [dict(section="span", set=s, thr=t, key=k, value=r[k]) for k in
              ("spans_per_dlg", "span_precision", "tight", "mention", "value")
              + tuple(f"{h}_L{k}" for k in LEVELS for h in ("visible", "hidden"))]
        C += [dict(section="class_value_recall", set=s, thr=t, key=c, value=v[1]) for c, v in r["per_class"].items()]
        for name, c in r["cluster"].items():
            C += [dict(section="cluster", set=s, thr=t, stage2=name, key=k, value=c[k])
                  for k in ("P", "R", "F1", "K", "e2e_value", "e2e_tight")]
    with open(out / "gliner_labels.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["section", "set", "thr", "stage2", "key", "value"])
        w.writeheader()
        w.writerows(C)


def write_examples(out, sets, mentions, vkeys, hits, spanset):
    E = ["# GLiNER label set examples (threshold 0.5)", ""]
    for s in sets:
        spans = spanset[(s, 0.5)]
        E += [f"## {s}", "", "### Values recovered (missed by generic 0.5)", ""]
        if s == "generic" or BASE not in hits:
            E += ["(baseline)", ""]
        else:
            rec = sorted(k for k in hits[(s, 0.5)] if k not in hits[BASE])
            by_doc = defaultdict(list)
            for u in spans:
                by_doc[u.doc_id].append(u)
            for d, v in rec[::max(1, len(rec) // 15)][:15]:
                labs = ", ".join(sorted(mentions[vkeys[(d, v)][0]].labels))
                sp = next(u for ix in vkeys[(d, v)] for u in by_doc[d]
                          if min(u.end, mentions[ix].end) > max(u.start, mentions[ix].start))
                E.append(f"- {d}: \"{v}\" ({labs}) <- span \"{sp.text}\" label {sp.tag}")
            E += [f"({len(rec)} recovered in total)", ""]
        E += ["### Spans that matched nothing", ""]
        none = [u for u in spans if not u.labels]
        for u in none[::max(1, len(none) // 15)][:15]:
            E.append(f"- {u.doc_id}: \"{u.text}\" label {u.tag} score {u.score:.2f}")
        E += [f"({len(none)} of {len(spans)} spans)", ""]
    (out / "gliner_labels_examples.md").write_text("\n".join(E) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
