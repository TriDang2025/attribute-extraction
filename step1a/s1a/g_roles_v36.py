"""wf_v3.6 variant g: how well do `role_examples` match the gold L2 roles, and how many name merges would the role guard
block? Pure functions on parsed responses and decision tables; no data loading (scripts/score_v36.py loads them).
"""

import json
from collections import Counter

from . import pilot_verify as PV
from . import role_guard as RG


def role_accuracy(groups, pair):
    """(k, n) of one two-role cluster. `groups` = [(attribute, [gold role of each example id])] from its role_examples;
    `pair` = the two gold roles. n = examples whose gold role is in the pair. Each group takes the majority role of its
    examples (a tie takes none); the largest group claims a role first and a later group with a role already claimed
    gets none. k = examples whose gold role is their group's role."""
    pair = set(pair)
    counts = [Counter(r for r in roles if r in pair) for _, roles in groups]
    n = sum(sum(c.values()) for c in counts)
    claimed, k = set(), 0
    for c in sorted(counts, key=lambda c: -sum(c.values())):
        top = c.most_common(2)
        if not top or (len(top) == 2 and top[0][1] == top[1][1]) or top[0][0] in claimed:
            continue
        claimed.add(top[0][0])
        k += top[0][1]
    return k, n


def separates(groups, pair):
    """True when the groups' majority roles cover both roles of the pair (the model told the two roles apart)."""
    maj = set()
    for _, roles in groups:
        top = Counter(r for r in roles if r in set(pair)).most_common(2)
        if top and not (len(top) == 2 and top[0][1] == top[1][1]):
            maj.add(top[0][0])
    return maj == set(pair)


def cluster_rows(items, two):
    """One row per cluster of the responses. `items` = [(cluster object of a v3 response, {example id: gold role})];
    `two` = {cluster_id: pair of gold roles} (roles_v35.two_role_clusters). Columns: cluster_id, two_role, mixed,
    has_role_examples, groups, k, n, separated (the last three 0 / False outside two-role clusters)."""
    rows = []
    for c, ex_role in items:
        cid = c["cluster_id"]
        groups = [(str(g.get("attribute", "")), [ex_role.get(x, "") for x in g.get("examples") or []])
                  for g in c.get("role_examples") or [] if isinstance(g, dict)]
        two_role = cid in two
        k, n = role_accuracy(groups, two[cid]) if two_role and groups else (0, 0)
        rows.append({"cluster_id": cid, "two_role": two_role, "mixed": bool(c.get("mixed")),
                     "has_role_examples": bool(groups), "groups": len(groups), "k": k, "n": n,
                     "separated": bool(two_role and groups and separates(groups, two[cid]))})
    return rows


# ---- role guard on the name merge

def cluster_texts(obj):
    """{cluster_id: "<attribute name> <role>"} of a v2 / v3 response: the role of the attribute list entry that the cluster
    names (role_guard.filter_reconcile_answers reads names and roles this way)."""
    role = {PV.norm_name(a.get("name")): str(a.get("role") or "") for a in (obj or {}).get("attributes") or []
            if isinstance(a, dict)}
    return {c["cluster_id"]: f"{c.get('attribute', '')} {role.get(PV.norm_name(c.get('attribute')), '')}"
            for c in (obj or {}).get("clusters") or [] if isinstance(c, dict) and "cluster_id" in c}


def _pairs(dec):
    """{frozenset({a, b})} of cluster pairs the decision table puts in one attribute (merge_with)."""
    return {frozenset((r["cluster_id"], t)) for _, r in dec.iterrows() if r["action"] == "merge"
            for t in json.loads(r["merge_with"] or "[]")}


def guard_counts(dec, merged, texts):
    """(examined, blocked pairs): the cluster pairs that `merged` (the name merge of `dec`) newly puts in one attribute,
    and those among them that role_guard.forbidden_merge rejects (opposite sides of departure / destination, leave at /
    arrive by, location / address). `texts` = cluster_texts of the responses (all groups). Pairs without a text for
    both clusters are examined but never blocked."""
    new = sorted(tuple(sorted(p)) for p in _pairs(merged) - _pairs(dec))
    blocked = [p for p in new if p[0] in texts and p[1] in texts and RG.forbidden_merge(texts[p[0]], texts[p[1]])]
    return len(new), blocked


def own_blocked(dec, texts):
    """Pairs the responses' own merge groups (merge_with of `dec`) put together that the role guard would reject."""
    return [tuple(sorted(p)) for p in sorted(_pairs(dec), key=sorted)
            if all(c in texts for c in p) and RG.forbidden_merge(*(texts[c] for c in sorted(p)))]
