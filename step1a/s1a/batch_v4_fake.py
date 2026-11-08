"""A fake model for the wf_v4 batch (tests and the laptop dry run): a valid answer for every job, derived from the job's prompt and schema.

One group per heading with all its columns, table names from the headings, no relationships, new key columns, every column typed text; (e):
one table; placement: P1 into the first table. `respond(job, prompt, schema)` returns the raw JSON text; `run_jobs(out, jobs)` writes the
response rows like the notebook (llm_cache.parse_job on the raw text), so the stage builders can read them.
"""
import json
import re
from pathlib import Path

from . import llm_cache as LC
from .pilot_input import est_tokens


def _uniq(name, used):
    base, n = name, 2
    while name in used:
        name, n = f"{base}_{n}", n + 1
    used.add(name)
    return name


def respond(job, prompt, schema):
    fam = job["family"]
    if fam == "s4_41":
        ids = schema["properties"]["groups"]["items"]["properties"]["columns"]["items"]["enum"]
        groups = {}
        for i in ids:
            groups.setdefault(i.split(":")[0], []).append(i)
        return json.dumps({"groups": [{"group": f"G{k}", "columns": cols, "note": f"all columns of {e}"} for k, (e, cols) in enumerate(groups.items(), 1)],
                           "unused": [], "duplicate_flags": []})
    if fam == "s4_42":
        used, tables = set(), []
        for g in re.finditer(r"^(G\d+)[^\n]*:\n\[(\w+):", prompt, re.M):
            name = _uniq(g.group(2), used)
            tables.append({"group": g.group(1), "name": name, "description": f"The {name} table.", "row": f"one {name}"})
        return json.dumps({"tables": tables})
    if fam == "s4_43":
        return json.dumps({"relationships": [], "new_tables": []})
    if fam == "s4_44":
        tables, cur = [], None
        for line in prompt.split("Relationships (from = refers to")[0].splitlines():
            m = re.match(r"^Table (\S+): ", line)
            if m:
                cur = {"name": m.group(1), "primary_key": "new", "new_id_name": f"{m.group(1)} key", "columns": [], "foreign_keys": []}
                tables.append(cur)
                continue
            m = re.match(r"^\[(\S+:\d+)\] (.*)$", line)
            if m and cur is not None:
                names = {c["name"] for c in cur["columns"]}
                cur["columns"].append({"column": m.group(1), "name": _uniq(m.group(2), names), "type": "text"})
        return json.dumps({"tables": tables})
    if fam == "s4_e":
        return json.dumps({"tables": [{"name": "item", "description": "An item.", "row": "one item", "primary_key": ["item id"],
                                       "columns": [{"name": "item id", "type": "id"}, {"name": "item name", "type": "text"}],
                                       "foreign_keys": []}], "relationships": []})
    if fam == "s4_place":
        first = schema["properties"]["target_table"]["enum"][0]
        return json.dumps({"reason": "fake", "option": "P1", "target_table": first, "new_table": None, "link": None})
    raise ValueError(f"unknown family {fam!r}")


def run_jobs(out, jobs, root=None, model=respond, parse=None):
    """Write one response row per job under <out>/responses (the notebook's row fields); returns the number of parse errors.
    `model(job, prompt, schema) -> raw` is this fake by default (wf_v4.1: gemini_v41.responder for the dry runs; its `.last` metadata goes
    into the row, marked DRY RUN); `parse(raw, job, schema) -> (parsed, errors)` defaults to llm_cache.parse_job."""
    out, bad = Path(out), 0
    for job in jobs:
        prompt = (out / job["prompt"]).read_text(encoding="utf-8")
        schema = json.loads((out / job["schema"]).read_text(encoding="utf-8"))
        raw = model(job, prompt, schema)
        parsed, errors = parse(raw, job, schema) if parse else LC.parse_job(raw, job["format"], schema)[:2]
        bad += bool(errors)
        meta = getattr(model, "last", None) or {}
        row = {"job": job["job"], "format": job["format"], "run_tag": job["run_tag"], "guided": meta.get("guided", True),
               "finish_reason": meta.get("finish_reason", "stop"), "raw": raw, "parsed": parsed, "errors": errors,
               "prompt_tokens": meta.get("prompt_tokens") or est_tokens(prompt), "output_tokens": meta.get("output_tokens") or est_tokens(raw)}
        if meta:
            row.update(model=meta.get("model"), dry_run="DRY RUN, not a result", thinking_tokens=meta.get("thinking_tokens"))
        LC.put(out / "responses" / f"{job['job']}.jsonl", job["job"] + job["run_tag"], row)
    return bad
