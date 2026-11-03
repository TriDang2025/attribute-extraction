import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import score_v38 as S  # noqa: E402


def ans(*pairs):
    return {"answers": [{"id": i, "fits": f} for i, f in pairs]}


def test_answer_check_counts_missing_extra_repeated():
    c = S.answer_check({1, 2, 3}, ans((1, "yes"), (1, "no"), (3, "no"), (9, "yes")))
    assert c == {"expected": 3, "answered": 2, "missing": [2], "extra": [9], "repeated": [1]}


def test_yes_no_ignores_extra_and_repeats_and_counts_by_source():
    a = S.yes_no(ans((1, "yes"), (1, "no"), (2, "no"), (3, "yes"), (9, "yes")), expected={1, 2, 3})
    assert a == {1: True, 2: False, 3: True}
    assert S.counts_by_source(a, {1: 4, 2: 4, 3: 9}) == {4: (1, 2), 9: (1, 1)}


def test_union_joins_is_transitive_and_base_is_biggest():
    assert S.union_joins([{"columns": [3, 7]}, {"columns": [7, 9]}, {"columns": [1, 2]}]) == [[1, 2], [3, 7, 9]]
    cols = {3: {"n_mentions": 5}, 7: {"n_mentions": 9}, 9: {"n_mentions": 9}}
    assert S.join_base(cols, [3, 7, 9]) == 7           # most mentions, ties the lower id


def col(cid, name, groups, pools, types):
    items = [x for _, ms in pools for x in ms]
    return {"cid": cid, "name": name, "description": "", "groups": groups, "members": [f"c{cid}@{g}" for g in groups],
            "mention_ids": [x[0] for x in items], "n_mentions": len(items), "n_dialogues": len({x[1] for x in items}),
            "n_values": len({x[2] for x in items}), "value_types": types, "pools": pools}


def test_join_columns_pools_counts_on_the_union():
    a = col(1, "place", ["g1"], [("k1", [(1, "d1", "ely"), (2, "d2", "bath")])], "text:2")
    b = col(2, "town", ["g2", "g3"], [("k2", [(3, "d2", "bath"), (4, "d3", "ely")])], "text:1|code:1")
    j = S.join_columns([a, b], 2)
    assert (j["cid"], j["name"], j["groups"], j["joined"]) == (2, "town", ["g1", "g2", "g3"], [1, 2])
    assert (j["n_mentions"], j["n_dialogues"], j["n_values"]) == (4, 3, 2)
    assert j["value_types"] == "text:3|code:1" and len(j["pools"]) == 2


def test_renamed_and_marked_attrs_copy():
    attrs = pd.DataFrame({"attr_id": ["a", "b", "c"], "name": ["x", "y", "z"], "status": ["keep", "keep", "keep"]})
    r = S.renamed_attrs(attrs, {"b": "x", "c": "x"})
    assert list(r["name"]) == ["x", "x", "x"] and list(attrs["name"]) == ["x", "y", "z"]
    m = S.marked_attrs(attrs, ["c"])
    assert list(m["status"]) == ["keep", "keep", "not_attribute"] and list(attrs["status"]) == ["keep"] * 3


def info(name, label="real", attr="Hotel area", partner=0.0):
    return {"name": name, "label": label, "top_attr": attr, "partner": partner}


def test_join_right_status():
    assert S.join_right([info("a"), info("b")])[0] == "right"
    assert S.join_right([info("a"), info("b", attr="Hotel address")])[0] == "wrong"
    assert S.join_right([info("a"), info("b", partner=0.5)])[0] == "wrong"
    assert S.join_right([info("a"), info("b", label="noise", attr="")])[0] == "wrong"
    assert S.join_right([info("a", label="mixed", attr="x"), info("b")])[0] == "no_gt"


def test_pooled_support_sums_members_with_a_job():
    assert S.pooled_support([1, 2, 3], {1: (3, 5), 3: (1, 2)}) == (4, 7)
    assert S.pooled_support([9], {}) == (0, 0)


def test_neighbour_evidence_uses_base_answers_first_and_counts_once():
    src = {1: {5: (2, 5), 6: (1, 5)}, 2: {5: (4, 5), 7: (3, 5)}}
    ev = S.neighbour_evidence([1, 2], 1, [[5], [6, 7], [8]], src)
    assert ev == [{"cids": [5], "yes": 2, "n": 5}, {"cids": [6, 7], "yes": 4, "n": 10}, {"cids": [8], "yes": 0, "n": 0}]


def test_mixed_roles_needs_a_fitting_role_partner():
    fit = [{"names": ["destination station"], "yes": 3, "n": 5}]
    assert S.mixed_roles(["departure station"], fit)
    assert not S.mixed_roles(["departure station"], [{"names": ["destination station"], "yes": 2, "n": 5}])   # 2/5 does not fit
    assert not S.mixed_roles(["travel date"], fit)                                                             # no role pair
    assert not S.mixed_roles(["hotel location"], [{"names": ["hotel address"], "yes": 5, "n": 5}])           # never location vs address


def test_verdict_order_and_boundaries():
    assert S.verdict(0.39, 0.9, False) == "noise"                     # rule 1 first
    assert S.verdict(0.4, 0.51, False) == "too general"
    assert S.verdict(0.4, 0.51, True) == "mixed roles"
    assert S.verdict(0.7, 0.5, False) == "unsure"                      # fit 0.5 is not > 0.5
    assert S.verdict(0.7, 0.3, False) == "real"
    assert S.verdict(0.69, 0.0, False) == "unsure" and S.verdict(0.9, 0.31, False) == "unsure"
    assert S.verdict(None, None, False) == "unsure"
    assert S.verdict(0.9, None, False) == "real"


def test_dominant_share():
    assert S.dominant_share("text:3|code:1") == ("text", 0.75)
    assert S.dominant_share("") == ("", 0.0)


def test_gt_kinds_first_gt_then_duplicates():
    df = pd.DataFrame({"cid": [1, 2, 3, 4, 5, 6], "kind": ["gt", "gt", "gt", "wrong", "noise", "no_gt"],
                       "top_attr": ["A", "A", "B", "X", "", ""]})
    assert S.gt_kinds(df) == ["gt", "duplicate", "gt", "wrong", "wrong", "no_gt"]


def test_checker_table_shares_and_decision():
    kinds = ["gt", "gt", "wrong", "wrong", "wrong", "duplicate"]
    verd = ["real", "unsure", "noise", "too general", "real", "mixed roles"]
    t = S.checker_table(kinds, verd).set_index("gt_kind")
    assert t.loc["gt", "real_share"] == 0.5 and t.loc["wrong", "rejected_share"] == 2 / 3
    assert t.loc["duplicate", "rejected_share"] == 0 and t.loc["duplicate", "rejected_mixed_share"] == 1
    assert t.loc["no_gt", "n"] == 0 and pd.isna(t.loc["no_gt", "real_share"])
    assert S.filter_decision(4, 2, True)[0] and not S.filter_decision(4, 1, True)[0] and not S.filter_decision(4, 3, False)[0]
    assert not S.filter_decision(0, 0, True)[0]
