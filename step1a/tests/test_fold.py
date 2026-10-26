import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import fold as F  # noqa: E402

E = np.eye(3)


def _x(*rows):
    return np.array([E[r] if isinstance(r, int) else r for r in rows], float)


def test_small_moves_to_nearest_kept():
    # kept: a (e0 x3), b (e1 x3); small s = near e0
    x = _x(0, 0, 0, 1, 1, 1, [0.9, 0.1, 0])
    lab = ["a"] * 3 + ["b"] * 3 + ["s"]
    assert F.fold(x, lab, [0] * 7, 3) == ["a"] * 3 + ["b"] * 3 + ["a"]


def test_tau_blocks_far_move():
    x = _x(0, 0, 0, 1, 1, 1, [0.1, 0.1, 1.0])
    lab = ["a"] * 3 + ["b"] * 3 + ["s"]
    assert F.fold(x, lab, [0] * 7, 3, tau=0.5)[-1] == "s"
    assert F.fold(x, lab, [0] * 7, 3)[-1] in ("a", "b")


def test_mean_threshold_and_partitions():
    # partition 0: sizes 3 and 1 (mean 2) -> small moves; partition 1 moves only within itself
    x = _x(0, 0, 0, [0.9, 0.1, 0], 1, 1, 1, [0.1, 0.9, 0])
    lab = ["a", "a", "a", "s", "b", "b", "b", "t"]
    parts = [0] * 4 + [1] * 4
    assert F.fold(x, lab, parts, "mean") == ["a"] * 4 + ["b"] * 4
    # same labels but t sits in partition 0 with no kept cluster of its own nearby: goes to a
    parts2 = [0] * 4 + [1] * 3 + [0]
    assert F.fold(x, lab, parts2, 3)[-1] == "a"


def test_unchanged_without_kept_cluster():
    x = _x(0, 1, 2)
    assert F.fold(x, ["a", "b", "c"], [0, 0, 0], 2) == ["a", "b", "c"]


def test_booking_constraint_blocks():
    x = _x(0, 0, 0, 1, 1, 1, [0.9, 0.1, 0])
    lab = ["a"] * 3 + ["b"] * 3 + ["s"]
    texts = ["x", "x", "x", "y", "y", "y", "z"]
    books = [1, 2, 3, 4, 5, 6, 1]  # booking 1 already has "x" in a; "z" differs -> blocked from a
    out = F.fold(x, lab, [0] * 7, 3, books=books, texts=texts)
    assert out[-1] == "b"
    books_ok = [1, 2, 3, 4, 5, 6, 9]
    assert F.fold(x, lab, [0] * 7, 3, books=books_ok, texts=texts)[-1] == "a"
    same = F.fold(x, lab, [0] * 7, 3, books=books, texts=["x"] * 3 + ["y"] * 3 + ["X"])
    assert same[-1] == "a"  # same normalized string in the same booking is fine


def test_configs():
    assert 1 <= len(F.CONFIGS) <= 12
    assert {"F_m3_t05", "F_mean", "F_m2_t06_bk"} <= set(F.CONFIGS)
