from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from s1a import graph as G

# (cluster, instance) per mention; instance -> dialogue
ROWS = [("E0#0", "i1"), ("E0#0", "i2"), ("E0#0", "i4"), ("E0#1", "i1"), ("E0#1", "i2"), ("E0#2", "i3"),
        ("E1#0", "j1"), ("E1#0", "j2"), ("E1#1", "j1"), ("E1#1", "j2")]
DLG = {"i1": "d1", "i2": "d2", "i3": "d3", "i4": "d4", "j1": "d1", "j2": "d2"}
VEC = {"E0#0": [(1, 0), (1, 0), (0, 1)], "E0#1": [(1, 0)] * 2, "E0#2": [(0, 1)], "E1#0": [(1, 0)] * 2, "E1#1": [(1, 0)] * 2}


def toy():
    m = pd.DataFrame([dict(mention_id=k, dialogue_id=DLG[i], cluster_id=c, instance_id=i) for k, (c, i) in enumerate(ROWS)])
    nm = m.groupby("cluster_id").size()
    cl = pd.DataFrame([dict(cluster_id=c, entity=c.split("#")[0], n_mentions=int(nm[c]), top_values=f"v{c}|w")
                       for c in nm.index])
    inst = pd.DataFrame([dict(instance_id=i, entity="E0" if i[0] == "i" else "E1", dialogue_id=d,
                              start_turn=0, end_turn=0) for i, d in DLG.items()])
    seen = {c: iter(v) for c, v in VEC.items()}
    x = np.array([next(seen[c]) for c, _ in ROWS], dtype=np.float32)
    return SimpleNamespace(mentions=m, clusters=cl, instances=inst, ids=m["mention_id"].values, x=x)


def test_co_edges():
    g = G.build_graphs(toy()).co["E0"]
    ab = g["E0#0"]["E0#1"]
    assert ab["count"] == 2
    assert ab["jaccard"] == pytest.approx(2 / 3)
    assert ab["npmi"] == pytest.approx(np.log(0.5 / 0.375) / np.log(2))  # n=4 instances, p(a)=.75, p(b)=.5
    assert not g.has_edge("E0#0", "E0#2")  # never in the same instance
    assert g.nodes["E0#0"]["n_mentions"] == 3 and g.nodes["E0#0"]["top_values"] == ["vE0#0", "w"]


def test_always_together_npmi_is_one():
    e1 = G.build_graphs(toy()).co["E1"]["E1#0"]["E1#1"]
    assert e1["npmi"] == 1.0 and e1["jaccard"] == 1.0 and e1["count"] == 2


def test_sim_edges_and_centroids():
    ex = toy()
    c = G.centroids(ex)
    assert np.linalg.norm(c["E0#0"]) == pytest.approx(1.0)
    np.testing.assert_allclose(c["E0#0"], np.array([2, 1]) / np.sqrt(5), atol=1e-6)
    s = G.build_graphs(ex).sim["E0"]
    assert s.number_of_edges() == 3  # all pairs of 3 clusters
    assert s["E0#0"]["E0#1"]["cos"] == pytest.approx(2 / np.sqrt(5))
    assert s["E0#1"]["E0#2"]["cos"] == pytest.approx(0.0)


def test_cross_edges():
    x = G.build_graphs(toy()).cross
    assert x["E0#1"]["E1#0"]["count"] == 2 and x["E0#1"]["E1#0"]["npmi"] == pytest.approx(1.0)
    assert x["E0#0"]["E1#0"]["npmi"] == pytest.approx(np.log(0.5 / 0.375) / np.log(2))  # 4 dialogues
    assert not x.has_edge("E0#2", "E1#0")  # no shared dialogue
    assert not x.has_edge("E0#0", "E0#1")  # same entity


def test_save_load_draw(tmp_path):
    g = G.build_graphs(toy())
    G.save(g, tmp_path / "g.pkl")
    g2 = G.load(tmp_path / "g.pkl")
    assert set(g2.co) == {"E0", "E1"} and g2.cross.number_of_edges() == g.cross.number_of_edges()
    G.draw_entity(g2, "E0", tmp_path / "e0.png", top=2)
    assert (tmp_path / "e0.png").stat().st_size > 0
