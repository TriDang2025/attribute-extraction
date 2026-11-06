"""wf_v4 Step 4 GT (diary task 0): load gt/schema_gt_v1.yaml, build the acceptable designs, canonical schema JSON, SQL, checks, reachability.

Pure functions; files are read only in load_gt, map_handover and load_reachable. The GT is for scoring only (WF_V4_CONTRACT.md).

Designs: the YAML rule "Booking columns may be in the place table or in a booking table; if they are in the place table, the booking id and
link columns are not needed" gives one choice per entity that has an X_booking table (train, hotel, restaurant): split (booking table, main
design) or merged (the booking table's non-key columns move into table X; its id column and its link column are dropped; the link column of a
booking table is the one with role primary_key or foreign_key, so "Hotel confirmed name" goes too). That is 2^3 = 8 designs, kept as
gt["alternatives"] (the 7 non-main ones; each {name, merged, tables, foreign_keys}); the main design is gt["tables"] / gt["foreign_keys"]
(name "main"). The scorer scores every design as a whole and keeps the best (step4_score.py); a per-entity choice would need the table
matching to be separable per entity, which it is not when an output table mixes entities.
"""

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import yaml

PURITY = 0.6   # purity of a handover column's majority gt_L2 needed to count its GT column as found (as rules_groups.PURE)
ENTITIES = ("train", "hotel", "restaurant")  # entities in the Step-3 handover
CANON_TYPES = ("text", "integer", "decimal", "time", "day", "date", "boolean", "id", "duration", "price")
GT_TYPE_TO_CANON = {"number": "integer", "unknown": "text"}  # GT "number" (phone, people, stars) -> integer; "unknown" -> text (not scored)
SQL_TYPES = {"text": "TEXT", "integer": "INTEGER", "decimal": "REAL", "time": "TIME", "day": "TEXT", "date": "DATE",
             "boolean": "BOOLEAN", "id": "TEXT", "duration": "TEXT", "price": "REAL"}
GT_TYPES = set(CANON_TYPES) | set(GT_TYPE_TO_CANON)


def norm(s):
    """Name normalisation: lower case, single spaces."""
    return " ".join(str(s).lower().split())


# ---- load

def _column(c):
    return {"name": c["name"], "type": c.get("type", "unknown"), "slot": c.get("mwoz22_slot") or "none",
            "source": c["source"], "level": c.get("level"), "role": c.get("role"), "description": c.get("description", ""),
            "mentions": {"dev50": c.get("mentions_dev50"), "dev50b": c.get("mentions_dev50b")}}


def _merge_design(main, entities):
    """Design where the booking table of each entity in `entities` is folded into its place table."""
    tables = {n: {**t, "columns": list(t["columns"])} for n, t in main["tables"].items()}
    fks = list(main["foreign_keys"])
    for e in entities:
        booking = f"{e}_booking"
        for c in tables.pop(booking)["columns"]:
            if c["role"] not in ("primary_key", "foreign_key"):
                tables[e]["columns"].append(c)
        fks = [f for f in fks if f["table"] != booking]
    return {"name": "merged:" + "+".join(entities), "merged": list(entities), "tables": tables, "foreign_keys": fks}


def build_designs(main):
    """The 7 alternative designs: every non-empty subset of the entities that have a booking table."""
    ents = [e for e in ENTITIES if f"{e}_booking" in main["tables"]]
    return [_merge_design(main, list(s)) for r in range(1, len(ents) + 1) for s in combinations(ents, r)]


def parse_gt(doc):
    """GT dict from the parsed YAML (see module doc)."""
    tables, fks = {}, []
    for t in doc["tables"]:
        tables[t["name"]] = {"entity": t["entity"], "columns": [_column(c) for c in t["columns"]], "primary_key": list(t["key"])}
        for l in t.get("links") or []:
            rt, rc = l["to"].split(".", 1)
            fks.append({"table": t["name"], "columns": [l["from"]], "ref_table": rt, "ref_columns": [rc]})
    soft = []
    for t in doc["tables"]:
        for s in t.get("soft_links") or []:
            soft.append({"from_table": t["name"], "from_column": s["from"], "to": [l.split(".", 1) for l in s["to"]],
                         "kind": s.get("kind", ""), "note": s.get("note", "")})
    gt = {"tables": tables, "foreign_keys": fks, "soft_links": soft, "shared_values": doc.get("shared_values") or [],
          "matching": doc.get("matching") or [], "not_columns": doc.get("not_columns") or [], "not_connected": doc.get("not_connected") or [],
          "meta": doc.get("meta") or {}, "reachable": {}}
    gt["alternatives"] = build_designs(gt)
    return gt


