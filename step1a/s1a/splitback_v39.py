"""wf_v3.9 Phase 2 (tasks 6-7): keep-apart pairs of the co-occurrence graph, and splitting A s012's merged groups back apart.
Pure functions of already-loaded data; scripts/splitback_v39.py loads and writes. No models, no LLM, no gold.

Split back: a group of A s012 that holds several clusters is split when two of its clusters are in conflict, i.e. a keep-apart
pair (cosine >= sim_thr and co-occurrence count > 0, draft_schema.build) or a role pair by the method's own names
(merges_v38.guard_pairs over the names the cluster got in the orders and the vote). Every cluster in a conflict is a seed; seeds
are placed one by one (biggest first) into the best existing column that holds no conflicting seed (best = highest bge-m3
centroid cosine to a seed of the column), else they open a new column; the other members join the column of the most similar
seed (centroid cosine). Each column gets a new group id and a distinct name (the vote name of its biggest named cluster).
"""

from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd

from . import draft_schema as DS
from . import merges_v38 as M
from . import node_filter as NF
from . import pilot_verify as PV

APART, ROLE = "keep_apart", "role"
SOURCE = "splitback"
KA_COLS = ["set", "entity", "cluster_a", "cluster_b", "cos", "count", "values_a", "values_b"]
SPLIT_COLS = ["set", "ent", "attr_id", "name", "n_clusters", "conflicts", "columns", "column_names"]
FATE_COLS = ["set", "ent", "attr_id", "column", "was_right", "reason", "n_members", "members", "groups_after", "undone",
             "wrong_after", "fixed"]


# ---- task 6

def status_from_chosen(nodes, chosen):
    """nodes + score + status of a chosen.json (signals, directions, method, theta, threshold): graph_run.select with --chosen."""
    score = NF.combine(nodes, chosen["signals"], chosen["directions"], chosen["method"])
    return NF.apply(nodes, score, chosen["theta"], chosen["threshold"])


def sim_threshold(sim_graphs, kept, q):
    """Quantile q of the within-entity centroid cosines of pairs of kept nodes (graph_run.schema: relative threshold)."""
    cos = [c for h in sim_graphs.values() for a, b, c in h.edges(data="cos") if a in kept and b in kept]
    return float(np.quantile(cos, q))


def keep_apart_rows(set_name, schema, top_values, n_top=3):
    """KA_COLS rows of draft_schema.build output: one per keep_apart pair. top_values {cluster_id: "a|b|c"}."""
    def top(c):
        return "|".join([v for v in str(top_values.get(c, "")).split("|") if v and v != "nan"][:n_top])

    return [{"set": set_name, "entity": ent, "cluster_a": a, "cluster_b": b, "cos": round(h["cos"], 4), "count": h["count"],
             "values_a": top(a), "values_b": top(b)}
            for ent, body in DS.entities(schema).items() for h in body["keep_apart"] for a, b in [h["nodes"]]]


def apart_pairs(rows, entity):
    """{frozenset({a, b})} of the keep-apart rows of one entity id."""
    return {frozenset((r["cluster_a"], r["cluster_b"])) for r in rows if r["entity"] == entity}


# ---- task 7: which pairs conflict, and how the group is divided

def conflicts(clusters, apart, texts):
    """{frozenset({a, b}): "keep_apart" / "role" / "keep_apart+role"} over the pairs of `clusters`. apart = set of keep-apart
    pairs; texts {cluster: [names the method gave it]} (role pairs: merges_v38.guard_pairs)."""
    role = {frozenset(p) for p in M.guard_pairs({c: texts.get(c, []) for c in clusters})}
    out = {}
    for a, b in combinations(sorted(clusters), 2):
        k = frozenset((a, b))
        why = [w for w, hit in ((APART, k in apart), (ROLE, k in role)) if hit]
        if why:
            out[k] = "+".join(why)
    return out


def _cos(cent, a, b):
    return float(np.dot(cent[a], cent[b])) if a in cent and b in cent else 0.0


def split_columns(clusters, conf, size, cent):
    """List of columns (sorted cluster lists), biggest first. Seeds (clusters in any conflict) are placed biggest first: into
    the existing column without a conflicting seed that holds their most similar seed (ties: the earlier column), else a new
    column; non-seeds join the column of their most similar seed. No conflict -> one column."""
    seeds = sorted({c for k in conf for c in k}, key=lambda c: (-size.get(c, 0), c))
    cols = []
    for s in seeds:
        free = [col for col in cols if not any(frozenset((s, t)) in conf for t in col)]
        if free:
            max(free, key=lambda col: max(_cos(cent, s, t) for t in col)).append(s)
        else:
            cols.append([s])
    if not cols:
        return [sorted(clusters)]
    for c in sorted(set(clusters) - set(seeds)):
        max(cols, key=lambda col: max(_cos(cent, c, t) for t in col)).append(c)
    cols = [sorted(col) for col in cols]
    return sorted(cols, key=lambda col: (-sum(size.get(c, 0) for c in col), col[0]))


