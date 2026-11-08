"""wf_v4.1 task 5 (diary): contamination probe. Ask the model, with no dialogues, for the schema of MultiWOZ (the prompt names the dataset on
purpose), then score the answer against the schema GT with the Step-4 scorer. Pure functions; files are read only in `build` and `load_answer`.

Prompt: config/wf_v41_contamination_prompt.txt (+ .schema.json = the schema of the dialogues-only prompt (e), kept equal to
step4_prompts.build_prompt_e by a test). The answer has the (e) shape, so step4_sql.from_e makes the canonical schema.
Column mapping to the GT (the answer has no Step-3 sources): the table name gives the entity (first word, a trailing "s" cut; "taxi",
"hotel_booking", ...); the column name is compared as letters and digits only, with and without the entity word in front, against the GT
column name without its entity word and against the full GT name (ALIASES covers a few MultiWOZ spellings; in a table with "book" in its
name a bare "day" / "people" / "stay" / "time" / "reference" also tries "requested ..." / "confirmed reference"). A GT column is used once
per output table; unmatched columns keep gt = None and are reported.
"""
import json
import re
from pathlib import Path

from . import step4_score as SC
from .step4_gt import norm
from .step4_prompts import TYPES, _JSON_ONLY, build_prompt_e, validate_e
from .step4_sql import from_e

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "config" / "wf_v41_contamination_prompt.txt"
SCHEMA = ROOT / "config" / "wf_v41_contamination_prompt.schema.json"
ENTITIES = ("train", "hotel", "restaurant", "taxi", "attraction")
ALIASES = {"ref": "confirmedreference", "reference": "confirmedreference", "refnumber": "confirmedreference",
           "referencenumber": "confirmedreference", "bookday": "requestedday", "bookpeople": "requestedpeople",
           "booktime": "requestedtime", "bookstay": "requestedstay", "openinghours": "openhours", "id": "trainid"}  # "id" only in train
BOOK_PREFIX = {"day": "requestedday", "people": "requestedpeople", "stay": "requestedstay", "time": "requestedtime",
               "reference": "confirmedreference", "ref": "confirmedreference"}


def build():
    """(prompt text, JSON schema) of the probe."""
    text = PROMPT.read_text(encoding="utf-8").format(types=", ".join(TYPES), json_only=_JSON_ONLY)
    return text, json.loads(SCHEMA.read_text(encoding="utf-8"))


def schema_from_prompt_e():
    """The (e) answer schema, the source of SCHEMA (a test keeps the two equal)."""
    return build_prompt_e("")[1]


def key(s):
    """Letters and digits only, lower case ("Price range" -> "pricerange", "leaveAt" -> "leaveat")."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def entity_of(table_name):
    """Entity of an output table: its first word (a trailing "s" cut) if it is a MultiWOZ domain, else None."""
    words = re.split(r"[^a-z0-9]+", norm(table_name).replace("_", " ")) if table_name else [""]
    first = words[0].rstrip("s")
    return next((e for e in ENTITIES if first == e.rstrip("s")), None)


def _keys(entity, table_name, column):
    """Candidate GT keys of an output column (see the module doc), most specific first."""
    k = key(column)
    stripped = k[len(entity):] if entity and k.startswith(entity) and len(k) > len(entity) else k
    own = (k, stripped)
    cand = [k, stripped]
    if "book" in key(table_name):
        cand += [BOOK_PREFIX[x] for x in own if x in BOOK_PREFIX]
    cand += [ALIASES[x] for x in own if x in ALIASES and (x != "id" or entity == "train")]
    return [c for i, c in enumerate(cand) if c and c not in cand[:i]]


def gt_index(gt):
    """{entity: {key: GT name}}: keys = the GT name without its entity word and the full GT name, both as letters and digits only; main design,
    added columns (booking ids) included."""
    out = {}
    for t in gt["tables"].values():
        idx = out.setdefault(t["entity"], {})
        for c in t["columns"]:
            full = key(c["name"])
            idx.setdefault(full, c["name"])
            idx.setdefault(full[len(t["entity"]):] if full.startswith(t["entity"]) else full, c["name"])
    return out


def map_to_gt(schema, gt):
    """(schema with `gt` set on the matched columns, unmatched [(table, column)]). The input is not changed."""
    index = gt_index(gt)
    out, unmatched = json.loads(json.dumps(schema)), []
    for t in out["tables"]:
        ent, used = entity_of(t["name"]), set()
        for c in t["columns"]:
            by = index.get(ent, {})
            hit = next((by[k] for k in _keys(ent, t["name"], c["name"]) if k in by and by[k] not in used), None)
            if hit:
                c["gt"] = hit
                used.add(hit)
            else:
                unmatched.append((t["name"], c["name"]))
    return out, unmatched


def gt_columns(gt):
    """Names of the GT columns an answer can name: the main design's columns without the 'added' ones (booking ids, the taxi ride id)."""
    return {c["name"] for t in gt["tables"].values() for c in t["columns"] if c["source"] != "added"}


