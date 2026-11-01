"""wf_v3.6 W3 task 16: the blind L2 name-rating sheet for the Haiku raters. No LLM.

python scripts/names_l2_v36.py --dir33 ../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
Writes <out>/names_to_rate_l2.csv (rater copy: no variant, shuffled), names_to_rate_l2_key.csv (row -> join keys,
variants), names_l2_rubric.md. After rating, save the answers as names_l2_rater1.csv / names_l2_rater2.csv (row,label)
in <out> and score with the names switch `l2rated` (score_rules.load_extra(..., l2_dir=<out>)).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import names_l2 as NL  # noqa: E402
from s1a import v34_data  # noqa: E402
from noise_v36 import load_bundles  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=Path("results/graph_v22_dev50"))
    ap.add_argument("--dir32", type=Path, default=Path("results/loop1_v32"))
    ap.add_argument("--dir31", type=Path, default=Path("results/loop1_v31"))
    ap.add_argument("--dir33", required=True, type=Path)
    ap.add_argument("--gt", type=Path, default=Path("results/loop1_v35"))
    ap.add_argument("--mwoz", required=True, type=Path, help="MultiWOZ 2.2 folder (schema.json)")
    ap.add_argument("--tear-map", type=Path, default=Path("config/tear_to_mwoz.json"))
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v36"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    _, bundles = load_bundles(a.run, a.dir32, a.dir31, a.dir33)
    gt = v34_data.read_gt_levels(a.gt / "gt_levels.csv")
    tear_map = {k: v for k, v in json.loads(a.tear_map.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    schema = json.loads((a.mwoz / "schema.json").read_text(encoding="utf-8"))
    slot_desc = {s["name"]: s["description"] for svc in schema for s in svc["slots"]}
    rater, key = NL.rating_sheet(NL.l2_group_rows(bundles, gt), tear_map, slot_desc)
    rater.to_csv(a.out / "names_to_rate_l2.csv", index=False, encoding="utf-8", lineterminator="\n")
    key.to_csv(a.out / "names_to_rate_l2_key.csv", index=False, encoding="utf-8", lineterminator="\n")
    (a.out / "names_l2_rubric.md").write_text(NL.RUBRIC, encoding="utf-8", newline="\n")
    nodesc = int((rater["l2_slot_description"] == "").sum())
    print(f"names_to_rate_l2.csv: {len(rater)} rows ({nodesc} without a schema description), key rows {len(key)}")


if __name__ == "__main__":
    main()
