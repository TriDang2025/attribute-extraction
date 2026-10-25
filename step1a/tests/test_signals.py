import sys
from pathlib import Path
from types import SimpleNamespace

import networkx as nx
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import signals as S  # noqa: E402
from s1a import stability as ST  # noqa: E402

CENTS = {"train#0": np.array([1.0, 0]), "train#1": np.array([0.6, 0.8]),
         "train#2": np.array([0.0, 1.0]), "hotel#0": np.array([1.0, 0])}

# train#0: (value, doc, turn, left); to x4, from x3, via x2, by x1
A = [("london", 1, 0, "to"), ("paris", 1, 0, "to"), ("london", 2, 1, "to"), ("rome", 2, 1, "to"),
     ("oslo", 1, 0, "from"), ("bern", 1, 0, "from"), ("kiev", 2, 1, "from"),
     ("nice", 1, 0, "via"), ("lyon", 2, 1, "via"), ("graz", 1, 0, "by")]
B = [("9am", 1, 3, "at"), ("9am", 2, 5, "at")]
C = [("x", 3, 2, "")]
H = [("ritz", 1, 0, "at")]


def toy():
    rows = []
    for cid, ent, items in [("train#0", "train", A), ("train#1", "train", B),
                            ("train#2", "train", C), ("hotel#0", "hotel", H)]:
        for v, d, t, lw in items:
            rows.append(dict(cluster_id=cid, entity=ent, norm_value=v, dialogue_id=f"d{d}", turn=t,
                             left_word=lw, instance_id=f"d{d}|{ent}", gliner_score=0.5,
                             char_start=len(rows) * 10, char_end=len(rows) * 10 + 5))
    m = pd.DataFrame(rows)
    m["mention_id"] = np.arange(len(m))
    # vectors: train#0 -> [1,0]; train#1 -> [1,0] and [0,1]; others [1,0]
    x = np.tile([1.0, 0.0], (len(m), 1))
    x[len(A) + 1] = [0.0, 1.0]
    order = np.arange(len(m))[::-1]  # ids reversed: checks the id -> row mapping
    inst = pd.DataFrame({"instance_id": ["d1|train", "d2|train", "d3|train", "d1|hotel"],
                         "entity": ["train"] * 3 + ["hotel"]})
    exp = SimpleNamespace(mentions=m, instances=inst, ids=m["mention_id"].to_numpy()[order], x=x[order])
    co = nx.Graph()
    co.add_edge("train#0", "train#1", npmi=0.5)
    co.add_edge("train#0", "train#2", npmi=-0.2)
    co.add_node("hotel#0")
    gr = SimpleNamespace(co={"train": co, "hotel": nx.Graph()}, sim={}, cross=nx.Graph())
    return exp, gr


def test_wilson():
    lo, hi = S.wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3) and hi == pytest.approx(0.7634, abs=1e-3)
    assert all(np.isnan(S.wilson(0, 0)))
    assert S.wilson(10, 10)[1] == 1.0


def test_node_table(monkeypatch):
    from s1a import graph
    monkeypatch.setattr(graph, "centroids", lambda export: CENTS)
    exp, gr = toy()
    t = S.node_table(exp, gr, pd.Series({"train#0": 0.7}))
    a = t.loc["train#0"]
    assert (a.n_mentions, a.n_values, a.n_docs) == (10, 9, 2)
    assert (a.k, a.n) == (2, 3) and a.support == pytest.approx(2 / 3)
    assert a.wilson_lo < a.support < a.wilson_hi
    assert a.repetition == pytest.approx(1 / 9)
    assert a.cue_consistency == pytest.approx(0.9)
    assert a.cardinality == pytest.approx(5.0)
    assert a.proximity == pytest.approx(3.5)
    assert (a.degree, a.wdegree_npmi) == (2, 0.5)
    assert a.stability == 0.7 and a.confidence == 0.5
    assert a.separation == pytest.approx(0.6)
    assert a.cohesion == pytest.approx(1.0)
    b = t.loc["train#1"]
    assert b.proximity == pytest.approx(3.5) and b.cohesion == pytest.approx(0.0)
    assert np.isnan(b.stability) and b.repetition == 1.0
    assert np.isnan(t.loc["train#2", "proximity"]) and t.loc["train#2", "cohesion"] == 1.0
    h = t.loc["hotel#0"]
    assert np.isnan(h.separation) and h.degree == 0 and h.support == 1.0
    assert t.loc[["train#0", "train#1", "train#2"], "pagerank"].sum() == pytest.approx(1.0)
    assert h.pagerank == pytest.approx(1.0)


def stab_inputs():
    exp, _ = toy()
    docs = {f"d{i}": None for i in (1, 2, 3, 4)}
    return exp, docs


def test_stability_identical():
    exp, docs = stab_inputs()

    def fake(input, d, enc, seed):
        m = exp.mentions
        return SimpleNamespace(mentions=m[m["dialogue_id"].isin(d)])

    s = ST.stability_scores("spans", docs, None, exp, seeds=(0,), n_resamples=2, frac=0.75, build_fn=fake)
    assert s["train#0"] == 1.0 and s["train#1"] == 1.0


def test_stability_split():
    exp, docs = stab_inputs()

    def fake(input, d, enc, seed):
        m = exp.mentions[exp.mentions["dialogue_id"].isin(d)].copy()
        a = m["cluster_id"] == "train#0"
        half = m.loc[a, "char_start"] < 50
        m.loc[a, "cluster_id"] = np.where(half, "train#0a", "train#0b")
        return SimpleNamespace(mentions=m)

    s = ST.stability_scores("spans", docs, None, exp, seeds=(0,), n_resamples=1, frac=1.0, build_fn=fake)
    assert s["train#0"] == pytest.approx(0.5)
    assert s["train#1"] == 1.0
