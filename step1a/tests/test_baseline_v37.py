"""wf_v3.7 W3: baseline prompts (T10) and baseline scoring (T11). Toy data only."""

import json

import pandas as pd
import pytest

from s1a import baseline_prompt_v37 as BP
from s1a import baseline_v37 as BL
from s1a import llm_cache as LC
from s1a import pilot_input as PIN

SLOTS = {"Train destination": ("train-destination", "destination of the train"),
         "Train arrive by": ("train-arriveby", "arrival time of the train"),
         "Train day": ("train-day", "day of the train")}


# ---- T10
def test_fill_all_fit_and_order():
    texts = {"a": "User: hi", "b": "User: yo", "c": "User: hey"}
    assert BP.fill("train", ["a", "b", "c"], texts, "v0")[0] == ["a", "b", "c"]
    v1, v2 = (BP.fill("train", ["a", "b", "c"], texts, v)[0] for v in ("v1", "v2"))
    assert sorted(v1) == sorted(v2) == ["a", "b", "c"]
    assert BP.order(list("abcdefgh"), "v1") == BP.order(list("abcdefgh"), "v1") != list("abcdefgh")
    assert BP.order(list("abcdefgh"), "v1") != BP.order(list("abcdefgh"), "v2")


def test_fill_budget_skips_long_dialogue(monkeypatch):
    monkeypatch.setattr(BP, "BUDGET", PIN.est_tokens(BP.render("hotel", ["x" * 300])) + 5)
    texts = {"a": "x" * 300, "big": "y" * 5000, "c": "z" * 100}
    chosen, text = BP.fill("hotel", ["a", "big", "c"], texts, "v0")
    assert "big" not in chosen and chosen[0] == "a"
    assert PIN.est_tokens(text) <= BP.BUDGET
    assert text.startswith("Below are dialogues") and "hotel" in text and "[dialogue 1]" in text


def test_entity_ids_and_job_row():
    services = {"a": ["train", "taxi"], "b": ["hotel"], "c": ["train"]}
    assert BP.entity_ids(["c", "a", "b"], services, "train") == ["c", "a"]
    j = BP.job_row("hotel", "dev50b", "v2", 5, 123)
    assert j["job"] == "baseline_hotel_dev50b_v2" and j["family"] == "baseline" and j["entity"] == "E0"
    assert j["format"] == "baseline" and j["max_tokens"] == 4096 and j["prompt"].startswith("baseline/prompts/")


def test_prompt_has_no_dataset_name():
    t = BP.render("train", ["User: a"]).lower()
    assert "multiwoz" not in t and "cluster" not in t and "train journey" in t


def test_parse_baseline():
    ok = '{"attributes": [{"name": "a", "description": "b"}]}'
    obj, errs = LC.parse_baseline(ok)
    assert not errs and len(obj["attributes"]) == 1
    assert LC.parse_job(ok, "baseline", {})[2] == 1
    assert LC.parse_baseline('{"attributes": [{"name": 1}]}')[1]
    assert LC.parse_baseline("no json")[1]


# ---- T11
def test_candidate_slot():
    assert BL.candidate_slot("arrival_time", "when the train gets there", SLOTS)[0] == "Train arrive by"
    attr, ov = BL.candidate_slot("destination_station", "", SLOTS)
    assert attr == "Train destination" and ov > 0
    assert BL.candidate_slot("xyzzy", "", SLOTS)[1] == 0


def _lists():
    return {("dev50", "train", "v0"): [{"name": "arrival_time", "description": "arrives"},
                                       {"name": "phone_number", "description": "phone"}],
            ("dev50", "train", "v1"): [{"name": "Arrival Time", "description": "when"},
                                       {"name": "arrival-time", "description": "dup"}]}