def load_gt(path):
    with open(path, encoding="utf-8") as f:
        return parse_gt(yaml.safe_load(f))


def main_design(gt):
    return {"name": "main", "merged": [], "tables": gt["tables"], "foreign_keys": gt["foreign_keys"]}


def all_designs(gt):
    """[main design] + the alternatives; the main one is first (wins ties)."""
    return [main_design(gt)] + list(gt["alternatives"])


# ---- canonical schema and SQL

def to_canonical(gt, design=None):
    """Canonical schema JSON (WF_V4_CONTRACT.md) of a design (dict from all_designs, or None = main). Every column has gt = its own GT name;
    source null; new = true for added columns. Relationships: from = table holding the FK, kind one_to_many."""
    d = design or main_design(gt)
    tables = []
    for name, t in d["tables"].items():
        cols = [{"name": c["name"], "type": GT_TYPE_TO_CANON.get(c["type"], c["type"]), "source": None, "new": c["source"] == "added",
                 "gt": c["name"]} for c in t["columns"]]
        fk = [{"columns": f["columns"], "ref_table": f["ref_table"], "ref_columns": f["ref_columns"]}
              for f in d["foreign_keys"] if f["table"] == name]
        tables.append({"name": name, "description": f"{t['entity']} ({name})", "row": "one " + name.replace("_", " "),
                       "columns": cols, "primary_key": list(t["primary_key"]), "foreign_keys": fk})
    rel = [{"from": f["table"], "to": f["ref_table"], "kind": "one_to_many", "reason": "foreign key " + ", ".join(f["columns"])}
           for f in d["foreign_keys"]]
    return {"tables": tables, "relationships": rel, "unused": [], "duplicate_flags": []}


def _q(s):
    return '"' + str(s).replace('"', '""') + '"'


def to_sql(schema):
    """CREATE TABLE statements (referenced tables first) of a canonical schema, with PRIMARY KEY and FOREIGN KEY."""
    by = {t["name"]: t for t in schema["tables"]}
    order, seen = [], set()

    def visit(n):
        if n in seen or n not in by:
            return
        seen.add(n)
        for f in by[n]["foreign_keys"]:
            if f["ref_table"] != n:
                visit(f["ref_table"])
        order.append(n)

    for t in schema["tables"]:
        visit(t["name"])
    out = []
    for n in order:
        t = by[n]
        lines = [f"  {_q(c['name'])} {SQL_TYPES.get(c['type'], 'TEXT')}" for c in t["columns"]]
        if t["primary_key"]:
            lines.append("  PRIMARY KEY (" + ", ".join(_q(c) for c in t["primary_key"]) + ")")
        for f in t["foreign_keys"]:
            lines.append("  FOREIGN KEY (" + ", ".join(_q(c) for c in f["columns"]) + f") REFERENCES {_q(f['ref_table'])} ("
                         + ", ".join(_q(c) for c in f["ref_columns"]) + ")")
        out.append(f"CREATE TABLE {_q(n)} (\n" + ",\n".join(lines) + "\n);")
    return "\n\n".join(out) + "\n"


# ---- checks and questions