def score_answer(answer, gt, set_name="dev50"):
    """dict of the probe's scores: the step4_score result of the full GT (best design), GT tables named, GT columns named (k/n), the
    unmatched columns, the (e) validation errors."""
    errors = validate_e(answer)
    canon, unmatched = map_to_gt(from_e(answer), gt)
    res = SC.score(canon, gt, set_name)
    names = gt_columns(gt)
    named = {c["gt"] for t in canon["tables"] for c in t["columns"] if c["gt"]} & names
    return {"result": res, "tables_named": res["metrics"]["table_recall"], "columns_named": SC.share(len(named), len(names)),
            "unmatched": unmatched, "errors": errors, "n_answer_tables": len(canon["tables"]),
            "n_answer_columns": sum(len(t["columns"]) for t in canon["tables"])}


def flat(sc):
    """One CSV row of score_answer."""
    row = SC.flat(sc["result"])
    named = sc["columns_named"]
    row.update(columns_named_k=named["k"], columns_named_n=named["n"], columns_named=named["share"],
               answer_tables=sc["n_answer_tables"], answer_columns=sc["n_answer_columns"],
               unmatched_columns=len(sc["unmatched"]), validation_errors=len(sc["errors"]))
    return row


def _fmt(s):
    return f"{s['k']}/{s['n']} ({s['share']:.3f})" if s["n"] else f"{s['k']}/0 (n/a)"


def report_md(sc):
    m = sc["result"]["metrics"]
    lines = ["# wf_v4.1 contamination probe: MultiWOZ schema from memory (no dialogues)", "",
             f"Scored against the full schema GT, best design `{sc['result']['design']}` (step4_score, no reachability filter).", "",
             f"- GT tables named: {_fmt(sc['tables_named'])}; the answer has {sc['n_answer_tables']} tables, table precision {_fmt(m['table_precision'])}",
             f"- GT columns named: {_fmt(sc['columns_named'])} (GT columns without the added ids); the answer has {sc['n_answer_columns']} columns",
             f"- Grouping F1 (named columns in the right table): {'n/a (no GT column named)' if m['grouping_f1'] is None else format(m['grouping_f1'], '.3f')} (precision {_fmt(m['grouping_precision'])}, "
             f"recall {_fmt(m['grouping_recall'])}; {_fmt(m['gt_columns_placed'])} GT columns placed)",
             f"- Primary keys right (rule b, the default since diary Nov 7 task 5): {_fmt(m['pk_right_b'])}; rule (a): {_fmt(m['pk_right'])}",
             f"- Relationships: precision {_fmt(m['rel_precision'])}, recall {_fmt(m['rel_recall'])}, direction {_fmt(m['rel_direction'])}",
             f"- Types right: {_fmt(m['types_right'])}", ""]
    if sc["errors"]:
        lines += ["Validation errors of the answer: " + "; ".join(sc["errors"][:10]), ""]
    lines += [f"Unmatched answer columns ({len(sc['unmatched'])}; no GT column, counted as new): "
              + (", ".join(f"{t}.{c}" for t, c in sc["unmatched"]) or "none")]
    return "\n".join(lines) + "\n"


def load_answer(path):
    """Answer dict from a JSON file, or the first line of a .jsonl; a record with a "parsed" field gives that field."""
    text = Path(path).read_text(encoding="utf-8").strip()
    obj = json.loads(text.splitlines()[0] if str(path).endswith(".jsonl") else text)
    return obj["parsed"] if "parsed" in obj else obj
