"""wf_v4.7 Z3: the loop-2 switches (config/wf_v47_loop2.json): Step 1b format fix, r4 vote 1 of 3, r2 separate names, naming hint."""
import shutil

import pandas as pd
import pytest

from s1a import batch_v4 as B
from s1a import dupcheck_l2_v41 as DL
from s1a import loop2_v46 as L
from test_dupcheck_l2_v41 import OLD, joins, new
from test_loop2_v46 import LOOP1, SET, HashEnc, HotelGliner, col, need_data

V46, V47 = L.load_config(), L.load_config(L.CONFIG_V47)


def test_v47_config_differs_from_v46_only_in_the_switches():
    assert V47["evidence"] == V46["evidence"]
    assert (V47["step1b"]["min_votes"], V47["step1b"]["prompt_examples"]) == (1, "v47")
    assert V47["step3"]["separate_names"] and V47["step3"]["name_hint"]
    same = lambda d: {k: v for k, v in d.items() if k not in ("min_votes", "prompt_examples")}   # noqa: E731
    assert same(V47["step1b"]) == same(V46["step1b"])


def test_v47_step1b_examples_have_no_placeholder():
    cols = [col(1, "area"), col(2, "price")]
    old = L.question_prompts("hotel", cols, V46)
    fixed = L.question_prompts("hotel", cols, V47)
    assert all('"..."' in t for t, _ in old.values())                  # v4.6 text unchanged
    for t, _ in fixed.values():
        assert '"..."' not in t and "car rental" in t
    assert "fuel policy" in fixed["missing"][0] and "mileage limit" in fixed["missing"][0]


def ms(*v):
    return {"mentions": [{"norm_value": x} for x in v]}


def test_new_columns_separate_keeps_one_column_per_cluster():
    dec = pd.DataFrame([{"cluster_id": "L2_hotel#0", "name": "amenities", "description": "", "action": "keep"},
                        {"cluster_id": "L2_hotel#1", "name": "amenities", "description": "", "action": "keep"}])
    cl = {"L2_hotel#0": {**ms("free wifi"), "label": "amenities"}, "L2_hotel#1": {**ms("parking"), "label": "parking"}}
    assert len(DL.new_columns(dec, cl, 10)) == 1                         # v4.6: same name, one column
    cols = DL.new_columns(dec, cl, 10, separate=True)
    assert [(c["cid"], c["name"], c["clusters"]) for c in cols] == [(10, "amenities", ["L2_hotel#0"]), (11, "parking", ["L2_hotel#1"])]


def test_resolve_without_new_joins_keeps_new_columns_apart():
    n = [new(7, "free parking", 5), new(8, "pets")]
    both = [joins([7, 8]), joins([7, 8])]
    assert [r["name"] for r in DL.resolve(OLD, n, both)] == ["free parking"]
    out = DL.resolve(OLD, n, both, join_new=False)
    assert [(r["name"], r["status"], r["joined"]) for r in out] == [("free parking", "new", []), ("pets", "new", [])]


def test_add_hints_puts_the_label_under_each_shown_header():
    text = "intro\n### L2_hotel#0  (mentions 3, distinct values 2)\nExamples:\n### L2_hotel#1  (mentions 1)\nend"
    cl = [{"id": "L2_hotel#0", "label": "amenities"}, {"id": "L2_hotel#1", "label": "parking"}, {"id": "L2_hotel#9", "label": "x"}]
    out = L.add_hints(text, cl).splitlines()
    assert out[2] == L.NAME_HINT.format(label="amenities") and out[5] == L.NAME_HINT.format(label="parking")
    assert len(out) == len(text.splitlines()) + 2                       # the cluster not in this batch adds nothing
    with pytest.raises(ValueError):
        L.add_hints(text + "\n### L2_hotel#0  (again)", cl[:1])


@pytest.fixture()
def loop1_copy(tmp_path):
    for rel in ("scores/final_columns.json", f"a_llama44/{SET}/a.columns.json"):
        (tmp_path / "step3" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(LOOP1 / "step3" / rel, tmp_path / "step3" / rel)
    return tmp_path


@need_data
def test_run_loop2_v47_end_to_end_with_the_fake_model(loop1_copy):
    info = L.run_loop2(loop1_copy, SET, L.FakeLoop2LLM(), HashEnc(), HotelGliner, V47, log=lambda *_: None)
    l2 = loop1_copy / "loop2"
    sug = pd.read_csv(l2 / "suggestions.csv", keep_default_na=False)
    hotel = {r.name: r for r in sug.itertuples() if r.entity == "hotel"}
    assert hotel["contact number"].stage != "vote"                      # one order is enough now (r4)
    assert not (sug["stage"] == "vote").any()
    for p in l2.glob("step1b/prompts/*.txt"):
        assert '"..."' not in p.read_text(encoding="utf-8"), p.name
    names = [p.read_text(encoding="utf-8") for p in l2.glob("step3/prompts/*names*.txt")]
    assert names and all("Hint: this cluster was searched for as" in t for t in names)
    final = B.read_json(l2 / "columns_l2.json")
    assert all(len(c["clusters"]) == 1 and not c["joined"] for cs in final.values() for c in cs)   # r2: one cluster per column
    assert info["new_columns"] >= 1
