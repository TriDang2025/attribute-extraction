"""Merge hints for the Step-3 pilot (contract: PILOT_V31_CONTRACT.md, section Hints).

For each cluster of one predicted entity: the k nearest other clusters by cosine of cluster centroids.
Modes: string (centroids of export.x, the wf_v3 hints), window (centroids of bge-m3 vectors of each mention's
`context` column), filtered (window, minus hub clusters, minus pairs under the 80th percentile).
"""

from collections import Counter
from itertools import combinations
from types import SimpleNamespace

import numpy as np

from . import graph as GR
from .pilot_input import _percentile
from .pilot_score import mode

HUB_FACTOR = 2.0   # hub = appears in more than HUB_FACTOR x the mean number of top-k lists
MIN_PCT = 80.0     # filtered mode keeps pairs with pct >= MIN_PCT
MODES = ("string", "window", "filtered")


def _lists(export, entity, x, k):
    """({cluster: [(other, cos)] nearest first, up to k}, all pair cosines) of the entity's clusters from vectors x.
    Cluster names sorted as strings and a stable sort, so ties order like pilot_score.merge_hints."""
    cen = GR.centroids(SimpleNamespace(mentions=export.mentions, ids=export.ids, x=x))
    names = sorted(c for c in cen if c.split("#")[0] == entity)
    if not names:
        return {}, np.array([])
    m = np.stack([cen[c] for c in names])
    sim = m @ m.T
    out = {}
    for i, c in enumerate(names):
        order = [j for j in np.argsort(-sim[i], kind="stable") if j != i]
        out[c] = [(names[j], float(sim[i, j])) for j in order[:k]]
    pairs = np.array([sim[i, j] for i, j in combinations(range(len(names)), 2)])
    return out, pairs


def merge_hints(export, entity, mode, window_x=None, k=3):
    """{cluster_id: [dict(other, rank, cos, pct)]} for the clusters of `entity`; pct = percentile (0-100) of the pair
    cosine among all cluster pairs of the entity. window_x: one row per export.ids row (window / filtered modes).
    filtered: hubs (counted on the unfiltered top-k lists) are dropped as `other`, the lists are not refilled."""
    if mode not in MODES:
        raise ValueError(f"mode {mode!r} not in {MODES}")
    if mode != "string":
        if window_x is None or len(window_x) != len(export.ids):
            raise ValueError("window_x must have one row per export.ids row")
    lists, pairs = _lists(export, entity, export.x if mode == "string" else window_x, k)
    out = {c: [dict(other=o, rank=r, cos=cs, pct=_percentile(pairs, cs)) for r, (o, cs) in enumerate(lst, 1)]
           for c, lst in lists.items()}
    if mode != "filtered":
        return out
    cnt = Counter(h["other"] for lst in out.values() for h in lst)
    mean = sum(cnt.values()) / len(out) if out else 0.0
    hubs = {c for c, n in cnt.items() if n > HUB_FACTOR * mean}
    return {c: [h for h in lst if h["other"] not in hubs and h["pct"] >= MIN_PCT] for c, lst in out.items()}


def majority_classes(mentions):
    """{cluster_id: majority gold_attr} for clusters with at least one gold-labelled mention."""
    m = mentions[(mentions["cluster_id"].fillna("") != "") & (mentions["gold_attr"].fillna("") != "")]
    return {c: mode(g["gold_attr"]) for c, g in m.groupby("cluster_id")}


def same_class(a, b, maj):
    """Both clusters have a majority gold_attr and it is equal."""
    return a in maj and b in maj and maj[a] == maj[b]


def hint_precision(hints, mentions):
    """(n_hints, n_same_class) over every (cluster, other) pair in hints."""
    maj = majority_classes(mentions)
    pairs = [(c, h["other"]) for c, lst in hints.items() for h in lst]
    return len(pairs), sum(same_class(a, b, maj) for a, b in pairs)


def encode_windows(export, enc):
    """bge-m3 (or any object with .encode(list of str) -> array) vectors of each mention's `context`, in
    export.ids order."""
    ctx = dict(zip(export.mentions["mention_id"].astype(int), export.mentions["context"].fillna("")))
    return np.asarray(enc.encode([str(ctx[int(i)]) for i in export.ids]), dtype=np.float32)


def save_window(path, ids, x):
    np.savez(path, ids=np.asarray(ids, dtype=int), x=np.asarray(x, dtype=np.float32))


def load_window(path):
    v = np.load(path)
    return v["ids"], v["x"]
