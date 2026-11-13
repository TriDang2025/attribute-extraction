"""wf_v4.3 U3 / U4: Step 4 v4.3 (s1a/step4_v43.py, step4_fake_v43.py, step4_score_v43.py, scripts/u4_step4_v43.py) with the fake model."""
import json
import shutil
import sys
from pathlib import Path

import pytest

from s1a import batch_v4 as B
from s1a import examples_v43 as EX
from s1a import nov16_v41 as NV
from s1a import step4_fake_v43 as F
from s1a import step4_prompts as SP
from s1a import step4_score_v43 as SC
from s1a import step4_v43 as S
from s1a.log_v43 import RepairLog, call_rows

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
INPUT_A = ROOT / "results" / "wf_v4" / "inputs"
needs_inputs = pytest.mark.skipif(not (INPUT_A / "dev50" / "a.columns.json").exists(), reason="Step 4 inputs not in this checkout")


def col(i, name, ents="x"):
    return {"id": f"{ents}:{i}", "name": name, "description": f"d {name}", "role": "", "value_type": {"dominant": "text", "share": 1.0},
            "examples": [["v", "in v text"]], "n_mentions": 3, "n_dialogues": 2}


COLS = [col(1, "car model"), col(2, "car class"), col(3, "plate"), col(4, "customer name"), col(5, "phone"), col(6, "noise")]


def state(links=(), assign=None, names=("car", "customer")):
    a = assign or {"x:1": "car", "x:2": "car", "x:3": "car", "x:4": "customer", "x:5": "customer", "x:6": None}
    return {"cols": COLS, "names": list(names), "assign": a, "links": [dict(x) for x in links]}


# ---------------------------------------------------------------- schemas and pass 1
def test_p1_schema_caps_at_8_tables():
    sch = S.p1_schema()["properties"]["tables"]
    assert (sch["minItems"], sch["maxItems"]) == (1, 8)
    log = RepairLog()
    names = S.p1_names({"tables": [f"t{i}" for i in range(11)]}, log)
    assert len(names) == 8 and log.counts["p1_over_cap"] == 1


def test_p1_repeats_and_names_are_repaired_and_counted():
    log = RepairLog()
    names = S.p1_names({"tables": ["Rental", "rental", "Car Class", ""]}, log, "c")
    assert names == ["rental", "rental_2", "car_class"]
    assert log.counts["p1_name_repeat"] == 1 and log.counts["p1_empty_name"] == 1 and log.counts["p1_name_normalised"] == 2
    assert S.p1_names({"tables": "no list"}, RepairLog()) == []


# ---------------------------------------------------------------- pass 2
def test_p2_schema_keys_every_column_once_and_blocks_new_groups():
    sch = S.p2_schema([c["id"] for c in COLS], ["car", "customer"])
    assert list(sch["properties"]) == [c["id"] for c in COLS] and sch["required"] == list(sch["properties"])
    assert sch["additionalProperties"] is False
    assert all(v == {"enum": ["car", "customer", "unused"]} for v in sch["properties"].values())


def test_p2_assign_counts_repairs_and_drops_empty_tables():
    log = RepairLog()
    got = {"x:1": "car", "x:2": "Car", "x:3": "boat", "x:4": "unused", "x:5": "customer", "x:99": "car"}      # x:6 missing
    assign, kept = S.p2_assign(got, COLS, ["car", "customer", "spare"], log, "c")
    assert assign == {"x:1": "car", "x:2": "car", "x:3": None, "x:4": None, "x:5": "customer", "x:6": None}
    assert kept == ["car", "customer"]
    assert (log.counts["p2_bad_name"], log.counts["p2_missing_column"], log.counts["p2_unknown_column"], log.counts["p2_empty_table"]) == (1, 1, 1, 1)


