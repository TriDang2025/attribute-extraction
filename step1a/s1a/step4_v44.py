"""wf_v4.4 (diary Nov 14, T5) Step 4 for Llama-3.1-8B: the v4.3 chain (s1a/step4_v43.py, imported, not copied) plus five changes, each with a switch in
config/wf_v44_step4.json ("switches"). With every switch off the job set, the prompts and the answer formats are those of v4.3.

1 entity_hint   code puts each column in the table of its Step 1a entity (heading = entity name). Pass 1 only lists further tables (0 to 8 - entities,
                names equal to an entity are dropped); pass 2 asks per column "keep", "move to <table>" or the third option (guided enum, format s44_p2).
2 other_choice  the third option of pass 2 is "other" instead of "unused": those columns are kept in one JSON column "rest" (type text) of their
                host table = the table of their entity, else the table with most columns (ties: first). One rest column per host table, named "rest" (a
                repeated name gets " 2"). The columns stay in a41.unused with the reason REST_REASON, so the scorer reads them as unused and
                step4_v44.rest_gt_columns counts the GT columns held there.
3 key_candidates  per table, code lists the id-like columns (is_idlike); the key call is a choice of one of them or "none" (new id column, as v4.3).
                A table with no candidate and no reference to ask about gets no key call: new key "<table> id" made by code (no repair).
4 code_links    code proposes a link between two tables when they hold id-like columns with the same name or overlapping values (link_evidence);
                one call per proposed pair, answer "x -> y" | "y -> x" | "none" (no many_to_many). Not proposed = none, no call.
5 vote          per (input, set), one more chain "<input>_<set>_vote": its pass-2 result is the vote of the seed chains' pass-2 results, then pairs and
                keys are asked once for it. A column goes to the table most seeds chose ("other" and "unused" are choices of their own); a tie goes to
                the choice of the earliest seed among the tied ones. Table names across seeds: equal names are one table, else the best Jaccard of the
                column sets >= vote_table_jaccard (one to one, against the first finished seed); an unmatched table is a table of its own (name made
                unique). The voted chain's schema is scored next to the single-seed schemas.

Thresholds (config "thresholds"): see the notes there. Values per column (distinct values, mentions) come from the mention ids of the input
(column_values): input a = handover, c1 = gold labels, a_llama43 / a_llama44 = <step 3 dir>/scores/final_columns.json (or a `mention_ids` field of the
columns). They are saved per input and set in <out>/values/<input>_<set>.json. The same mention ids give the scoring map <out>/score_map/<input>
(step4_gt.map_handover format): the v4.3 scorer maps columns through the Qwen handover ids, which is right for input a only.

Chains are batch_v4 chain dicts with `switches`, `thresholds`, `values_file` and, for the vote chain, kind "vote" and `members` (the seed chains).
Stages: 1 p1 (seed chains), 2 p2 (seed chains), 3 pairs (all chains), 4 keys (all chains); each is built from the earlier responses (replay).
"""
import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

from . import batch_v4 as B
from . import nov16_v41 as NV
from . import step4_gt as G
from . import step4_inputs as I
from . import step4_prompts as SP
from . import step4_score as S
from . import step4_score_v43 as SC43
from . import step4_sql as SQL
from . import step4_v43 as V
from .log_v44 import CALL_FIELDS, RepairLog, call_rows, call_totals

ROOT = V.ROOT
CONFIG = ROOT / "config" / "wf_v44_step4.json"
SWITCHES = ("entity_hint", "other_choice", "key_candidates", "code_links", "vote")
INPUTS = ("a_llama44", "c1")
SETS, SEEDS = V.SETS, V.SEEDS
STEP3_DIRS = {"a_llama43": V.A_LLAMA43_DIR, "a_llama44": ROOT / "results" / "wf_v44" / "t4" / "a_llama44"}   # the dirs of <set>/a.columns.json
OUT_T6 = ROOT / "results" / "wf_v44" / "t6"
FORMATS = ("s44_p1", "s44_p2", "s44_pair", "s44_key")
MAX_TOKENS = {**V.MAX_TOKENS, "s44_p1": 200, "s44_p2": 1500, "s44_pair": 100, "s44_key": 400}
NV.PLAIN_FORMATS = tuple(dict.fromkeys(NV.PLAIN_FORMATS + FORMATS))
KEEP, MOVE, OTHER, NONE, REST = "keep", "move to ", "other", "none", "rest"
REST_REASON = "kept in the rest column of"
NON_KEY_TYPES = {"time", "day", "date", "duration", "price", "decimal", "boolean"}    # measurements, not identifiers
_HEAD = V._EXAMPLE_HEAD
_JSON_ONLY = V._JSON_ONLY


# ---------------------------------------------------------------- config
def load_config(path=CONFIG):
    """{"switches": {...}, "thresholds": {...}} from the config file (every switch key must be there)."""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in SWITCHES if k not in cfg["switches"]]
    if missing:
        raise ValueError(f"{path}: missing switches {missing}")
    return {"switches": dict(cfg["switches"]), "thresholds": dict(cfg["thresholds"])}


def with_switches(cfg, off=(), **kw):
    """Copy of cfg with the switches in `off` set to False and the keyword switches set (e.g. all_off = with_switches(cfg, off=SWITCHES))."""
    sw = {**cfg["switches"], **kw, **{k: False for k in off}}
    unknown = set(sw) - set(SWITCHES)
    if unknown:
        raise ValueError(f"unknown switches {sorted(unknown)}")
    return {"switches": sw, "thresholds": dict(cfg["thresholds"])}


