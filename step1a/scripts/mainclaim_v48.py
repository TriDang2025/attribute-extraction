"""wf_v4.8 W1: score loop 1 and loop 1 + 2 (v4.7 run 1) with the filled human-check sheets (scorer v4.6 / rules v1.3, unchanged).

python scripts/mainclaim_v48.py  -> results/wf_v48/w1/<set>/{compare.md, compare.csv, human_check_sheet.csv, human_check_key.csv, ...}
                                    results/wf_v48/w1/w1.md, w1.csv
Input: results/wf_v48/w1/sheets/<set>_human_check_sheet.csv (filled real + same_as; same rows as results/wf_v47/z6/run1/<set>/).
The sheet is put where the scorer reads it, so mainclaim_v41.merge_answers keeps the answers (and fails if the rows differ).
same_as groups: s1a/human_groups_v48.py. Scoring only, never fed back.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v47 as M47  # noqa: E402
from s1a import human_groups_v48 as H  # noqa: E402

OUT = ROOT / "results" / "wf_v48" / "w1"
SHEETS = OUT / "sheets"
RUN = 1
SOURCES = {"loop1": ("loop1",), "loop2": ("loop1", "loop2")}   # loop 1 + 2 = all rows


def score_set(set_name):
    """Run the v4.7 run-1 scoring into OUT/<set> with the filled sheet; return the merged sheet + key rows (with same_as)."""
    d = OUT / set_name
    d.mkdir(parents=True, exist_ok=True)
    filled = pd.read_csv(SHEETS / f"{set_name}_human_check_sheet.csv", dtype=str, keep_default_na=False)
    # mainclaim_v46.fill_empty_examples adds the "(no mentions)" values after merge_answers checks the rows, so blank them first
    blank = filled["example_values"].str.endswith("(no mentions)")
    filled.assign(example_values=filled["example_values"].mask(blank, "")).drop(columns="same_as").to_csv(
        d / "human_check_sheet.csv", index=False, encoding="utf-8", lineterminator="\n")
    M46.loop2_file = M47.loop2_file(RUN)
    try:
        M46.run(set_name, out=OUT)
    finally:
        M46.loop2_file = M47.ORIG_LOOP2_FILE
    key = pd.read_csv(d / "human_check_key.csv", dtype=str, keep_default_na=False)
    sheet = pd.read_csv(d / "human_check_sheet.csv", dtype=str, keep_default_na=False)
    if not sheet.equals(filled.drop(columns="same_as")):
        raise ValueError(f"{set_name}: the rescored sheet differs from the filled one")
    sheet["same_as"] = filled["same_as"]          # the scorer writes SHEET_COLS only; keep the human column
    sheet.to_csv(d / "human_check_sheet.csv", index=False, encoding="utf-8", lineterminator="\n")
    return sheet.merge(key[["id", "source", "item_id", "name_match"]], on="id")


def main():
    rows = []
    for s in M47.SETS:
        merged = score_set(s)
        cmp = pd.read_csv(OUT / s / "compare.csv", keep_default_na=False)
        for src, keep in SOURCES.items():
            c = cmp[(cmp["source"] == src) & (cmp["entity"] == "all")].iloc[0]
            part = merged[merged["source"].isin(keep)].to_dict("records")
            rows.append({"set": s, "source": src, "found_k": c["found_k"], "found_human_k": c["found_human_k"], "gold_n": c["gold_n"],
                         **H.summary(part)})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "w1.csv", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / "w1.md").write_text("# wf_v4.8 W1: loop 1 and loop 1 + 2 (v4.7 run 1) with the human check\n\n" + df.to_markdown(index=False) + "\n",
                               encoding="utf-8", newline="\n")
    print(df.to_string())


if __name__ == "__main__":
    main()
