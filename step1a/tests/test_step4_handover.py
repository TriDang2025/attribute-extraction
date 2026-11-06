import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_handover as H  # noqa: E402


def col(i, name="c"):
    return {"id": i, "name": name, "description": "", "n_mentions": 3, "n_dialogues": 2, "value_type": {"dominant": "text"}, "top_values": []}


HAND = {"train": {"columns": [col(1), col(2), col(3)]}, "hotel": {"columns": [col(1)]}}


def canon(extra=None):
    cols = [{"name": "a", "type": "text", "source": "train:1", "new": False, "gt": None},
            {"name": "id", "type": "id", "source": None, "new": True, "gt": None}]
    return {"tables": [{"name": "t", "description": "", "row": "", "columns": cols + (extra or []), "primary_key": ["id"], "foreign_keys": []}],
            "relationships": [], "unused": [{"source": "train:2", "reason": "noise"}, {"source": "hotel:1", "reason": "noise"}],
            "duplicate_flags": []}


def test_build_links_every_column():
    s = H.build(canon(), HAND, "dev50", "a_dev50_s0")
    t = s["tables"][0]
    assert t["columns"][0]["step3"]["id"] == 1 and t["columns"][1]["step3"] is None
    assert s["unused"][0]["step3"]["entity"] == "train"
    assert s["source_to_table"] == {"train:1": "t", "train:2": None, "train:3": None, "hotel:1": None}


def test_check_and_unknown_source():
    s = H.build(canon(), HAND, "dev50", "r")
    assert H.check(s, HAND) == ["train:3 is neither in a table nor unused"]
    s["unused"].append({"source": "train:3", "reason": ""})
    assert H.check(s, HAND) == []
    with pytest.raises(ValueError):
        H.build(canon([{"name": "z", "type": "text", "source": "train:9", "new": False, "gt": None}]), HAND, "dev50", "r")
