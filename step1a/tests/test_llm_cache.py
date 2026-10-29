import json
from pathlib import Path

from s1a import llm_cache as lc

OBJ = {"cluster_id": "E1#3", "name": "leave at", "description": "d", "value_type": "time",
       "action": "keep", "merge_with": [], "split": [], "placement": "current entity",
       "evidence": "leave at [[5pm]]"}


def test_key_stable_and_param_order_free():
    a = lc.key("m", {"t": 0, "n": 1}, "p", "r1")
    assert a == lc.key("m", {"n": 1, "t": 0}, "p", "r1")
    assert len(a) == 64
    assert a != lc.key("m", {"t": 0, "n": 1}, "p2", "r1")


def test_run_tag_changes_key():
    assert lc.key("m", {}, "p", "r1") != lc.key("m", {}, "p", "r2")


def test_cache_hit_and_miss(tmp_path):
    f = tmp_path / "sub" / "c.jsonl"
    k = lc.key("m", {}, "p", "r1")
    assert lc.get(f, k) is None
    lc.put(f, k, {"raw": "x"})
    assert lc.get(f, k)["raw"] == "x"
    assert lc.get(f, lc.key("m", {}, "p", "r2")) is None


def test_parse_with_fences_and_extra_text():
    raw = "Here you go:\n```json\n" + json.dumps([OBJ]) + "\n```\nHope that helps [1]."
    objs, errs = lc.parse_response(raw)
    assert errs == [] and objs[0]["cluster_id"] == "E1#3"


def test_parse_plain_array():
    objs, errs = lc.parse_response(json.dumps([OBJ, OBJ]))
    assert len(objs) == 2 and errs == []


def test_schema_errors_detected():
    bad = dict(OBJ, action="delete", value_type="date")
    del bad["evidence"]
    _, errs = lc.parse_response(json.dumps([bad]))
    joined = " ".join(errs)
    assert "missing key evidence" in joined and "bad action" in joined and "bad value_type" in joined


def test_bad_split_and_no_array():
    _, errs = lc.parse_response(json.dumps([dict(OBJ, split=[{"name": "a"}])]))
    assert any("split" in e for e in errs)
    assert lc.parse_response("no json here")[1]


V2 = {"attributes": [{"name": "destination", "description": "d", "role": "r"}],
      "clusters": [{"cluster_id": "E1#0", "attribute": "destination", "evidence": "e", "mixed": False,
                    "placement": "current entity E1"},
                   {"cluster_id": "E1#1", "attribute": "not_attribute", "evidence": "e", "mixed": True,
                    "placement": "current entity E1"}]}


def test_v2_good_with_fence():
    obj, errs = lc.parse_response_v2("ok\n```json\n" + json.dumps(V2) + "\n```", ["E1#0", "E1#1"])
    assert errs == [] and len(obj["clusters"]) == 2


def test_v2_bad():
    bad = json.loads(json.dumps(V2))
    bad["clusters"][1] = dict(bad["clusters"][0], attribute="origin")  # duplicate id + unlisted name
    j = " ".join(lc.parse_response_v2(json.dumps(bad), ["E1#0", "E1#1", "E1#2"])[1])
    assert "duplicate cluster_id" in j and "not in the attribute list" in j and "missing cluster_id 'E1#2'" in j
    off = " ".join(lc.parse_response_v2(json.dumps(bad), ["E1#0"], attribute_names_check=False)[1])
    assert "attribute list" not in off and "duplicate cluster_id" in off
    assert lc.parse_response_v2("nothing", ["E1#0"])[1]


SPLIT = {"cluster_id": "E1#1", "is_mixed": True, "parts": [
    {"name": "leave_time", "role": "r", "examples": ["E1-1:s0"]},
    {"name": "arrive_time", "role": "r", "examples": ["E1-1:s1"]}]}


def test_split_good_and_bad():
    ids = ["E1-1:s0", "E1-1:s1", "E1-1:s2"]
    assert lc.parse_split(json.dumps(SPLIT), ids)[1] == []
    bad = json.loads(json.dumps(SPLIT))
    bad["parts"][1]["examples"] = ["E1-1:s0", "E1-1:s9"]
    j = " ".join(lc.parse_split(json.dumps(bad), ids)[1])
    assert "more than once" in j and "unknown example 'E1-1:s9'" in j
    assert lc.parse_split("[1]", ids)[1]
    assert lc.parse_split(json.dumps({"parts": 3}), ids)[1]


def test_v1_enum():
    ids, opts = ["E1#3", "E1#4"], ["current entity E1"]
    ok = dict(OBJ, placement="current entity E1", merge_with=["E1#4"])
    assert lc.parse_v1_enum(json.dumps([ok]), ids, opts)[1] == []
    bad = dict(ok, cluster_id="E9#1", merge_with=["E1#7"], placement="elsewhere")
    j = " ".join(lc.parse_v1_enum(json.dumps([bad]), ids, opts)[1])
    assert "unknown cluster_id" in j and "unknown merge_with" in j and "bad placement" in j


def test_v31_notebook_compiles():
    path = Path(__file__).resolve().parent.parent / "colab" / "S1A_llm_v31_colab.ipynb"
    nb = json.loads(path.read_text(encoding="utf-8"))
    codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(codes) == 8
    for i, c in enumerate(codes):
        src = "\n".join("" if ln.lstrip().startswith(("!", "%")) else ln for ln in "".join(c["source"]).splitlines())
        compile(src, f"cell{i + 1}", "exec")


