"""wf_v4 Colab batch end to end with a fake model: stage 1, stages 2-4, the placement stages, assembly. Needs results/wf_v4/inputs (scripts/inputs_v4.py)."""
import json
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

from s1a import batch_v4 as B
from s1a import batch_v4_fake as F
from s1a import llm_cache as lc
from s1a import step4_prompts as sp

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / "results" / "wf_v4" / "inputs" / "dev50" / "a.columns.json").exists(), reason="run scripts/inputs_v4.py first")
N_PLACE = 5            # held-out columns of config/wf_v4_placement.json: hotel:18, restaurant:10, train:7 + train:8, train:14


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    """Stages 1 .. 9 into a temporary folder; returns (folder, {stage: jobs})."""
    out = tmp_path_factory.mktemp("colab")
    stages = {1: B.build_stage1(ROOT, out)}
    for k in range(1, 5 + N_PLACE):
        assert F.run_jobs(out, stages[k]) == 0                       # 0 parse errors
        if k < 4 + N_PLACE:
            stages[k + 1] = B.build_stage(out, k + 1, ROOT)
    return out, stages


def test_stage_job_counts(run):
    _, st = run
    assert {k: len(v) for k, v in st.items()} == {1: 31, 2: 25, 3: 25, 4: 25, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2}
    assert dict(Counter(j["family"] for j in st[1])) == {"s4_41": 25, "s4_e": 6}        # 24 chains + the placement base chain; 3 orders x 2 sets
    assert [j["family"] for j in st[2][:1] + st[3][:1] + st[4][:1] + st[5][:1]] == ["s4_42", "s4_43", "s4_44", "s4_place"]
    assert sum(len(v) for v in st.values()) == 116


def test_manifest_fields_and_limits(run):
    out, st = run
    for k, jobs in st.items():
        man = json.loads((out / ("manifest.json" if k == 1 else f"manifest_stage{k}.json")).read_text(encoding="utf-8"))
        assert man["stage"] == k and man["jobs"] == jobs
        for j in jobs:
            assert j["stage"] == k and j["round"] == 0 and j["format"] == j["family"] and j["max_tokens"] == B.MAX_TOKENS[j["family"]]
            assert (out / j["prompt"]).exists() and json.loads((out / j["schema"]).read_text(encoding="utf-8"))
            assert j["est_prompt_tokens"] < (B.LIMIT_FIRST if j["family"] in B.FIRST_STEPS else B.LIMIT_ANY)
    assert B.MAX_TOKENS == {"s4_41": 6000, "s4_42": 3000, "s4_43": 3000, "s4_44": 6000, "s4_e": 8000, "s4_place": 1000}
    names = [j["job"] for jobs in st.values() for j in jobs]
    assert len(names) == len(set(names))


def test_chain_inputs_and_orders(run):
    out, st = run
    chains = {c["id"]: c for c in B.read_json(out / "chains.json")}
    assert len(chains) == 25 and sum(c["kind"] == "main" for c in chains.values()) == 24 and chains["base_dev50_s0"]["kind"] == "base"
    first = {j["chain"]: (out / j["prompt"]).read_text(encoding="utf-8") for j in st[1] if j["family"] == "s4_41"}
    assert "data signals:" in first["b_dev50_s0_41".replace("_41", "")] and "data signals:" not in first["a_dev50_s0"]
    assert "[gt:1]" in first["c1_dev50_s1"] and "gt:" not in first["a_dev50_s0"]
    assert first["a_dev50_s1"] != first["a_dev50_s0"] != first["a_dev50_s2"]               # seeds reorder the columns
    assert all("multiwoz" not in t.lower() for t in first.values())
    plc = B.read_json(out / "placement.json")
    base = first["base_dev50_s0"]
    assert all(f"[{c}]" not in base for c in plc["hold_out"]) and all(f"[{c}]" in first["a_dev50_s0"] for c in plc["hold_out"])
    assert len(plc["steps"]) == N_PLACE and [a["kind"] for a in plc["attributes"]] == ["P1", "P2", "P3", "P4"]


def test_placement_prompts_sig_vs_nosig_and_state_carries(run):
    out, st = run
    sig = (out / "prompts" / "place_sig_0.txt").read_text(encoding="utf-8")
    nosig = (out / "prompts" / "place_nosig_0.txt").read_text(encoding="utf-8")
    assert "data signals:" in sig and "data signals:" not in nosig
    plc = B.read_json(out / "placement.json")
    last = (out / "prompts" / f"place_nosig_{N_PLACE - 1}.txt").read_text(encoding="utf-8")
    assert f"[{plc['steps'][-1]['column']}]" in last
    assert "stars" in last.lower() or plc["steps"][0]["column"] == "hotel:18"       # the first placed column is part of the later schema
    first_col = B.place_column(out, 0, "nosig", ROOT)["name"]
    assert first_col in last