def column_names(group_name, cols, own, top, size):
    """One name per column: the vote name (`own` {cluster: norm name or ""}) of its biggest named cluster, else the group's
    name. A name that an earlier column already has (normalised) gets " (<top value of the column's biggest cluster>)", and
    if that is taken too " (<cluster id>)". `top` {cluster: first top value}."""
    used, out = set(), []
    for col in cols:
        big = sorted(col, key=lambda c: (-size.get(c, 0), c))
        name = next((own[c] for c in big if own.get(c)), group_name)
        if PV.norm_name(name) in used:
            alt = f"{name} ({top.get(big[0], '')})"
            name = alt if top.get(big[0]) and PV.norm_name(alt) not in used else f"{name} ({big[0]})"
        used.add(PV.norm_name(name))
        out.append(name)
    return out


def apply_split(attrs, assign, mention_cluster, plan):
    """(new attrs, new assign, number of mentions of a split group that sit in no listed cluster). plan {attr_id: [{"clusters",
    "name", "description"}]} (one entry per new column, biggest first). A new group id = its clusters joined by "|"; status
    of the old group is kept, source = SOURCE. Mentions of a cluster go to its column; a mention from a cluster that the old
    group did not list (a reconcile part joined to the group) goes to the first column."""
    new_assign, orphans, col_of = {}, 0, {}
    for gid, cols in plan.items():
        for col in cols:
            for c in col["clusters"]:
                col_of[(gid, c)] = "|".join(sorted(col["clusters"]))
    for i, a in assign.items():
        if a not in plan:
            new_assign[i] = a
            continue
        to = col_of.get((a, mention_cluster.get(i, "")))
        if to is None:
            orphans += 1
            to = "|".join(sorted(plan[a][0]["clusters"]))
        new_assign[i] = to
    n = Counter(new_assign.values())
    rows = []
    for _, r in attrs.iterrows():
        if r["attr_id"] not in plan:
            rows.append(r.to_dict())
            continue
        for col in plan[r["attr_id"]]:
            gid = "|".join(sorted(col["clusters"]))
            rows.append({**r.to_dict(), "attr_id": gid, "name": col["name"], "description": col["description"],
                         "clusters": ";".join(sorted(col["clusters"])), "n_mentions": n[gid], "source": SOURCE})
    return pd.DataFrame(rows, columns=attrs.columns), new_assign, orphans


# ---- the fate of the merges

def merge_fate(set_name, ent, before, after, groups_after):
    """FATE_COLS rows, one per judged merge of `before` (rules_groups.merges of A s012). groups_after {cluster: group id} of the
    split variant. undone = the merge's judged members now sit in >= 2 groups; wrong_after = judged merges of `after` that still
    hold >= 2 of its members and are not right; fixed = a wrong merge with wrong_after 0."""
    rows = []
    judged = after[after["judged"].astype(bool)]
    for _, r in before[before["judged"].astype(bool)].iterrows():
        members = r["members"].split(";")
        groups = {groups_after.get(c, "?" + c) for c in members}
        desc = judged[pd.Series([len(set(m.split(";")) & set(members)) >= 2 for m in judged["members"]], index=judged.index, dtype=bool)]
        wrong_after = int((~desc["right"].astype(bool)).sum())
        rows.append({"set": set_name, "ent": ent, "attr_id": r["attr_id"], "column": r["name"], "was_right": bool(r["right"]),
                     "reason": r["reason"], "n_members": len(members), "members": r["members"], "groups_after": len(groups),
                     "undone": len(groups) > 1, "wrong_after": wrong_after, "fixed": (not r["right"]) and wrong_after == 0})
    return rows


def fate_counts(fate):
    """dict per set: wrong / right merges before, wrong undone, wrong fixed, right undone (by mistake)."""
    out = {}
    for s, g in pd.DataFrame(fate, columns=FATE_COLS).groupby("set", sort=False):
        w, r = g[~g["was_right"]], g[g["was_right"]]
        out[s] = {"wrong": len(w), "wrong_undone": int(w["undone"].sum()), "wrong_fixed": int(w["fixed"].sum()),
                  "right": len(r), "right_undone": int(r["undone"].sum())}
    return out


def decide(counts, wrong_after, guard_pass):
    """(adopt?, lines) for one set: adopt = wrong merges down (wrong_after < counts["wrong"]), <= 1 right merge undone, guard pass."""
    ok_wrong, ok_right = wrong_after < counts["wrong"], counts["right_undone"] <= 1
    return ok_wrong and ok_right and guard_pass, [
        f"wrong merges {counts['wrong']} -> {wrong_after} ({'down' if ok_wrong else 'NOT down'})",
        f"right merges undone {counts['right_undone']}/{counts['right']} ({'ok' if ok_right else 'too many'}, limit 1)",
        f"recall guard {'pass' if guard_pass else 'FAIL'}"]
