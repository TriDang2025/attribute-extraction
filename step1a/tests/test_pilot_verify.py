import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import pilot_verify as PV  # noqa: E402

# (cluster, entity, entity_gold, vector, norm_value)
ROWS = [("E1#0", "E1", "train", [1, 0, 0], "monday"), ("E1#0", "E1", "train", [1, 0, 0], "tuesday"),
        ("E1#1", "E1", "train", [1, 0, 0], "monday"), ("E1#1", "E1", "train", [1, 0, 0], "friday"),
        ("E1#2", "E1", "train", [1, 0, 0], "sunday"), ("E1#2", "E1", "train", [1, 0, 0], "monday"),
        ("E1#3", "E1", "train", [1, 0, 0], "10:00"), ("E1#3", "E1", "train", [0.9, 0.1, 0], "11:00"),
        ("E1#3", "E1", "train", [0, 1, 0], "5 people"), ("E1#3", "E1", "train", [0.1, 0.9, 0], "6 people"),
        ("E1#4", "E1", "train", [0, 0, 1], "ok"),
        ("E2#0", "E2", "hotel", [0, 0, 1], "cheap"), ("E2#0", "E2", "hotel", [0, 0, 1], "cheap")]


def toy():
    m = pd.DataFrame({"mention_id": range(len(ROWS)), "dialogue_id": "d1", "cluster_id": [r[0] for r in ROWS],
                      "entity": [r[1] for r in ROWS], "entity_gold": [r[2] for r in ROWS],
                      "norm_value": [r[4] for r in ROWS], "gold_attr": ""})
    x = np.array([r[3] for r in ROWS], float)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    ex = pd.DataFrame({"ex_id": ["E1#3:0", "E1#3:1"], "cluster_id": "E1#3", "mention_id": [6, 8]})
    return m, np.arange(len(ROWS)), x, ex


def dec_of(*objs):
    return PV.decisions_table(list(objs), ["E1#0", "E1#1", "E1#2", "E1#3", "E1#4"], "full", "r1")


def test_response_key_and_load_last_row(tmp_path):
    p = tmp_path / "responses_nocontext_r1.jsonl"
    p.write_text(json.dumps({"parsed": [{"cluster_id": "E1#0"}]}) + "\n" +
                 json.dumps({"parsed": None, "raw": '[{"cluster_id": "E1#1"}]'}) + "\n", encoding="utf-8")
    assert PV.response_key(p) == ("nocontext", "r1")
    assert [o["cluster_id"] for o in PV.load_objects(p)] == ["E1#1"]  # a rerun's row replaces the earlier one


def test_decisions_unknown_action_and_missing():
    d = dec_of({"cluster_id": "E1#0", "name": "day", "action": "bogus"}, {"cluster_id": "E1#1", "action": "keep"})
    assert d.set_index("cluster_id")["action"].to_dict() == {"E1#0": "unsure", "E1#1": "keep", "E1#2": "",
                                                              "E1#3": "", "E1#4": ""}


def test_merge_transitive_split_nearest_centroid_and_marked():
    m, ids, x, ex = toy()
    d = dec_of({"cluster_id": "E1#0", "name": "day", "action": "merge", "merge_with": ["E1#1", "E2#0"]},
               {"cluster_id": "E1#1", "name": "weekday", "action": "merge", "merge_with": ["E1#2"]},
               {"cluster_id": "E1#2", "name": "d", "action": "keep"},
               {"cluster_id": "E1#3", "name": "mixed", "action": "split",
                "split": [{"name": "time", "examples": ["E1#3:0"]}, {"name": "people", "examples": ["E1#3:1"]}]},
               {"cluster_id": "E1#4", "name": "junk", "action": "not_attribute"})
    assign, attrs, parts = PV.final_attributes(d, m, ids, x, ex, "E1")
    a = attrs.set_index("attr_id")
    assert a.loc["E1#0|E1#1|E1#2", ["n_mentions", "status", "source", "name"]].tolist() == [6, "keep", "merge", "day"]
    assert a.loc["E1#4", "status"] == "not_attribute" and a.loc["E1#4", "n_mentions"] == 1
    assert assign[10] == "E1#4"  # marked, not deleted
    assert {i: assign[i] for i in (6, 7, 8, 9)} == {6: "E1#3/0", 7: "E1#3/0", 8: "E1#3/1", 9: "E1#3/1"}
    assert a.loc["E1#3/1", "name"] == "people" and parts["E1#3"] == [("time", ["E1#3:0"]), ("people", ["E1#3:1"])]
    assert 11 not in assign and 12 not in assign  # other entity untouched
    assert PV.relabel(m, assign)["cluster_id"].tolist()[:3] == ["E1#0|E1#1|E1#2"] * 3


