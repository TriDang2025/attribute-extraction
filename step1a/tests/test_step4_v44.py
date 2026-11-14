"""wf_v4.4 T5 / T6 / T7: Step 4 v4.4 (s1a/step4_v44.py, step4_fake_v44.py, scripts/t6_step4_v44.py, scripts/t7_ablation_v44.py) with the fake model."""
import json
import shutil
import sys
from pathlib import Path

import pytest

from s1a import batch_v4 as B
from s1a import examples_v43 as EX
from s1a import nov16_v41 as NV
from s1a import step4_fake_v43 as F43
from s1a import step4_fake_v44 as F
from s1a import step4_prompts as SP
from s1a import step4_v43 as V
from s1a import step4_v44 as S
from s1a.log_v44 import RepairLog, call_rows

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CFG = S.load_config()
TH = CFG["thresholds"]
ALL_OFF = S.with_switches(CFG, off=S.SWITCHES)
needs_real = pytest.mark.skipif(not (S.STEP3_DIRS["a_llama43"] / "dev50" / "a.columns.json").exists()
                                or not (ROOT / "results" / "wf_v43" / "u2" / "scores" / "final_columns.json").exists()
                                or not (ROOT / "gt" / "schema_gt_v1.yaml").exists(), reason="a_llama43 / GT files not in this checkout")


def col(ent, i, name, vtype="text", n=10):
    return {"id": f"{ent}:{i}", "name": name, "description": f"d {name}", "role": "", "value_type": {"dominant": vtype, "share": 1.0},
            "examples": [["v", "in v text"]], "n_mentions": n, "n_dialogues": 3, "signal": "", "flag": ""}


# two entities (boat, shop): reference numbers with the same name in both, one with shared values; times; plain columns
COLS = [col("boat", 1, "boat name"), col("boat", 2, "reference number", "id"), col("boat", 3, "departure time", "time"),
        col("boat", 4, "colour"), col("boat", 5, "crew size", "number"),
        col("shop", 1, "shop name"), col("shop", 2, "ticket code", "id"), col("shop", 3, "opening time", "time"),
        col("shop", 4, "reference number", "id"), col("shop", 5, "note")]
VALUES = {"boat:1": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"], "boat:2": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10"],
          "boat:3": [f"0{k}:00" for k in range(10)], "boat:4": ["red"] * 4 + ["blue"] * 3 + ["green"] * 3,
          "boat:5": [str(k) for k in range(10)],
          "shop:1": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"], "shop:2": ["r1", "r2", "r3", "x4", "x5", "x6", "x7", "x8", "x9", "x10"],
          "shop:3": [f"1{k}:00" for k in range(10)], "shop:4": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"],
          "shop:5": ["x"] * 10}
STATS = {i: {"n": len(v), "values": sorted(set(v))} for i, v in VALUES.items()}


def fake_values(inp, set_name, columns_file, cols, root):
    return {c["id"]: STATS[c["id"]] for c in cols}


@pytest.fixture()
def root(tmp_path):
    d = tmp_path / "root" / B.INPUT_DIR / "dev50"
    d.mkdir(parents=True)
    B.write_json(d / "a.columns.json", COLS)
    return tmp_path / "root"


def run_fake(out, root, cfg, inputs=("a",), seeds=(0, 1, 2), backend=None):
    return S.run(out, backend or F.FakeV44(), inputs=inputs, sets=("dev50",), seeds=seeds, cfg=cfg, root=root, log=lambda m: None,
                 values_fn=fake_values)


# ---------------------------------------------------------------- config, key and link candidates
def test_config_has_every_switch_and_thresholds():
    assert set(CFG["switches"]) == set(S.SWITCHES) and all(v is True for v in CFG["switches"].values())
    assert {"key_min_mentions", "key_distinct_share", "link_min_shared_values", "link_overlap_share", "vote_table_jaccard"} <= set(TH)
    off = S.with_switches(CFG, off=("vote",))
    assert off["switches"]["vote"] is False and off["switches"]["code_links"] is True and CFG["switches"]["vote"] is True
    with pytest.raises(ValueError):
        S.with_switches(CFG, nope=True)