# ---------------------------------------------------------------- pairs
def test_pair_cap_is_28_and_answer_options():
    assert S.MAX_PAIRS == 28
    assert len(S.pairs_of({"names": [f"t{i}" for i in range(S.MAX_TABLES)]})) == 28
    assert S.pair_options("a", "b") == ["none", "a -> b", "b -> a", "many_to_many"]
    assert S.pair_schema("a", "b")["properties"]["link"]["enum"] == S.pair_options("a", "b")
    log = RepairLog()
    assert [S.pair_kind({"link": v}, "a", "b", log) for v in ("none", "a->b", "B -> A", "many_to_many")] == ["none", "xy", "yx", "mm"]
    assert S.pair_kind({"link": "maybe"}, "a", "b", log) == "none" and log.counts["pair_bad_answer"] == 1


# ---------------------------------------------------------------- keys and assembly
def answers(st, keys, log=None):
    log = log or RepairLog()
    a41, a42, a43, a44 = S.build_answers(st, keys, log, "c")
    errs = (SP.validate_41(a41, COLS) + SP.validate_42(a42, a41) + SP.validate_43(a43, a41, a42) + SP.validate_44(a44, a41, a42, a43, COLS))
    return (a41, a42, a43, a44), errs, log


def test_key_schema_and_prompt_are_one_table():
    text, sch = S.build_key("car", [COLS[0], COLS[1]], ["customer"])
    assert sch["properties"]["primary_key"]["enum"] == ["x:1", "x:2", "new"]
    assert list(sch["properties"]["foreign_keys"]["properties"]) == ["customer"]
    assert "[x:3]" not in text and "car model" in text and "Worked example (other domain):" in text
    assert "foreign_keys" not in S.build_key("car", [COLS[0]], [])[1]["properties"]


def test_no_column_in_two_tables_and_types_from_value_type():
    st = state([{"one": "customer", "many": "car", "kind": "one_to_many"}])
    ans, errs, log = answers(st, {0: {"primary_key": "x:3", "new_id_name": "", "foreign_keys": {"customer": "x:1"}},
                                  1: {"primary_key": "new", "new_id_name": "cust id"}})
    assert errs == [] and log.total() == 0
    seen = [c["column"] for t in ans[3]["tables"] for c in t["columns"] if not c["column"].startswith("new:")]
    assert sorted(seen) == ["x:1", "x:2", "x:3", "x:4", "x:5"] and len(seen) == len(set(seen))
    assert all(c["type"] == "text" for t in ans[3]["tables"] for c in t["columns"] if not c["column"].startswith("new:"))
    car = ans[3]["tables"][0]
    assert car["foreign_keys"] == [{"column": "x:1", "ref_table": "customer", "ref_column": "new:cust id"}]
    assert ans[0]["unused"] == [{"column": "x:6", "reason": "not assigned to a table"}]


def test_new_key_name_equal_to_a_column_is_renamed_and_counted():
    ans, errs, log = answers(state(), {0: {"primary_key": "new", "new_id_name": "Plate"}, 1: {"primary_key": "x:4", "new_id_name": ""}})
    assert errs == [] and log.counts["key_name_renamed"] == 1
    car = ans[3]["tables"][0]
    assert car["new_id_name"] == "Plate key"
    assert "new:Plate key" not in [c["column"] for c in car["columns"]]


def test_missing_and_bad_key_answers_are_repairs_not_errors():
    st = state([{"one": "customer", "many": "car", "kind": "one_to_many"}])
    ans, errs, log = answers(st, {0: {"primary_key": "x:5", "new_id_name": "", "foreign_keys": {"customer": "x:99"}}})   # x:5 is not a car column
    assert errs == []
    assert log.counts["key_invalid"] == 1 and log.counts["fk_invalid"] == 1 and log.counts["key_no_answer"] == 1 and log.counts["key_name_empty"] == 2
    car = ans[3]["tables"][0]
    assert car["primary_key"] == "new" and car["new_id_name"] == "car id"
    assert [c["name"] for c in car["columns"]][-1] == "customer id" and car["foreign_keys"][0]["column"] == "new:customer id"


