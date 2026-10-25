"""Task 3: per-node signals (one row per cluster) from an Export and its Graphs."""
import math

import networkx as nx
import numpy as np
import pandas as pd

MAX_COHESION = 200
TOP_LEFT = 3
TOP_NEIGHBOURS = 3


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials."""
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def _cohesion(vecs: np.ndarray, rng: np.random.Generator) -> float:
    n = len(vecs)
    if n < 2:
        return 1.0
    if n > MAX_COHESION:
        vecs = vecs[rng.choice(n, MAX_COHESION, replace=False)]
        n = MAX_COHESION
    s = _unit(vecs).sum(0)
    return float((s @ s - n) / (n * (n - 1)))


def _graph_signals(g: nx.Graph, clusters: list[str]) -> dict[str, tuple[int, float, float]]:
    """cluster -> (degree, wdegree_npmi, pagerank) on graph g; absent nodes count as isolated."""
    h = nx.Graph()
    h.add_nodes_from(clusters)
    wdeg = dict.fromkeys(clusters, 0.0)
    deg = dict.fromkeys(clusters, 0)
    for a, b, d in g.edges(data=True):
        w = max(d.get("npmi", 0.0), 0.0)
        h.add_edge(a, b, w=w)
        for u in (a, b):
            if u in deg:
                deg[u] += 1
                wdeg[u] += w
    pr = nx.pagerank(h, weight="w") if h.number_of_nodes() else {}
    return {c: (deg[c], wdeg[c], pr.get(c, float("nan"))) for c in clusters}


def _proximity(node, g, turns, top=TOP_NEIGHBOURS):
    """Mean over top-NPMI neighbours of the mean min |turn distance| over shared instances."""
    if node not in g:
        return float("nan")
    nbrs = sorted(g[node].items(), key=lambda kv: -kv[1].get("npmi", 0.0))[:top]
    mine = turns.get(node, {})
    per_nb = []
    for nb, _ in nbrs:
        other = turns.get(nb, {})
        dists = [np.abs(mine[i][:, None] - other[i][None, :]).min() for i in mine.keys() & other.keys()]
        if dists:
            per_nb.append(float(np.mean(dists)))
    return float(np.mean(per_nb)) if per_nb else float("nan")


def node_table(export, graphs, stability: pd.Series | None = None) -> pd.DataFrame:
    from s1a.graph import centroids

    m = export.mentions
    m = m[m["cluster_id"] != ""].copy()
    pos = pd.Series(np.arange(len(export.ids)), index=export.ids)
    m["_row"] = pos.loc[m["mention_id"]].to_numpy()
    n_inst = export.instances.groupby("entity").size()
    cents = centroids(export)
    rng = np.random.default_rng(0)

    # per (cluster, instance) turns, used by proximity
    turns = {}
    for (c, i), t in m.groupby(["cluster_id", "instance_id"])["turn"]:
        turns.setdefault(c, {})[i] = np.sort(t.to_numpy())

    # per-cluster scalars from single groupbys
    grp = m.groupby("cluster_id")
    size = pd.DataFrame({
        "n_mentions": grp.size(),
        "n_values": grp["norm_value"].nunique(),
        "n_docs": grp["dialogue_id"].nunique(),
        "k": grp["instance_id"].nunique(),
        "confidence": grp["gliner_score"].mean(),
    })
    entity = grp["entity"].first()
    vi = m.groupby(["cluster_id", "norm_value"])["instance_id"].nunique()
    repetition = (vi >= 2).groupby(level=0).mean()
    cardinality = m.groupby(["cluster_id", "instance_id"])["norm_value"].nunique().groupby(level=0).mean()

    rows = []
    gsig = {}
    for ent, cl in entity.groupby(entity):
        ids_ = list(cl.index)
        gsig.update(_graph_signals(graphs.co.get(ent, nx.Graph()), ids_))
    for c, sub in grp:
        ent = entity[c]
        k, n = int(size.at[c, "k"]), int(n_inst.get(ent, 0))
        lo, hi = wilson(k, n)
        deg, wdeg, pr = gsig[c]
        vecs = export.x[sub["_row"].to_numpy()]
        others = [v for o, v in cents.items() if o != c and entity.get(o) == ent]
        sep = float((_unit(np.array(others)) @ _unit(cents[c])).max()) if others else float("nan")
        top = sub["left_word"].value_counts().head(TOP_LEFT).index
        rows.append({
            "cluster_id": c, "entity": ent,
            "n_mentions": int(size.at[c, "n_mentions"]),
            "n_values": int(size.at[c, "n_values"]), "n_docs": int(size.at[c, "n_docs"]),
            "k": k, "n": n, "support": k / n if n else float("nan"), "wilson_lo": lo, "wilson_hi": hi,
            "degree": deg, "wdegree_npmi": wdeg, "pagerank": pr,
            "cohesion": _cohesion(vecs, rng), "separation": sep,
            "stability": float(stability.get(c, np.nan)) if stability is not None else float("nan"),
            "repetition": float(repetition[c]),
            "cue_consistency": float(sub["left_word"].isin(top).mean()),
            "cardinality": float(cardinality[c]),
            "proximity": _proximity(c, graphs.co.get(ent, nx.Graph()), turns),
            "confidence": float(size.at[c, "confidence"]),
        })
    df = pd.DataFrame(rows).set_index("cluster_id")
    return df
