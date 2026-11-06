"""wf_v4 task 7: error list of the main Step-4 runs on dev50 -> results/wf_v4/scores/errors_dev50.{md,csv}.

python scripts/errors_v4.py [--runs a_dev50_s0,b_dev50_s0] [--set dev50]
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import score_v4 as SC  # noqa: E402
from s1a import step4_errors as E  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_score as S  # noqa: E402

FINAL = ROOT / "results" / "wf_v4" / "colab" / "final"
OUT = ROOT / "results" / "wf_v4" / "scores"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="a_dev50_s0,b_dev50_s0")
    ap.add_argument("--set", default="dev50")
    a = ap.parse_args()
    gt = SC.load(ROOT / "gt" / "schema_gt_v1.yaml", ROOT / "results" / "wf_v4" / "gt", [a.set])
    hand = ROOT / "handover"
    full = G.map_handover(hand, a.set, SC.GT_LEVELS[a.set], G.gt_names(gt))
    runs, rows = {}, []
    for run in a.runs.split(","):
        schema = json.loads((FINAL / run / "canonical.json").read_text(encoding="utf-8"))
        mapping = S.map_columns(schema, a.set, hand, SC.GT_LEVELS[a.set], gt)
        runs[run] = E.list_errors(schema, gt, a.set, mapping, full)
        rows += [{"run": run, "design": runs[run]["design"], **e, "sources": " ".join(e["sources"])} for e in runs[run]["errors"]]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"errors_{a.set}.md").write_text(E.to_markdown(runs), encoding="utf-8", newline="\n")
    with open(OUT / f"errors_{a.set}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run", "design", "step", "kind", "text", "sources", "step3", "step3_reason"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for run, r in runs.items():
        print(run, r["design"], len(r["errors"]), json.dumps(E.count_table(r["errors"])))


if __name__ == "__main__":
    main()
