"""T1 (GT_V35_CONTRACT.md): MultiWOZ 2.2 span labels -> one row per labelled span.

python scripts/multiwoz_span_labels.py --mwoz C:/Users/nguye/data/MultiWOZ_2.2 --ids results/graph_v22_dev50/spans/mentions.csv --out data/mwoz22_spans.csv
(--all instead of --ids: every dialogue).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import gt_ext as GT  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mwoz", required=True)
    ap.add_argument("--ids", help="mentions.csv; only its dialogue_id values are labelled")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.all and not a.ids:
        ap.error("give --ids or --all")
    ids = None if a.all else set(pd.read_csv(a.ids, usecols=["dialogue_id"])["dialogue_id"])
    dialogues, acts = GT.load_mwoz(a.mwoz, ids)
    spans = GT.span_table(dialogues, acts)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    spans.to_csv(a.out, index=False, encoding="utf-8")
    print(f"{len(dialogues)} dialogues, {len(spans)} rows -> {a.out}")
    print(spans.groupby(["speaker", "source"]).size().to_string())


if __name__ == "__main__":
    main()