# ---------------------------------------------------------------- values per column (mention ids of the input)
def own_table(c):
    """Table of a column by its Step 1a entity (heading), as a slug."""
    return V._slug(SP._entity(c))


def entity_tables(cols):
    return list(dict.fromkeys(own_table(c) for c in cols))


def mention_ids_of(inp, set_name, columns_file, cols, root=ROOT):
    """{column id: [mention ids]} of an input, or None when the data is not there. Order: a `mention_ids` field of every column; c1 / c2: the
    mentions whose gold label is the column's `gt`; a: the handover; a_llama4x: <dir of the columns>/../../scores/final_columns.json."""
    if cols and all("mention_ids" in c for c in cols):
        return {c["id"]: list(c["mention_ids"]) for c in cols}
    if inp in ("c1", "c2"):
        levels = G.read_gt_levels(Path(root) / I.GT_LEVELS[set_name])
        labels = {i: set(G.split_labels(v)) for i, v in levels.items()}
        return {c["id"]: [i for i in levels.index if c["gt"] in labels.get(i, ())] for c in cols}
    if inp == "a":
        ho = I.load_handover(set_name, root)
        return {f"{e}:{c['id']}": c["mention_ids"] for e in I.ENTITIES for c in ho[e]["columns"]}
    f = Path(columns_file).parents[2] / "scores" / "final_columns.json"
    if not f.exists():
        return None
    final = B.read_json(f)[set_name]
    return {f"{e}:{c['cid']}": c["mention_ids"] for e, cs in final.items() for c in cs}


def column_values(inp, set_name, columns_file, cols, root=ROOT):
    """{column id: {"n": mentions, "values": sorted distinct normalised values}} for the columns of an input, or None when mention ids are missing."""
    ids = mention_ids_of(inp, set_name, columns_file, cols, root)
    if ids is None:
        return None
    m = I.load_mentions(set_name, root)
    out = {}
    for c in cols:
        v = m.loc[[i for i in ids.get(c["id"], []) if i in m.index]]["norm_value"].tolist()
        out[c["id"]] = {"n": len(v), "values": sorted(set(v))}
    return out


def load_stats(out, chain):
    p = chain.get("values_file")
    return B.read_json(Path(out) / p) if p else {}


def is_idlike(c, stat, th):
    """Id-like column: enough mentions, (almost) all values different, and a value type that is not a measurement (NON_KEY_TYPES)."""
    if not stat or stat["n"] < th["key_min_mentions"] or SP.canon_type(c.get("value_type")) in NON_KEY_TYPES:
        return False
    return len(stat["values"]) / stat["n"] >= th["key_distinct_share"]


def key_candidates(cols, stats, th):
    """Ids of the id-like columns of a table (input order)."""
    return [c["id"] for c in cols if is_idlike(c, stats.get(c["id"]), th)]


def link_evidence(x, y, cols_x, cols_y, stats, th):
    """Reasons to ask about the pair x, y: id-like columns (one in each table) with the same name, or sharing values (shared distinct values >=
    link_min_shared_values and >= link_overlap_share of the smaller value set). [] = no proposal."""
    ev = []
    ix = [c for c in cols_x if is_idlike(c, stats.get(c["id"]), th)]
    iy = [c for c in cols_y if is_idlike(c, stats.get(c["id"]), th)]
    for cx in ix:
        for cy in iy:
            vx, vy = set(stats[cx["id"]]["values"]), set(stats[cy["id"]]["values"])
            shared = len(vx & vy)
            if V._slug(cx["name"]) == V._slug(cy["name"]):
                ev.append(f'"{cx["name"]}" in {x} and "{cy["name"]}" in {y} have the same name')
            elif shared >= th["link_min_shared_values"] and shared / min(len(vx), len(vy)) >= th["link_overlap_share"]:
                ev.append(f'"{cx["name"]}" in {x} and "{cy["name"]}" in {y} share {shared} values')
    return ev


# ---------------------------------------------------------------- schemas
def p1_schema_h(cap):
    return V._obj({"tables": {"type": "array", "items": {"type": "string", "pattern": V.NAME_PATTERN}, "minItems": 0, "maxItems": cap}})


def p2_options(c, names, third):
    """Guided enum of one column in hint mode: keep, move to each other table, the third option."""
    return [KEEP] + [MOVE + t for t in names if t != own_table(c)] + [third]


def p2_schema_h(cols, names, third):
    return V._obj({c["id"]: {"enum": p2_options(c, names, third)} for c in cols})


def p2_schema_plain(ids, names, third):
    return V._obj({i: {"enum": list(names) + [third]} for i in ids})


def pair_options3(x, y):
    return ["none", f"{x} -> {y}", f"{y} -> {x}"]


def pair_schema3(x, y):
    return V._obj({"link": {"enum": pair_options3(x, y)}})


def key_schema_c(cands, col_ids, refs):
    """Key schema with candidates: primary_key = a candidate id or "none"; references choose among all column ids or "new" as in v4.3."""
    props = {"primary_key": {"enum": list(cands) + [NONE]}, "new_id_name": {"type": "string", "maxLength": V.KEY_NAME_CAP}}
    if refs:
        props["foreign_keys"] = V._obj({r: {"enum": list(col_ids) + [V.NEW]} for r in refs})
    return V._obj(props)


