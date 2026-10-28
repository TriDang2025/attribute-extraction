import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import hints as H  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a.mentions import Export  # noqa: E402


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def toy(vecs, attrs=None, per=2):
    """Export with one cluster E1#i per row of vecs (per mentions each, same vector), all in entity E1."""
    rows, x = [], []
    for i, v in enumerate(vecs):
        for _ in range(per):
            rows.append(dict(mention_id=len(rows), cluster_id=f"E1#{i}", entity="E1",
                             gold_attr=attrs[i] if attrs else "", context=f"ctx {i}"))
            x.append(unit(v))
    m = pd.DataFrame(rows)
    return Export(m, None, None, m["mention_id"].to_numpy(), np.stack(x))


def order(h):
    return {c: [d["other"] for d in lst] for c, lst in h.items()}


def test_string_equals_pilot_score():
    rng = np.random.default_rng(0)
    e = toy(rng.normal(size=(12, 5)))
    ref = PS.merge_hints(e.mentions, e.ids, e.x, "E1", k=3)
    got = H.merge_hints(e, "E1", "string", k=3)
    assert order(got) == ref
    assert all([d["rank"] for d in lst] == [1, 2, 3] for lst in got.values())


def test_window_uses_window_x():
    e = toy([[1, 0, 0], [0.9, 0.1, 0], [0, 1, 0]])
    assert order(H.merge_hints(e, "E1", "string", k=1))["E1#0"] == ["E1#1"]
    wx = np.stack([unit(v) for v in [[1, 0, 0]] * 2 + [[0, 1, 0]] * 2 + [[0.9, 0.1, 0]] * 2])  # cluster 0 ~ cluster 2
    assert order(H.merge_hints(e, "E1", "window", wx, k=1))["E1#0"] == ["E1#2"]
    assert np.isclose(H.merge_hints(e, "E1", "window", wx, k=1)["E1#0"][0]["cos"], unit([0.9, 0.1, 0]) @ [1, 0, 0])


def test_pct():
    e = toy([[1, 0], [0.9, 0.1], [0, 1], [-1, 0.2]])
    h = H.merge_hints(e, "E1", "string", k=1)
    best = max(h.values(), key=lambda l: l[0]["cos"])[0]
    assert best["pct"] == 100.0  # the closest pair of the entity
    assert all(0 < d["pct"] <= 100 for lst in h.values() for d in lst)


def test_filtered_drops_hub_and_low_pct():
    # E1#0 is nearest to everyone (hub); the others form two tight pairs apart from it
    vecs = [[1, 1, 0], [1, 0.1, 1], [1, 0, 1.1], [1, 1, -0.1] , [1, 1.1, 0], [1, 0.9, 0.1],
            [1, 0.1, 0.9], [1, 0.05, 1.2], [0.2, 1, 1], [-1, 0.5, 0.2]]
    # make cluster 0 the centre of mass: nearest to all
    vecs[0] = np.mean([unit(v) for v in vecs[1:]], axis=0)
    e = toy(vecs)
    win = H.merge_hints(e, "E1", "window", e.x)
    n0 = sum(d["other"] == "E1#0" for lst in win.values() for d in lst)
    assert n0 >= 5
    fil = H.merge_hints(e, "E1", "filtered", e.x)
    assert all(d["other"] != "E1#0" for lst in fil.values() for d in lst)
    assert all(d["pct"] >= 80 for lst in fil.values() for d in lst)
    assert sum(len(l) for l in fil.values()) < sum(len(l) for l in win.values())
    assert set(fil) == set(win)  # lists may be empty, keys stay


def test_filtered_pct_cutoff_only():
    # two close pairs and far singletons: no hub, only the close pairs survive pct >= 80
    e = toy([[1, 0, 0], [0.99, 0.1, 0], [0, 1, 0], [0.1, 0.99, 0], [0, 0, 1], [0.5, 0.5, 0.7]], per=1)
    fil = H.merge_hints(e, "E1", "filtered", e.x, k=2)
    kept = {(c, d["other"]) for c, lst in fil.items() for d in lst}
    assert ("E1#0", "E1#1") in kept and ("E1#2", "E1#3") in kept
    assert all(d["pct"] >= 80 for lst in fil.values() for d in lst)


def test_precision():
    e = toy([[1, 0], [1, 0.1], [0, 1], [0, 1.1]], attrs=["a", "a", "b", ""])
    maj = H.majority_classes(e.mentions)
    assert maj == {"E1#0": "a", "E1#1": "a", "E1#2": "b"}
    hints = {"E1#0": [dict(other="E1#1"), dict(other="E1#2")], "E1#2": [dict(other="E1#3")], "E1#3": []}
    assert H.hint_precision(hints, e.mentions) == (3, 1)  # E1#3 has no majority: not same class


def test_encode_save_load(tmp_path):
    e = toy([[1, 0], [0, 1]], per=2)

    class Fake:
        def encode(self, texts):
            return np.array([[len(t), 1.0] for t in texts])

    wx = H.encode_windows(e, Fake())
    assert wx.shape == (4, 2) and wx[0, 0] == len("ctx 0")
    H.save_window(tmp_path / "w.npz", e.ids, wx)
    ids, x = H.load_window(tmp_path / "w.npz")
    assert (ids == e.ids).all() and np.allclose(x, wx)
