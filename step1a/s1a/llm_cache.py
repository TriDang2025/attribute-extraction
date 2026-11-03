"""JSONL response cache and output parser for the Loop-1 LLM runs (schema: LOOP1_CONTRACT.md "LLM output")."""
import hashlib
import json
import re
from pathlib import Path

VALUE_TYPES = ["time", "day", "number", "name", "code", "other"]
ACTIONS = ["keep", "merge", "split", "not_attribute", "unsure"]
STR_KEYS = ["cluster_id", "name", "description", "placement", "evidence"]
REQUIRED = STR_KEYS + ["value_type", "action", "merge_with", "split"]
NOT_ATTRIBUTE = "not_attribute"
ATTRIBUTE_CUE = "attribute_cue"

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


def _extract_json(raw, opener, typ):
    """First JSON value of type `typ` that starts at an `opener` in `raw`, tolerating fences and surrounding text."""
    text = re.sub(r"```(?:json)?", "", raw)
    dec = json.JSONDecoder()
    for m in re.finditer(re.escape(opener), text):
        try:
            val, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if isinstance(val, typ):
            return val
    raise ValueError("no JSON array found" if typ is list else "no JSON object found")


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
        arr = _extract_json(raw, "[", list)
    except ValueError as e:
        return [], [str(e)]
    errors = [e for i, o in enumerate(arr) for e in _check(o, i)]
    return arr, errors


def parse_v1_enum(raw, cluster_ids, options):
    """Like parse_response, plus enum errors: unknown cluster_id / merge_with id, placement not in `options`.
    `cluster_ids` / `options` None skips that check."""
    arr, errors = parse_response(raw)
    ids = None if cluster_ids is None else set(cluster_ids)
    opts = None if options is None else set(options)
    for i, o in enumerate(arr):
        if not isinstance(o, dict):
            continue
        if ids is not None and isinstance(o.get("cluster_id"), str) and o["cluster_id"] not in ids:
            errors.append(f"[{i}] unknown cluster_id {o['cluster_id']!r}")
        mw = o.get("merge_with")
        if ids is not None and isinstance(mw, list):
            errors += [f"[{i}] unknown merge_with id {x!r}" for x in mw if isinstance(x, str) and x not in ids]
        if opts is not None and isinstance(o.get("placement"), str) and o["placement"] not in opts:
            errors.append(f"[{i}] bad placement {o['placement']!r}")
    return arr, errors


def parse_response_v2(raw, cluster_ids, attribute_names_check=True):
    """(obj, errors) for output format v2: {"attributes": [...], "clusters": [...]} (PILOT_V31_CONTRACT.md)."""
    try:
        obj = _extract_json(raw, "{", dict)
    except ValueError as e:
        return {}, [str(e)]
    errors, names = [], set()
    attrs, clusters = obj.get("attributes"), obj.get("clusters")
    if not isinstance(attrs, list):
        errors.append("attributes missing or not a list")
        attrs = []
    for i, a in enumerate(attrs):
        if not (isinstance(a, dict) and isinstance(a.get("name"), str)):
            errors.append(f"attributes[{i}] not an object with a string name")
            continue
        errors += [f"attributes[{i}] {k} not a string" for k in ("description", "role")
                   if not isinstance(a.get(k), str)]
        if a["name"] in names:
            errors.append(f"duplicate attribute name {a['name']!r}")
        names.add(a["name"])
    if not isinstance(clusters, list):
        errors.append("clusters missing or not a list")
        clusters = []
    ids, seen = set(cluster_ids), set()
    for i, c in enumerate(clusters):
        if not isinstance(c, dict):
            errors.append(f"clusters[{i}] not an object")
            continue
        errors += [f"clusters[{i}] {k} not a string" for k in ("cluster_id", "attribute", "evidence", "placement")
                   if not isinstance(c.get(k), str)]
        if not isinstance(c.get("mixed"), bool):
            errors.append(f"clusters[{i}] mixed not a boolean")
        cid = c.get("cluster_id")
        if isinstance(cid, str):
            if cid not in ids:
                errors.append(f"clusters[{i}] unknown cluster_id {cid!r}")
            elif cid in seen:
                errors.append(f"duplicate cluster_id {cid!r}")
            seen.add(cid)
        at = c.get("attribute")
        if attribute_names_check and isinstance(at, str) and at != NOT_ATTRIBUTE and at not in names:
            errors.append(f"clusters[{i}] attribute {at!r} not in the attribute list")
    errors += [f"missing cluster_id {cid!r}" for cid in cluster_ids if cid not in seen]
    return obj, errors


def _name_key(name):
    return re.sub(r"[\s_\-]+", " ", str(name or "").lower()).strip()


