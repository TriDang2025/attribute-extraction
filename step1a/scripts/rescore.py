"""Rescore the two entity_seg configs (50/400 and 25/100 +merge 0.45, two stages at t=0.4) under
the v2 protocol, one change at a time, then all together.

Rows: old (one unit per gold value, spans.match, single-label B-cubed); E1 match_all (B);
E2 class merge + lenient multi-label B-cubed; E3 verbatim-only span recall (B); E4 every mention
as a unit (A); all = E1-E4 with visible / hidden blocks. A = gold-value units, B = GLiNER spans
(threshold 0.5, from the entity_seg cache; GLiNER is never run). Mean over 3 k-means seeds.

python scripts/rescore.py --limit 50 [--split dev]
  -> results/v2_n50/{rescore.md, rescore.csv, rescore_examples.md}
"""

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from entity_seg import cfg_key, cfg_name, gliner_spans, load_chunks  # noqa: E402
from relabel import SEEDS, entity_groups, stage2  # noqa: E402
from run import build_units, encoder  # noqa: E402
from s1a import gold as G  # noqa: E402
from s1a import metrics as M  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import segment as S  # noqa: E402
from s1a import spans as SP  # noqa: E402
from s1a import units as U  # noqa: E402

CONFIGS = (((50, 400), None), ((25, 100), 0.45))
T = 0.4
SPAN_THR = 0.5
# results/n50/entity_seg.md (2026-10-21), t=0.4 attribute P / R / F1 (K)
REF = {("50/400", "A"): (0.614, 0.381, 0.470, 134), ("50/400", "B"): (0.715, 0.421, 0.530, 102),
       ("25/100 +merge 0.45", "A"): (0.641, 0.480, 0.549, 120),
       ("25/100 +merge 0.45", "B"): (0.762, 0.473, 0.583, 105)}
ROWS = (("old", "A"), ("E2", "A"), ("E4", "A"), ("all", "A"),
        ("old", "B"), ("E1", "B"), ("E2", "B"), ("E3", "B"), ("all", "B"))


def score(labels, raw, pred, strict, levels):
    """P/R/F1 on the labelled items, overall and visible / hidden per level. Subsets average
    the per-item scores of the full clustering (strict = single-label B-cubed on the joined label)."""
    pred = [str(p) for p in pred]
    idx = [i for i, s in enumerate(labels) if s]
    ls = [frozenset({"|".join(sorted(labels[i]))}) if strict else labels[i] for i in idx]
    p, r = M.bcubed_items(ls, [pred[i] for i in idx]) if idx else (np.zeros(0), np.zeros(0))

    def f(ix):
        return M._prf(p[ix], r[ix]) if len(ix) else (0.0, 0.0, 0.0)

    out = dict(zip(("p", "r", "f1"), f(list(range(len(idx))))), n=len(idx), K=len(set(pred)),
               K_scored=len({pred[i] for i in idx}))
    for k, h in levels.items():
        vis = [j for j, i in enumerate(idx) if not raw[i] & h]
        hid = [j for j, i in enumerate(idx) if raw[i] & h]
        out[f"vis{k}_f1"], out[f"hid{k}_f1"] = f(vis)[2], f(hid)[2]
        out[f"vis{k}_n"], out[f"hid{k}_n"] = len(vis), len(hid)
    return out


def cache_dir(split, limit):
    if split == "dev" and limit <= 50:
        return paths.RESULTS / "n50" / "entity_seg"
    return paths.RESULTS / (f"n{limit}" if split == "dev" else f"{split}_n{limit}") / "entity_seg"


