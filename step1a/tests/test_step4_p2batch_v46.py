"""wf_v4.6 Y8: Step 4 pass 2 in batches (s1a/step4_p2batch_v46.py, switch p2_batch of s1a/step4_v44.py), fake model only."""
import json
from pathlib import Path

import pytest

from s1a import batch_v4 as B
from s1a import pipeline_v45 as PL
from s1a import step4_fake_v43 as F43
from s1a import step4_fake_v44 as F
from s1a import step4_p2batch_v46 as P2B
from s1a import step4_v43 as V
from s1a import step4_v44 as S

CFG = S.load_config()
ALL_OFF = S.with_switches(CFG, off=S.SWITCHES)
ENTS = ("boat", "shop", "port", "crew", "ticket", "route")


def col(ent, i):
    return {"id": f"{ent}:{i}", "name": f"{ent} item {i}", "description": f"d {ent} {i}", "role": "",
            "value_type": {"dominant": "text", "share": 1.0}, "examples": [["v", "in v text"]], "n_mentions": 10, "n_dialogues": 3,
            "signal": "", "flag": ""}


def make_root(tmp_path, n):
    """n columns spread over the entities (input order kept)."""
    d = tmp_path / "root" / B.INPUT_DIR / "dev50"
    d.mkdir(parents=True)
    cols = [col(ENTS[k % len(ENTS)], k) for k in range(n)]
    B.write_json(d / "a.columns.json", cols)
    return tmp_path / "root", cols


class ByIdFake(F.FakeV44):
    """Pass 2 answers depend on the column id only (so one prompt or batches give the same assignment); the rest as FakeV44."""
    def respond(self, job, prompt, schema):
        if job["format"] != "s43_p2":
            return super().respond(job, prompt, schema)
        enum = next(iter(schema["properties"].values()))["enum"]
        return json.dumps({cid: enum[sum(map(ord, cid)) % len(enum)] for cid in schema["properties"]})


def run(out, root, cfg, seeds=(0,), backend=None):
    return S.run(out, backend or ByIdFake(), inputs=("a",), sets=("dev50",), seeds=seeds, cfg=cfg, root=root, log=lambda m: None)


def jobs_of(out, stage):
    return B.read_json(Path(out) / "manifests" / f"a_stage{stage}.json")["jobs"]


def test_off_is_the_single_prompt(tmp_path):
    root, cols = make_root(tmp_path, 25)
    assert S.with_switches(CFG, p2_batch=0) == S.with_switches(CFG) and "p2_batch" not in S.with_switches(CFG, p2_batch=None)
    cfgs = {"none": ALL_OFF, "zero": S.with_switches(ALL_OFF, p2_batch=0), "step4_config": PL.step4_config("v43")}
    texts = {}
    for k, cfg in cfgs.items():
        out = tmp_path / k
        run(out, root, cfg)
        (j,) = jobs_of(out, 2)
        assert j["job"] == "a_dev50_s0_p2" and j["max_tokens"] == V.MAX_TOKENS["s43_p2"] and j["n_columns"] == 25
        texts[k] = ((out / j["prompt"]).read_text(encoding="utf-8"), (out / j["schema"]).read_text(encoding="utf-8"))
        assert all("p2_batch" not in c for c in B.read_json(out / "chains.json"))
    assert texts["none"] == texts["zero"] == texts["step4_config"]
    ch = B.read_json(tmp_path / "none" / "chains.json")[0]
    st, err, _ = S.replay(tmp_path / "none", ch, 1, root)
    want_text, want_schema = V.build_p2(st["cols"], st["p1_names"])
    assert err is None and texts["none"] == (want_text, json.dumps(want_schema, indent=1))
    assert want_schema["required"] == [c["id"] for c in cols]


def test_batches_have_own_keyed_schema_and_same_table_list(tmp_path):
    root, cols = make_root(tmp_path, 45)
    out = tmp_path / "on"
    info = run(out, root, S.with_switches(ALL_OFF, p2_batch=20))
    assert info["finished"] == "1/1" and info["p2_batch"] == 20
    jobs = jobs_of(out, 2)
    assert [j["job"] for j in jobs] == ["a_dev50_s0_p2_b0", "a_dev50_s0_p2_b1", "a_dev50_s0_p2_b2"]
    assert [j["n_columns"] for j in jobs] == [20, 20, 5] and [j["max_tokens"] for j in jobs] == [700, 700, 250]
    ids = [c["id"] for c in B.chain_columns(B.read_json(out / "chains.json")[0], root)]      # frozen order of the chain
    got, tables = [], set()
    for b, j in enumerate(jobs):
        schema = json.loads((out / j["schema"]).read_text(encoding="utf-8"))
        text = (out / j["prompt"]).read_text(encoding="utf-8")
        assert "pattern" not in json.dumps(schema)
        assert list(schema["properties"]) == schema["required"] == ids[20 * b:20 * b + 20] and schema["additionalProperties"] is False
        assert len({json.dumps(p) for p in schema["properties"].values()}) == 1        # same enum for every column
        tables.add(next(ln for ln in text.splitlines() if ln.startswith("Tables: ")))
        assert f"Columns ({len(schema['properties'])}):" in text
        got += list(schema["properties"])
    assert got == ids and len(tables) == 1


def test_joined_answer_equals_single_answer(tmp_path):
    root, _ = make_root(tmp_path, 45)
    single, batched = tmp_path / "single", tmp_path / "batched"
    run(single, root, ALL_OFF)
    run(batched, root, S.with_switches(ALL_OFF, p2_batch=20))
    ch1, ch2 = (B.read_json(d / "chains.json")[0] for d in (single, batched))
    a1, why1 = P2B.answer(single, ch1, B.chain_columns(ch1, root))
    a2, why2 = P2B.answer(batched, ch2, B.chain_columns(ch2, root))
    assert why1 is why2 is None and a1 == a2 and len(a2) == 45
    s1, e1, _ = S.replay(single, ch1, 4, root)
    s2, e2, _ = S.replay(batched, ch2, 4, root)
    assert e1 is e2 is None and s1["assign"] == s2["assign"] and s1["ans"] == s2["ans"]


def test_missing_batch_stops_the_chain_with_a_clear_error(tmp_path):
    root, _ = make_root(tmp_path, 45)
    out = tmp_path / "on"
    cfg = S.with_switches(ALL_OFF, p2_batch=20)
    run(out, root, cfg)
    (out / "responses" / "a_dev50_s0_p2_b1.jsonl").unlink()
    ch = B.read_json(out / "chains.json")[0]
    _, err, _ = S.replay(out, ch, 4, root)
    assert err == "p2: batch b1: no response"


def test_p2_batch_value_is_checked():
    for bad in (-1, 2.5, "20", True):
        with pytest.raises(ValueError):
            S.with_switches(CFG, p2_batch=bad)


def test_300_columns_finish_and_largest_prompt_is_far_smaller(tmp_path):
    root, _ = make_root(tmp_path, 300)
    big = {}
    for k, cfg in (("single", ALL_OFF), ("batched", S.with_switches(ALL_OFF, p2_batch=20))):
        out = tmp_path / k
        assert run(out, root, cfg)["finished"] == "1/1"
        jobs = jobs_of(out, 2)
        big[k] = max(j["est_prompt_tokens"] for j in jobs)
        if k == "batched":
            assert len(jobs) == 15 and all(j["max_tokens"] <= V.MAX_TOKENS["s43_p2"] for j in jobs)
    print(f"largest pass-2 prompt, 300 columns: single {big['single']} tokens, batches of 20 {big['batched']} tokens")
    assert big["batched"] * 10 < big["single"]
