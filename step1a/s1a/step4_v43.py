"""wf_v4.3 (diary Nov 13, U3) Step 4 for Llama-3.1-8B: small closed questions, the code does the bookkeeping.

Changes from wf_v4.2 option B extended (s1a/keyed_v42.py; frozen prompts, parsers and validators of v4.1 are reused by import):
- 4.1 in two calls. p1: "list the main things (tables)": {"tables": [short names]}, 1 to 8 names. p2: one answer per column id (keyed object, every
  column exactly once) with an enum of the p1 names plus "unused", so no new group can appear.
- 4.2 is code: the table names are the p1 names (repeats renamed with keyed_v42._unique_names); description = "The <name> table." and
  row = "one <name>" are made up by code (no call; the later calls and the scorer do not need model text for them).
- 4.3 one call per table pair (at most 28): answer none | "x -> y" (one x has many y) | "y -> x" | many_to_many. Code builds the relationships
  (from = many side) and, for many_to_many, a link table x_y (new id key, two id columns that refer to x and y).
- 4.4 one call per table: primary key (a column id of the table or "new" + a key name) and, for every table it refers to (4.3 links where it is the
  many side), the column that holds the reference (a column id of the table or "new"). Code puts every column in its p2 table, takes types from
  the Step-3 value types (step4_prompts.canon_type), renames repeated column names and a new key name that equals a column name, adds the new
  reference columns and the link tables, and writes the frozen answer shapes a41..a44, so step4_prompts.validate_* and batch_v4.assemble_chain
  (step4_sql.assemble) give the canonical schema the T7 scorers read (scripts/score_v4.score_rows).
- Every repair of an answer is counted by type in log_v43.RepairLog (repairs.json per chain under final/<chain>/ and in total).
- The prompts carry the U1 worked example (examples_v43.STEP4_EXAMPLE), the part for the call, under "Worked example (other domain):".

Answers are plain JSON (formats s43_p1, s43_p2, s43_pair, s43_key, registered in nov16_v41.PLAIN_FORMATS). Jobs are nov16_v41 jobs, so
nov16_v41.VllmBackend (Colab) and the fake model of s1a/step4_fake_v43.py run them. Stages: 1 p1, 2 p2, 3 pairs, 4 keys; each stage is built from the
responses of the earlier ones (replay). A chain stops only when its p1 or p2 answer is missing, unparsable or leaves no table; a missing or bad
pair / key answer is a repair (pair: none, key: new key, new reference column).
Seeds: as option B, seed 0 = input order, seeds 1, 2 shuffle the columns inside each entity block (step4_inputs.order_columns).
"""
import re
from itertools import combinations
from pathlib import Path

from . import batch_v4 as B
from . import examples_v43 as EX
from . import keyed_v42 as K
from . import nov16_v41 as NV
from . import step4_prompts as SP
from . import step4_sql as SQL
from .log_v43 import RepairLog

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("a", "c1", "a_llama43")             # priority order
SETS, SEEDS = ("dev50", "dev50b"), (0, 1, 2)
A_LLAMA43_DIR = ROOT / "results" / "wf_v43" / "u2" / "a_llama43"
OUT = ROOT / "results" / "wf_v43" / "u4"
MAX_TABLES = 8
MAX_PAIRS = MAX_TABLES * (MAX_TABLES - 1) // 2
FORMATS = ("s43_p1", "s43_p2", "s43_pair", "s43_key")
MAX_TOKENS = {"s43_p1": 300, "s43_p2": 1500, "s43_pair": 100, "s43_key": 400}
STEP_FORMAT = {1: "s43_p1", 2: "s43_p2", 3: "s43_pair", 4: "s43_key"}
UNUSED = "unused"
NEW = SP.NEW
NAME_PATTERN = "^[a-z][a-z0-9_]{0,29}$"
KEY_NAME_CAP = 40
NV.PLAIN_FORMATS = tuple(dict.fromkeys(NV.PLAIN_FORMATS + FORMATS))   # nov16_v41.parse_answer reads these as plain JSON