def cached_spans(cache, key, docs, sp):
    path = cache / f"gliner_{key}.jsonl"
    have = {json.loads(line)["doc_id"] for line in open(path, encoding="utf-8")} if path.exists() else set()
    if set(docs) - have:
        raise SystemExit(f"{path} lacks {len(set(docs) - have)} docs; run entity_seg.py first")
    return [u for u in gliner_spans(cache, key, docs, sp, None) if u.score >= SPAN_THR]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--split", choices=("dev", "test"), default="dev")
    args = ap.parse_args()
    out = paths.RESULTS / (f"v2_n{args.limit}" if args.split == "dev" else f"v2_{args.split}_n{args.limit}")
    out.mkdir(parents=True, exist_ok=True)
    cache = cache_dir(args.split, args.limit)
    t0 = time.time()

    docs, sets, _ = build_units(args.limit, args.split)
    vals = sets["value"]
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    levels = G.load_levels()
    classes = G.merge_classes(G.load_all_tables())
    men_r = G.mentions_for(docs, tables, levels, {a: a for a in classes})
    men_m = G.mentions_for(docs, tables, levels, classes)
    verb_r = [m for m in men_r if m.verbatim]
    verb_m = [m for m in men_m if m.verbatim]
    assert [(m.doc_id, m.start) for m in verb_r] == [(m.doc_id, m.start) for m in verb_m]
    enc = encoder()

    def raw1(lab):
        return frozenset([lab]) if lab else frozenset()

    val_raw = [raw1(u.label) for u in vals]
    results, blocks, checks = [], {}, []
    for size, tau in CONFIGS:
        name = cfg_name(size, tau)
        chunks = load_chunks(cache, docs, enc, size)
        sp = {d: S.merge_adjacent(docs[d].text, S.piece_spans(docs[d], chunks[d]), enc, tau) for d in docs}
        segs = [u for d in docs for u in U.chroma_units(docs[d], S.as_chunks(docs[d], sp[d]))]
        spans = cached_spans(cache, cfg_key(size, tau), docs, sp)
        for u in spans:
            u.label = ""
        n_match = SP.match(spans, vals)
        old_b = [raw1(u.label) for u in spans]
        M.match_all(spans, men_r)
        e1_b = [u.labels for u in spans]
        used = M.match_all(spans, men_m)
        all_b = [u.labels for u in spans]
        raw_b = [u.raw_labels for u in spans]
        amb_b = [any(men_m[i].ambiguous for i in u.matched) for u in spans]
        sr_r, sr_m = M.span_recall(spans, men_r, tuple(levels)), M.span_recall(spans, men_m, tuple(levels))
        cl = lambda ls: [frozenset(classes.get(a, a) for a in s) for s in ls]  # noqa: E731
        rows = {
            ("old", "A"): (val_raw, val_raw, True), ("E2", "A"): (cl(val_raw), val_raw, False),
            ("E4", "A"): ([m.labels for m in verb_r], [m.raw_labels for m in verb_r], True),
            ("all", "A"): ([m.labels for m in verb_m], [m.raw_labels for m in verb_m], False),
            ("old", "B"): (old_b, old_b, True), ("E1", "B"): (e1_b, raw_b, True),
            ("E2", "B"): (cl(old_b), old_b, False), ("E3", "B"): (old_b, old_b, True),
            ("all", "B"): (all_b, raw_b, False)}
        unitset = {"A": {"old": vals, "E2": vals, "E4": verb_m, "all": verb_m}, "B": spans}
        preds = {}
        for key, us in (("vals", vals), ("men", verb_m), ("spans", spans)):
            x = enc.encode([u.text for u in us])
            preds[key] = [stage2(x, g, T) for g in entity_groups(us, segs, enc).values()]
        print(f"{name}: {len(segs)} segs, {len(spans)} spans, {time.time() - t0:.0f}s", flush=True)
        for row, ab in ROWS:
            labels, raw, strict = rows[(row, ab)]
            us = unitset["B"] if ab == "B" else unitset["A"][row]
            pk = "spans" if ab == "B" else ("vals" if row in ("old", "E2") else "men")
            per = [score(labels, raw, p, strict, levels) for p in preds[pk]]
            r = dict(config=name, row=row, units=ab, units_per_dlg=len(us) / len(docs))
            r |= {k: float(np.mean([x[k] for x in per])) for k in per[0]}
            if ab == "B":
                multi = [s for s in labels if s]
                r["multi_label_pct"] = 100 * sum(len(s) > 1 for s in multi) / max(1, len(multi))
                lab_amb = [a for a, s in zip(amb_b, all_b) if s]
                r["ambiguous_pct"] = 100 * sum(lab_amb) / max(1, len(lab_amb)) if row in ("E1", "all") else ""
                if row == "old":
                    r["span_recall_old"] = n_match / max(1, len(vals))
                if row in ("E3", "all"):
                    sr = sr_r if row == "E3" else sr_m
                    r["span_recall_mention"], r["span_recall_value"] = sr["mention"], sr["value"]
                    for k in levels:
                        r[f"sr_vis{k}"] = sr[f"visible_L{k}"]["value"]
                        r[f"sr_hid{k}"] = sr[f"hidden_L{k}"]["value"]
            else:
                if row in ("E4", "all"):
                    r["ambiguous_pct"] = 100 * float(np.mean([m.ambiguous for m in verb_m]))
                    r["multi_label_pct"] = 100 * float(np.mean([len(s) > 1 for s in labels]))
            results.append(r)
            if row == "old" and (name, ab) in REF:
                checks.append((name, ab, (r["p"], r["r"], r["f1"], r["K_scored"]), REF[(name, ab)]))
            if row == "all":
                us_b = us
                for u, s, h in zip(us_b, labels, raw):
                    u.labels, u.hidden = s, {k: bool(h & lv) for k, lv in levels.items()}
                d = M.report_block(us_b, preds[pk][0], tuple(levels))
                d["ci"] = M.bootstrap_ci(us_b, preds[pk][0])
                d["matched_mentions"] = len(used) if ab == "B" else None
                blocks[(name, ab)] = d
        enc.save()

    reproduce = args.split == "dev" and args.limit == 50
    for name, ab, got, ref in checks:
        ok = all(abs(a - b) <= 0.0015 for a, b in zip(got[:3], ref[:3])) and round(got[3]) == ref[3]
        flag = "ok" if ok else ("MISMATCH" if reproduce else "n/a (reference is dev n50)")
        print(f"old {name} {ab}: got {got[0]:.3f}/{got[1]:.3f}/{got[2]:.3f} K {got[3]:.0f}; "
              f"entity_seg.md {ref[0]:.3f}/{ref[1]:.3f}/{ref[2]:.3f} K {ref[3]}: {flag}")
    keys = list(dict.fromkeys(k for r in results for k in r))
    with open(out / "rescore.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(results)
    write_md(out, results, blocks, checks, reproduce, men_r, docs, levels, classes,
             f"{args.split}, {args.limit}", time.time() - t0)
    write_examples(out, docs, men_m)
    print(f"done in {time.time() - t0:.0f}s -> {out / 'rescore.md'}")


def _f(x, d=3):
    return "" if x == "" or x is None else f"{x:.{d}f}"


def _vh(r, side, k):
    return f"{r[f'{side}{k}_f1']:.3f}" if r[f"{side}{k}_n"] else "-"


def write_md(out, results, blocks, checks, reproduce, men_r, docs, levels, classes, limit, secs):
    lv = sorted(levels)
    merged = {a: b for a, b in classes.items() if a != b}
    L = [f"# Step 1a rescoring under the v2 protocol ({limit} dialogues)", "",
         f"Two stages (k-means k=5 on segments, then agglomerative cosine/average at t={T}), mean over "
         f"3 k-means seeds. B = GLiNER spans at threshold {SPAN_THR} from the entity_seg cache. "
         f"Run time {secs / 60:.1f} min.", "",
         "Rows: old = one unit per gold value, spans.match, single-label B-cubed; E1 = match_all "
         "(a span takes every overlapping mention's attributes; strict on the joined label); "
         f"E2 = class merge ({'; '.join(f'{a} -> {b}' for a, b in merged.items())}) + lenient "
         "multi-label B-cubed; E3 = span recall on verbatim mentions only; E4 = every verbatim mention "
         "is a unit (strict on the joined label); all = E1-E4, lenient. "
         "Span recall: old = share of located gold values matched (each once); E3/all = mention / value level.", "",
         "Old-protocol check against results/n50/entity_seg.md: "
         + "; ".join(f"{n} {ab} {g[2]:.3f} vs {r[2]:.3f}" + ("" if not reproduce else
                     (" ok" if abs(g[2] - r[2]) <= 0.0015 and round(g[3]) == r[3] else " **MISMATCH**"))
                     for n, ab, g, r in checks)
         + ("" if reproduce else " (reference is dev n50, not comparable)") + ".", "",
         "| Config | Row | Units | Units/dlg | Scored | K | P | R | F1 | Span recall | "
         + " | ".join(f"F1 vis/hid L{k}" for k in lv) + " | Ambig % | >1 label % |",
         "|" + "---|" * (12 + len(lv))]
    for r in results:
        if "span_recall_mention" in r:
            sr = f"{r['span_recall_mention']:.2f} / {r['span_recall_value']:.2f}"
        else:
            sr = _f(r.get("span_recall_old", ""), 2)
        L.append(f"| {r['config']} | {r['row']} | {r['units']} | {r['units_per_dlg']:.1f} | {r['n']:.0f} | "
                 f"{r['K']:.0f} | {_f(r['p'])} | {_f(r['r'])} | **{_f(r['f1'])}** | {sr} | "
                 + " | ".join(f"{_vh(r, 'vis', k)} / {_vh(r, 'hid', k)}" for k in lv)
                 + f" | {_f(r.get('ambiguous_pct', ''), 1)} | {_f(r.get('multi_label_pct', ''), 1)} |")
    sr_rows = [r for r in results if r["row"] == "all" and "sr_vis1" in r]
    if sr_rows:
        L += ["", "Span recall (value level) on visible / hidden attributes, all rows: "
              + "; ".join(f"{r['config']}: " + ", ".join(f"L{k} {r[f'sr_vis{k}']:.2f} / {r[f'sr_hid{k}']:.2f}"
                                                       for k in lv) for r in sr_rows)]
    nv = Counter(a for m in men_r if not m.verbatim for a in m.raw_labels)
    n_ver = sum(m.verbatim for m in men_r)
    L += ["", "## Gold mentions", "",
          f"{n_ver} verbatim mentions ({n_ver / len(docs):.1f} per dialogue, "
          f"{100 * np.mean([m.ambiguous for m in men_r if m.verbatim]):.1f}% ambiguous), "
          f"{len(men_r) - n_ver} non-verbatim values. Non-verbatim by attribute: "
          + ", ".join(f"{a} {n}" for a, n in nv.most_common()) + "."]
    L += ["", "## Report blocks (all rows, k-means seed 42)", ""]
    for (name, ab), d in blocks.items():
        L.append(M.format_block(d, f"{name}, {ab}") + f"Bootstrap 95% CI of F1 (dialogues): "
                 f"{d['ci'][0]:.3f}-{d['ci'][1]:.3f}.\n")
    (out / "rescore.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def write_examples(out, docs, mentions, n_docs=3):
    L = ["# Gold mentions, examples", "",
         "labels = classes after merge; raw = attributes; amb = no attribute of the turn's entity "
         "(all attributes with the value kept); verbatim = found in the text (turn -1 otherwise).", ""]
    for did in list(docs)[:n_docs]:
        doc = docs[did]
        L += [f"## {did}", "", "| Value | Text | Turn | Domain | Labels | Raw | Amb | Verbatim | Hidden L1/L2/L3 |",
              "|---|---|---|---|---|---|---|---|---|"]
        for m in (m for m in mentions if m.doc_id == did):
            dom = doc.domains[m.turn] if m.turn >= 0 else ""
            hid = "/".join("y" if m.hidden.get(k) else "-" for k in (1, 2, 3))
            L.append(f"| {m.value} | {m.text} | {m.turn} | {dom} | {', '.join(sorted(m.labels))} | "
                     f"{', '.join(sorted(m.raw_labels))} | {'y' if m.ambiguous else ''} | "
                     f"{'y' if m.verbatim else 'n'} | {hid} |")
        L += ["", "Dialogue:", ""] + [f"> {i}: {doc.text[s:e]}" for i, (s, e) in enumerate(doc.spans)] + [""]
    (out / "rescore_examples.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
