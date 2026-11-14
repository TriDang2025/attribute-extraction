"""wf_v4.4 shared logging (s1a/log_v44.py): guided raw kept on retry, per-job seconds, model load time logged once."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import log_v44 as L  # noqa: E402


class _Out:
    def __init__(self, text):
        self.prompt_token_ids = list(range(5))
        self.outputs = [type("O", (), {"text": text, "token_ids": list(range(3)), "finish_reason": "length"})()]


class _Tok:
    def apply_chat_template(self, msgs, tokenize, add_generation_prompt):
        return msgs[0]["content"]

    def __call__(self, text, add_special_tokens):
        return type("E", (), {"input_ids": text.split()})()


class _Engine:
    """Guided calls answer `guided`, unguided calls answer `plain`."""

    def __init__(self, guided, plain):
        self.guided, self.plain = guided, plain

    def get_tokenizer(self):
        return _Tok()

    def generate(self, texts, params):
        ps = params if isinstance(params, list) else [params] * len(texts)
        return [_Out(self.guided if p["schema"] is not None else self.plain) for p in ps]


def _sampling(max_tokens, schema):
    return {"max_tokens": max_tokens, "schema": schema}


def _job(out, name):
    B.write(out / "prompts" / f"{name}.txt", "a prompt")
    B.write_json(out / "prompts" / f"{name}.schema.json", {"type": "object"})
    return {"job": name, "family": "dupcheck_l2", "format": "dupcheck", "run_tag": "t", "prompt": f"prompts/{name}.txt",
            "schema": f"prompts/{name}.schema.json", "max_tokens": 50}


def test_retry_keeps_the_failed_guided_raw(tmp_path):
    be = L.VllmBackend44(_Engine('{"joins": [', '{"joins": []}'), "M", "rev", _sampling, log=lambda *_: None)
    assert be.run(tmp_path, [_job(tmp_path, "d")])["parse_errors"] == 0
    row = B.last_row(tmp_path / "responses" / "d.jsonl")
    assert row["retried"] and row["guided"] is False and row["raw"] == '{"joins": []}'
    assert row["guided_raw"] == '{"joins": [' and row["guided_errors"] and row["guided_finish_reason"] == "length"
    assert row["prompt_tokens"] == 10 and row["job_seconds"] is not None
    rows = L.call_rows(tmp_path)
    assert rows[0]["guided_finish_reason"] == "length" and rows[0]["batch_size"] == 1


def test_job_seconds_splits_the_batch():
    assert L.job_seconds({"batch_seconds": 10.0, "batch_size": 4}) == 2.5
    assert L.job_seconds({"batch_seconds": None, "batch_size": 4}) is None


def test_load_time_is_written_once(tmp_path):
    p = tmp_path / "model_load.json"
    assert L.load_time(p) is None
    assert L.save_load_time(p, 61.24, "M", "rev")["load_seconds"] == 61.2
    assert L.save_load_time(p, 99)["load_seconds"] == 61.2
