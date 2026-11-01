import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import names_l2 as NL  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import rules_labels as RL  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import v34_data as D  # noqa: E402
from s1a.score_rules import Rules  # noqa: E402
from test_v35_levels import GT, MEN, toy_ed  # noqa: E402


# ---- task 13

@pytest.mark.parametrize("text,kind", [
    ("15:45", "time"), ("7pm", "time"), ("£12.50", "price"), ("TR9016", "ref code"), ("cb11ln", "postcode"),
    ("01223 249955", "phone"), ("7", "number"), ("15 minutes", "number"), ("Friday", "day"), ("okay thanks", "yes/no/ok/thanks"),
    ("book", "booking word"), ("Both", "choice word"), ("another part of town", "choice word"),
    ("What day", "request word"), ("how many seats", "request word"), ("their phone number", "request word"),
    ("the restaurant", "pronoun/generic noun"), ("venue", "pronoun/generic noun"), ("your destination", "pronoun/generic noun"),
    ("Cambridge", "other"), ("moderate price range", "other")])
def test_unmatched_kind(text, kind):
    assert NV.unmatched_kind(text) == kind


def test_mark_value():
    assert NV.mark_value("Is the cb11ln ok?", "CB11LN") == "Is the [[cb11ln]] ok?"
    assert NV.mark_value("Hello", "x") == "Hello [[x]]"


def test_unmatched_table_summary_sheet():
    men = pd.DataFrame({"mention_id": [0, 1, 2, 3], "dialogue_id": ["D1"] * 4, "turn": [0, 0, 1, 1],
                        "text": ["What day", "what day", "Cambridge", "7"]})
    matched = pd.DataFrame({"mention_id": [0, 1, 2, 3], "match": ["none", "none", "none", "span"]})
    df = NV.unmatched_table(men, matched, lambda d, t: ("user", f"turn {t}: What day or Cambridge"))
    assert list(df["kind"]) == ["request word", "request word", "other"]
    s = NV.unmatched_summary(df).set_index("kind")
    assert s.loc["request word", "n"] == 2 and s.loc["other", "n"] == 1 and s.loc["time", "n"] == 0
    assert s.loc["request word", "share"] == pytest.approx(2 / 3)
    assert "[[What day]]" in s.loc["request word", "example_1"] and s.loc["time", "example_1"] == ""
    sheet = NV.other_sheet(df)
    assert list(sheet["mention_id"]) == [2] and list(sheet["row"]) == [0] and "[[Cambridge]]" in sheet["turn_marked"][0]


# ---- task 14

def test_mwoz_classes_and_labels():
    led = D.with_level({"train": toy_ed()}, GT, 2)["train"]
    cls = RL.mention_class(led, NV.mwoz_rules(2), {})
    assert list(cls) == ["Train departure"] * 2 + ["Train trainid"] * 2 + ["request", "noise"]
    cl = RL.cluster_labels(led, NV.mwoz_rules(2), {}).set_index("cluster_id")
    assert list(cl["label"]) == ["real", "real", "mixed"]  # request counted, neither real nor noise: 1 noise of 2
    nr = D.with_level({"train": toy_ed()}, GT.assign(is_request=False), 2)["train"]
    assert RL.cluster_labels(nr, NV.mwoz_rules(2), {}).set_index("cluster_id").loc["E1#2", "label"] == "noise"
    # choice beats a label; a label beats noise
    both = D.with_level({"train": toy_ed()}, GT.assign(is_choice=[True, False, False, False, False, True]), 2)["train"]
    assert RL.mention_class(both, NV.mwoz_rules(2), {})[0] == "noise"
    with pytest.raises(ValueError):  # data that is not a level copy has no is_request / is_choice
        RL.mention_class(toy_ed(), NV.mwoz_rules(2), {})


def test_default_and_sweep_unchanged():
    assert Rules.default().noise_kind == "pattern" and Rules.default().names == "v34"
    sweep = SR.single_changes()
    assert not any("mwoz" in s or "l2rated" in s for s in sweep)
    assert Rules.parse("default,noise_kind=mwoz,names=l2rated").noise_kind == "mwoz"


