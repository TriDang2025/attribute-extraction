"""wf_v4.1 task 7: table of the v0 Step-4 scores with "GT columns placed" next to grouping F1 and keys under rule (a) and (b).

python scripts/t7_table_v41.py  -> results/wf_v41/t7_scores.md
Reads results/wf_v4/colab/final/scores.csv (assemble_v4.py --score; its e rows are unrated and skipped), results/wf_v4/scores/baselines_df.csv
(d, f) and results/wf_v4/scores/e_scores.csv (e with the rated columns, task 6).
Mean over seeds s0-s2 (e: versions v0-v2); counts are summed over the runs.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "wf_v4"
OUT = ROOT / "results" / "wf_v41" / "t7_scores.md"
ORDER = ["a", "b", "c1", "c2", "d", "e", "f"]


def rows():
    for f in (RES / "colab" / "final" / "scores.csv", RES / "scores" / "baselines_df.csv", RES / "scores" / "e_scores.csv"):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if not (f.parent.name == "final" and r["schema"].startswith("e_")):
                yield r


def kn(rs, m):
    k, n = sum(int(r[f"{m}_k"]) for r in rs), sum(int(r[f"{m}_n"]) for r in rs)
    return f"{k}/{n} ({k / n:.3f})" if n else "n/a"


def main():
    groups = defaultdict(list)
    for r in rows():
        inp = r["schema"].split("_")[0]
        if inp in ORDER and r["reachable_only"] == "False":
            groups[(inp, r["set"])].append(r)
    lines = ["# wf_v4.1 task 7: v0 scores with GT columns placed and two key rules", "",
             "Full GT (not reachable-only). Counts summed over the runs of each row (3 seeds; e: 3 versions; d, f: 1 run).",
             "Key rule (a) = current: the PK maps to the GT PK. Rule (b) = (a), or the PK is one new id and the table also holds every GT PK column.", "",
             "| input | set | runs | grouping F1 (mean) | GT columns placed | table F1 (mean) | keys (a) | keys (b) |", "|---|---|---|---|---|---|---|---|"]
    for inp in ORDER:
        for s in ("dev50", "dev50b"):
            rs = groups.get((inp, s))
            if not rs:
                continue
            gf = sum(float(r["grouping_f1"] or 0) for r in rs) / len(rs)
            tf = sum(float(r["table_f1"] or 0) for r in rs) / len(rs)
            lines.append(f"| {inp} | {s} | {len(rs)} | {gf:.3f} | {kn(rs, 'gt_columns_placed')} | {tf:.3f} | {kn(rs, 'pk_right')} | {kn(rs, 'pk_right_b')} |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("->", OUT)


if __name__ == "__main__":
    main()