def test_lists_and_sheet_blind():
    raw = {("dev50", "train", "v0"): json.dumps({"attributes": [{"name": "A_b", "description": "x"},
                                                                 {"name": "a b", "description": "dup"}]}),
           ("dev50", "train", "v1"): "garbage"}
    lists, notes = BL.attribute_lists(raw)
    assert [a["name"] for a in lists[("dev50", "train", "v0")]] == ["A_b"] and len(notes) == 1
    rater, key = BL.rating_sheet(_lists(), {"train": SLOTS})
    assert len(rater) == len(key) == 4   # one row per listed name (attribute_lists dedups, the sheet does not)
    assert list(rater.columns) == ["row", "ent", "group_name", "group_description", "top_values", "l2_attr", "l2_slot",
                                   "l2_slot_description"]
    assert "set" not in rater.columns and "version" not in rater.columns
    assert set(key["row"]) == set(rater["row"])


def test_read_ratings_lower_wins():
    a = pd.DataFrame({"row": [0, 1], "label": ["right", "partly"]})
    b = pd.DataFrame({"row": [0, 1], "label": ["partly", "partly"]})
    assert BL.read_ratings([a, b]) == {"0": "partly", "1": "partly"}
    with pytest.raises(ValueError):
        BL.read_ratings([pd.DataFrame({"row": [0], "label": ["ok"]})])


def test_supported():
    kinds, turns = BL.dialogue_kinds_turns(["User: my phone is 01223123456", "System: the train leaves at noon"])
    assert "phone" in kinds
    assert BL.supported("phone_number", "Train day", "wrong", set(), turns, kinds)       # typed value
    assert BL.supported("train_leaves", "Train day", "wrong", set(), turns, kinds)       # all words in one turn
    assert not BL.supported("loyalty_points", "Train day", "wrong", set(), turns, kinds)
    assert BL.supported("x", "Train day", "right", {"Train day"}, turns, kinds)
    assert not BL.supported("x", "Train day", "right", set(), turns, kinds)


def test_score_rows_and_table():
    rater, key = BL.rating_sheet(_lists(), {"train": SLOTS})
    labels = {}
    for r in key.itertuples():
        labels[str(r.row)] = "right" if "arriv" in r.name.lower() else "wrong"
    kinds, turns = BL.dialogue_kinds_turns(["User: arrive soon"])
    sc = BL.score_rows(key, labels, {"train": list(SLOTS)}, {("dev50", "train"): {"Train arrive by"}},
                       {("dev50", "train"): (kinds, turns)})
    v0 = sc[(sc["version"] == "v0")].iloc[0]
    assert (v0["right"], v0["base_n"], v0["columns"]) == (1, 3, 2)
    assert v0["no_support"] == 1                       # phone_number: no phone value
    un = sc[sc["version"] == "union"].iloc[0]
    assert un["columns"] == 2 and un["right"] == 1 and un["unrated"] == 0   # arrival_time / Arrival Time / arrival-time merge
    tot, md = BL.table(sc)
    assert "1/3 (0.333)" in md and set(tot["version"]) == {"v0", "v1", "union"}


def test_unrated_rows_counted():
    _, key = BL.rating_sheet(_lists(), {"train": SLOTS})
    kinds, turns = BL.dialogue_kinds_turns(["User: x"])
    sc = BL.score_rows(key, {}, {"train": list(SLOTS)}, {("dev50", "train"): set()}, {("dev50", "train"): (kinds, turns)})
    assert sc["right"].sum() == 0 and sc[sc["version"] == "v0"]["unrated"].iloc[0] == 2


def test_a_reference():
    df = pd.DataFrame({"setting": ["default"] * 2, "level": ["2"] * 2, "ent": ["train", "hotel"], "variant": ["A r1"] * 2,
                       "name_right_l2rated": ["3", "4"], "name_base_l2rated": ["10", "14"], "found_n": ["5", "6"],
                       "gold_n": ["10", "14"]})
    r = BL.a_reference(df, ("A r1", "A r2"), "default").iloc[0]
    assert (r["right"], r["base_n"], r["found"], r["gold_n"]) == (7, 24, 11, 24)