# ---------------------------------------------------------------- prompts (v4.3 builders are used unchanged when a switch is off)
INSTRUCTION_P1H = """\
Below are the columns found by analysing a corpus of dialogues. Each column is a kind of information that people give in the dialogues, with a
description, the type of its values, a few example values (each with a short piece of text around it) and counts. The columns were found under
{n_ent} headings; a heading may be wrong.{notes}
Each heading already is a table of a relational database: {ents}.
Task: list further tables that this database needs, for a part of a heading that is a separate thing or event (not for a single column). Give each
a short lower-case name (words joined by "_"), different from the names above. Give between 0 and {cap} names; an empty list is fine.
{json_only} Shape (the names here are made up): {{"tables": ["name_1"]}}
{example}
Columns ({n_cols}):
"""

INSTRUCTION_P2H = """\
Below are columns found by analysing a corpus of dialogues (a kind of information, with a description, the type of its values, example values and
counts). Each column sits in a table of a database design: the heading above it is its table. For every column choose exactly one answer:
- "keep": the column stays in the table it is in
- "move to <table>": the column belongs in another listed table
- "{third}": {third_text}
Use only the listed tables; do not add tables. Most columns stay where they are.{notes}
{json_only} Shape (the ids and names here are made up): {{"x:1": "keep", "x:2": "move to table_b", "x:3": "{third}"}}
Every column id must appear once.
{example}
Tables: {tables}

Columns ({n_cols}):
"""
_THIRD_TEXT = {OTHER: "the column fits none of the listed tables; it is kept in a general \"rest\" column",
               V.UNUSED: "a database would not store the column"}
P2H_EXAMPLE = """\
Tables: customer, car, rental
Columns as listed (the heading is the table the column is in now): customer: customer_name, customer_phone, car_model; car: car_class, plate_number,
pickup_date; rental: return_date, daily_rate, loyalty_points
Answer: {"customer_name": "keep", "customer_phone": "keep", "car_model": "move to car", "car_class": "keep", "plate_number": "keep",
 "pickup_date": "move to rental", "return_date": "keep", "daily_rate": "keep", "loyalty_points": "%s"}"""

INSTRUCTION_PAIR44 = """\
Below are two tables of a relational database design, each with its columns. They may be linked: {evidence}
Decide whether {x} and {y} are linked, and which way. Answer with exactly one of:
- "none": no direct link
- "{x} -> {y}": one {x} row has many {y} rows (each {y} row refers to one {x} row)
- "{y} -> {x}": one {y} row has many {x} rows (each {x} row refers to one {y} row)
Do not invent a link that the columns do not support.
{json_only} Shape: {{"link": "none"}}
{example}
"""

INSTRUCTION_KEY44 = """\
Below is one table of a relational database design, with its columns.
Choose its primary key. The candidates are columns whose values are (almost) all different, so one of them may identify a row. Answer with the id of
one candidate, or "none" when no candidate identifies a row (a new id column is then added); then give the name of the new key column in
new_id_name (use "" when the primary key is an existing column).{fk_text}{note}
Candidates: {cands}
{json_only} Shape (the names and ids here are made up): {shape}
{example}
"""


def _p2_plain_other(text):
    """The v4.3 pass-2 instruction with "other" in place of "unused" (same layout)."""
    a = 'or into "unused" when a database\nwould not store it.'
    b = 'Use "unused" only when the column clearly holds nothing a database would\nstore.'
    if a not in text or b not in text:
        raise ValueError("step4_v43.INSTRUCTION_P2 changed: update step4_v44._p2_plain_other")
    text = text.replace(a, 'or into "other" when it fits none of them (it is then kept in a general "rest" column).')
    return text.replace(b, 'Use "other" only when the column clearly fits none of the tables.').replace('"x:3": "unused"', '"x:3": "other"')


def extra_cap(cols):
    n = len(entity_tables(cols))
    if n > V.MAX_TABLES:
        raise ValueError(f"{n} entities, more than the {V.MAX_TABLES}-table cap")
    return V.MAX_TABLES - n


def build_p1(cols, sw):
    """(prompt, schema, format) of pass 1."""
    if not sw["entity_hint"]:
        return (*V.build_p1(cols), "s43_p1")
    ents = entity_tables(cols)
    cap = extra_cap(cols)
    text = (INSTRUCTION_P1H.format(n_ent=len(ents), notes=V._signals_note(cols) + SP.V41_NOTE_41, ents=", ".join(ents), cap=cap,
                                   json_only=_JSON_ONLY, example=V._example("Pass 1"), n_cols=len(cols))
            + SP.render_columns([{**c, "entity": own_table(c)} for c in cols]) + "\nReturn the JSON object now.\n")
    return text, p1_schema_h(cap), "s44_p1"


def build_p2(cols, names, sw):
    """(prompt, schema, format) of pass 2."""
    if not sw["entity_hint"] and not sw["other_choice"]:
        return (*V.build_p2(cols, names), "s43_p2")
    third = OTHER if sw["other_choice"] else V.UNUSED
    if not sw["entity_hint"]:
        text = (_p2_plain_other(V.INSTRUCTION_P2).format(notes=V._signals_note(cols), json_only=_JSON_ONLY,
                                                          example=V._example("Pass 1", "Pass 2"), tables=", ".join(names), n_cols=len(cols))
                + SP.render_columns(cols) + "\nReturn the JSON object now.\n")
        return text, p2_schema_plain([c["id"] for c in cols], names, third), "s44_p2"
    example = _HEAD + P2H_EXAMPLE % third + "\n"
    text = (INSTRUCTION_P2H.format(third=third, third_text=_THIRD_TEXT[third], notes=V._signals_note(cols), json_only=_JSON_ONLY, example=example,
                                   tables=", ".join(names), n_cols=len(cols))
            + SP.render_columns([{**c, "entity": own_table(c)} for c in cols]) + "\nReturn the JSON object now.\n")
    return text, p2_schema_h(cols, names, third), "s44_p2"


