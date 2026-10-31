import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import checks_v35 as CK  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from s1a.score_rules import Rules  # noqa: E402

RULES = Rules(unlabeled="exclude", noise_kind="pattern", cluster_label="0.6")


def dec(rows):
    return pd.DataFrame(rows, columns=["cluster_id", "action"])


def test_noise_vote_2of3():
    seeds = {"C s0": dec([("c1", "not_attribute"), ("c2", "keep"), ("c3", "unsure")]),
             "C s1": dec([("c1", "attribute_cue"), ("c2", "keep"), ("c3", "keep")]),
             "C s2": dec([("c1", "keep"), ("c2", "unsure"), ("c3", "keep")])}
    v = CK.noise_vote_2of3(seeds)
    assert v.to_dict() == {"c1": True, "c2": False, "c3": False}
    assert CK.noise_vote_2of3(seeds, need=1).to_dict() == {"c1": True, "c2": True, "c3": True}


def test_value_type_v35_fixes():
    for t in ("8.08GBP", "37.79 GPB", "66 GBP", "5 pounds", "£3.50"):
        assert CK.value_type_v35(t) == "price", t
    for t in ("28-minute", "105 minutes", "2 hours", "45 mins"):
        assert CK.value_type_v35(t) == "duration", t
    assert CK.value_type_v35("17:45") == "time" and CK.value_type_v35("monday") == "day"
    assert CK.value_type_v35("3") == "number" and CK.value_type_v35("the hotel") == "text"


def test_value_type_changes_pairs():
    m = pd.DataFrame({"ent": ["train"] * 6, "cluster_id": ["a", "a", "b", "b", "c", "c"],
                      "text": ["8.08GBP", "37.79 GPB", "66 GBP", "12 GBP", "28-minute", "105 minutes"]})
    cl, s = CK.value_type_changes(m)
    # old types: a text, b price, c number; new: a price, b price, c duration
    assert dict(zip(cl["cluster_id"], cl["type_new"])) == {"a": "price", "b": "price", "c": "duration"}
    assert s["mentions_changed"] == 4 and s["pairs"] == 3
    assert s["pairs_gained"] == 1 and s["pairs_lost"] == 0  # a-b: differ -> agree


SPEC = [("c1", "Train departure", "train", "Cambridge")] * 4 + [("c2", "", "", "8 GBP")] * 3 +        [("c3", "", "", "the cheap one")] * 3 + [("c4", "", "", "x")] * 2


def toy_ed(spec=None, train=("Train departure",)):
    # default: c1 = gold A (4), c2 = extra price (3, no L1 gold), c3 = noise-like values (3), c4 = L3-only (2)
    spec = spec or SPEC
    m = pd.DataFrame({"mention_id": range(len(spec)), "cluster_id": [s[0] for s in spec], "entity": "E1",
                      "gold_attr": [s[1] for s in spec], "entity_gold": [s[2] for s in spec],
                      "text": [s[3] for s in spec], "norm_value": [s[3].lower() for s in spec],
                      "dialogue_id": [f"d{i % 2}" for i in range(len(spec))], "turn_text": "ok"})
    cids = list(dict.fromkeys(s[0] for s in spec))
    assign = {i: s[0] for i, s in enumerate(spec)}
    attrs = pd.DataFrame({"attr_id": cids + ["c9"], "name": cids + ["q"], "status": ["keep"] * len(cids) + ["not_attribute"]})
    d = pd.DataFrame({"cluster_id": cids, "action": ["keep"] * len(cids), "placement": [""] * len(cids)})
    vo = SimpleNamespace(assign=assign, attrs=attrs, dec=d)
    seed = {f"C s{i}": d for i in range(3)}
    labels = pd.DataFrame({"cluster_id": cids, "label": ["other"] * len(cids)})
    ctx = SimpleNamespace(mentions=m, entity="E1", train=list(train), pm=m, cluster_gold={}, entity_gold_of={})
    return VD.EntityData("train", "E1", ["train"], cids, m, labels, ctx, ctx, {"C s012": vo}, {}, seed)


def toy_levels(n=12):
    lv = pd.DataFrame({"mention_id": range(n), "gt_L1": [""] * n, "gt_L2": [""] * n, "gt_L3": [""] * n,
                       "ent_L1": [""] * n, "ent_L2": [""] * n, "ent_L3": [""] * n, "is_request": False,
                       "is_choice": False})
    lv.loc[:3, ["gt_L1", "gt_L2", "gt_L3"]] = "Train departure"
    lv.loc[4:6, ["gt_L2", "gt_L3"]] = "Train price"
    lv.loc[10:11, "gt_L3"] = "Train trainid"
    return lv


