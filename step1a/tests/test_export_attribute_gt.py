"""Toy tests for the pure functions of scripts/export_attribute_gt.py."""

import sys
from collections import Counter

import pandas as pd

from s1a import paths

sys.path.insert(0, str(paths.ROOT / "scripts"))
import export_attribute_gt as EX  # noqa: E402


def test_split_and_counts():
    assert EX.split_labels("A;B") == ["A", "B"] and EX.split_labels("") == []
    df = pd.DataFrame({"gt_L3": ["A", "A;B", "", "B"], "speaker": ["user", "system", "user", "system"]})
    c = EX.attr_counts(df)
    assert c["A"] == Counter(user=1, system=1) and c["B"] == Counter(system=2) and "" not in c


def test_majority_and_top_values():
    assert EX.majority(["a", "b", "a"]) == ("a", 2, 3) and EX.majority([]) == ("", 0, 0)
    assert EX.top_values(["x", "y", "x", "", "z"], 2) == [("x", 2), ("y", 1)]


def test_level_and_partner():
    assert EX.level_of("Train day", {"Train day"}, "train-day") == "L1"
    assert EX.level_of("Train price", {"Train day"}, "train-price") == "L2"
    assert EX.level_of("Restaurant signature", set(), "") == "L3"
    pairs = [{"slots": ["departure", "destination"], "entities": ["train", "taxi"]}]
    assert EX.role_partner("Train departure", pairs) == "Train destination"
    assert EX.role_partner("Hotel area", pairs) == ""


def test_format_and_table():
    b = EX.format_block({"name": "Train day", "fields": [("level", "L1"), ("value type", "text")]})
    assert b.splitlines() == ["Train day", "  level      : L1", "  value type : text"]
    assert EX.fmt_counts(Counter(user=2)) == "user 2, system 0 (total 2)"
    assert EX.md_rows("| a | b |\n|---|---|\n| x | 1 |\n") == [["x", "1"]]