def test_reference_column_repeats_and_name_clash_are_repaired():
    cols = COLS + [col(7, "customer id")]
    st = {"cols": cols, "names": ["car", "customer", "owner"], "assign": {"x:1": "car", "x:2": "car", "x:3": "car", "x:4": "customer", "x:5": "customer",
          "x:6": "owner", "x:7": "car"}, "links": [{"one": "customer", "many": "car", "kind": "one_to_many"}, {"one": "owner", "many": "car", "kind": "one_to_many"}]}
    log = RepairLog()
    a41, a42, a43, a44 = S.build_answers(st, {0: {"primary_key": "x:3", "new_id_name": "", "foreign_keys": {"customer": "x:7", "owner": "x:7"}},
                                              1: {"primary_key": "x:4", "new_id_name": ""}, 2: {"primary_key": "x:6", "new_id_name": ""}}, log, "c")
    assert SP.validate_44(a44, a41, a42, a43, cols) == []
    assert log.counts["fk_col_dup"] == 1
    assert [f["column"] for f in a44["tables"][0]["foreign_keys"]] == ["x:7", "new:owner id"]


def test_many_to_many_makes_a_link_table_with_two_references():
    st = state([{"a": "car", "b": "customer", "kind": "many_to_many"}])
    ans, errs, _ = answers(st, {0: {"primary_key": "x:3", "new_id_name": ""}, 1: {"primary_key": "x:4", "new_id_name": ""}})
    assert errs == []
    link = ans[3]["tables"][-1]
    assert link["name"] == "car_customer" and {f["ref_table"] for f in link["foreign_keys"]} == {"car", "customer"}
    assert [t["name"] for t in ans[2]["new_tables"]] == ["car_customer"]
    assert {r["kind"] for r in ans[2]["relationships"]} == {"many_to_many", "one_to_many"}


def test_prompts_carry_the_worked_example():
    for sections, text in ((("Pass 1",), S.build_p1(COLS)[0]), (("Pass 1", "Pass 2"), S.build_p2(COLS, ["car"])[0]),
                           (("Links",), S.build_pair("a", "b", [COLS[0]], [COLS[3]])[0]), (("Keys",), S.build_key("car", [COLS[0]], [])[0])):
        assert "Worked example (other domain):" in text and S.example_part(*sections) in text
    assert S.example_part("Pass 1") != EX.STEP4_EXAMPLE and "Keys" not in S.example_part("Pass 1").split("\n")[-1]


# ---------------------------------------------------------------- fake end to end
@pytest.fixture(scope="module")
def fake_run(tmp_path_factory):
    if not (INPUT_A / "dev50" / "a.columns.json").exists():
        pytest.skip("Step 4 inputs not in this checkout")
    tmp = tmp_path_factory.mktemp("u4")
    llama = tmp / "a_llama43"
    for s in S.SETS:                                      # a fake copy of input a stands in for the Step 3 v4.3 columns
        (llama / s).mkdir(parents=True)
        shutil.copy(INPUT_A / s / "a.columns.json", llama / s / "a.columns.json")
    out, msgs = tmp / "out", []
    backend = F.FakeV43()
    info = S.run(out, backend, a_llama43_dir=llama, log=msgs.append)
    return out, info, backend, tmp


