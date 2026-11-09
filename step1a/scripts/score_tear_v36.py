"""wf_v3.6 TEAR scorer: map the columns of a TEAR run on dev50 to MultiWOZ 2.2 attributes and count its extras.

python scripts/score_tear_v36.py --tear ../tear/results/conversation_dev50/te_tear_Lfull_s0.jsonl
python scripts/score_tear_v36.py --set dev50b --tear ../tear/results/conversation_dev50b/te_tear_Lfull_s0.jsonl --out results/wf_v41/tear_dev50b
        (wf_v4.1: --set picks the default spans file of the set and the report title)
        [--spans data/mwoz22_spans.csv --map config/tear_to_mwoz.json --db ../chunking/data/MULTIWOZ2.4.zip --out results/loop1_v36]
Value mapping and name mapping: see s1a/tear_cols.py. Writes <out>/tear_names_to_rate.csv (blind sheet for 2 raters; labels come
back as tear_names_rater1.csv / tear_names_rater2.csv with columns row_id,label, read on the next run), tear_columns.csv,
tear_label_disagree.csv, tear_extras.csv and tear_extras.md (extras_table.md format). Rows of dialogues without spans are skipped.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import checks_v35 as CK  # noqa: E402
from s1a import gt_ext as G  # noqa: E402
from s1a import precision_v36 as PR  # noqa: E402
from s1a import tear_cols as TC  # noqa: E402

SPANS = {"dev50": Path("data/mwoz22_spans.csv"), "dev50b": Path("results/loop1_v37/dev50b/gt/mwoz22_spans.csv")}


def score(rows, spans, tear_map, db_idx=None, raters=()):
    """(columns, sheet, disagree, table): columns = tear_cols.final_columns, sheet = the name sheet, disagree = label
    disagreements, table = extras_table of the columns (variant TEAR). Rows of dialogues without spans are skipped."""
    known = {G.dialogue_key(d) for d in spans["dialogue_id"]}
    rows = [r for r in rows if G.dialogue_key(r["id"]) in known]
    cells = TC.tear_cells(rows)
    values = TC.value_labels(cells, spans, tear_map, db_idx)
    sheet = TC.name_sheet(values, cells, spans, tear_map)
    names, name_diff = TC.read_name_labels(sheet, raters)
    cols = TC.final_columns(values, names, tear_map)
    return cols, sheet, TC.disagreements(cols, name_diff), CK.extras_table(TC.extras_rows(cols))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tear", required=True, type=Path)
    ap.add_argument("--set", default="dev50", choices=list(SPANS))
    ap.add_argument("--spans", type=Path, help="default: SPANS[--set]")
    ap.add_argument("--map", type=Path, default=Path("config/tear_to_mwoz.json"))
    ap.add_argument("--db", type=Path, default=Path("../chunking/data/MULTIWOZ2.4.zip"))
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v36"))
    a = ap.parse_args()
    a.spans = a.spans or SPANS[a.set]
    a.out.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(line) for line in a.tear.read_text(encoding="utf-8").splitlines() if line.strip()]
    spans = pd.read_csv(a.spans, encoding="utf-8")
    tear_map = json.loads(a.map.read_text(encoding="utf-8"))
    db_idx = G.db_index(G.load_db(a.db)) if a.db.exists() else None
    raters = [a.out / "tear_names_rater1.csv", a.out / "tear_names_rater2.csv"]
    cols, sheet, diff, table = score(rows, spans, tear_map, db_idx, raters)

    def write(df, name):
        df.to_csv(a.out / name, index=False, encoding="utf-8", lineterminator="\n")
    write(sheet, "tear_names_to_rate.csv")
    write(cols, "tear_columns.csv")
    write(diff, "tear_label_disagree.csv")
    table.to_csv(a.out / "tear_extras.csv", encoding="utf-8", lineterminator="\n")
    rated = sum(p.exists() for p in raters)
    notes = [f"{len(cols)} columns from {len({r['id'] for r in rows})} TEAR rows ({a.tear.name}); {len(sheet)} unmatched columns "
             f"on the name sheet, {rated} of 2 rater files read."]
    (a.out / "tear_extras.md").write_text(PR.kinds_md(f"wf_v3.6 TEAR extras by GT level ({a.set})", table, notes),
                                          encoding="utf-8", newline="\n")
    print(cols.to_string(index=False))
    print(table.to_string())


if __name__ == "__main__":
    main()
