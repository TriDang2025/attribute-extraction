"""wf_v3.6: column precision (T41) for every score_v35.SHOWN variant plus F, and the task-11 re-score of v3.3 F (de-lexicalised
prompts, broken map) next to E seed 0. No LLM, no models.

python scripts/precision_v36.py --dir33 <attribute-extraction-wf-v3.3/step1a/results/loop1_v33>
        [--f2-dir results/loop1_v36/colab] [--tear-columns results/loop1_v36/tear_columns.csv] [--out results/loop1_v36]
Writes <out>/column_precision.{md,csv} (T41, L1 and L2, rules v1), <out>/f_delex_L2.{md,csv} (task 11: extras by kind and the
L2 scores of E s0, F s0 and, with --f2-dir, F2 s0), <out>/extras_by_level_v36.csv (T38 rows behind both).
F is marked invalid (its map pulled generic words). F2 hook: pass the v3.6 Colab folder; a missing F2 is skipped with a note.
--tear-columns: tear_columns.csv of scripts/score_tear_v36.py adds a TEAR row to the precision table.
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import checks_v35 as CK  # noqa: E402
from s1a import precision_v36 as PR  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import tear_cols as TC  # noqa: E402
from s1a import v34_data, v35_data  # noqa: E402
from checks_v35 import prepare_extra  # noqa: E402  (scripts/checks_v35.py)
from score_v35 import HEAD, SHOWN, variant_cells  # noqa: E402

INVALID_F = {"F s0": "broken delex map: it pulled generic words (hotel, restaurant, travel time) from name clusters"}
COMPARE = ["E s0", "F s0", "F2 s0"]


def extras_rows(data, labels, levels, extra):
    """T38 rows (extras_by_level + ent, variant) of the given labels of every entity of `data`."""
    rules = SR.Rules.default()
    return [CK.extras_by_level(ed, v, levels, rules, extra).assign(ent=ed.ent, variant=v)
            for ed in data.values() for v in labels if v in ed.variants]


def score_rows(data, labels, shared, extra):
    """Score rows (COLS of score_v35, level 2, rules v1) of the given labels."""
    rules = replace(SR.Rules.default(), gt="L2")
    rows = []
    for ed in PR.only(data, labels).values():
        rows += [{"level": 2, **r} for r in SR.score_entity(ed, shared, rules, extra)]
    return pd.DataFrame(rows)


def f_delex_md(table, scores, notes):
    lines = [PR.kinds_md("wf_v3.6 task 11: F de-lexicalisation re-scored at L2 (rules v1)", table, notes).rstrip(), "",
             "## Scores at L2", "", "| variant | " + " | ".join(HEAD) + " |", "|---|" + "---|" * len(HEAD)]
    for v in COMPARE:
        g = scores[scores["variant"] == v]
        if len(g):
            tag = " (invalid)" if v in INVALID_F else ""
            lines.append(f"| {v}{tag} | " + " | ".join(variant_cells(g)) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=Path("results/graph_v22_dev50"))
    ap.add_argument("--dir32", type=Path, default=Path("results/loop1_v32"))
    ap.add_argument("--dir31", type=Path, default=Path("results/loop1_v31"))
    ap.add_argument("--dir33", required=True, type=Path)
    ap.add_argument("--f2-dir", type=Path, default=None)
    ap.add_argument("--levels", type=Path, default=Path("results/loop1_v35/gt_levels.csv"))
    ap.add_argument("--tear-columns", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v36"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    levels = v34_data.read_gt_levels(a.levels)
    shared, data = v34_data.load_all(a.run, a.dir32, a.dir31)
    data33, notes = v35_data.load_v33(shared, data, a.dir33, a.dir32)
    data33, n = PR.seed0_variants(data33, shared, a.dir33, [("E", "e"), ("F", "f")])
    notes += n
    if a.f2_dir:
        data33, n = PR.seed0_variants(data33, shared, a.f2_dir, [("F2", "f2")])
        notes += n
    ex32 = prepare_extra(shared, data, Path("results/loop1_v34"), a.dir32)
    ex33 = prepare_extra(shared, data33, Path("results/loop1_v34"), a.dir32)

    labels32 = [v for v in SHOWN if v in next(iter(data.values())).variants]
    labels33 = [v for v in SHOWN + ["F s0"] + COMPARE if v in next(iter(data33.values())).variants and v not in labels32]
    rows = pd.concat(extras_rows(data, labels32, levels, ex32) + extras_rows(data33, list(dict.fromkeys(labels33)),
                                                                           levels, ex33), ignore_index=True)
    rows.to_csv(a.out / "extras_by_level_v36.csv", index=False, encoding="utf-8", lineterminator="\n")

    # T41
    order = [v for v in SHOWN + ["E s0", "F s0", "F2 s0"] if v in set(rows["variant"])]
    table = PR.precision_table(rows, RN.invalid_runs(), order)
    table["variant"] = [f"{v} (invalid)" if v in INVALID_F else v for v in table["variant"]]
    tear_note = []
    if a.tear_columns and a.tear_columns.exists():
        tear = pd.read_csv(a.tear_columns, dtype=str, keep_default_na=False)
        t_rows = TC.extras_rows(tear)
        table = pd.concat([table, PR.precision_table(t_rows)], ignore_index=True)
        tear_note = [f"TEAR row from {a.tear_columns.name} (value + name mapping, tear_cols.py)"]
    table.to_csv(a.out / "column_precision.csv", index=False, encoding="utf-8", lineterminator="\n")
    inv = [f"{r['variant']} {r['ent']} left out ({r.get('reason', 'invalid')})" for r in RN.invalid_runs()]
    inv += [f"{v} is shown but invalid: {why}" for v, why in INVALID_F.items()]
    (a.out / "column_precision.md").write_text(PR.precision_md(table, inv + tear_note), encoding="utf-8", newline="\n")

    # task 11
    kinds = rows[rows["variant"].isin(COMPARE)]
    ktable = CK.extras_table(kinds)
    ktable.index = [f"{v} (invalid)" if v in INVALID_F else v for v in ktable.index]
    scores = score_rows(data33, [v for v in COMPARE if v in data33[next(iter(data33))].variants], shared, ex33)
    ktable.to_csv(a.out / "f_delex_L2.csv", encoding="utf-8", lineterminator="\n")
    knotes = [f"F: {INVALID_F['F s0']}.", "E s0 = same prompt without delex; both are one order (seed 0), no gate or split.",
              "Extras = distinct final attributes per kind (T38); the kinds are the GT levels of the attribute's majority label."]
    knotes += [f"Note: {x}" for x in notes if "skipped" in x and "F2" in x]
    (a.out / "f_delex_L2.md").write_text(f_delex_md(ktable, scores, knotes), encoding="utf-8", newline="\n")
    print(table.to_string(index=False))
    print(ktable.to_string())
    for x in notes:
        print("note:", x)


if __name__ == "__main__":
    main()
