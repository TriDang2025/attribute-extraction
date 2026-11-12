"""wf_v4.2 option B (user choice 2026-11-11): "exactly once" guided schemas for Llama. Frozen prompts, parsers and validators unchanged.

T1 / T2 showed one failure: Llama-3.1-8B breaks "every id exactly once" (Step 3 A repeats a cluster; Step 4 4.2 writes one table per
column). The frozen schemas check each list item's shape only. Here the per-id lists become objects with one required key per id
(in the frozen enum order, no other keys), so guided decoding cannot repeat or skip an id:
- v2 (Step 3 A):   clusters    -> {cluster_id: {attribute, evidence, mixed, placement}}; attributes capped (n clusters + 2 items,
                   short strings) because 3/18 T1 answers looped inside the attribute list.
- s4_41 (4.1):     groups + unused -> columns {column: {group "G<n>" | "unused", reason}} and groups [{group, note}].
- s4_42 (4.2):     tables      -> {group: {name, description, row}}.
- s4_44 (4.4):     tables      -> {table name: {primary_key, new_id_name, columns, foreign_keys}}.
Extension (user choice 2026-11-12, after the first option B run: 4/12 chains looped at 4.3, 3/12 stopped at 4.2 on a repeated name):
- s4_43 (4.3):     list form kept (no fixed ids); relationships capped at 2 x the pairs of tables, new_tables at the pairs,
                   short strings.
- s4_42 names:     unkey() renames a repeated table name (case-insensitive, as validate_42) to <name>_<group>, the first keeps it;
                   renamed_42() counts these repairs for the report.
unkey() turns an answer back into the frozen list format before the frozen parser runs (an answer already in list form, e.g. an
unguided retry, passes unchanged). KeyedLLM wraps a backend (nov16_v41.VllmBackend / FakeLLM): it rewrites the schema files of these
formats to the keyed form (the frozen file kept as <schema>.frozen.json) and marks the jobs, so nov16_v41.parse_answer unkeys them.
"""
import json
from pathlib import Path

MARK = "keyed_v42"
FORMATS = ("v2", "s4_41", "s4_42", "s4_43", "s4_44")
CAP = {"attr_name": 60, "attr_text": 200, "evidence": 300, "reason": 150, "name": 60}
_STR = {"type": "string"}


def _obj(props, required=None):
    return {"type": "object", "properties": props, "required": list(props) if required is None else required,
            "additionalProperties": False}


def _cap(n):
    return {"type": "string", "maxLength": n}


def _items(schema, key):
    return schema["properties"][key]["items"]


def _value(item, drop):
    """Item schema without its id property `drop` (the id becomes the key)."""
    props = {k: v for k, v in item["properties"].items() if k != drop}
    return _obj(props, [k for k in item.get("required", props) if k != drop])


