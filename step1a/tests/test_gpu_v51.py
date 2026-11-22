"""wf_v5.1 R5 driver (scripts/gpu_v51.py): guards, switches off = v5.0, column clash, the whole flow with the laptop fakes. No GPU, no real LLM."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import gpu_v51 as G  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import rolenames_v51 as RN  # noqa: E402
from s1a import step3_v44 as S3  # noqa: E402

needs_data = pytest.mark.skipif(bool(G.need()), reason=f"R5 inputs missing (run scripts/gpu_v51.py --prepare): {G.need()[:2]}")


def write_row(folder, job, **row):
    p = Path(folder) / "responses" / f"{job}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"job": job, "guided": True, "finish_reason": "stop", **row}) + "\n", encoding="utf-8")


class StubBackend:
    model_id = "stub"

    def __init__(self, **row):
        self.row, self.runs = row, 0

    def run(self, folder, jobs):
        self.runs += 1
        for j in jobs:
            write_row(folder, j["job"], **self.row)
        return {"jobs": len(jobs)}


# ---------------------------------------------------------------- guards
def test_guarded_counts_jobs_and_stops_before_the_limit(tmp_path):
    inner = StubBackend()
    g = G.Guarded(inner, 5, "t")
    g.run(tmp_path, [{"job": f"a{i}"} for i in range(3)])
    assert g.calls == 3 and g.model_id == "stub"            # other attributes are passed on
    with pytest.raises(G.CallLimit):
        g.run(tmp_path, [{"job": f"b{i}"} for i in range(3)])
    assert inner.runs == 1                                    # the second run never started


@pytest.mark.parametrize("row", [{"finish_reason": "error"}, {"guided_finish_reason": "error"}, {"guided": False}])
def test_guarded_raises_on_lost_guided_decoding(tmp_path, row):
    with pytest.raises(G.GuidedError):
        G.Guarded(StubBackend(**row), 10).run(tmp_path, [{"job": "x"}])
    if row.get("guided") is False:
        with pytest.raises(G.GuidedError):
            G.assert_guided(tmp_path)


def test_guarded_accepts_a_retried_row_that_stayed_guided(tmp_path):
    G.Guarded(StubBackend(retried=True, guided_finish_reason="stop"), 10).run(tmp_path, [{"job": "x"}])
    G.assert_guided(tmp_path)


def engine(finish, text):
    out = SimpleNamespace(finish_reason=finish, text=text)
    return SimpleNamespace(generate=lambda prompts, params: [SimpleNamespace(outputs=[out])])


@pytest.mark.parametrize("finish,text,ok", [("stop", '{"a": "x"}', True), ("error", '{"a": "x"}', False), ("stop", "oops", False),
                                            ("stop", '{"a": "z"}', False), ("length", '{"a": "x"}', False)])
def test_smoke_test(finish, text, ok):
    args = (engine(finish, text), lambda n, schema: (n, schema), lambda t: t)
    if ok:
        assert G.smoke_test(*args) == (finish, text)
    else:
        with pytest.raises(G.GuidedError):
            G.smoke_test(*args)


def test_context_split_setting_is_the_v50_big40():
    import g3_ctxsplit_v50 as G3S
    assert G.CTX == G3S.VARIANTS["big40"]


def test_frozen_step4_variant_is_registered():
    assert G.G48.VARIANTS[G.VARIANT] == G.G48.VARIANTS["ARM"]
    cfg = G.G48.config(G.VARIANT)
    assert cfg["p2_batch"] == 20


# ---------------------------------------------------------------- vectors
def test_cached_enc_fallback_counts_new_texts(tmp_path):
    for dev in G.SETS:
        (tmp_path / dev).mkdir()
        np.savez(tmp_path / dev / "vectors.npz", texts=np.array([f"{dev}_a"]), x=np.ones((1, 3), dtype=np.float32))
    fb = SimpleNamespace(encode=lambda texts: np.zeros((len(texts), 3)))
    enc = G.G50.CachedEnc(tmp_path, "vectors.npz", fallback=fb)
    x = enc.encode(["dev50_a", "new"])
    assert x.shape == (2, 3) and enc.fallback_texts == 1 and x[0].sum() == 3
    enc.encode(["new"])
    assert enc.fallback_texts == 1                            # kept, not encoded twice
    with pytest.raises(KeyError):
        G.G50.CachedEnc(tmp_path, "vectors.npz").encode(["new"])


@needs_data
def test_prepared_vectors_cover_the_context_texts_and_every_mention_value():
    enc = G.G50.CachedEnc(G.R5, "vectors.npz")
    for dev in G.SETS:
        mt = G.CS.mention_table(dev)
        enc.encode(sorted({G.F.norm(v) for v in mt["norm_value"] if v} - {""}))


# ---------------------------------------------------------------- switches off = v5.0
@needs_data
def test_switches_off_give_the_v50_step3_prompts(tmp_path):
    res = G.regression_check(tmp_path)
    assert all(r["equal"] == r["in_v50"] >= 300 for r in res.values())


@needs_data
def test_default_g4_jobs_are_the_v50_ones(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    G.G50.g4_jobs("dev50", "c_n50", tmp_path)
    for f in (G.G50.G4 / "dev50" / "prompts").glob("*.txt"):
        assert (tmp_path / "dev50" / "prompts" / f.name).read_bytes() == f.read_bytes().replace(b"\r\n", b"\n")


@needs_data
def test_step3_default_and_explicit_off_runs_are_identical(tmp_path):
    """pipeline_v45.step3 with no switches (the v5.0 call) and with both v5.1 switches False: same prompts, answers and final columns."""
    run, dev, outs = "c_n50b", "dev50b", []
    for tag, sw in (("default", None), ("off", {k: False for k in G.SWITCHES})):
        out = tmp_path / tag
        cfg = S3.load_config(switches=sw) if sw else None
        with PL.use_corpus(run, B.read_json(G.Y3 / dev / "entities.json"), G.Y3 / dev / "a_prompts"):
            PL.step3(run, out, G.G46.Fakes().s3, S3.FakeEncoder(), cfg=cfg)
        outs.append(out)
    a, b = outs
    files = sorted(p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file() and p.name != "config_used.json")
    assert len(files) > 500 and files == sorted(p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file() and p.name != "config_used.json")
    assert all((a / f).read_bytes() == (b / f).read_bytes() for f in files if not f.endswith(".npz"))
    assert not list(a.glob("*clash*"))


# ---------------------------------------------------------------- column clash
@needs_data
def test_column_clash_asks_for_columns_that_share_a_name(tmp_path, monkeypatch):
    """v5.0 G4 named both train time parts "departure time": the check asks one question and applies the answer."""
    monkeypatch.chdir(ROOT)
    run, dev = "c_n50", "dev50"
    final = B.read_json(G.G50.G4 / "run" / dev / "step3" / "scores" / "final_columns.json")[run]
    same = [c for c in final["train_info"] if c["name"] == "departure time"]
    assert len(same) >= 2
    final2, rows, info = G.column_clash(dev, run, final, tmp_path, G.Fakes51().s3, "v1", log=lambda *_: None)
    assert info["pairs"] >= 1
    prompt = next((tmp_path / "prompts").glob("*clashq*.txt")).read_text(encoding="utf-8")
    assert RN.CONTEXT_HEAD.split(" (")[0] in prompt and "two different roles" in prompt
    shared = {c["cid"] for e in final for c in final[e] if sum(x["name"] == c["name"] for x in final[e]) > 1}
    assert rows and all(r["cid"] in shared and r["new"] != r["old"] for r in rows)
    changed = [(e, c["cid"]) for e in final for c, c0 in zip(final2[e], final[e]) if c["name"] != c0["name"]]
    assert sorted(changed) == sorted((r["entity"], r["cid"]) for r in rows)
    assert [c["cid"] for c in final2["train_info"]] == [c["cid"] for c in final["train_info"]]


def test_clash_state_leaves_unique_names_out():
    cols = [{"cid": 1, "name": "a b", "mention_ids": [1]}, {"cid": 2, "name": "a b", "mention_ids": [2]}, {"cid": 3, "name": "c", "mention_ids": [3]}]
    if not (G.Y3 / "dev50" / "entities.json").exists():
        pytest.skip("Y3 missing")
    ent = next(iter(B.read_json(G.Y3 / "dev50" / "entities.json")))
    doc, state, ids = G.clash_state("dev50", "c_n50", {ent: cols}, lambda e, c: (G.G50.block_id(e, c["cid"]), f"block {c['cid']}"))
    (key, st), = state.items()
    assert key == ("c_n50", ent, 0) and list(st["names"].values()) == ["a_b", "a_b"] and sorted(ids.values()) == [[1], [2]]
    assert list(doc[f"c_n50/{ent}"]["blocks"]) == st["frozen_ids"]


# ---------------------------------------------------------------- the whole flow with fakes
@needs_data
def test_fake_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    before = sorted(p.relative_to(G.R5).as_posix() for p in G.R5.rglob("*"))
    cost = G.fake_check(tmp_path)
    assert sorted(p.relative_to(G.R5).as_posix() for p in G.R5.rglob("*")) == before          # nothing written into the repo results
    for dev in G.SETS:
        assert cost["step3"][dev]["calls"] > 300 and cost["step4"][dev]["calls"] > 30
        for stage in cost.values():
            assert stage[dev]["guided"] == stage[dev]["calls"]
        d = tmp_path / dev
        assert (d / "step3" / "scores" / "final_columns.json").exists() and (d / "ctxsplit" / "final_columns.json").exists()
        assert (d / "input" / "a_llama44" / G.SETS[dev] / "a.columns.json").exists()
        status = B.read_json(d / f"step4_{G.VARIANT}" / "final" / "status.json")
        assert [r["ok"] for r in status] == [True] * len(G.SEEDS)
        assert RN.CONTEXT_HEAD in (d / "step3" / "prompts" / f"{next(iter(B.read_json(G.Y3 / dev / 'entities.json')))}_names_{G.SETS[dev]}_s0_b1.txt").read_text(encoding="utf-8")
        assert B.read_json(d / "step3" / "config_used.json")["switches"]["name_clash"] is True
        assert (tmp_path / "rename" / "w2" / dev / "a2.columns.json").exists()                 # loop 2 replayed
    assert (tmp_path / "calls.csv").exists()
    assert "step3" in cost and "rename" in cost and "step4" in cost


def test_cost_report_leaves_assembled_rows_out(tmp_path):
    write_row(tmp_path / "dev50" / "step3", "real", prompt_tokens=10, output_tokens=2, batch_seconds=1.0, batch_size=2)
    write_row(tmp_path / "dev50" / "step3", "assembled", model="assembled by code")
    res = G.cost_report(tmp_path, {"dev50": "c_n50"})
    assert res["step3"]["dev50"]["calls"] == 1 and res["step3"]["dev50"]["prompt_tokens"] == 10 and res["step3"]["dev50"]["guided"] == 1
    assert res["rename"]["dev50"]["calls"] == 0 and res["step4"]["dev50"]["calls"] == 0
