"""wf_v5.1 R3 + R4 (s1a/rolenames_v51.py): fake-LLM tests, no GPU."""
import json
import random
from pathlib import Path

import pytest

from s1a import batch_v4 as B
from s1a import llm_cache as LC
from s1a import log_v43 as L43
from s1a import rolenames_v51 as RN
from s1a import step3_v43 as S3_43
from s1a import step3_v44 as S3
from s1a import step3_post_v43 as PP

ROOT = S3.ROOT


def block(cid, n, values, lines=("- {c}:0 [user] turn: I need it at [[x]]",)):
    head = f"### {cid}  (mentions {n}, distinct values {len(values)})\nExamples:\n"
    return head + "\n".join(x.format(c=cid) for x in lines) + "\n" + "".join(f"- {cid}:v [[{v}]] ..\n" for v in values)


def frozen_prompt(blocks):
    ids = ", ".join(c for c, _ in blocks)
    return "\n\n".join(["instruction", "Entity E1: 3 clusters", "Placement options:\nsome\nOther entities (id, top values):\n- E0: a, b", *[b for _, b in blocks],
                        f"Return ({ids})"])


@pytest.fixture
def blocks():
    return [("E1#0", block("E1#0", 12, ["09:15", "10:30"])), ("E1#1", block("E1#1", 9, ["cambridge", "london"])),
            ("E1#2", block("E1#2", 3, ["yes"])), ("E1#3", block("E1#3", 20, ["leeds"]))]


@pytest.fixture(autouse=True)
def run_key(monkeypatch):
    monkeypatch.setitem(PP.RUN_KEY, "tset", "tset")


@pytest.fixture
def prompt(blocks):
    return frozen_prompt(blocks)


# ---------------------------------------------------------------- R4
def test_switch_off_prompts_identical(prompt):
    cfg = S3.with_switches(S3.load_config(), {"similar_batches": False})
    old, old_files = S3_43.names_jobs_for("tset", "train", 0, prompt)
    new, files = S3.names_jobs_for_v44("tset", "train", 0, prompt, "v0", cfg)
    assert [f[1] for f in files] == [f[1] for f in old_files]
    # switch on but nothing to show (no snippets for these clusters) = identical as well
    _, files2 = S3.names_jobs_for_v44("tset", "train", 0, prompt, "v0", cfg, snippets={})
    assert [f[1] for f in files2] == [f[1] for f in old_files]


def test_switch_on_adds_only_context_lines(prompt):
    cfg = S3.with_switches(S3.load_config(), {"similar_batches": False})
    snips = {"E1#0": ['... leave after [09:15] ...'], "E1#1": ['... from [cambridge] to ...', '... to [london] on ...']}
    _, off = S3.names_jobs_for_v44("tset", "train", 0, prompt, "v0", cfg)
    rows, on = S3.names_jobs_for_v44("tset", "train", 0, prompt, "v0", cfg, snippets=snips)
    assert on[0][1] != off[0][1] and on[0][2] == off[0][2]
    stripped = "\n".join(x for x in on[0][1].split("\n") if not x.startswith("- \"...") and x != RN.CONTEXT_HEAD)
    assert stripped == off[0][1]
    assert '- "... leave after [09:15] ..."' in on[0][1]
    assert rows[0]["est_prompt_tokens"] > S3_43.PIN.est_tokens(off[0][1])


def test_load_config_accepts_new_switches_and_default_off():
    cfg = S3.load_config()
    assert not RN.switch_on(cfg, "naming_context") and not RN.switch_on(cfg, "name_clash")
    cfg = S3.load_config(switches={"naming_context": True, "name_clash": True})
    assert RN.switch_on(cfg, "naming_context") and RN.switch_on(cfg, "name_clash")
    with pytest.raises(ValueError):
        S3.load_config(switches={"nope": True})


CACHED = ROOT / "results" / "wf_v46" / "y3" / "dev50"


