"""wf_v4.4 (diary Nov 14) T2: keyed "exactly once" split pass for Llama-3.1-8B (v4.3: 41/54 frozen split answers did not parse).

The frozen split answer is {cluster_id, is_mixed, parts: [{name, role, examples: [ids]}]}; llm_cache.parse_split fails when Llama
repeats an example id or invents one. Here the examples become a keyed object with one required key per example id (as option B,
keyed_v42), so guided decoding cannot repeat or skip an id:
  {"is_mixed": bool, "parts": [{"name", "role"}] (at most 4), "examples": {"<example id>": "P1".."P4"}}
`P<k>` is the k-th entry of `parts`. unkey_split() turns an answer back into the frozen format, so the frozen readers
(pilot_verify.load_split_results, batch_build_v39 split_roles, reconcile, dupcheck) run unchanged.
The prompt keeps the frozen text (intro, cluster block, examples) and only replaces the answer-format paragraph.
Jobs run with format "judge" (plain JSON, the retry rule fires on invalid JSON as for the names jobs); the keyed checks are in
unkey_split(), and assemble_split() writes the frozen-format answers under the frozen job names.
"""
import json
import re
from pathlib import Path

from . import batch_v4 as B
from . import llm_cache as LC

MARK = "split_keyed_v44"
PARTS_MAX = 4
PART_IDS = tuple(f"P{i}" for i in range(1, PARTS_MAX + 1))
NAME_MAX, ROLE_MAX = 60, 150
FAMILY = "splitk"
_FORMAT_BLOCK = re.compile(r"If it does mix, give the parts.*?(?=\n\nCluster )", re.S)


def keyed_schema(ex_ids):
    """Guided schema: is_mixed, a short parts list, and one required part reference per example id (no other keys)."""
    part = {"type": "object", "properties": {"name": {"type": "string", "maxLength": NAME_MAX},
                                             "role": {"type": "string", "maxLength": ROLE_MAX}},
            "required": ["name", "role"], "additionalProperties": False}
    ex = {"type": "object", "properties": {e: {"type": "string", "enum": list(PART_IDS)} for e in ex_ids},
          "required": list(ex_ids), "additionalProperties": False}
    return {"type": "object", "title": MARK,
            "properties": {"is_mixed": {"type": "boolean"}, "parts": {"type": "array", "items": part, "maxItems": PARTS_MAX}, "examples": ex},
            "required": ["is_mixed", "parts", "examples"], "additionalProperties": False}


def keyed_prompt(frozen_text, ex_ids):
    """The frozen split prompt with its answer-format paragraph replaced by the keyed one (everything else is copied)."""
    shape = ", ".join(f'"{e}": "P{i % 2 + 1}"' for i, e in enumerate(ex_ids[:2]))
    new = (f"If it does mix, list the parts (at most {PARTS_MAX}): for each part a snake_case name and a short role. Then give every\n"
           f"example the number of the part it belongs to (P1 for the first part, P2 for the second, and so on). Every example gets\n"
           f"exactly one part. If it does not mix, give is_mixed false, no parts, and P1 for every example.\n"
           f"Return ONLY one JSON object, nothing before or after it:\n"
           f'{{"is_mixed": true,\n "parts": [{{"name": "str", "role": "str"}}],\n "examples": {{{shape}}}}}')
    text, n = _FORMAT_BLOCK.subn(lambda _: new, frozen_text, count=1)
    if n != 1:
        raise ValueError("not a frozen split prompt (no answer-format paragraph)")
    return text


def _load(raw):
    try:
        return LC._extract_json(raw, "{", dict), None
    except (ValueError, TypeError) as e:
        return None, str(e)