_JSON_ONLY = SP._JSON_ONLY
_EXAMPLE_HEAD = "\nWorked example (other domain):\n"


# ---------------------------------------------------------------- worked example parts
def example_part(*sections):
    """The U1 Step 4 example reduced to the "Columns:" line plus the named sections ("Pass 1", "Pass 2", "Links", "Keys"; a section starts
    at the line that begins with its name and ends before the next section line). Falls back to the whole example when a name is missing."""
    lines, heads = EX.STEP4_EXAMPLE.splitlines(), ("Columns:", "Pass 1", "Pass 2", "Links", "Keys")
    blocks, cur = {}, None
    for ln in lines:
        h = next((x for x in heads if ln.startswith(x)), None)
        if h:
            cur = h
            blocks[cur] = []
        if cur:
            blocks[cur].append(ln)
    want = ("Columns:",) + sections
    if any(w not in blocks for w in want):
        return EX.STEP4_EXAMPLE
    return "\n".join("\n".join(blocks[w]) for w in want)


def _example(*sections):
    return _EXAMPLE_HEAD + example_part(*sections) + "\n"


# ---------------------------------------------------------------- schemas
def _obj(props, required=None):
    return {"type": "object", "properties": props, "required": list(props) if required is None else required, "additionalProperties": False}


def p1_schema():
    return _obj({"tables": {"type": "array", "items": {"type": "string", "pattern": NAME_PATTERN}, "minItems": 1, "maxItems": MAX_TABLES}})


def p2_schema(ids, names):
    """One required key per column id, value an enum of the p1 names plus "unused" (no other key, so no column twice or missing)."""
    return _obj({i: {"enum": list(names) + [UNUSED]} for i in ids})


def pair_options(x, y):
    return ["none", f"{x} -> {y}", f"{y} -> {x}", "many_to_many"]


def pair_schema(x, y):
    return _obj({"link": {"enum": pair_options(x, y)}})


def key_schema(col_ids, refs):
    props = {"primary_key": {"enum": list(col_ids) + [NEW]}, "new_id_name": {"type": "string", "maxLength": KEY_NAME_CAP}}
    if refs:
        props["foreign_keys"] = _obj({r: {"enum": list(col_ids) + [NEW]} for r in refs})
    return _obj(props)


# ---------------------------------------------------------------- prompts
INSTRUCTION_P1 = """\
Below are the columns found by analysing a corpus of dialogues. Each column is a kind of information that people give in the dialogues, with a
description, the type of its values, a few example values (each with a short piece of text around it) and counts. The columns were found under
{n_ent} headings; a heading may be wrong.{notes}
Task: list the main things (tables) that a relational database for these columns needs. Give each table a short lower-case name (words joined by
"_"). Give between 1 and {cap} names, no two the same. A table holds several columns about the same thing or event; do not make one table per column.
{json_only} Shape (the names here are made up): {{"tables": ["name_1", "name_2"]}}
{example}
Columns ({n_cols}):
"""

INSTRUCTION_P2 = """\
Below are columns found by analysing a corpus of dialogues (a kind of information, with a description, the type of its values, example values and
counts) and the list of tables of a database design. Put every column into exactly one of the listed tables, or into "unused" when a database
would not store it. Use only the listed names; do not add tables. Use "unused" only when the column clearly holds nothing a database would
store.{notes}
{json_only} Shape (the ids and names here are made up): {{"x:1": "table_a", "x:2": "table_b", "x:3": "unused"}}
Every column id must appear once.
{example}
Tables: {tables}

Columns ({n_cols}):
"""

