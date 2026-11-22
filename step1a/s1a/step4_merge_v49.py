"""wf_v4.9 B+M: join the tables of one Step 1a entity in the finished schema of Step 4 (chain key `merge_same_entity` of s1a/step4_v44.py; off = v4.8).

Why: variant B (neutral ids) names tables after their majority entity and adds _2, _3 for repeats, so one entity can end as several tables
(accommodation, accommodation_2). No model call; applied by assemble_all to the canonical schema of a chain after the full assembly.
Entity of a table: the most common entity heading (step4_prompts._entity, slugged as in step4_neutral_v48.name_tables) of its columns that come from a
Step 1a column (ties: first in column order); a table with no such column (a link table) is never merged. Tables with the same entity are one group.
Per group: keep the table with most Step 1a columns (ties: a name without a _<n> suffix, then the first); its name, description, row and primary key stay.
Columns: those of the kept table, then the others' in order, skipping a column whose source is already there and a new column whose name is already
there (its id / key column); a sourced column with a taken name gets " 2" (step4_v43._uniq). The primary key column of a dropped table is not carried
over when it is a new column. Links: relationships and foreign keys inside the group are dropped (with the new, non-key columns that held them);
others are re-pointed to the kept table (ref column = the dropped key -> the kept key) and duplicates removed. `unused` and `duplicate_flags` unchanged.
Columns keep their `source`, so the score map of the chain needs no change.
Returns (canonical, merges): merges = [{"entity", "kept", "dropped": [names], "tables_before"}] (empty list = nothing merged).
"""
import copy
import json
import re

from . import step4_prompts as SP
from . import step4_v43 as V

SUFFIX = re.compile(r"_\d+$")


def table_entity(t, entity_of):
    """Majority entity slug of the Step 1a columns of canonical table `t` (ties: first), or None. entity_of = {column id: slug}."""
    ents = [entity_of.get(c["source"], V._slug(c["source"].split(":")[0])) for c in t["columns"] if c.get("source")]
    return max(ents, key=lambda e: (ents.count(e), -ents.index(e))) if ents else None


def _size(t):
    return sum(1 for c in t["columns"] if c.get("source"))


def _absorb(kept, other, fks):
    """Add the columns and foreign keys of table `other` to `kept` (rules in the module doc); fks = list collecting the foreign keys."""
    taken = {x["name"].strip().lower() for x in kept["columns"]}
    sources = {x["source"] for x in kept["columns"] if x.get("source")}
    for col in other["columns"]:
        new = not col.get("source")
        if (new and (col["name"] in other["primary_key"] or col["name"].strip().lower() in taken)) or (not new and col["source"] in sources):
            continue
        kept["columns"].append(col if new else {**col, "name": V._uniq(col["name"], taken)})
        taken.add(col["name"].strip().lower())
        sources.add(col.get("source"))
    fks.extend(other["foreign_keys"])


def merge_same_entity(canonical, cols):
    """(merged copy of the canonical schema, merges); see the module doc. cols = the chain's column dicts (their entity headings)."""
    c = copy.deepcopy(canonical)
    entity_of = {x["id"]: V._slug(SP._entity(x)) for x in cols}
    groups = {}
    for t in c["tables"]:
        e = table_entity(t, entity_of)
        if e:
            groups.setdefault(e, []).append(t)
    merges, keep_of, key_map, group_of = [], {}, {}, {}      # keep_of: dropped table -> kept table; key_map: (dropped table, key) -> kept key
    for e, g in groups.items():
        if len(g) < 2:
            continue
        kept = min(enumerate(g), key=lambda x: (-_size(x[1]), bool(SUFFIX.search(x[1]["name"])), x[0]))[1]
        others = [t for t in g if t is not kept]
        fks = list(kept["foreign_keys"])
        for t in others:
            keep_of[t["name"]] = kept["name"]
            key_map.update({(t["name"], k): kept["primary_key"][0] for k in t["primary_key"] if kept["primary_key"]})
            _absorb(kept, t, fks)
        kept["foreign_keys"] = fks
        group_of.update({t["name"]: e for t in g})
        merges.append({"entity": e, "kept": kept["name"], "dropped": [t["name"] for t in others], "tables_before": len(g)})
    if not merges:
        return c, []
    c["tables"] = [t for t in c["tables"] if t["name"] not in keep_of]
    for t in c["tables"]:
        out, seen, gone = [], set(), set()
        for fk in t["foreign_keys"]:
            if group_of.get(fk["ref_table"]) and group_of.get(fk["ref_table"]) == group_of.get(t["name"]):
                gone.update(fk["columns"])
                continue
            fk = {**fk, "ref_table": keep_of.get(fk["ref_table"], fk["ref_table"]),
                  "ref_columns": [key_map.get((fk["ref_table"], x), x) for x in fk["ref_columns"]]}
            k = json.dumps(fk, sort_keys=True)
            if k not in seen:
                seen.add(k)
                out.append(fk)
        t["foreign_keys"] = out
        dead = gone - {x for f in out for x in f["columns"]} - set(t["primary_key"])
        t["columns"] = [x for x in t["columns"] if x.get("source") or x["name"] not in dead]
    rels, seen = [], set()
    for r in c["relationships"]:
        if group_of.get(r["from"]) and group_of.get(r["from"]) == group_of.get(r["to"]):
            continue
        a, b = keep_of.get(r["from"], r["from"]), keep_of.get(r["to"], r["to"])
        k = (a, b, r["kind"]) if r["kind"] != "many_to_many" else (*sorted((a, b)), r["kind"])
        if k not in seen:
            seen.add(k)
            rels.append({**r, "from": a, "to": b})
    c["relationships"] = rels
    return c, merges
