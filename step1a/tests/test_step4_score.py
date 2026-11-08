import copy
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_gt as G  # noqa: E402
from s1a import step4_score as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SHARES = ["table_recall", "table_precision", "grouping_precision", "grouping_recall", "placement", "pk_right", "rel_precision",
          "rel_recall", "rel_direction", "rel_kind", "types_right"]


@pytest.fixture()
def gt():
    g = G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml")
    rows = [{"gt_table": tn, "gt_column": c["name"], "level": "", "found_by": "",
             "reachable": "added" if c["source"] == "added" else "yes" if t["entity"] in G.ENTITIES and c["slot"] != "none" else "no"}
            for tn, t in g["tables"].items() for c in t["columns"]]
    G.attach_reachable(g, "dev50", rows)
    return g


def full(res):
    m = res["metrics"]
    for k in SHARES:
        if k.startswith("rel_") and res["design"] == "merged:train+hotel+restaurant":  # no links at all in that design
            assert m[k]["n"] == 0
            continue
        assert m[k]["n"] > 0 and m[k]["k"] == m[k]["n"], (k, m[k])
    assert m["grouping_f1"] == 1.0 and m["table_f1"] == 1.0
    assert m["wrong_columns"]["k"] == 0 and m["unused_real"]["n"] == 0 and m["duplicates"]["n"] == 0 and m["new_unmatched"]["n"] == 0


def test_gt_vs_itself_every_design(gt):
    for d in G.all_designs(gt):
        res = S.score(G.to_canonical(gt, d), gt, "dev50")
        assert res["design"] == d["name"]
        full(res)


def test_reachable_only_drops_taxi_attraction(gt):
    c = G.to_canonical(gt)
    a = S.score(c, gt, "dev50")
    b = S.score(c, gt, "dev50", reachable_only=True)
    assert a["metrics"]["table_recall"]["n"] == 8 and b["metrics"]["table_recall"]["n"] == 6
    assert b["metrics"]["table_precision"]["n"] == 6  # taxi and attraction output tables are neutral, not wrong
    assert b["metrics"]["placement"]["n"] < a["metrics"]["placement"]["n"]
    full(b)
    assert not any(g in ("taxi", "attraction") for g in b["metrics"]["match"].values())
    with pytest.raises(ValueError):
        S.score(c, gt, "dev50b", reachable_only=True)


def test_reachable_only_every_design(gt):
    for d in G.all_designs(gt):
        res = S.score(G.to_canonical(gt, d), gt, "dev50", reachable_only=True)
        assert res["design"] == d["name"]
        full(res)


def nonzero(res, skip=()):
    for k, v in res["metrics"].items():
        if k in SHARES and k not in skip and v["n"]:
            assert v["k"] > 0, k


def test_planted_merge_two_tables(gt):
    c = G.to_canonical(gt)
    by = {t["name"]: t for t in c["tables"]}
    by["hotel"]["columns"] += by["restaurant"]["columns"]
    c["tables"] = [t for t in c["tables"] if t["name"] != "restaurant"]
    for t in c["tables"]:
        for f in t["foreign_keys"]:
            f["ref_table"] = "hotel" if f["ref_table"] == "restaurant" else f["ref_table"]
    for r in c["relationships"]:
        r["to"] = "hotel" if r["to"] == "restaurant" else r["to"]
    m = S.score(c, gt, "dev50")["metrics"]
    assert m["table_recall"]["k"] < 8 and m["grouping_precision"]["share"] < 1 and m["placement"]["share"] < 1
    assert m["grouping_f1"] < 1 and m["rel_recall"]["share"] < 1
    nonzero(S.score(c, gt, "dev50"))


def test_planted_remove_fk(gt):
    c = G.to_canonical(gt)
    c["tables"][1]["foreign_keys"] = []
    c["relationships"] = [r for r in c["relationships"] if r["from"] != "train_booking"]
    m = S.score(c, gt, "dev50")["metrics"]
    assert (m["rel_recall"]["k"], m["rel_recall"]["n"]) == (2, 3) and m["rel_precision"]["share"] == 1.0
    assert m["table_f1"] == 1.0 and m["placement"]["share"] == 1.0 and m["grouping_f1"] == 1.0
    nonzero(S.score(c, gt, "dev50"))


