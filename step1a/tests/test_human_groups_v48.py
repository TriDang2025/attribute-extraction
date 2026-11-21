import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import human_groups_v48 as H  # noqa: E402


def row(i, real, same_as="", name_match=""):
    return {"id": str(i), "real": real, "same_as": same_as, "name_match": name_match}


def test_parse_same_as():
    assert H.parse_same_as("") == (set(), False, False)
    assert H.parse_same_as("14") == ({14}, False, False)
    assert H.parse_same_as("20; loop-1 cuisine column") == ({20}, True, False)
    assert H.parse_same_as("mix of 8 + 22") == (set(), False, True)
    with pytest.raises(ValueError):
        H.parse_same_as("maybe 3")


def test_groups_and_summary():
    rows = [row(1, "yes", name_match="Restaurant postcode"), row(2, "yes", "3"), row(3, "yes", "2"), row(4, "no"),
            row(5, "yes", "mix of 2 + 3"), row(6, "yes", "7; loop-1 cuisine column"), row(7, "yes", "6"), row(8, "yes", "99")]
    assert H.groups(rows) == [{"ids": [1], "kind": "new"}, {"ids": [2, 3], "kind": "new"}, {"ids": [5], "kind": "mix"},
                              {"ids": [6, 7], "kind": "loop1_repeat"}, {"ids": [8], "kind": "new"}]   # 99: not in rows, ignored
    s = H.summary(rows)
    assert s == {"rows": 8, "real_rows": 7, "new_groups": 3, "new_not_gold": 2, "loop1_repeat_groups": 1, "mix": 1, "repeat_rows": 5}