def unkey_split(raw, cluster_id, ex_ids):
    """(frozen-format object, errors) of a keyed split answer. An answer already in the frozen format (an unguided retry may give one)
    is only checked by the frozen parser. Keyed errors: not a JSON object, examples not an object, missing / unknown example ids, a
    part reference that is not P1..P4 or (when parts are listed) points past them. Parts without examples are dropped; fewer than two parts left
    means not mixed (a one-part split changes nothing)."""
    obj, err = _load(raw)
    if obj is None:
        return {}, [err]
    parts = obj.get("parts")
    if isinstance(parts, list) and any(isinstance(p, dict) and "examples" in p for p in parts):
        return LC.parse_split(raw, ex_ids)
    ex = obj.get("examples")
    if not isinstance(ex, dict):
        return {}, ["examples missing or not an object"]
    errs = [f"missing example {e}" for e in ex_ids if e not in ex] + [f"unknown example {k!r}" for k in ex if k not in set(ex_ids)]
    if not isinstance(parts, list):
        errs.append("parts missing or not a list")
        parts = []
    got = [p if isinstance(p, dict) else {} for p in parts]
    out = []
    for i, p in enumerate(got, 1):
        mine = [e for e in ex_ids if ex.get(e) == f"P{i}"]
        if mine:
            out.append({"name": str(p.get("name") or ""), "role": str(p.get("role") or ""), "examples": mine})
    for e in ex_ids:
        v = ex.get(e)
        if e in ex and (v not in PART_IDS or (got and int(v[1:]) > len(got))):
            errs.append(f"example {e}: part {v!r} is not a listed part")
    mixed = obj.get("is_mixed")
    if not isinstance(mixed, bool):
        errs.append("is_mixed missing or not a boolean")
    mixed = bool(mixed) and len(out) >= 2
    frozen = {"cluster_id": cluster_id, "is_mixed": mixed, "parts": out if mixed else []}
    return frozen, errs + LC.parse_split(json.dumps(frozen), ex_ids)[1]


def split_jobs(out, frozen_rows):
    """Write the keyed prompt + schema of every frozen split row (step3_post_v43.copy_split_jobs rows, files already in `out`) and return
    the keyed job rows (family "splitk", frozen_job = the frozen job name the assembled answer is written under)."""
    out, rows = Path(out), []
    for fr in frozen_rows:
        frozen_schema = json.loads((out / fr["schema"]).read_text(encoding="utf-8"))
        ex_ids = LC.schema_enum(frozen_schema, "examples") or []
        name = fr["job"].replace("_split_", "_splitk_")
        B.write(out / "prompts" / f"{name}.txt", keyed_prompt((out / fr["prompt"]).read_text(encoding="utf-8"), ex_ids))
        B.write_json(out / "prompts" / f"{name}.schema.json", keyed_schema(ex_ids))
        rows.append({**fr, "job": name, "family": FAMILY, "format": "judge", "format44": "split_keyed", "frozen_job": fr["job"],
                     "example_ids": ex_ids, "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json"})
    B.write_json(out / "manifest_split44.json", {"stage": 0, "jobs": rows})
    return rows


def read_split_jobs(out):
    return B.read_json(Path(out) / "manifest_split44.json")["jobs"]


def assemble_split(out):
    """Write the frozen-format answer of every keyed split job to responses/<frozen job>.jsonl (rewritten on every call; one row, marked
    "assembled"). Returns {jobs, answered, parse_errors (final answers with any error), retried, errors: [(job, [..])]}."""
    out, res = Path(out), {"jobs": 0, "answered": 0, "parse_errors": 0, "retried": 0, "errors": []}
    for j in read_split_jobs(out):
        res["jobs"] += 1
        last = B.last_row(out / "responses" / f"{j['job']}.jsonl")
        if last is None:
            continue
        res["answered"] += 1
        res["retried"] += bool(last.get("retried"))
        obj, errs = unkey_split(last.get("raw") or "", j["cluster_id"], j["example_ids"])
        errs = list(last.get("errors") or []) + [e for e in errs if e not in (last.get("errors") or [])]
        res["parse_errors"] += bool(errs)
        res["errors"] += [(j["job"], errs)] if errs else []
        row = {"key": j["frozen_job"] + j["run_tag"], "job": j["frozen_job"], "format": "split", "run_tag": j["run_tag"], "guided": last.get("guided"),
               "finish_reason": last.get("finish_reason"), "raw": json.dumps(obj, ensure_ascii=False), "parsed": obj, "errors": errs,
               "assembled": True, "from_job": j["job"]}
        p = out / "responses" / f"{j['frozen_job']}.jsonl"
        p.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return res


def fake_answer(schema, cluster_id):
    """Valid keyed answer for the laptop fake model: every other cluster is split in two halves (as FakeStep3 does)."""
    import zlib
    ex = list(schema["properties"]["examples"]["properties"])
    mixed = len(ex) >= 4 and zlib.crc32(cluster_id.encode()) % 2 == 0
    h = len(ex) // 2
    return json.dumps({"is_mixed": mixed,
                       "parts": [{"name": "fake_part_a", "role": "first"}, {"name": "fake_part_b", "role": "second"}] if mixed else [],
                       "examples": {e: ("P1" if (i < h or not mixed) else "P2") for i, e in enumerate(ex)}})


def summary(res):
    return {k: res[k] for k in ("jobs", "answered", "parse_errors", "retried")} | {"target": "<= 5 of 54"}

