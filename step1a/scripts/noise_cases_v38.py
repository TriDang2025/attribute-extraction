"""wf_v3.8 W3 (task 12): the noise misses and false noise marks of A s012 on dev50b (and a count line for dev50). No LLM.

python scripts/noise_cases_v38.py --dir33 ../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--out results/loop1_v38/noise  + the score_t14_v37 arguments]
Runs: dev50b = results/graph_v22_dev50b with the v3.7 batch (A s0 / s1 / s2 + the vote A s012, run key v22d50b), GT
results/loop1_v37/dev50b/gt; dev50 = the existing A r1 / A r2 / A s2 + A s012. Checks first that dev50b gives noise caught 5/9
and 5 of 15 marks (v3.7 t14.md) and stops otherwise.
Writes <out>/noise_cases_dev50b.csv and noise_cases.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

import score_t14_v37 as T14  # noqa: E402
from s1a import noise_cases_v38 as NC  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402

EXPECTED = {"noise_n": 9, "noise_marked": 5, "marked_n": 15, "marked_noise": 5}   # v3.7 t14.md, dev50b v2.2 A s012
RUN_B, KEY_B, GT_B = Path("results/graph_v22_dev50b"), "v22d50b", Path("results/loop1_v37/dev50b/gt/gt_levels.csv")
GT_A = Path("results/loop1_v35/gt_levels.csv")


def pooled(bundle, gt, label):
    """{noise_n, noise_marked, marked_n, marked_noise} summed over the entities (noise_v36.noise_l2_rows)."""
    rows = NV.noise_l2_rows(bundle, {"gt_levels": gt}, [label])
    return {k: int(rows[k].sum()) for k in EXPECTED}


def main():
    a = T14.parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    gt_b, gt_a = VD.read_gt_levels(GT_B), VD.read_gt_levels(GT_A)
    shared, bundle, _ = T14.load_new(a, RUN_B, KEY_B, [])
    got = pooled(bundle, gt_b, NC.VOTE)
    print("dev50b A s012:", got, "expected", EXPECTED)
    if got != EXPECTED:
        sys.exit("cannot reproduce the v3.7 numbers (5/9 noise caught, 5/15 marks noise); stopping")
    cases = NC.build_cases(bundle, gt_b, shared)
    shared_a, bundle_a, _ = T14.load_old(a, [])
    cases_a = NC.build_cases(bundle_a, gt_a, shared_a, orders=T14.OLD_ORDERS)
    na = pooled(bundle_a, gt_a, NC.VOTE)["noise_n"]
    lines = [NC.summary_line("dev50b (A s012, v2.2)", cases, got["noise_n"]),
             NC.summary_line("dev50 (A s012, v2.2, contrast)", cases_a, na)]
    write_csv(NC.csv_frame(cases), a.out / "noise_cases_dev50b.csv")
    write(a.out / "noise_cases.md", NC.cases_md(cases, "wf_v3.8 noise misses and false noise marks of A s012 on dev50b", lines))
    print("\n".join(lines))
    print(pd.Series(NC.guess_summary(cases)).to_dict())


if __name__ == "__main__":
    main()
