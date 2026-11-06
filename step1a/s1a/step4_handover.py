"""wf_v4 task 16: Step-4 handover. The chosen setting (main, input a, seed 0; run `a_<set>_s0`) as a schema in which every column is linked
to its Step-3 column (id "<entity>:<id>") and its table. Pure; files are read and written by scripts/handover_v4.py.

schema.json = canonical schema (WF_V4_CONTRACT.md) + per column `step3` (entity, id, name, description, n_mentions, mention_ids count, value type),
per unused entry the same, and `source_to_table` {Step-3 column id: table name or null when the column is unused}.
"""


def index_columns(handover):
    """{"<entity>:<id>": handover column dict} from {entity: handover file dict}."""
    return {f"{ent}:{c['id']}": {**c, "entity": ent} for ent, doc in handover.items() for c in doc["columns"]}


def _step3(col):
    return {"entity": col["entity"], "id": col["id"], "name": col["name"], "description": col.get("description", ""), "n_mentions": col["n_mentions"],
            "n_dialogues": col["n_dialogues"], "value_type": col["value_type"]["dominant"], "top_values": col.get("top_values", [])}


def build(canonical, handover, set_name, run):
    """Handover schema dict. Raises ValueError for a source that is not a Step-3 column of the set."""
    idx = index_columns(handover)

    def link(source):
        if source is None:
            return None
        if source not in idx:
            raise ValueError(f"source {source!r} is not a Step-3 column of {set_name}")
        return _step3(idx[source])

    s2t = {s: None for s in idx}
    tables = []
    for t in canonical["tables"]:
        cols = []
        for c in t["columns"]:
            cols.append({**c, "step3": link(c["source"])})
            if c["source"]:
                s2t[c["source"]] = t["name"]
        tables.append({**t, "columns": cols})
    unused = [{**u, "step3": link(u["source"])} for u in canonical.get("unused", [])]
    return {"set": set_name, "setting": f"main (input a, no signals), column order seed 0; run {run}", "tables": tables,
            "relationships": canonical["relationships"], "unused": unused, "duplicate_flags": canonical.get("duplicate_flags", []),
            "source_to_table": s2t}


def check(schema, handover):
    """Problems (empty = fine): a Step-3 column that is neither in a table nor unused, or placed twice."""
    idx = index_columns(handover)
    seen, problems = {}, []
    for t in schema["tables"]:
        for c in t["columns"]:
            if c["source"]:
                if c["source"] in seen:
                    problems.append(f"{c['source']} in two places: {seen[c['source']]}, {t['name']}")
                seen[c["source"]] = t["name"]
    for u in schema["unused"]:
        if u["source"] in seen:
            problems.append(f"{u['source']} is both unused and in {seen[u['source']]}")
        seen[u["source"]] = "unused"
    problems += [f"{s} is neither in a table nor unused" for s in idx if s not in seen]
    return problems
