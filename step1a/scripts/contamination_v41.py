"""wf_v4.1 task 5: contamination probe (MultiWOZ schema from memory, no dialogues).

python scripts/contamination_v41.py --build
    writes results/wf_v41/contamination/prompts/contamination.{txt,schema.json} (the prompt names the dataset on purpose)
python scripts/contamination_v41.py --score <answer.json> [--out results/wf_v41/contamination]
    answer = the model's JSON (the dialogues-only (e) shape; a .jsonl or a record with "parsed" also works); writes
    <out>/scores.{csv,md}: GT tables named, GT columns named (k/n), grouping F1, keys, relationships, unmatched columns.
Run the prompt on the Nov 16 Colab (guided JSON with the schema file); see s1a/contamination_v41.py.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from s1a import contamination_v41 as C  # noqa: E402
from s1a.step4_gt import load_gt  # noqa: E402

OUT = ROOT / "results" / "wf_v41" / "contamination"
GT = ROOT / "gt" / "schema_gt_v1.yaml"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--score", type=Path, metavar="ANSWER")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if not a.build and not a.score:
        ap.error("give --build or --score <answer.json>")
    if a.build:
        text, schema = C.build()
        d = a.out / "prompts"
        d.mkdir(parents=True, exist_ok=True)
        (d / "contamination.txt").write_text(text, encoding="utf-8", newline="\n")
        (d / "contamination.schema.json").write_text(json.dumps(schema, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {d / 'contamination.txt'} and .schema.json")
    if a.score:
        sc = C.score_answer(C.load_answer(a.score), load_gt(GT))
        a.out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([C.flat(sc)]).to_csv(a.out / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
        (a.out / "scores.md").write_text(C.report_md(sc), encoding="utf-8", newline="\n")
        print(C.report_md(sc))


if __name__ == "__main__":
    main()