def build_pair(x, y, cols_x, cols_y, sw, evidence=()):
    """(prompt, schema, format) of the link question of one pair."""
    if not sw["code_links"]:
        return (*V.build_pair(x, y, cols_x, cols_y), "s43_pair")
    text = (INSTRUCTION_PAIR44.format(x=x, y=y, evidence="; ".join(evidence[:3]), json_only=_JSON_ONLY, example=V._example("Links"))
            + "\n" + V._render_table(x, cols_x) + "\n" + V._render_table(y, cols_y) + "\nReturn the JSON object now.\n")
    return text, pair_schema3(x, y), "s44_pair"


def build_key(name, col_dicts, refs, sw, cands=()):
    """(prompt, schema, format) of the key question of one table (cands = key candidate ids, used when key_candidates is on)."""
    if not sw["key_candidates"]:
        return (*V.build_key(name, col_dicts, refs), "s43_key")
    ids = [c["id"] for c in col_dicts]
    fk_text = V._FK_TEXT.format(refs=", ".join(f"{r} (one {r} row has many rows of {name})" for r in refs)) if refs else ""
    shape = ('{"primary_key": "x:3", "new_id_name": "", "foreign_keys": {"table_b": "new"}}' if refs
             else '{"primary_key": "none", "new_id_name": "name id"}')
    text = (INSTRUCTION_KEY44.format(fk_text=fk_text, note=SP.V41_NOTE_44.replace('"new"', '"none"'), cands=", ".join(cands) or "(none)", json_only=_JSON_ONLY, shape=shape,
                                     example=V._example("Keys")) + "\n" + V._render_table(name, col_dicts) + "\nReturn the JSON object now.\n")
    return text, key_schema_c(cands, ids, refs), "s44_key"


# ---------------------------------------------------------------- answers -> state
def p1_extras(parsed, cols, log, where=""):
    """Table names of a hint-mode pass 1: the entity tables, then the listed names that are not an entity name (counted), within the cap."""
    ents, got = entity_tables(cols), []
    for n in V.p1_names(parsed, log, where):
        if n in ents:
            log.add("p1_entity_name", where, n)
        else:
            got.append(n)
    cap = extra_cap(cols)
    if len(got) > cap:
        log.add("p1_over_cap", where, f"{len(got)} extra names, kept {cap}")
    return ents + got[:cap]


def p2_assign(parsed, cols, names, sw, log, where=""):
    """(assign {id: table or None}, rest_host {id: table} for the "other" columns, names without an empty table). "unused" -> None; "other"
    -> None and a rest host (own table if it is kept, else the table with most columns, ties first). Bad, missing or unknown answers go to unused
    (counted, as v4.3)."""
    got = parsed if isinstance(parsed, dict) else {}
    ids = [c["id"] for c in cols]
    for k in got:
        if k not in ids:
            log.add("p2_unknown_column", where, repr(k))
    lookup = {n.lower(): n for n in names}
    third = OTHER if sw["other_choice"] else V.UNUSED
    assign, rest = {}, []
    for c in cols:
        i, v = c["id"], got.get(c["id"])
        s = str(v).strip().lower()
        t = None
        if v is None:
            log.add("p2_missing_column", where, i)
        elif s == third:
            if third == OTHER:
                rest.append(c)
        elif sw["entity_hint"] and s == KEEP:
            t = lookup.get(own_table(c))
        elif sw["entity_hint"] and s.startswith(MOVE):
            t = lookup.get(s[len(MOVE):].strip())
        elif not sw["entity_hint"] and s in lookup:
            t = lookup[s]
        if t is None and v is not None and s != third:
            log.add("p2_bad_name", where, f"{i}: {v!r}")
        assign[i] = t
    return (assign, *rest_hosts(assign, rest, names, log, where))


def rest_hosts(assign, rest, names, log, where=""):
    """(rest_host, kept names): the host table of every "other" column and the tables with at least one column or rest column hosted."""
    count = Counter(assign.values())
    kept = [n for n in names if count[n]]
    host = {}
    for c in rest:
        own = own_table(c)
        host[c["id"]] = own if own in kept else (max(kept, key=lambda n: (count[n], -kept.index(n))) if kept else None)
    for n in names:
        if n not in kept:
            log.add("p2_empty_table", where, n)
    return {i: h for i, h in host.items() if h}, kept


# ---------------------------------------------------------------- vote
def _label(st, i):
    if i in st.get("rest_host", {}):
        return ("rest", None)
    t = st["assign"].get(i)
    return ("table", t) if t else ("unused", None)


def align_tables(sts, th):
    """(reference table names, [per state {its table name: reference name}]): equal names are one table, else the best Jaccard of the column sets
    >= vote_table_jaccard (one to one, against the first state), else a table of its own with a unique name."""
    groups = [{n: {i for i, a in st["assign"].items() if a == n} for n in st["names"]} for st in sts]
    ref = {n: set(g) for n, g in groups[0].items()}
    maps = [{n: n for n in ref}]
    for g in groups[1:]:
        m, used = {n: n for n in g if n in ref}, {n for n in g if n in ref}
        cand = sorted(((-len(a & b) / len(a | b), n, r) for n, a in g.items() if n not in m for r, b in ref.items() if r not in used and a & b),
                      key=lambda x: (x[0], x[1], x[2]))
        for negj, n, r in cand:
            if -negj >= th["vote_table_jaccard"] and n not in m and r not in used:
                m[n] = r
                used.add(r)
        for n in g:
            if n not in m:
                m[n] = V._uniq(n, {r.lower() for r in ref})
                ref[m[n]] = set(g[n])
        maps.append(m)
    return list(ref), maps