def test_split_with_one_usable_part_stays_whole():
    m, ids, x, ex = toy()
    d = dec_of({"cluster_id": "E1#3", "name": "x", "action": "split",
                "split": [{"name": "a", "examples": ["E1#3:0"]}, {"name": "b", "examples": ["nope"]}]})
    assign, attrs, parts = PV.final_attributes(d, m, ids, x, ex, "E1")
    assert parts == {} and assign[6] == assign[8] == "E1#3"
    assert attrs.set_index("attr_id").loc["E1#0", "status"] == "missing"


class Fake:
    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, name, doc, windows):
        self.calls.append(name)
        return self.table.get(name, [])


def test_verify_jaccard_unverified_and_cache(tmp_path):
    m, ids, x, ex = toy()
    text = "User: leave monday or friday\nSystem: ok\nUser: later"
    spans = [(0, 28), (29, 38), (39, 52)]
    docs = {"d1": SimpleNamespace(doc_id="d1", text=text, spans=spans)}
    inst = pd.DataFrame({"instance_id": ["d1|0"], "entity": ["E1"], "dialogue_id": ["d1"],
                         "start_turn": [0], "end_turn": [1]})
    attrs = pd.DataFrame({"attr_id": ["E1#0", "E1#1", "E1#4"], "name": ["day", "weekday", ""], "clusters": "",
                          "n_mentions": 2, "status": "keep", "source": "keep"})
    assign = {0: "E1#0", 1: "E1#0", 2: "E1#1", 3: "E1#1"}   # E1#0 = {monday, tuesday}, E1#1 = {monday, friday}
    fake = Fake({"day": ["Monday", "friday"], "weekday": ["10:00"]})
    v = PV.verify(attrs, assign, m, docs, inst, "E1", fake, tmp_path / "g", "full", "r1").set_index("attr_id")
    assert v.loc["E1#0", "jaccard"] == pytest.approx(1 / 3) and not v.loc["E1#0", "unverified"]
    assert v.loc["E1#1", "jaccard"] == 0.0 and v.loc["E1#1", "unverified"]
    assert "E1#4" not in v.index and sorted(fake.calls) == ["day", "weekday"]
    PV.verify(attrs, assign, m, docs, inst, "E1", fake, tmp_path / "g")
    assert len(fake.calls) == 2  # cached per name


def test_verify_only_pilot_turns(tmp_path):
    seen = []
    docs = {"d1": SimpleNamespace(doc_id="d1", text="User: a b\nSystem: c d", spans=[(0, 9), (10, 21)])}
    inst = pd.DataFrame({"instance_id": ["i"], "entity": ["E1"], "dialogue_id": ["d1"], "start_turn": [1], "end_turn": [1]})
    PV.span_values("x", docs, PV.pilot_turns(inst, "E1"), lambda n, d, w: seen.append(w) or [])
    assert seen == [[(18, 21)]]


# ---------------------------------------------------------------- wf_v3.1: v2 adapter, split results, description label
V2 = {"attributes": [{"name": "day", "description": "day of the trip", "role": "x"},
                     {"name": "Leave_Time", "description": "when it leaves", "role": "y"},
                     {"name": "people", "description": "party size", "role": "z"}],
      "clusters": [{"cluster_id": "E1#0", "attribute": "day", "evidence": "e0", "mixed": False, "placement": "current entity E1"},
                   {"cluster_id": "E1#1", "attribute": "Day", "mixed": False, "placement": "current entity E1"},
                   {"cluster_id": "E1#2", "attribute": "bogus_name", "mixed": False, "placement": ""},
                   {"cluster_id": "E1#3", "attribute": "leave time", "mixed": True, "placement": "p"},
                   {"cluster_id": "E1#4", "attribute": "not_attribute", "mixed": False, "placement": ""}]}
