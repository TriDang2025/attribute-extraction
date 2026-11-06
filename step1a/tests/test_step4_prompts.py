import copy
import json
from pathlib import Path

import pytest

from s1a import llm_cache as lc
from s1a import step4_prompts as sp

ROOT = Path(__file__).resolve().parent.parent


def col(i, name, vt="text", ex=("a", "b"), **kw):
    return {"id": i, "name": name, "description": f"the {name}", "role": "", "value_type": vt, "examples": list(ex),
            "n_mentions": 10, "n_dialogues": 5, **kw}


COLS = [col("train:1", "leave at", "time", ("5pm", "6pm")), col("train:2", "destination", ex=("ely", "leeds")),
        col("train:3", "price", "number", ("10 pounds",), signal="support 3/10", flag="unsure"),
        col("train:4", "okay", ex=("ok",)),
        col("hotel:1", "hotel name", ex=("alpha", "beta")), col("hotel:2", "stars", "number", ("3", "4")),
        col("hotel:3", "name of the hotel", ex=("alpha",))]
A41 = {"groups": [{"group": "G1", "columns": ["train:1", "train:2", "train:3"], "note": "journeys"},
                  {"group": "G2", "columns": ["hotel:1", "hotel:2", "hotel:3"], "note": "hotels"}],
       "unused": [{"column": "train:4", "reason": "noise"}],
       "duplicate_flags": [{"column": "hotel:3", "duplicate_of": "hotel:1"}]}
A42 = {"tables": [{"group": "G1", "name": "train", "description": "A train.", "row": "one train"},
                  {"group": "G2", "name": "hotel", "description": "A hotel.", "row": "one hotel"}]}
A43 = {"relationships": [{"from": "trip", "to": "train", "kind": "one_to_many", "reason": "r"},
                         {"from": "trip", "to": "hotel", "kind": "one_to_many", "reason": "r"}],
       "new_tables": [{"name": "trip", "description": "A trip.", "row": "one trip", "between": ["train", "hotel"]}]}
A44 = {"tables": [
    {"name": "train", "primary_key": "new", "new_id_name": "train id",
     "columns": [{"column": "train:1", "name": "leave at", "type": "time"}, {"column": "train:2", "name": "destination", "type": "text"},
                 {"column": "train:3", "name": "price", "type": "price"}], "foreign_keys": []},
    {"name": "hotel", "primary_key": "hotel:1", "new_id_name": "",
     "columns": [{"column": "hotel:1", "name": "hotel name", "type": "text"}, {"column": "hotel:2", "name": "stars", "type": "integer"},
                 {"column": "hotel:3", "name": "name of the hotel", "type": "text"}], "foreign_keys": []},
    {"name": "trip", "primary_key": "new", "new_id_name": "trip id",
     "columns": [{"column": "new:train id", "name": "train id", "type": "id"}, {"column": "new:hotel name", "name": "hotel name", "type": "text"}],
     "foreign_keys": [{"column": "new:train id", "ref_table": "train", "ref_column": "new:train id"},
                      {"column": "new:hotel name", "ref_table": "hotel", "ref_column": "hotel:1"}]}]}


def jsonschema_ok(schema):
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema


def prompts():
    block = sp.render_columns(COLS)
    return {"41": sp.build_prompt_41(block, COLS), "42": sp.build_prompt_42(A41, COLS),
            "43": sp.build_prompt_43(A41, A42, COLS), "44": sp.build_prompt_44(A41, A42, A43, COLS),
            "e": sp.build_prompt_e("[user] I need a train to ely.\n[system] At what time?")}


def test_prompts_build_and_schemas_valid():
    for k, (text, schema) in prompts().items():
        assert text.strip() and json.dumps(schema)
        jsonschema_ok(schema)


def test_no_dataset_name():
    for k, (text, schema) in prompts().items():
        assert "multiwoz" not in (text + json.dumps(schema)).lower()


def test_schema_enums_hold_ids_and_tables():
    _, s41 = sp.build_prompt_41("", COLS)
    assert lc.schema_enum(s41, "column") == [c["id"] for c in COLS]
    _, s42 = sp.build_prompt_42(A41, COLS)
    assert lc.schema_enum(s42, "group") == ["G1", "G2"]
    _, s44 = sp.build_prompt_44(A41, A42, A43, COLS)
    assert lc.schema_enum(s44, "primary_key") == [c["id"] for c in COLS] + ["new"]
    assert lc.schema_enum(s44, "ref_table") == ["train", "hotel", "trip"]


