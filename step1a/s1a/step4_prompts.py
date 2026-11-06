"""wf_v4 Step 4 (schema creation): the four chained prompts (4.1 group, 4.2 name, 4.3 relationships, 4.4 keys and types),
the dialogues-only prompt (e), their JSON schemas for guided decoding and the validators. Pure functions; no model, no file
access (contract: WF_V4_CONTRACT.md). Each build_* returns (prompt text, JSON schema). A prompt never names a dataset and
gives no hint of the expected schema.

Data passed between the steps (the parsed JSON answers):
  a41 {groups:[{group, columns:[id], note}], unused:[{column, reason}], duplicate_flags:[{column, duplicate_of}]}
  a42 {tables:[{group, name, description, row}]}
  a43 {relationships:[{from, to, kind, reason}], new_tables:[{name, description, row, between:[t1, t2]}]}
  a44 {tables:[{name, primary_key, new_id_name, columns:[{column, name, type}], foreign_keys:[{column, ref_table, ref_column}]}]}
`cols` is a list of column dicts: {id "<entity>:<id>", name, description, role, value_type, examples, n_mentions,
n_dialogues, signal (optional text), flag (optional text)}; `columns_from_handover` makes them from a handover file.
In 4.4 a column is an existing id or "new:<name>"; primary_key is an existing id of the table or "new" (then new_id_name
names the key; that key column is not listed again in `columns`).
"""
from .pilot_input import est_tokens

TYPES = ["text", "integer", "decimal", "time", "day", "date", "boolean", "id", "duration", "price"]
KINDS = ["one_to_many", "many_to_many"]
NEW = "new"
NEW_REF_PATTERN = "^new:.+"
_TYPE_HELP = ("text = free text or a name, integer = whole number, decimal = number with a fraction, time = clock time, "
              "day = day of the week, date = calendar date, boolean = yes/no, id = identifier or reference code, "
              "duration = length of time, price = amount of money")
_JSON_ONLY = "Return ONLY one JSON object, nothing before or after it."
DATA_SIGNALS_NOTE = (' Lines labelled "data signals" are automatic counts over the dialogues (for example how often a column has '
                     'several values in one booking, or appears together with another column); they can be misleading.')

INSTRUCTION_41 = """\
Below are the columns found by analysing a corpus of dialogues. Each column is a kind of information that people give
in the dialogues, with a description, the type of its values, a few example values (each with a short piece of text
around it) and counts. The columns were found
under {n_ent} headings; the id of a column starts with its heading, but a heading may be wrong.
Design a relational database from these columns. Step 1: put every column into exactly one group; each group will
become one table of the database. A table may hold columns from several of the headings below. If a column would
not be stored in any table (noise, a booking word, a value a database would not keep), do not put it in a group; list
it as unused with a reason. If a column looks like a duplicate of another column, say so in duplicate_flags; this is
only a flag, the column still goes into a group (or into unused). Lines labelled "checker" and "checker evidence" are
automatic and can be wrong; decide from the descriptions and examples.{notes}
{json_only} Shape (the names and ids here are made up):
{{"groups": [{{"group": "G1", "columns": ["x:1", "x:4"], "note": "what the columns have in common"}}],
 "unused": [{{"column": "x:2", "reason": "..."}}],
 "duplicate_flags": [{{"column": "x:4", "duplicate_of": "x:1"}}]}}
Use the group names G1, G2, ... .

Columns ({n_cols}):
"""

INSTRUCTION_42 = """\
Below are the groups of columns of a relational database design. Each group will become one table. For every group give
the table a name (lower case, words separated by "_"), a one-sentence description, and what one row of the table stands
for (for example "one lecture" or "one library loan").
{json_only} Shape (the names here are made up):
{{"tables": [{{"group": "G1", "name": "lecture", "description": "A lecture given in a course.", "row": "one lecture"}}]}}
Every group must appear exactly once.

Groups:
"""

INSTRUCTION_43 = """\
Below are the tables of a relational database design, each with its columns. Decide how the tables relate to each other.
For each pair of tables that are related, give one relationship: "from" is the table that refers to the other (the
many side, whose rows carry the reference), "to" is the table it refers to, "kind" is one_to_many or many_to_many, and
"reason" is one short sentence. If two tables are related many-to-many, or a relationship needs a table of its own,
add a new linking table in new_tables (name, description, what one row stands for, and the two tables it sits
between); the relationships of a new table are listed like any other. Do not invent a relationship that the columns do
not support.
{json_only} Shape (the names here are made up):
{{"relationships": [{{"from": "loan", "to": "book", "kind": "one_to_many", "reason": "A book is lent many times."}}],
 "new_tables": [{{"name": "loan_item", "description": "...", "row": "one book on one loan", "between": ["loan", "book"]}}]}}
Give empty lists when there is nothing to add.

Tables:
"""