@needs_inputs
def test_fake_run_all_inputs_no_parse_errors_and_call_counts(fake_run):
    out, info, backend, _ = fake_run
    assert info["chains"] == 18 and info["finished"] == "18/18"
    assert all(v["parse_errors"] == 0 for inp in info["inputs"].values() for v in inp.values())
    status = B.read_json(out / "final" / "status.json")
    assert {r["input"] for r in status} == {"a", "c1", "a_llama43"} and all(r["ok"] for r in status)
    rows = call_rows(out)
    for ch in B.read_json(out / "chains.json"):
        st, err, _ = S.replay(out, ch, 4)
        n = k = len(st["names"])
        mine = [r for r in rows if r["job"].startswith(ch["id"] + "_")]
        assert err is None and len(mine) == 2 + n * (n - 1) // 2 + k <= 2 + 28 + 8
        assert sum(r["job"].endswith("_p1") for r in mine) == 1 and sum(r["job"].endswith("_p2") for r in mine) == 1
        assert sum("_r" in r["job"][len(ch["id"]):] for r in mine) == n * (n - 1) // 2
        keys = [r for r in mine if r["job"][len(ch["id"]):].startswith("_k")]
        assert len(keys) == k                                      # one key call per table
        assert len({r["job"] for r in mine}) == len(mine)
    assert backend.n_made == len(rows)


@needs_inputs
def test_fake_run_each_column_once_and_seeds_change_order(fake_run):
    out, *_ = fake_run
    for ch in B.read_json(out / "chains.json"):
        c = B.read_json(out / "final" / ch["id"] / "canonical.json")
        used = [x["source"] for t in c["tables"] for x in t["columns"] if x["source"]]
        assert len(used) == len(set(used))
        ids = {x["id"] for x in B.chain_columns(ch, ROOT)}
        assert set(used) | {u["source"] for u in c["unused"]} == ids
    p = lambda ch: (out / "prompts" / f"{ch}_p1.txt").read_text(encoding="utf-8")      # noqa: E731
    assert p("a_dev50_s0") != p("a_dev50_s1") and p("a_dev50_s1") != p("a_dev50_s2")


@needs_inputs
def test_fake_run_output_is_read_by_the_t7_scorer_and_repairs_are_saved(fake_run):
    out, *_ = fake_run
    if not (ROOT / "gt" / "schema_gt_v1.yaml").exists():
        pytest.skip("GT not in this checkout")
    rows = SC.score_chains(out)
    assert len(rows) == 36 and {"table_f1", "grouping_f1", "pk_right", "pk_right_b", "rel_recall", "rel_precision", "gt_columns_placed_k"} <= set(rows[0])
    assert (out / "scores.csv").exists()
    text = SC.summary(out, rows)
    assert "| a | all | 6/6" in text and "| a_llama43 | all | 6/6" in text and "calls per chain" in text
    fig = SC.figure_data(out)
    assert fig["finished"] and fig["model"]["tables"] and fig["gt"]["tables"] and "match" in fig
    rep = B.read_json(out / "repairs.json")
    assert rep["total"] == sum(rep["counts"].values()) == sum(sum(v.values()) for v in rep["per_chain"].values())
    assert all((out / "final" / c / "repairs.json").exists() for c in rep["per_chain"])


@needs_inputs
def test_missing_a_llama43_is_skipped_with_a_message_and_rerun_is_cached(tmp_path):
    msgs = []
    info = S.run(tmp_path, F.FakeV43(), inputs=("c1", "a_llama43"), sets=("dev50",), seeds=(0,), a_llama43_dir=tmp_path / "none", log=msgs.append)
    assert info["inputs"]["a_llama43"].startswith("skipped") and info["chains"] == 1
    assert any("skip input a_llama43 dev50" in m for m in msgs)
    again = S.run(tmp_path, F.FakeV43(), inputs=("c1",), sets=("dev50",), seeds=(0,), log=lambda m: None)
    assert all(v["run"] == 0 for v in again["inputs"]["c1"].values())


def test_formats_are_plain_json_for_the_backend():
    assert set(S.FORMATS) <= set(NV.PLAIN_FORMATS)
    assert NV.parse_answer('{"link": "none"}', {"format": "s43_pair"}, {}) == ({"link": "none"}, [])
    assert NV.parse_answer("{cut", {"format": "s43_pair"}, {})[1]