def test_key_candidates_need_all_different_values_enough_mentions_and_a_non_measure_type():
    cands = S.key_candidates(COLS[:5], STATS, TH)
    assert cands == ["boat:1", "boat:2", "boat:5"]          # departure time is a time, colour repeats
    assert S.key_candidates([COLS[5]], {"shop:1": {"n": 4, "values": list("abcd")}}, TH) == []       # fewer than key_min_mentions
    assert S.key_candidates([COLS[1]], {"boat:2": {"n": 10, "values": list("abcdefgh")}}, TH) == []                 # 8/10 < 0.9


def test_key_candidate_threshold_is_inclusive():
    c = COLS[1]
    assert S.is_idlike(c, {"n": 10, "values": [str(k) for k in range(9)]}, TH)
    assert not S.is_idlike(c, {"n": 11, "values": [str(k) for k in range(9)]}, TH)


def test_link_evidence_by_name_and_by_values_and_never_for_plain_columns():
    boat, shop = COLS[:5], COLS[5:]
    ev = S.link_evidence("boat", "shop", boat, shop, STATS, TH)
    assert len(ev) == 2 and any("same name" in e for e in ev) and any("share 3 values" in e for e in ev)    # reference numbers; ticket code shares r1..r3
    assert S.link_evidence("boat", "shop", [COLS[0], COLS[3]], shop, STATS, TH) == []                          # no id-like column on one side
    one = {**STATS, "shop:2": {"n": 10, "values": sorted({"r1", "x4", "x5", "x6", "x7", "x8", "x9", "x10", "x11", "x12"})}}
    assert not any("ticket code" in e for e in S.link_evidence("boat", "shop", boat, shop, one, TH))          # 1 shared value < link_min_shared_values


def test_link_pairs_all_pairs_when_off_and_only_proposed_when_on():
    st = {"cols": COLS, "names": ["boat", "shop", "extra"], "stats": STATS,
          "assign": {c["id"]: c["id"].split(":")[0] for c in COLS}}
    assert [(i, j) for i, j, _ in S.link_pairs(st, ALL_OFF["switches"], TH)] == [(0, 1), (0, 2), (1, 2)]
    got = S.link_pairs(st, CFG["switches"], TH)
    assert [(i, j) for i, j, _ in got] == [(0, 1)] and got[0][2]


# ---------------------------------------------------------------- pass 1 and 2
def test_p1_hint_lists_extras_only_and_drops_entity_names():
    text, schema, fmt = S.build_p1(COLS, CFG["switches"])
    assert fmt == "s44_p1" and schema["properties"]["tables"]["minItems"] == 0 and schema["properties"]["tables"]["maxItems"] == 6
    assert "Each heading already is a table" in text and "boat, shop" in text and "Worked example (other domain):" in text
    log = RepairLog()
    assert S.p1_extras({"tables": ["Boat", "Trip Log", "shop"]}, COLS, log, "c") == ["boat", "shop", "trip_log"]
    assert log.counts["p1_entity_name"] == 2


def test_p2_hint_schema_options_and_prompt():
    names = ["boat", "shop", "trip"]
    text, schema, fmt = S.build_p2(COLS, names, CFG["switches"])
    assert fmt == "s44_p2" and list(schema["properties"]) == [c["id"] for c in COLS] and schema["required"] == list(schema["properties"])
    assert schema["properties"]["boat:1"]["enum"] == ["keep", "move to shop", "move to trip", "other"]
    assert schema["properties"]["shop:1"]["enum"] == ["keep", "move to boat", "move to trip", "other"]
    assert "== boat ==" in text and "Tables: boat, shop, trip" in text and S.P2H_EXAMPLE.splitlines()[0] in text
    off = S.build_p2(COLS, names, S.with_switches(CFG, off=("other_choice",))["switches"])
    assert off[1]["properties"]["boat:1"]["enum"][-1] == "unused" and '"unused"' in off[0]


def test_p2_other_without_hint_is_the_v43_text_with_other():
    sw = S.with_switches(CFG, off=("entity_hint",))["switches"]
    text, schema, fmt = S.build_p2(COLS, ["boat", "shop"], sw)
    base = V.build_p2(COLS, ["boat", "shop"])
    assert fmt == "s44_p2" and schema["properties"]["boat:1"]["enum"] == ["boat", "shop", "other"]
    assert 'or into "other"' in text and '"x:3": "other"' in text and "unused" not in text.split("Tables:")[0]
    assert text.split("Tables:")[1] == base[0].split("Tables:")[1]