def test_planted_move_column(gt):
    c = G.to_canonical(gt)
    by = {t["name"]: t for t in c["tables"]}
    col = next(x for x in by["hotel"]["columns"] if x["name"] == "Hotel area")
    by["hotel"]["columns"].remove(col)
    by["restaurant"]["columns"].append(col)
    res = S.score(c, gt, "dev50")
    m = res["metrics"]
    assert res["design"] == "main" and m["placement"]["k"] == m["placement"]["n"] - 1
    assert m["grouping_f1"] < 1 and m["table_f1"] == 1.0 and m["rel_recall"]["share"] == 1.0
    assert m["wrong_columns"]["k"] == 1  # a hotel column inside the restaurant table
    nonzero(res)


def test_wrong_type_and_unknown_not_scored(gt):
    c = G.to_canonical(gt)
    next(x for x in c["tables"][0]["columns"] if x["name"] == "Train price")["type"] = "text"   # price ~ text: ok
    next(x for x in c["tables"][0]["columns"] if x["name"] == "Train day")["type"] = "integer"   # day ~ integer: wrong
    m = S.score(c, gt, "dev50")["metrics"]
    assert m["types_right"]["n"] == m["types_right"]["k"] + 1
    # unknown GT types (Hotel internet, ...) are not in n
    assert m["types_right"]["n"] < sum(len(t["columns"]) for t in c["tables"])


def test_wrong_direction_and_kind(gt):
    c = G.to_canonical(gt)
    c["relationships"][0].update({"from": "train", "to": "train_booking", "kind": "many_to_many"})
    m = S.score(c, gt, "dev50")["metrics"]
    assert (m["rel_direction"]["k"], m["rel_direction"]["n"]) == (2, 3) and (m["rel_kind"]["k"], m["rel_kind"]["n"]) == (2, 3)
    assert m["rel_recall"]["share"] == 1.0


def test_soft_link_is_correct_not_required(gt):
    c = G.to_canonical(gt)
    c["relationships"].append({"from": "taxi", "to": "hotel", "kind": "one_to_many", "reason": ""})
    m = S.score(c, gt, "dev50")["metrics"]
    assert m["rel_precision"]["k"] == m["rel_precision"]["n"] == 4 and m["rel_recall"]["share"] == 1.0
    c["relationships"].append({"from": "taxi", "to": "train", "kind": "one_to_many", "reason": ""})
    m = S.score(c, gt, "dev50")["metrics"]
    assert (m["rel_precision"]["k"], m["rel_precision"]["n"]) == (4, 5)


# ---- handover mapping, sources, new columns, unused, duplicates

def toy(tmp_path, gt):
    """Handover with 6 train columns; mentions: 1 -> leave at, 2 -> arrive by, 3 -> arrive by (duplicate), 4 -> noise, 5 -> hotel name."""
    d = tmp_path / "handover" / "dev50"
    d.mkdir(parents=True)
    ids = {1: [0, 1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8], 5: [9], 6: [10, 11]}
    (d / "train.json").write_text(json.dumps({"columns": [{"id": i, "mention_ids": v} for i, v in ids.items()]}), encoding="utf-8")
    lev = pd.Series(["Train leave at"] * 3 + ["Train arrive by"] * 4 + ["", ""] + ["Hotel name"] + ["Train price", ""])
    return tmp_path / "handover", lev


def test_map_columns_toy(tmp_path, gt):
    ho, lev = toy(tmp_path, gt)
    schema = {"tables": [{"name": "train", "columns": [{"name": "dep", "type": "time", "source": "train:1", "new": False, "gt": None}]}],
              "unused": [{"source": "train:4", "reason": ""}, {"source": "train:6", "reason": ""}]}
    m = S.map_columns(schema, "dev50", ho, lev, gt)
    assert m["train:1"] == {"gt": "Train leave at", "purity": 1.0, "n": 3, "entity": "train", "labels": {"Train leave at": 3}, "n_labelled": 3}
    assert m["train:4"]["gt"] is None and m["train:6"]["gt"] is None and m["train:6"]["purity"] == 0.5 and "train:2" not in m
    assert S.map_columns(schema, "dev50", ho, lev, gt, min_purity=1.1)["train:1"]["gt"] is None


