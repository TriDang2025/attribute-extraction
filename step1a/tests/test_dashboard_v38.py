import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import nosplit_v38 as NS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a import run_data_v37 as RD  # noqa: E402
from test_w1_v37 import toy, variant, with_variants  # noqa: E402

RULES = CE.rules_v11(2)


def toy_ed(split=()):
    clusters = {"c1": ["Train price"] * 6, "c2": ["Train price"] * 6, "c3": [""] * 8, "c4": ["Train departure"] * 5}
    ed = toy(clusters)
    ed = replace(ed, labels=pd.DataFrame(columns=["cluster_id", "label"]))
    v = variant(ed, {"c1": "g1", "c2": "g2", "c3": "g3", "c4": "g4"}, names={"g1": "price", "g2": "fare", "g3": "chat", "g4": "departure"},
                split=split)
    return with_variants(ed, A_s012=v)


def test_guard_check():
    ok, text = DB.guard_check("dev50", {"train": 8, "hotel": 12, "restaurant": 11})
    assert ok and "train 8/8" in text
    ok, text = DB.guard_check("dev50b", {"train": 8, "hotel": 9, "restaurant": 12})
    assert not ok and text.endswith("below: hotel")


def test_column_kind():
    base = {"Train price"}
    assert DB.column_kind("noise", "", base) == "noise"
    assert DB.column_kind("real", "Train price", base) == "gt"
    assert DB.column_kind("real", "Hotel area", base) == "wrong"
    assert DB.column_kind("mixed", "Train price", base) == "no_gt"
    assert DB.column_kind("unknown", "", base) == "no_gt"


def test_name_tokens_and_pair_cause():
    assert DB.name_tokens("Train_departure-stations") == {"departure", "station"}
    assert DB.pair_cause(True, False, "a", "b") == "split_pass"
    assert DB.pair_cause(False, False, "arrival_location", "departure location") == "wording"
    assert DB.pair_cause(False, False, "price", "fare") == "other"
    assert DB.pair_cause(False, False, "train price", "hotel price") == "wording"


def test_entity_counts_and_dup_pairs():
    ed = toy_ed(split={"g2"})
    c = DB.entity_counts(ed, "A s012", RULES, {})
    assert c["found"] == 2 and c["gold"] == 9 and c["columns"] == 4
    assert c["found_columns"] == 3 and c["dup"] == 1   # price has two columns, departure one
    assert c["kinds"] == {"gt": 3, "wrong": 0, "noise": 1, "no_gt": 0}
    p = DB.dup_pairs(ed, "A s012", RULES, {})
    assert len(p) == 1 and p.iloc[0]["cause"] == "split_pass" and p.iloc[0]["same_role"]
    assert set(p.iloc[0][["col_a", "col_b"]]) == {"fare", "price"}
    p2 = DB.dup_pairs(toy_ed(), "A s012", RULES, {})
    assert p2.iloc[0]["cause"] == "other"
    counts = DB.cause_counts(pd.concat([p.assign(row="x"), p2.assign(row="y")]))
    assert counts.set_index("row").loc["x", "split_pass"] == 1 and counts.set_index("row").loc["y", "other"] == 1


def test_range_row_and_md():
    rows = pd.DataFrame([{"set": "dev50", "row": r, "n_runs": 1, "found_train": t, "found_hotel": 12, "found_restaurant": 11,
                          "found_total": t + 23, "gold_total": 40, "columns": col, "columns_per_found": cpf, "dup_columns": 1,
                          "wrong_columns": 2, "wrong_entity_columns": 1, "noise_columns": 1, "extras_no_gt": 3, "merges_right": 3,
                          "merges_judged": 11, "noise_caught": 9, "noise_n": 13, "marks_right": 9, "marks_n": 14, "review_edits": 3,
                          "guard": "pass", "guard_detail": "", "cpf_bar": "pass"}
                         for r, t, col, cpf in (("o1", 7, 60, 1.1), ("o2", 8, 64, 1.3))])
    r = DB.range_row(rows, ["o1", "o2"], "range")
    assert r["found_train"] == "7-8" and r["columns"] == "60-64" and r["columns_per_found"] == "1.100-1.300"
    assert r["guard"] == "n/a" and r["cpf_bar"] == "mixed" and "train 7" in r["guard_detail"]
    md = DB.dashboard_md(pd.DataFrame([r]))
    assert "| range | 7-8 + 12 + 11" in md


def test_no_split_patches_and_restores():
    orig_load, orig_jobs = PV.load_split_results, RD.batch_jobs
    with NS.no_split():
        assert PV.load_split_results("anywhere") == {}
    assert PV.load_split_results is orig_load and RD.batch_jobs is orig_jobs
    wrapped = NS.drop_split_jobs(lambda *a: (["a1"], ["s1"]))
    assert wrapped("d", "r", "e") == (["a1"], [])