def test_p2_assign_keep_move_other_unused_and_repairs():
    names = ["boat", "shop", "trip"]
    got = {c["id"]: "keep" for c in COLS}
    got.update({"boat:2": "move to trip", "boat:3": "other", "boat:4": "other", "shop:5": "other", "shop:3": "move to nowhere", "shop:4": "unused"})
    del got["shop:2"]
    log = RepairLog()
    assign, host, kept = S.p2_assign(got, COLS, names, CFG["switches"], log, "c")
    assert assign["boat:1"] == "boat" and assign["boat:2"] == "trip" and assign["boat:3"] is None and assign["shop:2"] is None
    assert host == {"boat:3": "boat", "boat:4": "boat", "shop:5": "shop"}
    assert kept == ["boat", "shop", "trip"]
    assert log.counts["p2_missing_column"] == 1 and log.counts["p2_bad_name"] == 2          # move to nowhere; "unused" is not an option when other is on
    sw = S.with_switches(CFG, off=("other_choice",))["switches"]
    a2, h2, _ = S.p2_assign({**got, "boat:3": "unused"}, COLS, names, sw, RepairLog(), "c")
    assert a2["boat:3"] is None and "boat:3" not in h2


def test_rest_host_is_own_table_else_the_largest_kept_table():
    names = ["boat", "shop", "trip"]
    got = {c["id"]: "move to trip" if c["id"].startswith("boat") else "keep" for c in COLS}
    got["boat:1"] = "other"
    assign, host, kept = S.p2_assign(got, COLS, names, CFG["switches"], RepairLog())
    assert kept == ["shop", "trip"]
    assert host == {"boat:1": "shop"}                         # shop has 5 columns, trip 4: the largest kept table hosts


# ---------------------------------------------------------------- rest column in the answers
def test_rest_column_and_unused_reason_in_the_answers():
    st = {"cols": COLS, "names": ["boat", "shop"], "links": [],
          "assign": {**{c["id"]: c["id"].split(":")[0] for c in COLS}, "boat:4": None, "shop:5": None}, "rest_host": {"boat:4": "boat", "shop:5": "shop"}}
    keys = {0: {"primary_key": "boat:1", "new_id_name": ""}, 1: {"primary_key": "shop:1", "new_id_name": ""}}
    a41, a42, a43, a44 = S.build_answers(st, keys, RepairLog(), "c")
    assert SP.validate_44(a44, a41, a42, a43, COLS) == [] and SP.validate_41(a41, COLS) == []
    assert {u["column"]: u["reason"] for u in a41["unused"]} == {"boat:4": f"{S.REST_REASON} boat", "shop:5": f"{S.REST_REASON} shop"}
    for t in a44["tables"]:
        assert t["columns"][-1] == {"column": "new:rest", "name": "rest", "type": "text"}
    canon = B.assemble_chain({"41": a41, "42": a42, "43": a43, "44": a44}, COLS)
    assert [c["name"] for c in canon["tables"][0]["columns"]][-1] == "rest" and canon["tables"][0]["columns"][-1]["new"]
    # a column already named "rest" keeps its name; the rest column becomes "rest 2"
    cols2 = [{**c, "name": "rest"} if c["id"] == "boat:5" else c for c in COLS]
    st2 = {**st, "cols": cols2}
    a = S.build_answers(st2, keys, RepairLog(), "c")
    assert [c["name"] for c in a[3]["tables"][0]["columns"]][-1] == "rest 2"


