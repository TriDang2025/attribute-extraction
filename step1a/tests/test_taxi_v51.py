import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / "scripts")]

from s1a import mainclaim_v41 as MC  # noqa: E402
from s1a import taxi_v51 as T  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

GT = pd.DataFrame({"gt_L2": ["Restaurant food", "Taxi phone", "Taxi leave at", "Train day", "Hotel name"],
                   "ent_L2": ["restaurant", "taxi", "taxi", "train", "hotel"]})


def test_gold_lists_switch_off_keeps_taxi_under_restaurant():
    off = MC.gold_lists(GT, [])
    assert off["restaurant"] == ["Restaurant food", "Taxi leave at", "Taxi phone"] and "taxi" not in off


def test_gold_lists_taxi_own_entity_same_attributes_and_restore():
    off = MC.gold_lists(GT, [])
    with T.taxi_scoring(True):
        on = MC.gold_lists(GT, [])
        assert MC.DOMAIN_ENTITY["taxi"] == "taxi"
    assert on["taxi"] == ["Taxi leave at", "Taxi phone"] and on["restaurant"] == ["Restaurant food"]
    assert T.moved_attrs(off, on) == {"Taxi leave at": ("restaurant", "taxi"), "Taxi phone": ("restaurant", "taxi")}
    assert MC.DOMAIN_ENTITY["taxi"] == "restaurant" and VD.GOLD_ENTS["restaurant"] == ["restaurant", "taxi"] and "taxi" not in VD.GOLD_ENTS
    assert MC.ENTITIES == ("train", "hotel", "restaurant")
    assert MC.gold_lists(GT, []) == off


def test_switch_off_changes_nothing():
    with T.taxi_scoring(False):
        assert MC.gold_lists(GT, [])["restaurant"][-1] == "Taxi phone" and "taxi" not in MC.gold_lists(GT, [])


def test_restore_after_error():
    with pytest.raises(RuntimeError), T.taxi_scoring(True):
        raise RuntimeError
    assert MC.DOMAIN_ENTITY["taxi"] == "restaurant" and VD.GOLD_ENTS["restaurant"] == ["restaurant", "taxi"]


def test_moved_attrs_fails_on_different_gold():
    with pytest.raises(ValueError):
        T.moved_attrs({"a": ["X"]}, {"a": ["Y"]})
    assert T.moved_attrs({"a": ["X"]}, {"a": ["X"]}) == {}


def test_adjust_conservative():
    assert T.adjust({"A", "B"}, {"A", "C"}, {"C", "D"}) == {"B", "D"}
    assert T.adjust({"A"}, {"X"}, {"X"}) == {"A"}


@pytest.fixture(scope="module")
def r0():
    import r0_taxi_v51 as R
    return R


def test_found_l2_rule_off_reproduces_v50(r0):
    # wf_v5.0: found L2 with human check 34/40 | 30/41 (context split big40)
    assert [len(r0.found_l2(r0.final_v50(s), s, False)) for s in r0.SETS] == [34, 30]


def test_found_l2_taxi_rule_moves_only_taxi(r0, tmp_path):
    for s in r0.SETS:
        off, on = r0.found_l2(r0.final_v50(s), s, False), r0.found_l2(r0.final_v50(s), s, True, tmp_path)
        assert {a for a in off ^ on if not a.startswith("Taxi")} == set()
        assert off != on
