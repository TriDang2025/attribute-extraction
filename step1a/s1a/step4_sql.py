"""wf_v4 Step 4: from the model answers to the canonical schema JSON (WF_V4_CONTRACT.md), to SQL and to plan operations.

`to_operations(canonical)` returns a list of dicts in this order: all CREATE_ENTITY, then all ADD_ATTR, then all CREATE_REL.
  {"op": "CREATE_ENTITY", "name", "description", "row"}
  {"op": "ADD_ATTR", "entity", "name", "type", "source" (Step-3 column id or None), "is_key" (column is in the primary key)}
  {"op": "CREATE_REL", "from" (referring table), "to", "kind", "fk_columns" (columns of "from" that refer to "to")}
"""
from .step4_prompts import NEW, named_tables

SQL_TYPES = {"text": "TEXT", "integer": "INTEGER", "decimal": "REAL", "time": "TIME", "day": "TEXT", "date": "DATE",
             "boolean": "BOOLEAN", "id": "INTEGER", "duration": "INTERVAL", "price": "NUMERIC(10, 2)"}


def _column(name, type_, source):
    return {"name": name, "type": type_, "source": source, "new": source is None, "gt": None}


def _canon_table(name, description, row, columns, pk, fks):
    return {"name": name, "description": description, "row": row, "columns": columns, "primary_key": pk, "foreign_keys": fks}


def assemble(a41, a42, a43, a44, cols=None):
    """Canonical schema from the validated answers of 4.1 to 4.4. A column "new:<x>" gets source None and new true; a
    new primary key (`primary_key` "new") becomes a leading column `new_id_name` of type id. `cols` is accepted for the
    caller's convenience and not needed (the ids are in the answers)."""
    meta = {t["name"]: t for t in named_tables(a41, a42, a43)}
    tables = []
    for t in a44["tables"]:
        names, columns = {}, []     # column reference -> column name
        if t["primary_key"] == NEW:
            names[f"new:{t['new_id_name']}"] = t["new_id_name"]
            columns.append(_column(t["new_id_name"], "id", None))
        for c in t["columns"]:
            names[c["column"]] = c["name"]
            columns.append(_column(c["name"], c["type"], None if c["column"].startswith("new:") else c["column"]))
        tables.append((t, names, columns))
    refnames = {t["name"]: names for t, names, _ in tables}

    def resolve(table, ref):
        return refnames.get(table, {}).get(ref, ref[4:] if str(ref).startswith("new:") else ref)

    out = []
    for t, names, columns in tables:
        m = meta[t["name"]]
        pk = [names[f"new:{t['new_id_name']}"] if t["primary_key"] == NEW else names[t["primary_key"]]]
        fks = [{"columns": [resolve(t["name"], f["column"])], "ref_table": f["ref_table"],
                "ref_columns": [resolve(f["ref_table"], f["ref_column"])]} for f in t.get("foreign_keys", [])]
        out.append(_canon_table(t["name"], m["description"], m["row"], columns, pk, fks))
    return {"tables": out,
            "relationships": [{"from": r["from"], "to": r["to"], "kind": r["kind"], "reason": r.get("reason", "")}
                              for r in a43.get("relationships", [])],
            "unused": [{"source": u["column"], "reason": u.get("reason", "")} for u in a41.get("unused", [])],
            "duplicate_flags": [{"source": d["column"], "duplicate_of": d["duplicate_of"]} for d in a41.get("duplicate_flags", [])]}


def from_e(answer):
    """Canonical schema from a parsed (e) answer: every column has source None and new true (no Step-3 ids)."""
    tables = [_canon_table(t["name"], t.get("description", ""), t.get("row", ""),
                           [_column(c["name"], c["type"], None) for c in t.get("columns", [])],
                           list(t.get("primary_key", [])),
                           [{"columns": [f["column"]], "ref_table": f["ref_table"], "ref_columns": [f["ref_column"]]}
                            for f in t.get("foreign_keys", [])])
              for t in answer.get("tables", [])]
    return {"tables": tables,
            "relationships": [{"from": r["from"], "to": r["to"], "kind": r["kind"], "reason": r.get("reason", "")}
                              for r in answer.get("relationships", [])],
            "unused": [], "duplicate_flags": []}


def quote(name):
    """SQL identifier in double quotes."""
    return '"' + str(name).replace('"', '""') + '"'


def _ordered(tables):
    """Tables with referenced tables first (input order otherwise; a cycle keeps its input order)."""
    by = {t["name"]: t for t in tables}
    done, out = set(), []

    def visit(t, stack):
        if t["name"] in done or t["name"] in stack:
            return
        for fk in t["foreign_keys"]:
            if fk["ref_table"] in by:
                visit(by[fk["ref_table"]], stack | {t["name"]})
        if t["name"] not in done:
            done.add(t["name"])
            out.append(t)

    for t in tables:
        visit(t, frozenset())
    return out


def to_sql(canonical):
    """CREATE TABLE statements (identifiers quoted, PRIMARY KEY and FOREIGN KEY clauses), referenced tables first."""
    stmts = []
    for t in _ordered(canonical["tables"]):
        lines = [f"  {quote(c['name'])} {SQL_TYPES.get(c['type'], 'TEXT')}" for c in t["columns"]]
        if t["primary_key"]:
            lines.append(f"  PRIMARY KEY ({', '.join(quote(c) for c in t['primary_key'])})")
        for fk in t["foreign_keys"]:
            lines.append(f"  FOREIGN KEY ({', '.join(quote(c) for c in fk['columns'])}) REFERENCES "
                         f"{quote(fk['ref_table'])} ({', '.join(quote(c) for c in fk['ref_columns'])})")
        stmts.append(f"CREATE TABLE {quote(t['name'])} (\n" + ",\n".join(lines) + "\n);")
    return "\n\n".join(stmts) + "\n"


def to_operations(canonical):
    """Plan operations (format in the module docstring)."""
    ops = [{"op": "CREATE_ENTITY", "name": t["name"], "description": t["description"], "row": t["row"]} for t in canonical["tables"]]
    ops += [{"op": "ADD_ATTR", "entity": t["name"], "name": c["name"], "type": c["type"], "source": c["source"],
             "is_key": c["name"] in t["primary_key"]} for t in canonical["tables"] for c in t["columns"]]
    tabs = {t["name"]: t for t in canonical["tables"]}
    for r in canonical["relationships"]:
        fk_cols = [c for fk in tabs.get(r["from"], {}).get("foreign_keys", []) if fk["ref_table"] == r["to"] for c in fk["columns"]]
        ops.append({"op": "CREATE_REL", "from": r["from"], "to": r["to"], "kind": r["kind"], "fk_columns": fk_cols})
    return ops