def vote_state(sts, th):
    """State of the voted pass 2 from the finished seed states (cols, names, assign, rest_host, votes, info). Ties: the choice of the earliest state."""
    ref, maps = align_tables(sts, th)
    cols = sts[0]["cols"]
    assign, rest, votes, ties = {}, [], [], 0
    for c in cols:
        labs = []
        for st, m in zip(sts, maps):
            kind, t = _label(st, c["id"])
            labs.append((kind, m[t] if t else None))
        cnt = Counter(labs)
        top = max(cnt.values())
        win = next(x for x in labs if cnt[x] == top)             # earliest state among the tied choices
        ties += sum(v == top for v in cnt.values()) > 1
        assign[c["id"]] = win[1] if win[0] == "table" else None
        if win[0] == "rest":
            rest.append(c)
        votes.append({"id": c["id"], "choices": [f"{k}:{t}" if t else k for k, t in labs], "winner": f"{win[0]}:{win[1]}" if win[1] else win[0]})
    log = RepairLog()
    host, names = rest_hosts(assign, rest, ref, log)
    return {"cols": cols, "p1_names": ref, "names": names, "assign": assign, "rest_host": host, "votes": votes,
            "vote_info": {"seeds": len(sts), "tables_before": len(ref), "tables": len(names), "ties": ties, "empty_tables": log.counts["p2_empty_table"]}}


# ---------------------------------------------------------------- replay
def link_pairs(st, sw, th):
    """[(i, j, evidence)] of the pairs to ask about: every pair (v4.3) or the proposed ones (code_links)."""
    if not sw["code_links"]:
        return [(i, j, []) for i, j in V.pairs_of(st)]
    out = []
    for i, j in V.pairs_of(st):
        x, y = st["names"][i], st["names"][j]
        ev = link_evidence(x, y, V.table_cols(st, x), V.table_cols(st, y), st["stats"], th)
        if ev:
            out.append((i, j, ev))
    return out


def key_plan(st, i, sw, th):
    """(candidate ids, asked) of table i: key candidates (key_candidates on) and whether a key call is made."""
    n = st["names"][i]
    if not sw["key_candidates"]:
        return [], True
    cands = key_candidates(V.table_cols(st, n), st["stats"], th)
    return cands, bool(cands or V.key_refs(st, i))


def build_answers(st, keys, log, where=""):
    """V.build_answers plus the rest columns: a41.unused carries the REST_REASON of an "other" column, every host table gets a column "rest"."""
    a41, a42, a43, a44 = V.build_answers(st, keys, log, where)
    host = st.get("rest_host") or {}
    for u in a41["unused"]:
        if u["column"] in host:
            u["reason"] = f"{REST_REASON} {host[u['column']]}"
    for t in a44["tables"]:
        if t["name"] in host.values():
            taken = {c["name"].strip().lower() for c in t["columns"]} | {t["new_id_name"].strip().lower()}
            name = V._uniq(REST, taken)
            t["columns"].append({"column": f"new:{name}", "name": name, "type": "text"})
    return a41, a42, a43, a44


def replay(out, chain, upto, root=ROOT):
    """(state, error or None, RepairLog) of a chain after calls 1..upto (0 columns only, 1 p1, 2 p2, 3 pairs, 4 keys). As v4.3 plus stats,
    rest_host and, for a vote chain, the voted pass 2 (upto >= 2) from the pass-2 states of its members."""
    sw, th, cid, log = chain["switches"], chain["thresholds"], chain["id"], RepairLog()
    st = {"cols": B.chain_columns(chain, root), "stats": load_stats(out, chain), "rest_host": {}}
    if upto < 1:
        return st, None, log
    if chain["kind"] == "vote":
        sts = [s for s, err, _ in (replay(out, m, 2, root) for m in chain["members"]) if err is None]
        if not sts:
            return st, "vote: no seed chain reached pass 2", log
        st.update(vote_state(sts, th))
    else:
        cols = st["cols"]
        if sw["entity_hint"] and extra_cap(cols) == 0:
            st["p1_names"] = entity_tables(cols)
        else:
            parsed, why = V._answer(out, f"{cid}_p1")
            if why:
                return st, f"p1: {why}", log
            st["p1_names"] = p1_extras(parsed, cols, log, cid) if sw["entity_hint"] else V.p1_names(parsed, log, cid)
            if not st["p1_names"]:
                return st, "p1: no table name", log
        if upto < 2:
            return st, None, log
        parsed, why = V._answer(out, f"{cid}_p2")
        if why:
            return st, f"p2: {why}", log
        st["assign"], st["rest_host"], st["names"] = p2_assign(parsed, cols, st["p1_names"], sw, log, cid)
    if not st["names"]:
        return st, "p2: no column assigned to a table", log
    st["links"] = []
    if upto < 3:
        return st, None, log
    for i, j, _ in link_pairs(st, sw, th):
        x, y = st["names"][i], st["names"][j]
        parsed, why = V._answer(out, f"{cid}_r{i}_{j}")
        if why:
            log.add("pair_no_answer", f"{cid}:{x}/{y}", why)
            continue
        kind = V.pair_kind(parsed, x, y, log, f"{cid}:{x}/{y}")
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
        cands, asked = key_plan(st, i, sw, th)
        if not asked:
            keys[i] = {"primary_key": V.NEW, "new_id_name": f"{n} id"}
            continue
        parsed, why = V._answer(out, f"{cid}_k{i}")
        keys[i] = parsed if not why and isinstance(parsed, dict) else None
        if why and why != "no response":
            log.add("key_parse_error", f"{cid}:{n}", why)
        if keys[i] and keys[i].get("primary_key") == NONE:
            keys[i] = {**keys[i], "primary_key": V.NEW}
    a41, a42, a43, a44 = build_answers(st, keys, log, cid)
    errs = (SP.validate_41(a41, st["cols"]) + SP.validate_42(a42, a41) + SP.validate_43(a43, a41, a42)
            + SP.validate_44(a44, a41, a42, a43, st["cols"], strict=True))
    st["ans"] = {"41": a41, "42": a42, "43": a43, "44": a44}
    if errs:
        return st, f"assembly: {len(errs)} validation errors, e.g. {errs[:2]}", log
    return st, None, log