def test_schema_accepts_answers():
    js = jsonschema_ok({})
    for (a, (_, s)) in [(A41, prompts()["41"]), (A42, prompts()["42"]), (A43, prompts()["43"]), (A44, prompts()["44"])]:
        js.validate(a, s)
    with pytest.raises(js.ValidationError):
        js.validate({**A41, "unused": [{"column": "train:99", "reason": "x"}]}, prompts()["41"][1])
    with pytest.raises(js.ValidationError):   # a column that is neither an id nor "new:<name>"
        bad = copy.deepcopy(A44)
        bad["tables"][0]["columns"][0]["column"] = "invented"
        js.validate(bad, prompts()["44"][1])


def test_valid_answers_have_no_errors():
    assert sp.validate_41(A41, COLS) == []
    assert sp.validate_42(A42, A41) == []
    assert sp.validate_43(A43, A41, A42) == []
    assert sp.validate_44(A44, A41, A42, A43, COLS) == []


def has(errs, text):
    return any(text in e for e in errs)


def test_validate_41_catches_planted_errors():
    a = copy.deepcopy(A41)
    a["groups"][1]["columns"].append("train:1")           # in two groups
    a["groups"][0]["columns"].remove("train:2")           # missing
    a["groups"][0]["columns"].append("train:77")          # unknown
    a["unused"].append({"column": "train:3", "reason": "x"})   # both
    a["duplicate_flags"].append({"column": "hotel:2", "duplicate_of": "hotel:2"})
    errs = sp.validate_41(a, COLS)
    for t in ("two groups", "train:2' neither", "unknown column 'train:77'", "both in a group and unused", "duplicate of itself"):
        assert has(errs, t), (t, errs)


def test_validate_42_catches_planted_errors():
    a = copy.deepcopy(A42)
    a["tables"][1]["group"] = "G1"
    a["tables"][1]["name"] = "Train"
    assert has(sp.validate_42(a, A41), "named twice") and has(sp.validate_42(a, A41), "not named")
    assert has(sp.validate_42(a, A41), "duplicate table name")
    assert has(sp.validate_42({"tables": [{"group": "G9", "name": "x", "description": "", "row": "r"}]}, A41), "unknown group")


def test_validate_43_catches_planted_errors():
    a = copy.deepcopy(A43)
    a["relationships"].append({"from": "ghost", "to": "train", "kind": "one_to_many", "reason": ""})
    a["relationships"].append({"from": "train", "to": "train", "kind": "weird", "reason": ""})
    a["new_tables"].append({"name": "hotel", "description": "", "row": "r", "between": ["train", "nope"]})
    errs = sp.validate_43(a, A41, A42)
    for t in ("unknown table 'ghost'", "itself", "bad kind", "already used", "between must be"):
        assert has(errs, t), (t, errs)


def test_validate_44_catches_planted_errors():
    a = copy.deepcopy(A44)
    a["tables"][0]["columns"].pop(1)                                       # column missing
    a["tables"][1]["columns"][0]["type"] = "varchar"                       # bad type
    a["tables"][1]["columns"].append({"column": "train:1", "name": "x", "type": "text"})   # not in its group, in two tables
    a["tables"][2]["foreign_keys"][0]["ref_table"] = "ghost"
    a["tables"][2]["foreign_keys"][1]["ref_column"] = "hotel:99"
    a["tables"][2]["primary_key"] = "train:3"
    errs = sp.validate_44(a, A41, A42, A43, COLS)
    for t in ("column 'train:2' missing", "bad type", "not in its group", "in two tables", "unknown table 'ghost'",
              "unknown column 'hotel:99'", "primary key 'train:3'"):
        assert has(errs, t), (t, errs)
    b = copy.deepcopy(A44)
    b["tables"][2]["foreign_keys"] = b["tables"][2]["foreign_keys"][:1]    # relationship trip -> hotel not implemented
    assert has(sp.validate_44(b, A41, A42, A43, COLS), "'trip' -> 'hotel' has no foreign key")
    c = copy.deepcopy(A44)
    c["tables"][0]["new_id_name"] = ""
    assert has(sp.validate_44(c, A41, A42, A43, COLS), "without new_id_name")
    d = copy.deepcopy(A44)
    d["tables"].pop(2)
    assert has(sp.validate_44(d, A41, A42, A43, COLS), "table 'trip' missing")