# ---------------------------------------------------------------- keys
def test_key_prompt_and_schema_with_candidates_and_the_no_call_rule():
    sw = CFG["switches"]
    text, schema, fmt = S.build_key("boat", COLS[:5], ["shop"], sw, ["boat:1", "boat:2"])
    assert fmt == "s44_key" and schema["properties"]["primary_key"]["enum"] == ["boat:1", "boat:2", "none"]
    assert schema["properties"]["foreign_keys"]["properties"]["shop"]["enum"] == [c["id"] for c in COLS[:5]] + ["new"]
    assert 'Use "none" only when no column' in text and 'Use "new" only' not in text
    assert "Candidates: boat:1, boat:2" in text and "Worked example (other domain):" in text
    st = {"cols": COLS, "names": ["boat", "shop"], "links": [], "stats": STATS, "assign": {c["id"]: c["id"].split(":")[0] for c in COLS}}
    assert S.key_plan(st, 0, sw, TH) == (["boat:1", "boat:2", "boat:5"], True)
    st["stats"] = {**STATS, **{c: {"n": 10, "values": ["x"]} for c in ("shop:1", "shop:2", "shop:4")}}
    assert S.key_plan(st, 1, sw, TH) == ([], False)                                       # no candidate, no link: no call
    st["links"] = [{"one": "boat", "many": "shop", "kind": "one_to_many"}]
    assert S.key_plan(st, 1, sw, TH) == ([], True)                                         # a reference to ask about
    assert S.key_plan(st, 1, ALL_OFF["switches"], TH) == ([], True)


def test_pair_prompt_has_three_options_and_the_evidence():
    text, schema, fmt = S.build_pair("boat", "shop", COLS[:5], COLS[5:], CFG["switches"], ["a and b share 3 values"])
    assert fmt == "s44_pair" and schema["properties"]["link"]["enum"] == ["none", "boat -> shop", "shop -> boat"]
    assert "a and b share 3 values" in text and "many_to_many" not in text and "Worked example (other domain):" in text


def test_new_prompts_have_no_dataset_words_and_examples_use_no_domain_words():
    assert not any(w in S.P2H_EXAMPLE.lower() for w in EX.BANNED)
    for name in ("INSTRUCTION_P1H", "INSTRUCTION_P2H", "INSTRUCTION_PAIR44", "INSTRUCTION_KEY44"):
        assert not any(w in getattr(S, name).lower() for w in EX.BANNED + ("multiwoz", "tear"))


# ---------------------------------------------------------------- vote
def st_of(assign, rest=(), names=None):
    names = names or sorted({a for a in assign.values() if a})
    return {"cols": COLS, "names": names, "assign": assign, "rest_host": {i: names[0] for i in rest}}


def base_assign(**over):
    a = {c["id"]: c["id"].split(":")[0] for c in COLS}
    a.update(over)
    return a


def test_vote_majority_and_tie_goes_to_the_earliest_seed():
    s0 = st_of(base_assign(**{"boat:1": "shop", "boat:2": "shop", "boat:3": None}))
    s1 = st_of(base_assign(**{"boat:1": "shop", "boat:2": "boat", "boat:3": "shop"}))
    s2 = st_of(base_assign(**{"boat:1": "boat", "boat:2": "boat", "boat:3": "boat"}))
    v = S.vote_state([s0, s1, s2], TH)
    assert v["assign"]["boat:1"] == "shop" and v["assign"]["boat:2"] == "boat"             # 2 of 3 each
    assert v["assign"]["boat:3"] is None                                                   # unused / shop / boat: tie, seed 0's choice
    assert v["vote_info"]["ties"] == 1 and v["names"] == ["boat", "shop"]
    row = next(x for x in v["votes"] if x["id"] == "boat:3")
    assert row["choices"] == ["unused", "table:shop", "table:boat"] and row["winner"] == "unused"


def test_vote_other_counts_as_a_choice_and_gets_a_host():
    a = base_assign(**{"shop:5": None})
    v = S.vote_state([st_of(a, rest=["shop:5"]), st_of(a, rest=["shop:5"]), st_of(base_assign())], TH)
    assert v["assign"]["shop:5"] is None and list(v["rest_host"]) == ["shop:5"]
    assert v["rest_host"]["shop:5"] in v["names"]
    v2 = S.vote_state([st_of(a, rest=["shop:5"]), st_of(a), st_of(a)], TH)               # rest, unused, unused
    assert "shop:5" not in v2["rest_host"]


