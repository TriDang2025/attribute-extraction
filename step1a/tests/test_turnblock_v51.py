import pandas as pd

from s1a import turnblock_v51 as TB


def index(rows):
    """rows = (mention_id, dialogue, turn, value, start, end)."""
    df = pd.DataFrame(rows, columns=["mention_id", "dialogue_id", "turn", "norm_value", "char_start", "char_end"]).set_index("mention_id")
    return TB.TurnIndex(df)


def test_norm_value_and_different():
    assert TB.norm_value("The  Cambridge, Station") == "cambridge station"
    assert not TB.different("ashley hotel", "ashley")      # one contains the other: one value
    assert TB.different("cambridge", "london")
    assert not TB.different("", "london")


def test_from_x_to_y_same_turn_is_blocked():
    ix = index([(1, "d", 0, "cambridge", 10, 19), (2, "d", 0, "london", 23, 29), (3, "d", 1, "ely", 5, 8), (4, "d", 1, "norwich", 12, 19)])
    s = TB.pair_stats(ix, [1, 3], [2, 4])
    assert (s["hits"], s["count"], s["n"], s["share"]) == (4, 2, 4, 1.0)
    assert TB.blocked(([1, 3], [2, 4]), ix, 0.5, 2)
    assert not TB.blocked(([1, 3], [2, 4]), ix, 0.5, 3)       # min count
    assert not TB.blocked(([1, 3], [2, 4]), ix, None)         # switch off


def test_other_turns_same_value_and_overlap_do_not_count():
    ix = index([(1, "d", 0, "cambridge", 10, 19), (2, "d", 1, "london", 5, 11),      # different turns
                (3, "d", 2, "ely", 0, 3), (4, "d", 2, "ely", 20, 23),               # same value
                (5, "d", 3, "ely", 0, 3), (6, "d", 3, "norwich", 0, 7)])            # overlapping spans
    assert TB.pair_stats(ix, [1, 3, 5], [2, 4, 6])["hits"] == 0
    assert TB.pair_stats(ix, [], [])["share"] == 0.0


def test_share_is_fraction_of_mentions():
    ix = index([(1, "d", 0, "a1", 0, 2), (2, "d", 0, "b1", 5, 7), (3, "d", 1, "a2", 0, 2), (4, "d", 2, "b2", 0, 2)])
    s = TB.pair_stats(ix, [1, 3], [2, 4])
    assert (s["hits"], s["share"], s["count"]) == (2, 0.5, 1)


def test_unjoin_blocked_cannot_link():
    size = {"A": 5, "B": 3, "C": 1}
    bad = {frozenset("AB")}
    groups = TB.unjoin_blocked(["C", "B", "A"], size, lambda a, b: frozenset((a, b)) in bad)
    assert groups == [["A", "C"], ["B"]]
    assert TB.unjoin_blocked(["A", "B"], size, lambda a, b: False) == [["A", "B"]]


def test_apply_to_columns_unjoins_blocked_pair_only():
    ix = index([(1, "d", 0, "cambridge", 10, 19), (2, "d", 0, "london", 23, 29), (3, "d", 1, "ely", 0, 3), (4, "d", 2, "x", 0, 1)])
    cols = [{"cid": 1, "name": "station", "groups": ["g"], "members": ["A@g", "B@g"], "mention_ids": [1, 2]},
            {"cid": 2, "name": "other", "groups": ["h"], "members": ["C@h", "D@h"], "mention_ids": [3, 4]}]
    cluster_of = {1: "A", 2: "B", 3: "C", 4: "D"}
    out = TB.apply_to_columns(cols, cluster_of, {"B": "destination"}, ix, 0.1, 1)
    assert [(c["cid"], c["name"], c["mention_ids"]) for c in out] == [(1, "station", [1]), (3, "destination", [2]), (2, "other", [3, 4])]
    assert out[1]["unjoined_from"] == 1
    assert TB.apply_to_columns(cols, cluster_of, {}, ix, None) == cols
