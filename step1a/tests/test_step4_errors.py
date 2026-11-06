import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_errors as E  # noqa: E402
from s1a import step4_gt as G  # noqa: E402

from test_step4_score import gt  # noqa: E402,F401  (fixture)


def errs(schema, gt, full=None):
    return E.list_errors(schema, gt, "dev50", {}, full or {})


def kinds(r):
    return [e["kind"] for e in r["errors"]]


def test_gt_has_no_errors(gt):
    r = errs(G.to_canonical(gt), gt)
    assert r["design"] == "main" and r["errors"] == []


def test_planted_errors_are_listed_with_step(gt):
    c = G.to_canonical(gt)
    by = {t["name"]: t for t in c["tables"]}
    col = by["hotel"]["columns"].pop(0)                      # a hotel column moves to the train table
    by["train"]["columns"].append(col)
    by["hotel_booking"]["foreign_keys"] = []                 # FK removed; relationship stays
    by["restaurant"]["primary_key"] = []                     # no primary key
    c["relationships"] = [r for r in c["relationships"] if not (r["from"] == "train_booking" and r["to"] == "train")]
    by["train_booking"]["foreign_keys"] = []                 # link removed completely
    r = errs(c, gt)
    got = {(e["step"], e["kind"]) for e in r["errors"]}
    assert ("4.1", "column in wrong table") in got
    assert ("4.3", "missing link") in got
    assert ("4.4", "missing primary key") in got
    assert ("4.4", "missing foreign key") in got
    assert all(e["step3"] == "no" for e in r["errors"])


def test_wrong_direction_type_and_extra_link(gt):
    c = G.to_canonical(gt)
    for rel in c["relationships"]:
        if rel["from"] == "hotel_booking":
            rel["from"], rel["to"] = rel["to"], rel["from"]
    by = {t["name"]: t for t in c["tables"]}
    by["hotel_booking"]["foreign_keys"] = []
    by["hotel"]["foreign_keys"] = [{"columns": ["Hotel name"], "ref_table": "hotel_booking", "ref_columns": ["Hotel booking id"]}]
    by["hotel"]["columns"][5]["type"] = "time"
    c["relationships"].append({"from": "hotel", "to": "restaurant", "kind": "one_to_many", "reason": ""})
    k = kinds(errs(c, gt))
    assert "wrong direction" in k and "wrong type" in k and "extra link" in k


def test_unused_duplicate_and_noise(gt):
    c = G.to_canonical(gt)
    by = {t["name"]: t for t in c["tables"]}
    gone = by["train"]["columns"].pop(0)                     # a real column becomes unused
    c["unused"].append({"source": "train:1", "reason": ""})
    c["tables"][0]["columns"].append({"name": "x", "type": "text", "source": "train:2", "new": False, "gt": None})
    r = E.list_errors(c, gt, "dev50", {"train:1": {"gt": gone["name"], "purity": 1.0, "n": 5, "entity": "train"},
                                       "train:2": {"gt": None, "purity": 0.0, "n": 5, "entity": "train"}},
                      {"train:1": {"gt": gone["name"], "purity": 1.0, "n": 5, "entity": "train"},
                       "train:2": {"gt": None, "purity": 0.0, "n": 5, "entity": "train"}})
    byk = {e["kind"]: e for e in r["errors"]}
    assert byk["real column unused"]["step3"] == "no" and byk["noise column placed"]["step3"] == "yes"


def test_step3_status():
    full = {"train:1": {"gt": "Train leave at", "purity": 0.9, "n": 10, "entity": "train"},
            "train:2": {"gt": "Train leave at", "purity": 0.9, "n": 4, "entity": "train"},
            "train:3": {"gt": None, "purity": 0.9, "n": 4, "entity": "train"},
            "train:4": {"gt": "Hotel name", "purity": 0.9, "n": 4, "entity": "train"},
            "train:5": {"gt": "Train price", "purity": 0.5, "n": 4, "entity": "train"}}
    bad = E.step3_status(full, {"Train leave at": "train", "Hotel name": "hotel", "Train price": "train"})
    assert set(bad) == {"train:2", "train:3", "train:4", "train:5"}
    assert "duplicate of train:1" in bad["train:2"] and "another entity" in bad["train:4"] and "purity" in bad["train:5"]


def test_count_table():
    es = [{"step": "4.1", "step3": "yes"}, {"step": "4.1", "step3": "no"}, {"step": "4.4", "step3": "no"}]
    t = E.count_table(es)
    assert t["4.1"] == {"yes": 1, "no": 1, "all": 2} and t["all"]["all"] == 3 and t["4.3"]["all"] == 0
