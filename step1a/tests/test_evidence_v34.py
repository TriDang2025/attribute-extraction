import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import v34_data as V  # noqa: E402
from chk.data import Doc  # noqa: E402

TEXT = "User: I need a train\nSystem: Leaves at 10:00\n  User :  Thanks,   bye"
SPANS = [(0, 20), (21, 44), (45, len(TEXT))]
DOC = Doc("D1", TEXT, SPANS, [], [])


def _vo(rows, assign):
    dec = pd.DataFrame(rows, columns=["cluster_id", "name", "action", "placement"])
    return V.VariantOut(dec, pd.DataFrame(), assign, {})


def _data():
    m = pd.DataFrame({"mention_id": [5, 6], "dialogue_id": ["D1", "D1"], "turn": [1, 2], "text": ["10:00", "bye"],
                      "norm_value": ["10:00", "bye"], "left_word": ["at", "thanks"], "cluster_id": ["E1#0", "E1#1"],
                      "gold_attr": ["Train leave at", ""], "entity_gold": ["train", ""]})
    m = V._with_context(m, {"D1": DOC})
    labels = pd.DataFrame({"cluster_id": ["E1#0", "E1#1"], "label": ["gold", "noise"]})
    vo = _vo([["E1#0", "leave_at", "keep", "current entity E1"], ["E1#1", "", "keep", "current entity E1"]],
             {5: "E1#0", 6: "E1#1"})
    return {"train": V.EntityData("train", "E1", ["train"], ["E1#0", "E1#1"], m, labels, None, None,
                                  {k: vo for k in V.VARIANTS}, {}, {})}


def test_turn_context():
    assert V.turn_context(DOC, 0) == ("user", "I need a train", "")
    assert V.turn_context(DOC, 1) == ("system", "Leaves at 10:00", "user: I need a train")
    assert V.turn_context(DOC, 2) == ("user", "Thanks, bye", "system: Leaves at 10:00")


def test_evidence_columns_and_rows():
    ev = V.evidence_table(_data())
    expected = list(V.BASE_COLS)
    for k in V.VARIANTS:
        expected += [f"{k.replace(' ', '_')}_{f}" for f in V.VARIANT_FIELDS]
    assert list(ev.columns) == expected
    assert "C_s012_group" in ev.columns and ev.shape[0] == 2
    r = ev.iloc[0]
    assert (r["speaker"], r["turn_text"], r["prev_turn"]) == ("system", "Leaves at 10:00", "user: I need a train")
    assert (r["gold_attr"], r["old_label"], r["A_r1_group"], r["D_s012_place"]) == (
        "Train leave at", "gold", "E1#0", "current entity E1")
    assert ev.iloc[1]["gold_attr"] == "none" and ev.iloc[1]["old_label"] == "noise"
