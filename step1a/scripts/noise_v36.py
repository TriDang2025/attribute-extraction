"""wf_v3.6 W3 tasks 13-15: unmatched mention kinds, model-free noise at L2, noise at L2 for every variant. No LLM.

python scripts/noise_v36.py --dir33 ../attribute-extraction-wf-v3.3/step1a/results/loop1_v33
        [--run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 --gt results/loop1_v35
         --out results/loop1_v36 --invalid config/invalid_runs.json --variants "A r1,A r2,..."]
Writes <out>/unmatched_kinds.{md,csv}, unmatched_other_to_rate.csv, unmatched_other_rubric.md, noise_mwoz.{md,csv},
noise_l2.{md,csv}. The v3.6 batch decisions use `noise_l2_rows` on one more {ent: EntityData} bundle (see load_bundles).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import v34_data, v35_data  # noqa: E402
from score_v35 import SHOWN  # noqa: E402

OTHER_RUBRIC = """# Unmatched mentions of kind "other": rubric (wf_v3.6)

Each row is a value found in a hotel / restaurant / train dialogue, with its turn (the value in [[ ]]). MultiWOZ has no
span label for it. Say what the value is. Answer with exactly one label:

- **entity_value**: a real attribute value of the thing discussed (a name, place, area, price range, food, time).
- **generic**: a general word or description that is not a value of one attribute (a type word, "the place").
- **request**: a phrase that asks for information.
- **broken**: a fragment or a span that cuts a word or phrase.

Answer file: `row,label`.
"""


def load_bundles(run, dir32, dir31, dir33):
    """(shared, [data v3.2, data v3.3]): the same bundles score_v35 scores. Append a v3.6 bundle to the list to score
    the new batch decisions with the same functions."""
    shared, data = v34_data.load_all(run, dir32, dir31)
    data33, notes = v35_data.load_v33(shared, data, dir33, dir32)
    for n in notes:
        print("note:", n)
    return shared, [data, data33]


def turn_lookup(docs):
    def get(dialogue_id, turn):
        speaker, text, _ = v34_data.turn_context(docs[dialogue_id], turn)
        return speaker, text
    return get


def write_md(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def part_unmatched(run, gt_dir, out):
    e = MN.load(run / "spans")
    docs, _, _ = MN.load_shared(run)
    matched = pd.read_csv(gt_dir / "mwoz_match.csv", keep_default_na=False, encoding="utf-8")
    df = NV.unmatched_table(e.mentions, matched, turn_lookup(docs))
    summary = NV.unmatched_summary(df)
    summary.to_csv(out / "unmatched_kinds.csv", index=False, encoding="utf-8", lineterminator="\n")
    lines = ["# wf_v3.6 unmatched mentions by kind", "",
             f"The {len(df)} dev50 mentions with no MultiWOZ 2.2 match (match == none in mwoz_match.csv), grouped by "
             "rules on the value text (shapes first, then closed word lists, else other). Examples show the value "
             "in [[ ]].", "", "| kind | n | share | example 1 | example 2 |", "|---|---|---|---|---|"]
    lines += [f"| {r['kind']} | {r['n']} | {r['share']:.3f} | {r['example_1']} | {r['example_2']} |"
              for _, r in summary.iterrows()]
    write_md(out / "unmatched_kinds.md", "\n".join(lines) + "\n")
    NV.other_sheet(df).to_csv(out / "unmatched_other_to_rate.csv", index=False, encoding="utf-8", lineterminator="\n")
    write_md(out / "unmatched_other_rubric.md", OTHER_RUBRIC)
    print(summary[["kind", "n", "share"]].to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=Path("results/graph_v22_dev50"))
    ap.add_argument("--dir32", type=Path, default=Path("results/loop1_v32"))
    ap.add_argument("--dir31", type=Path, default=Path("results/loop1_v31"))
    ap.add_argument("--dir33", required=True, type=Path)
    ap.add_argument("--gt", type=Path, default=Path("results/loop1_v35"), help="folder with mwoz_match.csv, gt_levels.csv")
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v36"))
    ap.add_argument("--invalid", type=Path, default=RN.INVALID_RUNS_PATH)
    ap.add_argument("--variants", default=",".join(SHOWN))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    part_unmatched(a.run, a.gt, a.out)

    shared, bundles = load_bundles(a.run, a.dir32, a.dir31, a.dir33)
    gt = v34_data.read_gt_levels(a.gt / "gt_levels.csv")
    extra = NV.prepare_extra(shared, bundles, a.gt, a.dir32, gt_levels=gt)

    sets = NV.noise_sets(bundles[0], extra)
    sets.to_csv(a.out / "noise_mwoz.csv", index=False, encoding="utf-8", lineterminator="\n")
    write_md(a.out / "noise_mwoz.md", NV.noise_sets_md(sets))

    invalid = RN.invalid_runs(a.invalid)
    rows = pd.concat([NV.noise_l2_rows(b, extra, a.variants.split(","), invalid) for b in bundles], ignore_index=True)
    rows.to_csv(a.out / "noise_l2.csv", index=False, encoding="utf-8", lineterminator="\n")
    table = NV.noise_l2_table(rows)
    write_md(a.out / "noise_l2.md", NV.noise_l2_md(table, invalid))
    print(table[["variant", "noise_marked_kn", "precision_kn", "marked_real", "marked_mixed"]].to_string(index=False))


if __name__ == "__main__":
    main()
