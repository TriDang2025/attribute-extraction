"""wf_v3.9 Colab batch (contract WF_V39_BATCH.md): pure functions, no I/O, no models. Builds on s1a/batch_v38.py.

- T4 reconcile: part_records (the split-pass parts of A s012 that have mentions), nearest_columns (5 nearest OTHER columns of
  the part), shuffled_order (candidate order per seed), render_reconcile / schema_reconcile (one call per part),
  choice_from_response, apply_reconcile (stage 2: join each part's mentions to the chosen column; role pairs blocked by
  batch_v38.check_joins; "none" keeps the part where it is). apply_reconcile is the one place the joins are applied: the
  stage 2 builder and the local scoring both call it.
- T8 A-cue: A's v2 prompt plus one cue line (render_a_cue), schema_a_cue, parse_job (llm_cache.parse_job that accepts
  "attribute_cue" as a cluster's attribute for the a_cue family: parse_response_v2 reports it as not in the attribute list).
"""

import zlib

import numpy as np

from . import batch_v38 as BT
from . import llm_cache as LC

N_CANDIDATES = 5      # T4: nearest other columns shown with a part
N_PART_EXAMPLES = 5   # T4: example sentences of the part
NONE = "none"
MAX_TOKENS = {"reconcile": 256, "dupcheck": BT.MAX_TOKENS["dupcheck"]}


# ---- T4: parts and candidates

def part_records(cols, attrs, roles=None):
    """[dict] one per split-pass part of the variant that has mentions. cols: column dicts (column_table, or loaded from
    JSON); attrs: dicts with attr_id, name, clusters, source (the variant's attrs rows; a part has source "split" and
    attr_id "<cluster>/<k>"); roles {(cluster id, raw part name): role} from the split responses (description of the part, ""
    when unknown). Keys: pid (attr_id), key (member key "<cluster>@<attr_id>" of the column pools), cid (the column that
    holds the part), name (that column's name), description, cluster, mention_ids."""
    roles = roles or {}
    owner = {}
    for c in cols:
        for key, items in c["pools"]:
            owner[key] = (c, items)
    out = []
    for a in attrs:
        if a["source"] != "split":
            continue
        key = f"{a['clusters']}@{a['attr_id']}"
        if key not in owner:   # a part with no mention is in no column
            continue
        c, items = owner[key]
        out.append({"pid": a["attr_id"], "key": key, "cid": c["cid"], "name": c["name"], "cluster": a["clusters"],
                    "description": roles.get((a["clusters"], a["name"]), ""), "mention_ids": [int(x[0]) for x in items]})
    return out


def nearest_columns(cent, part_vec, own_cid, k=N_CANDIDATES):
    """The k cids of the columns other than `own_cid` with the highest cosine to the unit vector `part_vec` (ties by lower
    cid). cent: {cid: unit vector} (batch_v38.centroids); a column without mentions has no centroid and is never a candidate."""
    rest = {c: v for c, v in cent.items() if c != own_cid}
    sentinel = -1
    rest[sentinel] = part_vec
    return BT.nearest(rest, sentinel, k)


def shuffled_order(items, seed, salt):
    """`items` in a random order fixed by (seed, salt); the same input and seed always give the same order."""
    rng = np.random.default_rng([seed, zlib.crc32(str(salt).encode())])
    return [items[i] for i in rng.permutation(len(items))]


RECONCILE_INSTRUCTION = """\
Below is one part of a cluster of values taken from dialogue turns, and a list of other columns of the same table. Each
column has a name, a description (when there is one) and example values. The examples of the part are marked with [[ ]]
inside the turn they come from. Values that play different roles (where something starts and where it ends, the
earliest and the latest time) are different attributes. If unsure, answer none."""


def render_reconcile(part, cands, example_lines):
    """Prompt of one reconcile call. part: a part_records dict; cands: candidate column dicts (name, description,
    top_values) in the order shown; example_lines: the part's example lines (numbered)."""
    head = f"Part {part['pid']}: name: {part['name']}" + (f" | description: {part['description']}" if part["description"] else "")
    rows = []
    for c in cands:
        parts = [f"name: {c['name']}"]
        if c["description"]:
            parts.append(f"description: {c['description']}")
        parts.append("examples: " + ("; ".join(c["top_values"]) or "(none)"))
        rows.append("- " + " | ".join(parts))
    return "\n\n".join([RECONCILE_INSTRUCTION, head + "\nExamples:\n" + "\n".join(example_lines),
                        f"Columns ({len(cands)}):\n" + "\n".join(rows),
                        "Question: Is this part the same attribute, with the same role, as one of these columns? "
                        "Answer that column's name, or none.",
                        'Return ONLY one JSON object, nothing before or after it, with a reason of at most 25 words '
                        'written before the answer: {"unit_id": "' + part["pid"] + '", "reason": "str", '
                        '"same_as": "<column name or none>"}']) + "\n"


def schema_reconcile(pid, names):
    """Guided JSON: unit_id (the part), a short reason, same_as = one of the candidate names or "none"."""
    return {"type": "object",
            "properties": {"unit_id": {"enum": [pid]}, "reason": {"type": "string"}, "same_as": {"enum": list(names) + [NONE]}},
            "required": ["unit_id", "reason", "same_as"]}


def choice_from_response(parsed, errors, candidates):
    """Chosen column cid of one reconcile response, or None. parsed, errors: llm_cache.parse_reconcile output;
    candidates: [{"cid", "name"}] of the job. None when the response has errors, answers none or names no candidate."""
    if errors or not isinstance(parsed, dict):
        return None
    by_name = {c["name"]: c["cid"] for c in candidates}
    return by_name.get(parsed.get("same_as"))