# ---------------------------------------------------------------- schemas
def key_schema(fmt, frozen):
    if fmt == "v2":
        item = _items(frozen, "clusters")
        ids = item["properties"]["cluster_id"]["enum"]
        val = _value(item, "cluster_id")
        val["properties"]["evidence"] = _cap(CAP["evidence"])
        attr = _obj({"name": _cap(CAP["attr_name"]), "description": _cap(CAP["attr_text"]), "role": _cap(CAP["attr_text"])})
        props = {"attributes": {"type": "array", "items": attr, "minItems": 1, "maxItems": len(ids) + 2},
                 "clusters": _obj({c: val for c in ids})}
    elif fmt == "s4_41":
        ids = _items(frozen, "groups")["properties"]["columns"]["items"]["enum"]
        col = _obj({"group": {"type": "string", "pattern": "^(G[0-9]{1,2}|unused)$"}, "reason": _cap(CAP["reason"])})
        props = {"columns": _obj({c: col for c in ids}),
                 "groups": {"type": "array", "items": _obj({"group": {"type": "string", "pattern": "^G[0-9]{1,2}$"}, "note": _STR}),
                            "maxItems": len(ids)},
                 "duplicate_flags": {**frozen["properties"]["duplicate_flags"], "maxItems": len(ids)}}
    elif fmt == "s4_42":
        item = _items(frozen, "tables")
        props = {"tables": _obj({g: _value(item, "group") for g in item["properties"]["group"]["enum"]})}
    elif fmt == "s4_43":
        n = len(_items(frozen, "new_tables")["properties"]["between"]["items"]["enum"])
        pairs = max(1, n * (n - 1) // 2)
        rel = _obj({"from": _cap(CAP["name"]), "to": _cap(CAP["name"]), "kind": _items(frozen, "relationships")["properties"]["kind"],
                    "reason": _cap(CAP["reason"])})
        new = _obj({"name": _cap(CAP["name"]), "description": _cap(CAP["attr_text"]), "row": _cap(CAP["attr_text"]),
                    "between": _items(frozen, "new_tables")["properties"]["between"]})
        props = {"relationships": {"type": "array", "items": rel, "maxItems": 2 * pairs},
                 "new_tables": {"type": "array", "items": new, "maxItems": pairs}}
    elif fmt == "s4_44":
        item = _items(frozen, "tables")
        props = {"tables": _obj({n: _value(item, "name") for n in item["properties"]["name"]["enum"]})}
    else:
        raise ValueError(f"no keyed schema for format {fmt!r}")
    return {**_obj(props), "title": MARK}


def parse_schema(fmt, keyed):
    """The schema the frozen parser gets: for v2 the cluster-id enum (llm_cache.schema_enum finds it); the Step 4 parsers only read
    the nested kind / type / option enums, which the keyed schema still has."""
    if fmt == "v2":
        return {"properties": {"cluster_id": {"enum": list(keyed["properties"]["clusters"]["properties"])}}}
    return keyed


# ---------------------------------------------------------------- answers
def _load(raw):
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None


def unkey(fmt, raw):
    """Raw answer text in the frozen list format. Text that is not a JSON object (cut off) or already in list form is returned as is."""
    obj = _load(raw)
    if obj is None:
        return raw
    if fmt == "v2" and isinstance(obj.get("clusters"), dict):
        obj["clusters"] = [{"cluster_id": k, **v} for k, v in obj["clusters"].items()]
    elif fmt == "s4_41" and isinstance(obj.get("columns"), dict):
        notes = {g.get("group"): g.get("note", "") for g in obj.get("groups") or [] if isinstance(g, dict)}
        groups, unused = {}, []
        for c, v in obj["columns"].items():
            if v.get("group") == "unused":
                unused.append({"column": c, "reason": v.get("reason", "")})
            else:
                groups.setdefault(v.get("group"), []).append(c)
        obj = {"groups": [{"group": g, "columns": cs, "note": notes.get(g, "")} for g, cs in groups.items()], "unused": unused,
               "duplicate_flags": obj.get("duplicate_flags", [])}
    elif fmt == "s4_42" and isinstance(obj.get("tables"), dict):
        obj["tables"] = _unique_names([{"group": g, **v} for g, v in obj["tables"].items()])
    elif fmt == "s4_44" and isinstance(obj.get("tables"), dict):
        obj["tables"] = [{"name": n, **v} for n, v in obj["tables"].items()]
    else:
        return raw
    return json.dumps(obj, ensure_ascii=False)


def _norm(name):
    return str(name or "").strip().lower()


def _unique_names(tables):
    """4.2 tables with a repeated name (as validate_42 compares them) renamed to <name>_<group>[_<k>]; the first keeps its name."""
    used = set()
    for t in tables:
        if isinstance(t, dict) and _norm(t.get("name")):
            base = name = str(t["name"]).strip()
            if _norm(name) in used:
                base = name = f"{base}_{str(t.get('group', '')).lower()}"
                k = 2
                while _norm(name) in used:
                    name, k = f"{base}_{k}", k + 1
            t["name"] = name
            used.add(_norm(name))
    return tables


def renamed_42(raw):
    """Number of table names unkey() renames in a keyed 4.2 answer (0 for a cut-off or list-form answer)."""
    obj = _load(raw)
    tables = obj.get("tables") if obj else None
    if not isinstance(tables, dict):
        return 0
    names = [_norm(v.get("name")) for v in tables.values() if isinstance(v, dict) and _norm(v.get("name"))]
    return len(names) - len(set(names))


def key_answer(fmt, raw):
    """The inverse of unkey for a frozen-format answer (the laptop fake model answers the frozen schema; tests)."""
    obj = json.loads(raw)
    if fmt == "v2":
        obj["clusters"] = {c.pop("cluster_id"): c for c in obj["clusters"]}
    elif fmt == "s4_41":
        cols = {c: {"group": g["group"], "reason": ""} for g in obj["groups"] for c in g["columns"]}
        cols.update({u["column"]: {"group": "unused", "reason": u["reason"]} for u in obj["unused"]})
        obj = {"columns": cols, "groups": [{"group": g["group"], "note": g["note"]} for g in obj["groups"]],
               "duplicate_flags": obj["duplicate_flags"]}
    elif fmt == "s4_42":
        obj["tables"] = {t.pop("group"): t for t in obj["tables"]}
    elif fmt == "s4_44":
        obj["tables"] = {t.pop("name"): t for t in obj["tables"]}
    return json.dumps(obj, ensure_ascii=False)


# ---------------------------------------------------------------- backend wrapper
def frozen_path(schema_path):
    p = Path(schema_path)
    return p.with_name(p.name.replace(".schema.json", ".frozen.json"))


def key_job(out, job):
    """Rewrite the job's schema file to the keyed form (idempotent; the frozen file kept once) and return the marked job."""
    if job["format"] not in FORMATS:
        return job
    p = Path(out) / job["schema"]
    schema = json.loads(p.read_text(encoding="utf-8"))
    if schema.get("title") != MARK:
        frozen_path(p).write_text(json.dumps(schema, indent=1) + "\n", encoding="utf-8", newline="\n")
        p.write_text(json.dumps(key_schema(job["format"], schema), indent=1) + "\n", encoding="utf-8", newline="\n")
    return {**job, "keyed": True}


def fake_keyed():
    """Laptop stand-in for a keyed run: nov16_v41.FakeLLM answers the frozen schema (<schema>.frozen.json), then key_answer."""
    from .nov16_v41 import FakeLLM

    class FakeKeyed(FakeLLM):
        def run(self, out, jobs):
            self.out = Path(out)
            return super().run(out, jobs)

        def respond(self, job, prompt, schema):
            if not job.get("keyed"):
                return super().respond(job, prompt, schema)
            frozen = json.loads(frozen_path(self.out / job["schema"]).read_text(encoding="utf-8"))
            return key_answer(job["format"], super().respond(job, prompt, frozen))
    return FakeKeyed()


class KeyedLLM:
    """Decorator of a backend with run(out, jobs): keys the schemas of FORMATS, then runs the inner backend."""

    def __init__(self, inner):
        self.inner = inner
        self.model_id = getattr(inner, "model_id", "")

    def run(self, out, jobs):
        return self.inner.run(out, [key_job(out, j) for j in jobs])
