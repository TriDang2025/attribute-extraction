import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import merges_v38 as M  # noqa: E402

ORDERS = ("o0", "o1", "o2")


def merges_df(rows):
    cols = ["attr_id", "name", "members", "member_attrs", "member_roles", "noise_share", "right", "reason", "judged"]
    return pd.DataFrame(rows, columns=cols)


def test_cluster_groups_skips_split_parts():
    attrs = pd.DataFrame({"attr_id": ["a|b", "c", "d/0"], "clusters": ["a;b", "c", "d"], "source": ["merge", "keep", "split"]})
    assert M.cluster_groups(attrs) == {"a": "a|b", "b": "a|b", "c": "c"}


def test_decision_names():
    dec = pd.DataFrame({"cluster_id": ["a", "b"], "name": ["Departure_Location", ""], "action": ["merge", "not_attribute"]})
    assert M.decision_names(dec) == {"a": ("departure location", "merge"), "b": ("", "not_attribute")}


def test_merge_source():
    same = {"a": "g", "b": "g"}
    apart = {"a": "g", "b": "h"}
    assert M.merge_source(["a", "b"], {"o0": same, "o1": same, "o2": apart}, ORDERS) == (["o0", "o1"], "majority of orders")
    assert M.merge_source(["a", "b"], {"o0": same, "o1": apart, "o2": apart}, ORDERS) == (["o0"], "one order (o0)")
    assert M.merge_source(["a", "b"], {"o0": apart, "o1": apart, "o2": {}}, ORDERS) == ([], "vote only")


def test_guard_pairs_uses_any_name():
    names = {"a": ["departure location"], "b": ["arrival location", "departure location"], "c": ["hotel name"]}
    assert M.guard_pairs(names) == [("a", "b")]
    assert M.guard_pairs({"a": ["departure location"], "b": ["departure location"]}) == []
    assert M.guard_pairs({"a": [], "b": ["destination"]}) == []


def test_odd_members():
    assert M.odd_members({"a": "X", "b": "Y", "c": "X"}, {"a": 1, "b": 5, "c": 1}) == ["a", "c"]
    assert M.odd_members({"a": "X", "b": "Y"}, {"a": 2, "b": 2}) == ["b"]  # tie: attribute name order keeps X
    assert M.odd_members({}, {}) == []


def test_wrong_merge_rows_and_cause_table():
    men = pd.DataFrame({"cluster_id": ["a", "a", "b", "c", "c", "d"], "cls": ["Train departure", "noise", "Train destination",
                                                                          "x", "x", "y"]})
    mg = merges_df([["a|b", "departure location", "a;b", "Train departure;Train destination", "departure;destination", 0.1,
                     False, "wrong_role", True],
                    ["c|d", "name", "c;d", "x;y", ";", 0.0, True, "", True],
                    ["e|f", "name", "e;f", "", "", float("nan"), False, "unjudged", False]])
    same = {"a": "a|b", "b": "a|b", "c": "c|d", "d": "c|d"}
    maps = {"o0": same, "o1": {"a": "a", "b": "b"}, "o2": same, "v": same}
    names = {"o0": {"a": ("departure location", "merge"), "b": ("departure location", "merge")},
             "o1": {"a": ("departure location", "keep"), "b": ("destination", "keep")},
             "o2": {}, "v": {"a": ("departure location", "merge"), "b": ("departure location", "merge")}}
    rows = M.wrong_merge_rows({"set": "s", "version": "v", "ent": "train"}, mg, men, ORDERS, "v", maps, names, "A prompt")
    assert len(rows) == 1
    r = rows[0]
    assert (r["reason"], r["source"], r["orders_full"]) == ("wrong_role", "majority of orders", "o0;o2")
    assert r["member_n"] == "2;1" and r["member_noise"] == "0.50;0.00" and r["odd_members"] == "b"
    assert r["guard_orders"] is True and r["guard_name"] is False and r["guard_pairs"] == "a+b"
    assert M.wrong_merge_rows({"set": "s", "version": "v", "ent": "train"}, mg, men, ORDERS, "v", maps, names, "name merge",
                              skip_attrs={"a|b"}) == []
    ct = M.cause_table(rows)
    assert ct.to_dict("records") == [{"set": "s", "step": "A prompt", "reason": "wrong_role", "source": "majority of orders",
                                      "n": 1, "guard_name": 0, "guard_orders": 1}]
    assert len(M.cause_table([])) == 0


def test_blocked_right():
    mg = merges_df([["a|b", "n", "a;b", "", "", 0.0, True, "", True], ["c|d", "n", "c;d", "", "", 0.0, True, "", True]])
    names = {"o0": {"a": ("departure", ""), "b": ("arrival", ""), "c": ("x", ""), "d": ("x", "")}, "v": {}}
    assert M.blocked_right(mg, names, ("o0",), "v") == 1


STATS = [{"label": "x", "n": 4, "members": [10, 11, 12, 13], "parts": [0, 1, 1, 2]}]
MEN = pd.DataFrame({"mention_id": ["10", "11", "12", "13", "14"], "cluster_id": ["c0", "c1", "c1", "c2", ""],
                    "gold_attr": ["Train departure", "Train destination", "Train destination;Train arrive by", "Train departure",
                                  ""]})