def test_attr_counts():
    ed = toy_ed()
    ac = CK.attr_counts(ed, "C s012").set_index("attr_id")
    assert list(ac.index) == ["c1", "c2", "c3", "c4"]  # the not_attribute attr has no mentions and is skipped
    assert ac.loc["c2", "types"] == "price:3" and bool(ac.loc["c2", "one_type"])
    assert ac.loc["c1", "n_distinct"] == 1 and ac.loc["c1", "variety"] == 0.25 and ac.loc["c1", "n_dialogues"] == 2


def test_extras_by_level_kinds():
    ed = toy_ed()
    ex = CK.extras_by_level(ed, "C s012", toy_levels(), RULES, {}).set_index("attr_id")
    assert ex["kind"].to_dict() == {"c1": "gt_found", "c2": "extra_L2", "c3": "wrong_extra", "c4": "extra_L3"}
    assert (ex.loc["c2", "majority_L1"], ex.loc["c2", "majority_L2"]) == ("", "Train price")
    assert ex.loc["c4", "majority_L3"] == "Train trainid" and ex.loc["c4", "majority_L2"] == ""


def test_extras_table_counts_distinct_once_per_entity():
    rows = pd.DataFrame({"ent": ["train", "train", "hotel", "train"], "variant": ["v"] * 4,
                         "attr_id": ["a", "b", "c", "d"], "name": ["p1", "p2", "p3", "z"],
                         "majority_L1": [""] * 4, "majority_L2": ["Train price", "Train price", "Train price", ""],
                         "majority_L3": [""] * 4, "kind": ["extra_L2", "extra_L2", "extra_L2", "extra_none"]})
    t = CK.extras_table(rows)
    assert t.loc["v", "extra_L2"] == 2 and t.loc["v", "extra_none"] == 1 and t.loc["v", "total"] == 3


def test_noise_vote_scores_levels():
    ed = toy_ed()
    # c3 is noise-like (pattern: general phrase). Orders: c3 marked in 2 of 3; C s012 marks c3 and c2.
    ed.seed_decs = {"C s0": dec([("c3", "not_attribute"), ("c2", "keep")]),
                    "C s1": dec([("c3", "unsure"), ("c2", "keep")]),
                    "C s2": dec([("c3", "keep"), ("c2", "unsure")])}
    ed.variants["C s012"].dec = dec([("c1", "keep"), ("c2", "not_attribute"), ("c3", "not_attribute")])
    s = CK.noise_vote_scores(ed, RULES, {}, toy_levels()).set_index(["level", "method"])
    cur, vote = s.loc[(1, "C s012")], s.loc[(1, "2of3")]
    assert (cur["noise_n"], cur["noise_marked"], cur["marked_n"], cur["precision"]) == (1, 1, 2, 0.5)
    assert (vote["noise_marked"], vote["marked_n"], vote["precision"]) == (1, 1, 1.0)
    assert {1, 2, 3} == set(s.index.get_level_values("level"))
    assert s.loc[(1, "2of3")]["marked_noise"] == 1


def test_extras_majority_leaves_unlabeled_out_and_found_marks_gt_found():
    # like "Hotel stars": 2 labelled mentions + 3 unlabeled ones in one group: purity 1.0 over counted, so found and majority
    spec = [("c1", "Train departure", "train", "Alpha")] * 2 + [("c1", "", "", "Beta")] * 3 +            [("c2", "Train stars", "train", "Gamma")] * 4
    ed = toy_ed(spec, train=("Train departure", "Train stars"))
    lv = toy_levels(len(spec))
    lv.loc[:1, ["gt_L1", "gt_L2", "gt_L3"]] = "Train departure"
    lv.loc[5:8, ["gt_L1", "gt_L2", "gt_L3"]] = "Train stars"
    ex = CK.extras_by_level(ed, "C s012", lv, RULES, {}).set_index("attr_id")
    assert ex.loc["c1", "majority_L1"] == "Train departure"  # 2 of 2 counted, not 2 of 5
    assert ex.loc["c1", "kind"] == "gt_found" and ex.loc["c2", "kind"] == "gt_found"
    # the count matches the Q5 found rows
    from s1a import rules_groups as RG
    f = RG.found(CK.SR.level_entity(ed, CK.replace(RULES, gt="L1"), {"gt_levels": lv}), "C s012", RULES, {})
    assert set(ex.index[ex["kind"] == "gt_found"]) == set(f.loc[f["found"], "best_group"])


def test_at_level_one_marks_choice_as_noise():
    lv = toy_levels()
    lv.loc[8, "is_choice"] = True
    led = CK.at_level(toy_ed(), lv, 1)
    assert led.level == 1 and bool(led.mentions["is_choice"].iloc[8])