# ---- T4 stage 2: apply the joins

def _items(pool):
    return [(int(x[0]), x[1], x[2]) for x in pool]


def apply_reconcile(cols, parts, choices):
    """(new columns, report): each part with a chosen column moves its mentions (its pool) from its own column to the chosen
    one. choices {pid: cid or None}; None, the part's own cid or an unknown cid keep the part; a join whose two column names
    form a role pair (batch_v38.check_joins, names only, never the GT) is blocked and keeps the part. A column that loses a
    part and ends with no mention is dropped (a column that was empty before stays). New columns are sorted by name and
    numbered 1..n like batch_v38.column_table; keys: cid, name, description, groups, members, mention_ids, n_mentions,
    n_dialogues, n_values, top_values, pools, old_cids (the cids of `cols` that went into it). value_types is not carried.
    report: [{pid, from, to, status}], status joined | none | blocked | invalid."""
    by_id = {c["cid"]: c for c in cols}
    pools = {c["cid"]: {k: _items(p) for k, p in c["pools"]} for c in cols}
    groups = {c["cid"]: list(c["groups"]) for c in cols}
    lost, report = set(), []
    for p in parts:
        to = choices.get(p["pid"])
        row = {"pid": p["pid"], "from": p["cid"], "to": to}
        if to is None:
            report.append({**row, "status": "none"})
        elif to == p["cid"] or to not in by_id or p["key"] not in pools[p["cid"]]:
            report.append({**row, "status": "invalid"})
        elif BT.check_joins([{"columns": [p["cid"], to]}], by_id)[1]:
            report.append({**row, "status": "blocked"})
        else:
            pools[to][p["key"]] = pools[p["cid"]].pop(p["key"])
            groups[p["cid"]] = [g for g in groups[p["cid"]] if g != p["pid"]]
            groups[to].append(p["pid"])
            lost.add(p["cid"])
            report.append({**row, "status": "joined"})
    return assemble_columns(cols, pools, groups, lost), report


def assemble_columns(cols, pools, groups, lost):
    """The columns of `cols` after their pools {cid: {member key: items}} and groups {cid: [attr ids]} were changed: a column in
    `lost` (it gave a member away) with no pool left is dropped; the rest are sorted by name, numbered 1..n and get their counts
    and top values recomputed (keys of apply_reconcile)."""
    out = []
    for c in sorted(cols, key=lambda c: c["name"]):
        cid = c["cid"]
        if cid in lost and not pools[cid]:
            continue
        ps = sorted(pools[cid].items(), key=lambda kv: (-len(kv[1]), kv[0]))
        rows = [x for _, items in ps for x in items]
        out.append({"cid": len(out) + 1, "name": c["name"], "description": c["description"], "groups": sorted(groups[cid]),
                    "members": sorted(pools[cid]), "mention_ids": [x[0] for x in rows], "n_mentions": len(rows),
                    "n_dialogues": len({x[1] for x in rows}), "n_values": len({x[2] for x in rows}),
                    "top_values": BT._top_values([x[2] for x in rows]), "pools": ps, "old_cids": [cid]})
    return out


# ---- T8: A with a cue line

def a_cue_instruction():
    """INSTRUCTION_V2 with pilot_input.CUE_LINE after its noise sentence (where INSTRUCTION_V2_AE adds the noise rule);
    nothing else changes."""
    from . import pilot_input as PIN
    end = "and values that a database would not store."
    assert PIN.INSTRUCTION_V2.count(end) == 1
    return PIN.INSTRUCTION_V2.replace(end, end + " " + PIN.CUE_LINE)


def render_a_cue(text):
    """The A prompt `text` (pilot_input.render_v2, any order) with the cue line added to its instruction."""
    from . import pilot_input as PIN
    if not text.startswith(PIN.INSTRUCTION_V2):
        raise ValueError("not an INSTRUCTION_V2 prompt")
    return a_cue_instruction() + text[len(PIN.INSTRUCTION_V2):]


def schema_a_cue(schema):
    """Copy of an A schema (pilot_input.schema_v2) whose cluster `attribute` says it may also be "attribute_cue"; the
    property is a free string in v2 already, so only its description changes (the parser accepts attribute_cue)."""
    import copy
    out = copy.deepcopy(schema)
    prop = out["properties"]["clusters"]["items"]["properties"]["attribute"]
    prop["description"] = 'a listed attribute name, "not_attribute" or "attribute_cue"'
    return out



def parse_a_cue(raw, schema):
    """(obj, errors, n clusters) of an A-cue response: llm_cache.parse_job format v2 without the error for a cluster whose
    attribute is "attribute_cue" (the label of a question phrase; it is not in the attribute list on purpose)."""
    obj, errs, n = LC.parse_job(raw, "v2", schema)
    cue = {f"clusters[{i}] attribute {LC.ATTRIBUTE_CUE!r} not in the attribute list"
           for i, c in enumerate(obj.get("clusters") or []) if isinstance(c, dict) and c.get("attribute") == LC.ATTRIBUTE_CUE}
    return obj, [e for e in errs if e not in cue], n


def parse_job(raw, fmt, schema, family=""):
    """llm_cache.parse_job, except that the a_cue family is read by parse_a_cue (the notebook calls this)."""
    return parse_a_cue(raw, schema) if family == "a_cue" else LC.parse_job(raw, fmt, schema)