def test_part_clusters():
    assert M.part_clusters(STATS, MEN) == [{"split": 0, "part": "start", "cluster": "c0", "n_part": 1},
                                           {"split": 0, "part": "end", "cluster": "c1", "n_part": 2},
                                           {"split": 0, "part": "unknown", "cluster": "c2", "n_part": 1}]


def test_gold_part():
    cnt, top, role = M.gold_part(MEN, [11, 12], "train")
    assert top == "Train destination" and role == "destination" and cnt["Train arrive by"] == 1
    assert M.gold_part(MEN, [14], "train")[1:] == ("", "")
    assert M.gold_part(MEN.assign(gold_attr="Train day"), [10], "train")[1:] == ("Train day", "")


def test_joined_with():
    assert M.joined_with("a", {"a", "b", "c"}, {"a": "g", "b": "g", "c": "h"}) == ["b"]
    assert M.joined_with("a", {"a", "b"}, {"b": "g"}) == []


def test_name_side_and_ok():
    assert M.name_side("Departure Location") == "start" and M.name_side("arrival_station") == "end"
    assert M.name_side("location") == "" and M.name_side("departure arrival") == ""
    assert M.name_ok("origin station", "departure") is True and M.name_ok("destination", "departure") is False
    assert M.name_ok("location", "departure") is None and M.name_ok("origin", "-") is None


def part_ed(vote_groups, names_vote):
    ed = type("E", (), {})()
    ed.mentions = MEN
    maps = {o: dict(vote_groups) for o in ORDERS} | {"v": dict(vote_groups)}
    names = {o: dict(names_vote) for o in ORDERS} | {"v": dict(names_vote)}
    return ed, maps, names


def test_part_rows_and_verdicts():
    ed, maps, names = part_ed({"c0": "g0", "c1": "g1", "c2": "g0"},
                              {"c0": ("departure location", "merge"), "c1": ("arrival location", "merge"),
                               "c2": ("departure location", "merge")})
    rows = M.part_rows("s", "train", ed, STATS, MEN, ORDERS, "v", maps, names, "train")
    by = {r["cluster"]: r for r in rows}
    assert by["c0"]["joined_vote"] == "c2" and by["c0"]["same_name_vote"] == "c2" and by["c0"]["joined_back"] is True
    assert by["c1"]["gold_role"] == "destination" and by["c1"]["name_ok_vote"] is True and by["c1"]["joined_back"] is False
    assert by["c2"]["gold_role"] == "departure" and by["c2"]["gold_counts"] == "Train departure 1"
    assert by["c1"]["n_part"] == 2 and by["c1"]["n_cluster"] == 2
    # departure part joined with departure part: same role, kept apart from the destination part
    assert M.split_verdicts(rows) == {("s", "train", 0): "kept apart"}
    # the unknown part (departure) named like the end part and joined with it: re-merged across roles
    ed, maps, names = part_ed({"c0": "g0", "c1": "g1", "c2": "g1"},
                              {"c0": ("departure location", "merge"), "c1": ("arrival location", "merge"),
                               "c2": ("arrival location", "merge")})
    bad = M.part_rows("s", "train", ed, STATS, MEN, ORDERS, "v", maps, names, "train")
    assert M.split_verdicts(bad) == {("s", "train", 0): "re-merged across roles"}
    assert [r["name_ok_vote"] for r in bad] == [True, True, False]
    # a part with a gold role and no name
    ed, maps, names = part_ed({"c0": "g0", "c1": "g1"}, {"c0": ("departure location", "merge"), "c1": ("arrival", "merge"),
                                                          "c2": ("", "not_attribute")})
    assert M.split_verdicts(M.part_rows("s", "train", ed, STATS, MEN, ORDERS, "v", maps, names, "train")) == {
        ("s", "train", 0): "unnamed part"}


def test_split_verdict_one_role_only():
    rows = [{"set": "s", "ent": "e", "split": 0, "cluster": c, "gold_side": g, "joined_vote": "", "name_vote": "n",
             "gold_role": "-"} for c, g in (("a", "end"), ("b", "end"))]
    assert M.split_verdicts(rows) == {("s", "e", 0): "one role only"}


def test_role_status_and_cause():
    rows = [{"attr_id": "g1", "name": "dep", "description": "d", "majority_gold_attr": "Train departure", "ent": "train"},
            {"attr_id": "g2", "name": "x", "description": "d", "majority_gold_attr": "Train departure", "ent": "train"},
            {"attr_id": "g3", "name": "", "description": "", "majority_gold_attr": "Train destination", "ent": "train"},
            {"attr_id": "g4", "name": "y", "description": "d", "majority_gold_attr": "Train day", "ent": "train"}]
    ratings = {("train", "dep", "d", "Train departure"): "right", ("train", "x", "d", "Train departure"): "wrong"}
    st = M.role_status(rows, ratings, ["Train departure", "Train destination", "Train leave at"])
    assert st == {"Train departure": [("g1", "dep", "right"), ("g2", "x", "wrong")], "Train destination": [],
                  "Train leave at": []}
    assert M.role_cause(st["Train departure"], True, True) == "right"
    assert M.role_cause([("g", "n", "partly"), ("h", "n", "wrong")], True, True) == "named partly/wrong"
    assert M.role_cause([("g", "n", "unrated")], True, True) == "unrated name"
    assert M.role_cause([], True, True) == "no group has it as majority (found)"
    assert M.role_cause([], False, True) == "no group has it as majority (recoverable)"
    assert M.role_cause([], False, False) == "not recoverable by step 1a"
