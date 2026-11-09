"""Diary Nov 7 task 7: the Nov 16 run (scripts/nov16_v41.py, s1a/nov16_v41.py, colab/S1A_nov16_v41_colab.ipynb)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v4 as B  # noqa: E402
from s1a import llm_cache as LC  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402
import nov16_v41 as P  # noqa: E402


def test_step4_chains_are_the_chosen_18():
    chs = NV.step4_chains({"dev50": "x/a2_dev50.json", "dev50b": "x/a2_dev50b.json"})
    assert len(chs) == 18 and all(c["prompt_version"] == "v41" for c in chs)
    assert sorted({(c["input"], c["set"]) for c in chs}) == sorted(NV.STEP4_RUNS)
    a2 = [c for c in chs if c["input"] == "a2"]
    assert len(a2) == 6 and all(c["columns_file"] == f"x/a2_{c['set']}.json" for c in a2)
    assert all("columns_file" not in c for c in chs if c["input"] != "a2")


def test_a2_columns_appends_new_loop2_columns_to_their_entity():
    a = [{"id": "train:1", "name": "t"}, {"id": "hotel:1", "name": "h1"}, {"id": "hotel:2", "name": "h2"}, {"id": "restaurant:1", "name": "r"}]
    ms = [dict(mention_id=i, dialogue_id=f"D{i % 2}", text=t, norm_value=t, context=f"it has {t} too") for i, t in
          enumerate(["free wifi", "wifi", "free wifi"])]
    clusters = {"L2_hotel#0": {"mentions": ms[:2]}, "L2_hotel#1": {"mentions": ms[2:]}, "L2_hotel#2": {"mentions": []}}
    final = {"hotel": [{"name": "has wifi", "description": "d", "clusters": ["L2_hotel#0", "L2_hotel#1"], "status": "new"},
                       {"name": "hotel name", "description": "", "clusters": ["L2_hotel#2"], "status": "duplicate"}]}
    cols, added = NV.a2_columns(a, final, clusters)
    assert [c["id"] for c in cols] == ["train:1", "hotel:1", "hotel:2", "hotel:3", "restaurant:1"]   # entity blocks kept
    new = cols[3]
    assert added == [("hotel:3", "has wifi", ["L2_hotel#0", "L2_hotel#1"])]
    assert new["examples"][0][0] == "free wifi" and new["n_mentions"] == 3 and new["n_dialogues"] == 2
    assert set(new) >= {"id", "name", "description", "role", "value_type", "examples", "n_mentions", "n_dialogues", "signal", "flag"}
    assert NV.a2_columns(a, {}, {})[0] == a


def test_chain_columns_reads_the_chain_input_file(tmp_path):
    p = tmp_path / "in" / "a2.columns.json"
    B.write_json(p, [{"id": "hotel:2", "name": "b"}, {"id": "hotel:1", "name": "a"}])
    ch = {"set": "dev50", "input": "a2", "seed": 0, "exclude": [], "columns_file": "in/a2.columns.json"}
    assert [c["name"] for c in B.chain_columns(ch, tmp_path)] == ["b", "a"]


def test_state_and_todo(tmp_path):
    assert NV.load_state(tmp_path) == {"done": []}
    NV.mark_done(tmp_path, "step1b", {"n": 1})
    NV.mark_done(tmp_path, "step1b", {"n": 2})
    st = NV.load_state(tmp_path)
    assert st["done"] == ["step1b"] and st["info"]["step1b"] == {"n": 2}
    jobs = [{"job": "a"}, {"job": "b"}]
    LC.put(tmp_path / "responses" / "a.jsonl", "k", {"raw": "{}"})
    assert NV.todo_jobs(tmp_path, jobs) == [{"job": "b"}]


def test_run_all_skips_done_stages_and_saves_after_each(tmp_path, monkeypatch):
    calls, saved = [], []

    def fake_stage(name, fail=False):
        def fn(run, llm, ctx):
            calls.append(name)
            if fail:
                raise RuntimeError("crash")
            return {"ok": name}
        return fn
    monkeypatch.setattr(P, "STAGE_FN", {s: fake_stage(s, fail=(s == "dupcheck")) for s in NV.STAGES})
    llm = NV.FakeLLM()
    with pytest.raises(RuntimeError):
        P.run_all(tmp_path, llm, encoder=object, on_saved=saved.append, log=lambda *_: None)
    assert calls == ["step1b", "loop2", "step3_l2", "dupcheck"] and saved == ["step1b", "loop2", "step3_l2"]
    monkeypatch.setattr(P, "STAGE_FN", {s: fake_stage(s) for s in NV.STAGES})
    calls.clear()
    st = P.run_all(tmp_path, llm, encoder=object, on_saved=saved.append, log=lambda *_: None)   # restart after the crash
    assert calls == ["dupcheck", "step4", "contamination", "task13"] and st["done"] == list(NV.STAGES)
    assert st["info"]["step4"]["model"] == "fake"
    calls.clear()
    P.run_all(tmp_path, llm, encoder=object, stop_after="loop2", log=lambda *_: None)
    assert calls == []


def _job(tmp_path, name, family, fmt, prompt, schema, run_tag="t"):
    B.write(tmp_path / "prompts" / f"{name}.txt", prompt)
    B.write_json(tmp_path / "prompts" / f"{name}.schema.json", schema)
    return {"job": name, "family": family, "format": fmt, "run_tag": run_tag, "prompt": f"prompts/{name}.txt",
            "schema": f"prompts/{name}.schema.json", "max_tokens": 100}


def test_fake_llm_replays_then_makes_valid_answers(tmp_path):
    from s1a import pilot_input as PIN
    rep = tmp_path / "replay"
    j = _job(rep, "step1b_dev50", "s1b", "s1b", "same prompt", {"type": "object"})
    LC.put(rep / "responses" / "step1b_dev50.jsonl", "k", {"raw": '{"headings": []}'})
    out = tmp_path / "run"
    jobs = [_job(out, "step1b_dev50", "s1b", "s1b", "same prompt", {"type": "object"}),
            _job(out, "hotel_a", "a", "v2", "### L2_hotel#0", PIN._schema_attr_clusters(["L2_hotel#0", "L2_hotel#1"], ["current entity E0"])),
            _job(out, "dup", "dupcheck_l2", "dupcheck", "x", {"type": "object"})]
    llm = NV.FakeLLM([rep])
    assert llm.run(out, jobs) == {"jobs": 3, "run": 3, "parse_errors": 0}
    assert (llm.n_replayed, llm.n_made) == (1, 2)
    assert B.last_row(out / "responses" / "step1b_dev50.jsonl")["parsed"] == {"headings": []}
    a = B.last_row(out / "responses" / "hotel_a.jsonl")
    assert a["model"] == "fake" and [c["cluster_id"] for c in a["parsed"]["clusters"]] == ["L2_hotel#0", "L2_hotel#1"]
    assert llm.run(out, jobs)["run"] == 0                                   # answered jobs are skipped
    other = tmp_path / "other"
    with pytest.raises(ValueError, match="replay"):
        NV.FakeLLM([rep]).run(other, [_job(other, "step1b_dev50", "s1b", "s1b", "a changed prompt", {"type": "object"})])


class _Out:
    def __init__(self, text, n_in=5):
        self.prompt_token_ids = list(range(n_in))
        self.outputs = [type("O", (), {"text": text, "token_ids": list(range(3)), "finish_reason": "stop"})()]


class _Engine:
    """Stub vLLM engine: answers {"joins": []}; `bad_schema` makes guided batches fail."""

    def __init__(self, bad_schema=False, text='{"joins": []}'):
        self.calls, self.bad, self.text = [], bad_schema, text

    def get_tokenizer(self):
        return _Tok()

    def generate(self, texts, params):
        ps = params if isinstance(params, list) else [params] * len(texts)
        if self.bad and any(p["schema"] is not None for p in ps):
            raise ValueError("bad schema")
        self.calls.append((len(texts), [p["schema"] is not None for p in ps]))
        return [_Out(self.text) for _ in texts]


class _Tok:
    def apply_chat_template(self, msgs, tokenize, add_generation_prompt):
        return "<u>" + msgs[0]["content"]

    def __call__(self, text, add_special_tokens):
        return type("E", (), {"input_ids": text.split()})()


def _sampling(max_tokens, schema):
    return {"max_tokens": max_tokens, "schema": schema}


def test_vllm_backend_batches_caches_and_falls_back(tmp_path):
    jobs = [_job(tmp_path, f"d{i}", "dupcheck_l2", "dupcheck", f"prompt {i}", {"type": "object"}) for i in range(5)]
    eng = _Engine()
    be = NV.VllmBackend(eng, "M", "rev", _sampling, batch=2, log=lambda *_: None)
    assert be.run(tmp_path, jobs) == {"jobs": 5, "run": 5, "parse_errors": 0}
    assert [n for n, _ in eng.calls] == [2, 2, 1] and all(all(g) for _, g in eng.calls)       # guided, in batches of 2
    row = B.last_row(tmp_path / "responses" / "d0.jsonl")
    assert row["guided"] is True and row["model"] == "M" and row["revision"] == "rev" and row["params"]["guided_json"] == jobs[0]["schema"]
    assert be.run(tmp_path, jobs)["run"] == 0                                                 # cached
    assert NV.VllmBackend(eng, "M", "rev2", _sampling, log=lambda *_: None).run(tmp_path, jobs[:1])["run"] == 1   # new revision: new key
    bad = NV.VllmBackend(_Engine(bad_schema=True), "M", "rev", _sampling, log=lambda *_: None)
    other = tmp_path / "o"
    j = _job(other, "x", "dupcheck_l2", "dupcheck", "p", {"type": "object"})
    bad.run(other, [j])
    assert B.last_row(other / "responses" / "x.jsonl")["guided"] is False                     # its own schema fails: unguided
    with pytest.raises(ValueError, match="over the limit"):
        NV.VllmBackend(eng, "M", "rev", _sampling, limit=1, log=lambda *_: None).run(tmp_path / "l", [_job(tmp_path / "l", "y", "a", "v2", "a b c", {})])


def test_vllm_backend_retries_unguided_when_the_answer_does_not_parse(tmp_path):
    eng = _Engine(text="not json")
    j = _job(tmp_path, "d", "dupcheck_l2", "dupcheck", "p", {"type": "object"})
    NV.VllmBackend(eng, "M", "rev", _sampling, log=lambda *_: None).run(tmp_path, [j])
    row = B.last_row(tmp_path / "responses" / "d.jsonl")
    assert row["retried"] is True and row["errors"] and row["prompt_tokens"] == 2 * 5
    assert eng.calls[-1] == (1, [False])


def test_parse_answer_plain_and_frozen_formats():
    assert NV.parse_answer('{"a": 1}', {"format": "s1b"}, {}) == ({"a": 1}, [])
    assert NV.parse_answer("x", {"format": "s1b"}, {})[1]
    assert NV.parse_answer('{"joins": []}', {"format": "dupcheck"}, {"properties": {}}) == ({"joins": []}, [])


def test_notebook_pins_and_runs_the_pipeline():
    nb = json.loads((ROOT / "colab" / "S1A_nov16_v41_colab.ipynb").read_text(encoding="utf-8"))
    src = "".join("".join(c["source"]) for c in nb["cells"])
    for pin in ("vllm==0.33.0", "gliner==0.2.29", "sentence-transformers==5.6.0",
                "40ec419335d09393f298636f471328b722c6da9e", "5617a9f61b028005a4858fdac845db406aefb181"):
        assert pin in src, pin
    assert "NV.VllmBackend(" in src and 'P.run_all(RUN, backend, on_saved=push, copy_v4_base=SET["copy_v4_base"])' in src
    assert 'BRANCH = "wf-v4.1"' in src and 'quantization=SET["quantization"]' in src and "TAG = SETTING" in src
    cfg = json.loads(NV.MODELS_CONFIG.read_text(encoding="utf-8"))
    assert f'SETTING = "qwen32b"  #@param {json.dumps([k for k in cfg if not k.startswith("_")])}' in src   # the options = the config


# ---------------------------------------------------------------- task 9: model settings
def test_model_settings_qwen_and_llama():
    q, ll = NV.model_setting("qwen32b"), NV.model_setting("llama8b")
    assert (q["model"], q["revision"], q["quantization"]) == ("Qwen/Qwen2.5-32B-Instruct-AWQ", "5c7cb76a268fc6cfbb9c4777eb24ba6e27f9ee6c", "awq")
    assert (ll["model"], ll["quantization"]) == ("meta-llama/Llama-3.1-8B-Instruct", None) and len(ll["revision"]) == 40
    assert q["copy_v4_base"] is True and ll["copy_v4_base"] is False      # only the v4 model reuses the v4 base chain
    with pytest.raises(ValueError, match="unknown model setting"):
        NV.model_setting("gpt")


def test_fake_llm_counts_prompts_with_the_setting_tokenizer(tmp_path):
    jobs = [_job(tmp_path, "d", "dupcheck_l2", "dupcheck", "a b c d", {"type": "object"})]
    llm = NV.FakeLLM(tok=_Tok())
    llm.run(tmp_path, jobs)
    assert llm.max_prompt_tokens == 4
    with pytest.raises(ValueError, match="over the limit"):
        NV.FakeLLM(tok=_Tok(), limit=3).run(tmp_path / "o", [_job(tmp_path / "o", "d", "dupcheck_l2", "dupcheck", "a b c d", {})])


def test_task13_runs_its_own_base_chain_when_not_copying(tmp_path):
    P.stage_task13(tmp_path, NV.FakeLLM(), {"copy_v4_base": False})
    base = [c for c in B.read_json(tmp_path / "task13" / "chains.json") if c["kind"] == "base"][0]
    for k in (1, 2, 3, 4):
        assert B.last_row(tmp_path / "task13" / "responses" / f"{base['id']}_4{k}.jsonl")["model"] == "fake"   # not the v4 Qwen rows
    P.stage_task13(tmp_path / "c", NV.FakeLLM(), {"copy_v4_base": True})
    assert B.last_row(tmp_path / "c" / "task13" / "responses" / f"{base['id']}_41.jsonl")["model"] != "fake"
