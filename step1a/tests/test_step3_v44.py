"""wf_v4.4 T1 / T2 / T4: s1a/step3_v44.py, s1a/split_v44.py and the scripts t1_names_probe_v44, t2_split_v44, t4_step3_v44.
Pure tests first, then end-to-end runs with the fake model on the real frozen inputs (about 3 minutes together)."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

from s1a import batch_v4 as B
from s1a import llm_cache as LC
from s1a import split_v44 as SP
from s1a import step3_post_v43 as PP
from s1a import step3_v43 as S3
from s1a import step3_v44 as S

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
need_data = pytest.mark.skipif(not (PP.T1B / "manifest.json").exists() or not (ROOT / "results" / "graph_v22_dev50" / "spans" / "vectors.npz").exists(),
                               reason="wf_v4.2 option B answers or bge-m3 vectors not in this checkout")
OFF = {"similar_batches": False, "rescue": False, "merge": False}


def block(cid, n, vals):
    lines = "\n".join(f"- {cid}:{i} [user] turn: I want the [[{v}]] please." for i, v in enumerate(vals))
    return f"### {cid}  (mentions {n}, distinct values {len(vals)})\nExamples:\n{lines}"


def frozen_prompt(n=7, ent="E0"):
    blocks = [block(f"{ent}#{i}", 10 - i, [f"v{i}a", f"v{i}b"]) for i in range(n)]
    head = (f"INTRO\n\nEntity {ent}: {n} clusters.\n\nPlacement options (copy one exactly into \"placement\"):\n- current entity {ent}: x\n"
            f"Other entities (id, top values of their 3 biggest clusters):\n- E1: a, b; c")
    return head + "\n\n" + "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------- config, T1 schemas
def test_config_and_switches():
    cfg = S.load_config()
    assert set(cfg["switches"]) == set(S.SWITCHES) and cfg["batch"] == 5 and cfg["orders"] == [0, 1, 2]
    assert 0 < cfg["merge"]["cosine"] < 1 and cfg["merge"]["max_pairs"] > 0
    off = S.with_switches(cfg, {"rescue": False})
    assert off["switches"]["rescue"] is False and cfg["switches"]["rescue"] is True          # copy
    with pytest.raises(ValueError):
        S.with_switches(cfg, {"nope": True})
    with pytest.raises(ValueError):
        S.load_config(switches={"nope": True})


def test_names_schema_variants():
    ids = ["E1#0", "E1#12"]
    assert S.names_schema_v44(ids, "v0") == S3.names_schema(ids)
    v1 = S.names_schema_v44(ids, "v1")
    assert list(v1["properties"]) == ids and v1["properties"]["E1#0"] == {"type": "string", "maxLength": 60}
    v2 = S.names_schema_v44(ids, "v2")
    assert list(v2["properties"]) == ["E1_0", "E1_12"] and v2["required"] == ["E1_0", "E1_12"] and "pattern" in v2["properties"]["E1_0"]
    v3 = S.names_schema_v44(ids, "v3")
    assert list(v3["properties"]) == ["E1_0", "E1_12"] and "pattern" not in v3["properties"]["E1_0"] and v3["properties"]["E1_0"]["maxLength"] == 60
    assert S.names_schema_v44(ids, "v4")["properties"]["E1_0"] == {"type": "string"}
    for v in S.VARIANTS:
        s = S.names_schema_v44(ids, v)
        assert s["additionalProperties"] is False and s["type"] == "object" and len(s["required"]) == 2
    with pytest.raises(ValueError):
        S.names_schema_v44(ids, "v9")


def test_key_mapping_back():
    ids = ["E1#0", "E1#1", "E1#2"]
    raw = json.dumps({"E1_0": "Departure-Time", "E1_1": "not_attribute", "E1_2": "price"})
    m, errs = S.validate_names_v44(raw, ids, "v3")
    assert errs == [] and m == {"E1#0": "departure_time", "E1#1": "not_attribute", "E1#2": "price"}
    assert json.loads(S.unkey_names(raw, ids, "v2")) == {"E1#0": "Departure-Time", "E1#1": "not_attribute", "E1#2": "price"}
    # variants that keep "#": unchanged; wrong key style under a #-free variant is reported, not guessed
    assert S.validate_names_v44(json.dumps({"E1#0": "a", "E1#1": "b", "E1#2": "c"}), ids, "v1")[1] == []
    assert S.validate_names_v44(json.dumps({"E1#0": "a", "E1#1": "b", "E1#2": "c"}), ids, "v3")[1] == []   # an original id is still accepted
    m, errs = S.validate_names_v44(json.dumps({"E1_0": "a", "E1_1": "b"}), ids, "v2")
    assert any("missing cluster E1#2" in e for e in errs) and m == {"E1#0": "a", "E1#1": "b"}
    assert S.validate_names_v44("```json\n" + raw + "\n```", ids, "v2")[1] == []                      # fenced unguided retry
    assert S.validate_names_v44("not json", ids, "v2")[1]


def test_prompt_ids_follow_the_variant():
    text = frozen_prompt()
    fp = S3.parse_frozen_prompt(text)
    bl = fp["blocks"][:3]
    v0 = S.render_names_v44("E0", 1, 2, 7, fp["others"], bl, "v0")
    assert v0 == S3.render_names("E0", 1, 2, 7, fp["others"], bl)                                  # v0 = the v4.3 prompt, byte for byte
    assert S.render_names_v44("E0", 1, 2, 7, fp["others"], bl, "v1") == v0
    v3 = S.render_names_v44("E0", 1, 2, 7, fp["others"], bl, "v3")
    assert "E0#" not in v3 and "R1#" not in v3 and "C1#" not in v3                                  # also the worked examples
    assert "### E0_0" in v3 and "- E0_0:0 [user]" in v3 and '{"R1_0": "pickup_branch"' in v3 and "E0_0, E0_1, E0_2" in v3
    assert "E0_10" not in v3 and "[[v0a]]" in v3                                                    # values are untouched
    assert re.sub(r"E0_(\d)", r"E0#\1", re.sub(r"([RC]1)_(\d)", r"\1#\2", v3)) == v0


# ---------------------------------------------------------------- T1 probe choice
def probe_dir(tmp_path, rows_by_variant):
    """A probe folder with 3 jobs per variant and hand-made answers: {variant: [row dict or None] * 3}."""
    jobs, out = [], tmp_path / "t1"
    (out / "responses").mkdir(parents=True)
    for v, rows in rows_by_variant.items():
        for k, r in enumerate(rows):
            ids = [f"E{k}#0", f"E{k}#1"]
            jobs.append({"job": f"p_{v}_{k}", "names_variant": v, "cluster_ids": ids})
            if r is not None:
                raw = r.pop("raw", json.dumps({S.wire_id(c, v): "name_a" for c in ids}))
                row = {"key": "k", "job": f"p_{v}_{k}", "guided": True, "finish_reason": "stop", "raw": raw, "errors": [], **r}
                (out / "responses" / f"p_{v}_{k}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    B.write_json(out / "manifest_probe.json", {"jobs": jobs})
    return out


def test_probe_choice_rule(tmp_path):
    bad_retry = {"retried": True, "guided_raw": "", "guided_errors": ["no JSON object found"], "guided_finish_reason": "error", "guided": False}
    out = probe_dir(tmp_path, {"v1": [{}, {}, dict(bad_retry)], "v2": [{}, {}, {}], "v3": [{}, {}, {}], "v4": [{}, {}, {}], "v0": [dict(bad_retry)] * 3})
    c = S.evaluate_probe(out)
    assert c["chosen"] == "v2" and c["passed"] is True                                              # v1 failed 1 of 3, v2 is the first 3/3
    assert c["variants"]["v1"]["ok"] == 2 and c["variants"]["v1"]["retried"] == 1 and c["variants"]["v2"]["ok"] == 3
    raws = [json.loads(x) for x in (out / "guided_raw.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(raws) == 15 and [r["finish"] for r in raws if r["job"] == "p_v1_2"] == ["error"]    # the failed guided answer is kept
    assert B.read_json(out / "choice.json")["chosen"] == "v2"
    # a guided answer with a bad name (valid JSON, so the backend would not retry) is not ok either
    out = probe_dir(tmp_path / "b", {"v1": [{"raw": json.dumps({"E0#0": "ok", "E0#1": "Not Valid!!"[:0]})}, {}, {}], "v0": [{}, {}, {}]})
    assert S.evaluate_probe(out)["chosen"] == "v0"
    # nothing passes: the best one is named, passed is false
    out = probe_dir(tmp_path / "c", {"v1": [{}, None, {}], "v2": [{}, {}, None], "v3": [None] * 3, "v0": [{}, {}, {"errors": ["x"]}]})
    c = S.evaluate_probe(out)
    assert c["passed"] is False and c["chosen"] == "v1"                                             # 2 ok each for v1, v2, v0: earliest wins


def test_names_variant_reads_choice(tmp_path):
    cfg = S.load_config()
    p = tmp_path / "choice.json"
    with pytest.raises(FileNotFoundError):
        S.names_variant(cfg, p)
    B.write_json(p, {"chosen": "v3"})
    assert S.names_variant(cfg, p) == "v3" and S.names_variant({**cfg, "names_variant": "v1"}) == "v1"
    with pytest.raises(ValueError):
        S.names_variant({**cfg, "names_variant": "v7"})


# ---------------------------------------------------------------- T2 keyed split
def split_ids(n=6, cid="E0#0"):
    return [f"{cid}:s{i}" for i in range(n)]


def test_keyed_split_schema_exactly_once():
    ids = split_ids()
    s = SP.keyed_schema(ids)
    ex = s["properties"]["examples"]
    assert list(ex["properties"]) == ids and ex["required"] == ids and ex["additionalProperties"] is False        # one required key per id
    assert all(v == {"type": "string", "enum": list(SP.PART_IDS)} for v in ex["properties"].values())
    assert s["required"] == ["is_mixed", "parts", "examples"] and s["properties"]["parts"]["maxItems"] == SP.PARTS_MAX
    assert list(s["properties"]) == ["is_mixed", "parts", "examples"]                                                # parts before the references
    json.dumps(s)


def test_unkey_split_maps_to_frozen_format():
    ids = split_ids()
    raw = json.dumps({"is_mixed": True, "parts": [{"name": "a_part", "role": "first"}, {"name": "b_part", "role": "second"}],
                      "examples": {e: ("P1" if i < 4 else "P2") for i, e in enumerate(ids)}})
    obj, errs = SP.unkey_split(raw, "E0#0", ids)
    assert errs == [] and obj == {"cluster_id": "E0#0", "is_mixed": True, "parts": [
        {"name": "a_part", "role": "first", "examples": ids[:4]}, {"name": "b_part", "role": "second", "examples": ids[4:]}]}
    assert LC.parse_split(json.dumps(obj), ids)[1] == []                                          # what the frozen parser accepts
    # not mixed: references are ignored
    obj, errs = SP.unkey_split(json.dumps({"is_mixed": False, "parts": [], "examples": {e: "P1" for e in ids}}), "E0#0", ids)
    assert errs == [] and obj == {"cluster_id": "E0#0", "is_mixed": False, "parts": []}
    # a part with no example is dropped; fewer than two parts left -> not mixed
    one = json.dumps({"is_mixed": True, "parts": [{"name": "x", "role": "r"}, {"name": "y", "role": "r"}], "examples": {e: "P1" for e in ids}})
    assert SP.unkey_split(one, "E0#0", ids) == ({"cluster_id": "E0#0", "is_mixed": False, "parts": []}, [])
    # every kind of structural error is reported
    bad = json.dumps({"is_mixed": True, "parts": [{"name": "x", "role": "r"}, {"name": "y", "role": "r"}],
                      "examples": {ids[0]: "P1", ids[1]: "P3", ids[2]: "Q", "E0#0:zz": "P1"}})
    errs = SP.unkey_split(bad, "E0#0", ids)[1]
    assert any("missing example" in e for e in errs) and any("unknown example" in e for e in errs) and sum("not a listed part" in e for e in errs) == 2
    assert SP.unkey_split("no json", "E0#0", ids)[1] and SP.unkey_split(json.dumps({"is_mixed": True, "parts": []}), "E0#0", ids)[1]
    # an answer already in the frozen list format (an unguided retry) goes to the frozen parser unchanged
    frozen = {"cluster_id": "E0#0", "is_mixed": True, "parts": [{"name": "a", "role": "r", "examples": ids[:3]}, {"name": "b", "role": "r", "examples": ids[3:]}]}
    assert SP.unkey_split(json.dumps(frozen), "E0#0", ids) == (frozen, [])
    assert SP.unkey_split(json.dumps({**frozen, "parts": [{"name": "a", "role": "r", "examples": ids[:3] + ids[:1]}]}), "E0#0", ids)[1]   # repeated id is still caught


def frozen_split_prompt(ids):
    return ("Below are examples of ONE cluster of values taken from a dialogue corpus. Decide whether the cluster mixes\n"
            "two or more attributes (roles): values that look alike but play different roles in the dialogue.\n"
            "Examples are marked with [[...]] inside the turn they come from.\n"
            "If it does mix, give the parts: for each part a snake_case name, a short role, and the ids of the examples\n"
            "that belong to it. Every example must be in exactly one part. If it does not mix, give is_mixed false and\n"
            "no parts.\nReturn ONLY one JSON object, nothing before or after it:\n"
            '{"cluster_id": "C#0", "is_mixed": true,\n "parts": [{"name": "str", "role": "str", "examples": ["C#0:s0"]}]}\n\n'
            "Cluster E0#0 of entity E0 (mentions 6, distinct values 3).\nExamples:\n"
            + "\n".join(f"- {e} [user] turn: [[x]]" for e in ids) + "\n\nReturn the JSON object now.\n")


def test_keyed_split_prompt_keeps_the_frozen_text():
    ids = split_ids()
    frozen = frozen_split_prompt(ids)
    new = SP.keyed_prompt(frozen, ids)
    head, tail = frozen.split("If it does mix")[0], "Cluster E0#0 of entity E0"
    assert new.startswith(head) and new.endswith(frozen[frozen.index(tail):])                    # intro, cluster and examples copied
    assert '"examples": {"E0#0:s0": "P1", "E0#0:s1": "P2"}' in new and "P1 for every example" in new
    assert '"examples": ["C#0:s0"]' not in new
    with pytest.raises(ValueError):
        SP.keyed_prompt("some other prompt", ids)


@need_data
def test_split_jobs_on_the_real_frozen_prompts(tmp_path):
    frozen = []
    for s in PP.SETS:
        frozen += PP.copy_split_jobs(tmp_path, s)[0]
    rows = SP.split_jobs(tmp_path, frozen)
    assert len(rows) == 54 and all(r["family"] == "splitk" and "_splitk_" in r["job"] and r["frozen_job"] == r["job"].replace("_splitk_", "_split_")
                                   for r in rows)
    for r in rows[::9]:
        sch = json.loads((tmp_path / r["schema"]).read_text(encoding="utf-8"))
        assert list(sch["properties"]["examples"]["properties"]) == r["example_ids"] and r["example_ids"]
        f = (tmp_path / r["prompt"].replace("_splitk_", "_split_")).read_text(encoding="utf-8")
        k = (tmp_path / r["prompt"]).read_text(encoding="utf-8")
        assert f[f.index("Cluster "):] == k[k.index("Cluster "):] and f.split("If it does mix")[0] == k.split("If it does mix")[0]
    assert all(r["job"].endswith("_r1") for r in rows) and B.read_json(tmp_path / "manifest_split44.json")["jobs"] == rows


# ---------------------------------------------------------------- booster 1: similar batches
def unit(*xs):
    v = np.array(xs, dtype=float)
    return v / np.linalg.norm(v)


def test_similar_order_chain():
    vecs = {"a": unit(1, 0), "b": unit(0, 1), "c": unit(1, 0.1), "d": unit(0.1, 1), "e": unit(-1, 0)}
    items = [("a", 0), ("b", 1), ("c", 2), ("d", 3), ("e", 4), ("x", 5)]                           # x has no vector
    out = S.similar_order(items, vecs)
    assert [k for k, _ in out] == ["a", "c", "d", "b", "e", "x"]                                   # a -> nearest c -> nearest d -> b -> e; x last
    assert sorted(out) == sorted(items) and out[0] == items[0]
    assert S.similar_order([("a", 0)], vecs) == [("a", 0)] and S.similar_order([], vecs) == []
    assert S.similar_order(items, vecs) == out                                                      # deterministic
    tie = {"a": unit(1, 0), "b": unit(0, 1), "c": unit(0, 1)}
    assert [k for k, _ in S.similar_order([("a", 0), ("b", 1), ("c", 2)], tie)][:2] == ["a", "b"]  # ties: earlier position


def test_names_jobs_switches_off_equal_v43():
    text = frozen_prompt(12)
    cfg = S.with_switches(S.load_config(), OFF)
    rows, files = S.names_jobs_for_v44("dev50", "hotel", 1, text, "v0", cfg)
    rows43, files43 = S3.names_jobs_for("dev50", "hotel", 1, text)
    assert files == files43                                                                         # same names, prompts and schemas
    keep = ("job", "entity", "ent", "set", "run", "family", "format", "format43", "run_tag", "order", "batch", "cluster_ids", "prompt", "schema",
            "max_tokens", "est_prompt_tokens")
    assert [{k: r[k] for k in keep} for r in rows] == [{k: r[k] for k in keep} for r in rows43]
    assert all(r["names_variant"] == "v0" and r["frozen_ids"] == [f"E0#{i}" for i in range(12)] for r in rows)


def test_similar_batches_switch_fills_batches_with_neighbours():
    n = 12
    text = frozen_prompt(n)
    # clusters 0..11: even ids point one way, odd ids the other; the frozen order alternates
    vecs = {f"E0#{i}": unit(1, 0.01 * i) if i % 2 == 0 else unit(0.01 * i, 1) for i in range(n)}
    on = S.with_switches(S.load_config(), {"similar_batches": True})
    rows, files = S.names_jobs_for_v44("dev50", "hotel", 0, text, "v0", on, vecs)
    got = [c for r in rows for c in r["cluster_ids"]]
    assert sorted(got) == sorted(f"E0#{i}" for i in range(n)) and len(set(got)) == n and all(len(r["cluster_ids"]) <= 5 for r in rows)
    assert got[0] == "E0#0" and [int(c.split("#")[1]) % 2 for c in got[:5]] == [0] * 5                # first batch: the even (similar) clusters
    off = S.with_switches(on, {"similar_batches": False})
    base, _ = S.names_jobs_for_v44("dev50", "hotel", 0, text, "v0", off, vecs)
    assert [c for r in base for c in r["cluster_ids"]] == [f"E0#{i}" for i in range(n)] and got != [c for r in base for c in r["cluster_ids"]]
    assert rows[0]["frozen_ids"] == base[0]["frozen_ids"]                                           # the A answer keeps the frozen cluster order
    for (name, prompt, schema), r in zip(files, rows):                                              # prompts show the clusters of their own batch only
        assert re.findall(r"^### (\S+)", prompt, re.M) == r["cluster_ids"] == list(schema["properties"])


# ---------------------------------------------------------------- blocks, rescue, merge (pure parts)
def test_block_helpers():
    b = block("E0#3", 7, ["alpha", "beta", "alpha"])
    assert S.block_mentions(b) == 7 and S.block_values(b) == ["alpha", "beta"]
    assert S.block_examples(b, 2) == ["[user] turn: I want the [[alpha]] please.", "[user] turn: I want the [[beta]] please."]
    d = S.entity_description([("E0#0", block("E0#0", 1, ["tiny"])), ("E0#1", block("E0#1", 9, ["x", "y"])), ("E0#2", block("E0#2", 5, ["z"]))])
    assert d == "x, y; z; tiny"                                                                     # biggest clusters first


def test_rescue_prompts_and_answers():
    b = block("E0#3", 7, ["alpha", "beta"])
    q = S.render_rescue_q("E0", "x, y; z", b)
    assert "Is this information about the entity E0?" in q and "[[alpha]], [[beta]]" in q and q.count("\n- ") == 2 and "x, y; z" in q
    assert not re.search(r"multiwoz|hotel|train|restaurant", q, re.I)
    assert S.parse_yes_no('{"answer": "Yes"}') == "yes" and S.parse_yes_no('{"answer": "no"}') == "no"
    assert S.parse_yes_no('{"answer": "maybe"}') is None and S.parse_yes_no("yes") is None and S.parse_yes_no("[1]") is None
    n = S.render_rescue_n("E0", ["Other entities (id, top values of their 3 biggest clusters):", "- E1: a"], b, ["price", "stay"], "v3")
    assert "Names already used for this entity" in n and "price, stay" in n and "### E0_3" in n and "E0#" not in n
    assert S.render_rescue_n("E0", ["Other entities:"], b, [], "v0").count("none yet") == 1
    assert S.YESNO_SCHEMA["properties"]["answer"]["enum"] == ["yes", "no"]


def test_merge_pairs_and_groups(tmp_path):
    enc = S.FakeEncoder()
    nv = S.NameVectors(None, enc)
    names = ["departure_time", "departure_times", "arrival_place", "stay_duration", "stay_length"]
    nv.encode_missing(names)
    pairs = S.candidate_pairs(names, nv, 0.75, 20)
    assert [(a, b) for _, a, b in pairs][0] in {("departure_time", "departure_times"), ("stay_duration", "stay_length")}
    assert all(c >= 0.75 for c, _, _ in pairs) and pairs == sorted(pairs, key=lambda p: (-p[0], p[1], p[2]))
    assert len(S.candidate_pairs(names, nv, 0.75, 1)) == 1 and S.candidate_pairs(names, nv, 1.01, 20) == []
    assert ("arrival_place", "stay_length") not in [(a, b) for _, a, b in pairs]
    # union-find merge: the kept name has most clusters, then is first alphabetically; chains merge into one group
    mp = S.merge_groups(["a", "b", "c", "d"], [("a", "b"), ("b", "c")], {"a": 1, "b": 3, "c": 1, "d": 2})
    assert mp == {"a": "b", "c": "b"} and S.merge_groups(["a", "b"], [], {}) == {} and S.merge_groups(["b", "a"], [("a", "b")], {}) == {"b": "a"}
    # name vectors: save / load round trip, no encoder needed for known names, an unknown name without an encoder fails
    p = tmp_path / "vecs.npz"
    nv.save(p)
    nv2 = S.NameVectors(p)
    nv2.encode_missing(["stay_length", "departure_time"])
    assert nv2.n_new == 0 and abs(nv2.cosine("stay_length", "stay_duration") - nv.cosine("stay_length", "stay_duration")) < 1e-6
    with pytest.raises(ValueError):
        nv2.encode_missing(["something_new"])
    enc_calls = []
    nv3 = S.NameVectors(p, lambda t: enc_calls.append(list(t)) or enc(t))
    nv3.encode_missing(["something_new", "stay_length"])
    assert enc_calls == [["something new"]] and nv3.n_new == 1 and not np.load(p)["names"].tolist().count("something new")   # new names stay in memory


def test_merge_prompt():
    blocks = {"E0#0": block("E0#0", 3, ["a1", "a2"]), "E0#1": block("E0#1", 9, ["b1"]), "E0#2": block("E0#2", 4, ["b2"])}
    q = S.render_merge_q("E0", "name_a", "name_b", ["E0#0"], ["E0#1", "E0#2"], blocks)
    assert "Column A: name_a" in q and "Column B: name_b" in q and "[[b1]], [[b2]]" in q and "Same information?" in q and "different roles" in q
    assert q.count("example:") == 2 and "[[b1]] please" in q                                         # the example comes from the biggest cluster


# ---------------------------------------------------------------- end to end (fake model, real frozen inputs)
@pytest.fixture(scope="module")
def full(tmp_path_factory):
    out = tmp_path_factory.mktemp("t4")
    cfg = S.load_config()
    info, sizes = S.full_run(out, S.FakeStep44(), cfg, S.FakeEncoder(), name_vecs=out / "name_vecs.npz", save_vecs=True, variant="v3")
    return out, cfg, info, sizes


@need_data
def test_all_off_is_the_v43_job_set(tmp_path):
    cfg = S.with_switches(S.load_config(), OFF)
    names, jobs = S.build(tmp_path / "v44", cfg, "v0")
    names43, jobs43 = S3.build(tmp_path / "v43")
    assert [(j["job"], j["cluster_ids"], j["batch"]) for j in names] == [(j["job"], j["cluster_ids"], j["batch"]) for j in names43] and len(names) == 138
    for j in names:
        assert (tmp_path / "v44" / j["prompt"]).read_bytes() == (tmp_path / "v43" / j["prompt"]).read_bytes()
        assert B.read_json(tmp_path / "v44" / j["schema"]) == B.read_json(tmp_path / "v43" / j["schema"])
    assert [j["job"] for j in jobs if j["family"] == "a"] == [j["job"] for j in jobs43 if j["family"] == "a"]
    assert [j["job"] for j in jobs if j["family"] == "split"] == [j["job"] for j in jobs43 if j["family"] == "split"]
    assert all(j.get("assembled") for j in jobs if j["family"] == "split")                           # their answers come from the keyed jobs
    assert len(B.read_json(tmp_path / "v44" / "manifest_split44.json")["jobs"]) == 54


@need_data
def test_similar_batches_on_real_clusters(tmp_path):
    cfg = S.with_switches(S.load_config(), {"rescue": False, "merge": False})
    names, _ = S.build(tmp_path, cfg, "v1")                                                         # reads the bge-m3 cluster centroids, read only
    base = S3.names_jobs_for("dev50", "train", 0, (PP.T1B / "prompts" / "train_a_v22d50_s0.txt").read_text(encoding="utf-8"))[0]
    mine = [j for j in names if (j["set"], j["ent"], j["order"]) == ("dev50", "train", 0)]
    assert sorted(c for j in mine for c in j["cluster_ids"]) == sorted(c for j in base for c in j["cluster_ids"])
    assert [j["cluster_ids"] for j in mine] != [j["cluster_ids"] for j in base]
    vecs = S.cluster_vectors("dev50")
    assert all(abs(np.linalg.norm(v) - 1) < 1e-5 for v in vecs.values())

    def mean_sim(js):
        return np.mean([float(vecs[a] @ vecs[b]) for j in js for a, b in zip(j["cluster_ids"], j["cluster_ids"][1:])])
    assert mean_sim(mine) > mean_sim(base)                                                          # neighbours are closer than in the frozen order


@need_data
def test_full_fake_run(full):
    out, cfg, info, sizes = full
    assert info["names+split"] == {"jobs": 138 + 54, "run": 138 + 54, "parse_errors": 0}
    assert info["split_assemble"]["parse_errors"] == 0 and info["split_assemble"]["answered"] == 54
    assert info["assemble"] == {"answers": 18, "errors": 0}
    r, m = info["boosters"]["rescue"], info["boosters"]["merge"]
    assert r["asked"] == info["rescue_q"]["jobs"] > 0 and r["yes"] + r["no"] == r["asked"] and r["unparsed"] == 0
    assert r["names_asked"] == info["rescue_n"]["jobs"] == r["named"] > 0
    assert m["pairs_asked"] == info["merge_q"]["jobs"] > 0 and m["yes"] + m["no"] == m["pairs_asked"] and 0 < m["merged"] <= m["yes"] * 3
    assert info["dupcheck"]["parse_errors"] == 0 and info["reconcile"]["parse_errors"] == 0
    calls = B.read_json(out / "scores" / "calls_v44.json")
    assert {"names", "split", "rescue_q", "rescue_n", "merge_q", "reconcile", "dupcheck", "total"} <= set(calls)
    assert calls["names"]["calls"] == 138 and calls["split"]["calls"] == 54 and calls["total"]["prompt_tokens"] > 0
    assert calls["total"]["calls"] == sum(d["calls"] for k, d in calls.items() if k != "total")
    assert (out / "scores" / "summary.md").exists() and "Boosters" in (out / "scores" / "summary.md").read_text(encoding="utf-8")


@need_data
def test_full_fake_run_applies_rescue_and_merge(full):
    out, cfg, info, sizes = full
    base = S.read_base(out)
    assert all(not st["errors"] for st in base.values())
    after, named = S.apply_rescue(out, base)
    assert sum(len(v) for v in named.values()) == info["boosters"]["rescue"]["named"]
    for key, cids in named.items():                                                                 # rescued clusters were not_attribute, are named now
        assert all(base[key]["names"][c] == "not_attribute" and after[key]["names"][c].startswith("fake_rescued_") for c in cids)
    merged, moved = S.apply_merge(out, after)
    assert sum(len(v) for v in moved.values()) == info["boosters"]["merge"]["merged"]
    for key, mp in moved.items():
        assert not set(mp) & {n for n in merged[key]["names"].values()}                              # a removed name is gone from the answers
    # the assembled A answers are the post-merge names
    for a in [j for j in PP.read_manifest(out) if j["family"] == "a"]:
        row = B.last_row(out / "responses" / f"{a['job']}.jsonl")
        key = (a["set"], a["ent"], int(a["run_tag"][1:]))
        assert {c["cluster_id"]: c["attribute"] for c in row["parsed"]["clusters"]} == merged[key]["names"] and row["assembled"]


@need_data
def test_a_llama44_files(full):
    out, cfg, info, sizes = full
    files = S.a_llama44_files(out, root=out)
    assert set(files) == {"dev50", "dev50b"} and all((out / f).exists() for f in files.values())
    assert S.a_llama44_file("dev50b", out) == out / "a_llama44" / "dev50b" / "a.columns.json"
    assert S.a_llama44_files() == {s: f"results/wf_v44/t4/a_llama44/{s}/a.columns.json" for s in PP.SETS}
    ref = B.read_json(ROOT / "results" / "wf_v4" / "inputs" / "dev50" / "a.columns.json")
    stats = B.read_json(out / "scores" / "stats.json")
    for s in PP.SETS:
        chain = {"input": "a_llama44", "set": s, "seed": 0, "exclude": [], "columns_file": files[s]}
        cols = B.chain_columns(chain, root=out)                                                      # as a Step 4 chain loads input a
        assert len(cols) == sizes[s] > 0 and list(cols[0]) == list(ref[0])
        assert sum(c["n_mentions"] for c in cols) == sum(e["mentions_in_columns"] for e in stats[s]["entities"].values())
    # Step 4 reads mention_ids and n_values of every column from <out>/scores/final_columns.json (as for a_llama43)
    final = B.read_json(out / "scores" / "final_columns.json")
    for s in PP.SETS:
        cols = B.read_json(out / files[s])
        by_id = {f"{ent}:{c['cid']}": c for ent, cs in final[s].items() for c in cs}
        assert set(by_id) == {c["id"] for c in cols}
        for c in cols:
            f = by_id[c["id"]]
            assert f["mention_ids"] and len(f["mention_ids"]) == c["n_mentions"] and isinstance(f["n_values"], int) and f["n_values"] > 0


@need_data
def test_name_vectors_single_writer(full):
    out, *_ = full
    z = np.load(out / "name_vecs.npz")
    assert len(z["names"]) > 0 and z["vecs"].shape[0] == len(z["names"])
    assert not (S.OUT_ABLATE).exists() or not any(S.OUT_ABLATE.glob("*/name_vecs.npz"))              # ablations never write name vectors


@need_data
def test_ablation_is_one_call(tmp_path):
    cfg = S.load_config()
    out_t4 = tmp_path / "t4"
    out_t4.mkdir()
    nv = S.NameVectors(None, S.FakeEncoder())
    nv.encode_missing(["fake_attr_0", "fake_attr_1"])
    nv.save(out_t4 / "name_vecs.npz")
    before = (out_t4 / "name_vecs.npz").read_bytes()
    info, sizes = S.ablation("rescue", S.FakeStep44(), cfg, S.FakeEncoder(), root=tmp_path / "abl", name_vecs=out_t4 / "name_vecs.npz", variant="v1")
    out = tmp_path / "abl" / "rescue"
    assert info["names+split"]["jobs"] == 46 + 54                                                    # order 0 only: 25 + 21 names jobs
    assert "rescue_q" not in info and info["boosters"]["rescue"]["asked"] == 0 and info["boosters"]["merge"]["pairs_asked"] > 0
    assert (out / "a_llama44" / "dev50" / "a.columns.json").exists() and (out / "scores" / "rows.csv").exists() and sizes["dev50"] > 0
    assert (out_t4 / "name_vecs.npz").read_bytes() == before and not (out / "name_vecs.npz").exists()   # read only
    rows = [B.last_row(out / "responses" / f"{ent}_a_v22d50_s{o}.jsonl") for ent in PP.ENTS for o in (0, 1, 2)]
    for ent in PP.ENTS:                                                                              # orders 1 and 2 are copies of order 0
        s = [B.last_row(out / "responses" / f"{ent}_a_v22d50_s{o}.jsonl") for o in (0, 1, 2)]
        assert s[1]["copy_of"] == s[2]["copy_of"] == "s0" and s[1]["parsed"] == s[0]["parsed"] == s[2]["parsed"] and "copy_of" not in s[0]
    assert len(rows) == 9
    with pytest.raises(ValueError):
        S.ablation("nope", S.FakeStep44(), cfg, S.FakeEncoder(), root=tmp_path / "x")


@need_data
def test_scripts_entry_points(tmp_path):
    import importlib
    t1, t2, t4 = (importlib.import_module(m) for m in ("t1_names_probe_v44", "t2_split_v44", "t4_step3_v44"))
    choice, info = t1.run_probe(tmp_path / "t1", S.FakeStep44())
    assert choice["chosen"] == "v1" and choice["passed"] and info == {"jobs": 15, "run": 15, "parse_errors": 0}
    assert len({(j["ent"], tuple(j["cluster_ids"])) for j in B.read_json(tmp_path / "t1" / "manifest_probe.json")["jobs"] if j["names_variant"] == "v1"}) == 3
    first = [tuple(j["cluster_ids"]) for j in B.read_json(tmp_path / "t1" / "manifest_probe.json")["jobs"] if j["names_variant"] == "v1"]
    for v in ("v2", "v3", "v0"):                                                                     # the same 3 cluster batches for every variant
        assert [tuple(j["cluster_ids"]) for j in B.read_json(tmp_path / "t1" / "manifest_probe.json")["jobs"] if j["names_variant"] == v] == first
    t2.build(tmp_path / "t2")
    res = t2.run(tmp_path / "t2", S.FakeStep44())
    assert res["split"]["jobs"] == 54 and res["split"]["parse_errors"] == 0
    rep = t2.report(tmp_path / "t2")
    assert rep["parse_errors"] == 0 and rep["calls"]["calls"] == 54 and (tmp_path / "t2" / "split_report.md").exists()
    assert t4.OUT == S.OUT_T4 and t4.a_llama44_files()["dev50"].endswith("a_llama44/dev50/a.columns.json")
