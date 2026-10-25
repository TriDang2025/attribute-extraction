import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import labels as L  # noqa: E402
from s1a import node_filter as S  # noqa: E402


def toy(n=40):
    rng = np.random.default_rng(0)
    cid = [f"E0#{i}" for i in range(n)]
    real = np.arange(n) < n // 2
    nodes = pd.DataFrame({
        "cluster_id": cid,
        "sep": np.where(real, 1.0, 0.0) + rng.random(n) * 0.1,        # perfect, higher = real
        "sep_copy": np.where(real, 1.0, 0.0) + rng.random(n) * 0.1,   # near-duplicate of sep
        "rev": 0.0,  # filled below: exact mirror of sep, lower = real
        "junk": rng.random(n),
        "wilson_hi": np.where(np.arange(n) % 10 == 0, 0.01, 0.5),
    })
    nodes["rev"] = 1.0 - nodes["sep"]
    labels = pd.DataFrame({"cluster_id": cid, "label": np.where(real, "gold", "noise"),
                           "gold_attr": [f"a{i}" if r else "" for i, r in enumerate(real)]})
    return nodes, labels


def test_gold_labels_purity():
    m = pd.DataFrame({
        "cluster_id": ["c1"] * 5 + ["c2"] * 4 + [""],
        "gold_attr": ["a", "a", "a;b", "", "b", "a", "b", "", "", "a"],
    })
    g = L.gold_labels(m).set_index("cluster_id")
    assert g.loc["c1", "purity"] == pytest.approx(3 / 5)  # a counts 3 of 5 members
    assert g.loc["c1", "label"] == "gold" and g.loc["c1", "gold_attr"] == "a"
    assert g.loc["c2", "purity"] == pytest.approx(1 / 4)
    assert g.loc["c2", "label"] == "unlabelled" and g.loc["c2", "gold_attr"] == ""
    assert "" not in g.index


def test_sheet_and_merge():
    m = pd.DataFrame({"cluster_id": [f"c{i}" for i in range(6) for _ in range(i + 1)],
                      "norm_value": "v", "context": "ctx", "entity": "E0"})
    lab = pd.DataFrame({"cluster_id": [f"c{i}" for i in range(6)], "label": "unlabelled",
                        "gold_attr": "", "purity": 0.0, "label_by": "rule"})
    lab.loc[0, "label"] = "gold"
    sh = L.sheet(m, lab, n=3, seed=1)
    assert len(sh) == 3 and "c0" not in set(sh["cluster_id"])
    assert len(L.sheet(m, lab, n=50)) == 5
    sh["label"] = ["valid_new", "noise", ""][: len(sh)]
    out = L.merge_sheet(lab, sh)
    assert (out["label_by"] == "human").sum() == 2
    sh.loc[0, "label"] = "bogus"
    with pytest.raises(ValueError):
        L.merge_sheet(lab, sh)


def test_auc_perfect_and_direction():
    nodes, labels = toy()
    t = S.auc_table(nodes, labels, ["sep", "rev", "junk"], n_boot=50).set_index("signal")
    assert t.loc["sep", "auc"] == 1.0 and t.loc["sep", "direction"] == 1
    assert t.loc["rev", "auc"] == 0.0 and t.loc["rev", "direction"] == -1
    assert t.loc["rev", "auc_oriented"] == 1.0
    assert t.loc["sep", "lo"] <= t.loc["sep", "hi"] <= 1.0
    assert t.loc["junk", "auc_oriented"] < 0.85
    assert t.loc["sep", "n_real"] == 20 and t.loc["sep", "n_noise"] == 20


def test_auc_ignores_unlabelled_and_nan():
    nodes, labels = toy()
    labels.loc[:4, "label"] = "unlabelled"
    nodes.loc[5, "sep"] = np.nan
    t = S.auc_table(nodes, labels, ["sep"], n_boot=10).iloc[0]
    assert t["n_real"] == 14 and t["n_noise"] == 20


def test_choose_skips_correlated():
    nodes, labels = toy()
    sigs = ["sep", "sep_copy", "rev", "junk"]
    auc = S.auc_table(nodes, labels, sigs, n_boot=10)
    corr = S.correlations(nodes, sigs)
    got = [s for s, _ in S.choose(auc, corr, corr_max=0.8)]
    assert "sep" in got and "sep_copy" not in got
    assert "rev" not in got  # |rho| with sep is high too
    assert all(isinstance(r, str) and r for _, r in S.choose(auc, corr))


def test_combine():
    nodes, labels = toy()
    d = {"sep": 1, "rev": -1}
    r = S.combine(nodes, ["sep", "rev"], d, "rank")
    assert r.between(0, 1).all() and r[:20].mean() > r[20:].mean()
    w = S.combine(nodes, ["sep", "rev"], d, "weak2")
    assert (w <= 0).all() and w[:20].mean() > w[20:].mean()


def test_sweep_pick_apply():
    nodes, labels = toy()
    score = S.combine(nodes, ["sep", "rev"], {"sep": 1, "rev": -1})
    attrs = [f"a{i}" for i in range(20)]
    sw = S.sweep(nodes, labels, score, attrs, thetas=(0.05, 0.2))
    assert set(sw["theta"]) == {0.05, 0.2}
    for _, g in sw.groupby("theta"):
        g = g.sort_values("threshold")
        assert g["kept"].is_monotonic_decreasing
        assert g["attr_covered"].is_monotonic_decreasing
    top = sw[sw["kept"] > 0].sort_values("threshold").iloc[-1]
    assert top["node_precision"] == 1.0
    assert sw["kept"].max() == 36  # 4 of 40 nodes have wilson_hi < theta
    assert (sw["llm_saved"] + sw["kept"] == 40).all()
    row = S.pick(sw, target_prec=0.9, min_attrs=5)
    assert row["target_met"] and row["node_precision"] >= 0.9 and row["attr_covered"] >= 5
    row = S.pick(sw, target_prec=2.0, min_attrs=5)
    assert not row["target_met"]
    out = S.apply(nodes, score, 0.05, row["threshold"])
    assert len(out) == 40 and set(out["status"]) <= {"kept", "dropped"}
    assert set(out.loc[out["wilson_hi"] < 0.05, "reason"]) == {"support"}
    assert (out.loc[out["status"] == "kept", "reason"] == "").all()


def test_plot_curve(tmp_path):
    nodes, labels = toy()
    score = S.combine(nodes, ["sep"], {"sep": 1})
    sw = S.sweep(nodes, labels, score, [f"a{i}" for i in range(20)])
    S.plot_curve(sw, tmp_path / "c.png", min_attrs=1)
    assert (tmp_path / "c.png").exists()