INSTRUCTION_44 = """\
Below are the tables of a relational database design with their columns, and the relationships between the tables.
Finish the design: for every table (the new linking tables too) give
- the primary key: the id of one of the table's columns, or "new" when no column can identify a row (then give the name
  of the new key column in new_id_name, and do not list that key column again in columns);
- the columns of the table, each with its id (or "new:<name>" for a column you add, for example a reference column of a
  linking table), the column name to use, and its type, one of: {types};
- the foreign keys: the column of this table, the table it refers to and the column of that table (an id, or
  "new:<name>" for a new column or a new key; for a new key use "new:" plus its new_id_name).
Every relationship below must be implemented by a foreign key in the table on its "from" side (a linking table
implements its own relationships). Every column listed under a table must appear in that table, exactly once.
{json_only} Shape (the names and ids here are made up):
{{"tables": [{{"name": "loan", "primary_key": "new", "new_id_name": "loan id",
   "columns": [{{"column": "x:3", "name": "due date", "type": "date"}}, {{"column": "new:book id", "name": "book id", "type": "id"}}],
   "foreign_keys": [{{"column": "new:book id", "ref_table": "book", "ref_column": "x:7"}}]}}]}}
Use "" as new_id_name when the primary key is an existing column.

"""

INSTRUCTION_E = """\
Design a relational schema for the information in these dialogues: tables, columns with types, primary keys and foreign keys.
For every table give a name (lower case), a one-sentence description and what one row stands for. Column types are one of:
{types}. Also list the relationships between the tables: "from" is the table that refers to the other (the many side),
"to" is the table it refers to, "kind" is one_to_many or many_to_many.
{json_only} Shape (the names here are made up):
{{"tables": [{{"name": "loan", "description": "...", "row": "one loan", "primary_key": ["loan id"],
   "columns": [{{"name": "loan id", "type": "id"}}, {{"name": "book id", "type": "id"}}],
   "foreign_keys": [{{"column": "book id", "ref_table": "book", "ref_column": "book id"}}]}}],
 "relationships": [{{"from": "loan", "to": "book", "kind": "one_to_many", "reason": "..."}}]}}

Dialogues:
"""

VALUE_TYPE_TO_TYPE = {"number": "integer"}   # Step-3 value types that are not canonical types; all others (text, time, day, price, ...) are
OPTIONS = ["P1", "P2", "P3", "P4", "P5"]

INSTRUCTION_PLACE = """Below is a relational database schema (its tables, columns, keys and relationships) and one new column, a kind of
information found in dialogues. Decide where the new column belongs. Choose exactly one option:
- P1: the column is one more property of the rows of an existing table; it is stored in that table (target_table).
- P2: the column describes a relationship between rows of two tables (for example something that is true of a pair, not of
  either one alone); it is stored in the table that implements that relationship (target_table), or in a new linking table
  (new_table) between the two tables given in link.
- P3: the column needs a new table of its own (new_table: its name and what one row stands for); give in link how the new
  table relates to an existing table.
- P4: the column creates a new relationship between two tables that exist already: it is the reference that ties rows of
  the table in link.from to rows of the table in link.to (target_table = link.from).
- P5: the column and the columns of an existing table (target_table) belong together in a table of their own (new_table).
Use null for new_table and link when the option needs none. "kind" is one_to_many or many_to_many; "from" is the table that
refers to the other (the many side).
{json_only} Shape (the names here are made up):
{{"reason": "one short sentence", "option": "P1", "target_table": "loan", "new_table": null, "link": null}}

Schema:
"""


def canon_type(value_type):
    """Canonical column type of a Step-3 value type (dict {dominant, ...}, a string, or None -> text)."""
    vt = value_type.get("dominant") if isinstance(value_type, dict) else value_type
    vt = VALUE_TYPE_TO_TYPE.get(vt, vt)
    return vt if vt in TYPES else "text"


