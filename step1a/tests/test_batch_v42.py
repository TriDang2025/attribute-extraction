"""wf_v4.2 compact A prompt (s1a/batch_v42.py): placement codes, the compact parser, C1 window, schema, C5 plan."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v42 as C  # noqa: E402
from s1a import llm_cache as LC  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402

IDS = ["E0#0", "E0#1", "E0#2"]
ATTRS = [{"name": "price", "description": "d", "role": "r"}, {"name": "area", "description": "d", "role": "r"}]


def _answer(clusters, attrs=ATTRS):
    return json.dumps({"attributes": attrs, "clusters": clusters})


def _c(cid, attr="price", placement="cur", mixed=False):
    return {"cluster_id": cid, "attribute": attr, "mixed": mixed, "placement": placement}


# ---------------------------------------------------------------- codes
def test_codes_round_trip_every_option():
    opts = PIN.option_texts("E0", ["E1", "E2"])
    codes = [C.code_of(t) for t, _ in opts]
    assert codes == ["cur", "sub", "oth:E1", "oth:E2", "rel:E1", "rel:E2", "sep"]
    assert [C.option_of(c, "E0") for c in codes] == [t for t, _ in opts]
    for bad in ("other", "oth:", "rel", "xyz:E1"):
        with pytest.raises(ValueError):
            C.option_of(bad, "E0")
    with pytest.raises(ValueError):
        C.code_of("somewhere else")


# ---------------------------------------------------------------- parser
def test_parse_compact_maps_back_to_the_v2_shape():
    raw = _answer([_c("E0#0"), _c("E0#1", "area", "oth:E2", True), _c("E0#2", "not_attribute", "sep")])
    obj, errors = C.parse_compact(raw, IDS)
    assert errors == []
    cl = obj["clusters"]
    assert [c["placement"] for c in cl] == ["current entity E0", "other entity E2", PIN.SEPARATE]
    assert all(c["evidence"] == "" for c in cl) and cl[1]["mixed"] is True
    v2_obj, v2_err = LC.parse_response_v2(json.dumps(obj), IDS)     # downstream reads it as a frozen v2 answer
    assert v2_err == [] and v2_obj == obj


def test_parse_compact_relationship_uses_the_entity_of_the_ids():
    obj, errors = C.parse_compact(_answer([_c(i, placement="rel:E3") for i in ["E5#0", "E5#1"]]), ["E5#0", "E5#1"])
    assert errors == [] and obj["clusters"][0]["placement"] == "relationship(E5, E3)"


def test_parse_compact_counts_errors_and_never_repairs():
    raw = _answer([_c("E0#0", placement="elsewhere"), _c("E0#0"), _c("E0#9", "colour")])
    obj, errors = C.parse_compact(raw, IDS)
    assert "clusters[0] unknown placement code 'elsewhere'" in errors
    assert obj["clusters"][0]["placement"] == "elsewhere"                      # kept as written
    assert "duplicate cluster_id 'E0#0'" in errors and "clusters[2] unknown cluster_id 'E0#9'" in errors
    assert "clusters[2] attribute 'colour' not in the attribute list" in errors
    assert {"missing cluster_id 'E0#1'", "missing cluster_id 'E0#2'"} <= set(errors)


def test_parse_compact_bad_json_and_bad_types():
    assert C.parse_compact("not json at all", IDS) == ({}, C.parse_compact("not json at all", IDS)[1])
    assert C.parse_compact("not json at all", IDS)[1]
    obj, errors = C.parse_compact('Sure! {"attributes": [], "clusters": [{"cluster_id": "E0#0", "attribute": "x", '
                                  '"mixed": "no", "placement": 3}]} hope it helps', ["E0#0"])
    assert "clusters[0] mixed not a boolean" in errors and "clusters[0] placement not a string" in errors
    assert C.parse_compact('{"attributes": {}, "clusters": "x"}', IDS)[1][:2] == ["attributes missing or not a list",
                                                                                 "clusters missing or not a list"]


def test_parse_job_routes_the_compact_format_only():
    schema = {"properties": {"clusters": {"items": {"properties": {"cluster_id": {"enum": IDS}}}}}}
    parsed, errs, n = C.parse_job(_answer([_c(i) for i in IDS]), C.FORMAT, schema)
    assert errs == [] and n == 3 and parsed["clusters"][2]["placement"] == "current entity E0"
    raw = json.dumps({"joins": []})
    assert C.parse_job(raw, "dupcheck", {"properties": {}}) == LC.parse_job(raw, "dupcheck", {"properties": {}})


# ---------------------------------------------------------------- prompt pieces
def test_instruction_switches():
    assert C.instruction(False, False) == PIN.INSTRUCTION_V2
    full = C.instruction()
    assert "evidence" not in full and "Quote one example" not in full and '"placement": "cur"' in full
    assert "inside a few words of the turn" in full
    assert "evidence" in C.instruction(True, False)


def test_window_text():
    marked = "one two three four five six seven eight nine ten [[Friday]] a b c d e f g h i j k l m n"
    assert C.window_text(marked) == "... three four five six seven eight nine ten [[Friday]] a b c d e f g h i j k l ..."
    assert C.window_text("[[ok]] thanks") == "[[ok]] thanks"
    assert C.window_text("I need [[two]] tickets", before=1, after=0) == "... need [[two]] ..."


def test_schema_compact_has_codes_and_no_evidence():
    inp = PIN.PilotInput("E0", [PIN.ClusterInput(i, 3, 2, False, []) for i in IDS], PIN.option_texts("E0", ["E1"]), {})
    s = C.schema_compact(inp)
    clu = s["properties"]["clusters"]["items"]
    assert "evidence" not in clu["properties"] and "evidence" not in clu["required"]
    assert clu["properties"]["placement"]["enum"] == ["cur", "sub", "oth:E1", "rel:E1", "sep"]
    assert LC.schema_enum(s, "cluster_id") == IDS
    assert LC.schema_enum(C.schema_compact(inp, ["E0#2"]), "cluster_id") == ["E0#2"]


def test_plan_calls_splits_only_when_needed(monkeypatch):
    inp = PIN.PilotInput("E0", [PIN.ClusterInput(f"E0#{i}", 3, 2, False, []) for i in range(6)], [], {})
    monkeypatch.setattr(C, "render_compact", lambda inp, export, docs, group_ids=None, part=None, **kw:
                        "x" * (len(group_ids) if group_ids else 6))
    monkeypatch.setattr(PIN, "neighbourhoods", lambda export, entity, max_size: [
        [f"E0#{i}" for i in range(j, min(j + max_size, 6))] for j in range(0, 6, max_size)])
    count, ans = len, (lambda n: 10 * n)
    assert C.plan_calls(inp, None, None, count, ans, budget=66) == [(None, None)]
    plan = C.plan_calls(inp, None, None, count, ans, budget=40)                 # 6 clusters x 11 > 40: 2 parts of 3 (33)
    assert plan == [(["E0#0", "E0#1", "E0#2"], (1, 2)), (["E0#3", "E0#4", "E0#5"], (2, 2))]
    with pytest.raises(ValueError, match="do not fit"):
        C.plan_calls(inp, None, None, count, ans, budget=5)


def test_built_manifest_fits_the_budget():
    m = ROOT / "results" / "wf_v42" / "compact" / "manifest.json"
    if not m.exists():
        pytest.skip("run scripts/compact_v42.py first")
    man = json.loads(m.read_text(encoding="utf-8"))
    assert len(man["jobs"]) == 21 and all(j["format"] == C.FORMAT for j in man["jobs"])
    for j in man["jobs"]:
        n = len(j["clusters"])
        est = -(-man["answer_tokens"]["per_cluster"] * man["answer_tokens"]["margin"] * n // 1) + man["answer_tokens"]["base"]
        assert j["prompt_tokens"] + est <= man["budget"] and j["max_tokens"] == man["budget"] - j["prompt_tokens"]
        schema = json.loads((m.parent / j["schema"]).read_text(encoding="utf-8"))
        assert LC.schema_enum(schema, "cluster_id") == j["clusters"]
