"""Loop-1 recall analysis (LOOP1_CONTRACT T2): how many gold classes does a clustering recover?

Per gold class: strict = some cluster has purity >= 0.6; recoverable = strict, or >= 2 verbatim mentions sit
inside clusters and some purity >= 0.25; present = >= 1 verbatim mention sits inside a cluster.
Purity follows labels.gold_labels: members = all clustered mentions, a multi-class member counts for each class."""

import numpy as np
import pandas as pd

from .coverage import _kept, _value_hits
from .labels import _classes

PURITY_COLS = ["cluster_id", "entity", "gold_attr", "n_class", "size", "purity"]
MEASURES = ("K", "strict", "recoverable", "present")


def _counts(mentions):
    """Per-dialogue member counts of the clustered mentions: (class counts, sizes), both by (dialogue, cluster),
    and the entity of each cluster."""
    m = _kept(mentions)
    size = m.groupby(["dialogue_id", "cluster_id"]).size().rename("size").reset_index()
    cls = pd.DataFrame([(d, c, a) for d, c, v in zip(m["dialogue_id"], m["cluster_id"], m["gold_attr"])
                        for a in set(_classes(v))], columns=["dialogue_id", "cluster_id", "gold_attr"])
    cls = cls.groupby(["dialogue_id", "cluster_id", "gold_attr"]).size().rename("n").reset_index()
    return cls, size, m.groupby("cluster_id")["entity"].first()


def _purity(cls, size, entity) -> pd.DataFrame:
    """purity_table from count frames (columns n / size may be weighted)."""
    n = cls.groupby(["cluster_id", "gold_attr"])["n"].sum().rename("n_class").reset_index()
    s = size.groupby("cluster_id")["size"].sum().reset_index()
    t = n.merge(s[s["size"] > 0], on="cluster_id")
    t["entity"] = t["cluster_id"].map(entity)
    t["purity"] = t["n_class"] / t["size"]
    return t[PURITY_COLS].sort_values(["cluster_id", "gold_attr"]).reset_index(drop=True)


def purity_table(mentions) -> pd.DataFrame:
    """One row per (cluster, gold class present in it): n_class members of the class, size = all members."""
    return _purity(*_counts(mentions))


def _hits(mentions, gold_values) -> pd.DataFrame:
    """Verbatim gold rows with `hit` (overlaps a clustered span), one row per class of a multi-class value."""
    hits = _value_hits(mentions, gold_values)
    g = gold_values.loc[hits.index, ["dialogue_id", "gold_attr"]].assign(hit=hits)
    return g.assign(gold_attr=g["gold_attr"].map(_classes)).explode("gold_attr")


def inside_counts(mentions, gold_values) -> pd.Series:
    """Verbatim gold mentions of each class overlapped by a clustered span (gold_attr -> n)."""
    return _hits(mentions, gold_values).groupby("gold_attr")["hit"].sum().astype(int)


def _table(pur, inside, attrs, strict, recov, min_inside) -> pd.DataFrame:
    rows = []
    for a in attrs:
        sub = pur[pur["gold_attr"] == a].sort_values(["purity", "n_class", "cluster_id"],
                                                     ascending=[False, False, True])
        best, bp = (sub["cluster_id"].iloc[0], float(sub["purity"].iloc[0])) if len(sub) else ("", 0.0)
        n = int(inside.get(a, 0))
        s = bp >= strict
        r = s or (n >= min_inside and bp >= recov)
        rows.append(dict(gold_attr=a, strict=s, recoverable=r, present=n >= 1 or r, n_inside=n,
                         best_cluster=best, best_purity=bp))
    return pd.DataFrame(rows, columns=["gold_attr", "strict", "recoverable", "present", "n_inside",
                                       "best_cluster", "best_purity"])


def recall_table(mentions, gold_values, attrs, strict=0.6, recov=0.25, min_inside=2) -> pd.DataFrame:
    """One row per gold class; strict <= recoverable <= present (present is OR-ed with recoverable)."""
    return _table(purity_table(mentions), inside_counts(mentions, gold_values), attrs, strict, recov, min_inside)


def summary(mentions, table) -> dict:
    """K = clusters with a mention; strict / recoverable / present = number of classes."""
    return dict(K=int(_kept(mentions)["cluster_id"].nunique()),
                **{k: int(table[k].sum()) for k in MEASURES[1:]})


def bootstrap(mentions, gold_values, attrs, n=1000, seed=0, strict=0.6, recov=0.25, min_inside=2) -> dict:
    """95% range (2.5 / 97.5 percentiles) of strict, recoverable, present over n resamples of dialogues
    (with replacement). Clusters are fixed; each resample re-weights the per-dialogue counts. No range for K:
    a resample drops the clusters of unsampled dialogues, so its K is biased low."""
    cls, size, entity = _counts(mentions)
    ins = _hits(mentions, gold_values).groupby(["dialogue_id", "gold_attr"])["hit"].sum()
    dids = np.array(sorted(set(gold_values["dialogue_id"]) | set(mentions["dialogue_id"])))
    pos = {d: i for i, d in enumerate(dids)}
    cw, sw = cls["dialogue_id"].map(pos).to_numpy(), size["dialogue_id"].map(pos).to_numpy()
    iw = ins.index.get_level_values(0).map(pos).to_numpy()
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n):
        w = np.bincount(rng.integers(0, len(dids), len(dids)), minlength=len(dids))
        pur = _purity(cls.assign(n=cls["n"] * w[cw]), size.assign(size=size["size"] * w[sw]), entity)
        inside = pd.Series(ins.to_numpy() * w[iw], index=ins.index.get_level_values(1)).groupby(level=0).sum()
        t = _table(pur, inside, attrs, strict, recov, min_inside)
        draws.append([int(t[c].sum()) for c in MEASURES[1:]])
    lo, hi = np.percentile(np.array(draws), [2.5, 97.5], axis=0)
    return {k: (float(a), float(b)) for k, a, b in zip(MEASURES[1:], lo, hi)}
