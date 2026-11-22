"""wf_v5.0 G3 (S3): context split. Step 3's A marks two-role clusters and the split pass cuts them into parts, but it cuts by surface
format ("time str" / "time int"), not by role ("leave after" / "arrive by"). This post-step keeps A's decision and the number of parts
and only reassigns the cluster's mentions to the parts: k-means (k = number of parts, seed 0) on bge-m3 vectors of each mention's left
context (the last W words of the turn before the value). New parts are matched to the old parts by largest mention overlap (Hungarian),
so every part keeps its name, column and joins. No gold, no word list. Switch: `min_parts`/`max_parts` select the split clusters it
touches, `min_size` the smallest cluster (wf_v5.0: 40, set on dev50, where every cluster the context split hurt had <= 28 mentions)
(off = not run).

Limit of the replay: reconcile / duplicate check decided on the old parts' examples; a GPU rerun could decide differently.
"""

import re

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans

W = 4
SEED = 0


def left_context(text, lo, start, w=W):
    """The last `w` words of text[lo:start] ("[start]" when the value opens the turn)."""
    words = re.findall(r"[\w']+", text[lo:start])
    return " ".join(words[-w:]) or "[start]"


def kmeans_parts(x, k, seed=SEED):
    """Labels 0..k-1 of the rows of x (unit vectors)."""
    if k < 2 or len(x) < k:
        return np.zeros(len(x), dtype=int)
    return KMeans(k, n_init=10, random_state=seed).fit(x).labels_


def match_parts(old, new_labels, ids):
    """{new label: old part key}: Hungarian on the mention overlap. old = {part key: set of mention ids}; ids = mention ids in row order."""
    keys = list(old)
    labs = sorted(set(new_labels))
    gain = np.array([[sum(1 for i, l in zip(ids, new_labels) if l == lab and i in old[k]) for k in keys] for lab in labs])
    rows, cols = linear_sum_assignment(-gain)
    return {labs[r]: keys[c] for r, c in zip(rows, cols)}


def reassign(parts, vec, min_parts=2, max_parts=99, min_size=0, seed=SEED):
    """{part key: new mention id list} for the split clusters with min_parts..max_parts parts and >= min_size mentions in parts.
    parts = columns.json parts (key, cluster, mention_ids); vec = {mention_id: unit vector}. Other clusters keep their parts."""
    by_cluster = {}
    for p in parts:
        by_cluster.setdefault(p["cluster"], {})[p["key"]] = {int(i) for i in p["mention_ids"]}
    out = {}
    for _cl, old in by_cluster.items():
        if not min_parts <= len(old) <= max_parts or len(set().union(*old.values())) < min_size:
            out.update({k: sorted(v) for k, v in old.items()})
            continue
        ids = sorted(set().union(*old.values()))
        labels = kmeans_parts(np.stack([vec[i] for i in ids]), len(old), seed)
        to_old = match_parts(old, labels, ids)
        new = {k: [] for k in old}
        for i, lab in zip(ids, labels):
            new[to_old[lab]].append(i)
        out.update(new)
    return out


def apply(columns, parts, new_parts):
    """Columns of one entity with the mentions of each split part replaced by its new mentions. A column holds a part when the part key is
    one of its members; mentions of the part's cluster that are in no part are left as they are."""
    old = {p["key"]: {int(i) for i in p["mention_ids"]} for p in parts}
    out = []
    for col in columns:
        ids = [int(i) for i in col["mention_ids"]]
        mine = [m for m in col["members"] if m in old]
        if not mine:
            out.append(col)
            continue
        drop = set().union(*(old[m] for m in mine))
        add = [i for m in mine for i in new_parts[m]]
        keep = [i for i in ids if i not in drop]
        new_ids = sorted(set(keep) | set(add))
        out.append({**col, "mention_ids": new_ids, "n_mentions": len(new_ids)})
    return out
