"""wf_v4.7 Z6: main-claim scoring of the Z4 loop-2 runs with the v4.6 scorer (scripts/mainclaim_v46.py, rules v1.3, unchanged).

python scripts/mainclaim_v47.py [--runs 1,2,3]  -> results/wf_v47/z6/run<r>/<set>/{compare.md, compare.csv, human_check_sheet.csv, ...}
                                                   results/wf_v47/z6/z6.md   (found per run, mean and range)
Loop 1 = results/wf_v46/y3/<set> (Z4 copied the same loop-1 files). Loop 2 = the Z4 run's evidence clusters that became a new column
(columns_l2.json status new); the clusters the duplicate check joined to a loop-1 column are left out. Scoring only, never fed back.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import mainclaim_v46 as M46  # noqa: E402

Z4 = ROOT / "results" / "wf_v47" / "z4"
OUT = ROOT / "results" / "wf_v47" / "z6"
SETS = tuple(M46.RUN_OF)
ORIG_LOOP2_FILE = M46.loop2_file


def new_cluster_ids(l2):
    cols = json.loads((l2 / "columns_l2.json").read_text(encoding="utf-8"))
    return {cid for cs in cols.values() for c in cs if c.get("status") == "new" for cid in c["clusters"]}


def loop2_file(r):
    """M46.loop2_file over the Z4 run r clusters, keeping only the clusters of new columns."""
    def f(_run_dir, emap, out):
        l2 = Z4 / f"run{r}" / out.name / "loop2"
        p = ORIG_LOOP2_FILE(Z4 / f"run{r}" / out.name, emap, out)
        keep = new_cluster_ids(l2)
        rows = [c for c in json.loads(p.read_text(encoding="utf-8")) if c["id"] in keep]
        p.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        return p
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default="1,2,3")
    a = ap.parse_args()
    rows = []
    for r in (int(x) for x in a.runs.split(",")):
        M46.loop2_file = loop2_file(r)
        try:
            for s in SETS:
                M46.run(s, out=OUT / f"run{r}")
                cmp = pd.read_csv(OUT / f"run{r}" / s / "compare.csv", keep_default_na=False)
                rows += [{"run": r, "set": s, **x} for x in cmp.to_dict("records")]
        finally:
            M46.loop2_file = ORIG_LOOP2_FILE
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "z6_runs.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(df.to_string())


if __name__ == "__main__":
    main()
