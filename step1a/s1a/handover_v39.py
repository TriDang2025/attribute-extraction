"""wf_v3.9 final setting and handover (tasks 9 and 11): pure functions, no I/O, no models. Loading and writing are in
scripts/final_v39.py.

Final setting = A s012 + split pass + reconcile joins both candidate orders agree on + duplicate-check joins both reconcile
orders unite (same set of A s012 groups) applied on the agreed columns (role-pair block still applies) + the v3.8 checker as a
flag only.
- group_sets / both_orders / joins_on_columns / merge_joined_columns: the both-orders rule for duplicate-check joins.
- parse_group / value_type_counts / keep_apart_flags: facts of a final column.
- evidence_card: the card of a final column from the evidence of the columns it was made of (pooled), and its verdict.
- column_record / dropped_record / check_handover: the handover file (step1a/handover/HANDOVER_FORMAT.md).
"""

from collections import Counter

from . import batch_v39 as B9
from . import score_v38 as S
from .value_types import value_type_v35


# ---- the both-orders rule

def group_sets(cols, joins):
    """[frozenset of attr ids]: for every join ({"columns": [cids]}) the groups of the columns it unites."""
    by_id = {c["cid"]: c for c in cols}
    return [frozenset(g for c in j["columns"] for g in by_id[c]["groups"]) for j in joins]


def both_orders(sets0, sets1):
    """Group sets that both orders unite (a join counts only when both orders unite exactly the same groups), sorted."""
    return sorted(set(sets0) & set(sets1), key=lambda s: sorted(s))


def joins_on_columns(cols, sets):
    """[{"columns": [cids], "reason"}] on the columns `cols`: for each group set the columns that hold its groups; a set inside one column
    is already united and gives no join."""
    owner = {g: c["cid"] for c in cols for g in c["groups"]}
    out = []
    for s in sets:
        ids = sorted({owner[g] for g in s if g in owner})
        if len(ids) >= 2:
            out.append({"columns": ids, "reason": "same groups united by both reconcile orders' duplicate checks"})
    return out


def merge_joined_columns(cols, joins):
    """Columns after the joins (union_joins; old_cids = the cids of `cols` united; the biggest member names the column, a
    description is taken from the biggest member that has one). Columns are rebuilt by batch_v39.assemble_columns (sorted by
    name, numbered 1..n)."""
    by_id = {c["cid"]: c for c in cols}
    pools = {c["cid"]: {k: B9._items(p) for k, p in c["pools"]} for c in cols}
    groups = {c["cid"]: list(c["groups"]) for c in cols}
    lost, shown = set(), [dict(c) for c in cols]
    comps = S.union_joins(list(joins))
    for comp in comps:
        base = S.join_base(by_id, comp)
        for c in comp:
            if c != base:
                pools[base].update(pools[c])
                groups[base] += groups[c]
                pools[c], groups[c] = {}, []
                lost.add(c)
        desc = next((by_id[c]["description"] for c in sorted(comp, key=lambda c: (-by_id[c]["n_mentions"], c))
                     if by_id[c]["description"]), "")
        next(x for x in shown if x["cid"] == base)["description"] = desc
    out = B9.assemble_columns(shown, pools, groups, lost)
    united = {c["cid"]: [] for c in out}
    name_of = {c["name"]: c["cid"] for c in out}
    for comp in comps:
        united[name_of[by_id[S.join_base(by_id, comp)]["name"]]] = sorted(comp)
    for c in out:
        c["old_cids"] = united[c["cid"]] or c["old_cids"]
    return out


# ---- facts of a column

def parse_group(attr_id):
    """([cluster ids], part id or None) of a group id: "E1#3|E1#5" = two clusters, "E1#3/0" = a split part of E1#3."""
    if "/" in attr_id:
        return [attr_id.split("/")[0]], attr_id
    return attr_id.split("|"), None


def value_type_counts(texts):
    """Counter of value_types.value_type_v35 over the mention texts."""
    return Counter(value_type_v35(t) for t in texts)


def keep_apart_flags(clusters, pairs):
    """[{"a", "b", "cos"}]: keep-apart pairs (dicts with cluster_a, cluster_b, cos) whose two clusters are both in `clusters`."""
    cs = set(clusters)
    return [{"a": p["cluster_a"], "b": p["cluster_b"], "cos": float(p["cos"])} for p in pairs
            if p["cluster_a"] in cs and p["cluster_b"] in cs and p["cluster_a"] != p["cluster_b"]]


# ---- evidence card

