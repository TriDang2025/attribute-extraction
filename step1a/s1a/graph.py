"""Attribute graphs over clusters: co-occurrence (per entity), centroid similarity (per entity), cross-entity."""
import pickle
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

import networkx as nx
import numpy as np
from matplotlib.figure import Figure


@dataclass
class Graphs:
    co: dict      # entity -> nx.Graph, edges: count, jaccard, npmi
    sim: dict     # entity -> nx.Graph, edges: cos
    cross: nx.Graph  # edges between clusters of different entities: count, npmi


def _npmi(n_ab, n_a, n_b, n) -> float:
    """NPMI from counts; 1.0 when the pair is always together (p(ab) = 1, formula is 0/0)."""
    p_ab = n_ab / n
    if p_ab >= 1.0:
        return 1.0
    return float(np.log(p_ab / ((n_a / n) * (n_b / n))) / -np.log(p_ab))


def centroids(export) -> dict:
    """{cluster_id: mean of the cluster's vectors from export.x, L2-renormalised}."""
    row = {int(i): k for k, i in enumerate(export.ids)}
    m = export.mentions[export.mentions["cluster_id"].fillna("") != ""]
    out = {}
    for cid, g in m.groupby("cluster_id"):
        c = export.x[[row[int(i)] for i in g["mention_id"]]].mean(axis=0)
        nrm = np.linalg.norm(c)
        out[cid] = c / nrm if nrm > 0 else c
    return out


def _cooccurrence(groups: dict, n: int) -> nx.Graph:
    """Edges between clusters sharing a group (instance or dialogue); groups = {group id: set of clusters}."""
    single, pair = Counter(), Counter()
    for cl in groups.values():
        single.update(cl)
        pair.update(combinations(sorted(cl), 2))
    g = nx.Graph()
    for (a, b), c in pair.items():
        g.add_edge(a, b, count=c, jaccard=c / (single[a] + single[b] - c), npmi=_npmi(c, single[a], single[b], n))
    return g


def _groups(pairs, key: str, ids=None) -> dict:
    """{key value: set of clusters} from a deduplicated (key, cluster_id) frame."""
    if ids is not None:
        pairs = pairs[pairs["cluster_id"].isin(ids)]
    out = {}
    for k, c in zip(pairs[key], pairs["cluster_id"]):
        out.setdefault(k, set()).add(c)
    return out


def build_graphs(export) -> Graphs:
    cl = export.clusters[export.clusters["cluster_id"].fillna("") != ""]
    ent_of = dict(zip(cl["cluster_id"], cl["entity"]))
    nodes = {r.cluster_id: dict(entity=r.entity, n_mentions=int(r.n_mentions),
                                top_values=[v for v in str(r.top_values).split("|") if v and v != "nan"])
             for r in cl.itertuples()}
    m = export.mentions[export.mentions["cluster_id"].isin(ent_of)]
    inst_pairs = m[["instance_id", "cluster_id"]].drop_duplicates()
    dlg_pairs = m[["dialogue_id", "cluster_id"]].drop_duplicates()
    cent = centroids(export)

    co, sim = {}, {}
    for ent in sorted(set(ent_of.values())):
        ids = [c for c in nodes if nodes[c]["entity"] == ent]
        n = int((export.instances["entity"] == ent).sum())
        g = _cooccurrence(_groups(inst_pairs, "instance_id", ids), n) if n else nx.Graph()
        s = nx.Graph()
        for c in ids:
            g.add_node(c, **nodes[c])
            s.add_node(c, **nodes[c])
        if len(ids) > 1:
            C = np.stack([cent[c] for c in ids])
            cos = C @ C.T
            for i, j in combinations(range(len(ids)), 2):
                s.add_edge(ids[i], ids[j], cos=float(cos[i, j]))
        co[ent], sim[ent] = g, s

    n_dlg = export.instances["dialogue_id"].nunique() or m["dialogue_id"].nunique()
    full = _cooccurrence(_groups(dlg_pairs, "dialogue_id"), n_dlg) if n_dlg else nx.Graph()
    cross = nx.Graph()
    for c, attrs in nodes.items():
        cross.add_node(c, **attrs)
    for a, b, d in full.edges(data=True):
        if ent_of[a] != ent_of[b]:
            cross.add_edge(a, b, count=d["count"], npmi=d["npmi"])
    return Graphs(co=co, sim=sim, cross=cross)


def save(g: Graphs, path) -> None:
    with open(path, "wb") as f:
        pickle.dump(g, f)


def load(path) -> Graphs:
    with open(path, "rb") as f:
        return pickle.load(f)


def draw_entity(g: Graphs, entity: str, path, top=None) -> None:
    """PNG of the co-occurrence graph of `entity`: node size = n_mentions, edge width = NPMI,
    label = cluster_id + top value. `top` keeps only the `top` clusters by n_mentions."""
    co = g.co[entity]
    keep = sorted(co.nodes, key=lambda c: -co.nodes[c]["n_mentions"])[:top]
    h = co.subgraph(keep)
    fig = Figure(figsize=(12, 9))
    ax = fig.add_subplot()
    pos = nx.spring_layout(h, seed=0, weight="npmi")
    sizes = [30 + 8 * h.nodes[c]["n_mentions"] for c in h]
    widths = [0.3 + 3 * max(d["npmi"], 0) for _, _, d in h.edges(data=True)]
    nx.draw_networkx_edges(h, pos, ax=ax, width=widths, alpha=0.5)
    nx.draw_networkx_nodes(h, pos, ax=ax, node_size=sizes, node_color="tab:blue", alpha=0.8)
    labels = {c: f"{c}\n{(h.nodes[c]['top_values'] or [''])[0]}" for c in h}
    nx.draw_networkx_labels(h, pos, labels=labels, ax=ax, font_size=6)
    ax.set_title(f"{entity}: cluster co-occurrence")
    ax.axis("off")
    fig.savefig(path, dpi=150, bbox_inches="tight")
