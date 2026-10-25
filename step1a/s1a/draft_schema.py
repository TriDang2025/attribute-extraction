"""Task 7: draft schema per entity from the kept nodes of the attribute graph.

Reads Export (mentions, clusters), graphs (co, sim, cross) and the nodes table
(see GRAPH_CONTRACT.md). `build` returns {entity: {...}, "relationships": {"pairs": [...]}}.
"""
import json
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

REL_KEY = "relationships"


def _graph(graphs, name):
    return graphs[name] if isinstance(graphs, dict) else getattr(graphs, name)


def _py(v):
    """numpy / NaN -> JSON-safe python value."""
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else float(v)
    return v


def _pair_count(co, a, b):
    return int(co.edges[a, b].get("count", 0)) if co.has_edge(a, b) else 0


def _identifier(kept):
    med = kept["n_values"].median()
    cand = kept[kept["n_values"] >= med]
    row = cand.sort_values(["pagerank", "cluster_id"], ascending=[False, True]).iloc[0]
    why = (f"highest pagerank ({row['pagerank']:.4g}) among {len(cand)} kept nodes with "
           f"n_values >= median {med:g}")
    return row, why


def _examples(m, n, rng):
    """n mentions: one per distinct norm_value first (random), then fill with the rest."""
    if m.empty:
        return []
    m = m.iloc[rng.permutation(len(m))]
    first = m.drop_duplicates("norm_value")
    rest = m.drop(first.index)
    pick = pd.concat([first, rest]).head(n)
    return [{"text": r.text, "context": r.context, "dialogue_id": r.dialogue_id, "turn": int(r.turn)}
            for r in pick.itertuples()]


def _sub_entities(co, ids, ident, seed):
    g = nx.Graph()
    g.add_nodes_from(ids)
    for a, b, d in co.subgraph(ids).edges(data=True):
        w = max(float(d.get("npmi", 0.0) or 0.0), 0.0)
        if w > 0:
            g.add_edge(a, b, w=w)
    comms = nx.community.louvain_communities(g, weight="w", seed=seed)
    return sorted(sorted(c) for c in comms if len(c) >= 2 and ident not in c)


def _relationships(cross, kept_ent, rel_npmi, rel_min):
    agg = {}
    for a, b, d in cross.edges(data=True):
        if a not in kept_ent or b not in kept_ent or kept_ent[a] == kept_ent[b]:
            continue
        npmi, cnt = d.get("npmi"), int(d.get("count", 0))
        if npmi is None or npmi < rel_npmi or cnt < rel_min:
            continue
        key = tuple(sorted((kept_ent[a], kept_ent[b])))
        r = agg.setdefault(key, {"entities": list(key), "n_node_pairs": 0, "max_npmi": -np.inf})
        r["n_node_pairs"] += 1
        if npmi > r["max_npmi"]:
            r["max_npmi"] = float(npmi)
            r["example"] = {"nodes": [a, b], "npmi": float(npmi), "count": cnt}
    return sorted(agg.values(), key=lambda r: (-r["n_node_pairs"], r["entities"]))


def build(export, graphs, nodes, sim_thr=0.75, card_thr=1.2, rel_npmi=0.2, rel_min=3,
          n_examples=8, seed=0):
    co, sim, cross = _graph(graphs, "co"), _graph(graphs, "sim"), _graph(graphs, "cross")
    kept_all = nodes[nodes["status"] == "kept"]
    num_cols = [c for c in kept_all.columns if pd.api.types.is_numeric_dtype(kept_all[c])]
    top = export.clusters.set_index("cluster_id")["top_values"].fillna("")
    mentions = export.mentions
    rng = np.random.default_rng(seed)
    schema = {}
    for ent, kept in kept_all.groupby("entity", sort=True):
        ident, why = _identifier(kept)
        ids = list(kept["cluster_id"])
        co_g, sim_g = co.get(ent, nx.Graph()), sim.get(ent, nx.Graph())
        by_id = kept.set_index("cluster_id")
        ment_by = {cid: g for cid, g in mentions[mentions["cluster_id"].isin(ids)].groupby("cluster_id")}
        empty = mentions.iloc[0:0]

        def node_info(cid):
            row = by_id.loc[cid]
            return {
                "cluster_id": cid,
                "scores": {c: _py(row[c]) for c in num_cols},
                "top_values": [v for v in top.get(cid, "").split("|") if v],
                "examples": _examples(ment_by.get(cid, empty), n_examples, rng),
            }

        identifier = node_info(ident["cluster_id"])
        identifier["why"] = why
        attrs = {}
        for cid in ids:
            if cid == ident["cluster_id"]:
                continue
            info = node_info(cid)
            info["form"] = "column" if by_id.loc[cid, "cardinality"] <= card_thr else "table"
            attrs["#" + cid] = info
        merge, apart = [], []
        for a, b in combinations(sorted(ids), 2):
            if not sim_g.has_edge(a, b):
                continue
            cos = float(sim_g.edges[a, b]["cos"])
            if cos < sim_thr:
                continue
            cnt = _pair_count(co_g, a, b)
            (merge if cnt == 0 else apart).append({"nodes": [a, b], "cos": cos, "count": cnt})
        schema[ent] = {
            "identifier": identifier,
            "attributes": attrs,
            "merge_hints": merge,
            "keep_apart": apart,
            "sub_entities": [{"nodes": c} for c in _sub_entities(co_g, ids, ident["cluster_id"], seed)],
        }
    kept_ent = dict(zip(kept_all["cluster_id"], kept_all["entity"]))
    schema[REL_KEY] = {"pairs": _relationships(cross, kept_ent, rel_npmi, rel_min)}
    return schema


def entities(schema):
    return {k: v for k, v in schema.items() if k != REL_KEY}


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write(schema, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for ent, body in entities(schema).items():
        _dump(out / f"{ent}.json", body)
    _dump(out / f"{REL_KEY}.json", schema[REL_KEY])


def to_markdown(schema):
    lines = []
    for ent, s in entities(schema).items():
        ident = s["identifier"]
        lines += [f"## {ent}", f"- identifier: {ident['cluster_id']} ({', '.join(ident['top_values'][:3])})"]
        for name, a in s["attributes"].items():
            lines.append(f"- {name} [{a['form']}]: {', '.join(a['top_values'][:3])}")
        for h in s["merge_hints"]:
            lines.append(f"- merge: {h['nodes'][0]} + {h['nodes'][1]} (cos {h['cos']:.2f})")
        for h in s["keep_apart"]:
            lines.append(f"- keep apart: {h['nodes'][0]} / {h['nodes'][1]} (cos {h['cos']:.2f}, co {h['count']})")
        for c in s["sub_entities"]:
            lines.append(f"- sub-entity: {', '.join(c['nodes'])}")
        lines.append("")
    pairs = schema[REL_KEY]["pairs"]
    if pairs:
        lines += ["## relationships", "| entities | node pairs | max npmi |", "|---|---|---|"]
        lines += [f"| {' - '.join(p['entities'])} | {p['n_node_pairs']} | {p['max_npmi']:.2f} |" for p in pairs]
    return "\n".join(lines) + "\n"