SPLIT = {"E1#3": {"cluster_id": "E1#3", "is_mixed": True,
                  "parts": [{"name": "leave_time", "role": "r", "examples": ["E1#3:s0"]},
                            {"name": "party_size", "role": "r", "examples": ["E1#3:s1"]}]}}
CIDS = ["E1#0", "E1#1", "E1#2", "E1#3", "E1#4"]


def test_decisions_from_v2_shared_not_attribute_unknown_and_split():
    d = PV.decisions_from_v2(V2, CIDS + ["E1#9"], "v2", "r1", SPLIT).set_index("cluster_id")
    assert list(PV.decisions_from_v2(V2, CIDS, "v2", "r1").columns) == PV.DEC_COLS
    assert d["action"].to_dict() == {"E1#0": "merge", "E1#1": "merge", "E1#2": "unsure", "E1#3": "split",
                                     "E1#4": "not_attribute", "E1#9": ""}
    assert json.loads(d.at["E1#0", "merge_with"]) == ["E1#1"] and json.loads(d.at["E1#1", "merge_with"]) == ["E1#0"]
    assert (d.at["E1#0", "name"], d.at["E1#0", "description"], d.at["E1#0", "evidence"]) == ("day", "day of the trip", "e0")
    assert d.at["E1#2", "name"] == d.at["E1#4", "name"] == ""  # no name on unsure / not_attribute rows
    assert json.loads(d.at["E1#3", "split"]) == [{"name": "leave_time", "examples": ["E1#3:s0"]},
                                                 {"name": "party_size", "examples": ["E1#3:s1"]}]
    assert d.at["E1#3", "name"] == "Leave_Time" and d.at["E1#3", "placement"] == "p"


def test_decisions_from_v2_split_needs_mixed_and_is_mixed():
    no_split = {"E1#3": {"is_mixed": False, "parts": SPLIT["E1#3"]["parts"]}}
    assert PV.decisions_from_v2(V2, CIDS, "v2", "r1", no_split).set_index("cluster_id").at["E1#3", "action"] == "keep"
    unmixed = {"attributes": V2["attributes"], "clusters": [{**V2["clusters"][3], "mixed": False}]}
    assert PV.decisions_from_v2(unmixed, ["E1#3"], "v2", "r1", SPLIT).at[0, "action"] == "keep"
    assert PV.decisions_from_v2(unmixed, ["E1#3"], "v2", "r1", SPLIT, require_mixed=False).at[0, "action"] == "split"
    assert PV.decisions_from_v2(None, ["E1#0"], "v2", "r1").at[0, "action"] == ""  # unparsed response


def test_v2_split_examples_reach_final_attributes():
    m, ids, x, ex = toy()
    ex = pd.concat([ex, pd.DataFrame({"ex_id": ["E1#3:s0", "E1#3:s1"], "cluster_id": "E1#3", "mention_id": [7, 9]})],
                   ignore_index=True)  # normal and split ex ids in one table
    d = PV.decisions_from_v2(V2, CIDS, "v2", "r1", SPLIT)
    assign, attrs, parts = PV.final_attributes(d, m, ids, x, ex, "E1")
    assert parts == {"E1#3": [("leave_time", ["E1#3:s0"]), ("party_size", ["E1#3:s1"])]}
    assert {i: assign[i] for i in (6, 7, 8, 9)} == {6: "E1#3/0", 7: "E1#3/0", 8: "E1#3/1", 9: "E1#3/1"}
    a = attrs.set_index("attr_id")
    assert a.loc["E1#0|E1#1", "source"] == "merge" and a.loc["E1#0|E1#1", "description"] == "day of the trip"
    assert a.loc["E1#2", "status"] == "unsure" and a.loc["E1#4", "status"] == "not_attribute"
    other = ex.assign(cluster_id="E1#0", ex_id=ex["ex_id"].str.replace("E1#3", "E1#0"))  # ids of another cluster's
    assert PV.final_attributes(d, m, ids, x, other, "E1")[0].get(6) == "E1#3"  # examples: the split is not applied