def test_vote_matches_tables_by_name_then_by_jaccard_and_keeps_unmatched_ones():
    s0 = st_of(base_assign(**{"boat:4": "extra", "boat:5": "extra"}))
    s1 = st_of(base_assign(**{"boat:4": "trip", "boat:5": "trip", "shop:4": "other_thing", "shop:5": "other_thing"}))
    ref, maps = S.align_tables([s0, s1], TH)
    assert maps[1]["trip"] == "extra"                              # same two columns: Jaccard 1
    assert maps[1]["other_thing"] == "other_thing" and ref == ["boat", "extra", "shop", "other_thing"]
    ref2, maps2 = S.align_tables([s0, s1], {**TH, "vote_table_jaccard": 1.1})
    assert maps2[1]["trip"] == "trip" and "trip" in ref2           # no match above the threshold: its own table
    s2 = st_of(base_assign(**{"boat:4": "boat_extra"}))
    assert S.align_tables([s0, s2], TH)[1][1]["boat_extra"] == "extra"                 # Jaccard of {4,5} and {4} is 0.5: matched (>=)
    s4 = st_of(base_assign(**{"boat:4": "wide", "shop:4": "wide", "shop:5": "wide"}))
    assert S.align_tables([s0, s4], TH)[1][1]["wide"] == "wide"                        # Jaccard 1/4: a table of its own
    s3 = st_of(base_assign(**{"boat:4": "extra"}))
    assert S.align_tables([s0, s3], TH)[1][1]["extra"] == "extra"                      # same name: one table


def test_vote_drops_a_table_without_winning_columns():
    s0 = st_of(base_assign(**{"boat:4": "extra"}))
    v = S.vote_state([s0, st_of(base_assign()), st_of(base_assign())], TH)
    assert "extra" not in v["names"] and v["vote_info"]["tables_before"] == 3 and v["vote_info"]["tables"] == 2


# ---------------------------------------------------------------- all switches off = v4.3
def test_all_off_gives_the_v43_jobs_and_prompts(root, tmp_path):
    out43, out44 = tmp_path / "o43", tmp_path / "o44"
    V.run(out43, F43.FakeV43(), inputs=("a",), sets=("dev50",), seeds=(0, 1, 2), root=root, log=lambda m: None)
    info = run_fake(out44, root, ALL_OFF)
    assert info["finished"] == "3/3"                                       # no vote chain when the vote is off
    p43 = sorted(p.name for p in (out43 / "prompts").iterdir())
    assert p43 == sorted(p.name for p in (out44 / "prompts").iterdir())
    for name in p43:
        assert (out43 / "prompts" / name).read_text(encoding="utf-8") == (out44 / "prompts" / name).read_text(encoding="utf-8"), name
    for k in (1, 2, 3, 4):
        j43 = B.read_json(out43 / "manifests" / f"a_stage{k}.json")["jobs"]
        j44 = B.read_json(out44 / "manifests" / f"a_stage{k}.json")["jobs"]
        assert [{x: y for x, y in j.items() if x != "prompt_version"} for j in j43] == [{x: y for x, y in j.items() if x != "prompt_version"} for j in j44]
    for ch in B.read_json(out43 / "chains.json"):
        assert B.read_json(out43 / "final" / ch["id"] / "canonical.json") == B.read_json(out44 / "final" / ch["id"] / "canonical.json")
    assert B.read_json(out43 / "repairs.json")["counts"] == B.read_json(out44 / "repairs.json")["counts"]


# ---------------------------------------------------------------- end to end, all on
@pytest.fixture()
def full_run(root, tmp_path):
    out = tmp_path / "out"
    backend = F.FakeV44()
    info = run_fake(out, root, CFG, backend=backend)
    return out, info, backend


def test_all_on_run_finishes_with_a_vote_chain_and_each_column_once(full_run, root):
    out, info, backend = full_run
    assert info["chains"] == 4 and info["finished"] == "4/4"
    assert all(v["parse_errors"] == 0 for v in info["inputs"]["a"].values())
    status = B.read_json(out / "final" / "status.json")
    assert [r["kind"] for r in status] == ["main", "main", "main", "vote"] and status[-1]["run"] == "a_dev50_vote"
    for r in status:
        c = B.read_json(out / "final" / r["run"] / "canonical.json")
        used = [x["source"] for t in c["tables"] for x in t["columns"] if x["source"]]
        assert len(used) == len(set(used)) and set(used) | {u["source"] for u in c["unused"]} == {x["id"] for x in COLS}
        assert any(x["name"] == "rest" for t in c["tables"] for x in t["columns"])        # the fake answers "other" for every 7th column
    votes = B.read_json(out / "votes" / "a_dev50_vote.json")
    assert votes["info"]["seeds"] == 3 and len(votes["votes"]) == len(COLS)
    assert len(call_rows(out)) == backend.n_made


