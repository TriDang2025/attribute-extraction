import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import run_data_v37 as RD  # noqa: E402
from s1a import split as SPL  # noqa: E402
from s1a import step1a_v37 as S  # noqa: E402


def mentions():
    rows = [(0, "E1#0", "E1", "train", "t1"), (1, "E1#0", "E1", "train", "t2"), (2, "E1#0", "E1", "train", "t3"),
            (3, "E1#1", "E1", "train", "t4"), (4, "E1#1", "E1", "train", "t5"), (5, "", "", "", ""),
            (6, "E2#0", "E2", "hotel", "h1")]
    return pd.DataFrame({"mention_id": [r[0] for r in rows], "cluster_id": [r[1] for r in rows],
                         "entity": [r[2] for r in rows], "entity_gold": [r[3] for r in rows],
                         "dialogue_id": "D", "turn": 0, "char_start": range(7), "char_end": range(1, 8)})


GT = pd.DataFrame({"mention_id": [0, 1, 2, 3, 4, 6], "gt_L2": ["Train a", "Train a", "Train b", "Train b", "Train b", "Hotel x"]})


def test_recall_l2():
    tab, s = S.recall_l2(mentions(), GT, ["Train a", "Train b", "Hotel x", "Train c"])
    by = tab.set_index("gold_attr")
    # cluster E1#0 = a, a, b (purity 2/3 for a); E1#1 = b, b (purity 1); b is also 1/3 of E1#0
    assert bool(by.loc["Train a", "strict"]) and bool(by.loc["Train b", "strict"]) and bool(by.loc["Hotel x", "present"])
    assert not by.loc["Train c", "present"] and s["K"] == 3 and s["strict"] == 3 and s["present"] == 3


def test_with_l2_and_same_spans():
    m = mentions()
    assert list(S.with_l2(m, GT)["gold_attr"]) == ["Train a", "Train a", "Train b", "Train b", "Train b", "", "Hotel x"]
    assert S.same_spans(m, m.copy()) and not S.same_spans(m, m.assign(char_end=m["char_end"] + 1))


def test_j_split_summary():
    m = mentions()
    stats = [{"n": 3, "start": 1, "end": 1, "unknown": 1, "learned": ["via"], "members": [0, 1, 2], "parts": [0, 1, 2]}]
    df = S.j_split_summary(stats, m)
    assert list(df.loc[0, ["entity", "n", "unknown", "learned"]]) == ["E1", 3, 1, "via"]
    assert df.loc[0, "clusters"] == "E1#0;E1#0;E1#0"      # start, end, unknown part (one cluster id each, toy data)


def test_entity_ids_looked_up():
    m = mentions().assign(entity_gold=["train", "train", "train", "train", "train", "", "hotel"])
    m2 = pd.concat([m, pd.DataFrame({"cluster_id": ["E3#0"], "entity": ["E3"], "entity_gold": ["restaurant"]})])
    out = RD.entity_ids(m2)
    assert out == {"train": "E1", "hotel": "E2", "restaurant": "E3"}
    with pytest.raises(ValueError):
        RD.entity_ids(m)         # no restaurant entity


def test_dev50b_split_is_a_name_and_fresh_stays_sealed():
    assert "dev50b" in SPL.RUNNABLE and "fresh" not in SPL.RUNNABLE
    assert SPL.DEV50B == slice(50, 100)
    with pytest.raises(PermissionError):
        SPL.dialogues("fresh")


def test_j_split_summary_l2_labels():
    stats = [{"n": 3, "start": 1, "end": 1, "unknown": 1, "learned": [], "members": [0, 1, 5], "parts": [0, 1, 2]}]
    df = S.j_split_summary(stats, mentions(), GT)
    assert df.loc[0, "l2_labels"] == "start: Train a 1; end: Train a 1; unknown: - 1"