def test_validate_e():
    ok = {"tables": [{"name": "a", "description": "", "row": "", "primary_key": ["id"], "columns": [{"name": "id", "type": "id"}], "foreign_keys": []},
                     {"name": "b", "description": "", "row": "", "primary_key": ["id"],
                      "columns": [{"name": "id", "type": "id"}, {"name": "a id", "type": "id"}],
                      "foreign_keys": [{"column": "a id", "ref_table": "a", "ref_column": "id"}]}],
          "relationships": [{"from": "b", "to": "a", "kind": "one_to_many", "reason": ""}]}
    assert sp.validate_e(ok) == []
    bad = copy.deepcopy(ok)
    bad["tables"][1]["foreign_keys"][0]["ref_table"] = "zzz"
    bad["tables"][1]["primary_key"] = ["nope"]
    bad["relationships"][0]["kind"] = "x"
    errs = sp.validate_e(bad)
    assert has(errs, "unknown table 'zzz'") and has(errs, "primary key 'nope'") and has(errs, "bad kind")


def test_render_columns_headers_and_flag():
    block = sp.render_columns(COLS, max_examples=1)
    assert "== train ==" in block and "== hotel ==" in block
    assert "[train:3] price" in block and "checker: unsure" in block and "checker evidence: support 3/10" in block
    assert '"ely"' in block and '"leeds"' not in block


def test_columns_from_handover_and_tokens():
    f = ROOT / "handover" / "dev50" / "train.json"
    if not f.exists():
        pytest.skip("no handover")
    cols = sp.columns_from_handover("train", json.loads(f.read_text(encoding="utf-8")))
    assert cols and cols[0]["id"].startswith("train:")
    block = sp.render_columns(cols)
    text, schema = sp.build_prompt_41(block, cols)
    assert "multiwoz" not in text.lower()
    assert sp.first_prompt_tokens(text) < 20000
    assert lc.schema_enum(schema, "column") == [c["id"] for c in cols]


def test_first_prompt_tokens_matches_estimator():
    assert sp.first_prompt_tokens("x" * 350) == 100


# ---------------------------------------------------------------- llm_cache.parse_job formats
@pytest.mark.parametrize("fmt, key, ans", [("s4_41", "41", A41), ("s4_42", "42", A42), ("s4_43", "43", A43), ("s4_44", "44", A44)])
def test_parse_job_step4_ok(fmt, key, ans):
    schema = prompts()[key][1]
    parsed, errs, n = lc.parse_job("```json\n" + json.dumps(ans) + "\n```", fmt, schema)
    assert errs == [] and parsed == ans and n == len(ans["groups" if key == "41" else "tables" if key != "43" else "relationships"])


def test_parse_job_step4_structure_errors():
    schema = prompts()["43"][1]
    bad = copy.deepcopy(A43)
    bad["relationships"][0]["kind"] = "one_to_one"
    del bad["new_tables"][0]["row"]
    _, errs, _ = lc.parse_job(json.dumps(bad), "s4_43", schema)
    assert any("bad kind" in e for e in errs) and any("row missing" in e for e in errs)
    _, errs, n = lc.parse_job("no json", "s4_41", prompts()["41"][1])
    assert errs and n == 0
    _, errs, _ = lc.parse_job(json.dumps({"groups": "x"}), "s4_41", prompts()["41"][1])
    assert any("not a list" in e for e in errs) and any("unused missing" in e for e in errs)


def test_parse_job_step4_e():
    schema = prompts()["e"][1]
    ans = {"tables": [{"name": "a", "description": "d", "row": "r", "primary_key": ["id"],
                       "columns": [{"name": "id", "type": "id"}], "foreign_keys": []}], "relationships": []}
    parsed, errs, n = lc.parse_job(json.dumps(ans), "s4_e", schema)
    assert errs == [] and n == 1
    ans["tables"][0]["columns"][0]["type"] = "blob"
    assert any("bad type" in e for e in lc.parse_job(json.dumps(ans), "s4_e", schema)[1])
