"""wf_v4.1 diary Nov 7 task 6: the v3.8 duplicate check after loop 2 Step 3, so a new column cannot repeat an old one (pure; no I/O).

Old columns = the entity's handover columns (frozen loop 1). New columns = the loop-2 clusters that the voted Step 3 answer names
(action other than not_attribute; clusters with the same name form one column). Per entity the frozen v3.8 prompt
(batch_v38.render_dupcheck / schema_dupcheck) lists old and new columns together, in 2 shuffled orders (batch_v39.shuffled_order,
seeds 0 and 1), as v3.9 ran it on 2 orders.
Decision (resolve):
- same name: a new column whose name equals an old column's name (pilot_verify.norm_name) is a duplicate, no LLM needed;
- dupcheck: a new column that a join puts with an old column in BOTH orders is a duplicate of that column (joins cleaned as
  score_v39_batch.clean_joins, role pairs blocked by batch_v38.check_joins);
- new columns that both orders join with each other become one column (name of the member with the most mentions);
- old-old joins are ignored: the handover is frozen.
Nothing in the frozen Step 3 code changes.
"""
from collections import Counter

from . import batch_v38 as BT
from . import batch_v39 as B9
from . import pilot_verify as PV
from . import score_v39_batch as SB

ORDERS = (0, 1)
N_TOP = 5


def new_columns(dec, clusters, first_cid):
    """New column dicts (cid, name, description, top_values, clusters, n_mentions) from the voted decision table `dec`
    (pilot_verify.DEC_COLS) of one entity; clusters = {L2 id: cluster record}. cids from `first_cid` on, in table order."""
    groups = {}
    for r in dec.to_dict("records"):
        if r["action"] in ("not_attribute", "", None) or not r["name"]:
            continue
        g = groups.setdefault(PV.norm_name(r["name"]), {"name": r["name"], "description": r["description"] or "", "clusters": []})
        g["clusters"].append(r["cluster_id"])
    out = []
    for i, g in enumerate(groups.values()):
        vals = Counter(m["norm_value"] for c in g["clusters"] for m in clusters[c]["mentions"])
        out.append({"cid": first_cid + i, **g, "n_mentions": sum(vals.values()),
                    "top_values": [v for v, _ in sorted(vals.items(), key=lambda kv: (-kv[1], kv[0]))[:N_TOP]]})
    return out


def old_columns(handover):
    """Old column dicts (cid = handover id) of one handover file."""
    return [{"cid": int(c["id"]), "name": c["name"], "description": c.get("description") or "", "top_values": list(c.get("top_values", [])),
             "n_mentions": c.get("n_mentions", 0)} for c in handover["columns"]]


def prompts(old, new, salt):
    """{order: (prompt text, schema)} of the duplicate check over old + new columns; `salt` (e.g. "dev50/hotel") fixes the shuffle."""
    cols = old + new
    out = {}
    for o in ORDERS:
        shown = B9.shuffled_order(cols, o, salt)
        out[o] = (BT.render_dupcheck(shown), BT.schema_dupcheck([c["cid"] for c in shown]))
    return out


def agreed_pairs(parsed_by_order, cols_by_id):
    """Set of frozenset({a, b}) column pairs that a kept join (clean_joins, then check_joins) puts together in every order."""
    sets = []
    for parsed in parsed_by_order:
        joins, _ = SB.clean_joins([j for j in parsed.get("joins", []) if all(c in cols_by_id for c in j.get("columns", []))])
        kept, _ = BT.check_joins(joins, cols_by_id)
        sets.append({frozenset((a, b)) for j in kept for i, a in enumerate(j["columns"]) for b in j["columns"][i + 1:]})
    return set.intersection(*sets) if sets else set()


def resolve(old, new, parsed_by_order):
    """Final new columns: [{name, description, clusters, top_values, n_mentions, status, duplicate_of, reason, joined}]. status "new" or
    "duplicate" (duplicate_of = old column names; reason "same name" or "dupcheck, both orders"); joined = names of the new columns
    merged into this one."""
    by_id = {c["cid"]: c for c in old + new}
    old_ids, new_ids = {c["cid"] for c in old}, [c["cid"] for c in new]
    pairs = agreed_pairs(parsed_by_order, by_id)
    old_by_name = {PV.norm_name(c["name"]): c for c in old}
    status = {}
    for n in new_ids:
        same = old_by_name.get(PV.norm_name(by_id[n]["name"]))
        partners = sorted(o for p in pairs if n in p for o in p - {n} if o in old_ids)
        if same:
            status[n] = ([same["name"]], "same name")
        elif partners:
            status[n] = ([by_id[o]["name"] for o in partners], "dupcheck, both orders")
    parent = {n: n for n in new_ids if n not in status}          # union-find over the remaining new columns

    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for p in pairs:
        a, b = sorted(p)
        if a in parent and b in parent:
            parent[root(b)] = root(a)
    out = []
    for n in new_ids:
        c = by_id[n]
        if n in status:
            out.append({**_keep(c), "status": "duplicate", "duplicate_of": status[n][0], "reason": status[n][1], "joined": []})
        elif root(n) == n:
            members = [by_id[m] for m in parent if root(m) == n]
            head = max(members, key=lambda m: (m["n_mentions"], -m["cid"]))
            vals = Counter(v for m in members for v in m["top_values"])
            out.append({**_keep(head), "clusters": [x for m in members for x in m["clusters"]],
                        "n_mentions": sum(m["n_mentions"] for m in members),
                        "top_values": [v for v, _ in sorted(vals.items(), key=lambda kv: (-kv[1], kv[0]))[:N_TOP]],
                        "status": "new", "duplicate_of": [], "reason": "", "joined": [m["name"] for m in members if m is not head]})
    return out


def _keep(c):
    return {k: c[k] for k in ("name", "description", "clusters", "top_values", "n_mentions")}
