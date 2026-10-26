"""wf_v2.2 part I: multi-view clustering (CMVC, KDD 2022). The string view and the context view stay
separate; per partition (stage-1 group, value type) their cosine DISTANCES are combined with per-view
weights, D = w_s * D_s + w_c * D_c, instead of averaging the vectors. The number of clusters is a
distance threshold t or Log-Jump (largest jump of log merge distance).
"""

from collections import defaultdict
from functools import partial

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import calinski_harabasz_score

from . import step2 as S2
from .combos import V21_FILTER, V21_TEXT
from .variants import Variant

FLOOR = 0.01  # merge distances are floored here before the log: duplicate strings (d = 0) must not dominate


def cosine_dist(x):
    x = S2._unit(np.asarray(x, float))
    return np.clip(1 - x @ x.T, 0, 2)


def threshold_labels(D, t):
    """Agglomerative (precomputed, average), distance threshold t. Labels 0..K-1."""
    if len(D) == 1:
        return np.zeros(1, dtype=int)
    return AgglomerativeClustering(n_clusters=None, distance_threshold=t, metric="precomputed",
                                   linkage="average").fit_predict(D)


def log_jump_k(merge_d):
    """K from ascending merge distances d_1..d_{n-1} (n items): cutting after merge i leaves n - i clusters;
    pick i (1..n-2) with the largest log d_{i+1} - log d_i. K lies in 2..n-1 (needs n >= 3)."""
    d = np.log(np.maximum(np.asarray(merge_d, float), FLOOR))
    i = int(np.argmax(np.diff(d))) + 1
    return len(merge_d) + 1 - i


def log_jump_labels(D):
    """Full average-linkage merge sequence on D, cut at the Log-Jump K. n < 3: the threshold result at
    t = 0.4 (one item -> one cluster; two items merge only when close, as the t 0.4 variants do)."""
    n = len(D)
    if n < 3:
        return threshold_labels(D, 0.4)
    Z = linkage(squareform(np.asarray(D, float), checks=False), method="average")
    return fcluster(Z, log_jump_k(Z[:, 2]), criterion="maxclust") - 1


def view_quality(x, t=0.4):
    """Calinski-Harabasz index of the view's own agglomerative clustering at t; None if it has < 2 clusters
    (or n - 1 or more, where the index is undefined)."""
    lab = threshold_labels(cosine_dist(x), t)
    if not 2 <= len(set(lab)) < len(x):
        return None
    return float(calinski_harabasz_score(x, lab))


def view_weights(xs, xc, weights, t=0.4):
    """(w_s, w_c) summing to 1. weights = (w_s, w_c) fixed (normalised), or "ch": CH quality of each view,
    normalised; fixed 0.5 / 0.5 when either view gives < 2 clusters."""
    if weights != "ch":
        ws, wc = weights
        return ws / (ws + wc), wc / (ws + wc)
    qs, qc = view_quality(xs, t), view_quality(xc, t)
    if qs is None or qc is None:
        return 0.5, 0.5
    return qs / (qs + qc), qc / (qs + qc)


def partition_labels(xs, xc, weights, method, t=0.4):
    """Cluster one partition: combine the two views' distances, then threshold t or Log-Jump."""
    ws, wc = view_weights(xs, xc, weights, t)
    D = ws * cosine_dist(xs) + wc * cosine_dist(xc)
    return log_jump_labels(D) if method == "lj" else threshold_labels(D, t)


def cluster_fn(spans, docs, enc, groups, books, weights="ch", method="t", t=0.4, k=2):
    """Variant cluster_fn. Returns (string vectors, labels). Views: string = encode(V21_TEXT(text)),
    context = encode(k-word symmetric masked window, target marked)."""
    by_doc = defaultdict(list)
    for u in spans:
        by_doc[u.doc_id].append(u)
    xs = enc.encode([V21_TEXT(u.text) for u in spans])
    xc = enc.encode([S2.window_texts(docs[u.doc_id], u, by_doc[u.doc_id], k, side="sym") for u in spans])
    parts = [(g, S2.value_type(u.text)) for g, u in zip(groups, spans)]
    lab = [None] * len(spans)
    for g, idx in S2._by_group(parts).items():
        for i, c in zip(idx, partition_labels(xs[idx], xc[idx], weights, method, t)):
            lab[i] = f"{S2._name(g)}:{c}"
    return xs, lab


def _v(wname, weights, mname, method, k):
    wtxt = "CH view-quality weights" if weights == "ch" else f"fixed weights {weights[0]}/{weights[1]}"
    mtxt = "Log-Jump K" if method == "lj" else "threshold t 0.4"
    return f"I_{wname}_{mname}_k{k}", Variant(
        span_filter=V21_FILTER, cluster_fn=partial(cluster_fn, weights=weights, method=method, t=0.4, k=k),
        note=f"multi-view distances, {wtxt}, {mtxt}, window k {k}")


_W = {"ch": "ch", "w07": (0.7, 0.3), "w05": (0.5, 0.5)}
_M = {"t04": "t", "lj": "lj"}
CONFIGS = dict(_v(w, _W[w], m, _M[m], 2) for w in _W for m in _M)
CONFIGS |= dict(_v("ch", "ch", m, _M[m], 3) for m in _M)
