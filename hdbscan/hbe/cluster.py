"""UMAP -> HDBSCAN, as in run_macro_topic_modeling.ipynb cells 8 and 10."""

import numpy as np

from . import config


def umap_reduce(emb, seed=config.RANDOM_STATE, **overrides):
    from umap import UMAP
    params = {**config.UMAP_PARAMS, **overrides}
    return UMAP(random_state=seed, **params).fit_transform(emb)


def hdbscan_labels(x, **overrides):
    from hdbscan import HDBSCAN
    params = {**config.HDBSCAN_PARAMS, **overrides}
    return HDBSCAN(**params).fit_predict(x).astype(int)


def summary(labels):
    labels = np.asarray(labels)
    k = len(set(labels)) - (1 if -1 in labels else 0)
    return {"K": int(k), "noise_pct": round(100 * float((labels == -1).mean()), 1)}