def test_all_on_calls_stages_and_candidate_rules(full_run, root):
    out, *_ = full_run
    rows = call_rows(out)
    fmts = {r["format"] for r in rows}
    assert fmts == {"s44_p1", "s44_p2", "s44_pair", "s44_key"}
    for ch in B.read_json(out / "chains.json"):
        mine = [r for r in rows if r["job"].startswith(ch["id"] + "_")]
        stage = lambda s: [r for r in mine if r["job"][len(ch["id"]):].startswith(s)]      # noqa: E731
        if ch["kind"] == "vote":
            assert not stage("_p1") and not stage("_p2")
        else:
            assert len(stage("_p1")) == 1 and len(stage("_p2")) == 1
        st, err, _ = S.replay(out, ch, 4, root)
        assert err is None
        assert len(stage("_r")) == len(S.link_pairs(st, ch["switches"], ch["thresholds"])) <= 1       # only the reference-number pair is proposed
        assert len(stage("_k")) == sum(S.key_plan(st, i, ch["switches"], ch["thresholds"])[1] for i in range(len(st["names"])))


def test_all_on_has_fewer_calls_than_v43_on_the_same_columns(full_run, root, tmp_path):
    out, *_ = full_run
    out43 = tmp_path / "o43"
    V.run(out43, F43.FakeV43(), inputs=("a",), sets=("dev50",), seeds=(0, 1, 2), root=root, log=lambda m: None)
    n44 = len([r for r in call_rows(out) if "_vote_" not in r["job"]])
    assert n44 < len(call_rows(out43))


def test_rerun_is_cached_and_missing_inputs_are_skipped(root, tmp_path):
    msgs = []
    out = tmp_path / "out"
    S.run(out, F.FakeV44(), inputs=("a_llama44", "a"), sets=("dev50",), seeds=(0, 1), cfg=CFG, root=root, step3_dirs={"a_llama44": tmp_path / "none"},
          log=msgs.append, values_fn=fake_values)
    assert any("skip input a_llama44 dev50" in m for m in msgs)
    again = S.run(out, F.FakeV44(), inputs=("a",), sets=("dev50",), seeds=(0, 1), cfg=CFG, root=root, log=lambda m: None, values_fn=fake_values)
    assert all(v["run"] == 0 for v in again["inputs"]["a"].values())


def test_missing_value_data_fails_fast_when_candidates_are_on(root, tmp_path):
    with pytest.raises(ValueError, match="no mention ids"):
        S.run(tmp_path / "o", F.FakeV44(), inputs=("a",), sets=("dev50",), seeds=(0,), cfg=CFG, root=root, log=lambda m: None, values_fn=lambda *a: None)
    S.run(tmp_path / "o2", F.FakeV44(), inputs=("a",), sets=("dev50",), seeds=(0,), cfg=S.with_switches(CFG, off=("key_candidates", "code_links")),
          root=root, log=lambda m: None, values_fn=lambda *a: None)


def test_column_file_resolver_knows_a_llama44(tmp_path):
    d = tmp_path / "a_llama44" / "dev50"
    d.mkdir(parents=True)
    assert S.columns_path("a_llama44", "dev50", {"a_llama44": tmp_path / "a_llama44"}) is None
    (d / "a.columns.json").write_text("[]", encoding="utf-8")
    assert S.columns_path("a_llama44", "dev50", {"a_llama44": tmp_path / "a_llama44"}) == d / "a.columns.json"
    assert S.columns_path("a_llama43", "dev50", {"a_llama43": tmp_path / "x"}) is None


def test_formats_are_plain_json_for_the_backend():
    assert set(S.FORMATS) <= set(NV.PLAIN_FORMATS)
    assert NV.parse_answer('{"link": "none"}', {"format": "s44_pair"}, {}) == ({"link": "none"}, [])
    assert NV.parse_answer("{cut", {"format": "s44_key"}, {})[1]


def test_fake_answers_are_valid_for_the_hint_and_plain_p2_schemas():
    for sw in (CFG["switches"], S.with_switches(CFG, off=("entity_hint",))["switches"]):
        text, schema, fmt = S.build_p2(COLS, ["boat", "shop", "extra"], sw)
        ans = json.loads(F.FakeV44().respond({"format": fmt}, text, schema))
        assert set(ans) == set(schema["properties"]) and all(v in schema["properties"][k]["enum"] for k, v in ans.items())


