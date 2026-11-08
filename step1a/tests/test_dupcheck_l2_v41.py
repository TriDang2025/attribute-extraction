"""Diary Nov 7 task 6: the v3.8 duplicate check after loop 2 Step 3, and guided JSON for every loop-2 Step 3 call."""
import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v38 as BT  # noqa: E402
from s1a import dupcheck_l2_v41 as DL  # noqa: E402
from s1a import llm_cache as LC  # noqa: E402
import step3_loop2_v41 as SC  # noqa: E402

OLD = [{"cid": 1, "name": "hotel name", "description": "", "top_values": ["acorn"], "n_mentions": 9},
       {"cid": 2, "name": "internet", "description": "", "top_values": ["wifi"], "n_mentions": 5},
       {"cid": 3, "name": "parking", "description": "", "top_values": ["parking"], "n_mentions": 4}]


def new(cid, name, n=3):
    return {"cid": cid, "name": name, "description": "d", "top_values": [name], "clusters": [f"L2_hotel#{cid}"], "n_mentions": n}


def joins(*groups):
    return {"joins": [{"columns": list(g), "reason": "r"} for g in groups]}


def test_new_columns_from_the_voted_table():
    dec = pd.DataFrame([{"cluster_id": "L2_hotel#0", "name": "has_wifi", "description": "wifi?", "action": "keep"},
                        {"cluster_id": "L2_hotel#1", "name": "Has WiFi", "description": "", "action": "merge"},
                        {"cluster_id": "L2_hotel#2", "name": "", "description": "", "action": "not_attribute"}])
    ms = lambda *v: {"mentions": [{"norm_value": x} for x in v]}   # noqa: E731
    cols = DL.new_columns(dec, {"L2_hotel#0": ms("wifi", "free wifi"), "L2_hotel#1": ms("wifi"), "L2_hotel#2": ms("x")}, 20)
    assert len(cols) == 1 and cols[0]["cid"] == 20 and cols[0]["clusters"] == ["L2_hotel#0", "L2_hotel#1"]   # same name key: one column
    assert cols[0]["top_values"] == ["wifi", "free wifi"] and cols[0]["n_mentions"] == 3


def test_resolve_same_name_both_orders_and_new_joins():
    n = [new(4, "Hotel_Name"), new(5, "has wifi"), new(6, "has parking"), new(7, "free parking", 5), new(8, "pets")]
    o0 = joins([5, 2], [6, 3], [7, 8])
    o1 = joins([2, 5], [7, 8], [1, 2])                          # 6+3 only in order 0; old-old join 1+2 ignored
    out = {r["name"]: r for r in DL.resolve(OLD, n, [o0, o1])}
    assert (out["Hotel_Name"]["status"], out["Hotel_Name"]["reason"], out["Hotel_Name"]["duplicate_of"]) == ("duplicate", "same name", ["hotel name"])
    assert (out["has wifi"]["status"], out["has wifi"]["duplicate_of"]) == ("duplicate", ["internet"])
    assert out["has parking"]["status"] == "new"                # one order is not enough
    assert out["free parking"]["status"] == "new" and out["free parking"]["joined"] == ["pets"] and "pets" not in out   # biggest member names it
    assert out["free parking"]["clusters"] == ["L2_hotel#7", "L2_hotel#8"] and out["free parking"]["n_mentions"] == 8


def test_resolve_ignores_bad_ids_and_blocks_role_pairs():
    n = [new(4, "departure time"), new(5, "arrival time")]
    both = joins([4, 5], [4, 99])
    assert [r["status"] for r in DL.resolve(OLD, n, [both, both])] == ["new", "new"]
    assert {r["name"] for r in DL.resolve(OLD, n, [both, both])} == {"departure time", "arrival time"}   # role pair: not joined
    assert all(r["status"] == "new" for r in DL.resolve(OLD, n, [joins([4, 5]), {"joins": []}]))


def test_prompts_are_the_frozen_v38_prompt_in_two_orders():
    n = [new(4, "has wifi")]
    p = DL.prompts(OLD, n, "dev50/hotel")
    assert set(p) == {0, 1}
    for text, schema in p.values():
        shown = [int(x) for x in re.findall(r"^(\d+)\. name:", text, re.M)]
        assert sorted(shown) == [1, 2, 3, 4] and text == BT.render_dupcheck([{c["cid"]: c for c in OLD + n}[i] for i in shown])
        assert schema == BT.schema_dupcheck(shown)
    assert DL.prompts(OLD, n, "dev50/hotel") == p                              # fixed shuffle


