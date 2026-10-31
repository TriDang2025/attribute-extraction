import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import gt_ext as GT  # noqa: E402

DLG = {"dialogue_id": "X1.json", "turns": [
    {"speaker": "USER", "turn_id": "0", "utterance": "I need a train to Ely at 10:30",
     "frames": [{"service": "train", "state": {"active_intent": "find_train"},
                 "slots": [{"slot": "train-leaveat", "start": 25, "exclusive_end": 30, "value": "10:30"}]},
                {"service": "taxi", "state": {"active_intent": "NONE"},
                 "slots": [{"slot": "taxi-leaveat", "start": 25, "exclusive_end": 30, "value": "10:30"}]}]},
    {"speaker": "SYSTEM", "turn_id": "1", "utterance": "There are 5 trains. What day?",
     "frames": [{"service": "train", "slots": [{"slot": "train-day", "start": 0, "exclusive_end": 1, "value": "x"},
                                                {"slot": "train-copy", "value": "y"}]}]}]}
ACTS = {"0": {"dialog_act": {"Train-Inform": [["destination", "Ely"], ["leaveat", "10:30"]]},
              "span_info": [["Train-Inform", "destination", "ely", 17, 20], ["Train-Inform", "leaveat", "10:30", 25, 30]]},
        "1": {"dialog_act": {"Train-Inform": [["choice", "5"]], "Train-Request": [["day", "?"]]},
              "span_info": [["Train-Inform", "choice", "5", 10, 11]]}}


def spans():
    return GT.span_table([DLG], {"X1.json": ACTS})


def test_spans_dedup_and_request():
    s = spans()
    u = s[(s.turn == 0)]
    assert sorted(u.slot) == ["destination", "leaveat"]  # taxi frame skipped (NONE), slot + act_span once
    assert u[u.slot == "leaveat"].source.iloc[0] == "slot"
    assert u[u.slot == "destination"].source.iloc[0] == "act_span"
    req = s[s.act == "request"]
    assert len(req) == 1 and req.slot.iloc[0] == "day" and pd.isna(req.char_start.iloc[0]) and req.source.iloc[0] == "request"
    assert (s.dialogue_id == "X1").all() and "copy" not in set(s.slot)


def mention(mid, turn, start, text, **kw):
    r = {"mention_id": mid, "dialogue_id": "X1", "turn": turn, "char_start": start, "char_end": start + len(text), "text": text,
         "norm_value": text.lower(), "context": "", "entity": "E1", "gold_attr": "", "entity_gold": ""}
    r.update(kw)
    return r


def test_match_exact_fuzzy_and_choice():
    s = spans()
    utt = {("X1", 0): "I need a train to Ely at 10:30", ("X1", 1): "There are 5 trains.  What day?"}
    mw = {("X1", 0): DLG["turns"][0]["utterance"], ("X1", 1): DLG["turns"][1]["utterance"]}
    ms = pd.DataFrame([mention(0, 0, 25, "10:30"), mention(1, 0, 17, "Ely"), mention(2, 1, 10, "5"), mention(3, 0, 0, "I need")])
    r = GT.match(ms, s, utt, mw).set_index("mention_id")
    assert list(r.loc[[0, 1], "match"]) == ["span", "span"] and r.loc[0, "mw_slot"] == "leaveat" and r.loc[0, "mw_act"] == "inform"
    assert r.loc[2, "text_match"] == "exact" and r.loc[2, "mw_slot"] == "choice"
    assert r.loc[3, "match"] == "none"
    assert r.loc[2, "request_slots"] == "train-day"
    utt2 = {("X1", 0): "I really need a train to Ely at 10:30", ("X1", 1): "x"}  # fuzzy: offsets shift by 7
    r = GT.match(pd.DataFrame([mention(0, 0, 32, "10:30"), mention(1, 1, 0, "x")]), s, utt2, mw).set_index("mention_id")
    assert r.loc[0, "text_match"] == "fuzzy" and r.loc[0, "mw_turn"] == 0 and r.loc[0, "mw_slot"] == "leaveat"
    assert r.loc[1, "text_match"] == "none"