# ---------------------------------------------------------------- scoring and the T6 / T7 runners on the a_llama43 stand-in
@pytest.fixture(scope="module")
def t6_run(tmp_path_factory):
    if not (S.STEP3_DIRS["a_llama43"] / "dev50" / "a.columns.json").exists():
        pytest.skip("a_llama43 not in this checkout")
    import t6_step4_v44 as T6
    out = tmp_path_factory.mktemp("t6")
    info = T6.run(F.FakeV44(), out=out, inputs=("a_llama43",), sets=("dev50",), seeds=(0, 1, 2), log=lambda m: None)
    return T6, out, info


@needs_real
def test_t6_fake_run_on_the_stand_in_scores_vote_and_single_schemas(t6_run):
    T6, out, info = t6_run
    assert info["finished"] == "4/4"
    assert (out / "values" / "a_llama43_dev50.json").exists() and (out / "score_map" / "a_llama43" / "dev50" / "train.json").exists()
    rows = T6.score(out)
    assert len(rows) == 8 and {"table_f1", "grouping_f1", "gt_columns_placed_k", "gt_in_rest_k", "gt_in_rest_n", "pk_right", "pk_right_b", "rel_recall",
                               "rel_precision", "kind"} <= set(rows[0])
    assert {r["kind"] for r in rows} == {"main", "vote"} and all(int(r["gt_in_rest_k"]) <= int(r["gt_in_rest_n"]) for r in rows)
    text = (out / "summary.md").read_text(encoding="utf-8")
    assert "| a_llama43 | dev50 | vote | 1/1" in text and "| a_llama43 | dev50 | single | 3/3" in text and "GT columns in rest" in text
    assert (out / "calls.csv").exists()


@needs_real
def test_rest_gt_count_uses_the_unused_entries_with_the_rest_reason(t6_run):
    import score_v4 as SCR
    from s1a import step4_score as SS
    from s1a import step4_score_v43 as SC43
    T6, out, _ = t6_run
    gt = SC43.load_gt(ROOT)
    c = B.read_json(out / "final" / "a_llama43_dev50_s0" / "canonical.json")
    mapping = SS.map_columns(c, "dev50", S.score_map_dir(out, "a_llama43", ROOT), SCR.GT_LEVELS["dev50"], gt)
    res = SS.score(c, gt, "dev50", False, mapping)
    k, n = S.rest_gt_columns(c, mapping, gt, res["design"], None)
    assert 0 <= k <= n and n == res["metrics"]["gt_columns_placed"]["n"]
    noreason = {**c, "unused": [{**u, "reason": "x"} for u in c["unused"]]}
    assert S.rest_gt_columns(noreason, mapping, gt, res["design"], None)[0] == 0


@needs_real
def test_score_map_for_a_llama43_differs_from_the_qwen_handover_mapping(t6_run):
    T6, out, _ = t6_run
    rows_new = T6.score(out)
    legacy = S.score_chains(out, ROOT, legacy_mapping=True)
    assert [r["schema"] for r in rows_new] == [r["schema"] for r in legacy]
    assert any(a["gt_columns_placed_k"] != b["gt_columns_placed_k"] for a, b in zip(rows_new, legacy))
    S.score_chains(out, ROOT)                                           # leave scores.csv as the corrected one


@needs_real
def test_t7_fake_run_writes_one_table_and_the_layout(tmp_path):
    import t7_ablation_v44 as T7
    info = T7.run(F.FakeV44(), out=tmp_path, inp="a_llama43", set_name="dev50", log=lambda m: None)
    assert set(info["runs"]) == {"all_on", *S.SWITCHES}
    for sw in S.SWITCHES:
        assert (tmp_path / sw / "scores.csv").exists()
    assert (tmp_path / "all_on" / "final" / "status.json").exists()
    text = T7.table(tmp_path)
    for sw in S.SWITCHES:
        assert f"| {sw} |" in text
    assert "table F1 on" in text and (tmp_path / "t7_table.md").exists()
    off = B.read_json(tmp_path / "entity_hint" / "chains.json")
    assert [c["seed"] for c in off] == [0] and off[0]["switches"]["entity_hint"] is False