def test_noise_sets_toy():
    ed = toy_ed()
    ed = replace(ed, mentions=MEN.assign(turn_text=MEN["text"]))
    extra = {"gt_levels": GT.assign(is_request=False), "_other_gold": {"train": {}}}
    s = NV.noise_sets({"train": ed}, extra).set_index("cluster_id")
    assert list(s["label_mwoz"]) == ["real", "real", "noise"] and bool(s.loc["E1#2", "noise_mwoz"])
    assert list(s["n"]) == [2, 2, 2]
    md = NV.noise_sets_md(s.reset_index())
    assert "| all | 3 |" in md


# ---- task 15

def toy_variants():
    dec = pd.DataFrame({"cluster_id": ["E1#0", "E1#1", "E1#2"], "action": ["keep", "not_attribute", "attribute_cue"]})
    ok = pd.DataFrame({"cluster_id": ["E1#0", "E1#1", "E1#2"], "action": ["keep", "keep", "not_attribute"]})
    return {"E s012": SimpleNamespace(dec=dec), "A r1": SimpleNamespace(dec=ok)}


def test_noise_l2_rows_and_table():
    ed = toy_ed(toy_variants())
    extra = {"gt_levels": GT.assign(is_request=False)}
    rows = NV.noise_l2_rows({"train": ed}, extra, ["E s012", "A r1", "C s0"])
    assert list(rows["variant"]) == ["E s012", "A r1"]  # C s0 is not in the bundle
    e = rows[rows["variant"] == "E s012"].iloc[0]
    # noise set = {E1#2}; marked = {E1#1 (real), E1#2 (noise)}
    assert (e["noise_n"], e["noise_marked"], e["marked_n"], e["marked_noise"], e["marked_real"]) == (1, 1, 2, 1, 1)
    a = rows[rows["variant"] == "A r1"].iloc[0]
    assert (a["noise_marked"], a["marked_n"], a["marked_real"]) == (1, 1, 0)
    t = NV.noise_l2_table(rows).set_index("variant")
    assert t.loc["E s012", "noise_marked_kn"] == "1/1 (1.000)" and t.loc["E s012", "precision_kn"] == "1/2 (0.500)"
    assert t.loc["E s012", "marked_real"] == 1
    skipped = NV.noise_l2_rows({"train": ed}, extra, ["E s012", "A r1"], invalid=[{"ent": "train", "variant": "A r1"}])
    assert list(skipped["variant"]) == ["E s012"]
    assert "A r1" in NV.noise_l2_md(t.reset_index(), [{"ent": "train", "variant": "A r1"}])


def test_noise_l2_pools_entities():
    rows = pd.DataFrame([["V", "train", 3, 2, 4, 2, 1, 1], ["V", "hotel", 2, 2, 3, 2, 1, 0]], columns=NV.L2_COLS)
    t = NV.noise_l2_table(rows).iloc[0]
    assert t["noise_marked_kn"] == "4/5 (0.800)" and t["precision_kn"] == "4/7 (0.571)" and t["marked_real"] == 2


# ---- task 16

def toy_named_ed():
    attrs = pd.DataFrame([["E1#0", "departure", "d", "E1#0", "keep", "keep"],
                          ["E1#1", "train_id", "d", "E1#1", "keep", "keep"]],
                         columns=["attr_id", "name", "description", "clusters", "source", "status"])
    vo = SimpleNamespace(attrs=attrs, assign={0: "E1#0", 1: "E1#0", 2: "E1#1", 3: "E1#1"}, dec=None)
    return toy_ed({"A r1": vo})