def test_schema_enum_and_parse_job():
    sch = {"type": "object", "properties": {"parts": {"type": "array", "items": {"type": "object", "properties": {
        "examples": {"type": "array", "items": {"enum": ["a:s0", "a:s1"]}}}}}}}
    assert lc.schema_enum(sch, "examples") == ["a:s0", "a:s1"] and lc.schema_enum(sch, "zzz") is None
    raw = json.dumps({"cluster_id": "a", "is_mixed": True, "parts": [{"name": "n", "role": "r", "examples": ["a:s0"]}]})
    assert lc.parse_job(raw, "split", sch) == (json.loads(raw), [], 1)
    arr = {"type": "array", "items": {"type": "object", "properties": {
        "cluster_id": {"enum": ["E1#3"]}, "placement": {"enum": ["p"]}}}}
    assert lc.parse_job(json.dumps([OBJ]), "v1", arr)[1] == [f"[0] bad placement 'current entity'"]
    assert lc.parse_job(json.dumps([OBJ]), "v1", {})[1] == []


def _schema(**enums):
    return {"type": "object", "properties": {k: {"enum": v} for k, v in enums.items()}}


def test_parse_job_v3():
    obj = {"attributes": [{"name": "a", "description": "d", "role": "r"}],
           "clusters": [{"cluster_id": "E1#0", "reason": "why", "attribute": "a", "evidence": "e",
                         "mixed": False, "placement": "current entity E1"}]}
    sch = _schema(cluster_id=["E1#0"])
    assert lc.parse_job(json.dumps(obj), "v3", sch) == (obj, [], 1)
    no_reason = json.loads(json.dumps(obj))
    del no_reason["clusters"][0]["reason"]
    assert "reason missing" in " ".join(lc.parse_job(json.dumps(no_reason), "v3", sch)[1])
    assert lc.parse_job(json.dumps(no_reason), "v2", sch)[1] == []  # v2 does not need a reason
    bad = json.loads(json.dumps(obj))
    bad["clusters"][0]["cluster_id"] = "E1#9"
    assert "unknown cluster_id" in " ".join(lc.parse_job(json.dumps(bad), "v3", sch)[1])


def test_parse_job_noise():
    sch = _schema(cluster_id=["E1#7"], verdict=["attribute", "noise", "unsure"])
    ok = {"cluster_id": "E1#7", "reason": "r", "verdict": "attribute", "name": "price"}
    assert lc.parse_job(json.dumps(ok), "noise", sch) == (ok, [], 1)
    assert lc.parse_job(json.dumps(dict(ok, verdict="noise", name="")), "noise", sch)[1] == []
    assert "bad verdict 'maybe'" in " ".join(lc.parse_job(json.dumps(dict(ok, verdict="maybe")), "noise", sch)[1])
    assert "bad cluster_id" in " ".join(lc.parse_job(json.dumps(dict(ok, cluster_id="E1#8")), "noise", sch)[1])
    miss = {k: v for k, v in ok.items() if k != "name"}
    assert lc.parse_job(json.dumps(miss), "noise", sch)[1] == ["missing key name"]
    assert lc.parse_job(json.dumps(dict(ok, verdict="maybe")), "noise", {})[1][0].startswith("bad verdict")  # default enum


def test_parse_job_gate():
    sch = _schema(cluster_id=["E1#7"])
    ok = {"cluster_id": "E1#7", "summary": "times", "coherent": True}
    assert lc.parse_job(json.dumps(ok), "gate", sch) == (ok, [], 1)
    assert lc.parse_job(json.dumps(dict(ok, coherent="yes")), "gate", sch)[1] == ["coherent missing or not a boolean"]
    assert lc.parse_job(json.dumps({"cluster_id": "E1#7", "coherent": False}), "gate", sch)[1] == ["missing key summary"]
    assert "bad cluster_id" in " ".join(lc.parse_job(json.dumps(dict(ok, cluster_id="x")), "gate", sch)[1])


def test_parse_job_reconcile():
    sch = _schema(unit_id=["a0"], same_as=["price", "none"])
    ok = {"unit_id": "a0", "reason": "same", "same_as": "price"}
    assert lc.parse_job(json.dumps(ok), "reconcile", sch) == (ok, [], 1)
    assert lc.parse_job(json.dumps(dict(ok, same_as="none")), "reconcile", sch)[1] == []
    assert "bad same_as 'cost'" in " ".join(lc.parse_job(json.dumps(dict(ok, same_as="cost")), "reconcile", sch)[1])
    assert lc.parse_job(json.dumps({"unit_id": "a0", "same_as": "none"}), "reconcile", sch)[1] == ["missing key reason"]
    assert lc.parse_job("not json", "reconcile", sch)[1] == ["no JSON object found"]


def test_parse_job_unknown_format():
    import pytest
    with pytest.raises(ValueError):
        lc.parse_job("{}", "nope", {})


def test_token_fields_fake_output():
    from types import SimpleNamespace as NS
    out = NS(prompt_token_ids=[1, 2, 3], outputs=[NS(token_ids=[4, 5], text="x")])
    assert lc.token_fields(out, 12.3456, 64) == {"prompt_tokens": 3, "output_tokens": 2,
                                                 "batch_seconds": 12.35, "batch_size": 64}


def test_v32_notebook_compiles():
    path = Path(__file__).resolve().parent.parent / "colab" / "S1A_llm_v32_colab.ipynb"
    nb = json.loads(path.read_text(encoding="utf-8"))
    codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(codes) == 10
    for i, c in enumerate(codes):
        src = "\n".join("" if ln.lstrip().startswith(("!", "%")) else ln for ln in "".join(c["source"]).splitlines())
        compile(src, f"cell{i + 1}", "exec")