def test_match_value_fallback():
    s = spans()
    utt = {("X1", 0): "I need a train to Ely at 10:30"}
    r = GT.match(pd.DataFrame([mention(0, 0, 0, "Ely")]), s, utt, {("X1", 0): utt[("X1", 0)]})
    assert r.loc[0, "match"] == "value" and r.loc[0, "mw_slot"] == "destination"


def test_match_span_inside_mention():
    utt = "It costs 8.08 pounds for 7 people"
    sp = pd.DataFrame([
        {"dialogue_id": "X1", "turn": 0, "speaker": "system", "utterance": utt, "char_start": 9, "char_end": 13,
         "value": "8.08", "domain": "train", "slot": "price", "act": "inform", "source": "act_span"},
        {"dialogue_id": "X1", "turn": 0, "speaker": "system", "utterance": utt, "char_start": 26, "char_end": 27,
         "value": "7", "domain": "train", "slot": "bookpeople", "act": "inform", "source": "slot"}])
    ms = pd.DataFrame([mention(0, 0, 9, "8.08 pounds"), mention(1, 0, 26, "7 people"), mention(2, 0, 9, "costs 8.08 pounds")])
    r = GT.match(ms, sp, {("X1", 0): utt}, {("X1", 0): utt}).set_index("mention_id")
    assert (r.loc[0, "match"], r.loc[0, "mw_slot"]) == ("span", "price")
    assert (r.loc[1, "match"], r.loc[1, "mw_slot"]) == ("span", "bookpeople")
    assert r.loc[2, "match"] == "span"  # the old rule (>= 50% overlap) does not apply: 4 of 17 characters
    far = pd.DataFrame([mention(3, 0, 0, "It costs 8.08 pounds for 7 people")])
    assert GT.match(far, sp, {("X1", 0): utt}, {("X1", 0): utt}).loc[0, "match"] == "span"  # both inside: the larger overlap


DB = {"train": [{"id": str(i), "departure": "cambridge", "leaveAt": f"1{i}:00", "trainID": f"TR{i}"} for i in range(10)],
      "hotel": [], "restaurant": []}


def test_levels():
    ms = pd.DataFrame([
        mention(0, 0, 25, "10:30", gold_attr="Train leave at", entity_gold="train"),
        mention(1, 0, 17, "Ely"),  # L2 via span
        mention(2, 1, 10, "5"),  # choice
        mention(3, 0, 0, "TR3"),  # L3 via DB
        mention(4, 0, 1, "cambridge"),  # too common
        mention(5, 1, 14, "What day", context="What day?")])
    tear = {"Train leave at": "train-leaveat", "_notes": "x"}
    matched = pd.DataFrame([
        {"mention_id": 0, "match": "span", "mw_domain": "train", "mw_slot": "leaveat", "request_slots": ""},
        {"mention_id": 1, "match": "span", "mw_domain": "train", "mw_slot": "destination", "request_slots": ""},
        {"mention_id": 2, "match": "span", "mw_domain": "train", "mw_slot": "choice", "request_slots": "train-day"},
        {"mention_id": 3, "match": "none", "mw_domain": "", "mw_slot": "", "request_slots": ""},
        {"mention_id": 4, "match": "none", "mw_domain": "", "mw_slot": "", "request_slots": ""},
        {"mention_id": 5, "match": "none", "mw_domain": "", "mw_slot": "", "request_slots": "train-day;taxi-leaveat"}])
    lv = GT.levels(ms, matched, tear, DB, schema={"train-leaveat", "train-destination"}).set_index("mention_id")
    assert (lv.loc[0, "gt_L1"], lv.loc[0, "gt_L2"]) == ("Train leave at", "Train leave at")
    assert (lv.loc[1, "gt_L1"], lv.loc[1, "gt_L2"], lv.loc[1, "ent_L2"]) == ("", "Train destination", "train")
    assert lv.loc[2, "is_choice"] and lv.loc[2, "gt_L2"] == "" and lv.loc[2, "gt_L3"] == ""
    assert lv.loc[3, "gt_L2"] == "" and lv.loc[3, "gt_L3"] == "Train trainid" and lv.loc[3, "ent_L3"] == "train"
    assert lv.loc[4, "gt_L3"] == ""
    assert lv.loc[5, "is_request"] and lv.loc[5, "request_slot"] == "train-day" and not lv.loc[1, "is_request"]