def repair_undeclared(obj):
    """(obj, repaired_names) for a format-v2/v3 object: every cluster attribute that is neither `not_attribute` /
    `attribute_cue` nor in `attributes` is appended to `attributes` as {name, description "", role "", repaired true}
    (first-seen order). Names compare as in pilot_verify.norm_name (case, `_`, `-`, space equal), so a name that only
    differs in spelling of the separators is not repaired. Returns a copy; `obj` is not changed. Not an object:
    returned as is."""
    if not isinstance(obj, dict):
        return obj, []
    attrs = [a for a in obj.get("attributes") or []]
    names = {_name_key(a.get("name")) for a in attrs if isinstance(a, dict)}
    added = []
    for c in obj.get("clusters") or []:
        at = c.get("attribute") if isinstance(c, dict) else None
        if isinstance(at, str) and _name_key(at) not in names | {_name_key(NOT_ATTRIBUTE), _name_key(ATTRIBUTE_CUE)}:
            names.add(_name_key(at))
            added.append(at)
    fixed = {**obj, "attributes": attrs + [{"name": n, "description": "", "role": "", "repaired": True} for n in added]}
    return fixed, added


def parse_split(raw, ex_ids):
    """(obj, errors) for the split format: {cluster_id, is_mixed, parts: [{name, role, examples}]}."""
    try:
        obj = _extract_json(raw, "{", dict)
    except ValueError as e:
        return {}, [str(e)]
    errors = []
    if not isinstance(obj.get("cluster_id"), str):
        errors.append("cluster_id missing or not a string")
    if not isinstance(obj.get("is_mixed"), bool):
        errors.append("is_mixed missing or not a boolean")
    parts = obj.get("parts")
    if not isinstance(parts, list):
        errors.append("parts missing or not a list")
        parts = []
    ids, seen = set(ex_ids), set()
    for i, p in enumerate(parts):
        if not (isinstance(p, dict) and isinstance(p.get("name"), str) and isinstance(p.get("examples"), list)):
            errors.append(f"parts[{i}] not {{name, examples}}")
            continue
        for x in p["examples"]:
            if x not in ids:
                errors.append(f"parts[{i}] unknown example {x!r}")
            elif x in seen:
                errors.append(f"example {x!r} used more than once")
            seen.add(x)
    return obj, errors


def schema_enum(schema, name):
    """Enum list of property `name` (or of its array items) anywhere in a JSON schema, or None."""
    if isinstance(schema, dict):
        prop = (schema.get("properties") or {}).get(name)
        if isinstance(prop, dict):
            for node in (prop, prop.get("items")):
                if isinstance(node, dict) and isinstance(node.get("enum"), list):
                    return node["enum"]
        for v in schema.values():
            found = schema_enum(v, name)
            if found is not None:
                return found
    elif isinstance(schema, list):
        for v in schema:
            found = schema_enum(v, name)
            if found is not None:
                return found
    return None


NOISE_VERDICTS = ["attribute", "noise", "unsure"]


def _obj_errors(raw, str_keys, extra):
    """(obj, errors) for a single JSON object: `str_keys` must be strings; `extra(obj, errors)` adds format checks."""
    try:
        obj = _extract_json(raw, "{", dict)
    except ValueError as e:
        return {}, [str(e)]
    errors = []
    for k in str_keys:
        if k not in obj:
            errors.append(f"missing key {k}")
        elif not isinstance(obj[k], str):
            errors.append(f"{k} not a string")
    extra(obj, errors)
    return obj, errors


def _enum_check(obj, errors, key, allowed):
    if allowed is not None and isinstance(obj.get(key), str) and obj[key] not in allowed:
        errors.append(f"bad {key} {obj[key]!r}")


def parse_response_v3(raw, cluster_ids):
    """(obj, errors) for output format v3: v2 plus a string `reason` on every cluster object."""
    obj, errors = parse_response_v2(raw, cluster_ids)
    for i, c in enumerate(obj.get("clusters") or []):
        if isinstance(c, dict) and not isinstance(c.get("reason"), str):
            errors.append(f"clusters[{i}] reason missing or not a string")
    return obj, errors


def parse_noise(raw, cluster_ids=None, verdicts=NOISE_VERDICTS):
    """(obj, errors) for the noise probe: {cluster_id, reason, verdict, name}; None skips an enum check."""
    def extra(obj, errors):
        _enum_check(obj, errors, "cluster_id", None if cluster_ids is None else set(cluster_ids))
        _enum_check(obj, errors, "verdict", verdicts)
    return _obj_errors(raw, ["cluster_id", "reason", "verdict", "name"], extra)


def parse_gate(raw, cluster_ids=None):
    """(obj, errors) for the coherence gate: {cluster_id, summary, coherent}."""
    def extra(obj, errors):
        _enum_check(obj, errors, "cluster_id", None if cluster_ids is None else set(cluster_ids))
        if not isinstance(obj.get("coherent"), bool):
            errors.append("coherent missing or not a boolean")
    return _obj_errors(raw, ["cluster_id", "summary"], extra)


def parse_reconcile(raw, unit_ids=None, candidates=None):
    """(obj, errors) for reconcile: {unit_id, reason, same_as}; same_as is a candidate name or "none"."""
    def extra(obj, errors):
        _enum_check(obj, errors, "unit_id", None if unit_ids is None else set(unit_ids))
        _enum_check(obj, errors, "same_as", None if candidates is None else set(candidates))
    return _obj_errors(raw, ["unit_id", "reason", "same_as"], extra)


