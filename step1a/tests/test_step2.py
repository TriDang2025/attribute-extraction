import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest
from sklearn.cluster import AgglomerativeClustering

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step2 as S  # noqa: E402
from chk.data import make_doc  # noqa: E402


@dataclass
class M:
    doc_id: str
    text: str
    start: int
    end: int
    turn: int = -1
    labels: frozenset = field(default_factory=frozenset)


def same_partition(a, b):
    a, b = list(a), list(b)
    return all((a[i] == a[j]) == (b[i] == b[j]) for i in range(len(a)) for j in range(len(a)))


@pytest.mark.parametrize("raw,want", [
    ("5:30 pm", "17:30"), ("17.30", "17:30"), ("1715", "17:15"), ("12:00 am", "00:00"),
    ("7 pm", "19:00"), ("Two", "2"), ("two nights", "2 night"), ("  Swimming Pools. ", "swimming pool"),
    ("Cambridge!", "cambridge"), ("after 5:30 pm", "after 17:30"), ("colleges", "college"),
    ("2500", "2500"), ("guest   house", "guest house")])
def test_normalize(raw, want):
    assert S.normalize(raw) == want


@pytest.mark.parametrize("raw,want", [
    ("17:15", "time"), ("5:30 pm", "time"), ("1715", "time"), ("Friday", "day"),
    ("tomorrow", "day"), ("3", "number"), ("two", "number"), ("2 nights", "number"),
    ("£10.50", "price"), ("10 pounds", "price"), ("cheap", "text"), ("moderate", "text"),
    ("TR1234", "id"), ("8A2BC3D1", "id"), ("cambridge", "text"), ("abcdefgh", "text"), ("OAEJMYOI", "id"), ("noon", "time")])
def test_value_type(raw, want):
    assert S.value_type(raw) == want


def _doc():
    dlg = {"id": "D1",
           "turns": ["User: I need a train to cambridge on monday at 5:30 pm.",
                     "System: TR1234 leaves london at 17:30, for 2 people. cambridge is nice."],
           "domains": ["train", "train"]}
    return make_doc("D1", [dlg])


def _mentions(doc):
    out = []
    for v in ("cambridge", "monday", "5:30 pm", "TR1234", "london", "17:30", "2"):
        s = doc.text.index(v)
        out.append(M("D1", v, s, s + len(v), labels=frozenset({"Train x"})))
    return out


def test_masked_context_hides_all_mentions():
    doc = _doc()
    ms = _mentions(doc)
    ctx = S.masked_context(doc, ms[3], ms, prev_turns=1)
    for m in ms:
        assert m.text not in ctx
    assert "[TIME]" in ctx and "[DAY]" in ctx and "[ID]" in ctx and "[NUMBER]" in ctx
    only_turn = S.masked_context(doc, ms[3], ms, prev_turns=0)
    assert only_turn.startswith("System:")


def test_masked_context_marks_target():
    doc = _doc()
    ms = _mentions(doc)
    same = [m for m in ms if S.turn_index(doc, m) == S.turn_index(doc, ms[3]) and m.text != "2"]  # "2" sits inside TR1234
    ctxs = {S.masked_context(doc, m, ms) for m in same}
    assert len(ctxs) == len(same) and all(c.count("<<") == 1 for c in ctxs)


def test_combine_unit_norm():
    rng = np.random.RandomState(0)
    a, b = S._unit(rng.randn(5, 8)), S._unit(rng.randn(5, 8))
    v = S.combine(a, b, 0.7)
    assert np.allclose(np.linalg.norm(v, axis=1), 1, atol=1e-5)
    assert np.allclose(S.combine(a, b, 1.0), a, atol=1e-5)


@pytest.mark.parametrize("linkage", ["average", "complete", "single"])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_constrained_equals_sklearn_without_constraints(linkage, seed):
    rng = np.random.RandomState(seed)
    x = S._unit(rng.randn(30, 6))
    d = np.clip(1 - x @ x.T, 0, 2)
    np.fill_diagonal(d, 0)
    for t in (0.3, 0.6, 0.9):
        ref = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage=linkage,
                                      distance_threshold=t).fit_predict(d)
        assert same_partition(S.constrained_agglomerative(d, None, t, linkage), ref)


def test_constraints_never_violated():
    rng = np.random.RandomState(3)
    x = S._unit(rng.randn(30, 6))
    d = np.clip(1 - x @ x.T, 0, 2)
    pairs = {(int(a), int(b)) for a, b in rng.randint(0, 30, (40, 2)) if a != b}
    for linkage in ("average", "complete", "single"):
        lab = S.constrained_agglomerative(d, pairs, 1.5, linkage)
        assert all(lab[a] != lab[b] for a, b in pairs)
        assert len(set(lab)) < 30  # it still merges


def test_cannot_links_same_booking_different_string():
    us = [M("D1", "Cambridge", 0, 1), M("D1", "cambridge", 2, 3), M("D1", "london", 4, 5),
          M("D2", "london", 0, 1)]
    books = [("D1", "Train")] * 3 + [("D2", "Train")]
    assert S.cannot_links(us, books) == {(0, 2), (1, 2)}


def test_merge_split_clusters_respects_bookings():
    ctx = S._unit(np.array([[1, 0.0], [1, 0.01], [1, 0.02], [0, 1.0]]))
    labels = ["a", "b", "c", "d"]
    books = ["D1", "D2", "D1", "D3"]
    out, log = S.merge_split_clusters(labels, ctx, books, theta=0.9)
    assert out[0] != out[2]          # a and c share booking D1
    assert out[1] in (out[0], out[2])  # b merges with one of them
    assert out[3] == "d" and len(log) == 1
    out2, _ = S.merge_split_clusters(labels, ctx, ["D1", "D2", "D3", "D4"], theta=0.9,
                                     groups=["g1", "g1", "g2", "g2"])
    assert out2[0] == out2[1] and out2[2] != out2[0]


def test_string_ceiling_toy():
    us = [M("D1", "Cambridge", 0, 0, labels=frozenset({"Train departure"})),
          M("D2", "cambridge", 0, 0, labels=frozenset({"Train departure"})),
          M("D3", "cambridge", 0, 0, labels=frozenset({"Train destination"})),
          M("D4", "london", 0, 0, labels=frozenset({"Train destination"})),
          M("D5", "cambridge", 0, 0, labels=frozenset({"Taxi destination"}))]
    lab = S.string_ceiling(us, ["Train"] * 4 + ["Taxi"])
    assert lab[:4] == ["Train:Train departure"] * 3 + ["Train:Train destination"]
    assert lab[4] == "Taxi:Taxi destination"


def test_gold_entity_prefers_turn_domain():
    doc = _doc()
    u = M("D1", "cambridge", 0, 1, 0, frozenset({"Taxi destination", "Train destination"}))
    assert S.gold_entity(u, doc) == "Train"
    assert S.gold_entity(u) == "Taxi"
