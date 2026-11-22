"""wf_v5.0 G5: score Step 4 variant ARMg (A+R+M, guided rerun, on the G3+G4 input) next to the wf_v4.9 variants A, B, BM, AR with the v4.9 V3
scorer (scripts/step4_score_v49_v3.py, its module globals pointed at results/wf_v50/g5), then the final freeze rule (s1a/step4_pick_v50.py).

python scripts/g5_score_v50.py  -> results/wf_v50/g5/{scores.csv, g5.md}; score-map copies with L2_ ids in results/wf_v50/g5/l2map.
The loop-2 columns of the v5.0 input equal the v4.9 ones (checked), so V1.prepare (v4.9 W2 loop-2 columns) is right for ARMg too.
The first G5 run (step4_ARM, unguided fallback on every call) is not scored.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import gpu_v50 as G  # noqa: E402
import step4_score_v48 as S48  # noqa: E402
import step4_score_v49 as V1  # noqa: E402
import step4_score_v49_v3 as V3  # noqa: E402
from s1a import step4_gt as SG  # noqa: E402
from s1a import step4_pick_v50 as PF  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402

OUT = G.G5
V3.VARIANTS = {**V3.VARIANTS, "ARMg": G.G5}
V3.REASK = {**V3.REASK, "p2_reask2": "reask2"}


def freeze_md(chosen, res):
    lines = ["| variant | chains failing rule 1 (max 1 of 6) | rule 1 problems | limit: placed > 0.05 below best | table F1 + grouping F1, sum |",
             "|---|---|---|---|---|"]
    for v, r in res.items():
        lines.append(f"| {v} | {r['bad_chains']} {'pass' if r['rule1'][0] else 'FAIL'} | {r['rule1'][1]} | {r['limit'] or 'none'} | "
                     f"{'n/a' if r['score'] is None else f'{r['score']:.3f}'} |")
    return "\n".join(lines) + f"\n\nFrozen as Step 4 v5.0: {chosen or 'none (no variant passes rule 1)'}."


def main():
    gt = SC43.load_gt(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    names = SG.gt_names(gt)
    l2map = OUT / "l2map"
    prep = {dev: V1.prepare(dev, run, names, V3.VARIANTS, l2map) for dev, run in G.SETS.items()}
    hotel = V3.hotel_entities(prep)
    parts = []
    for view in V1.VIEWS:
        opts = V1.opts_for(prep, view, l2map)
        parts.append(V1.placement(gt, prep, S48.rows(gt, opts=opts, variants=V3.VARIANTS), opts, V3.VARIANTS, hotel).assign(l2_view=view))
    df = V3.reasks(pd.concat(parts, ignore_index=True))
    df.to_csv(OUT / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
    d = V3.main_rows(df)
    chosen, res = PF.freeze(d, V3.SEEDS)
    md = ["# wf_v5.0 G5: Step 4 A+R+M (ARMg) vs the wf_v4.9 variants, final freeze rule", "",
          f"Hotel entities: {', '.join(f'{k}: {sorted(v)}' for k, v in hotel.items())}. ARMg = A + re-ask r1 + re-ask r2 + same-entity merge, on the "
          "G3 (context split) + G4 (renames) input; the others on the v4.9 input. reask2 row = p2_reask2 per chain.", "",
          V3.table_md(d), "", "## Freeze rule (diary Nov 23)", "", freeze_md(chosen, res)]
    (OUT / "g5.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
