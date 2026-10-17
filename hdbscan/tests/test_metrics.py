import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hbe import config, data, metrics  # noqa: E402


def test_purity_hand_case():
    # clusters: A={a,a,b}, B={b,c}; majority 2 + 1 = 3 of 5
    assert metrics.purity(list("aabbc"), list("AAABB")) == pytest.approx(3 / 5)


def test_bcubed_hand_case():
    true, pred = list("aabbc"), list("AAABB")
    # precision per item: a:2/3, a:2/3, b:1/3, b:1/2, c:1/2
    # recall per item:    a:2/2, a:2/2, b:1/2, b:1/2, c:1/1
    p = (2 / 3 + 2 / 3 + 1 / 3 + 1 / 2 + 1 / 2) / 5
    r = (1 + 1 + 1 / 2 + 1 / 2 + 1) / 5
    bp, br, bf = metrics.bcubed(true, pred)
    assert bp == pytest.approx(p) and br == pytest.approx(r)
    assert bf == pytest.approx(2 * p * r / (p + r))


def test_perfect_and_noise_as_cluster():
    ext = metrics.external(list("aabb"), [0, 0, 1, 1])
    assert ext["purity"] == ext["bcubed_f1"] == ext["ari"] == pytest.approx(1.0)
    # noise (-1) is one ordinary cluster, as in the repo
    ext = metrics.external(list("aabb"), [-1, -1, -1, -1])
    assert ext["gold_k_pred"] == 1 and ext["bcubed_recall"] == pytest.approx(1.0)


def test_internal_excludes_noise():
    rng = np.random.RandomState(0)
    x = np.vstack([rng.normal(0, .1, (20, 2)), rng.normal(5, .1, (20, 2)), rng.normal(50, 1, (5, 2))])
    lab = np.array([0] * 20 + [1] * 20 + [-1] * 5)
    m = metrics.internal(x, lab)
    assert m["K"] == 2 and m["n_clustered"] == 40
    assert m["noise_pct"] == pytest.approx(100 * 5 / 45)
    assert m["silhouette"] > 0.9


@pytest.mark.skipif(not (config.DATA / "hf" / "train.parquet").exists(), reason="data not fetched")
def test_corpus_matches_repo_order():
    import pandas as pd
    corpus = data.hansard_corpus()
    ref = pd.read_csv(config.DATA / "v11_cluster_assignments.csv")
    assert len(corpus) == 19553
    assert (corpus["speech_id"].values == ref["speech_id"].values).all()
    assert (corpus["year"].values == ref["year"].astype(int).values).all()


@pytest.mark.skipif(not (config.DATA / "ground_truth_300.csv").exists(), reason="data not fetched")
def test_gold_join_269():
    import pandas as pd
    ref = pd.read_csv(config.DATA / "v11_cluster_assignments.csv").rename(columns={"hdbscan_cluster": "cluster"})
    assert len(data.gold(config.DATA)) == 273
    assert len(data.gold_join(ref)) == 269


def test_conversation_labels():
    df = data.conversation()
    assert len(df) == 1000 and df["id"].is_unique
    assert df["main_domain"].isin(df["domain_set"].str.split("+").explode().unique()).all()