@pytest.mark.skipif(not (CACHED / "step3" / "prompts").exists(), reason="cached v5.0 Step 3 not in this checkout")
def test_switch_off_equals_cached_v50_prompts():
    from s1a import pipeline_v45 as PL
    step3, a_dir = CACHED / "step3", CACHED / "a_prompts"
    cfg, variant = S3.load_config(), B.read_json(step3 / "config_used.json")["names_variant_used"]
    vecs = S3.cluster_vectors("c_n50")
    j = [j for j in B.read_json(a_dir / "manifest.json")["jobs"] if j["family"] == "a" and j["ent"] == "train_info"][0]
    with PL.use_corpus("c_n50", B.read_json(CACHED / "entities.json"), a_dir):
        rows, files = S3.names_jobs_for_v44("c_n50", "train_info", int(j["run_tag"][1:]), (a_dir / j["prompt"]).read_text(encoding="utf-8"),
                                            variant, cfg, vecs)
    assert rows and all((step3 / "prompts" / f"{r['job']}.txt").read_bytes().replace(b"\r\n", b"\n") == f[1].encode("utf-8")
                        for r, f in zip(rows, files))


def test_snippet_length_cap_and_value_bracketed():
    rng = random.Random(1)
    words = [f"w{i}" for i in range(80)]
    for _ in range(200):
        text = " ".join(rng.choice(words + ["end.", "ok!"]) for _ in range(rng.randint(1, 60)))
        toks = text.split()
        i = rng.randrange(len(toks))
        j = min(len(toks), i + rng.randint(1, 12))
        start = len(" ".join(toks[:i])) + (1 if i else 0)
        end = start + len(" ".join(toks[i:j]))
        line = RN.snippet_from_turn(text, start, end)
        assert RN.n_words(line) <= 15
        assert line.count("[") == 1 and line.count("]") == 1


def test_snippet_example_and_sentence_cut():
    t = "Thanks a lot. I need a train that leaves cambridge after 09:15 on friday please. Bye."
    s = t.index("09:15")
    line = RN.snippet_from_turn(t, s, s + 5)
    assert line == "... a train that leaves cambridge after [09:15] on friday please. ..."
    assert RN.snippet_from_turn("09:15", 0, 5) == "[09:15]"


def test_pick_mentions_deterministic_and_spread():
    rows = [{"mention_id": i, "dialogue_id": f"D{i % 4}"} for i in range(40)]
    a = RN.pick_mentions(rows, "E1#0", 0, 3)
    assert a == RN.pick_mentions(list(reversed(rows)), "E1#0", 0, 3)
    assert len({r["dialogue_id"] for r in a[:3]}) == 3
    one = [{"mention_id": i, "dialogue_id": "D0"} for i in range(5)]
    assert len(RN.pick_mentions(one, "c", 0, 3)) >= 3


def test_cluster_snippets_distinct_and_capped():
    rows = [{"mention_id": i, "dialogue_id": f"D{i}"} for i in range(6)]
    lines = RN.cluster_snippets(rows, lambda r: ("go to the same place", 12, 20), "c", k=3)
    assert len(lines) == 1                                          # identical texts are skipped
    lines = RN.cluster_snippets(rows, lambda r: (f"leave at {r['mention_id']}", 9, len(f"leave at {r['mention_id']}")), "c", k=3)
    assert len(lines) == 3 and len(set(lines)) == 3


# ---------------------------------------------------------------- R3
def state_of(names, ids=None):
    ids = ids or list(names)
    return {("tset", "train", 0): {"frozen_ids": ids, "names": dict(names), "errors": [], "batches": 1, "ok": 1, "across": []}}


@pytest.fixture
def run_dir(tmp_path, blocks):
    B.write_json(tmp_path / "blocks.json", {"tset/train": {"entity": "E1", "others": [], "frozen_ids": [c for c, _ in blocks], "desc": "",
                                                           "blocks": dict(blocks)}})
    (tmp_path / "prompts").mkdir()
    (tmp_path / "responses").mkdir()
    return tmp_path


