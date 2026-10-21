"""The clusterer grid: HDBSCAN, agglomerative (cosine, average) and k-means, on raw bge-m3
vectors and on UMAP-5D (the HDBSCAN reproduction's settings)."""

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans

from . import paths  # noqa: F401
from hbe.cluster import hdbscan_labels, umap_reduce

UMAP_SEEDS = (42, 0, 1)
KMEANS_SEEDS = (42, 0, 1)
HDB_SIZES = (3, 5, 10, 20)
HDB_SELECT = ("eom", "leaf")
HDB_MIN_SAMPLES = (1, 5)
AGG_THRESHOLDS = (0.2, 0.3, 0.4, 0.5, 0.6)
KS = (5, 10, 20, 35, 50)


def spaces(emb):
    """(space name, seed, matrix): raw once, UMAP once per seed."""
    yield "raw", 0, emb
    n_nb = min(15, len(emb) - 1)
    for s in UMAP_SEEDS:
        yield "umap5", s, umap_reduce(emb, seed=s, n_neighbors=n_nb)


def runs(x, space, gold_k):
    """Yield (method, setting, seed, labels)."""
    n = len(x)
    metric = "cosine" if space == "raw" else "euclidean"
    for size in HDB_SIZES:
        if size >= n:
            continue
        for sel in HDB_SELECT:
            for ms in HDB_MIN_SAMPLES:
                # the hdbscan library has no cosine with its fast trees; raw vectors are unit-norm,
                # so euclidean ranks neighbours the same way
                lab = hdbscan_labels(x, min_cluster_size=size, min_samples=ms,
                                     cluster_selection_method=sel, metric="euclidean")
                yield "hdbscan", f"mcs={size},{sel},ms={ms}", 0, lab
    for k in sorted(set(KS) | {gold_k}):
        if k >= n:
            continue
        yield "agglo", f"k={k}", 0, AgglomerativeClustering(
            n_clusters=k, metric=metric, linkage="average").fit_predict(x)
        for s in KMEANS_SEEDS:
            yield "kmeans", f"k={k}", s, KMeans(k, n_init=10, random_state=s).fit_predict(x)
    if space == "raw":
        for t in AGG_THRESHOLDS:
            lab = AgglomerativeClustering(n_clusters=None, distance_threshold=t, metric="cosine",
                                          linkage="average").fit_predict(x)
            yield "agglo", f"thr={t}", 0, lab


def n_clusters(labels):
    labels = np.asarray(labels)
    return int(len(set(labels)) - (1 if -1 in labels else 0)), float((labels == -1).mean() * 100)
