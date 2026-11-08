import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import gemini_v41 as GM  # noqa: E402
from s1a import step1b_v41 as S  # noqa: E402

COLS = [
    {"id": "a:1", "name": "start time", "description": "when it starts", "value_type": {"dominant": "time", "share": 1.0},
     "examples": [["10:00", "starts at 10:00"], ["springfield", "she lives in Springfield"]], "n_mentions": 5, "n_dialogues": 3},
    {"id": "a:2", "name": "begin time", "description": "when it begins", "value_type": "time", "examples": ["11:00"], "n_mentions": 2,
     "n_dialogues": 2},
    {"id": "b:1", "name": "title", "description": "name of it", "value_type": "text", "examples": [], "n_mentions": 1, "n_dialogues": 1},
]


def answer(**over):
    a = {"headings": [
        {"heading": "a", "summary": "s", "decisions": [
            {"id": "a:1", "action": "keep", "new_name": "", "merge_into": "", "reason": "r"},
            {"id": "a:2", "action": "merge", "new_name": "", "merge_into": "a:1", "reason": "r"}],
         "new_attributes": [{"name": "end time", "description": "d", "type": "time", "label": "end time", "reason": "r"}]},
        {"heading": "b", "summary": "s", "decisions": [{"id": "b:1", "action": "rename", "new_name": "book title", "merge_into": "", "reason": "r"}],
         "new_attributes": []}]}
    a.update(over)
    return a


def test_prompt_and_schema():
    text, schema = S.build_prompt(COLS)
    assert "== a ==" in text and "[b:1] title" in text and "Attributes (3):" in text
    h = schema["properties"]["headings"]
    assert h["minItems"] == h["maxItems"] == 2
    item = h["items"]["properties"]
    assert item["new_attributes"]["maxItems"] == S.MAX_NEW
    assert item["decisions"]["items"]["properties"]["merge_into"]["enum"] == ["a:1", "a:2", "b:1", ""]
    assert "Dialogues:" not in text and text.count("(in:") == 2  # only capped example contexts, no dialogues


def test_capped_examples():
    many = [dict(COLS[0], examples=[[f"v{i}", f"ctx {i}"] for i in range(9)])]
    assert S.render(many).count("(in:") == S.MAX_EXAMPLES


def test_valid_answer():
    a = answer()
    assert S.validate(a, COLS) == []
    assert S.summary(a, COLS) == {"a": {"keep": 1, "rename": 0, "merge": 1, "flag": 0, "new": 1},
                                  "b": {"keep": 0, "rename": 1, "merge": 0, "flag": 0, "new": 0}}
    assert S.labels(a, COLS) == [{"entity": "a", "name": "end time", "label": "end time", "description": "d", "value_type": "time"}]


def test_errors():
    a = answer()
    a["headings"][0]["decisions"].pop()                                   # a:2 missing -> "dropped"
    a["headings"][1]["decisions"][0]["new_name"] = ""                     # rename without a name
    a["headings"][0]["new_attributes"] += [{"name": "town", "description": "", "type": "text", "label": "springfield", "reason": ""},
                                          {"name": "start time", "description": "", "type": "time", "label": "start", "reason": ""},
                                          {"name": "x", "description": "", "type": "colour", "label": "dataset slot", "reason": ""}]
    errs = S.validate(a, COLS)
    assert any("a:2" in e and "without a decision" in e for e in errs)
    assert any("rename without new_name" in e for e in errs)
    assert any("example value" in e and "springfield" in e for e in errs)
    assert any("repeats an existing name" in e for e in errs)
    assert any("bad type" in e for e in errs) and any("corpus word" in e for e in errs)
    assert [x["label"] for x in S.labels(a, COLS)] == ["end time", "start"]  # the non-generic labels are not passed on


def test_merge_across_headings_and_limit():
    a = answer()
    a["headings"][0]["decisions"][1]["merge_into"] = "b:1"
    a["headings"][1]["new_attributes"] = [{"name": f"n{i}", "description": "", "type": "text", "label": f"n{i}", "reason": ""} for i in range(11)]
    errs = S.validate(a, COLS)
    assert any("bad merge_into" in e for e in errs) and any("max 10" in e for e in errs)


def test_ordinary_word_values_are_not_banned():
    vals = S.example_values([dict(COLS[0], examples=[["contact number", "the contact number is"], ["cambridge", "go to Cambridge"]])])
    assert S.generic_errors("contact number", vals) == [] and S.generic_errors("cambridge hotel", vals)


def test_generic_ok_words():
    vals = S.example_values([dict(COLS[0], examples=[["free", "it is free"]])])
    assert S.generic_errors("free parking", vals) == []


def test_fake_answer_is_valid():
    assert S.validate(S.fake_answer(COLS), COLS) == []


def test_gemini_generate_cache_and_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-not-a-key")
    calls = []

    def call(url, body):
        calls.append(json.loads(json.dumps(body)))
        if "responseJsonSchema" in body["generationConfig"]:
            raise GM.GeminiError("HTTP 400: Invalid JSON payload: unknown schema field")
        return {"candidates": [{"content": {"parts": [{"text": "thinking", "thought": True}, {"text": '{"ok": 1}'}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 3}, "modelVersion": "m-1"}
    schema = {"type": "object", "properties": {"x": {"type": "string", "pattern": "^G"}}}
    r = GM.generate("p", schema, "m", tmp_path, call=call)
    assert r["raw"] == '{"ok": 1}' and r["guided"] is False and not r["cached"] and r["model"] == "m-1"
    assert "pattern" not in json.dumps(calls[0]["generationConfig"]["responseJsonSchema"])
    r2 = GM.generate("p", schema, "m", tmp_path, call=call)
    assert r2["cached"] and len(calls) == 2


def test_gemini_needs_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(GM, "_user_env", lambda name: "")
    with pytest.raises(GM.GeminiError):
        GM._key()