def write_rated(folder, r1, r2):
    key = pd.DataFrame({"row": ["0", "1"], "ent": "train", "name": ["departure", "train_id"], "description": "d",
                        "majority_gold_attr": ["Train departure", "Train trainid"], "variants": "A r1",
                        "n_variants": 1})
    key.to_csv(folder / RN.L2_KEY_FILE, index=False)
    for f, labels in zip(RN.L2_FILES, (r1, r2)):
        pd.DataFrame({"row": ["0", "1"], "label": labels}).to_csv(folder / f, index=False)


def test_read_l2_rated_lower_label_wins(tmp_path):
    assert RN.read_l2_rated(tmp_path) is None
    write_rated(tmp_path, ["right", "right"], ["right", "partly"])
    got = RN.read_l2_rated(tmp_path).set_index("majority_gold_attr")["label"]
    assert got["Train departure"] == "right" and got["Train trainid"] == "partly"
    write_rated(tmp_path, ["right", "bad"], ["right", "right"])
    with pytest.raises(ValueError):
        RN.read_l2_rated(tmp_path)


def test_names_l2rated_at_level(tmp_path):
    ed = toy_named_ed()
    old = pd.DataFrame([["train", "departure", "d", "Train departure", "right"],
                        ["train", "train_id", "d", "", "valid_extra"]],
                       columns=["ent", "name", "description", "majority_gold_attr", "label"])
    rules = Rules.parse("default,names=l2rated")
    write_rated(tmp_path, ["right", "right"], ["right", "right"])
    extra = {"names_rated": old, "names_l2": RN.read_l2_rated(tmp_path)}
    l2ed = D.with_level({"train": ed}, GT, 2)["train"]
    r = RN.name_scores(l2ed, "A r1", rules, extra)
    assert (r["name_right"], r["name_base"], r["valid_extra"], r["names_unrated"]) == (2, 3, 0, 0)
    write_rated(tmp_path, ["right", "right"], ["right", "partly"])  # trainid: lower label wins -> not right
    extra["names_l2"] = RN.read_l2_rated(tmp_path)
    assert RN.name_scores(l2ed, "A r1", rules, extra)["name_right"] == 1
    # L1 stays as names=v34; the default rules still use the valid_extra approximation at L2
    l1 = D.with_level({"train": ed}, GT, 1)["train"]
    assert RN.name_scores(l1, "A r1", rules, extra)["name_right"] == 1
    assert RN.name_scores(l2ed, "A r1", Rules.parse("default"), extra)["name_right"] == 2
    extra["names_l2"] = RN.read_l2_rated(tmp_path).iloc[:1]  # a group the sheet does not hold is unrated, not right
    unrated = RN.name_scores(l2ed, "A r1", rules, extra)
    assert (unrated["name_right"], unrated["names_unrated"]) == (1, 1)
    with pytest.raises(ValueError):
        RN.name_scores(l2ed, "A r1", rules, {"names_rated": old})


def test_l2_sheet_is_blind_and_keyed():
    ed = toy_named_ed()
    rows = NL.l2_group_rows([{"train": ed}], GT)
    assert sorted(rows["majority_gold_attr"]) == ["Train departure", "Train trainid"]
    twice = pd.concat([rows, rows.assign(variant="B s0")], ignore_index=True)
    tear = {"Train departure": "train-departure"}
    rater, key = NL.rating_sheet(twice, tear, {"train-departure": "departure station", "train-trainid": "train id"})
    assert list(rater.columns) == NL.RATER_COLS and "variant" not in " ".join(rater.columns)
    assert list(key["row"]) == [0, 1] and set(key["variants"]) == {"A r1;B s0"} and set(key["n_variants"]) == {2}
    by = rater.set_index("l2_attr")
    assert by.loc["Train departure", "l2_slot"] == "train-departure"
    assert by.loc["Train trainid", "l2_slot"] == "train-trainid" and by.loc["Train trainid", "l2_slot_description"] == "train id"
    rater2, _ = NL.rating_sheet(twice, tear, {})
    assert list(rater2["row"]) == list(rater["row"]) and list(rater2["l2_attr"]) == list(rater["l2_attr"])  # fixed seed
