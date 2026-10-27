"""JSONL response cache and output parser for the Loop-1 LLM runs (schema: LOOP1_CONTRACT.md "LLM output")."""
import hashlib
import json
import re
from pathlib import Path

VALUE_TYPES = ["time", "day", "number", "name", "code", "other"]
ACTIONS = ["keep", "merge", "split", "not_attribute", "unsure"]
STR_KEYS = ["cluster_id", "name", "description", "placement", "evidence"]
REQUIRED = STR_KEYS + ["value_type", "action", "merge_with", "split"]

_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        **{k: {"type": "string"} for k in STR_KEYS},
        "value_type": {"enum": VALUE_TYPES},
        "action": {"enum": ACTIONS},
        "merge_with": {"type": "array", "items": {"type": "string"}},
        "split": {"type": "array", "items": {
            "type": "object",
            "properties": {"name": {"type": "string"},
                           "examples": {"type": "array", "items": {"type": "string"}}},
            "required": ["name", "examples"]}},
    },
    "required": REQUIRED,
}
ARRAY_SCHEMA = {"type": "array", "items": _ITEM_SCHEMA}  # for JSON-guided decoding


def key(model, params, prompt, run_tag):
    """sha256 over (model, params, prompt, run_tag); params is a JSON-able dict."""
    blob = json.dumps([model, params, prompt, run_tag], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def get(path, k):
    """Row cached under key `k` in the JSONL file `path`, or None."""
    p = Path(path)
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("key") == k:
                return row
    return None


def put(path, k, row):
    """Append `row` (stored with its key) to the JSONL file `path`."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"key": k, **row}, ensure_ascii=False) + "\n")


def _extract_array(raw):
    """Parse the single JSON array in `raw`, tolerating fences and surrounding text."""
    text = re.sub(r"```(?:json)?", "", raw)
    dec = json.JSONDecoder()
    for m in re.finditer(r"\[", text):
        try:
            val, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if isinstance(val, list):
            return val
    raise ValueError("no JSON array found")


def _check(obj, i):
    if not isinstance(obj, dict):
        return [f"[{i}] not an object"]
    errs = [f"[{i}] missing key {k}" for k in REQUIRED if k not in obj]
    for k in STR_KEYS:
        if k in obj and not isinstance(obj[k], str):
            errs.append(f"[{i}] {k} not a string")
    if "value_type" in obj and obj["value_type"] not in VALUE_TYPES:
        errs.append(f"[{i}] bad value_type {obj['value_type']!r}")
    if "action" in obj and obj["action"] not in ACTIONS:
        errs.append(f"[{i}] bad action {obj['action']!r}")
    if "merge_with" in obj and not (isinstance(obj["merge_with"], list)
                                    and all(isinstance(x, str) for x in obj["merge_with"])):
        errs.append(f"[{i}] merge_with not a list of strings")
    if "split" in obj:
        sp = obj["split"]
        if not (isinstance(sp, list) and all(
                isinstance(s, dict) and isinstance(s.get("name"), str)
                and isinstance(s.get("examples"), list) for s in sp)):
            errs.append(f"[{i}] split not a list of {{name, examples}}")
    return errs


def parse_response(raw):
    """(objects, errors): the JSON array in `raw`, each object checked against the contract schema."""
    try:
        arr = _extract_array(raw)
    except ValueError as e:
        return [], [str(e)]
    errors = [e for i, o in enumerate(arr) for e in _check(o, i)]
    return arr, errors