# ---------------------------------------------------------------- guided JSON
def _check_guided(odir, jobs, enum_key, id_pattern):
    """Every job has a schema file; it is a JSON object schema with required keys; its id enum equals the ids shown in the prompt; the
    answer of a schema-valid response parses without errors."""
    for j in jobs:
        assert j["schema"] and j["max_tokens"] > 0, j["job"]
        schema = json.loads((odir / j["schema"]).read_text(encoding="utf-8"))
        assert schema["type"] == "object" and schema["required"], j["job"]
        text = (odir / j["prompt"]).read_text(encoding="utf-8")
        enum = LC.schema_enum(schema, enum_key)
        assert enum and sorted(map(str, enum)) == sorted(set(re.findall(id_pattern, text, re.M))), j["job"]


@pytest.mark.parametrize("set_name", ["dev50", "dev50b"])
def test_loop2_step3_calls_use_guided_json(set_name):
    """The committed loop-2 Step 3 jobs: each call has its schema (the notebook runs every job with guided JSON from job["schema"])."""
    odir = ROOT / "results" / "wf_v41" / "step3_loop2" / set_name
    jobs = json.loads((odir / "manifest.json").read_text(encoding="utf-8"))["jobs"]
    assert jobs and all(j["format"] == "v2" and j["max_tokens"] == 12000 for j in jobs)
    _check_guided(odir, jobs, "cluster_id", r"^### (\S+)  \(mentions")


def test_dupcheck_jobs_use_guided_json(tmp_path, monkeypatch):
    """--dupcheck on the dry-run Step 3 answers (copied): every duplicate-check job has its schema; a fake guided answer parses and
    --dupcheck-apply writes columns_l2.json."""
    import shutil
    for d in ("step3_loop2", "loop2"):
        shutil.copytree(ROOT / "results" / "wf_v41" / d / "dev50", tmp_path / "wf_v41" / d / "dev50")
    monkeypatch.setattr(SC.paths, "RESULTS", tmp_path)
    a = type("A", (), {"set": "dev50"})()
    SC.dupcheck_build(a)
    odir = tmp_path / "wf_v41" / "step3_loop2" / "dev50"
    jobs = json.loads((odir / "manifest_dupcheck.json").read_text(encoding="utf-8"))["jobs"]
    assert len(jobs) == 2 and all(j["format"] == "dupcheck" and j["max_tokens"] == 1024 for j in jobs)   # hotel only, 2 orders
    _check_guided(odir, jobs, "columns", r"^(\d+)\. name:")
    cols = json.loads((odir / "new_columns.json").read_text(encoding="utf-8"))["hotel"]
    pair = [cols["new"][0]["cid"], cols["old"][0]["cid"]]       # a fake answer: the first new column twins the first old one
    for j in jobs:
        schema = json.loads((odir / j["schema"]).read_text(encoding="utf-8"))
        raw = json.dumps(joins(pair))
        parsed, errs, _ = LC.parse_job(raw, "dupcheck", schema)
        assert errs == []
        LC.put(odir / "responses" / f"{j['job']}.jsonl", j["job"] + j["run_tag"], {"job": j["job"], "guided": True, "raw": raw,
                                                                               "parsed": parsed, "errors": errs})
    SC.dupcheck_apply(a)
    final = json.loads((odir / "columns_l2.json").read_text(encoding="utf-8"))["hotel"]
    assert final[0]["status"] == "duplicate" and final[1]["status"] == "new"
    assert "| hotel |" in (odir / "dupcheck.md").read_text(encoding="utf-8")


def test_notebook_runner_reads_each_job_schema_for_guided_decoding():
    """The Colab runner that the Nov 16 notebook reuses loads job["schema"] per job and decodes with it."""
    src = "".join("".join(c["source"]) for c in json.loads((ROOT / "colab" / "S1A_llm_v39_colab.ipynb").read_text(encoding="utf-8"))["cells"])
    assert 'schemas[n] = json.loads((O / j["schema"])' in src and "guided_decoding" in src