def test_assemble_all_files_and_sql(run):
    out, _ = run
    status = B.assemble_all(out, ROOT)
    assert len(status) == 25 + 6 + 2 and all(r["ok"] for r in status), [r for r in status if not r["ok"]][:3]
    for tag in ("a_dev50_s0", "c1_dev50b_s2", "base_dev50_s0", "e_dev50_v1", "place_sig", "place_nosig"):
        d = out / "final" / tag
        c = json.loads((d / "canonical.json").read_text(encoding="utf-8"))
        assert c["tables"] and (d / "operations.json").exists()
        sqlite3.connect(":memory:").executescript((d / "schema.sql").read_text(encoding="utf-8"))
    ops = json.loads((out / "final" / "a_dev50_s0" / "operations.json").read_text(encoding="utf-8"))
    assert [o["op"] for o in ops][0] == "CREATE_ENTITY" and any(o["op"] == "ADD_ATTR" and o["source"] == "train:1" for o in ops)
    c1 = json.loads((out / "final" / "c1_dev50_s0" / "canonical.json").read_text(encoding="utf-8"))
    assert all(col["gt"] for t in c1["tables"] for col in t["columns"] if col["source"])      # c1 columns carry their GT name for the scorer
    for j in range(N_PLACE):
        assert (out / "final" / "place_sig" / f"canonical_{j}.json").exists()
    final = json.loads((out / "final" / "place_sig" / "canonical.json").read_text(encoding="utf-8"))
    placed = {c["source"] for t in final["tables"] for c in t["columns"]}
    assert set(B.read_json(out / "placement.json")["hold_out"]) - {"train:10"} <= placed    # every placed column ends up in the schema
    assert "train:10" not in placed                                                        # also_hold_out: held out and never placed


def test_stopped_chain_is_skipped_and_reported(run, tmp_path):
    out, st = run
    cut = tmp_path / "colab"
    shutil.copytree(out, cut)
    (cut / "responses" / "a_dev50_s1_42.jsonl").unlink()
    rows = (cut / "responses" / "b_dev50_s0_41.jsonl").read_text(encoding="utf-8").splitlines()
    bad = json.loads(rows[-1])
    bad["errors"] = ["boom"]
    (cut / "responses" / "b_dev50_s0_41.jsonl").write_text(json.dumps(bad) + "\n", encoding="utf-8")
    jobs = B.build_stage(cut, 3, ROOT)
    assert len(jobs) == 23 and "a_dev50_s1_43" not in {j["job"] for j in jobs} and "b_dev50_s0_43" not in {j["job"] for j in jobs}
    status = {s["chain"]: s for s in B.read_json(cut / "chain_status_stage3.json")}
    assert not status["a_dev50_s1"]["ok"] and "no response" in status["a_dev50_s1"]["error"] and "parse errors" in status["b_dev50_s0"]["error"]
    assert B.assemble_all(cut, ROOT) and not next(r for r in B.read_json(cut / "final" / "status.json") if r["run"] == "b_dev50_s0")["ok"]


# ---- repairs and the fake model

def test_repair_41_and_43():
    cols = [{"id": f"x:{i}"} for i in range(1, 5)]
    a, n = B.repair_41({"groups": [{"group": "G1", "columns": ["x:1", "x:2"], "note": ""}, {"group": "G2", "columns": ["x:2", "x:3"], "note": ""}],
                        "unused": [{"column": "x:1", "reason": "r"}], "duplicate_flags": []}, cols)
    assert [g["columns"] for g in a["groups"]] == [["x:1", "x:2"], ["x:3"]] and a["unused"] == [{"column": "x:4", "reason": "not placed by the model"}] and n == 3
    assert sp.validate_41(a, cols) == []
    a41 = {"groups": [{"group": "G1", "columns": ["x:1"], "note": ""}, {"group": "G2", "columns": ["x:2"], "note": ""}], "unused": [], "duplicate_flags": []}
    a42 = {"tables": [{"group": "G1", "name": "t1", "description": "d", "row": "r"}, {"group": "G2", "name": "t2", "description": "d", "row": "r"}]}
    a43 = {"relationships": [{"from": "t1", "to": "t2", "kind": "one_to_many", "reason": ""}, {"from": "t1", "to": "t2", "kind": "one_to_many", "reason": ""},
                             {"from": "t1", "to": "zzz", "kind": "one_to_many", "reason": ""}, {"from": "t2", "to": "t2", "kind": "one_to_many", "reason": ""}],
           "new_tables": [{"name": "t1", "description": "", "row": "", "between": ["t1", "t2"]}, {"name": "l", "description": "", "row": "", "between": ["t1", "t2"]}]}
    fixed, n = B.repair_43(a43, a41, a42)
    assert len(fixed["relationships"]) == 1 and [t["name"] for t in fixed["new_tables"]] == ["l"] and n == 4
    assert sp.validate_43(fixed, a41, a42) == []


def test_fake_answers_fit_their_schema(run):
    out, st = run
    js = pytest.importorskip("jsonschema")
    for jobs in st.values():
        for j in jobs[:3] + jobs[-1:]:
            row = B.last_row(out / "responses" / f"{j['job']}.jsonl")
            js.Draft202012Validator(json.loads((out / j["schema"]).read_text(encoding="utf-8"))).validate(json.loads(row["raw"]))
            assert row["errors"] == [] and lc.parse_job(row["raw"], j["format"], json.loads((out / j["schema"]).read_text(encoding="utf-8")))[1] == []
