import numpy as np
import pandas as pd

from s1a import noise_cases_v38 as NC
from s1a import v34_data as VD


def men(rows):
    return pd.DataFrame(rows, columns=["mention_id", "text", "dialogue_id", "speaker", "turn_text"])


def test_mention_kind():
    assert NC.mention_kind("noise", True) == "choice"
    assert NC.mention_kind("noise", False) == "no_l2_label"
    assert NC.mention_kind("request", False) == "request"
    assert NC.mention_kind("Hotel area", False) == "labelled"


def test_in_question():
    assert NC.in_question("Fine. What day would you like?", "What day")
    assert not NC.in_question("The day is Monday. Anything else?", "Monday")
    assert not NC.in_question("hello", "absent")
    assert NC.in_question("book a room?", "room")


def test_mark_context_cuts_long_turns():
    out = NC.mark_context("x" * 200 + " target " + "y" * 200, "target", width=60)
    assert "[[target]]" in out and len(out) < 70 and out.startswith("...")
    assert NC.mark_context("a target b", "target") == "a [[target]] b"


def test_examples_of_distinct_texts():
    m = men([[2, "Room", "d1", "user", "a room"], [1, "room", "d2", "system", "the room"], [3, "city", "d3", "user", "in city"]])
    ex = NC.examples_of(m, k=3)
    assert [e[0] for e in ex] == ["room", "city"]


def test_cluster_proxies():
    m = men([[1, "What day", "d1", "system", "What day are you?"], [2, "what day", "d2", "user", "what day is it"],
             [3, "15 minutes", "d2", "system", "for 15 minutes."]])
    p = NC.cluster_proxies(m)
    assert p["n"] == 3 and p["n_dialogues"] == 2 and p["n_distinct"] == 2
    assert p["top_type"] == "text" and abs(p["type_share"] - 2 / 3) < 1e-9 and p["n_types"] == 2
    assert abs(p["share_system"] - 2 / 3) < 1e-9
    assert abs(p["share_question"] - 1 / 3) < 1e-9


def test_nearest_other():
    cent = {"a": [1, 0], "b": [0.9, 0.1], "c": [0, 1]}
    cid, sim = NC.nearest_other(cent, "a", {"b", "c", "a"})
    assert cid == "b" and sim > 0.99
    cid, sim = NC.nearest_other(cent, "a", {"a"})
    assert cid == "" and np.isnan(sim)


def test_guess_checks():
    good = {"n": 6, "n_dialogues": 4, "n_distinct": 4, "type_share": 1.0, "share_question": 0.0}
    assert NC.guess_checks(good, 0.5) == {"example_flag": False, "neighbour_fit": False, "counting_flag": False}
    assert not NC.any_check(NC.guess_checks(good, float("nan")))
    small = dict(good, n=2, n_dialogues=1, n_distinct=1)
    g = NC.guess_checks(small, 0.9)
    assert g["counting_flag"] and g["neighbour_fit"] and NC.any_check(g)
    assert NC.guess_checks(dict(good, share_question=0.8), 0.0)["example_flag"]
    assert NC.guess_checks(dict(good, type_share=0.5), 0.0)["example_flag"]


def vo(dec_rows, attr_rows):
    dec = pd.DataFrame(dec_rows, columns=["cluster_id", "action", "name"])
    attrs = pd.DataFrame(attr_rows, columns=["name", "clusters", "status"])
    return VD.VariantOut(dec, attrs, {}, {})


def test_where_it_went_and_group():
    v = vo([["E0#1", "merge", "price"], ["E0#2", "merge", "price"], ["E0#3", "not_attribute", ""]],
           [["price", "E0#1;E0#2", "keep"]])
    assert NC.where_it_went(v, "E0#1") == ("merge", "price", 2)
    assert NC.where_it_went(v, "E0#3") == ("not_attribute", "", 0)
    assert NC.where_it_went(v, "E0#9") == ("-", "", 0)
    assert NC._group_clusters(v, "E0#2") == ["E0#1", "E0#2"] and NC._group_clusters(v, "E0#3") == ["E0#3"]
    assert NC.order_text("merge", "price", 2) == "merge 'price' (2 clusters)"
    assert NC.order_text("not_attribute", "", 0) == "not_attribute"


def test_reason_code():
    rc = NC.reason_code
    assert rc(NC.NOISE_CAUGHT, 3, "noise", "", 3, ["hotel"], "choice") == "caught_all_orders"
    assert rc(NC.NOISE_CAUGHT, 1, "noise", "", 3, ["hotel"], "choice") == "caught_by_vote"
    assert rc(NC.NOISE_MISSED, 0, "noise", "", 3, ["hotel"], "choice") == "kept_all_orders:choice"
    assert rc(NC.NOISE_MISSED, 2, "noise", "", 3, ["hotel"], "no_l2_label") == "vote_lost_mark:no_l2_label"
    assert rc(NC.MARKED_NOT_NOISE, 3, "real", "Attraction name", 1, ["hotel"], "") == "real_other_domain"
    assert rc(NC.MARKED_NOT_NOISE, 3, "real", "Hotel name", 1, ["hotel"], "") == "real_tiny"
    assert rc(NC.MARKED_NOT_NOISE, 3, "real", "Hotel name", 5, ["hotel"], "") == "real_marked"
    assert rc(NC.MARKED_NOT_NOISE, 3, "mixed", "", 5, ["hotel"], "", 0.8) == "request_phrases"
    assert rc(NC.MARKED_NOT_NOISE, 3, "mixed", "", 5, ["hotel"], "", 0.1) == "mixed_cluster"


def test_summaries():
    base = {"main_kind": "", "reason_code": "", "label": "noise", "example_flag": False, "neighbour_fit": False,
            "counting_flag": False, "guess_catch": None, "guess_rescue": None}
    rows = [dict(base, case_type=NC.NOISE_CAUGHT),
            dict(base, case_type=NC.NOISE_MISSED, main_kind="choice", reason_code="kept_all_orders:choice", counting_flag=True,
                 guess_catch=True),
            dict(base, case_type=NC.MARKED_NOT_NOISE, label="real", guess_rescue=False)]
    cases = pd.DataFrame(rows)
    g = NC.guess_summary(cases)
    assert g["missed"] == 1 and g["catch_any"] == 1 and g["catch_counting"] == 1 and g["fp"] == 1 and g["rescue"] == 0
    line = NC.summary_line("x", cases, 2)
    assert "noise caught 1/2" in line and "marks 2 = 1 noise + 1 real" in line and "catch 1/1" in line
