"""Entity segmentation (Chroma + bge-m3, smaller sizes, similarity + keyword merge) and GLiNER
value spans, put back into Step 1a's two-stage clustering and compared with the current method
(Chroma 50/400, no merge).

python scripts/entity_seg.py --limit 50
  -> results/n50/entity_seg.{md,csv}, entity_seg_examples.md, entity_seg/ (chunk and span caches)
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

from relabel import THRESHOLDS, entity_groups, stage2  # noqa: E402
from run import build_units, encoder  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import segment as S  # noqa: E402
from s1a import spans as SP  # noqa: E402
from s1a import units as U  # noqa: E402
from chk.metrics import boundary_counts, cuts_to_gaps, prf  # noqa: E402
from hbe.metrics import external  # noqa: E402

BASE = ((50, 400), None)
SPAN_THRESHOLDS = (0.3, 0.5)


def cfg_name(size, tau):
    return f"{size[0]}/{size[1]}" + (f" +merge {tau:.2f}" if tau else "")


def cfg_key(size, tau):
    return f"{size[0]}_{size[1]}" + (f"_m{int(tau * 100)}" if tau else "")


def load_chunks(cache, docs, enc, size):
    if size == BASE[0]:
        src = paths.CHROMA_CHUNKS
    else:
        src = cache / f"chunks_{size[0]}_{size[1]}.jsonl"
    have = {}
    if src.exists():
        for line in open(src, encoding="utf-8"):
            r = json.loads(line)
            have[r["doc_id"]] = r["chunks"]
    todo = [d for d in docs if d not in have]
    if todo and size == BASE[0]:
        raise SystemExit(f"{src} lacks {len(todo)} docs")
    with open(src, "a", encoding="utf-8") as f:
        for did in todo:
            have[did] = S.chroma_pieces(docs[did].text, enc, *size)
            f.write(json.dumps({"doc_id": did, "chunks": have[did]}) + "\n")
            f.flush()
        enc.save()
    return have


def segment_stats(docs, spans_by_doc):
    tp0 = tp1 = n_hyp = n_ref = inside = n_turns = pure = n_seg = 0
    for did, doc in docs.items():
        sp = spans_by_doc[did]
        gaps, ins = cuts_to_gaps(doc, sp)
        a, h, r = boundary_counts(doc.gold_gaps, gaps, 0)
        b, _, _ = boundary_counts(doc.gold_gaps, gaps, 1)
        tp0, tp1, n_hyp, n_ref = tp0 + a, tp1 + b, n_hyp + h, n_ref + r
        inside += ins
        n_seg += len(sp)
        seg_of = [next((i for i, (s, e) in enumerate(sp) if s <= ts < e), len(sp) - 1)
                  for ts, _ in doc.spans]
        for i in set(seg_of):
            doms = [doc.domains[t] for t, g in enumerate(seg_of) if g == i]
            pure += Counter(doms).most_common(1)[0][1]
        n_turns += doc.n_turns
    p0, r0, f0 = prf(tp0, n_hyp, n_ref)
    p1, r1, f1 = prf(tp1, n_hyp, n_ref)
    return dict(seg_per_dlg=n_seg / len(docs), cut_inside_pct=100 * inside / max(1, n_seg - len(docs)),
                p0=p0, r0=r0, f0=f0, p1=p1, r1=r1, f1=f1, purity=pure / n_turns)


def two_stage_scores(us, xv, groups_by_seed, golds, scored=None):
    """Mean over seeds of stage-1 entity F1 and stage-2 attribute/entity/slot F1 per threshold.
    scored: indices that have a gold label (all if None)."""
    idx = list(range(len(us))) if scored is None else scored
    sub = {g: [v[i] for i in idx] for g, v in golds.items()}
    res = {"stage1_entity_f1": np.mean([external(sub["entity"], [g[i] for i in idx])["bcubed_f1"]
                                        for g in groups_by_seed.values()])}
    for t in THRESHOLDS:
        ms = []
        for g in groups_by_seed.values():
            lab = stage2(xv, g, t)
            lab = [lab[i] for i in idx]
            ms.append({k: external(v, lab) for k, v in sub.items()} | {"K": len(set(lab))})
        res[f"t{t}_K"] = np.mean([m["K"] for m in ms])
        for k in sub:
            res[f"t{t}_{k}_f1"] = np.mean([m[k]["bcubed_f1"] for m in ms])
        res[f"t{t}_attr_nmi"] = np.mean([m["attribute"]["nmi"] for m in ms])
    return res


def golds_of(labels):
    """attribute ("Train day"), entity ("Train"), slot ("day")"""
    return {"attribute": list(labels),
            "entity": [a.split()[0] for a in labels],
            "slot": [a.split(" ", 1)[1] for a in labels]}


def gliner_spans(cache, key, docs, segs_by_doc, model):
    path = cache / f"gliner_{key}.jsonl"
    have = {}
    if path.exists():
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            have[r["doc_id"]] = r["spans"]
    with open(path, "a", encoding="utf-8") as f:
        for did, doc in docs.items():
            if did in have:
                continue
            us = SP.extract(model, doc, segs_by_doc[did])
            have[did] = [[u.start, u.end, u.tag, u.score] for u in us]
            f.write(json.dumps({"doc_id": did, "spans": have[did]}) + "\n")
            f.flush()
    out = []
    for did, doc in docs.items():
        for s, e, tag, score in have[did]:
            u = U.Unit("span", did, "", doc.text[s:e], s, e, U.turn_of(doc, s))
            u.tag, u.score = tag, score
            out.append(u)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--gliner-top", type=int, default=3, help="best configs (besides the base) to run GLiNER on")
    ap.add_argument("--no-gliner", action="store_true")
    args = ap.parse_args()
    out = paths.RESULTS / f"n{args.limit}"
    cache = out / "entity_seg"
    cache.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    docs, sets, stats = build_units(args.limit)
    enc = encoder()
    vals = sets["value"]
    vgold = golds_of([u.label for u in vals])
    xv = enc.encode([u.text for u in vals])

    # ---------------------------------------------------------------- segmentation grid
    rows, segs_of, adj = [], {}, {}
    for size in S.SIZES:
        chunks = load_chunks(cache, docs, enc, size)
        base_spans = {d: S.piece_spans(docs[d], chunks[d]) for d in docs}
        sims = []
        for d, sp in base_spans.items():
            v = enc.encode([docs[d].text[s:e] for s, e in sp])
            sims += [float(v[i] @ v[i + 1]) for i in range(len(sp) - 1)]
        adj[f"{size[0]}/{size[1]}"] = np.percentile(sims, [10, 50, 75, 90, 100])
        print(f"chunks {size}: {time.time() - t0:.0f}s", flush=True)
        for tau in S.TAUS:
            sp = {d: S.merge_adjacent(docs[d].text, base_spans[d], enc, tau) for d in docs}
            segs = [u for d in docs for u in U.chroma_units(docs[d], S.as_chunks(docs[d], sp[d]))]
            segs_of[(size, tau)] = (sp, segs)
            row = dict(config=cfg_name(size, tau), key=cfg_key(size, tau), n_seg=len(segs))
            row |= segment_stats(docs, sp)
            row |= two_stage_scores(vals, xv, entity_groups(vals, segs, enc), vgold)
            rows.append(row)
            print(f"  {row['config']}: {len(segs)} segs, A F1@0.4 {row['t0.4_attribute_f1']:.3f}", flush=True)
        enc.save()
    gold_row = dict(config="oracle entity (gold)", key="gold")
    gold_row |= two_stage_scores(vals, xv, {0: vgold["entity"]}, vgold)
    with open(out / "entity_seg.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---------------------------------------------------------------- GLiNER spans
    span_rows, span_examples = [], {}
    if not args.no_gliner:
        best = sorted((r for r in rows if r["key"] != cfg_key(*BASE)),
                      key=lambda r: -r["t0.4_attribute_f1"])[:args.gliner_top]
        chosen = [BASE] + [next(c for c in segs_of if cfg_key(*c) == r["key"]) for r in best]
        model = SP.load()
        for c in chosen:
            sp, segs = segs_of[c]
            allspans = gliner_spans(cache, cfg_key(*c), docs, sp, model)
            print(f"gliner {cfg_name(*c)}: {len(allspans)} spans, {time.time() - t0:.0f}s", flush=True)
            for thr in SPAN_THRESHOLDS:
                us = [u for u in allspans if u.score >= thr]
                for u in us:
                    u.label = ""
                n_match = SP.match(us, vals)
                scored = [i for i, u in enumerate(us) if u.label]
                xs = enc.encode([u.text for u in us])
                g = golds_of([u.label or "none none" for u in us])  # unmatched: never scored
                r = dict(config=cfg_name(*c), threshold=thr, n_spans=len(us),
                         spans_per_dlg=len(us) / len(docs), value_recall=n_match / len(vals),
                         unmatched_pct=100 * (len(us) - len(scored)) / max(1, len(us)))
                r |= two_stage_scores(us, xs, entity_groups(us, segs, enc), g, scored)
                span_rows.append(r)
                if thr == SPAN_THRESHOLDS[0]:
                    span_examples[cfg_name(*c)] = us
        enc.save()

    write_md(out, rows, gold_row, span_rows, adj, args.limit, len(vals), time.time() - t0)
    write_examples(out, docs, segs_of, span_examples)
    print(f"done in {time.time() - t0:.0f}s -> {out / 'entity_seg.md'}")


def _f(x, d=3):
    return f"{x:.{d}f}"


def write_md(out, rows, gold_row, span_rows, adj, limit, n_vals, secs):
    L = [f"# Entity segmentation and GLiNER spans in Step 1a ({limit} dialogues)", "",
         f"Chroma ClusterSemanticChunker with bge-m3 only. Base = 50/400, no merge (the current method). "
         f"Run time {secs / 60:.1f} min.", "",
         "## Segments", "",
         "Boundaries vs gold domain changes, pooled over dialogues; ±1 = within one turn. "
         "Purity = turns in their segment's majority gold domain.", "",
         "| Config | Seg/dialogue | Cuts inside turn % | P ±0 | R ±0 | F1 ±0 | P ±1 | R ±1 | F1 ±1 | Purity |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['config']} | {r['seg_per_dlg']:.1f} | {r['cut_inside_pct']:.0f} | {_f(r['p0'], 2)} | "
                 f"{_f(r['r0'], 2)} | {_f(r['f0'], 2)} | {_f(r['p1'], 2)} | {_f(r['r1'], 2)} | "
                 f"{_f(r['f1'], 2)} | {_f(r['purity'], 2)} |")
    L += ["", "Cosine of adjacent pieces before the merge (bge-m3), percentiles 10/50/75/90/max: "
          + "; ".join(f"{k}: " + "/".join(f"{x:.2f}" for x in v) for k, v in adj.items()) + ". "
          "Merge = cosine >= tau and no new entity word."]
    L += ["", f"## A. Two-stage on the {n_vals} gold values (segmentation only)", "",
          "Stage 1: k-means k=5 on segment vectors, value takes its segment's cluster (3 seeds). "
          "Stage 2: agglomerative on value strings, distance threshold t. B-cubed F1 vs attribute (NMI).", "",
          "| Config | Stage-1 entity F1 | t=0.3 | t=0.4 (K) | t=0.5 | slot F1 @0.4 |", "|---|---|---|---|---|---|"]
    for r in rows + [gold_row]:
        L.append(f"| {r['config']} | {_f(r['stage1_entity_f1'])} | {_f(r['t0.3_attribute_f1'])} | "
                 f"**{_f(r['t0.4_attribute_f1'])}** ({r['t0.4_K']:.0f}, NMI {r['t0.4_attr_nmi']:.2f}) | "
                 f"{_f(r['t0.5_attribute_f1'])} | {_f(r['t0.4_slot_f1'])} |")
    if span_rows:
        L += ["", "## B. End to end: GLiNER spans as units", "",
              f"Labels: {', '.join(SP.LABELS)}. A span is scored if it overlaps a gold value (each value once); "
              "all spans are clustered, only matched spans are scored. Same two stages as A.", "",
              "| Config | GLiNER thr | Spans/dialogue | Gold value recall | Unmatched spans % | Stage-1 entity F1 | "
              "attr F1 t=0.3 | t=0.4 (K) | t=0.5 |", "|---|---|---|---|---|---|---|---|---|"]
        for r in span_rows:
            L.append(f"| {r['config']} | {r['threshold']} | {r['spans_per_dlg']:.1f} | {_f(r['value_recall'], 2)} | "
                     f"{r['unmatched_pct']:.0f} | {_f(r['stage1_entity_f1'])} | {_f(r['t0.3_attribute_f1'])} | "
                     f"**{_f(r['t0.4_attribute_f1'])}** ({r['t0.4_K']:.0f}) | {_f(r['t0.5_attribute_f1'])} |")
    (out / "entity_seg.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def write_examples(out, docs, segs_of, span_examples, n_docs=3):
    base = BASE
    L = ["# Entity segmentation examples", ""]
    show = [c for c in segs_of if c == base] + [c for c in segs_of
                                                 if cfg_name(*c) in span_examples and c != base]
    for did in list(docs)[:n_docs]:
        doc = docs[did]
        L += [f"## {did}", ""]
        for c in show:
            sp, _ = segs_of[c]
            name = cfg_name(*c)
            spans = [u for u in span_examples.get(name, []) if u.doc_id == did]
            L += [f"### {name}: {len(sp[did])} pieces", ""]
            for i, (s, e) in enumerate(sp[did]):
                txt = doc.text[s:e]
                for u in sorted((u for u in spans if s <= u.start < e), key=lambda u: -u.start):
                    tag = u.tag + (f"={u.label}" if u.label else "")
                    a, b = u.start - s, u.end - s
                    txt = txt[:a] + f"[{txt[a:b]}]({tag})" + txt[b:]
                doms = Counter(doc.domains[t] for t, (ts, _) in enumerate(doc.spans) if s <= ts < e)
                L.append(f"**piece {i + 1}** (gold: {', '.join(f'{k} {v}' for k, v in doms.most_common())})")
                L += [f"> {line}" for line in txt.strip().split("\n")] + [""]
    for name, us in span_examples.items():
        un = Counter((u.tag, u.text.lower()) for u in us if not u.label)
        L += [f"## Unmatched GLiNER spans, {name} (most frequent)", "",
              ", ".join(f"{t}: \"{x}\" {n}" for (t, x), n in un.most_common(40)), ""]
    (out / "entity_seg_examples.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
