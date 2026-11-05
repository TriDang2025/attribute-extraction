import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import splitback_v39 as S  # noqa: E402

A, B, C, D = "E#0", "E#1", "E#2", "E#3"
SIZE = {A: 10, B: 8, C: 5, D: 3}
CENT = {A: np.array([1.0, 0.0]), B: np.array([0.0, 1.0]), C: np.array([0.9, 0.1]), D: np.array([0.1, 0.9])}


def test_conflicts_keep_apart_and_role():
    texts = {A: ["arrival location"], B: ["departure location"], C: ["price"], D: ["price"]}
    got = S.conflicts([A, B, C, D], {frozenset((C, D))}, texts)
    assert got == {frozenset((A, B)): "role", frozenset((C, D)): "keep_apart"}


def test_conflicts_both_reasons_and_outside_pairs_ignored():
    texts = {A: ["destination"], B: ["departure"]}
    got = S.conflicts([A, B], {frozenset((A, B)), frozenset((A, "E#9"))}, texts)
    assert got == {frozenset((A, B)): "keep_apart+role"}


def test_split_columns_seeds_and_members_by_similarity():
    conf = {frozenset((A, B)): "role"}
    cols = S.split_columns([A, B, C, D], conf, SIZE, CENT)
    assert cols == [[A, C], [B, D]]      # C near A, D near B; biggest column first


def test_split_columns_no_conflict_is_one_column():
    assert S.split_columns([B, A], {}, SIZE, CENT) == [[A, B]]


def test_split_columns_non_conflicting_seeds_share_a_column():
    # A-B and C-D conflict; C joins A's column (no conflict with A), D then conflicts with C so it opens / joins B's column
    conf = {frozenset((A, B)): "role", frozenset((C, D)): "keep_apart"}
    assert S.split_columns([A, B, C, D], conf, SIZE, CENT) == [[A, C], [B, D]]


def test_split_columns_three_way_conflict():
    conf = {frozenset(p): "role" for p in ((A, B), (A, C), (B, C))}
    assert S.split_columns([A, B, C], conf, SIZE, CENT) == [[A], [B], [C]]


def test_column_names_own_name_then_disambiguation():
    own = {A: "arrival location", B: "arrival location", C: "", D: ""}
    top = {A: "ely", B: "bath", C: "", D: ""}
    assert S.column_names("grp", [[A], [B]], own, top, SIZE) == ["arrival location", "arrival location (bath)"]
    assert S.column_names("grp", [[C], [D]], own, top, SIZE) == ["grp", "grp (D)".replace("D", D)]
    assert S.column_names("grp", [[A], [B]], own, {}, SIZE) == ["arrival location", f"arrival location ({B})"]


def test_apply_split_remaps_attrs_and_assign():
    attrs = pd.DataFrame({"attr_id": [f"{A}|{B}", C], "name": ["loc", "x"], "clusters": [f"{A};{B}", C], "n_mentions": [4, 1],
                          "status": ["keep", "keep"], "source": ["merge", "keep"], "description": ["d", ""]})
    assign = {1: f"{A}|{B}", 2: f"{A}|{B}", 3: f"{A}|{B}", 4: f"{A}|{B}", 5: C}
    mc = {1: A, 2: A, 3: B, 4: "E#9", 5: C}     # mention 4 is from a cluster the group did not list
    plan = {f"{A}|{B}": [{"clusters": [A], "name": "a", "description": "da"}, {"clusters": [B], "name": "b", "description": "db"}]}
    new_attrs, new_assign, orphans = S.apply_split(attrs, assign, mc, plan)
    assert new_assign == {1: A, 2: A, 3: B, 4: A, 5: C} and orphans == 1
    assert list(new_attrs["attr_id"]) == [A, B, C] and list(new_attrs["name"]) == ["a", "b", "x"]
    assert list(new_attrs["n_mentions"]) == [3, 1, 1] and list(new_attrs["source"]) == [S.SOURCE, S.SOURCE, "keep"]
    assert list(new_attrs["status"]) == ["keep"] * 3 and list(new_attrs["clusters"]) == [A, B, C]


