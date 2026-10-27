import json

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