# ---------------------------------------------------------------- rendering
def _vtype(c):
    vt = c.get("value_type")
    if isinstance(vt, dict):
        share = vt.get("share")
        return f"{vt.get('dominant', '?')} (share {share:.2f})" if isinstance(share, (int, float)) else str(vt.get("dominant", "?"))
    return str(vt or "?")


def render_column(c, max_examples=5):
    """Text block of one column."""
    exs = (c.get("examples") or [])[:max_examples]
    lines = [f"[{c['id']}] {c['name']}"]
    if c.get("description"):
        lines.append(f"  description: {c['description']}")
    if c.get("role"):
        lines.append(f"  role: {c['role']}")
    lines.append(f"  values: {_vtype(c)}; {c.get('n_mentions', 0)} mentions in {c.get('n_dialogues', 0)} dialogues")
    if exs and all(isinstance(e, str) for e in exs):
        lines.append("  examples: " + ", ".join(f'"{e}"' for e in exs))
    elif exs:
        lines.append("  examples:")
        lines += [f'    "{e}"' if isinstance(e, str) else (f'    "{e[0]}" (in: "{e[1]}")' if e[1] else f'    "{e[0]}"') for e in exs]
    else:
        lines.append("  no examples")
    if c.get("signal"):
        lines.append(f"  checker evidence: {c['signal']}")
    if c.get("data_signal"):
        lines.append(f"  data signals: {c['data_signal']}")
    if c.get("flag"):
        lines.append(f"  checker: {c['flag']}")
    return "\n".join(lines)


def _entity(c):
    """Heading of a column: its `entity` field, else the part of its id before the colon."""
    return c.get("entity") or c["id"].split(":")[0]


def render_columns(cols, max_examples=5):
    """Column block of prompt 4.1 (blocks under an `== entity ==` header, input order kept)."""
    out, last = [], None
    for c in cols:
        ent = _entity(c)
        if ent != last:
            out.append(f"== {ent} ==")
            last = ent
        out.append(render_column(c, max_examples))
    return "\n".join(out) + "\n"


def columns_from_handover(entity, data):
    """Column dicts (ids "<entity>:<id>") from the parsed handover file `data` of one entity; the evidence card becomes the
    signals text, the verdict and true flags become the checker text (empty for verdict "real" without flags)."""
    cols = []
    for c in data["columns"]:
        ev, fl = c.get("evidence") or {}, c.get("flags") or {}
        sig = []
        for k, label in (("support", "support"), ("neighbour_fit", "fits a neighbouring column")):
            s = ev.get(k)
            if s:
                sig.append(f"{label} {s['yes']}/{s['n']}")
        if ev.get("mixed_roles"):
            sig.append("answers suggest mixed roles")
        flags = [k.replace("_", " ") for k in ("noise", "too_general", "mixed_roles") if fl.get(k)]
        flag = c.get("verdict", "")
        if flags:
            flag += "; flags: " + ", ".join(flags)
        cols.append({"id": f"{entity}:{c['id']}", "name": c["name"], "description": c.get("description", ""),
                     "role": c.get("role", ""), "value_type": c.get("value_type"), "examples": c.get("top_values", []),
                     "n_mentions": c.get("n_mentions", 0), "n_dialogues": c.get("n_dialogues", 0),
                     "signal": "; ".join(sig), "flag": flag if flag != "real" else ""})
    return cols


def first_prompt_tokens(text):
    """Estimated tokens of a prompt (pilot_input.est_tokens)."""
    return est_tokens(text)


def _by_id(cols):
    return {c["id"]: c for c in cols}


def _obj(props, required=None):
    return {"type": "object", "properties": props, "required": required or list(props)}


def _arr(item):
    return {"type": "array", "items": item}


_S = {"type": "string"}
_TABLE_TEXT = {"description": _S, "row": _S}


def _ref(ids):
    """A column reference: an existing id or "new:<name>"."""
    return {"anyOf": [{"enum": list(ids)}, {"type": "string", "pattern": NEW_REF_PATTERN}]}