def test_score_with_sources_new_id_unused_duplicates(tmp_path, gt):
    ho, lev = toy(tmp_path, gt)
    cols = [{"name": "train id", "type": "id", "source": None, "new": True, "gt": None},
            {"name": "leave", "type": "time", "source": "train:1", "new": False, "gt": None},
            {"name": "arrive", "type": "time", "source": "train:2", "new": False, "gt": None},
            {"name": "arrive 2", "type": "time", "source": "train:3", "new": False, "gt": None},
            {"name": "mystery", "type": "text", "source": "train:4", "new": False, "gt": None},
            {"name": "hotel name", "type": "text", "source": "train:5", "new": False, "gt": None},
            {"name": "extra id", "type": "id", "source": None, "new": True, "gt": None}]
    schema = {"tables": [{"name": "trains", "description": "", "row": "", "columns": cols, "primary_key": ["train id"], "foreign_keys": []}],
              "relationships": [], "unused": [{"source": "train:6", "reason": "x"}],
              "duplicate_flags": [{"source": "train:2", "duplicate_of": "train:3"}]}
    mp = S.map_columns(schema, "dev50", ho, lev, gt)
    res = S.score(schema, gt, "dev50", mapping=mp)
    m = res["metrics"]
    assert m["match"] == {"trains": "train"}
    assert (m["pk_right"]["k"], m["pk_right"]["n"]) == (1, 1)            # the new id column stands for Train trainid
    assert (m["duplicates"]["k"], m["duplicates"]["n"]) == (1, 1)        # train:2 and train:3 map to Train arrive by, flagged
    assert (m["wrong_columns"]["k"], m["wrong_columns"]["n"]) == (2, 5)  # mystery (None), hotel name (other entity); the credited new id is not a real column
    assert (m["new_unmatched"]["k"], m["new_unmatched"]["n"]) == (1, 2)  # extra id has no GT column left
    assert m["placement"]["k"] == 3 and m["placement"]["n"] == 4          # leave, arrive (dup once), trainid ok; hotel name in the wrong table
    assert m["unused_real"]["n"] == 1 and m["unused_real"]["k"] == 0     # train:6 majority label is empty


def test_unused_real_column(tmp_path, gt):
    ho, lev = toy(tmp_path, gt)
    schema = {"tables": [{"name": "train", "columns": [{"name": "dep", "type": "time", "source": "train:1", "new": False, "gt": None}],
                          "primary_key": [], "foreign_keys": []}],
              "relationships": [], "unused": [{"source": "train:2", "reason": ""}, {"source": "train:4", "reason": ""}], "duplicate_flags": []}
    m = S.score(schema, gt, "dev50", mapping=S.map_columns(schema, "dev50", ho, lev, gt))["metrics"]
    assert (m["unused_real"]["k"], m["unused_real"]["n"]) == (1, 2) and m["unused_real_uncovered"]["k"] == 1


# ---- stability

def test_stability(gt):
    c = G.to_canonical(gt)
    assert S.stability([c, copy.deepcopy(c), copy.deepcopy(c)], gt=gt) == {"mean": 1.0, "pairs": 3, "n_runs": 3}
    d = copy.deepcopy(c)
    by = {t["name"]: t for t in d["tables"]}
    by["restaurant"]["columns"].append(by["hotel"]["columns"].pop(0))
    r = S.stability([c, d], gt=gt)
    assert 0 < r["mean"] < 1
    assert S.stability([c], gt=gt)["mean"] is None


def test_flat(gt):
    row = S.flat(S.score(G.to_canonical(gt), gt, "dev50"))
    assert row["table_recall_k"] == 8 and row["table_recall_n"] == 8 and row["table_recall"] == 1.0 and row["design"] == "main"
    assert "match" in row and row["grouping_f1"] == 1.0


def test_gt_columns_placed_and_key_rule_b(gt):
    c = G.to_canonical(gt)
    by = {t["name"]: t for t in c["tables"]}
    by["hotel"]["columns"].append({"name": "hotel id", "type": "id", "source": None, "new": True, "gt": None})
    by["hotel"]["primary_key"] = ["hotel id"]  # surrogate id while "Hotel name" stays in the table
    gone = by["restaurant"]["columns"].pop(0)  # one GT column not placed
    m = S.score(c, gt, "dev50")["metrics"]
    n_gt = sum(len(t["columns"]) for t in G.to_canonical(gt)["tables"])
    assert m["gt_columns_placed"]["n"] == n_gt and m["gt_columns_placed"]["k"] == n_gt - 1, gone
    assert m["pk_right"]["k"] == m["pk_right"]["n"] - 1  # rule (a): the new id is wrong
    assert m["pk_right_b"]["k"] == m["pk_right_b"]["n"]  # rule (b): right, the name column is in the table
    by["hotel"]["columns"] = [x for x in by["hotel"]["columns"] if x["name"] != "Hotel name"]
    m = S.score(c, gt, "dev50")["metrics"]
    # no name column: credit_new gives the new id the GT PK, so it is right under (a) and (b) alike
    assert m["pk_right"]["k"] == m["pk_right"]["n"] and m["pk_right_b"]["k"] == m["pk_right_b"]["n"]
