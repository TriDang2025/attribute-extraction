"""wf_v4.3 U5 / U6 checks: repair replay (s1a/repairs_v43.py) and cost table (s1a/cost_v43.py), on tiny fake inputs."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import cost_v43 as C  # noqa: E402
from s1a import keyed_v42 as K  # noqa: E402
from s1a import repairs_v43 as R  # noqa: E402
from s1a.log_v43 import RepairLog  # noqa: E402

COLS = [{"id": f"x:{i}", "name": f"col {i}", "value_type": "text"} for i in (1, 2, 3)]
CHAIN = {"id": "t_s0", "input": "x", "set": "s", "seed": 0, "exclude": [], "columns_file": "cols.json"}
A41 = {"groups": [{"group": "G1", "columns": ["x:1", "x:1", "x:9"], "note": ""}, {"group": "G2", "columns": ["x:2"], "note": ""}],
       "unused": [], "duplicate_flags": []}
RAW42 = json.dumps({"tables": {"G1": {"name": "Thing", "description": "d", "row": "r"}, "G2": {"name": "thing", "description": "d", "row": "r"}}})
A43 = {"relationships": [{"from": "Thing", "to": "ghost", "kind": "one_to_many", "reason": ""},
                         {"from": "Thing", "to": "Thing", "kind": "one_to_many", "reason": ""},
                         {"from": "Thing", "to": "thing_g2", "kind": "one_to_many", "reason": ""}],
       "new_tables": [{"name": "bad", "description": "", "row": "", "between": ["Thing"]}]}


def put(out, name, **row):
    p = Path(out) / "responses" / f"{CHAIN['id']}_{name}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"errors": [], **row}) + "\n", encoding="utf-8")


def fake_run(tmp_path):
    (tmp_path / "cols.json").write_text(json.dumps(COLS), encoding="utf-8")
    out = tmp_path / "run"
    put(out, "41", parsed=A41, raw=json.dumps(A41))
    put(out, "42", parsed=json.loads(K.unkey("s4_42", RAW42)), raw=RAW42)
    put(out, "43", parsed=A43, raw=json.dumps(A43))
    return out


def test_typed_41_matches_frozen_and_counts_types():
    typed, n = R.typed_41(A41, COLS)
    fixed, total = B.repair_41(A41, COLS)
    assert typed == fixed and sum(n.values()) == total
    assert dict(n) == {"col_unknown": 1, "col_twice": 1, "col_unplaced": 1}


def test_typed_41_switch_off_leaves_the_error():
    fixed, _ = R.typed_41(A41, COLS, off={"col_unplaced"})
    assert fixed["unused"] == []


def test_replay_counts_all_steps_and_rename(tmp_path):
    out = fake_run(tmp_path)
    t = R.replay_typed(out, CHAIN, tmp_path, upto=3)
    assert t["error"] is None
    assert dict(t["counts"]) == {"col_unknown": 1, "col_twice": 1, "col_unplaced": 1, "name_renamed": 1, "new_table_invalid": 1,
                                 "rel_unknown_table": 1, "rel_self": 1}
    assert [x["name"] for x in t["ans"]["42"]["tables"]] == ["Thing", "thing_g2"]


def test_typed_replay_equals_frozen_replay(tmp_path):
    out = fake_run(tmp_path)
    assert R.check_against_frozen(out, CHAIN, tmp_path)


def test_switching_a_repair_off_makes_the_validator_fail(tmp_path):
    out = fake_run(tmp_path)
    assert "duplicate table name" in R.replay_typed(out, CHAIN, tmp_path, off={"name_renamed"}, upto=2)["error"]
    assert "4.3" in R.replay_typed(out, CHAIN, tmp_path, off={"rel_unknown_table"}, upto=3)["error"]
    lenient = R.replay_typed(out, CHAIN, tmp_path, off={"rel_unknown_table"}, upto=3, strict=False)
    assert lenient["error"] is None and lenient["ignored"]
    res = R.ablate(out, CHAIN, tmp_path, {"rel_unknown_table"}, lambda c, ch: [], strict=True)
    assert res["ok"] is False and res["off"] == "rel_unknown_table"


def test_events_and_chain_repairs(tmp_path):
    out = fake_run(tmp_path)
    put(out, "43", parsed=A43, raw="{}", retried=True, guided=False, finish_reason="length")
    assert dict(R.events(out, CHAIN)) == {"unguided_retry": 1, "unguided_job": 1, "cut_off": 1}
    log, st = R.chain_repairs(out, CHAIN, tmp_path)
    assert log.counts["unguided_retry"] == 1 and log.counts["col_unknown"] == 1 and st["error"].startswith("4.4")


def test_repair_log_examples_come_with_the_items(tmp_path):
    out = fake_run(tmp_path)
    log = RepairLog(keep=1)
    R.replay_typed(out, CHAIN, tmp_path, upto=3, log=log)
    assert json.loads(log.examples["rel_unknown_table"][0]["detail"])["to"] == "ghost"
    assert R.snippet('{ "a":\n  "b" }', '"b"', 20) == '{ "a": "b" }'


def test_side_by_side_reads_repairs_json_of_new_chains(tmp_path):
    for name, counts in (("c1_s0", {"col_missing": 3, "rel_self": 1}), ("c1_s1", {"col_missing": 2, "fk_x": 4})):
        log = RepairLog()
        for k, n in counts.items():
            for _ in range(n):
                log.add(k, name)
        log.save(tmp_path / "u4" / "final" / name / "repairs.json")
    new = R.load_repairs(tmp_path / "u4")
    assert sorted(new) == ["final/c1_s0", "final/c1_s1"]
    rows = R.side_by_side({"old_a": {"col_missing": 10, "name_renamed": 2}}, new)
    by = {r["type"]: r for r in rows}
    assert (by["col_missing"]["old"], by["col_missing"]["new"]) == (10, 5)
    assert (by["name_renamed"]["old"], by["name_renamed"]["new"], by["name_renamed"]["step"]) == (2, 0, "4.2")
    assert (by["fk_x"]["old"], by["fk_x"]["new"], by["fk_x"]["step"]) == (0, 4, "?")
    assert by["total"]["old"] == 12 and by["total"]["new"] == 10 and rows[-1] is by["total"]
    assert R.load_repairs(tmp_path / "missing") == {}


# ---------------------------------------------------------------- U6
def row(job, secs, pt=100, ot=10, retried=None, fin="stop", guided=True):
    return {"job": job, "format": "x", "prompt_tokens": pt, "output_tokens": ot, "batch_seconds": secs, "finish_reason": fin,
            "guided": guided, "retried": retried}


def write_rows(out, name, rows):
    p = Path(out) / "responses" / f"{name}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_set_and_stage_of_names():
    assert C.set_of("hotel_a_v22d50_s0") == "dev50" and C.set_of("hotel_a_v22d50b_s0") == "dev50b"
    assert C.set_of("c1_dev50b_s2_43") == "dev50b" and C.set_of("c1_dev50_s2_43") == "dev50" and C.set_of("place_sig_0") == "other"
    assert C.stage_of("responses/c1_dev50_s0_42.jsonl") == "42" and C.stage_of("responses/hotel_a_v22d50_s0.jsonl") == "all"


def test_gpu_seconds_counts_each_batch_once(tmp_path):
    from s1a.log_v43 import call_rows
    # stage 41: 3 jobs share one batch of 30 s; stage 42: one batch of 12 s; stage 41 retry (batch of 1) 5 s
    write_rows(tmp_path, "a_dev50_s0_41", [row("a_dev50_s0_41", 30.0)])
    write_rows(tmp_path, "a_dev50_s1_41", [row("a_dev50_s1_41", 30.0)])
    write_rows(tmp_path, "a_dev50b_s0_41", [row("a_dev50b_s0_41", 5.0, retried=True)])
    write_rows(tmp_path, "a_dev50_s0_42", [row("a_dev50_s0_42", 12.0)])
    write_rows(tmp_path, "a_dev50_s1_42", [row("a_dev50_s1_42", 12.0)])
    assert C.gpu_seconds(call_rows(tmp_path)) == 47.0
    assert C.gpu_seconds([{"batch_seconds": None, "file": "x.jsonl"}]) == 0


def test_run_stats_per_set_retries_and_fake_runs_ignored(tmp_path):
    write_rows(tmp_path, "hotel_a_v22d50_s0", [row("hotel_a_v22d50_s0", 10.0, 100, 20, retried=True)])
    write_rows(tmp_path, "hotel_a_v22d50b_s0", [row("hotel_a_v22d50b_s0", 10.0, 50, 5)])
    write_rows(tmp_path / "fake" / "final", "hotel_a_v22d50_s1", [row("hotel_a_v22d50_s1", 1.0)])
    st = C.run_stats(tmp_path)
    assert st["gpu_seconds"] == 10.0 and st["rows"] == 2
    assert st["dev50"] == {"calls": 2, "jobs": 1, "retries": 1, "prompt_tokens": 100, "output_tokens": 20}
    assert st["dev50b"]["calls"] == 1 and st["both"]["prompt_tokens"] == 150
    assert C.run_stats(tmp_path / "nothing") is None and C.run_stats(tmp_path / "fake" / "empty") is None


def test_load_seconds_only_from_a_load_key(tmp_path):
    assert C.load_seconds(tmp_path, tmp_path / "missing") is None
    (tmp_path / "run_info.json").write_text(json.dumps({"stage1": {"jobs": 1}, "model_load_seconds": 90}), encoding="utf-8")
    assert C.load_seconds(tmp_path) == 90


def test_corpus_tokens_estimate_and_tokenizer():
    assert C.corpus_tokens(["a" * 40, "b" * 20]) == (15, "est.")

    class Tok:
        def __call__(self, text, add_special_tokens):
            return type("R", (), {"input_ids": text.split()})()
    assert C.corpus_tokens(["a b c", "d"], Tok()) == (4, "tok")


def test_cost_table_option_b_filled_v43_not_run(tmp_path):
    write_rows(tmp_path / "s3", "hotel_a_v22d50_s0", [row("hotel_a_v22d50_s0", 60.0, 1000, 100)])
    write_rows(tmp_path / "s4", "c1_dev50b_s0_41", [row("c1_dev50b_s0_41", 120.0, 3000, 300)])
    steps = {"option B": {"step3": C.run_stats(tmp_path / "s3"), "step4": C.run_stats(tmp_path / "s4"), "post": None},
             "v4.3": {"step3": None, "step4": None, "post": None}}
    rows = C.cost_rows(steps, {"dev50": (500, "tok"), "dev50b": (500, "est.")}, {"option B": None, "v4.3": None})
    by = {r["row"]: r for r in rows}
    assert by["Step 3 calls"]["option B dev50"] == 1 and by["Step 3 calls"]["option B dev50b"] == 0
    assert by["Step 4 tokens in"]["option B both"] == 3000 and by["Step 4 tokens in"]["v4.3 both"] == C.NOT_RUN
    assert by["GPU minutes total (model time, batches counted once)"]["option B both"] == 3.0
    assert by["Model loading time"]["option B both"] == C.NOT_LOGGED and by["Model loading time"]["v4.3 both"] == C.NOT_RUN
    assert by["Corpus tokens"]["option B both"] == 1000
    assert by["LLM tokens / corpus tokens (in + out)"]["option B dev50"] == round(1100 / 500, 1)
    assert "Post-step (U0) calls" not in by
    md = C.to_markdown(rows)
    assert md.startswith("| row | option B dev50") and "not run" in md and "1,100" in md


def test_cost_table_has_a_post_step_row_when_u0_ran(tmp_path):
    write_rows(tmp_path / "u0", "post_dev50_0", [row("post_dev50_0", 6.0, 10, 2)])
    steps = {"v4.3": {"step3": None, "step4": None, "post": C.run_stats(tmp_path / "u0")}}
    by = {r["row"]: r for r in C.cost_rows(steps, {"dev50": (10, "tok"), "dev50b": (10, "tok")}, {"v4.3": 120})}
    assert by["Post-step (U0) calls"]["v4.3 dev50"] == 1 and by["Post-step (U0) calls"]["v4.3 dev50b"] == 0
    assert by["Model loading time"]["v4.3 both"] == 2.0