# ---------------------------------------------------------------- 4.1 group
def build_prompt_41(column_block, cols):
    """(prompt, schema) of 4.1. `column_block` is the rendered columns; `cols` gives the ids for the schema enums."""
    ids = [c["id"] for c in cols]
    ents = list(dict.fromkeys(_entity(c) for c in cols))
    notes = DATA_SIGNALS_NOTE if any(c.get("data_signal") for c in cols) else ""
    text = INSTRUCTION_41.format(n_ent=len(ents), n_cols=len(ids), notes=notes, json_only=_JSON_ONLY) + column_block + "\nReturn the JSON object now.\n"
    schema = _obj({
        "groups": _arr(_obj({"group": {"type": "string", "pattern": r"^G[0-9]+$"}, "columns": _arr({"enum": ids}), "note": _S})),
        "unused": _arr(_obj({"column": {"enum": ids}, "reason": _S})),
        "duplicate_flags": _arr(_obj({"column": {"enum": ids}, "duplicate_of": {"enum": ids}}))})
    return text, schema


def validate_41(a, cols):
    """Errors of a parsed 4.1 answer: unknown / duplicated / missing columns, bad flags."""
    ids = set(_by_id(cols))
    errs, seen = [], {}
    names = [g.get("group") for g in a.get("groups", [])]
    errs += [f"duplicate group name {n!r}" for n in set(names) if names.count(n) > 1]
    for g in a.get("groups", []):
        if not g.get("columns"):
            errs.append(f"group {g.get('group')!r} is empty")
        for c in g.get("columns", []):
            if c not in ids:
                errs.append(f"unknown column {c!r} in group {g.get('group')!r}")
            elif c in seen:
                errs.append(f"column {c!r} in two groups ({seen[c]!r}, {g.get('group')!r})" if seen[c] != g.get("group")
                            else f"column {c!r} twice in group {g.get('group')!r}")
            seen[c] = g.get("group")
    used = set()
    for u in a.get("unused", []):
        c = u.get("column")
        if c not in ids:
            errs.append(f"unknown unused column {c!r}")
        elif c in seen:
            errs.append(f"column {c!r} both in a group and unused")
        elif c in used:
            errs.append(f"column {c!r} unused twice")
        used.add(c)
    errs += [f"column {c!r} neither in a group nor unused" for c in sorted(ids - set(seen) - used)]
    for d in a.get("duplicate_flags", []):
        for k in ("column", "duplicate_of"):
            if d.get(k) not in ids:
                errs.append(f"unknown duplicate_flags {k} {d.get(k)!r}")
        if d.get("column") == d.get("duplicate_of"):
            errs.append(f"column {d.get('column')!r} flagged as duplicate of itself")
    return errs


# ---------------------------------------------------------------- 4.2 name
def _render_groups(a41, cols):
    cb = _by_id(cols)
    out = []
    for g in a41["groups"]:
        out.append(f"{g['group']}" + (f" ({g['note']})" if g.get("note") else "") + ":")
        out += [render_column(cb[c], 3) for c in g["columns"] if c in cb]
    return "\n".join(out) + "\n"


def build_prompt_42(a41, cols):
    """(prompt, schema) of 4.2 from the 4.1 answer."""
    groups = [g["group"] for g in a41["groups"]]
    text = INSTRUCTION_42.format(json_only=_JSON_ONLY) + _render_groups(a41, cols) + "\nReturn the JSON object now.\n"
    schema = _obj({"tables": _arr(_obj({"group": {"enum": groups}, "name": _S, **_TABLE_TEXT}))})
    return text, schema


def validate_42(a, a41):
    """Errors of a parsed 4.2 answer: every group named exactly once, unique non-empty names."""
    groups = [g["group"] for g in a41["groups"]]
    errs, seen, names = [], [], []
    for t in a.get("tables", []):
        g = t.get("group")
        if g not in groups:
            errs.append(f"unknown group {g!r}")
        elif g in seen:
            errs.append(f"group {g!r} named twice")
        seen.append(g)
        for k in ("name", "description", "row"):
            if not str(t.get(k) or "").strip():
                errs.append(f"table of group {g!r}: empty {k}")
        names.append(str(t.get("name") or "").strip().lower())
    errs += [f"duplicate table name {n!r}" for n in set(names) if n and names.count(n) > 1]
    errs += [f"group {g!r} not named" for g in groups if g not in seen]
    return errs


def named_tables(a41, a42, a43=None):
    """Tables of the design so far: [{name, description, row, group, columns:[ids], new}]; the new linking tables of
    4.3 come last, with no columns."""
    cols_of = {g["group"]: list(g["columns"]) for g in a41["groups"]}
    out = [{"name": t["name"], "description": t["description"], "row": t["row"], "group": t["group"],
            "columns": cols_of.get(t["group"], []), "new": False} for t in a42["tables"]]
    for n in (a43 or {}).get("new_tables", []):
        out.append({"name": n["name"], "description": n["description"], "row": n["row"], "group": None, "columns": [],
                    "new": True, "between": list(n.get("between", []))})
    return out