def check(gt):
    """List of problems (empty = fine), over the main design and every alternative: every table has a primary key that is one of its
    columns; every FK points to an existing table and column and starts in an existing column; no column name appears in two tables
    (within a design); known types; no duplicate column inside a table."""
    problems = []
    for d in all_designs(gt):
        tag = d["name"]
        seen = {}
        for tn, t in d["tables"].items():
            names = [c["name"] for c in t["columns"]]
            if not t["primary_key"]:
                problems.append(f"[{tag}] table {tn}: no primary key")
            for k in t["primary_key"]:
                if k not in names:
                    problems.append(f"[{tag}] table {tn}: primary key {k!r} is not a column")
            for n, c in Counter(names).items():
                if c > 1:
                    problems.append(f"[{tag}] table {tn}: column {n!r} twice")
            for c in t["columns"]:
                if c["type"] not in GT_TYPES:
                    problems.append(f"[{tag}] table {tn}: column {c['name']!r} has unknown type {c['type']!r}")
                if c["name"] in seen and seen[c["name"]] != tn:
                    problems.append(f"[{tag}] column {c['name']!r} in two tables: {seen[c['name']]}, {tn}")
                seen.setdefault(c["name"], tn)
        for f in d["foreign_keys"]:
            if f["table"] not in d["tables"] or any(c not in {x["name"] for x in d["tables"][f["table"]]["columns"]} for c in f["columns"]):
                problems.append(f"[{tag}] FK {f['table']}.{f['columns']}: column missing")
            rt = d["tables"].get(f["ref_table"])
            if rt is None or any(c not in {x["name"] for x in rt["columns"]} for c in f["ref_columns"]):
                problems.append(f"[{tag}] FK {f['table']}.{f['columns']} -> {f['ref_table']}.{f['ref_columns']}: target missing")
    for s in gt["soft_links"]:
        for t, c in [(s["from_table"], s["from_column"])] + [tuple(x) for x in s["to"]]:
            if t not in gt["tables"] or c not in {x["name"] for x in gt["tables"][t]["columns"]}:
                problems.append(f"soft link {s['from_table']}.{s['from_column']}: {t}.{c} missing")
    return problems


def questions(gt, handover_entities=ENTITIES):
    """Things that look unclear in the GT, one plain-English line each. Questions for the user; nothing is decided here."""
    q = []
    for tn, t in gt["tables"].items():
        for c in t["columns"]:
            if c["type"] == "unknown":
                q.append(f"Column {c['name']!r} ({tn}) has type 'unknown'. Which type is right? It is not scored now.")
        if t["entity"] not in handover_entities:
            q.append(f"Table {tn!r} ({t['entity']}) has no Step-3 handover, so none of its {len(t['columns'])} columns can be found. "
                     f"Keep it in the full GT only?")
    fk_cols = {(f["table"], c) for f in gt["foreign_keys"] for c in f["columns"]}
    for tn, c in sorted(fk_cols):
        col = next(x for x in gt["tables"][tn]["columns"] if x["name"] == c)
        if col["source"] != "added":
            q.append(f"Link column {c!r} ({tn}) is a real attribute with 0 mentions and no MultiWOZ slot. Should it count as a GT attribute, "
                     f"and should it be dropped when the booking columns move into the place table (done now)?")
    for tn, t in gt["tables"].items():
        for c in t["columns"]:
            m = c["mentions"]
            if c["source"] != "added" and m["dev50"] == 0 and m["dev50b"] == 0 and (tn, c["name"]) not in fk_cols:
                q.append(f"Column {c['name']!r} ({tn}) has 0 mentions in dev50 and dev50b, so it can never be found. Keep it in the GT?")
            if c["slot"] == "none" and c["source"] != "added" and (tn, c["name"]) not in fk_cols:
                q.append(f"Column {c['name']!r} ({tn}) has no mwoz22_slot. Intended?")
    for s in gt["soft_links"]:
        tos = ", ".join(f"{t}.{c}" for t, c in s["to"])
        q.append(f"Soft link {s['from_table']}.{s['from_column']} -> {tos}: a predicted link here is counted correct, a missing one is not "
                 f"counted. Right?")
    if gt["shared_values"]:
        q.append(f"Shared value sets ({', '.join(v['values_of'] for v in gt['shared_values'])}) are not scored; an extra lookup table "
                 f"in the output counts as an unmatched table. Right?")
    q.append("When the booking columns sit in the place table, the booking id and link columns are dropped from the GT; "
             "the scorer takes the best of the 8 designs (best grouping F1, then table F1). Right?")
    return q


