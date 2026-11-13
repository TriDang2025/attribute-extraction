"""wf_v4.3 U0 / U2: Step 3 on Llama (s1a/step3_v43.py, s1a/step3_post_v43.py, scripts/u0_step3_post_v43.py, scripts/u2_step3_v43.py).
The end-to-end tests run every stage with the fake model on the real frozen inputs (about 2 minutes together)."""
import importlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

from s1a import batch_v4 as B
from s1a import nov16_v41 as NV
from s1a import step3_post_v43 as PP
from s1a import step3_v43 as S3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
need_data = pytest.mark.skipif(not (PP.T1B / "manifest.json").exists() or not (ROOT / "results" / "graph_v22_dev50" / "spans" / "vectors.npz").exists(),
                               reason="wf_v4.2 option B answers or bge-m3 vectors not in this checkout")


def frozen_prompts():
    return sorted((PP.T1B / "prompts").glob("*_a_v22d50*_s?.txt"))


# ---------------------------------------------------------------- pure pieces
def test_names_schema_shape():
    ids = ["E1#0", "E1#12", "E1#3"]
    s = S3.names_schema(ids)
    assert list(s["properties"]) == ids and s["required"] == ids and s["additionalProperties"] is False
    pat = re.compile(s["properties"]["E1#0"]["pattern"])
    assert s["properties"]["E1#0"]["maxLength"] == S3.NAME_MAX == 60
    for ok in ("departure_time", "not_attribute", "a1"):
        assert pat.fullmatch(ok)
    for bad in ("Departure_Time", "departure time", "_end", "1st_name", "x"):
        assert not pat.fullmatch(bad)
    assert "attributes" not in s["properties"]


def test_batches_cover_each_item_once():
    for n in (1, 4, 5, 6, 23):
        items = list(range(n))
        cut = S3.batches(items)
        assert [x for b in cut for x in b] == items and all(1 <= len(b) <= 5 for b in cut)
        assert all(len(b) == 5 for b in cut[:-1])


def test_validate_and_merge_names():
    ids = ["E1#0", "E1#1", "E1#2"]
    m, errs = S3.validate_names(json.dumps({"E1#0": "Departure-Time", "E1#1": "not_attribute", "E1#2": " arrival time "}), ids)
    assert errs == [] and m == {"E1#0": "departure_time", "E1#1": "not_attribute", "E1#2": "arrival_time"}
    m, errs = S3.validate_names(json.dumps({"E1#0": "x", "E1#9": "y", "E1#1": ""}), ids)
    assert any("missing cluster E1#2" in e for e in errs) and any("unknown key" in e for e in errs) and any("bad name" in e for e in errs)
    assert S3.validate_names("not json", ids)[1] and S3.validate_names("[1]", ids)[1]
    # names of two batches merge by exact (normalised) match; a cluster in two batches is a bug
    merged, shared = S3.merge_names([{"E1#0": "departure_time", "E1#1": "not_attribute"}, {"E1#2": "departure_time", "E1#3": "price"}])
    assert merged == {"E1#0": "departure_time", "E1#1": "not_attribute", "E1#2": "departure_time", "E1#3": "price"} and shared == ["departure_time"]
    with pytest.raises(ValueError):
        S3.merge_names([{"E1#0": "a"}, {"E1#0": "b"}])
    obj = S3.v2_object(merged, ["E1#0", "E1#1", "E1#2", "E1#3", "E1#4"])
    assert [a["name"] for a in obj["attributes"]] == ["departure_time", "price"]       # no not_attribute, every name used
    assert [c["cluster_id"] for c in obj["clusters"]] == ["E1#0", "E1#1", "E1#2", "E1#3"]   # E1#4 has no name: left out


def test_end_names():
    assert PP.is_end_name("train number end") and PP.is_end_name("day_end") and not PP.is_end_name("endpoint")
    s = PP.a_name_stats({"attributes": [{"name": "a_end"}, {"name": "b"}], "clusters": [{"attribute": "b"}, {"attribute": "c"}, {"attribute": "not_attribute"}]})
    assert s["unused"] == ["a end"] and s["undeclared"] == ["c"] and s["end_names"] == ["a end"]


