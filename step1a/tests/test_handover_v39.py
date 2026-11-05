import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import handover_v39 as HV  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def col(cid, name, pools, groups, description=""):
    rows = [x for _, items in pools for x in items]
    return {"cid": cid, "name": name, "description": description, "groups": groups, "members": [k for k, _ in pools],
            "mention_ids": [x[0] for x in rows], "n_mentions": len(rows), "n_dialogues": len({x[1] for x in rows}),
            "n_values": len({x[2] for x in rows}), "top_values": [], "pools": pools}


def columns():
    return [col(1, "departure place", [("E#0@E#0", [(1, "d1", "ely"), (2, "d2", "bath")])], ["E#0"], "from"),
            col(2, "leaving city", [("E#1@E#1", [(3, "d3", "york")])], ["E#1"]),
            col(3, "time", [("E#2@E#2", [(4, "d4", "9:00")])], ["E#2"])]


def test_group_sets_both_orders_and_joins_on_columns():
    cols = columns()
    s0 = HV.group_sets(cols, [{"columns": [1, 2]}])
    s1 = HV.group_sets(cols, [{"columns": [1, 2]}, {"columns": [1, 3]}])
    assert s0 == [frozenset({"E#0", "E#1"})]
    both = HV.both_orders(s0, s1)
    assert both == [frozenset({"E#0", "E#1"})]            # the join of only one order is dropped
    assert HV.both_orders(s0, HV.group_sets(cols, [{"columns": [1, 3]}])) == []
    assert HV.joins_on_columns(cols, both)[0]["columns"] == [1, 2]
    merged = [col(1, "m", [("a@E#0", [(1, "d", "x")]), ("b@E#1", [(2, "d", "y")])], ["E#0", "E#1"])]
    assert HV.joins_on_columns(merged, both) == []      # already one column: nothing to join


def test_merge_joined_columns_names_after_the_biggest_and_keeps_every_mention():
    out = HV.merge_joined_columns(columns(), [{"columns": [1, 2]}])
    by = {c["name"]: c for c in out}
    assert set(by) == {"departure place", "time"} and [c["cid"] for c in out] == [1, 2]
    dp = by["departure place"]
    assert sorted(dp["mention_ids"]) == [1, 2, 3] and dp["groups"] == ["E#0", "E#1"] and dp["description"] == "from"
    assert dp["old_cids"] == [1, 2] and by["time"]["old_cids"] == [3]
    assert sorted(m for c in out for m in c["mention_ids"]) == [1, 2, 3, 4]


def test_parse_group_and_keep_apart_flags():
    assert HV.parse_group("E1#3|E1#5") == (["E1#3", "E1#5"], None) and HV.parse_group("E1#3/1") == (["E1#3"], "E1#3/1")
    pairs = [{"cluster_a": "A", "cluster_b": "B", "cos": 0.6}, {"cluster_a": "A", "cluster_b": "C", "cos": 0.7}]
    assert HV.keep_apart_flags(["A", "B"], pairs) == [{"a": "A", "b": "B", "cos": 0.6}]
    assert HV.keep_apart_flags(["A"], pairs) == []


def test_evidence_card_pools_members_and_gives_verdict():
    names = {1: "arrival time", 2: "departure time", 3: "time query"}
    sup = {1: (1, 10), 2: (9, 10)}
    src = {1: {3: (0, 3)}, 2: {3: (1, 3)}}
    c = HV.evidence_card([2, 1], names, sup, src, [[3]])
    assert c["support"] == {"yes": 10, "n": 20, "share": 0.5} and c["neighbour_fit"]["n"] == 3
    assert c["verdict"] == "unsure" and c["neighbours"][0]["columns"] == ["time query"]
    low = HV.evidence_card([1], names, sup, src, [[3]])
    assert low["verdict"] == "noise"                      # support 0.1 < 0.4
    none = HV.evidence_card([3], names, sup, src, [])
    assert none["support"] is None and "no example answers" in none["null_reason"] and none["verdict"] == "unsure"
    assert HV.evidence_card([], names, sup, src, [])["null_reason"] == "the column has no mention"


def doc():
    c = HV.column_record(1, "x", "d", "r", {"dominant": "text", "share": 1.0, "counts": {"text": 2}},
                         [{"cluster": "E#0", "group": "E#0/0", "part": "E#0/0", "mentions": 1}], [1, 2], 2, [], "current entity E#",
                         HV.evidence_card([], {}, {}, {}, []), False, [], [], {})
    c2 = {**c, "id": 2, "mention_ids": [3], "members": [{"cluster": "E#0", "group": "E#0/1", "part": "E#0/1", "mentions": 1}]}
    d = HV.dropped_record("E#1", "not_attribute", "", "[[ok]]", "other entity E#9", [4])
    return {"clusters": ["E#0", "E#1"], "columns": [c, c2], "dropped": [d]}


def test_dropped_record_and_check_handover():
    d = doc()
    assert d["dropped"][0]["wrong_entity_placement"] and d["dropped"][0]["n_mentions"] == 1
    assert HV.check_handover(d) == []                     # a split cluster may sit in two columns
    bad = doc()
    bad["columns"][1]["mention_ids"] = [2]
    assert "mention 2 appears 2 times" in HV.check_handover(bad)
    bad = doc()
    bad["dropped"] = []
    assert "cluster E#1 is in no column and not dropped" in HV.check_handover(bad)
    bad = doc()
    bad["columns"][1]["members"][0]["part"] = None
    bad["columns"][0]["members"][0]["part"] = None
    assert any("without being split" in p for p in HV.check_handover(bad))
    bad = doc()
    bad["dropped"].append({**bad["dropped"][0], "cluster": "E#0", "mention_ids": [9]})
    assert any("in a column and dropped" in p for p in HV.check_handover(bad))


@pytest.mark.parametrize("set_name", ["dev50", "dev50b"])
def test_written_handover_files_load_and_are_consistent(set_name):
    files = [ROOT / "handover" / set_name / f"{e}.json" for e in ("train", "hotel", "restaurant")]
    if not all(f.exists() for f in files):
        pytest.skip("handover files not written (scripts/final_v39.py)")
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        assert HV.check_handover(d) == [], f.name
        assert d["counts"]["columns"] == len(d["columns"]) and d["clusters"]
        for c in d["columns"]:
            assert set(c) >= {"id", "name", "description", "role", "value_type", "members", "mention_ids", "evidence", "verdict", "flags"}
            assert c["n_mentions"] == len(c["mention_ids"]) == sum(m["mentions"] for m in c["members"])
            assert c["verdict"] in ("real", "unsure", "noise", "too general", "mixed roles")