# ---- handover mapping and reachability

def read_gt_levels(path):
    import pandas as pd
    return pd.read_csv(path, usecols=["mention_id", "gt_L2"]).set_index("mention_id")["gt_L2"].fillna("")


def split_labels(v):
    """gt_L2 of one mention: labels split on ';' (a mention can carry several); [""] when empty."""
    return [x.strip() for x in str(v).split(";") if x.strip()] or [""]


def map_handover(handover_dir, set_name, gt_levels, names=None, entities=ENTITIES):
    """{"<entity>:<id>": {"gt", "purity", "n", "entity"}} for every handover column: gt = the most common gt_L2 label of its mention_ids
    (gt_L2 is multi-label, "A;B": every label counts once for the mention; an empty gt_L2 counts as a label and the denominator is all mentions; ties by name; None when the top label is empty), purity =
    its share, n = number of mentions; also labels {label: mentions} (non-empty labels) and n_labelled (mentions with a gt_L2). gt_levels: path to gt_levels.csv or a Series mention_id -> gt_L2. names: {norm: GT name} to
    normalise case and spaces."""
    lev = read_gt_levels(gt_levels) if isinstance(gt_levels, (str, Path)) else gt_levels
    out = {}
    for ent in entities:
        p = Path(handover_dir) / set_name / f"{ent}.json"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        for c in doc["columns"]:
            ids = [i for i in c["mention_ids"] if i in lev.index]
            cnt = Counter((names or {}).get(norm(lab), lab) if lab else "" for i in ids for lab in split_labels(lev.loc[i]))
            top, k = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0] if cnt else ("", 0)
            labels = {l: v for l, v in cnt.items() if l}
            n_lab = sum(1 for i in ids if str(lev.loc[i]).strip())
            out[f"{ent}:{c['id']}"] = {"gt": top or None, "purity": k / len(ids) if ids else 0.0, "n": len(ids), "entity": ent,
                                       "labels": labels, "n_labelled": n_lab}
    return out


def gt_names(gt):
    """{norm name: GT name} over the main design."""
    return {norm(c["name"]): c["name"] for t in gt["tables"].values() for c in t["columns"]}


def reachable_rows(gt, mapping, min_purity=PURITY):
    """One row per main-design GT column: gt_table, gt_column, level, reachable yes / no / added, found_by (handover column ids).
    yes = some handover column of the same entity has that label on >= min_purity of its labelled mentions (any label, not only the top
    one; fallback of final_v39's found rule, which uses the same 0.6 over the counted = labelled mentions)."""
    found = {}
    for cid, m in mapping.items():
        for lab, k in m.get("labels", {}).items():
            if m["n_labelled"] and k / m["n_labelled"] >= min_purity:
                found.setdefault(lab, []).append(cid)
    rows = []
    for tn, t in gt["tables"].items():
        for c in t["columns"]:
            by = [i for i in found.get(c["name"], []) if i.split(":")[0] == t["entity"]]
            status = "added" if c["source"] == "added" else "yes" if by else "no"
            rows.append({"gt_table": tn, "gt_column": c["name"], "level": c["level"] or "", "reachable": status, "found_by": " ".join(by)})
    return rows


def reachable_status(rows):
    """{gt column: yes / no / added} where an 'added' column is reachable only if its table has a 'yes' column; returns that
    resolved dict as {column: yes|no} (added -> yes iff its table has a yes column)."""
    has = {r["gt_table"] for r in rows if r["reachable"] == "yes"}
    return {r["gt_column"]: ("yes" if r["reachable"] == "yes" or (r["reachable"] == "added" and r["gt_table"] in has) else "no")
            for r in rows}


def load_reachable(path):
    import pandas as pd
    return pd.read_csv(path, keep_default_na=False).to_dict("records")


def attach_reachable(gt, set_name, rows):
    """Store the resolved reachability ({column: yes|no}) of one set in gt['reachable'][set]."""
    gt["reachable"][set_name] = reachable_status(rows)
    return gt
