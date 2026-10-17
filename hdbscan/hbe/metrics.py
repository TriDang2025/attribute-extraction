"""Cluster metrics, matching the repo's definitions.

- External (classification_metrics.py): purity, B-Cubed P/R/F1, ARI, NMI. Labels are
  compared as strings, so HDBSCAN noise (-1) is one ordinary cluster.
- Internal (run_macro_topic_modeling.ipynb cell 16): noise excluded; silhouette on a
  stratified sample of at most 5000 points (seed 42); CH and DB on all clustered points.
"""

from collections import Counter, defaultdict

import numpy as np
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, normalized_mutual_info_score,
                             silhouette_score)


def purity(true, pred):
    true, pred = [str(x) for x in true], [str(x) for x in pred]
    clusters = defaultdict(Counter)
    for t, p in zip(true, pred):
        clusters[p][t] += 1
    return sum(max(c.values()) for c in clusters.values()) / len(true) if true else 0.0


def bcubed(true, pred):
    true, pred = [str(x) for x in true], [str(x) for x in pred]
    if not true:
        return 0.0, 0.0, 0.0
    pc, tc, pair = Counter(pred), Counter(true), Counter(zip(true, pred))
    p = float(np.mean([pair[(t, q)] / pc[q] for t, q in zip(true, pred)]))
    r = float(np.mean([pair[(t, q)] / tc[t] for t, q in zip(true, pred)]))
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def external(true, pred):
    true, pred = [str(x) for x in true], [str(x) for x in pred]
    p, r, f = bcubed(true, pred)
    return {
        "gold_n": len(true), "gold_k_true": len(set(true)), "gold_k_pred": len(set(pred)),
        "purity": purity(true, pred), "bcubed_precision": p, "bcubed_recall": r,
        "bcubed_f1": f, "ari": float(adjusted_rand_score(true, pred)),
        "nmi": float(normalized_mutual_info_score(true, pred)),
    }


def silhouette_stratified(emb, labels, max_total=5000, seed=42):
    labels = np.asarray(labels)
    mask = labels != -1
    if mask.sum() < 2 or len(set(labels[mask])) < 2:
        return 0.0
    x, y = emb[mask], labels[mask]
    if len(y) <= max_total:
        return float(silhouette_score(x, y))
    rng = np.random.RandomState(seed)
    uniq, counts = np.unique(y, return_counts=True)
    n_take = np.maximum(1, (counts / counts.sum() * max_total).astype(int))
    idx = []
    for lab, n in zip(uniq, n_take):
        members = np.where(y == lab)[0]
        idx.extend(rng.choice(members, size=min(n, len(members)), replace=False))
    idx = np.array(idx)
    return float(silhouette_score(x[idx], y[idx]))


def internal(emb, labels, max_total=5000):
    labels = np.asarray(labels)
    valid = labels != -1
    ok = valid.sum() > 1 and len(set(labels[valid])) > 1
    return {
        "K": int(len(set(labels[valid]))),
        "noise_pct": float(100 * (~valid).sum() / len(labels)),
        "n_clustered": int(valid.sum()),
        "silhouette": silhouette_stratified(emb, labels, max_total) if ok else 0.0,
        "calinski_harabasz": float(calinski_harabasz_score(emb[valid], labels[valid])) if ok else 0.0,
        "davies_bouldin": float(davies_bouldin_score(emb[valid], labels[valid])) if ok else 0.0,
    }


def agreement(a, b):
    """ARI/NMI between two full labelings (noise kept as a label)."""
    return {"ari": float(adjusted_rand_score(a, b)), "nmi": float(normalized_mutual_info_score(a, b))}


def knn_overlap(x, y, k=15, n_sample=2000, seed=0):
    """Mean share of each point's k nearest neighbours shared between two embeddings."""
    from sklearn.neighbors import NearestNeighbors
    rng = np.random.RandomState(seed)
    idx = rng.choice(len(x), size=min(n_sample, len(x)), replace=False)
    nx = NearestNeighbors(n_neighbors=k + 1).fit(x).kneighbors(x[idx], return_distance=False)[:, 1:]
    ny = NearestNeighbors(n_neighbors=k + 1).fit(y).kneighbors(y[idx], return_distance=False)[:, 1:]
    return float(np.mean([len(set(a) & set(b)) / k for a, b in zip(nx, ny)]))
