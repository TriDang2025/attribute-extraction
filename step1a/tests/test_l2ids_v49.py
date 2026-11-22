import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import l2ids_v49 as L  # noqa: E402
from s1a import gt_ext as GE  # noqa: E402
from s1a import step4_gt as G  # noqa: E402

MERGED = {"accommodation": [
    {"cid": 1, "name": "area", "source": "loop1", "mention_ids": [0, 1]},
    {"cid": 2, "name": "internet", "source": "loop2", "clusters": ["L2_accommodation#1", "L2_accommodation#2"], "mention_ids": [10, 11, 12]},
    {"cid": 3, "name": "parking", "source": "loop2", "clusters": ["L2_accommodation#3"], "mention_ids": [13]}]}


def test_columns_and_ids():
    cols = L.loop2_columns(MERGED)
    assert list(cols) == ["accommodation:2", "accommodation:3"]
    assert L.column_ids(cols) == {"accommodation:2": ["L2_10", "L2_11", "L2_12"], "accommodation:3": ["L2_13"]}


def test_extend_series_and_map_handover(tmp_path):
    cols = L.loop2_columns(MERGED)
    gt_l2 = pd.Series(["Hotel area", "Hotel area"], index=[0, 1], name="gt_L2")
    lev = L.extend(gt_l2, {10: ["Hotel name"], 11: ["Hotel name"], 12: []}, cols)
    assert list(lev.index) == [0, 1, "L2_10", "L2_11", "L2_12", "L2_13"]
    assert list(lev.iloc[2:]) == ["Hotel name", "Hotel name", "", ""]
    (tmp_path / "s").mkdir()
    doc = {"columns": [{"id": "1", "mention_ids": [0, 1]}, {"id": "2", "mention_ids": L.column_ids(cols)["accommodation:2"]},
                       {"id": "3", "mention_ids": ["L2_13", 99]}]}
    (tmp_path / "s" / "accommodation.json").write_text(json.dumps(doc), encoding="utf-8")
    m = G.map_handover(tmp_path, "s", lev)
    assert m["accommodation:2"]["gt"] == "Hotel name" and m["accommodation:2"]["n"] == 3
    assert m["accommodation:3"]["gt"] is None and m["accommodation:3"]["n"] == 1   # empty label, id 99 unknown
    assert m["accommodation:1"]["gt"] == "Hotel area"


def test_fallback_and_apply():
    cols = L.loop2_columns(MERGED)
    key = [{"source": "loop2", "item_id": "L2_accommodation#1", "name_match": "hotel internet"},
           {"source": "loop2", "item_id": "L2_accommodation#2", "name_match": "Hotel internet"},
           {"source": "loop2", "item_id": "L2_accommodation#3", "name_match": ""},
           {"source": "loop1", "item_id": "L2_accommodation#3", "name_match": "Hotel parking"}]
    over = L.fallback(cols, key, {"hotel internet": "Hotel internet"})
    assert over == {"accommodation:2": "Hotel internet"}
    mapping = {"accommodation:2": {"gt": None, "purity": 0.0, "n": 3, "entity": "accommodation"},
               "accommodation:3": {"gt": None, "purity": 0.0, "n": 1, "entity": "accommodation"},
               "accommodation:1": {"gt": "Hotel area", "purity": 1.0, "n": 2, "entity": "accommodation"}}
    out = L.apply_fallback(mapping, {**over, "accommodation:1": "Hotel name"})
    assert out["accommodation:2"]["gt"] == "Hotel internet" and out["accommodation:2"]["purity"] == 1.0
    assert out["accommodation:3"]["gt"] is None
    assert out["accommodation:1"]["gt"] == "Hotel area"     # a span label is never replaced
    assert mapping["accommodation:2"]["gt"] is None         # input untouched


def test_loop2_labels(tmp_path):
    ms = [{"mention_id": 10, "dialogue_id": "MUL0001", "turn": 3, "text": "Free Wifi", "norm_value": "free wifi"},
          {"mention_id": 11, "dialogue_id": "MUL0001", "turn": 4, "text": "cheap", "norm_value": "cheap"}]
    clusters = [{"id": "L2_accommodation#1", "entity": "accommodation", "keep": True, "name": "internet", "mentions": ms}]
    p = tmp_path / "clusters.json"
    p.write_text(json.dumps(clusters), encoding="utf-8")
    known = {(GE.dialogue_key("MUL0001"), 3, "free wifi"): ["Hotel internet"]}
    assert L.loop2_labels(p, {"accommodation": "hotel"}, known, None, {}) == {10: ["Hotel internet"], 11: []}