CFG = {"name_clash": {"min_mentions": 5, "max_per_name": 4}}
SNIPS = {"tset": {"E1#0": ["... leave after [09:15] ..."], "E1#1": ["... from [cambridge] to ..."], "E1#3": ["... to [leeds] on ..."]}}


class Scripted:
    """Backend stand-in: answers each job from `raw_of(job)`, writes one row (the VllmBackend row fields that matter here)."""

    def __init__(self, raw_of, finish="stop", guided=True):
        self.raw_of, self.finish, self.guided, self.jobs = raw_of, finish, guided, []

    def run(self, out, jobs):
        self.jobs = jobs
        for j in jobs:
            LC.put(Path(out) / "responses" / f"{j['job']}.jsonl", j["job"], {"job": j["job"], "raw": self.raw_of(j), "guided": self.guided,
                                                                              "finish_reason": self.finish})
        return {"jobs": len(jobs), "run": len(jobs), "parse_errors": 0}


def names_state():
    return state_of({"E1#0": "time", "E1#1": "place", "E1#2": "time", "E1#3": "place"})


def test_clash_detection(blocks):
    doc = dict(blocks)
    st = names_state()[("tset", "train", 0)]
    # E1#2 has 3 mentions (< 5): left out; place = E1#3 (20) anchor, E1#1 (9)
    assert RN.clash_pairs(st, doc, 5, 4) == [("place", "E1#3", "E1#1")]
    assert RN.clash_pairs(st, doc, 0, 4) == [("time", "E1#0", "E1#2"), ("place", "E1#3", "E1#1")]
    assert RN.clash_pairs(st, doc, 0, 1) == []                      # cap 1: no pair
    st["names"]["E1#1"] = "other"
    assert RN.clash_pairs(st, doc, 5, 4) == []


def test_clash_job_and_schema(run_dir):
    rows = RN.build_clash_q(run_dir, CFG, names_state(), "v1", SNIPS)
    assert len(rows) == 1 and rows[0]["cluster_ids"] == ["E1#1", "E1#3"] and rows[0]["format"] == "judge"
    text = (run_dir / rows[0]["prompt"]).read_text(encoding="utf-8")
    assert "Are A and B the same information, or two different roles? If different, give each a name." in text
    assert "... from [cambridge] to ..." in text and "... to [leeds] on ..." in text
    schema = json.loads((run_dir / rows[0]["schema"]).read_text(encoding="utf-8"))
    assert list(schema["properties"]) == ["answer", "E1#1", "E1#3"] and schema["additionalProperties"] is False
    assert schema["properties"]["answer"]["enum"] == ["same", "different"]
    assert "pattern" not in schema["properties"]["E1#1"]            # v4.4: the regex pattern breaks guided decoding (variant v1)


def test_orders_dedupe(run_dir):
    st = {**names_state(), ("tset", "train", 1): names_state()[("tset", "train", 0)]}
    rows = RN.build_clash_q(run_dir, CFG, st, "v1", SNIPS)
    assert len(rows) == 1 and rows[0]["orders"] == [0, 1]


def test_different_answer_renames(run_dir):
    be = Scripted(lambda j: json.dumps({"answer": "different", "E1#1": "departure_station", "E1#3": "destination_station"}))
    info, new = RN.run_clash(run_dir, be, CFG, names_state(), "v0", snips=SNIPS)
    n = new[("tset", "train", 0)]["names"]
    assert (n["E1#1"], n["E1#3"], n["E1#0"], n["E1#2"]) == ("departure_station", "destination_station", "time", "time")
    assert info["pairs"] == 1 and info["renamed_clusters"] == 2
    assert names_state()[("tset", "train", 0)]["names"]["E1#1"] == "place"      # input state not changed
    assert json.loads((run_dir / "clash_log.json").read_text(encoding="utf-8"))["counts"] == {"clash_different": 1}


