import copy
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_gt as G  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def gt():
    return G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml")


def test_load_shape(gt):
    assert list(gt["tables"]) == ["train", "train_booking", "hotel", "hotel_booking", "restaurant", "restaurant_booking", "taxi", "attraction"]
    assert gt["tables"]["hotel"]["primary_key"] == ["Hotel name"]
    assert {(f["table"], f["ref_table"]) for f in gt["foreign_keys"]} == {
        ("train_booking", "train"), ("hotel_booking", "hotel"), ("restaurant_booking", "restaurant")}
    c = next(c for c in gt["tables"]["hotel_booking"]["columns"] if c["name"] == "Hotel confirmed name")
    assert c["slot"] == "none" and c["type"] == "unknown" and c["source"] == "tear"
    assert len(gt["soft_links"]) == 2 and len(gt["alternatives"]) == 7
    assert sum(c["source"] == "added" for t in gt["tables"].values() for c in t["columns"]) == 5


def test_check_clean_and_planted(gt):
    assert G.check(gt) == []
    bad = copy.deepcopy(gt)
    bad["foreign_keys"][0]["ref_columns"] = ["nope"]
    bad["tables"]["taxi"]["columns"].append(dict(bad["tables"]["train"]["columns"][0]))
    bad["tables"]["attraction"]["primary_key"] = []
    text = "\n".join(G.check(bad))
    assert "target missing" in text and "in two tables" in text and "no primary key" in text


def test_merged_design(gt):
    d = next(d for d in gt["alternatives"] if d["name"] == "merged:hotel")
    assert "hotel_booking" not in d["tables"] and "train_booking" in d["tables"]
    names = [c["name"] for c in d["tables"]["hotel"]["columns"]]
    assert "Hotel requested day" in names and "Hotel confirmed reference" in names
    assert "Hotel booking id" not in names and "Hotel confirmed name" not in names
    assert [f["table"] for f in d["foreign_keys"]] == ["train_booking", "restaurant_booking"]
    assert gt["tables"]["hotel_booking"]["columns"]  # main untouched


def test_canonical_and_sql(gt):
    for d in G.all_designs(gt):
        c = G.to_canonical(gt, d)
        assert all(col["gt"] == col["name"] and col["type"] in G.CANON_TYPES for t in c["tables"] for col in t["columns"])
        assert len(c["relationships"]) == len(d["foreign_keys"])
        con = sqlite3.connect(":memory:")
        con.executescript(G.to_sql(c))
        assert {r[0] for r in con.execute("select name from sqlite_master where type='table'")} == set(d["tables"])
    c = G.to_canonical(gt)
    rel = next(r for r in c["relationships"] if r["from"] == "hotel_booking")
    assert rel["to"] == "hotel" and rel["kind"] == "one_to_many"
    assert next(col for t in c["tables"] for col in t["columns"] if col["name"] == "Hotel booking id")["new"] is True


def test_questions(gt):
    q = "\n".join(G.questions(gt))
    assert "taxi" in q and "attraction" in q and "Hotel internet" in q and "Soft link" in q and "Hotel confirmed name" in q


def _write_handover(tmp_path, cols):
    d = tmp_path / "handover" / "dev50"
    d.mkdir(parents=True)
    (d / "train.json").write_text(json.dumps({"columns": [{"id": i, "mention_ids": ids} for i, ids in cols.items()]}), encoding="utf-8")
    return tmp_path / "handover"


def test_map_handover_and_reachable(gt, tmp_path):
    lev = pd.Series({0: "Train leave at", 1: "Train  Leave AT", 2: "Train leave at;Train arrive by", 3: "", 4: "Train arrive by",
                     5: "", 6: "", 7: "Hotel name", 8: "Train day", 9: ""})
    ho = _write_handover(tmp_path, {1: [0, 1, 2, 4], 2: [3, 5, 6, 9], 3: [7, 8], 4: [4, 3, 5, 6]})
    m = G.map_handover(ho, "dev50", lev, G.gt_names(gt))
    assert m["train:1"]["gt"] == "Train leave at" and m["train:1"]["purity"] == 0.75 and m["train:1"]["n"] == 4
    assert m["train:2"]["gt"] is None  # the empty label is the top
    assert m["train:4"]["n_labelled"] == 1 and m["train:4"]["labels"] == {"Train arrive by": 1}
    rows = {r["gt_column"]: r for r in G.reachable_rows(gt, m)}
    assert rows["Train leave at"]["reachable"] == "yes" and rows["Train leave at"]["found_by"] == "train:1"
    assert rows["Train arrive by"]["found_by"] == "train:4"  # train:1 has it on 2/4 only, train:4 on 1/1
    assert rows["Hotel name"]["reachable"] == "no"  # entity of the handover file is train
    assert rows["Train day"]["reachable"] == "no"  # train:3 has 1 of 2 labelled = 0.5
    assert rows["Train booking id"]["reachable"] == "added"
    status = G.reachable_status(list(rows.values()))
    assert status["Train booking id"] == "no"  # train_booking has no reachable column here
    assert status["Train leave at"] == "yes"
