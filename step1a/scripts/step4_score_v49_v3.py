"""wf_v4.9 V3: score the Step 4 variants A, B, BM, AR with the V1 scoring (scorable loop-2 columns) and apply the coded pick rule (s1a/step4_pick_v49.py).

python scripts/step4_score_v49_v3.py  -> results/wf_v49/v3/{scores.csv, v3.md, fig_schema_dev50b_s0.png}; score-map copies with L2_ ids in results/wf_v49/v3/l2map.
Variants (folder <root>/<set>/step4_<v>, chain a_llama44_<run>_s<seed>, seeds 0-2): A, B = results/wf_v48/w3; BM (B + merge_same_entity, replayed on
cached B, calls and tokens = B), AR (A + p2_reask, GPU run) = results/wf_v49/v3. A variant without a final/ folder is "not run" (rerun when AR arrives).
Main view: GT view "Y1 rule", loop-2 view "spans+hc"; scores.csv also holds "spans". Scoring reuses step4_score_v49 (prepare, opts_for, placement)
and step4_score_v48 (rows, cell, share, figure). Gold is used for scoring only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import gpu_v48 as G48  # noqa: E402
import step4_score_v48 as S48  # noqa: E402
import step4_score_v49 as V1  # noqa: E402
from s1a import step4_gt as SG  # noqa: E402
from s1a import step4_pick_v49 as PK  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402

OUT = ROOT / "results" / "wf_v49" / "v3"
L2MAP = OUT / "l2map"
VARIANTS = {"A": G48.OUT, "B": G48.OUT, "BM": OUT, "AR": OUT}
MAIN = "spans+hc"
SEEDS = G48.SEEDS
REASK = {"p2_reask": "reask", "p2_reask_failed": "reask_failed", "p2_reask_missing": "reask_missing"}


def hotel_entities(prep):
    """{set: entities of its loop-2 internet / parking columns} (the hotel entity, read from the columns)."""
    return {dev: {k.split(":")[0] for k, c in p["cols"].items() if c["name"] in V1.CHECK} for dev, p in prep.items()}


def reasks(df):
    """df plus reask / reask_failed / reask_missing (p2_reask repairs of the chain, final/status.json repair_kinds; NaN = no status)."""
    kinds = {}
    for v, root in VARIANTS.items():
        for dev, run in G48.SETS.items():
            p = Path(root) / dev / f"step4_{v}" / "final" / "status.json"
            for r in json.loads(p.read_text(encoding="utf-8")) if p.exists() else []:
                kinds[(v, dev, r["seed"])] = r["repair_kinds"]
    for kind, col in REASK.items():
        df[col] = [kinds[k].get(kind, 0) if (k := (r["variant"], r["set"], r["seed"])) in kinds else float("nan") for r in df.to_dict("records")]
    return df


def main_rows(df):
    """The pick-rule frame: main view, one row per variant x set x seed, with `placed` (share of GT columns placed)."""
    d = df[(df["l2_view"] == MAIN) & (~df["finished"] | (df["gt_view"] == S48.VIEW))].copy()
    d["placed"] = [S48.share(r, "gt_columns_placed") if r["finished"] else float("nan") for r in d.to_dict("records")]
    return d


def table_md(d):
    shares = ("table_f1", "grouping_f1", "gt_columns_placed", "pk_right_b")
    metrics = [("chains finished", None), ("tables per chain", "tables"), ("table F1", "table_f1"), ("grouping F1", "grouping_f1"),
               ("GT columns placed", "gt_columns_placed"), ('columns in "unused"', "unused"), ("internet in a hotel table (seeds)", "internet_hotel"),
               ("parking in a hotel table (seeds)", "parking_hotel"), ("PK right, rule b", "pk_right_b"), ("calls per chain", "calls"),
               ("prompt tokens per chain", "prompt_tokens"), ("output tokens per chain", "output_tokens"), ("p2_reask per chain", "reask"),
               ("p2_reask_failed per chain", "reask_failed"), ("p2_reask_missing per chain", "reask_missing")]
    lines = [f"| dev50 / dev50b, mean (range), {S48.VIEW}, {MAIN} | " + " | ".join(VARIANTS) + " |", "|---" * (len(VARIANTS) + 1) + "|"]
    for label, k in metrics:
        cells = []
        for v in VARIANTS:
            per = []
            for dev in G48.SETS:
                ok = d[(d["variant"] == v) & (d["set"] == dev) & d["finished"]].to_dict("records")
                if not ok:
                    per.append("not run")
                elif k is None:
                    per.append(f"{len(ok)}/{len(SEEDS)}")
                elif k in ("internet_hotel", "parking_hotel"):
                    per.append(f"{sum(bool(r[k]) for r in ok)}/{len(ok)}")
                elif k.startswith("reask"):
                    per.append(S48.cell([r[k] for r in ok], "{:.1f}"))
                else:
                    per.append(S48.cell([S48.share(r, k) if k in shares else r[k] for r in ok],
                                        "{:.3f}" if k in shares else "{:.1f}" if k in ("tables", "unused") else "{:,.0f}"))
            cells.append(" / ".join(per))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def pick_md(chosen, res):
    lines = ["| variant | rule 1 (every seed, both sets) | rule 2 (placed within 0.05 of best) | table F1 + grouping F1, sum over sets |", "|---|---|---|---|"]
    for v, r in res.items():
        flag = lambda x: ("pass" if x[0] else "FAIL") + ("" if x[0] else f": {x[1]}")  # noqa: E731
        lines.append(f"| {v} | {flag(r['rule1'])} | {flag(r['rule2'])} | {'n/a' if r['score'] is None else f'{r['score']:.3f}'} |")
    return "\n".join(lines) + f"\n\nChosen: {chosen or 'none (no variant passes rules 1 and 2)'}."


def main():
    gt = SC43.load_gt(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    names = SG.gt_names(gt)
    prep = {dev: V1.prepare(dev, run, names, VARIANTS, L2MAP) for dev, run in G48.SETS.items()}
    hotel = hotel_entities(prep)
    parts = []
    for view in V1.VIEWS:
        opts = V1.opts_for(prep, view, L2MAP)
        parts.append(V1.placement(gt, prep, S48.rows(gt, opts=opts, variants=VARIANTS), opts, VARIANTS, hotel).assign(l2_view=view))
    df = reasks(pd.concat(parts, ignore_index=True))
    df.to_csv(OUT / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
    d = main_rows(df)
    chosen, res = PK.pick(d, SEEDS)
    fig = S48.figure(gt, "dev50b", 0, variants={v: VARIANTS[v] for v in [chosen or "BM"]}, out=OUT / "fig_schema_dev50b_s0.png")
    md = ["# wf_v4.9 V3: Step 4 variants with scorable loop-2 columns and the pick rule", "",
          f"Hotel entities (read from the loop-2 internet / parking columns): {', '.join(f'{k}: {sorted(v)}' for k, v in hotel.items())}. "
          "A hotel table = its main entity (strictly most common column source entity) is a hotel entity. BM tokens = B (replay of cached B).", "",
          table_md(d), "", "## Pick rule", "", pick_md(chosen, res), "", f"Figure: {fig.name} ({chosen or 'BM'}, dev50b seed 0, next to the GT)."]
    (OUT / "v3.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