def test_load_split_results(tmp_path):
    (tmp_path / "train_split_E1-1_r1.jsonl").write_text(json.dumps({"parsed": {"cluster_id": "E1#1", "is_mixed": False}}) + "\n" +
                                                         json.dumps({"parsed": {"cluster_id": "E1#1", "is_mixed": True}}) + "\n")
    (tmp_path / "train_split_E1-3_r1.jsonl").write_text(json.dumps({"parsed": None, "raw": '{"cluster_id": "E1#3"}'}) + "\n")
    (tmp_path / "hotel_split_E0-4_r2.jsonl").write_text(json.dumps({"parsed": {"is_mixed": False}}) + "\n")
    (tmp_path / "train_v2_r1.jsonl").write_text("{}\n")  # not a split file
    got = PV.load_split_results(tmp_path)
    assert sorted(got) == [("hotel", "r2"), ("train", "r1")]
    assert got[("train", "r1")]["E1#1"]["is_mixed"] is True and got[("train", "r1")]["E1#3"] == {"cluster_id": "E1#3"}


def test_verify_description_label_kind(tmp_path):
    m, ids, x, ex = toy()
    docs = {"d1": SimpleNamespace(doc_id="d1", text="User: leave monday or friday\nSystem: ok", spans=[(0, 28), (29, 38)])}
    inst = pd.DataFrame({"instance_id": ["d1|0"], "entity": ["E1"], "dialogue_id": ["d1"], "start_turn": [0], "end_turn": [1]})
    long_desc = "the day of the week on which the passenger wants to travel by train " * 2
    attrs = pd.DataFrame({"attr_id": ["E1#0", "E1#1", "E1#2"], "name": ["day", "weekday", "x"], "clusters": "",
                          "n_mentions": 2, "status": "keep", "source": "keep",
                          "description": [long_desc, "weekday words", ""]})
    assign = {0: "E1#0", 1: "E1#0", 2: "E1#1", 3: "E1#1"}
    fake = Fake({long_desc.strip()[:60].strip(): ["monday"], "weekday words": ["friday"], "day": ["monday"]})
    d = PV.verify(attrs, assign, m, docs, inst, "E1", fake, None, "v2", "r1", use_description=True)
    assert list(d.columns) == PV.VERIFY_COLS + ["label_kind"] and set(d["label_kind"]) == {"description"}
    assert sorted(fake.calls) == sorted([long_desc.strip()[:60].strip(), "weekday words"])  # trimmed; no description: skipped
    assert d.set_index("attr_id").loc["E1#1", "jaccard"] == pytest.approx(0.5)  # {friday} vs {monday, friday}
    n = PV.verify(attrs, assign, m, docs, inst, "E1", fake, None)
    assert list(n.columns) == PV.VERIFY_COLS and len(n) == 3 and "day" in fake.calls  # default: the name


def test_v2_failed_split_falls_back_to_its_attribute():
    bad = {"E1#3": {"cluster_id": "E1#3", "is_mixed": True,
                    "parts": [{"name": "a", "role": "r", "examples": ["E1#3:s0"]},
                              {"name": "b", "role": "r", "examples": []}]}}  # second part has no own example
    obj = {"attributes": V2["attributes"],
           "clusters": [dict(c, attribute="leave time") if c["cluster_id"] in ("E1#0", "E1#3") else c
                        for c in V2["clusters"]]}
    d = PV.decisions_from_v2(obj, CIDS, "v2", "r1", bad, require_mixed=False).set_index("cluster_id")
    assert d.at["E1#3", "action"] == "merge" and "E1#0" in d.at["E1#3", "merge_with"]
