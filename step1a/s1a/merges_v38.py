"""wf_v3.8 Phase 1, W2 (tasks 5 and 6): why A makes wrong merges, and what A did with the parts that the J split made.
Pure functions of already-loaded data (v34_data.EntityData at GT level 2, rules v1.1); scripts/merges_v38.py loads and writes.
No models, no LLM.

Wrong merge = a row of `rules_groups.merges` that is judged and not right (members disagree on the top attribute or on the
role slot, or the noise share is >= 20%). Step: "A prompt" = the attribute is made by A's own answer (clusters given the same
attribute name inside one prompt; the plain A variants have no name merge), "name merge" = a group that only the scorer's
+namemerge copy creates. Source: which orders (and the vote) put all judged members into one group. Role guard: s1a/role_guard
on the method's own names only (A gives no role field, so the text is the attribute name); never the gold.
"""

from collections import Counter

import pandas as pd

from . import pilot_score as PS
from . import pilot_verify as PV
from . import role_guard as RGD
from .labels import _classes

WRONG_COLS = ["set", "version", "ent", "variant", "attr_id", "column", "step", "reason", "n_members", "members",
              "member_attrs", "member_roles", "member_n", "member_noise", "odd_members", "noise_share", "source",
              "orders_full", "guard_name", "guard_orders", "guard_pairs"]
PART_NAMES = ("start", "end", "unknown")
PART_COLS = ["set", "ent", "split", "part", "cluster", "n_part", "n_cluster", "gold_top", "gold_role", "gold_counts",
             "name_s0", "name_s1", "name_s2", "name_vote", "action_vote", "group_vote", "joined_vote", "joined_orders",
             "same_name_vote", "joined_back", "gold_side", "name_side_vote", "name_ok_vote", "name_ok_orders"]


def cluster_groups(attrs):
    """{cluster_id: attr_id} of an attrs table (v34_data.VariantOut.attrs: `clusters` joined with ";"); split parts
    (source "split", attr_id "<cluster>/<k>") are left out, so a split cluster has no group."""
    keep = attrs[attrs["source"] != "split"] if "source" in attrs.columns else attrs
    return {c: a for a, cl in zip(keep["attr_id"], keep["clusters"]) for c in str(cl).split(";") if c}


def decision_names(dec):
    """{cluster_id: (norm name, action)} of a decision table; a marked / unnamed row has name ""."""
    return {r["cluster_id"]: (PV.norm_name(r["name"]), r["action"]) for _, r in dec.iterrows()}


def merge_source(members, maps, orders):
    """(orders that hold all `members` in one group, text). maps {label: {cluster_id: attr_id}}. Text: "majority of orders"
    (>= 2 of them), "one order (<label>)", or "vote only" (no single order has them together: the vote joined links from
    different orders)."""
    full = [o for o in orders if o in maps and len({maps[o].get(c, f"?{c}") for c in members}) == 1]
    if len(full) >= 2:
        return full, "majority of orders"
    if len(full) == 1:
        return full, f"one order ({full[0]})"
    return full, "vote only"


def guard_pairs(names):
    """[(cluster a, cluster b)] of member pairs that the role guard rejects. names {cluster_id: [name texts]} (the cluster's
    names in the orders and the vote); a pair is rejected when any name of a and any name of b sit on opposite sides of a
    forbidden pair (role_guard.forbidden_merge)."""
    cids = sorted(names)
    return [(a, b) for i, a in enumerate(cids) for b in cids[i + 1:]
            if any(RGD.forbidden_merge(x, y) for x in names[a] for y in names[b])]


