"""T3 missing-attribute analysis -> results/loop1_check/missing_attributes.csv (LOOP1_CONTRACT.md).

python scripts/loop1_missing.py [--run results/graph_v22_dev50] [--out results/loop1_check]
Recall is recomputed on the frozen <run>/spans mentions; GLiNER coverage uses the raw GLiNER cache of the run
(generic labels, score >= the pipeline threshold 0.5, before the span filter)."""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gliner_labels as GL  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import missing as MS  # noqa: E402
from s1a import recall as RC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SPAN_THR = 0.5  # export_mentions.span_inputs


def raw_spans(run):
    have = GL.read_cache(run / "cache" / "gliner_labels" / "gliner_turn_generic.jsonl")
    return pd.DataFrame([(d, s, e) for d, spans in have.items() for s, e, _, score in spans if score >= SPAN_THR],
                        columns=["dialogue_id", "char_start", "char_end"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--out", default="results/loop1_check")
    a = ap.parse_args()
    run, out = ROOT / a.run, ROOT / a.out
    _, gold_values, attrs = MN.load_shared(run)
    m = MN.load(run / "spans").mentions
    raw = raw_spans(run)
    raw = raw[raw["dialogue_id"].isin(set(gold_values["dialogue_id"]))]
    res = MS.missing_table(m, gold_values, RC.recall_table(m, gold_values, attrs), raw)
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "missing_attributes.csv", index=False)
    print(f"{len(raw)} raw GLiNER spans, {len(m)} mentions after the filter")
    print(res["cause"].value_counts().to_string())
    print(f"wrote {out / 'missing_attributes.csv'} ({len(res)} attributes)")


if __name__ == "__main__":
    main()