@need_data
def test_frozen_prompts_give_every_cluster_once_per_order():
    files = frozen_prompts()
    assert len(files) == 18
    by = {}
    for f in files:
        set_name = "dev50b" if "d50b" in f.name else "dev50"
        ent, order = f.name.split("_")[0], int(f.stem[-1])
        text = f.read_text(encoding="utf-8")
        fp = S3.parse_frozen_prompt(text)
        n = int(re.search(rf"Entity {re.escape(fp['entity'])}: (\d+) clusters", text).group(1))
        ids = [c for c, _ in fp["blocks"]]
        assert len(ids) == n == len(set(ids))
        rows, _ = S3.names_jobs_for(set_name, ent, order, text)
        got = [c for r in rows for c in r["cluster_ids"]]
        assert got == ids and all(len(r["cluster_ids"]) <= 5 for r in rows)          # every cluster exactly once, frozen order kept
        by[(set_name, ent, order)] = [tuple(r["cluster_ids"]) for r in rows]
    for s in ("dev50", "dev50b"):
        for ent in PP.ENTS:
            sets = [set(by[(s, ent, o)]) for o in S3.ORDERS]
            assert sets[0] != sets[1] or len(by[(s, ent, 0)]) == 1                      # batch neighbours differ between orders


@need_data
def test_prompt_has_examples_other_entities_and_only_its_clusters():
    f = next(p for p in frozen_prompts() if p.name.startswith("train_a_v22d50b_s0"))
    rows, files = S3.names_jobs_for("dev50b", "train", 0, f.read_text(encoding="utf-8"))
    name, prompt, schema = files[0]
    assert S3.EXAMPLES_HEAD in prompt and S3.EX.STEP3_EXAMPLE_1 in prompt and S3.EX.STEP3_EXAMPLE_2 in prompt
    assert "Other entities" in prompt and "Placement options" not in prompt
    heads = re.findall(r"^### (\S+)", prompt, re.M)
    assert heads == rows[0]["cluster_ids"] == list(schema["properties"])


# ---------------------------------------------------------------- end to end with the fake model
@pytest.fixture(scope="module")
def u0(tmp_path_factory):
    mod = importlib.import_module("u0_step3_post_v43")
    out = tmp_path_factory.mktemp("u0")
    jobs = mod.build(out)
    info = mod.run(out, PP.FakeStep3())
    return mod, out, jobs, info


@pytest.fixture(scope="module")
def u2(tmp_path_factory):
    mod = importlib.import_module("u2_step3_v43")
    out = tmp_path_factory.mktemp("u2")
    names, jobs = mod.build(out)
    info = mod.run(out, PP.FakeStep3())
    res, sizes = mod.score_all(out)
    return mod, out, names, jobs, info, res, sizes


@need_data
def test_u0_build_reuses_option_b_answers(u0):
    _, out, jobs, _ = u0
    a = [j for j in jobs if j["family"] == "a"]
    assert len(a) == 18 and all(j["reused"] for j in a) and len([j for j in jobs if j["family"] == "split"]) == 54
    for j in a:
        assert (out / "responses" / f"{j['job']}.jsonl").read_bytes() == (PP.T1B / "responses" / f"{j['job']}.jsonl").read_bytes()
        assert (out / j["prompt"]).read_bytes() == (PP.T1B / j["prompt"]).read_bytes()


@need_data
def test_u0_fake_end_to_end(u0):
    _, out, _, info = u0
    assert info["split"] == {"jobs": 54, "run": 54, "parse_errors": 0}
    rc = [j for j in PP.read_manifest(out) if j["family"] == "reconcile"]
    assert info["reconcile"] == {"jobs": len(rc), "run": len(rc), "parse_errors": 0} and len(rc) > 0 and len(rc) % 2 == 0
    assert info["dupcheck"] == {"jobs": 12, "run": 12, "parse_errors": 0}                 # 3 entities x 2 sets x 2 reconcile orders
    calls = PP.call_stats(out)
    assert calls["total"]["calls"] == 54 + len(rc) + 12 and calls["reused"]["calls"] == 18 and calls["total"]["errors"] == 0
    assert set(NV.load_state(out)["done"]) == set(PP.POST_STAGES)