# ---------------------------------------------------------------- stages
def _emit(jobs, name, fmt, text, schema, chain, step, **extra):
    jobs.emit(name, "s4_41", text, schema, chain["id"], chain["set"], ent=chain["input"], chain=chain["id"], step=step, **extra)
    jobs.jobs[-1].update(family=fmt, format=fmt, max_tokens=MAX_TOKENS[fmt])


def build_stage(out, k, chains, root=ROOT):
    """Prompts of stage k (1 p1, 2 p2, 3 pairs, 4 keys) of `chains` from the earlier responses; the vote chain has stages 3 and 4 only. Writes
    <out>/manifests/<input>_stage<k>.json and chain_status_stage<k>_<input>.json; returns the job dicts."""
    out = Path(out)
    jobs, status = B.Jobs(out, k), []
    for ch in chains:
        if ch["kind"] == "vote" and k < 3:
            continue
        sw, th, cid = ch["switches"], ch["thresholds"], ch["id"]
        st, err, _ = replay(out, ch, k - 1, root)
        status.append({"chain": cid, "ok": err is None, "reached": k - 1 if err is None else None, "error": err})
        if err:
            continue
        if k == 1:
            if sw["entity_hint"] and extra_cap(st["cols"]) == 0:
                continue
            text, schema, fmt = build_p1(st["cols"], sw)
            _emit(jobs, f"{cid}_p1", fmt, text, schema, ch, k, n_columns=len(st["cols"]))
        elif k == 2:
            text, schema, fmt = build_p2(st["cols"], st["p1_names"], sw)
            _emit(jobs, f"{cid}_p2", fmt, text, schema, ch, k, n_columns=len(st["cols"]))
        elif k == 3:
            for i, j, ev in link_pairs(st, sw, th):
                x, y = st["names"][i], st["names"][j]
                text, schema, fmt = build_pair(x, y, V.table_cols(st, x), V.table_cols(st, y), sw, ev)
                _emit(jobs, f"{cid}_r{i}_{j}", fmt, text, schema, ch, k, pair=[x, y])
        elif k == 4:
            for i, n in enumerate(st["names"]):
                cands, asked = key_plan(st, i, sw, th)
                if asked:
                    text, schema, fmt = build_key(n, V.table_cols(st, n), V.key_refs(st, i), sw, cands)
                    _emit(jobs, f"{cid}_k{i}", fmt, text, schema, ch, k, table=n)
        else:
            raise ValueError(f"stage {k}: only 1 to 4")
    inp = chains[0]["input"] if chains else "none"
    B.write_json(out / "manifests" / f"{inp}_stage{k}.json", {"stage": k, "jobs": jobs.jobs})
    B.write_json(out / f"chain_status_stage{k}_{inp}.json", status)
    return jobs.jobs


# ---------------------------------------------------------------- chains, run, assembly
def columns_path(inp, set_name, step3_dirs=None, root=ROOT):
    """Column file of an input and set (Path or None). a / c1: results/wf_v4/inputs/<set>/<input>.columns.json (v4.3). a_llama43 / a_llama44: the first
    existing of <dir>/<set>/<input>.columns.json, <dir>/<set>/a.columns.json, <dir>/<set>.columns.json, <dir>/<set>/columns.json, with
    dir = step3_dirs[input] (default STEP3_DIRS: results/wf_v43/u2/a_llama43, results/wf_v44/t4/a_llama44)."""
    if inp not in ("a_llama43", "a_llama44"):
        return V.columns_path(inp, set_name, root=root)
    d = Path({**STEP3_DIRS, **(step3_dirs or {})}[inp])
    cands = [d / set_name / f"{inp}.columns.json", d / set_name / "a.columns.json", d / f"{set_name}.columns.json", d / set_name / "columns.json"]
    return next((p for p in cands if p.exists()), None)


def _rel(p, root):
    try:
        return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(Path(p).resolve())


def write_score_map(out, inp, set_name, ids):
    """<out>/score_map/<input>/<set>/<entity>.json in the handover format that step4_gt.map_handover reads (id, mention_ids), for the scorer."""
    by = {}
    for cid, m in ids.items():
        e, n = cid.split(":", 1)
        by.setdefault(e, []).append({"id": n, "mention_ids": m})
    for e, cs in by.items():
        B.write_json(Path(out) / "score_map" / inp / set_name / f"{e}.json", {"columns": cs})