def test_same_answer_joins_as_before(run_dir):
    be = Scripted(lambda j: json.dumps({"answer": "same", "E1#1": "place", "E1#3": "place"}))
    _, new = RN.run_clash(run_dir, be, CFG, names_state(), "v0", snips=SNIPS)
    assert new == names_state()
    assert json.loads((run_dir / "clash_log.json").read_text(encoding="utf-8"))["counts"] == {"clash_same": 1}


@pytest.mark.parametrize("raw", ["not json at all", "{\"answer\": \"maybe\"}", "{\"answer\": \"different\", \"E1#1\": \"a\"}",
                                 "{\"answer\": \"different\", \"E1#1\": \"a\", \"E1#3\": \"a\"}",
                                 "{\"answer\": \"different\", \"E1#1\": \"\", \"E1#3\": \"b\"}", "[1, 2]"])
def test_malformed_answer_is_safe_fallback_and_logged(run_dir, raw):
    _, new = RN.run_clash(run_dir, Scripted(lambda j: raw), CFG, names_state(), "v0", snips=SNIPS)
    assert new == names_state()
    counts = json.loads((run_dir / "clash_log.json").read_text(encoding="utf-8"))["counts"]
    assert counts == {"clash_malformed": 1}


def test_no_response_is_safe_fallback_and_logged(run_dir):
    class Silent:
        def run(self, out, jobs):
            return {"jobs": len(jobs), "run": 0, "parse_errors": 0}
    _, new = RN.run_clash(run_dir, Silent(), CFG, names_state(), "v0", snips=SNIPS)
    assert new == names_state()
    assert json.loads((run_dir / "clash_log.json").read_text(encoding="utf-8"))["counts"] == {"clash_no_response": 1}


def test_finish_reason_error_raises(run_dir):
    be = Scripted(lambda j: json.dumps({"answer": "same", "E1#1": "place", "E1#3": "place"}), finish="error")
    with pytest.raises(RN.ClashError, match="finish_reason error"):
        RN.run_clash(run_dir, be, CFG, names_state(), "v0", snips=SNIPS)


def test_guided_finish_reason_error_of_retried_row_raises(run_dir):
    class Retried(Scripted):
        def run(self, out, jobs):
            info = super().run(out, jobs)
            for j in jobs:
                LC.put(Path(out) / "responses" / f"{j['job']}.jsonl", "k2", {"job": j["job"], "raw": "{}", "guided": False, "finish_reason": "stop",
                                                                             "guided_finish_reason": "error"})
            return info
    with pytest.raises(RN.ClashError):
        RN.run_clash(run_dir, Retried(lambda j: "{}"), CFG, names_state(), "v0", snips=SNIPS)


def test_unguided_row_is_logged_not_raised(run_dir):
    be = Scripted(lambda j: json.dumps({"answer": "same", "E1#1": "place", "E1#3": "place"}), guided=False)
    RN.run_clash(run_dir, be, CFG, names_state(), "v0", snips=SNIPS)
    assert json.loads((run_dir / "clash_log.json").read_text(encoding="utf-8"))["counts"]["clash_unguided"] == 1


def test_blocker_overrides_same(run_dir):
    seen = []
    be = Scripted(lambda j: json.dumps({"answer": "same", "E1#1": "place", "E1#3": "place"}))

    def blocked(pair):
        seen.append(pair)
        return pair == ("E1#1", "E1#3")
    info, new = RN.run_clash(run_dir, be, CFG, names_state(), "v0", blocked=blocked, snips=SNIPS)
    assert seen == [("E1#1", "E1#3")]
    n = new[("tset", "train", 0)]["names"]
    assert n["E1#3"] == "place" and n["E1#1"] == "place_2"         # anchor E1#3 keeps the name, the other gets <name>_2
    assert json.loads((run_dir / "clash_log.json").read_text(encoding="utf-8"))["counts"]["clash_blocked_same"] == 1