@need_data
def test_u2_build_job_counts(u2):
    _, out, names, jobs, *_ = u2
    assert len(names) == 138 and Counter(j["set"] for j in names) == {"dev50": 75, "dev50b": 63}
    assert len([j for j in jobs if j["family"] == "a"]) == 18 and all(j["assembled"] for j in jobs if j["family"] == "a")
    for j in names:
        assert j["format"] == "judge" and j["max_tokens"] == S3.NAMES_MAX_TOKENS
        assert list(json.loads((out / j["schema"]).read_text(encoding="utf-8"))["properties"]) == j["cluster_ids"]


@need_data
def test_u2_fake_end_to_end(u2):
    _, out, names, _, info, res, _ = u2
    assert info["names+split"] == {"jobs": 138 + 54, "run": 138 + 54, "parse_errors": 0}
    assert info["assemble"] == {"answers": 18, "errors": 0}
    rc = [j for j in PP.read_manifest(out) if j["family"] == "reconcile"]
    assert info["reconcile"]["parse_errors"] == 0 and info["reconcile"]["jobs"] == len(rc) > 0
    assert info["dupcheck"] == {"jobs": 12, "run": 12, "parse_errors": 0}
    stats = B.read_json(out / "scores" / "stats.json")
    assert set(stats) == {"dev50", "dev50b"} and set(stats["dev50"]["entities"]) == set(PP.ENTS)
    c = res["calls"]["total"]
    assert c["calls"] == 138 + 54 + len(rc) + 12 and c["errors"] == 0 and c["max_prompt_tokens"] > 0
    a = res["a_answers"]
    assert len(a) == 18 and a["errors"].sum() == 0 and a["unused_names"].sum() == 0 and a["undeclared_names"].sum() == 0   # by design
    assert set(res["rows"]["row"]) >= {"A s012 + split pass", "Final v3.9"} and (res["rows"]["found_total"] > 0).all()


@need_data
def test_a_llama43_written_and_loadable(u2):
    _, out, *_, res, sizes = u2
    files = S3.a_llama43_files(out, root=out)
    assert set(files) == {"dev50", "dev50b"} and all((out / f).exists() for f in files.values())
    assert S3.a_llama43_file("dev50b", out) == out / "a_llama43" / "dev50b" / "a.columns.json"
    ref = B.read_json(ROOT / "results" / "wf_v4" / "inputs" / "dev50" / "a.columns.json")
    stats = B.read_json(out / "scores" / "stats.json")
    for s in PP.SETS:
        chain = {"input": "a_llama43", "set": s, "seed": 0, "exclude": [], "columns_file": files[s]}
        cols = B.chain_columns(chain, root=out)                                  # as a Step 4 chain loads input a
        assert len(cols) == sizes[s] > 0 and list(cols[0]) == list(ref[0])
        assert {c["id"].split(":")[0] for c in cols} <= set(PP.ENTS) and len({c["id"] for c in cols}) == len(cols)
        assert sum(c["n_mentions"] for c in cols) == sum(e["mentions_in_columns"] for e in stats[s]["entities"].values())
    chains = NV.step4_chains(files, runs=(("a2", "dev50"),), seeds=(0,))        # the same dict plugs into the Nov 16 chain builder
    assert chains[0]["columns_file"] == files["dev50"]
    assert S3.a_llama43_files() == {s: f"results/wf_v43/u2/a_llama43/{s}/a.columns.json" for s in PP.SETS}


@need_data
def test_fig_train_attrs(u2):
    _, out, *_ = u2
    doc = B.read_json(out / "fig_train_attrs.json")
    assert doc["set"] == "dev50b" and doc["entity"] == "train" and doc["order"] == "s0"
    assert set(doc["sources"]) == {"qwen_frozen", "llama_option_b", "llama_v43"}
    v43 = doc["sources"]["llama_v43"]
    assert v43["unused"] == [] and v43["undeclared"] == [] and v43["n_clusters"] == 20
    assert doc["sources"]["llama_option_b"]["n_clusters"] == 20 and (out / "fig_train_attrs.csv").exists()
