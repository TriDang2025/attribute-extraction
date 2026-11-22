import pandas as pd
import pytest

from s1a import ceiling_v50 as C
from s1a import split as SPL


def _rows(*rows):
    return pd.DataFrame([dict(zip(C.MENTION_COLS, r)) for r in rows], columns=C.MENTION_COLS)


def test_dev50c_sealed_and_disjoint():
    with pytest.raises(PermissionError):
        SPL.dialogues("dev50c")
    pool = [{"id": f"d{i}"} for i in range(300)]
    picked = SPL.dev50c(pool)
    idx = [int(d["id"][1:]) for d in picked]
    assert len(set(idx)) == 50 and min(idx) >= 100 and idx == sorted(idx)
    assert picked == SPL.dev50c(pool)


def test_kind():
    assert C.kind(_rows(("A", "tear", "d", None, "yes", False), ("A", "tear", "d", None, "free", False))) == "yes/no"
    assert C.kind(_rows(("A", "tear", "d", 1, "cheap", True))) == "span"
    assert C.kind(_rows()) == "span"


def test_ceiling_rows_dedup_and_flags():
    ments = _rows(("A", "tear", "d1", 1, "x", True), ("A", "mwoz", "d1", 1, "x", True),   # same mention twice -> 1
                  ("A", "mwoz", "d2", 3, "y", True), ("A", "pipe", "d1", 1, "x", True),
                  ("B", "pipe", "d1", 2, "z", True))                                         # pipeline only -> not reachable
    rows = C.ceiling_rows({"A": "e", "B": "e"}, {"A"}, ments).set_index("attr")
    assert rows.loc["A", "n_text"] == 2 and rows.loc["A", "hard"] and rows.loc["A", "found_v49"]
    assert not rows.loc["B", "reachable"] and rows.loc["B", "n_pipe"] == 1
    s = C.summary(rows.reset_index())
    assert s["with >= 1 mention (reachable)"] == 1 and s["found / reachable"] == "1/1 (1.000)"
