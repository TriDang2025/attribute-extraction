"""Rule labels and a manual-labelling sheet for one run.

python scripts/label_sheet.py --run results/graph_dev50 --input spans|gold [--merge FILLED.csv]
  -> <run>/<input>/{labels.csv, label_sheet.csv}; --merge folds a filled sheet into labels.csv.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import labels as L  # noqa: E402
from s1a import mentions as M  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--input", required=True, choices=["spans", "gold"])
    ap.add_argument("--merge", help="filled label_sheet CSV")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    d = Path(a.run) / a.input
    if a.merge:
        labels = L.merge_sheet(pd.read_csv(d / "labels.csv", keep_default_na=False),
                               pd.read_csv(a.merge, keep_default_na=False))
        labels.to_csv(d / "labels.csv", index=False)
        print(labels["label"].value_counts().to_string())
        return
    mentions = M.load(d).mentions
    labels = L.gold_labels(mentions)
    labels.to_csv(d / "labels.csv", index=False)
    sh = L.sheet(mentions, labels, a.n, a.seed)
    sh.to_csv(d / "label_sheet.csv", index=False)
    print(labels["label"].value_counts().to_string(), f"\nsheet rows: {len(sh)}")


if __name__ == "__main__":
    main()