def parse_baseline(raw):
    """(obj, errors) for the LLM-only baseline (wf_v3.7): {"attributes": [{name, description}]}, every entry strings."""
    def extra(obj, errors):
        att = obj.get("attributes")
        if not isinstance(att, list):
            errors.append("attributes missing or not a list")
            return
        errors += [f"attributes[{i}] needs string name and description" for i, a in enumerate(att)
                   if not (isinstance(a, dict) and isinstance(a.get("name"), str) and isinstance(a.get("description"), str))]
    return _obj_errors(raw, [], extra)


def token_fields(out, batch_seconds, batch_size):
    """Token stats of one vLLM RequestOutput for a response row (PILOT_V32_CONTRACT.md "Token stats")."""
    return {"prompt_tokens": len(out.prompt_token_ids), "output_tokens": len(out.outputs[0].token_ids),
            "batch_seconds": round(float(batch_seconds), 2), "batch_size": int(batch_size)}


def parse_dupcheck(raw, column_ids=None):
    """(obj, errors) for the wf_v3.8 duplicate check: {"joins": [{"columns": [id, ...], "reason": str}]}; every join has
    >= 2 distinct ids (from `column_ids` when given) and a string reason."""
    def extra(obj, errors):
        joins = obj.get("joins")
        if not isinstance(joins, list):
            errors.append("joins missing or not a list")
            return
        allowed = None if column_ids is None else set(column_ids)
        for i, j in enumerate(joins):
            cols = j.get("columns") if isinstance(j, dict) else None
            if not isinstance(cols, list) or len({str(c) for c in cols}) < 2:
                errors.append(f"joins[{i}] needs a list of >= 2 distinct columns")
            elif allowed is not None and any(not isinstance(c, int) or c not in allowed for c in cols):
                errors.append(f"joins[{i}] unknown column id")
            if not (isinstance(j, dict) and isinstance(j.get("reason"), str)):
                errors.append(f"joins[{i}] reason missing or not a string")
    return _obj_errors(raw, [], extra)


def parse_evidence(raw, example_ids=None):
    """(obj, errors) for the wf_v3.8 example / neighbour check: {"answers": [{"id": int, "fits": "yes"|"no"}]}; one answer per
    id of `example_ids` when given (none missing, none twice, none unknown)."""
    def extra(obj, errors):
        ans = obj.get("answers")
        if not isinstance(ans, list):
            errors.append("answers missing or not a list")
            return
        seen = []
        for i, a in enumerate(ans):
            if not (isinstance(a, dict) and a.get("fits") in ("yes", "no") and isinstance(a.get("id"), int)):
                errors.append(f"answers[{i}] needs an integer id and fits yes|no")
                continue
            if example_ids is not None and a["id"] not in example_ids:
                errors.append(f"answers[{i}] unknown id {a['id']}")
            elif a["id"] in seen:
                errors.append(f"id {a['id']} answered more than once")
            seen.append(a["id"])
        if example_ids is not None:
            errors += [f"id {x} not answered" for x in example_ids if x not in seen]
    return _obj_errors(raw, [], extra)


def parse_job(raw, fmt, schema):
    """(parsed, errors, n_objects) for a manifest job of format v1 | v2 | v3 | split | noise | gate | reconcile | baseline | dupcheck | evidence;
    enums come from the job's schema."""
    if fmt == "v1":
        parsed, errs = parse_v1_enum(raw, schema_enum(schema, "cluster_id"), schema_enum(schema, "placement"))
        return parsed, errs, len(parsed)
    if fmt in ("v2", "v3"):
        parse = parse_response_v2 if fmt == "v2" else parse_response_v3
        parsed, errs = parse(raw, schema_enum(schema, "cluster_id") or [])
        return parsed, errs, len(parsed.get("clusters") or [])
    if fmt == "baseline":
        parsed, errs = parse_baseline(raw)
        return parsed, errs, len(parsed.get("attributes") or [])
    if fmt == "dupcheck":
        parsed, errs = parse_dupcheck(raw, schema_enum(schema, "columns"))
        return parsed, errs, len(parsed.get("joins") or [])
    if fmt == "evidence":
        parsed, errs = parse_evidence(raw, schema_enum(schema, "id"))
        return parsed, errs, len(parsed.get("answers") or [])
    if fmt == "split":
        parsed, errs = parse_split(raw, schema_enum(schema, "examples") or [])
        return parsed, errs, len(parsed.get("parts") or [])
    if fmt == "noise":
        parsed, errs = parse_noise(raw, schema_enum(schema, "cluster_id"), schema_enum(schema, "verdict") or NOISE_VERDICTS)
    elif fmt == "gate":
        parsed, errs = parse_gate(raw, schema_enum(schema, "cluster_id"))
    elif fmt == "reconcile":
        parsed, errs = parse_reconcile(raw, schema_enum(schema, "unit_id"), schema_enum(schema, "same_as"))
    else:
        raise ValueError(f"unknown job format {fmt!r}")
    return parsed, errs, 1 if parsed else 0
