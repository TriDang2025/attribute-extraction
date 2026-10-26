import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import multiview as MV  # noqa: E402
from s1a import step2 as S2  # noqa: E402


def blobs(seed=0, n=6):
    """Two well-separated blobs (orthogonal directions), n points each."""
    r = np.random.default_rng(seed)
    a = np.array([1, 0, 0, 0]) + 0.02 * r.normal(size=(n, 4))
    b = np.array([0, 1, 0, 0]) + 0.02 * r.normal(size=(n, 4))
    return np.vstack([a, b])


def test_weights_sum_to_one():
    xs, xc = blobs(0), blobs(1)
    for w in ("ch", (0.7, 0.3), (0.5, 0.5), (2, 1)):
        ws, wc = MV.view_weights(xs, xc, w)
        assert abs(ws + wc - 1) < 1e-9 and ws > 0 and wc > 0


def test_ch_weights_fall_back_when_a_view_is_one_cluster():
    xs = blobs()
    xc = np.ones((12, 4))  # identical rows: one cluster
    assert MV.view_weights(xs, xc, "ch") == (0.5, 0.5)


def test_log_jump_two_blobs():
    x = blobs()
    lab = MV.log_jump_labels(MV.cosine_dist(x))
    assert len(set(lab)) == 2
    assert len(set(lab[:6])) == 1 and len(set(lab[6:])) == 1 and lab[0] != lab[6]


def test_log_jump_small_partitions():
    assert len(set(MV.log_jump_labels(MV.cosine_dist(np.ones((1, 3)))))) == 1
    far = np.array([[1.0, 0], [0, 1.0]])
    assert len(set(MV.log_jump_labels(MV.cosine_dist(far)))) == 2  # d = 1 >= 0.4
    assert len(set(MV.log_jump_labels(MV.cosine_dist(np.ones((2, 3)))))) == 1


def test_zero_context_weight_equals_string_only_threshold():
    xs, xc = blobs(0), np.random.default_rng(5).normal(size=(12, 4))
    got = MV.partition_labels(xs, xc, (1, 0), "t", 0.4)
    want = MV.threshold_labels(MV.cosine_dist(xs), 0.4)
    assert np.array_equal(got, want)


class FakeEnc:
    def encode(self, texts):
        return np.array([[1.0, 0] if "a" in t else [0, 1.0] for t in texts])


def test_cluster_fn_end_to_end(monkeypatch):
    monkeypatch.setattr(S2, "window_texts", lambda doc, u, same, k, side="lr": u.text)
    spans = [SimpleNamespace(doc_id=0, text=t) for t in ("aa", "ab", "ba", "xx", "yy", "zz")]
    x, lab = MV.cluster_fn(spans, {0: None}, FakeEnc(), [0] * 6, [0] * 6, weights=(0.5, 0.5), method="t")
    assert x.shape == (6, 2) and len(lab) == 6
    assert lab[0] == lab[1] == lab[2] and lab[3] == lab[4] == lab[5] and lab[0] != lab[3]


def test_configs():
    assert len(MV.CONFIGS) <= 10
    assert {"I_ch_lj_k2", "I_w07_t04_k2"} <= set(MV.CONFIGS)