def evidence_card(members, names, sup, src, neighbours):
    """dict card + verdict of one final column made of the pre-join columns `members` (ids of the v3.8 batch columns, the
    biggest first). names {cid: name}; sup {cid: (yes, n)} the example answers; src {cid: {source cid: (yes, n)}} the neighbour
    answers; neighbours: list of lists of pre-join cids (the columns it was compared with). Support = pooled over the members that
    have an example job; neighbour fit as batch score_v38.neighbour_evidence (n = 0: no job asked about that neighbour).
    Returns {"support": {yes, n, share} | None, "neighbour_fit": {...} | None, "neighbours": [...], "mixed_roles", "verdict",
    "null_reason"}; support None when no member has an example job (verdict unsure, rule v0)."""
    if not members:   # a column with no mention was never asked about
        return {"support": None, "neighbour_fit": None, "neighbours": [], "mixed_roles": False, "verdict": "unsure",
                "null_reason": "the column has no mention"}
    entries = S.neighbour_evidence(members, members[0], neighbours, src)
    for e in entries:
        e["names"] = [names[c] for c in e["cids"]]
    sy, sn = S.pooled_support(members, sup)
    fy, fn = sum(e["yes"] for e in entries), sum(e["n"] for e in entries)
    s_share, f_share = S.share(sy, sn), S.share(fy, fn)
    mixed = S.mixed_roles([names[m] for m in members], entries)
    reasons = []
    if not sn:
        reasons.append("no example answers for any member column")
    if not fn:
        reasons.append("no neighbour answers for the compared columns")
    return {"support": {"yes": sy, "n": sn, "share": round(s_share, 3)} if sn else None,
            "neighbour_fit": {"yes": fy, "n": fn, "share": round(f_share, 3)} if fn else None,
            "neighbours": [{"columns": e["names"], "yes": e["yes"], "n": e["n"]} for e in entries], "mixed_roles": bool(mixed),
            "verdict": S.verdict(s_share, f_share, mixed), "null_reason": "; ".join(reasons)}


# ---- the handover file

def column_record(cid, name, description, role, value_type, members, mention_ids, n_dialogues, top_values, placement, card,
                  pooled, from_columns, keep_apart, origin):
    """The dict of one final column (HANDOVER_FORMAT.md)."""
    verdict = card["verdict"]
    return {"id": cid, "name": name, "description": description, "role": role, "value_type": value_type, "n_mentions": len(mention_ids),
            "n_dialogues": n_dialogues, "top_values": top_values, "placement": placement, "members": members,
            "mention_ids": sorted(mention_ids), "origin": origin,
            "evidence": {**{k: card[k] for k in ("support", "neighbour_fit", "neighbours", "mixed_roles", "null_reason")},
                         "pooled": pooled, "from_columns": from_columns},
            "verdict": verdict,
            "flags": {"noise": verdict == "noise", "too_general": verdict == "too general", "mixed_roles": verdict == "mixed roles" or card["mixed_roles"],
                      "keep_apart": keep_apart}}


def dropped_record(cluster_id, action, name, evidence, placement, mention_ids):
    """The dict of one dropped cluster: marked not_attribute / unsure / attribute_cue by A s012. wrong_entity: its placement names
    another entity (information only, from the model's own placement, not from the GT)."""
    wrong = placement.startswith("other entity") or placement.startswith("relationship")
    reason = {"not_attribute": "marked not_attribute (noise or not a database value)", "unsure": "marked unsure",
              "attribute_cue": "marked attribute_cue (a question about an attribute)"}.get(action, f"action {action}")
    return {"cluster": cluster_id, "action": action, "reason": reason, "wrong_entity_placement": wrong, "name": name,
            "evidence": evidence, "placement": placement, "n_mentions": len(mention_ids), "mention_ids": sorted(mention_ids)}


def check_handover(doc):
    """[problem strings] of one handover document {clusters, columns, dropped}: every mention id once; every cluster in a column
    (as a member), or dropped, never both; a cluster in two columns only as split parts."""
    problems, seen = [], Counter()
    in_cols, parts_only = {}, {}
    for col in doc["columns"]:
        seen.update(col["mention_ids"])
        for m in col["members"]:
            in_cols.setdefault(m["cluster"], []).append(col["id"])
            parts_only[m["cluster"]] = parts_only.get(m["cluster"], True) and m["part"] is not None
    dropped = {d["cluster"] for d in doc["dropped"]}
    for d in doc["dropped"]:
        seen.update(d["mention_ids"])
    problems += [f"mention {m} appears {n} times" for m, n in seen.items() if n > 1]
    for c in doc["clusters"]:
        n_col, is_drop = len(set(in_cols.get(c, []))), c in dropped
        if n_col and is_drop:
            problems.append(f"cluster {c} is in a column and dropped")
        elif not n_col and not is_drop:
            problems.append(f"cluster {c} is in no column and not dropped")
        elif n_col > 1 and not parts_only[c]:
            problems.append(f"cluster {c} is in {n_col} columns without being split")
    extra = (set(in_cols) | dropped) - set(doc["clusters"])
    problems += [f"cluster {c} is not a cluster of the entity" for c in sorted(extra)]
    return problems