def _render_tables(tables, cb):
    out = []
    for t in tables:
        out.append(f"Table {t['name']}: {t['description']} One row = {t['row']}." + (" (new linking table)" if t["new"] else ""))
        out += [render_column(cb[c], 3) for c in t["columns"] if c in cb]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 4.3 relationships
def build_prompt_43(a41, a42, cols):
    """(prompt, schema) of 4.3 from the 4.1 and 4.2 answers."""
    tables = named_tables(a41, a42)
    names = [t["name"] for t in tables]
    text = INSTRUCTION_43.format(json_only=_JSON_ONLY) + _render_tables(tables, _by_id(cols)) + "\nReturn the JSON object now.\n"
    schema = _obj({
        "relationships": _arr(_obj({"from": _S, "to": _S, "kind": {"enum": KINDS}, "reason": _S})),
        "new_tables": _arr(_obj({"name": _S, **_TABLE_TEXT, "between": {"type": "array", "items": {"enum": names}, "minItems": 2, "maxItems": 2}}))})
    return text, schema


def validate_43(a, a41, a42):
    """Errors of a parsed 4.3 answer: unknown tables, bad kind, new tables clashing with old names or between unknown tables."""
    old = [t["name"] for t in named_tables(a41, a42)]
    errs, new = [], []
    for n in a.get("new_tables", []):
        nm = n.get("name")
        if not str(nm or "").strip():
            errs.append("new table without a name")
        elif nm in old or nm in new:
            errs.append(f"new table name {nm!r} already used")
        new.append(nm)
        b = n.get("between", [])
        if len(b) != 2 or len(set(b)) != 2 or any(x not in old for x in b):
            errs.append(f"new table {nm!r}: between must be two different existing tables")
    allnames = set(old) | set(new)
    for i, r in enumerate(a.get("relationships", [])):
        for k in ("from", "to"):
            if r.get(k) not in allnames:
                errs.append(f"relationships[{i}] unknown table {r.get(k)!r}")
        if r.get("from") == r.get("to"):
            errs.append(f"relationships[{i}] relates a table to itself")
        if r.get("kind") not in KINDS:
            errs.append(f"relationships[{i}] bad kind {r.get('kind')!r}")
    return errs


# ---------------------------------------------------------------- 4.4 keys and types
def build_prompt_44(a41, a42, a43, cols):
    """(prompt, schema) of 4.4 from the answers of 4.1 to 4.3."""
    tables = named_tables(a41, a42, a43)
    names = [t["name"] for t in tables]
    ids = [c["id"] for c in cols]
    rels = "\n".join(f"- {r['from']} -> {r['to']} ({r['kind']}): {r['reason']}" for r in a43.get("relationships", [])) or "(none)"
    text = (INSTRUCTION_44.format(types=_TYPE_HELP, json_only=_JSON_ONLY) + _render_tables(tables, _by_id(cols))
            + "\nRelationships (from = refers to, to = referred to):\n" + rels + "\n\nReturn the JSON object now.\n")
    col = _obj({"column": _ref(ids), "name": _S, "type": {"enum": TYPES}})
    fk = _obj({"column": _ref(ids), "ref_table": {"enum": names}, "ref_column": _ref(ids)})
    schema = _obj({"tables": _arr(_obj({"name": {"enum": names}, "primary_key": {"enum": ids + [NEW]}, "new_id_name": _S,
                                        "columns": _arr(col), "foreign_keys": _arr(fk)}))})
    return text, schema


def table_refs(t):
    """Set of column references a parsed 4.4 table defines: its listed columns plus "new:<new_id_name>" for a new key."""
    refs = {c.get("column") for c in t.get("columns", [])}
    if t.get("primary_key") == NEW:
        refs.add(f"new:{t.get('new_id_name')}")
    return refs


