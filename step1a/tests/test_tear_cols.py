import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from s1a import precision_v36 as PR  # noqa: E402
from s1a import tear_cols as TC  # noqa: E402
from score_tear_v36 import score  # noqa: E402

MAP = {"Train destination": "train-destination", "Train departure": "train-departure", "Hotel name": "hotel-name",
       "Hotel area": "hotel-area", "Hotel confirmed reference": "hotel-ref", "Restaurant name": "restaurant-name"}
COLS = ["dialogue_id", "turn", "speaker", "utterance", "char_start", "char_end", "value", "domain", "slot", "act", "source"]


def spans(rows):
    """Span table from (dialogue, value, domain, slot) tuples."""
    return pd.DataFrame([{**dict.fromkeys(COLS), "turn": 0, "speaker": "user", "utterance": "u", "act": "inform",
                          "source": "slot", "dialogue_id": d, "value": v, "domain": dom, "slot": s}
                         for d, v, dom, s in rows], columns=COLS)


SPANS = spans([
    ("d1", "Ely", "train", "destination"), ("d1", "Cambridge", "train", "departure"),
    ("d1", "Acorn", "hotel", "name"), ("d1", "north", "hotel", "area"), ("d1", "north", "restaurant", "area"),
    ("d1", "5", "hotel", "choice"), ("d1", "ABCD1234", "booking", "ref"),
    ("d2", "Bath", "train", "destination"), ("d2", "Acorn", "restaurant", "name"), ("d2", "XYZ99", "booking", "ref"),
    ("d2", "Acorn", "hotel", "name"), ("d2", "oslo", "hotel", "phone"),
])
ROWS = [
    {"id": "d1.json", "table": {"headers": ["Train destination", "Hotel name", "Hotel area", "Hotel confirmed reference",
                                            "Restaurant name"],
                               "rows": [[["Ely"], ["Acorn"], ["North"], ["ABCD1234"], ["nobody"]]]}},
    {"id": "d2", "table": {"headers": ["Train destination", "Hotel name", "Hotel confirmed reference", "Restaurant name"],
                           "rows": [[["Bath"], ["Acorn"], ["XYZ99"], ["zzz"]]]}},
    {"id": "other", "table": {"headers": ["Train destination"], "rows": [[["Ely"]]]}},  # no spans: skipped
]


def run(raters=()):
    return score(ROWS, SPANS, MAP, None, raters)


def test_value_mapping_and_kinds():
    cols, sheet, diff, table = run()
    k = cols.set_index("column")
    assert k.loc["Train destination", "final_label"] == "Train destination" and k.loc["Train destination", "n_matched"] == 2
    assert k.loc["Hotel name", "kind"] == "gt_found"
    # "booking" ref spans belong to the header's domain: "Hotel confirmed reference" -> hotel-ref
    assert k.loc["Hotel confirmed reference", "final_label"] == "Hotel confirmed reference"
    # one matched cell only (< 2): unmatched, even though "north" matches
    assert k.loc["Hotel area", "value_label"] == "" and k.loc["Hotel area", "kind"] == "extra_none"
    assert k.loc["Restaurant name", "kind"] == "extra_none"
    assert sorted(sheet["column"]) == ["Hotel area", "Restaurant name"]
    assert table.loc["TEAR", "gt_found"] == 3 and table.loc["TEAR", "extra_none"] == 2


def test_name_raters_fill_unmatched_and_lower_label_wins(tmp_path):
    _, sheet, _, _ = run()
    rid = dict(zip(sheet["column"], sheet["row_id"]))
    cand = sheet.set_index("column")["candidates"]["Hotel area"].split(";")
    assert "Hotel phone" in cand and "Hotel area" in cand and cand[-1] == "none"
    r1, r2 = tmp_path / "r1.csv", tmp_path / "r2.csv"
    ids = [rid["Hotel area"], rid["Restaurant name"]]
    pd.DataFrame({"row_id": ids, "label": ["Hotel area", "Restaurant name"]}).to_csv(r1, index=False)
    pd.DataFrame({"row_id": ids, "label": ["Hotel area", "none"]}).to_csv(r2, index=False)
    cols, _, diff, table = run([r1, r2])
    k = cols.set_index("column")
    assert k.loc["Hotel area", "final_source"] == "name" and k.loc["Hotel area", "kind"] == "gt_found"
    assert k.loc["Restaurant name", "final_label"] == ""  # raters differ: none is lower
    assert diff["column"].tolist() == ["Restaurant name"] and diff["chosen"].tolist() == ["none"]
    assert table.loc["TEAR", "gt_found"] == 4


def test_wrong_entity_choice_and_db_tier():
    # a restaurant column holding hotel names is a wrong entity; `choice` is noise; a DB-only value is L3
    sp = spans([("d1", "Acorn", "hotel", "name"), ("d2", "Acorn", "hotel", "name"), ("d1", "5", "hotel", "choice"),
                ("d2", "6", "hotel", "choice")])
    rows = [{"id": d, "table": {"headers": ["Restaurant name", "Hotel type", "Hotel stars"],
                                "rows": [[["Acorn"], [c], ["zip"]]]}} for d, c in (("d1", "5"), ("d2", "6"))]
    cols, _, _, _ = score(rows, sp, MAP, {"hotel": {"zip": ["postcode"]}})
    k = cols.set_index("column")
    assert k.loc["Restaurant name", "kind"] == "wrong_extra"
    assert k.loc["Hotel type", "kind"] == "wrong_extra" and k.loc["Hotel type", "final_label"] == "choice"
    assert k.loc["Hotel stars", "kind"] == "extra_L3" and k.loc["Hotel stars", "final_label"] == "Hotel postcode"


def test_tear_row_in_the_precision_table():
    cols, _, _, _ = run()
    t = PR.precision_table(TC.extras_rows(cols))
    l1, l2 = (t[t["level"] == n].iloc[0] for n in (1, 2))
    assert (l1["gt"], l1["extra_none"], l1["columns"]) == (3, 2, 5)
    assert l2["gt"] == 3


def test_bucket_levels():
    row = {"kind": "extra_L2", "majority_L1": "", "majority_L2": "Hotel phone", "majority_L3": ""}
    assert PR.bucket(row, 1) == "extra_confirmed" and PR.bucket(row, 2) == "gt"
    row = {"kind": "extra_L3", "majority_L1": "", "majority_L2": "", "majority_L3": "Hotel x"}
    assert PR.bucket(row, 1) == "extra_confirmed" and PR.bucket(row, 2) == "extra_confirmed"
    assert PR.bucket({**row, "kind": "wrong_extra"}, 2) == "wrong"
    assert PR.bucket({**row, "kind": "extra_none", "majority_L3": ""}, 1) == "extra_none"
    assert PR.bucket({**row, "kind": "gt_found", "majority_L3": ""}, 2) == "gt"


def test_same_name_counts_once_in_best_bucket():
    ex = pd.DataFrame([{"variant": "V", "ent": "hotel", "name": "Hotel_name", "kind": "extra_none", "majority_L1": "",
                        "majority_L2": "", "majority_L3": ""},
                       {"variant": "V", "ent": "hotel", "name": "hotel name", "kind": "gt_found", "majority_L1": "Hotel name",
                        "majority_L2": "", "majority_L3": ""}])
    b = PR.column_buckets(ex, 1)
    assert len(b) == 1 and b["bucket"].iloc[0] == "gt"