def make_chains(out, inputs=INPUTS, sets=SETS, seeds=SEEDS, cfg=None, step3_dirs=None, root=ROOT, log=print, values_fn=column_values,
                ids_fn=mention_ids_of):
    """Chain dicts of the inputs in order (seed chains, then the vote chain of each input and set when the vote switch is on and there are two or
    more seeds). Writes <out>/values/<input>_<set>.json (when key_candidates or code_links is on; raises when the values cannot be found) and the
    scoring map <out>/score_map/<input>/ for inputs a_llama43 / a_llama44. A missing column file skips that input and set with a message."""
    cfg = cfg or load_config()
    sw, th, chains = cfg["switches"], cfg["thresholds"], []
    for inp in inputs:
        for s in sets:
            p = columns_path(inp, s, step3_dirs, root)
            if p is None:
                log(f"skip input {inp} {s}: column file not found")
                continue
            cols = B.read_json(p)
            vf = None
            if sw["key_candidates"] or sw["code_links"]:
                vals = values_fn(inp, s, p, cols, root)
                if vals is None:
                    raise ValueError(f"{inp} {s}: no mention ids for the columns in {p} (need <step 3 dir>/scores/final_columns.json or a "
                                     f"mention_ids field per column); needed by key_candidates / code_links")
                vf = f"values/{inp}_{s}.json"
                B.write_json(Path(out) / vf, vals)
            if inp in ("a_llama43", "a_llama44"):
                ids = ids_fn(inp, s, p, cols, root)
                if ids is not None:
                    write_score_map(out, inp, s, ids)
            seed_chains = [{"id": B.chain_id(inp, s, d), "kind": "main", "input": inp, "set": s, "seed": d, "exclude": [], "prompt_version": "v44",
                            "columns_file": _rel(p, root), "switches": dict(sw), "thresholds": dict(th), "values_file": vf} for d in seeds]
            chains += seed_chains
            if sw["vote"] and len(seeds) >= 2:
                chains.append({**seed_chains[0], "id": f"{inp}_{s}_vote", "kind": "vote", "seed": 0, "members": seed_chains})
    return chains


def assemble_all(out, chains, root=ROOT):
    """final/<chain>/{canonical.json, schema.sql, operations.json, repairs.json} per finished chain, final/status.json (every chain: kind, ok, tables,
    repairs by type, error), <out>/repairs.json (total + per chain) and <out>/votes/<chain>.json (the vote of each column). Returns the status."""
    out, status, total, per_chain = Path(out), [], RepairLog(), {}
    final = out / "final"
    for ch in chains:
        st, err, log = replay(out, ch, 4, root)
        total.merge(log)
        per_chain[ch["id"]] = log.to_dict()["counts"]
        row = {"run": ch["id"], "kind": ch["kind"], "input": ch["input"], "set": ch["set"], "seed": ch["seed"] if ch["kind"] == "main" else "vote",
               "ok": err is None, "repairs": log.total(), "repair_kinds": log.to_dict()["counts"], "error": err,
               "tables": len(st["ans"]["44"]["tables"]) if err is None else None}
        if err is None:
            c = B.assemble_chain(st["ans"], st["cols"])
            B.write_json(final / ch["id"] / "canonical.json", c)
            B.write(final / ch["id"] / "schema.sql", SQL.to_sql(c))
            B.write_json(final / ch["id"] / "operations.json", SQL.to_operations(c))
            log.save(final / ch["id"] / "repairs.json")
        if ch["kind"] == "vote" and "votes" in st:
            B.write_json(out / "votes" / f"{ch['id']}.json", {"info": st["vote_info"], "votes": st["votes"]})
        status.append(row)
    B.write_json(final / "status.json", status)
    B.write_json(out / "repairs.json", {**total.to_dict(), "per_chain": per_chain})
    return status


def run(out, backend, inputs=INPUTS, sets=SETS, seeds=SEEDS, cfg=None, step3_dirs=None, root=ROOT, log=print, values_fn=column_values,
        ids_fn=mention_ids_of):
    """All stages of the chains of `inputs`, one input after the other, then the assembly. backend.run(out, jobs) answers a stage (log_v44.VllmBackend44 on
    Colab, step4_fake_v44.FakeV44 on the laptop; a rerun skips answered jobs). Returns {"chains", "switches", "inputs": {input: {stage k: backend info}},
    "finished": "ok/n"}; also written to <out>/run_info.json."""
    out = Path(out)
    cfg = cfg or load_config()
    chains = make_chains(out, inputs, sets, seeds, cfg, step3_dirs, root, log, values_fn, ids_fn)
    B.write_json(out / "chains.json", chains)
    info = {"chains": len(chains), "switches": cfg["switches"], "thresholds": cfg["thresholds"], "inputs": {}}
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


# ---------------------------------------------------------------- scoring (v4.3 scorers: step4_score.score; rest field new)
def score_map_dir(out, inp, root=ROOT, legacy=False):
    """Handover-format dir that maps the input's column ids to mention ids: <out>/score_map/<input> (written by make_chains for a_llama4x), else the
    Qwen handover (right for input a; c1 columns carry `gt`). legacy=True: always the handover (what v4.3 did for a_llama43)."""
    d = Path(out) / "score_map" / inp
    return d if d.exists() and not legacy else Path(root) / "handover"


def rest_gt_columns(canonical, mapping, gt, design_name, reach):
    """(k, n): k = GT columns of the best design that are held only in a rest column (an unused entry with REST_REASON that maps to the GT column,
    and no table column does); n = GT columns of that design in the GT view (reach None = full GT)."""
    names = G.gt_names(gt)
    only_rest = {**canonical, "unused": [u for u in canonical.get("unused", []) if str(u.get("reason", "")).startswith(REST_REASON)]}
    res = S.resolve(only_rest, names, mapping)
    placed = {c["gt"] for t in res["tables"] for c in t["cols"] if c["gt"]}
    design = next(d for d in G.all_designs(gt) if d["name"] == design_name)
    gt_cols = {c for t in S.view(design, reach)["tables"].values() for c in t["cols"]}
    return len({u["gt"] for u in res["unused"] if u["gt"]} & (gt_cols - placed)), len(gt_cols)


