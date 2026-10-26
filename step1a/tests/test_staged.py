import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import paths  # noqa: E402, F401

sys.path.insert(0, str(paths.ROOT / "scripts"))
import relabel as RL  # noqa: E402
from s1a import staged as G  # noqa: E402
from s1a.combos import V21_FILTER  # noqa: E402

A = np.array([1.0, 0.0])
B = np.array([0.0, 1.0])
P = ("g", "text")


def test_same_string_different_context_splits():
    ctx = np.array([A, A, B, B])
    s = np.array([A, A, A, A])  # identical strings
    lab = G.staged_labels(ctx, s, [P] * 4, 0.1, 0.4)
    assert lab[0] == lab[1] and lab[2] == lab[3] and lab[0] != lab[2]
    assert lab[0].startswith("g|text|c")


def test_loose_t1_no_split():
    ctx = np.array([A, A, B, B])
    s = np.array([A, A, A, A])
    lab = G.staged_labels(ctx, s, [P] * 4, 1.5, 0.4)
    assert len(set(lab)) == 1


def test_same_context_equals_string_only():
    ctx = np.array([A] * 4)
    s = np.array([A, A, B, B])
    lab = G.staged_labels(ctx, s, [P] * 4, 0.3, 0.4)
    ref = RL.stage2(s, [P] * 4, 0.4)
    assert len(set(lab)) == len(set(ref)) == 2
    assert [a == b for a in lab for b in lab] == [a == b for a in ref for b in ref]


def test_partitions_kept_apart():
    x = np.array([A, A])
    lab = G.staged_labels(x, x, [("g", "time"), ("g", "day")], 0.3, 0.4)
    assert lab[0] != lab[1]


def test_min_size_merge():
    ctx = np.array([A, A, A, [0.9, 0.1], B, B, B])
    ctx = ctx / np.linalg.norm(ctx, axis=1, keepdims=True)
    lab = G.merge_small([0, 0, 0, 1, 2, 2, 2], ctx, 2)
    assert lab[3] == 0 and lab[4] == 2
    assert G.merge_small([0, 1], ctx[:2], 2) == [0, 1]  # nothing big enough: unchanged
    s = np.array([A] * 7)
    split = G.staged_labels(ctx, s, [P] * 7, 0.001, 0.4)
    merged = G.staged_labels(ctx, s, [P] * 7, 0.001, 0.4, min_size=2)
    assert len(set(split)) == 3 and len(set(merged)) == 2


def test_configs():
    assert 1 <= len(G.CONFIGS) <= 12
    assert all(v.span_filter is V21_FILTER and callable(v.cluster_fn) for v in G.CONFIGS.values())
    assert "G_w2_t1_03" in G.CONFIGS
