import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import rules_labels as RL  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import v34_data as D  # noqa: E402
from s1a.score_rules import Rules  # noqa: E402

GT_COLS = ["mention_id", "gt_L1", "gt_L2", "gt_L3", "ent_L1", "ent_L2", "ent_L3", "is_request", "request_slot",
           "is_choice"]


def gt_levels(rows):
    """rows: (mention_id, L1, L2, L3, ent, is_request, is_choice); the entity follows the first word of the attr."""
    out = []
    for i, a1, a2, a3, req, ch in rows:
        e = [a.split()[0].lower() if a else "" for a in (a1, a2, a3)]
        out.append([str(i), a1, a2, a3, *e, req, "", ch])
    return pd.DataFrame(out, columns=GT_COLS)


# E1#0: stations (L1 gold); E1#1: train ids (no L1, L2 "Train trainid"); E1#2: "which day" (cue / request) + a choice
MEN = pd.DataFrame({
    "mention_id": ["0", "1", "2", "3", "4", "5"], "cluster_id": ["E1#0", "E1#0", "E1#1", "E1#1", "E1#2", "E1#2"],
    "entity": "E1", "gold_attr": ["Train departure", "Train departure", "", "", "", ""],
    "entity_gold": ["train", "train", "", "", "", ""],
    "norm_value": ["cambridge", "london", "tr1234", "tr5678", "which day", "5 options"],
    "text": ["Cambridge", "London", "TR1234", "TR5678", "which day", "5 options"]})
GT = gt_levels([(0, "Train departure", "Train departure", "Train departure", False, False),
                (1, "Train departure", "Train departure", "Train departure", False, False),
                (2, "", "Train trainid", "Train trainid", False, False),
                (3, "", "Train trainid", "Train trainid", False, False),
                (4, "", "", "", True, False), (5, "", "", "", False, True)])
GT["is_request"] = GT["is_request"].astype(bool)
GT["is_choice"] = GT["is_choice"].astype(bool)


def toy_ed(variants=None):
    ctx = SimpleNamespace(mentions=MEN.assign(entity=["E1"] * 6), entity="E1", train=["Train departure", "Train arrive by"],
                          pm=None, cluster_gold={}, entity_gold_of={})
    pm = MEN
    return D.EntityData("train", "E1", ["train"], ["E1#0", "E1#1", "E1#2"], pm,
                        pd.DataFrame({"cluster_id": ["E1#0"], "label": ["gold"]}), ctx, ctx, variants or {}, {}, {})


def test_with_level_labels_and_train():
    ed = toy_ed()
    l1, l2 = (D.with_level({"train": ed}, GT, k)["train"] for k in (1, 2))
    assert list(l1.mentions["gold_attr"]) == list(MEN["gold_attr"]) and l1.level == 1
    assert list(l1.ctx_r.train) == ["Train departure", "Train arrive by"]  # L1 keeps ctx.train
    assert list(l2.mentions["gold_attr"]) == ["Train departure"] * 2 + ["Train trainid"] * 2 + ["", ""]
    assert list(l2.mentions["entity_gold"]) == ["train"] * 4 + ["", ""]
    assert list(l2.ctx_r.train) == ["Train departure", "Train arrive by", "Train trainid"]  # L1 attrs stay (arrive by has
    # no dev50 mention), plus the new one that occurs
    l3 = D.with_level({"train": ed}, GT, 3)["train"]
    assert set(l2.ctx_r.train) <= set(l3.ctx_r.train) and set(l1.ctx_r.train) <= set(l2.ctx_r.train)  # cumulative
    assert list(l2.mentions["is_choice"]) == [False] * 5 + [True] and l2.mentions["is_request"].iloc[4]
    assert l2.mentions_l1 is ed.mentions and list(ed.mentions["gold_attr"][2:4]) == ["", ""]  # original untouched
    assert set(l2.ctx_r.entity_gold_of.values()) == {"train"} and l2.ctx_r.cluster_gold["E1#1"] == "train"
    with pytest.raises(ValueError):
        D.with_level({"train": ed}, GT, 4)


def test_choice_is_noise_at_every_level():
    for k in (1, 2, 3):
        led = D.with_level({"train": toy_ed()}, GT, k)["train"]
        cls = RL.mention_class(led, Rules.parse("old"), {})
        assert cls[5] == "noise" and cls[4] == "unlabeled"  # a choice mention; "which day" stays unlabeled under old
    assert RL.mention_class(toy_ed(), Rules.parse("old"), {})[5] == "unlabeled"  # no level copy: unchanged


def test_cue_scores():
    dec = pd.DataFrame({"cluster_id": ["E1#0", "E1#1", "E1#2"], "action": ["keep", "attribute_cue", "attribute_cue"]})
    ed = toy_ed({"E s012": SimpleNamespace(dec=dec)})
    r = RL.cue_scores(ed, "E s012", GT)
    # E1#1 has no request mention; E1#2: one of two mentions is a request (50%)
    assert r == {"cue_n": 2, "cue_request": 1, "cue_share": 0.5}
    none = RL.cue_scores(ed, "E s012", GT.assign(is_request=False))
    assert none["cue_request"] == 0
    dec0 = dec.assign(action="keep")
    r0 = RL.cue_scores(toy_ed({"A r1": SimpleNamespace(dec=dec0)}), "A r1", GT)
    assert r0["cue_n"] == 0 and pd.isna(r0["cue_share"])


def test_names_valid_extra_counts_right_at_level():
    attrs = pd.DataFrame([["E1#0", "departure", "d", "E1#0", "keep", "keep"],
                          ["E1#1", "train_id", "d", "E1#1", "keep", "keep"]],
                         columns=["attr_id", "name", "description", "clusters", "source", "status"])
    vo = SimpleNamespace(attrs=attrs, assign={0: "E1#0", 1: "E1#0", 2: "E1#1", 3: "E1#1"}, dec=None)
    ed = toy_ed({"A r1": vo})
    rated = pd.DataFrame([["train", "departure", "d", "Train departure", "right"],
                          ["train", "train_id", "d", "", "valid_extra"]],
                         columns=["ent", "name", "description", "majority_gold_attr", "label"])
    extra = {"names_rated": rated}
    l1 = RN.name_scores(ed, "A r1", Rules.parse("default"), extra)
    assert (l1["name_right"], l1["name_base"], l1["valid_extra"], l1["names_unrated"]) == (1, 2, 1, 0)
    l2ed = D.with_level({"train": ed}, GT, 2)["train"]
    l2 = RN.name_scores(l2ed, "A r1", Rules.parse("default"), extra)
    # base = departure + arrive by (L1, no mention) + trainid; the valid_extra group (majority "Train trainid", no L1
    # mention) is right for it
    assert (l2["name_right"], l2["name_base"], l2["valid_extra"], l2["names_unrated"]) == (2, 3, 1, 0)
    l1lev = RN.name_scores(D.with_level({"train": ed}, GT, 1)["train"], "A r1", Rules.parse("default"), extra)
    assert l1lev["name_right"] == 1  # L1: the rating is not stretched


def test_level_entity_switch():
    ed = toy_ed()
    assert SR.level_entity(ed, Rules.parse("default"), {}) is ed  # no gt_levels table
    assert SR.level_entity(ed, Rules.parse("old"), {"gt_levels": GT}) is ed
    led = SR.level_entity(ed, Rules.parse("default,gt=L2"), {"gt_levels": GT})
    assert led.level == 2 and led is not ed