def score_chains(out, root=ROOT, gt_path=None, legacy_mapping=False):
    """Score every finished chain of <out>/final/status.json (single seeds and vote) with the v4.3 scorer, full and reachable-only GT, plus
    gt_in_rest_k / _n / gt_in_rest; writes <out>/scores.csv (columns of the scorer, then input, kind, seed, n_tables, repairs) and returns the rows."""
    import score_v4 as SCR
    out, root = Path(out), Path(root)
    gt = SC43.load_gt(root, gt_path)
    rows = []
    for r in B.read_json(out / "final" / "status.json"):
        if not r["ok"]:
            continue
        c = B.read_json(out / "final" / r["run"] / "canonical.json")
        mapping = S.map_columns(c, r["set"], score_map_dir(out, r["input"], root, legacy_mapping), SCR.GT_LEVELS[r["set"]], gt)
        for ro in (False, True):
            res = S.score(c, gt, r["set"], ro, mapping)
            k, n = rest_gt_columns(c, mapping, gt, res["design"], gt["reachable"].get(r["set"]) if ro else None)
            rows.append({"schema": r["run"], **S.flat(res), "gt_in_rest_k": k, "gt_in_rest_n": n, "gt_in_rest": k / n if n else None,
                         "input": r["input"], "kind": r["kind"], "seed": r["seed"], "n_tables": len(c["tables"]), "repairs": r["repairs"]})
    SCR.write_rows(out / "scores.csv", rows)
    return rows


METRICS = SC43.METRICS[:1] + (("gt_in_rest", "GT columns in rest"),) + SC43.METRICS[1:]


def summary(out, scores=None):
    """Write <out>/summary.md and <out>/calls.csv; returns the text. Rows per input and set: the voted schema and the single-seed schemas
    (counts summed over the chains, F1 means); then repairs by type and calls and tokens per input and set (job names start with <input>_<set>_)."""
    import csv
    out = Path(out)
    status = B.read_json(out / "final" / "status.json")
    if scores is None:
        with open(out / "scores.csv", encoding="utf-8") as f:
            scores = list(csv.DictReader(f))
    full = [r for r in scores if str(r["reachable_only"]) == "False"]
    lines = ["# wf_v4.4 Step 4 (Llama-3.1-8B)", "",
             "Scores with the v4.3 scorers (full GT; `scores.csv` has reachable-only too). Counts are summed over the finished chains of a row, F1 values "
             "are means. `vote` = the voted schema (one chain per input and set), `single` = the seed chains. GT columns in rest = GT columns held only "
             "in a \"rest\" column.", "",
             "| input | set | schema | chains finished | table F1 | grouping F1 | " + " | ".join(n for _, n in METRICS) + " | tables per chain | repairs per chain |",
             "|" + "---|" * (6 + len(METRICS) + 2)]
    inputs = list(dict.fromkeys(r["input"] for r in status))
    for inp in inputs:
        for s in sorted({r["set"] for r in status if r["input"] == inp}) + ["all"]:
            for kind, label in (("vote", "vote"), ("main", "single")):
                st = [r for r in status if r["input"] == inp and (s == "all" or r["set"] == s) and r["kind"] == kind]
                if not st:
                    continue
                ids = {r["run"] for r in st if r["ok"]}
                rs = [r for r in full if r["schema"] in ids]
                rep = [r["repairs"] for r in st]
                lines.append(f"| {inp} | {s} | {label} | {len(ids)}/{len(st)} | {SC43._mean(rs, 'table_f1')} | {SC43._mean(rs, 'grouping_f1')} | "
                             + " | ".join(SC43._kn(rs, m) for m, _ in METRICS)
                             + f" | {SC43._rng([r['tables'] for r in st if r['ok']])} | {sum(rep) / len(rep):.1f} ({SC43._rng(rep)}) |")
    bad = [r for r in status if not r["ok"]]
    lines += ["", f"Chains not finished: {len(bad)}" + "".join(f"\n- {r['run']}: {r['error']}" for r in bad), ""]
    if (out / "repairs.json").exists():
        rep = B.read_json(out / "repairs.json")
        lines += [f"Repairs (all chains): {rep['total']}", "", "| type | count |", "|---|---|"]
        lines += [f"| {k} | {n} |" for k, n in sorted(rep["counts"].items(), key=lambda kv: -kv[1])] + [""]
    rows = [r for r in call_rows(out) if not r['file'].startswith('fake/')]
    lines += ["| input | set | chains | calls | calls per chain | prompt tokens | output tokens | retried |", "|---|---|---|---|---|---|---|---|"]
    for inp in inputs:
        for s in sorted({r["set"] for r in status if r["input"] == inp}):
            mine = [r for r in rows if r["job"].startswith(f"{inp}_{s}_")]
            n = len([r for r in status if r["input"] == inp and r["set"] == s])
            t = call_totals(mine)
            lines.append(f"| {inp} | {s} | {n} | {t['calls']} | {t['calls'] / max(n, 1):.1f} | {t['prompt_tokens']} | {t['output_tokens']} | {t['retried']} |")
    text = "\n".join(lines) + "\n"
    B.write(out / "summary.md", text)
    with open(out / "calls.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(CALL_FIELDS) + ["file"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return text