def odd_members(member_attrs, member_n):
    """Clusters whose top attribute is not the one with most mentions among the members (ties: attribute name order).
    member_attrs / member_n {cluster_id: ...}."""
    weight = Counter()
    for c, a in member_attrs.items():
        weight[a] += member_n.get(c, 0)
    keep = sorted(weight.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if weight else ""
    return sorted(c for c, a in member_attrs.items() if a != keep)


def wrong_merge_rows(ctx, merges, mentions, orders, vote, maps, names, step, variant="A s012", skip_attrs=()):
    """One dict per wrong merge (WRONG_COLS) of `merges` (rules_groups.merges output). ctx = dict(set, version, ent).
    mentions: the mention table with `cluster_id` and `cls` (rules_groups._mentions). maps: {label: {cluster_id: attr_id}} of
    the orders and the vote; names: {label: {cluster_id: (norm name, action)}}. Rows whose attr_id is in skip_attrs are left
    out (the name merge keeps only the merges the plain variant does not have)."""
    size = mentions.groupby("cluster_id").size().to_dict()
    cls = mentions[mentions["cluster_id"] != ""]
    rows = []
    bad = merges[merges["judged"].astype(bool) & ~merges["right"].astype(bool)]
    for _, r in bad.iterrows():
        if r["attr_id"] in skip_attrs:
            continue
        members = r["members"].split(";")
        attrs = dict(zip(members, r["member_attrs"].split(";")))
        roles = dict(zip(members, r["member_roles"].split(";")))
        noise = {c: float(cls.loc[cls["cluster_id"] == c, "cls"].isin(("noise", "cue")).mean()) for c in members}
        full, source = merge_source(members, maps, orders)
        texts = {c: [names[lab][c][0] for lab in (*orders, vote) if lab in names and c in names[lab] and names[lab][c][0]]
                 for c in members}
        vote_texts = {c: [names[vote][c][0]] if c in names[vote] and names[vote][c][0] else [] for c in members}
        pairs = guard_pairs(texts)
        rows.append({**ctx, "variant": variant, "attr_id": r["attr_id"], "column": r["name"], "step": step,
                     "reason": r["reason"], "n_members": len(members), "members": ";".join(members),
                     "member_attrs": ";".join(attrs[c] for c in members), "member_roles": ";".join(roles[c] for c in members),
                     "member_n": ";".join(str(size.get(c, 0)) for c in members),
                     "member_noise": ";".join(f"{noise[c]:.2f}" for c in members),
                     "odd_members": ";".join(odd_members(attrs, size)), "noise_share": round(float(r["noise_share"]), 3),
                     "source": source, "orders_full": ";".join(full), "guard_name": bool(guard_pairs(vote_texts)),
                     "guard_orders": bool(pairs), "guard_pairs": ";".join(f"{a}+{b}" for a, b in pairs)})
    return rows


def cause_table(rows):
    """DataFrame of counts: per (set, step, reason, source) the number of wrong merges and how many each guard blocks."""
    df = pd.DataFrame(rows, columns=WRONG_COLS)
    if not len(df):
        return pd.DataFrame(columns=["set", "step", "reason", "source", "n", "guard_name", "guard_orders"])
    g = df.groupby(["set", "step", "reason", "source"], sort=True)
    out = g.agg(n=("attr_id", "size"), guard_name=("guard_name", "sum"), guard_orders=("guard_orders", "sum"))
    return out.reset_index()


# ---- task 6: the parts of the J split

def part_clusters(stats, mentions):
    """Long table of the J-split parts: one dict (split, part, cluster, n_part) per cluster that holds mentions of a part.
    stats = j_split.json (members = mention ids, parts = part id 0 / 1 / 2, as step1a_v37.j_split_summary reads it);
    `mentions` = the run's mention table (mention_id, cluster_id). A cluster is a part's cluster when it holds
    its mentions; one part can spread over several clusters (the fold step) and one cluster can hold two parts."""
    cid = dict(zip(mentions["mention_id"].astype(int), mentions["cluster_id"]))
    rows = []
    for k, s in enumerate(stats):
        cnt = Counter((p, cid[i]) for i, p in zip(s["members"], s["parts"]) if cid[i])
        for (p, c), n in sorted(cnt.items()):
            rows.append({"split": k, "part": PART_NAMES[p], "cluster": c, "n_part": n})
    return rows


def gold_part(lev_mentions, ids, gold_ents):
    """(Counter of L2 gold classes, top class, role slot of the top class or "") over the mentions `ids` (mention ids)."""
    sub = lev_mentions[lev_mentions["mention_id"].astype(int).isin({int(i) for i in ids})]
    cnt = Counter(c for g in sub["gold_attr"] for c in _classes(g)) if len(sub) else Counter()
    top = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if cnt else ""
    slot = PS._slot(top, gold_ents) if top else ""
    return cnt, top, slot if slot in PS.ROLE_SLOTS else ""


def joined_with(cluster, siblings, groups):
    """Sibling clusters (other parts of the same split) in the same group as `cluster` under `groups` {cluster: attr_id}."""
    g = groups.get(cluster)
    return sorted(s for s in siblings if s != cluster and g is not None and groups.get(s) == g)


START_WORDS = RGD.PAIRS[0][0] | RGD.PAIRS[1][0]
END_WORDS = RGD.PAIRS[0][1] | RGD.PAIRS[1][1]
GOLD_SIDE = {"departure": "start", "leave at": "start", "destination": "end", "arrive by": "end"}


def name_side(name):
    """"start" / "end" when the name has words of only one side of the departure / destination, leave at / arrive by pairs
    (role_guard word sets), else ""."""
    w = RGD._words(name)
    a, b = bool(w & START_WORDS), bool(w & END_WORDS)
    return "start" if a and not b else "end" if b and not a else ""


def name_ok(name, gold_role):
    """True / False when the name has a side and the part has a gold role: does the side match; None when either is missing."""
    side, want = name_side(name), GOLD_SIDE.get(gold_role, "")
    return None if not side or not want else side == want


def part_rows(set_name, ent, ed_lev, stats, mentions, orders, vote, maps, names, gold_ents):
    """PART_COLS rows: one per (split, part, cluster). name_s0..s2 / name_vote = the cluster's normalised name in each order
    and the vote ("" = marked or missing); joined_* = sibling clusters (other parts of this split) in the same group
    (vote, any order); same_name_vote = a sibling has the same non-empty vote name; joined_back = vote joins a sibling."""
    pc = part_clusters(stats, mentions)
    sib = {}
    for r in pc:
        sib.setdefault(r["split"], set()).add(r["cluster"])
    mid_of = ed_lev.mentions.groupby("cluster_id").size().to_dict()
    cid = dict(zip(mentions["mention_id"].astype(int), mentions["cluster_id"]))
    part_ids = {}
    for k, s in enumerate(stats):
        for i, p in zip(s["members"], s["parts"]):
            part_ids.setdefault((k, PART_NAMES[p], cid[i]), []).append(i)
    out = []
    for r in pc:
        c, k = r["cluster"], r["split"]
        cnt, top, role = gold_part(ed_lev.mentions, part_ids[(k, r["part"], c)], gold_ents)
        nm = {lab: names[lab].get(c, ("", ""))[0] for lab in (*orders, vote)}
        jv = joined_with(c, sib[k], maps[vote])
        jo = sorted({s for o in orders for s in joined_with(c, sib[k], maps[o])})
        same = sorted(s for s in sib[k] if s != c and nm[vote] and names[vote].get(s, ("", ""))[0] == nm[vote])
        out.append({"set": set_name, "ent": ent, "split": k, "part": r["part"], "cluster": c, "n_part": r["n_part"],
                    "n_cluster": mid_of.get(c, 0), "gold_top": top or "-", "gold_role": role or "-",
                    "gold_counts": ", ".join(f"{a} {n}" for a, n in cnt.most_common()) or "-",
                    **{f"name_s{j}": nm[o] for j, o in enumerate(orders)}, "name_vote": nm[vote],
                    "action_vote": names[vote].get(c, ("", ""))[1], "group_vote": maps[vote].get(c, ""),
                    "joined_vote": ";".join(jv), "joined_orders": ";".join(jo), "same_name_vote": ";".join(same),
                    "joined_back": bool(jv), "gold_side": GOLD_SIDE.get(role, ""), "name_side_vote": name_side(nm[vote]),
                    "name_ok_vote": name_ok(nm[vote], role),
                    "name_ok_orders": ";".join(str(name_ok(nm[o], role)) for o in orders)})
    return out


def split_verdicts(rows):
    """{(set, ent, split): verdict} from part_rows. "one role only" = the parts' gold roles are not on both sides (start /
    end) of a pair (the split did not separate two roles); with both sides: "re-merged across roles" (the vote puts parts of different gold roles into one
    group), "unnamed part" (a part with a gold role has no vote name: marked or missing), else "kept apart"."""
    df = pd.DataFrame(rows)
    out = {}
    for key, g in df.groupby(["set", "ent", "split"]):
        if len({x for x in g["gold_side"] if x}) < 2:
            out[key] = "one role only"
            continue
        role_of = dict(zip(g["cluster"], g["gold_role"]))
        side = dict(zip(g["cluster"], g["gold_side"]))
        cross = any(side[c] and side[t] and side[c] != side[t] for c, j in zip(g["cluster"], g["joined_vote"])
                    for t in j.split(";") if t)
        if cross:
            out[key] = "re-merged across roles"
        elif any(role_of[c] != "-" and not n for c, n in zip(g["cluster"], g["name_vote"])):
            out[key] = "unnamed part"
        else:
            out[key] = "kept apart"
    return out


def role_status(rows, ratings, base):
    """Per role base attribute: dict(attr, found groups). rows = rules_names._variant_rows-style dicts (attr_id, name,
    description, majority_gold_attr, ent) of the variant, ratings {(ent, name, description, majority attr): label}, base =
    role base attributes. Returns {attr: [(attr_id, name, label or "unrated")]} over the groups whose majority is attr."""
    out = {a: [] for a in base}
    for r in rows:
        a = r["majority_gold_attr"]
        if a in out and r["name"]:
            out[a].append((r["attr_id"], r["name"], ratings.get((r["ent"], r["name"], r["description"], a), "unrated")))
    return out


def role_cause(groups, found, recoverable):
    """Why a role base attribute is (not) role-correct. groups = role_status()[attr] (groups whose majority is the attribute).
    Returns one of "right", "named partly/wrong (<labels>)", "unrated name", "no group has it as majority (found)",
    "no group has it as majority (recoverable)", "not recoverable by step 1a"."""
    labels = [g[2] for g in groups]
    if "right" in labels:
        return "right"
    if labels:
        bad = sorted(set(labels) - {"unrated"})
        return f"named {'/'.join(bad)}" if bad else "unrated name"
    if found:
        return "no group has it as majority (found)"
    return "no group has it as majority (recoverable)" if recoverable else "not recoverable by step 1a"


def blocked_right(merges, names, orders, vote):
    """Number of judged right merges in which the role guard (any name of the clusters in the orders and the vote) rejects a
    member pair: the guard's cost. merges = rules_groups.merges output; names as for wrong_merge_rows."""
    n = 0
    for _, r in merges[merges["judged"].astype(bool) & merges["right"].astype(bool)].iterrows():
        texts = {c: [names[lab][c][0] for lab in (*orders, vote) if c in names[lab] and names[lab][c][0]]
                 for c in r["members"].split(";")}
        n += bool(guard_pairs(texts))
    return n