INSTRUCTION_PAIR = """\
Below are two tables of a relational database design, each with its columns. Decide whether {x} and {y} are linked, and which way. Answer with
exactly one of:
- "none": no direct link (they meet at most through a third table)
- "{x} -> {y}": one {x} row has many {y} rows (each {y} row refers to one {x} row)
- "{y} -> {x}": one {y} row has many {x} rows (each {x} row refers to one {y} row)
- "many_to_many": a {x} row can go with many {y} rows and the other way round
Do not invent a link that the columns do not support.
{json_only} Shape: {{"link": "none"}}
{example}
"""

INSTRUCTION_KEY = """\
Below is one table of a relational database design, with its columns.
Choose its primary key: the id of the one column whose value is different for every row, or "new" when no column can do this; then give the name
of the new key column in new_id_name (use "" when the primary key is an existing column).{fk_text}{note}
{json_only} Shape (the names and ids here are made up): {shape}
{example}
"""
_FK_TEXT = ("\nThis table refers to the other tables listed below. For each of them, choose the id of the column of this table that holds the "
            "reference (its value points to a row of that table), or \"new\" when no column does; a new reference column is then added. "
            "Tables referred to: {refs}.")


def _signals_note(cols):
    return SP.DATA_SIGNALS_NOTE if any(c.get("data_signal") for c in cols) else ""


def build_p1(cols):
    """(prompt, schema) of pass 1: the main things (tables)."""
    ents = list(dict.fromkeys(SP._entity(c) for c in cols))
    text = (INSTRUCTION_P1.format(n_ent=len(ents), notes=_signals_note(cols) + SP.V41_NOTE_41, cap=MAX_TABLES, json_only=_JSON_ONLY,
                                  example=_example("Pass 1"), n_cols=len(cols))
            + SP.render_columns(cols) + "\nReturn the JSON object now.\n")
    return text, p1_schema()


def build_p2(cols, names):
    """(prompt, schema) of pass 2: every column to one of `names` or "unused"."""
    text = (INSTRUCTION_P2.format(notes=_signals_note(cols), json_only=_JSON_ONLY, example=_example("Pass 1", "Pass 2"),
                                  tables=", ".join(names), n_cols=len(cols))
            + SP.render_columns(cols) + "\nReturn the JSON object now.\n")
    return text, p2_schema([c["id"] for c in cols], names)


def _render_table(name, col_dicts):
    return f"Table {name} (one row = one {name}), {len(col_dicts)} columns:\n" + "\n".join(SP.render_column(c, 2) for c in col_dicts) + "\n"


def build_pair(x, y, cols_x, cols_y):
    """(prompt, schema) of the link question for tables x and y (cols_* = column dicts of each table)."""
    text = (INSTRUCTION_PAIR.format(x=x, y=y, json_only=_JSON_ONLY, example=_example("Links")) + "\n" + _render_table(x, cols_x)
            + "\n" + _render_table(y, cols_y) + "\nReturn the JSON object now.\n")
    return text, pair_schema(x, y)


def build_key(name, col_dicts, refs):
    """(prompt, schema) of the key question of one table; refs = names of the tables it refers to (many side of a link)."""
    ids = [c["id"] for c in col_dicts]
    fk_text = _FK_TEXT.format(refs=", ".join(f"{r} (one {r} row has many rows of {name})" for r in refs)) if refs else ""
    shape = ('{"primary_key": "x:3", "new_id_name": "", "foreign_keys": {"table_b": "new"}}' if refs
             else '{"primary_key": "new", "new_id_name": "name id"}')
    text = (INSTRUCTION_KEY.format(fk_text=fk_text, note=SP.V41_NOTE_44, json_only=_JSON_ONLY, shape=shape, example=_example("Keys"))
            + "\n" + _render_table(name, col_dicts) + "\nReturn the JSON object now.\n")
    return text, key_schema(ids, refs)


