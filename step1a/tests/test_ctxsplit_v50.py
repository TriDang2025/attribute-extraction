import numpy as np

from s1a import ctxsplit_v50 as CS


def test_left_context():
    t = "User: I want to leave after 10:00"
    assert CS.left_context(t, 6, t.index("10:00")) == "want to leave after"
    assert CS.left_context(t, 6, 6) == "[start]"


def _parts():
    # cluster C cut by format into two parts that mix two context groups (ids 1-3 near e0, ids 4-6 near e1)
    return [{"key": "C@C/0", "cluster": "C", "mention_ids": [1, 2, 4]}, {"key": "C@C/1", "cluster": "C", "mention_ids": [3, 5, 6]},
            {"key": "D@D/0", "cluster": "D", "mention_ids": [7]}]


def _vec():
    e0, e1 = np.array([1.0, 0.0]), np.array([0.0, 1.0])
    return {1: e0, 2: e0, 3: e0, 4: e1, 5: e1, 6: e1, 7: e0}


def test_reassign_by_context_and_keep_part_keys():
    new = CS.reassign(_parts(), _vec())
    assert sorted(map(sorted, (new["C@C/0"], new["C@C/1"]))) == [[1, 2, 3], [4, 5, 6]]
    assert new["C@C/0"] == [1, 2, 3]          # part 0 had most of 1-3, so it keeps them
    assert new["D@D/0"] == [7]                # one-part cluster untouched


def test_min_size_switch_keeps_small_clusters():
    new = CS.reassign(_parts(), _vec(), min_size=10)
    assert new["C@C/0"] == [1, 2, 4]


def test_apply_moves_mentions_between_columns():
    cols = [{"cid": 1, "name": "time str", "members": ["C@C/0"], "mention_ids": [1, 2, 4, 9]},
            {"cid": 2, "name": "time int", "members": ["C@C/1"], "mention_ids": [3, 5, 6]}]
    out = CS.apply(cols, _parts(), CS.reassign(_parts(), _vec()))
    assert out[0]["mention_ids"] == [1, 2, 3, 9] and out[1]["mention_ids"] == [4, 5, 6]