def test_three_clusters_one_name_anchor_renamed_once(tmp_path):
    big = [("E1#0", block("E1#0", 30, ["a"])), ("E1#1", block("E1#1", 20, ["b"])), ("E1#2", block("E1#2", 10, ["c"]))]
    B.write_json(tmp_path / "blocks.json", {"tset/train": {"entity": "E1", "others": [], "frozen_ids": [c for c, _ in big], "desc": "", "blocks": dict(big)}})
    (tmp_path / "prompts").mkdir()
    st = state_of({"E1#0": "x", "E1#1": "x", "E1#2": "x"})
    answers = {"E1#1": {"answer": "different", "E1#0": "role_a", "E1#1": "role_b"}, "E1#2": {"answer": "same", "E1#0": "x", "E1#2": "x"}}

    def raw(j):
        return json.dumps(answers[j["cluster_ids"][1]] if j["cluster_ids"][1] in answers else answers["E1#2"])
    jobs_probe = RN.build_clash_q(tmp_path, CFG, st, "v0", {})
    assert [j["cluster_ids"] for j in jobs_probe] == [["E1#0", "E1#1"], ["E1#0", "E1#2"]]
    _, new = RN.run_clash(tmp_path, Scripted(lambda j: raw(j)), CFG, st, "v0", snips={})
    # E1#0 -> role_a, E1#1 -> role_b; E1#2 "same" as the anchor: follows the anchor's new name
    assert new[("tset", "train", 0)]["names"] == {"E1#0": "role_a", "E1#1": "role_b", "E1#2": "role_a"}


def test_wire_ids_for_hash_free_variant(run_dir):
    rows = RN.build_clash_q(run_dir, CFG, names_state(), "v2", SNIPS)
    schema = json.loads((run_dir / rows[0]["schema"]).read_text(encoding="utf-8"))
    assert list(schema["properties"]) == ["answer", "E1_1", "E1_3"]
    be = Scripted(lambda j: json.dumps({"answer": "different", "E1_1": "a_role", "E1_3": "b_role"}))
    _, new = RN.run_clash(run_dir, be, CFG, names_state(), "v2", snips=SNIPS)
    assert new[("tset", "train", 0)]["names"]["E1#1"] == "a_role"


def test_fake_backend_answers_clash_jobs(run_dir):
    be = RN.FakeStep51()
    info, new = RN.run_clash(run_dir, be, CFG, names_state(), "v0", snips=SNIPS)
    assert info["pairs"] == 1 and info["parse_errors"] == 0
    assert isinstance(L43.RepairLog.load(run_dir / "clash_log.json").counts, dict)


# ---------------------------------------------------------------- end to end on the frozen dev50 / dev50b inputs (fake model)
@pytest.mark.skipif(not (PP.T1B / "prompts").exists() or not (ROOT / "results" / "graph_v22_dev50" / "spans" / "mentions.csv").exists(),
                    reason="frozen Step 3 inputs not in this checkout")
def test_full_fake_run_with_both_switches(tmp_path):
    cfg = S3.load_config(switches={"naming_context": True, "name_clash": True})
    info, sizes = S3.full_run(tmp_path, RN.FakeStep51(), cfg, S3.FakeEncoder(), name_vecs=tmp_path / "name_vecs.npz", save_vecs=True, variant="v1")
    assert info["clash_q"]["pairs"] > 0 and info["clash_q"]["parse_errors"] == 0
    assert (tmp_path / "manifest_clash.json").exists() and (tmp_path / "clash_log.json").exists()
    names = S3.names_jobs(tmp_path)
    assert any(RN.CONTEXT_HEAD in (tmp_path / j["prompt"]).read_text(encoding="utf-8") for j in names)
    assert all(j["family"] != "clash_q" for j in B.read_json(tmp_path / "manifest.json")["jobs"])        # not part of the frozen manifest
    assert "clash_q" in S3.call_report(tmp_path) and sizes