def validate_44(a, a41, a42, a43, cols):
    """Errors of a parsed 4.4 answer: tables once each, columns of a table exactly its group's (plus new ones), types,
    primary key, foreign keys to known tables / columns, every 4.3 relationship implemented by a foreign key."""
    tables = {t["name"]: t for t in named_tables(a41, a42, a43)}
    errs, got, used = [], {}, {}
    for t in a.get("tables", []):
        n = t.get("name")
        if n not in tables:
            errs.append(f"unknown table {n!r}")
            continue
        if n in got:
            errs.append(f"table {n!r} given twice")
        got[n] = t
        listed = [c.get("column") for c in t.get("columns", [])]
        for c in set(listed):
            if listed.count(c) > 1:
                errs.append(f"table {n!r}: column {c!r} twice")
            if c in used and used[c] != n:
                errs.append(f"column {c!r} in two tables ({used[c]!r}, {n!r})")
            used[c] = n
            if not str(c).startswith("new:") and c not in tables[n]["columns"]:
                errs.append(f"table {n!r}: column {c!r} not in its group")
        errs += [f"table {n!r}: column {c!r} missing" for c in tables[n]["columns"] if c not in listed]
        cn = [str(c.get("name") or "").strip().lower() for c in t.get("columns", [])]
        errs += [f"table {n!r}: column name {x!r} empty or twice" for x in set(cn) if not x or cn.count(x) > 1]
        errs += [f"table {n!r}: bad type {c.get('type')!r}" for c in t.get("columns", []) if c.get("type") not in TYPES]
        pk = t.get("primary_key")
        if pk == NEW:
            if not str(t.get("new_id_name") or "").strip():
                errs.append(f"table {n!r}: new primary key without new_id_name")
            elif str(t["new_id_name"]).strip().lower() in cn:
                errs.append(f"table {n!r}: new key name {t['new_id_name']!r} is also a column name")
        elif pk not in listed:
            errs.append(f"table {n!r}: primary key {pk!r} is not one of its columns")
    errs += [f"table {n!r} missing" for n in tables if n not in got]
    for n, t in got.items():
        for f in t.get("foreign_keys", []):
            rt = f.get("ref_table")
            if f.get("column") not in table_refs(t):
                errs.append(f"table {n!r}: foreign key column {f.get('column')!r} not in the table")
            if rt not in got:
                errs.append(f"table {n!r}: foreign key to unknown table {rt!r}")
            elif f.get("ref_column") not in table_refs(got[rt]):
                errs.append(f"table {n!r}: foreign key to unknown column {f.get('ref_column')!r} of {rt!r}")
    fks = {(n, f.get("ref_table")) for n, t in got.items() for f in t.get("foreign_keys", [])}
    for r in a43.get("relationships", []):
        a_, b_ = r["from"], r["to"]
        if (a_, b_) in fks:
            continue
        linked = r["kind"] == "many_to_many" and (((b_, a_) in fks) or any(
            set(n.get("between", [])) == {a_, b_} and (n["name"], a_) in fks and (n["name"], b_) in fks for n in a43.get("new_tables", [])))
        if not linked:
            errs.append(f"relationship {a_!r} -> {b_!r} has no foreign key")
    return errs


# ---------------------------------------------------------------- (e) dialogues only
def build_prompt_e(dialogue_text):
    """(prompt, schema) of the dialogues-only prompt (e); column names are free, no ids."""
    text = INSTRUCTION_E.format(types=", ".join(TYPES), json_only=_JSON_ONLY) + dialogue_text.rstrip("\n") + "\n\nReturn the JSON object now.\n"
    fk = _obj({"column": _S, "ref_table": _S, "ref_column": _S})
    schema = _obj({
        "tables": _arr(_obj({"name": _S, **_TABLE_TEXT, "primary_key": _arr(_S),
                             "columns": _arr(_obj({"name": _S, "type": {"enum": TYPES}})), "foreign_keys": _arr(fk)})),
        "relationships": _arr(_obj({"from": _S, "to": _S, "kind": {"enum": KINDS}, "reason": _S}))})
    return text, schema