def merges(rows):
    return pd.DataFrame(rows, columns=["attr_id", "name", "members", "right", "reason", "judged"])


def test_merge_fate_undone_fixed_and_right_undone():
    before = merges([["g1", "n1", f"{A};{B}", False, "wrong_role", True], ["g2", "n2", f"{C};{D}", True, "", True],
                     ["g3", "n3", "E#7;E#8", False, "noise", True], ["g4", "n4", "E#5;E#6", False, "unjudged", False]])
    after = merges([["g3", "n3", "E#7;E#8", False, "noise", True], ["g2", "n2", f"{C};{D}", True, "", True]])
    groups = {A: "ga", B: "gb", C: "gc", D: "gc", "E#7": "g3", "E#8": "g3"}
    rows = S.merge_fate("s", "train", before, after, groups)
    assert [(r["attr_id"], r["undone"], r["wrong_after"], r["fixed"]) for r in rows] == [
        ("g1", True, 0, True), ("g2", False, 0, False), ("g3", False, 1, False)]
    right_undone = S.merge_fate("s", "train", before, merges([]), {**groups, D: "gd"})
    assert [r["undone"] for r in right_undone if r["was_right"]] == [True]


def test_fate_counts_and_decide():
    fate = [{"set": "s", "ent": "e", "attr_id": a, "column": a, "was_right": r, "reason": "", "n_members": 2, "members": "x;y",
             "groups_after": g, "undone": g > 1, "wrong_after": 0, "fixed": (not r) and g > 1}
            for a, r, g in (("w1", False, 2), ("w2", False, 1), ("r1", True, 1), ("r2", True, 2))]
    c = S.fate_counts(fate)["s"]
    assert c == {"wrong": 2, "wrong_undone": 1, "wrong_fixed": 1, "right": 2, "right_undone": 1}
    assert S.decide(c, 1, True)[0] is True
    assert S.decide(c, 2, True)[0] is False          # wrong merges not down
    assert S.decide(c, 1, False)[0] is False         # guard fails
    assert S.decide({**c, "right_undone": 2}, 1, True)[0] is False


def test_status_from_chosen_and_sim_threshold():
    nodes = pd.DataFrame({"cluster_id": ["a", "b", "c"], "wilson_hi": [0.5, 0.5, 0.01], "s": [3.0, 1.0, 2.0]})
    chosen = {"signals": ["s"], "directions": {"s": 1}, "method": "rank", "theta": 0.05, "threshold": 0.6}
    assert list(S.status_from_chosen(nodes, chosen)["status"]) == ["kept", "dropped", "dropped"]
    h = nx.Graph()
    h.add_edge("a", "b", cos=0.2)
    h.add_edge("a", "c", cos=0.8)
    assert S.sim_threshold({"E": h}, {"a", "b", "c"}, 0.5) == 0.5
    assert S.sim_threshold({"E": h}, {"a", "b"}, 0.5) == 0.2


def test_keep_apart_rows_flattens_schema():
    schema = {"E1": {"keep_apart": [{"nodes": ["E1#0", "E1#1"], "cos": 0.61234, "count": 2}]}, "relationships": {"pairs": []}}
    rows = S.keep_apart_rows("dev50", schema, {"E1#0": "a|b|c|d", "E1#1": "x"})
    assert rows == [{"set": "dev50", "entity": "E1", "cluster_a": "E1#0", "cluster_b": "E1#1", "cos": 0.6123, "count": 2,
                     "values_a": "a|b|c", "values_b": "x"}]
    assert S.apart_pairs(rows, "E1") == {frozenset(("E1#0", "E1#1"))} and S.apart_pairs(rows, "E2") == set()
