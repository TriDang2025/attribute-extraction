"""C7: the chosen Step 2 on predicted entities (Chroma segments + k-means stage 1), for gold
mentions (A) and GLiNER spans (B), against the original stage 2 (raw strings, average, t=0.4).

python scripts/plug_in.py --limit 50 [--seg 5/25,0.40,on,on] [--step2 results/v2_n50/chosen_step2_joint.json]
    [--step2-gold results/v3_n50/chosen_step2_window.json] [--spans <GLiNER cache .jsonl>]
  -> results/v2_n50/plug_in.md
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from relabel import entity_groups, stage2  # noqa: E402
from run import build_units, encoder  # noqa: E402
from s1a import gold, paths  # noqa: E402
from s1a import metrics as M  # noqa: E402
from s1a import segment as S  # noqa: E402
from s1a import step2 as S2  # noqa: E402
from s1a import units as U  # noqa: E402
import spans_compare as SC  # noqa: E402

CHUNKS = paths.RESULTS / "n50" / "entity_seg"
DEFAULT_SEG = "5/25,0.40,on,on"  # adopted 2026-10-25 (v3): snap + merge 0.40 with the keyword check
DEFAULT_SPANS = "results/v3_n50/gliner_labels/gliner_turn_generic.jsonl"  # GLiNER once per turn, no prefix


def parse_seg(s):
    size, tau, snap, kw = s.split(",")
    if size != "turn":
        a, b = size.split("/")
        size = (int(a), int(b))
    return size, (None if tau == "none" else float(tau)), snap == "on", kw == "on"


def seg_key(size, tau, snap, kw):
    k = ("turn" if size == "turn" else f"{size[0]}_{size[1]}") + ("_s" if snap and size != "turn" else "") + (f"_m{round(tau * 100)}" if tau else "")
    return k + ("" if kw or not tau else "_nk")


def segments(docs, enc, size, tau, snap, kw, cache=CHUNKS):
    have = {}
    if size != "turn":
        src = paths.CHROMA_CHUNKS if size == (50, 400) else cache / f"chunks_{size[0]}_{size[1]}.jsonl"
        for line in open(src, encoding="utf-8"):
            r = json.loads(line)
            have[r["doc_id"]] = r["chunks"]
    segs = []
    for did, doc in docs.items():
        sp = S.turn_pieces(doc) if size == "turn" else S.piece_spans(doc, have[did])
        if snap and size != "turn":
            sp = S.snap_to_turns(doc, sp)
        sp = S.merge_adjacent(doc.text, sp, enc, tau, use_keywords=kw)
        segs += U.chroma_units(doc, S.as_chunks(doc, sp))
    return segs


def piece_of(units, segs):
    by_doc = {}
    for i, c in enumerate(segs):
        by_doc.setdefault(c.doc_id, []).append((c.start, c.end, i))
    return [next((i for s, e, i in by_doc.get(u.doc_id, []) if s <= u.start < e), -1) for u in units]


def run(units, docs, segs, enc, cfg, ts=()):
    """Mean over the 3 stage-1 seeds of (original stage 2, chosen stage 2, chosen at each t in ts)
    report blocks."""
    xs = enc.encode([u.text for u in units])
    piece = piece_of(units, segs)
    books = [(u.doc_id, p) for u, p in zip(units, piece)]
    out = {"original": [], "chosen": []} | {f"chosen t={t}": [] for t in ts}
    for g in entity_groups(units, segs, enc).values():
        out["original"].append(M.report_block(units, stage2(xs, g, 0.4)))
        out["chosen"].append(M.report_block(units, S2.run_best(units, docs, g, books, enc, cfg)))
        for t in ts:
            out[f"chosen t={t}"].append(M.report_block(units, S2.run_best(units, docs, g, books, enc,
                                                                          dict(cfg, t=t))))
    return {k: dict(P=np.mean([d["all"]["p"] for d in v]), R=np.mean([d["all"]["r"] for d in v]),
                    F1=np.mean([d["all"]["f"] for d in v]), K=np.mean([d["K"] for d in v]),
                    **{f"{h}_L{k}": np.mean([d[f"{h}_L{k}"]["f"] for d in v])
                       for k in (1, 2, 3) for h in ("visible", "hidden")},
                    block=v[0])
            for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--seg", action="append", help="size,tau,snap,keywords e.g. 25/100,0.45,off,on or turn,0.40,on,on")
    ap.add_argument("--step2", default="results/v2_n50/chosen_step2_joint.json", help="Step 2 for spans (B)")
    ap.add_argument("--step2-gold", default="results/v3_n50/chosen_step2_window.json",
                    help="Step 2 for gold mentions (A)")
    ap.add_argument("--spans", default=DEFAULT_SPANS, help="GLiNER span cache (threshold 0.5 applied)")
    ap.add_argument("--chunk-cache", default=str(CHUNKS), help="dir with chunks_<a>_<b>.jsonl")
    ap.add_argument("--out", default="results/v2_n50")
    ap.add_argument("--t", default="", help="extra thresholds for the chosen Step 2, e.g. 0.25,0.3,0.35")
    ap.add_argument("--name", default="plug_in", help="output file stem")
    args = ap.parse_args()
    out = paths.ROOT / args.out
    t0 = time.time()
    cfg = json.load(open(paths.ROOT / args.step2, encoding="utf-8"))
    cfg_gold = json.load(open(paths.ROOT / args.step2_gold, encoding="utf-8"))
    docs, _, _ = build_units(args.limit)
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    docs = {d: v for d, v in docs.items() if d in tables}
    mentions = gold.mentions_for(docs, tables)
    verb = [m for m in mentions if m.verbatim]
    enc = encoder()
    spans = SC.gliner_units(paths.ROOT / args.spans, docs, 0.5)
    M.match_all(spans, mentions)
    vrec = M.span_recall(spans, mentions)["value"]
    rows = []
    for seg in args.seg or [DEFAULT_SEG]:
        size, tau, snap, kw = parse_seg(seg)
        segs = segments(docs, enc, size, tau, snap, kw, Path(args.chunk_cache))
        for unit_name, us, c in (("A gold mentions", verb, cfg_gold), ("B GLiNER 0.5 spans", spans, cfg)):
            res = run(us, docs, segs, enc, c, [float(x) for x in args.t.split(",") if x])
            for st, r in res.items():
                rows.append(dict(seg=seg_key(size, tau, snap, kw), units=unit_name, stage2=st, **r,
                                 e2e=(vrec * r["F1"]) if unit_name.startswith("B") else None))
            print(f"{seg} {unit_name}: original {res['original']['F1']:.3f} -> chosen {res['chosen']['F1']:.3f}",
                  flush=True)
    enc.save()
    L = [f"# C7: chosen Step 2 on predicted entities ({args.limit} dialogues)", "",
         f"Step 2 config (spans): `{json.dumps(cfg)}`; (gold mentions): `{json.dumps(cfg_gold)}`. Stage 1 = k-means k=5 on segments (3 seeds, mean). "
         f"Booking = (dialogue, segment). B value recall = {vrec:.3f}. Run {(time.time() - t0) / 60:.1f} min.", "",
         "| Segments | Units | Stage 2 | P | R | F1 | K | vis/hid L1 | vis/hid L2 | vis/hid L3 | End to end |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        vh = " | ".join(f"{r[f'visible_L{k}']:.3f} / {r[f'hidden_L{k}']:.3f}" for k in (1, 2, 3))
        e2e = f"{r['e2e']:.3f}" if r["e2e"] is not None else ""
        L.append(f"| {r['seg']} | {r['units']} | {r['stage2']} | {r['P']:.3f} | {r['R']:.3f} | **{r['F1']:.3f}** | "
                 f"{r['K']:.0f} | {vh} | {e2e} |")
    L += [""]
    for r in rows:
        if r["stage2"] == "chosen" and not args.t:
            L.append(M.format_block(r["block"], f"{r['seg']}, {r['units']}, chosen Step 2 (seed 42)"))
            L.append("")
    (out / f"{args.name}.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"done in {time.time() - t0:.0f}s -> {out / (args.name + '.md')}")


if __name__ == "__main__":
    main()