def validate_e(a):
    """Errors of a parsed (e) answer: duplicate tables / columns, bad types, primary key and foreign keys not in the tables."""
    errs, tabs = [], {}
    for t in a.get("tables", []):
        n = t.get("name")
        if n in tabs:
            errs.append(f"table {n!r} given twice")
        tabs[n] = t
    for n, t in tabs.items():
        names = [c.get("name") for c in t.get("columns", [])]
        errs += [f"table {n!r}: column {x!r} twice" for x in set(names) if names.count(x) > 1]
        errs += [f"table {n!r}: bad type {c.get('type')!r}" for c in t.get("columns", []) if c.get("type") not in TYPES]
        errs += [f"table {n!r}: primary key {k!r} not a column" for k in t.get("primary_key", []) if k not in names]
        for f in t.get("foreign_keys", []):
            if f.get("column") not in names:
                errs.append(f"table {n!r}: foreign key column {f.get('column')!r} not in the table")
            rt = tabs.get(f.get("ref_table"))
            if rt is None:
                errs.append(f"table {n!r}: foreign key to unknown table {f.get('ref_table')!r}")
            elif f.get("ref_column") not in [c.get("name") for c in rt.get("columns", [])]:
                errs.append(f"table {n!r}: foreign key to unknown column {f.get('ref_column')!r} of {f.get('ref_table')!r}")
    for i, r in enumerate(a.get("relationships", [])):
        errs += [f"relationships[{i}] unknown table {r.get(k)!r}" for k in ("from", "to") if r.get(k) not in tabs]
        if r.get("kind") not in KINDS:
            errs.append(f"relationships[{i}] bad kind {r.get('kind')!r}")
    return errs


# ---------------------------------------------------------------- placement into an existing schema
def render_schema(canonical):
    """Text of a canonical schema for the placement prompt: tables with columns (type, key marks) and the relationships."""
    out = []
    for t in canonical["tables"]:
        out.append(f"Table {t['name']}: {t.get('description', '')} One row = {t.get('row', '')}.")
        fk = {c: f"refers to {f['ref_table']}.{f['ref_columns'][i]}" for f in t["foreign_keys"] for i, c in enumerate(f["columns"])}
        for c in t["columns"]:
            marks = (["primary key"] if c["name"] in t["primary_key"] else []) + ([fk[c["name"]]] if c["name"] in fk else [])
            out.append(f"  - {c['name']} ({c['type']})" + (f" [{'; '.join(marks)}]" if marks else ""))
    rels = [f"{r['from']} -> {r['to']} ({r['kind']})" for r in canonical["relationships"]]
    out.append("Relationships (from = refers to, to = referred to): " + ("; ".join(rels) if rels else "(none)"))
    return "\n".join(out) + "\n"


def build_prompt_place(canonical, column):
    """(prompt, schema) of one placement question: `canonical` is the current schema, `column` a column dict as for 4.1
    (a `data_signal` text, when present, is shown as the signal card)."""
    names = [t["name"] for t in canonical["tables"]]
    text = (INSTRUCTION_PLACE.format(json_only=_JSON_ONLY) + render_schema(canonical) + "\nNew column:\n" + render_column(column)
            + "\n\nReturn the JSON object now.\n")
    new_table = {"anyOf": [{"type": "null"}, _obj({"name": _S, "row": _S})]}
    link = {"anyOf": [{"type": "null"}, _obj({"from": _S, "to": _S, "kind": {"enum": KINDS}})]}
    schema = _obj({"reason": _S, "option": {"enum": OPTIONS}, "target_table": {"enum": names + ["none"]}, "new_table": new_table,
                   "link": link})
    return text, schema


def validate_place(a, canonical):
    """Errors of a parsed placement answer: option needs its fields, target and link tables exist (or are the new table)."""
    names = {t["name"] for t in canonical["tables"]}
    nt, link, opt, tgt = a.get("new_table"), a.get("link"), a.get("option"), a.get("target_table")
    errs = []
    if opt not in OPTIONS:
        return [f"bad option {opt!r}"]
    if tgt != "none" and tgt not in names:
        errs.append(f"unknown target_table {tgt!r}")
    if nt is not None and (not str(nt.get("name") or "").strip() or nt["name"] in names):
        errs.append(f"new_table name {(nt or {}).get('name')!r} empty or already used")
    allnames = names | ({nt["name"]} if nt else set())
    if link is not None:
        errs += [f"link {k} {link.get(k)!r} unknown" for k in ("from", "to") if link.get(k) not in allnames]
        if link.get("from") == link.get("to"):
            errs.append("link relates a table to itself")
    if opt in ("P1", "P4") and tgt not in names:
        errs.append(f"{opt} needs an existing target_table")
    if opt in ("P3", "P5") and nt is None:
        errs.append(f"{opt} needs new_table")
    if opt == "P4" and link is None:
        errs.append("P4 needs link")
    if opt == "P2" and nt is None and tgt not in names:
        errs.append("P2 needs target_table or new_table")
    return errs