def test_coverage():
    ms = pd.DataFrame({"mention_id": [0, 1, 2], "entity": ["E1", "E1", "E0"], "speaker": ["user", "user", "system"],
                       "cluster_id": ["E1#0", "E1#0", "E0#0"], "norm_value": ["a", "b", "c"]})
    lv = pd.DataFrame({"mention_id": [0, 1, 2], "gt_L1": ["x", "", ""], "gt_L2": ["x", "y", ""], "gt_L3": ["x", "y", ""]})
    old = {"q2": pd.DataFrame({"cluster_id": ["E1#0", "E0#0"], "label_0.6": ["unknown", "unknown"]}),
           "q1": pd.DataFrame({"cluster_id": ["E1#0"], "norm_value": ["b"], "n": [1], "kind": ["other"]})}
    table, extra = GT.coverage(ms, lv, old)
    row = table[(table.entity == "train") & (table.speaker == "user")].iloc[0]
    assert row.L1 == "1/2 (0.500)" and row.L2 == "2/2 (1.000)"
    assert extra["unknown_clusters"] == 2 and extra["unknown_L2_any"] == 1 and extra["other_L2_any"] == 1 and extra["other_L1_any"] == 0


def test_levels_booking_request_and_l3_names():
    db = {"train": [{"id": str(i), "leaveAt": f"1{i}:00", "price": "5 pounds" if i < 2 else f"{i} pounds"}
                    for i in range(10)],
          "hotel": [{"id": str(i), "pricerange": "cheap" if i < 2 else "moderate", "stars": str(i)} for i in range(10)],
          "restaurant": []}
    ms = pd.DataFrame([mention(0, 1, 0, "What day", entity="E0"), mention(1, 1, 0, "how many days", entity="E0"),
                       mention(2, 0, 0, "cheap", entity="E0"), mention(3, 0, 0, "12:00", entity="E1"),
                       mention(4, 0, 0, "3 pounds", entity="E1"), mention(5, 0, 0, "What day", entity="E1")])
    none = {"match": "none", "mw_domain": "", "mw_slot": ""}
    matched = pd.DataFrame([{"mention_id": i, **none, "request_slots": rs} for i, rs in
                            enumerate(["booking-day", "booking-stay", "", "", "", "booking-day"])])
    tear = {"Hotel price range": "hotel-pricerange", "Train leave at": "train-leaveat", "_notes": "x"}
    lv = GT.levels(ms, matched, tear, db).set_index("mention_id")
    assert lv.loc[0, "is_request"] and lv.loc[0, "request_slot"] == "hotel-day"
    assert lv.loc[1, "is_request"] and lv.loc[1, "request_slot"] == "hotel-stay"
    assert lv.loc[5, "request_slot"] == "train-day"  # the cluster's domain, whatever the booking was for
    assert lv.loc[2, "gt_L3"] == "Hotel price range"  # through tear_map, no "Hotel pricerange" duplicate
    assert lv.loc[3, "gt_L3"] == "Train leave at" and lv.loc[4, "gt_L3"] == "Train price"
    assert GT.column_name("hotel", "pricerange", {}) == "Hotel price range"
    assert GT.column_name("train", "arriveBy", {}) == "Train arrive by" and GT.column_name("train", "trainID", {}) == "Train trainid"