# ---------------------------------------------------------------- answers -> state (every repair counted)
def _slug(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")


def p1_names(parsed, log, where=""):
    """Table names of a p1 answer: slugged, empty dropped, repeats renamed (keyed_v42._unique_names), at most MAX_TABLES."""
    raw = parsed.get("tables") if isinstance(parsed, dict) else None
    names = []
    for x in raw if isinstance(raw, list) else []:
        n = _slug(x)
        if not n:
            log.add("p1_empty_name", where, repr(x))
        else:
            if n != str(x):
                log.add("p1_name_normalised", where, f"{x!r} -> {n!r}")
            names.append(n)
    rows = K._unique_names([{"name": n, "group": str(i + 1)} for i, n in enumerate(names)])
    for old, r in zip(names, rows):
        if r["name"] != old:
            log.add("p1_name_repeat", where, f"{old!r} -> {r['name']!r}")
    names = [r["name"] for r in rows]
    if len(names) > MAX_TABLES:
        log.add("p1_over_cap", where, f"{len(names)} names, kept {MAX_TABLES}")
        names = names[:MAX_TABLES]
    return names


def p2_assign(parsed, cols, names, log, where=""):
    """({column id: table name or None}, names without an empty table). None = unused. Missing ids, unknown ids and names outside the
    list go to unused (counted)."""
    got = parsed if isinstance(parsed, dict) else {}
    ids = [c["id"] for c in cols]
    for k in got:
        if k not in ids:
            log.add("p2_unknown_column", where, repr(k))
    lookup = {n.lower(): n for n in names}
    assign = {}
    for i in ids:
        v = got.get(i)
        s = str(v).strip().lower()
        if v is None:
            log.add("p2_missing_column", where, i)
            assign[i] = None
        elif s == UNUSED:
            assign[i] = None
        elif s in lookup:
            assign[i] = lookup[s]
        else:
            log.add("p2_bad_name", where, f"{i}: {v!r}")
            assign[i] = None
    used = set(assign.values())
    kept = [n for n in names if n in used]
    for n in names:
        if n not in used:
            log.add("p2_empty_table", where, n)
    return assign, kept


def pair_kind(parsed, x, y, log, where=""):
    """"none", "xy" (one x has many y), "yx" or "mm" from a pair answer; a bad answer is "none" (counted)."""
    v = parsed.get("link") if isinstance(parsed, dict) else None
    key = lambda s: "".join(str(s).lower().split())     # noqa: E731
    for opt, kind in zip(pair_options(x, y), ("none", "xy", "yx", "mm")):
        if v is not None and key(v) == key(opt):
            return kind
    log.add("pair_bad_answer", where, repr(v))
    return "none"


def _uniq(name, taken):
    """name, or "<name> 2", "<name> 3", ... when its lower case is in `taken` (a set of lower-case names); adds the result to `taken`."""
    base, k, out = name, 2, name
    while out.strip().lower() in taken:
        out, k = f"{base} {k}", k + 1
    taken.add(out.strip().lower())
    return out


def _col_names(ids, cb, log, where):
    """{id: column name} of one table; a repeated name (case-insensitive) becomes "<name> (<id>)" (counted)."""
    taken, out = set(), {}
    for i in ids:
        nm = cb[i]["name"]
        if nm.strip().lower() in taken:
            log.add("col_name_dup", where, f"{nm!r} {i}")
            nm = f"{nm} ({i})"
        taken.add(nm.strip().lower())
        out[i] = nm
    return out


def build_answers(st, key_answers, log, where=""):
    """The frozen answers (a41, a42, a43, a44) of a chain from its state: st has cols, names, assign, links [{one, many, kind} | {a, b, kind}];
    key_answers = {table index: parsed key answer or None}. Key and reference-column repairs are counted in `log`."""
    cols, names, assign = st["cols"], st["names"], st["assign"]
    cb = {c["id"]: c for c in cols}
    group = {n: [c["id"] for c in cols if assign[c["id"]] == n] for n in names}
    a41 = {"groups": [{"group": f"G{i + 1}", "columns": group[n], "note": ""} for i, n in enumerate(names)],
           "unused": [{"column": c["id"], "reason": "not assigned to a table"} for c in cols if assign[c["id"]] is None],
           "duplicate_flags": []}
    a42 = {"tables": [{"group": f"G{i + 1}", "name": n, "description": f"The {n} table.", "row": f"one {n}"} for i, n in enumerate(names)]}
    taken_tables, rels, new_tables = {n.lower() for n in names}, [], []
    for ln in st["links"]:
        if ln["kind"] == "one_to_many":
            rels.append({"from": ln["many"], "to": ln["one"], "kind": "one_to_many", "reason": ""})
        else:
            x, y = ln["a"], ln["b"]
            name = _uniq(f"{x}_{y}", taken_tables).replace(" ", "_")
            ln["link_table"] = name
            new_tables.append({"name": name, "description": f"Links {x} and {y}.", "row": f"one {x} and {y} pair", "between": [x, y]})
            rels += [{"from": x, "to": y, "kind": "many_to_many", "reason": ""},
                     {"from": name, "to": x, "kind": "one_to_many", "reason": ""}, {"from": name, "to": y, "kind": "one_to_many", "reason": ""}]
    a43 = {"relationships": rels, "new_tables": new_tables}

    # primary keys first (a reference needs the key of the table it refers to)
    info = {}
    for i, n in enumerate(names):
        cn = _col_names(group[n], cb, log, f"{where}:{n}")
        ans = key_answers.get(i)
        pk = ans.get("primary_key") if isinstance(ans, dict) else None
        if ans is None:
            log.add("key_no_answer", f"{where}:{n}")
        if pk in group[n]:
            info[n] = {"cn": cn, "pk": pk, "new_name": None}
            continue
        if ans is not None and pk != NEW:
            log.add("key_invalid", f"{where}:{n}", repr(pk))
        want = str((ans or {}).get("new_id_name") or "").strip()
        if not want:
            log.add("key_name_empty", f"{where}:{n}")
            want = f"{n} id"
        used = {v.strip().lower() for v in cn.values()}
        name = want
        if want.lower() in used:
            name = _uniq(f"{want} key", used)
            log.add("key_name_renamed", f"{where}:{n}", f"{want!r} -> {name!r}")
        info[n] = {"cn": cn, "pk": NEW, "new_name": name}

    def pk_ref(n):
        return info[n]["pk"] if info[n]["pk"] != NEW else f"new:{info[n]['new_name']}"

    tables = []
    for i, n in enumerate(names):
        inf = info[n]
        listed = [{"column": c, "name": inf["cn"][c], "type": SP.canon_type(cb[c].get("value_type"))} for c in group[n]]
        taken = {v.strip().lower() for v in inf["cn"].values()} | ({inf["new_name"].strip().lower()} if inf["new_name"] else set())
        fks, used_cols = [], set()
        ans = key_answers.get(i)
        got_fk = ans.get("foreign_keys") if isinstance(ans, dict) and isinstance(ans.get("foreign_keys"), dict) else {}
        for ln in st["links"]:
            if ln["kind"] != "one_to_many" or ln["many"] != n:
                continue
            ref = ln["one"]
            choice = got_fk.get(ref)
            if choice is None:
                log.add("fk_no_answer", f"{where}:{n}", ref)
            if choice in group[n] and choice not in used_cols:
                used_cols.add(choice)
                fks.append({"column": choice, "ref_table": ref, "ref_column": pk_ref(ref)})
                continue
            if choice is not None and choice != NEW:
                log.add("fk_col_dup" if choice in group[n] else "fk_invalid", f"{where}:{n}", f"{ref}: {choice!r}")
            nm = _uniq(f"{ref} id", taken)
            if nm != f"{ref} id":
                log.add("fk_name_renamed", f"{where}:{n}", repr(nm))
            listed.append({"column": f"new:{nm}", "name": nm, "type": "id"})
            fks.append({"column": f"new:{nm}", "ref_table": ref, "ref_column": pk_ref(ref)})
        tables.append({"name": n, "primary_key": inf["pk"], "new_id_name": inf["new_name"] or "", "columns": listed, "foreign_keys": fks})
    for ln in st["links"]:
        if ln["kind"] != "many_to_many":
            continue
        x, y, name = ln["a"], ln["b"], ln["link_table"]
        taken = set()
        key, cx, cy = _uniq(f"{name} id", taken), _uniq(f"{x} id", taken), _uniq(f"{y} id", taken)
        tables.append({"name": name, "primary_key": NEW, "new_id_name": key,
                       "columns": [{"column": f"new:{cx}", "name": cx, "type": "id"}, {"column": f"new:{cy}", "name": cy, "type": "id"}],
                       "foreign_keys": [{"column": f"new:{cx}", "ref_table": x, "ref_column": pk_ref(x)},
                                        {"column": f"new:{cy}", "ref_table": y, "ref_column": pk_ref(y)}]})
    return a41, a42, a43, {"tables": tables}


# ---------------------------------------------------------------- replay (state from the responses)
def _answer(out, name):
    """(parsed, None) of a job's last response row, or (None, why)."""
    row = B.last_row(Path(out) / "responses" / f"{name}.jsonl")
    if row is None:
        return None, "no response"
    if row["errors"]:
        return None, f"parse errors {row['errors'][:2]}"
    return row["parsed"], None


def table_cols(st, name):
    return [c for c in st["cols"] if st["assign"][c["id"]] == name]


def key_refs(st, i):
    """Names of the tables table i refers to (the one sides of the one_to_many links where it is the many side)."""
    n = st["names"][i]
    return [ln["one"] for ln in st["links"] if ln["kind"] == "one_to_many" and ln["many"] == n]


def pairs_of(st):
    return list(combinations(range(len(st["names"])), 2))


def replay(out, chain, upto, root=ROOT):
    """(state, error or None, RepairLog) of a chain after calls 1..upto (1 p1, 2 p2, 3 pairs, 4 keys; 0 = columns only). The state has cols,
    p1_names, names, assign, links, ans (a41..a44 and the canonical schema, only when upto >= 4)."""
    cid, log = chain["id"], RepairLog()
    st = {"cols": B.chain_columns(chain, root)}
    if upto < 1:
        return st, None, log
    parsed, why = _answer(out, f"{cid}_p1")
    if why:
        return st, f"p1: {why}", log
    st["p1_names"] = p1_names(parsed, log, cid)
    if not st["p1_names"]:
        return st, "p1: no table name", log
    if upto < 2:
        return st, None, log
    parsed, why = _answer(out, f"{cid}_p2")
    if why:
        return st, f"p2: {why}", log
    st["assign"], st["names"] = p2_assign(parsed, st["cols"], st["p1_names"], log, cid)
    if not st["names"]:
        return st, "p2: no column assigned to a table", log
    st["links"] = []
    if upto < 3:
        return st, None, log
    for i, j in pairs_of(st):
        x, y = st["names"][i], st["names"][j]
        parsed, why = _answer(out, f"{cid}_r{i}_{j}")
        if why:
            log.add("pair_no_answer", f"{cid}:{x}/{y}", why)
            continue
        kind = pair_kind(parsed, x, y, log, f"{cid}:{x}/{y}")
        if kind == "xy":
            st["links"].append({"one": x, "many": y, "kind": "one_to_many"})
        elif kind == "yx":
            st["links"].append({"one": y, "many": x, "kind": "one_to_many"})
        elif kind == "mm":
            st["links"].append({"a": x, "b": y, "kind": "many_to_many"})
    if upto < 4:
        return st, None, log
    keys = {}
    for i, n in enumerate(st["names"]):
        parsed, why = _answer(out, f"{cid}_k{i}")
        keys[i] = parsed if not why and isinstance(parsed, dict) else None
        if why and why != "no response":
            log.add("key_parse_error", f"{cid}:{n}", why)
    a41, a42, a43, a44 = build_answers(st, keys, log, cid)
    errs = (SP.validate_41(a41, st["cols"]) + SP.validate_42(a42, a41) + SP.validate_43(a43, a41, a42)
            + SP.validate_44(a44, a41, a42, a43, st["cols"], strict=True))
    st["ans"] = {"41": a41, "42": a42, "43": a43, "44": a44}
    if errs:
        return st, f"assembly: {len(errs)} validation errors, e.g. {errs[:2]}", log
    return st, None, log


# ---------------------------------------------------------------- stages
def _emit(jobs, name, fmt, text, schema, chain, step, **extra):
    """B.Jobs.emit knows the v4 families only: emit with one of them, then set this module's format and token cap."""
    jobs.emit(name, "s4_41", text, schema, chain["id"], chain["set"], ent=chain["input"], chain=chain["id"], step=step, **extra)
    jobs.jobs[-1].update(family=fmt, format=fmt, max_tokens=MAX_TOKENS[fmt])


def build_stage(out, k, chains, root=ROOT):
    """Write the prompts of stage k (1 p1, 2 p2, 3 pairs, 4 keys) of `chains` from the responses of the earlier stages; returns the job dicts
    (chains that stopped are skipped) and writes <out>/manifests/<input>_stage<k>.json and chain_status_stage<k>.json."""
    out = Path(out)
    jobs, status = B.Jobs(out, k), []
    for ch in chains:
        st, err, _ = replay(out, ch, k - 1, root)
        status.append({"chain": ch["id"], "ok": err is None, "reached": k - 1 if err is None else None, "error": err})
        if err:
            continue
        cid = ch["id"]
        if k == 1:
            text, schema = build_p1(st["cols"])
            _emit(jobs, f"{cid}_p1", "s43_p1", text, schema, ch, k, n_columns=len(st["cols"]))
        elif k == 2:
            text, schema = build_p2(st["cols"], st["p1_names"])
            _emit(jobs, f"{cid}_p2", "s43_p2", text, schema, ch, k, n_columns=len(st["cols"]))
        elif k == 3:
            for i, j in pairs_of(st):
                x, y = st["names"][i], st["names"][j]
                text, schema = build_pair(x, y, table_cols(st, x), table_cols(st, y))
                _emit(jobs, f"{cid}_r{i}_{j}", "s43_pair", text, schema, ch, k, pair=[x, y])
        elif k == 4:
            for i, n in enumerate(st["names"]):
                text, schema = build_key(n, table_cols(st, n), key_refs(st, i))
                _emit(jobs, f"{cid}_k{i}", "s43_key", text, schema, ch, k, table=n)
        else:
            raise ValueError(f"stage {k}: only 1 to 4")
    inp = chains[0]["input"] if chains else "none"
    B.write_json(out / "manifests" / f"{inp}_stage{k}.json", {"stage": k, "jobs": jobs.jobs})
    B.write_json(out / f"chain_status_stage{k}_{inp}.json", status)
    return jobs.jobs


# ---------------------------------------------------------------- chains, run, assembly
def columns_path(inp, set_name, a_llama43_dir=A_LLAMA43_DIR, root=ROOT):
    """Column file of an input and set (Path or None when it does not exist). a / c1: results/wf_v4/inputs/<set>/<input>.columns.json.
    a_llama43 (Step 3 v4.3 columns, the format of input a): the first existing of <dir>/<set>/a_llama43.columns.json, <dir>/<set>/a.columns.json,
    <dir>/<set>.columns.json, <dir>/<set>/columns.json."""
    d = Path(a_llama43_dir)
    cands = ([d / set_name / "a_llama43.columns.json", d / set_name / "a.columns.json", d / f"{set_name}.columns.json", d / set_name / "columns.json"]
             if inp == "a_llama43" else [Path(root) / B.INPUT_DIR / set_name / f"{inp}.columns.json"])
    return next((p for p in cands if p.exists()), None)


def make_chains(inputs=INPUTS, sets=SETS, seeds=SEEDS, a_llama43_dir=A_LLAMA43_DIR, root=ROOT, log=print):
    """Chain dicts (batch_v4 format) of the inputs in order; a missing column file skips that input and set with a message."""
    out = []
    for inp in inputs:
        for s in sets:
            p = columns_path(inp, s, a_llama43_dir, root)
            if p is None:
                log(f"skip input {inp} {s}: column file not found" + (f" under {a_llama43_dir}" if inp == "a_llama43" else ""))
                continue
            try:
                rel = p.resolve().relative_to(Path(root).resolve()).as_posix()
            except ValueError:
                rel = str(p.resolve())
            out += [{"id": B.chain_id(inp, s, d), "kind": "main", "input": inp, "set": s, "seed": d, "exclude": [], "prompt_version": "v43",
                     "columns_file": rel} for d in seeds]
    return out


def assemble_all(out, chains, root=ROOT):
    """<out>/final/<chain>/{canonical.json, schema.sql, operations.json, repairs.json} per finished chain, final/status.json (every chain:
    ok, tables, calls, repairs by type, error) and <out>/repairs.json (total + per chain). Returns the status rows."""
    out, status, total, per_chain = Path(out), [], RepairLog(), {}
    final = out / "final"
    for ch in chains:
        st, err, log = replay(out, ch, 4, root)
        total.merge(log)
        per_chain[ch["id"]] = log.to_dict()["counts"]
        row = {"run": ch["id"], "kind": "main", "input": ch["input"], "set": ch["set"], "seed": ch["seed"], "ok": err is None,
               "repairs": log.total(), "repair_kinds": log.to_dict()["counts"], "error": err,
               "tables": len(st["ans"]["44"]["tables"]) if err is None else None}
        if err is None:
            c = B.assemble_chain(st["ans"], st["cols"])
            B.write_json(final / ch["id"] / "canonical.json", c)
            B.write(final / ch["id"] / "schema.sql", SQL.to_sql(c))
            B.write_json(final / ch["id"] / "operations.json", SQL.to_operations(c))
            log.save(final / ch["id"] / "repairs.json")
        status.append(row)
    B.write_json(final / "status.json", status)
    B.write_json(out / "repairs.json", {**total.to_dict(), "per_chain": per_chain})
    return status


def run(out, backend, inputs=INPUTS, sets=SETS, seeds=SEEDS, a_llama43_dir=A_LLAMA43_DIR, root=ROOT, log=print):
    """All stages (p1, p2, pairs, keys) of the chains of `inputs`, one input after the other (priority order), then the assembly. backend.run(out,
    jobs) answers a stage (nov16_v41.VllmBackend on Colab, step4_fake_v43.FakeV43 on the laptop; a rerun skips answered jobs). Returns
    {"chains", "inputs": {input: {stage k: backend info}}, "finished": "ok/n"}; also written to <out>/run_info.json."""
    out = Path(out)
    chains = make_chains(inputs, sets, seeds, a_llama43_dir, root, log)
    B.write_json(out / "chains.json", chains)
    info = {"chains": len(chains), "inputs": {}}
    for inp in inputs:
        cs = [c for c in chains if c["input"] == inp]
        if not cs:
            info["inputs"][inp] = "skipped: no column file"
            continue
        info["inputs"][inp] = {}
        for k in (1, 2, 3, 4):
            jobs = build_stage(out, k, cs, root)
            info["inputs"][inp][f"stage{k}"] = backend.run(out, jobs) if jobs else {"jobs": 0, "run": 0, "parse_errors": 0}
            log(f"{inp} stage {k}: {len(jobs)} jobs")
    status = assemble_all(out, chains, root)
    info["finished"] = f"{sum(r['ok'] for r in status)}/{len(status)}"
    B.write_json(out / "run_info.json", info)
    return info
