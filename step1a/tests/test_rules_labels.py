import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import rules_labels as RL  # noqa: E402


def R(unlabeled="old", noise_kind="old", cluster_label="0.6"):
    return SimpleNamespace(unlabeled=unlabeled, noise_kind=noise_kind, cluster_label=cluster_label)


def make(rows, labels):
    """rows: (cluster, text, gold_attr, entity_gold); one turn text 'text' for all."""
    m = pd.DataFrame([{"mention_id": i, "cluster_id": c, "text": t, "norm_value": t.lower(), "gold_attr": g,
                       "entity_gold": e, "speaker": "user", "turn_text": f"I want {t} please", "prev_turn": ""}
                      for i, (c, t, g, e) in enumerate(rows)])
    lab = pd.DataFrame({"cluster_id": list(labels), "label": list(labels.values())})
    return SimpleNamespace(ent="train", entity="E1", gold_ents=["train"], mentions=m, labels=lab)


OTHER = {"cambridge": "hotel"}


@pytest.mark.parametrize("value,kind", [
    ("which day", "question"), ("how many people", "question"),
    ("5 restaurants", "result_count"), ("three hotels", "result_count"),
    ("the restaurant", "general"), ("a cheap hotel", "general"),
    ("to Stansted", "broken"), ("Stansted airport and", "broken"),
    ("20:30", "odd_format"), ("TR1234", "odd_format"), ("10.10 pounds", "odd_format"), ("£12.50", "odd_format"),
    ("Cambridge", "other_entity"), ("Stansted", "other"), ("The Huntingdon Marriott", "other")])
def test_kinds(value, kind):
    assert RL.noise_kind_of(value, f"I want {value} please", OTHER) == kind


def test_kind_there_are_and_cut_word():
    assert RL.noise_kind_of("5", "there are 5 options", OTHER) == "result_count"
    assert RL.noise_kind_of("stan", "go to stansted", OTHER) == "broken"
    assert RL.noise_kind_of("Stansted", "Go to Stansted.", OTHER) == "other"


ROWS = [("c1", "Stansted", "Train destination", "train"), ("c1", "Ely", "Train destination", "train"),
        ("c1", "Bath", "", ""), ("c1", "Bury", "", ""), ("c1", "Leeds", "", ""),
        ("c2", "which day", "", ""), ("c2", "the hotel", "", ""), ("c2", "Leeds", "", "")]
LABELS = {"c1": "gold", "c2": "noise"}


def test_mention_class_old_and_unlabeled():
    ed = make(ROWS, LABELS)
    assert list(RL.mention_class(ed, R(), {})) == ["Train destination"] * 2 + ["unlabeled"] * 6
    assert list(RL.mention_class(ed, R("noise"), {}))[2:] == ["noise"] * 6


def test_pattern_classes():
    ed = make(ROWS + [("c2", "Cambridge", "", ""), ("c2", "20:30", "", "")], LABELS)
    got = list(RL.mention_class(ed, R("exclude", "pattern"), {"other_gold": OTHER}))
    assert got[5:] == ["cue", "noise", "unlabeled", "other_entity:hotel", "real_extra"]


def test_multiclass_kept():
    ed = make([("c1", "Ely", "Hotel area;Train destination", "hotel")], {"c1": "gold"})
    assert RL.mention_class(ed, R(), {}).iloc[0] == "Hotel area;Train destination"


def test_jury_and_missing():
    ed = make(ROWS, LABELS)
    jury = pd.DataFrame({"cluster_id": ["c1", "c2"], "jury": ["real", "noise"]})
    got = list(RL.mention_class(ed, R("exclude", "jury"), {"jury": jury}))
    assert got[2:5] == ["real_extra"] * 3 and got[5:] == ["noise"] * 3
    with pytest.raises(ValueError):
        RL.mention_class(ed, R("exclude", "jury"), {})


def test_unlabeled_exclusion_changes_shares():
    ed = make(ROWS, LABELS)
    c1 = lambda r: RL.cluster_labels(ed, r, {}).set_index("cluster_id").loc["c1"]  # noqa: E731
    old, exc = c1(R()), c1(R("exclude"))
    assert (old["n_counted"], old["top_share"], old["label"]) == (5, 0.4, "mixed")
    assert (exc["n_counted"], exc["top_share"], exc["label"]) == (2, 1.0, "real")
    assert c1(R("noise"))["noise_share"] == 0.6


def test_noise_counts_and_cue():
    ed = make(ROWS, LABELS)
    c2 = RL.cluster_labels(ed, R("exclude", "pattern"), {"other_gold": {}}).set_index("cluster_id").loc["c2"]
    assert c2["n_counted"] == 2 and c2["noise_share"] == 1.0 and c2["label"] == "noise"  # cue + noise


def test_thresholds_flip_label():
    rows = [("c1", f"v{i}", "Train day", "train") for i in range(11)] + [("c1", f"w{i}", "Train area", "train")
                                                                          for i in range(9)]
    ed = make(rows, {"c1": "gold"})
    lab = {t: RL.cluster_labels(ed, R("exclude", cluster_label=t), {}).iloc[0]["label"] for t in ("0.5", "0.6", "0.7")}
    assert lab == {"0.5": "real", "0.6": "mixed", "0.7": "mixed"}
    rows = [("c1", f"v{i}", "Train day", "train") for i in range(13)] + [("c1", f"w{i}", "Train area", "train")
                                                                          for i in range(7)]
    ed = make(rows, {"c1": "gold"})
    lab = {t: RL.cluster_labels(ed, R("exclude", cluster_label=t), {}).iloc[0]["label"] for t in ("0.5", "0.6", "0.7")}
    assert lab == {"0.5": "real", "0.6": "real", "0.7": "mixed"}


def test_old_label_maps_labels_csv():
    ed = make(ROWS + [("c3", "x", "", "")], {"c1": "gold", "c2": "noise", "c3": "other"})
    ed.labels = pd.DataFrame({"cluster_id": ["c1", "c2", "c3", "c4"], "label": ["valid_new", "noise", "other", "gold"]})
    out = RL.cluster_labels(ed, R("old", cluster_label="old"), {}).set_index("cluster_id")["label"]
    assert out.to_dict() == {"c1": "real", "c2": "noise", "c3": "mixed"}


def test_q2_table_differs():
    ed = make(ROWS, LABELS)
    ed.labels = pd.DataFrame({"cluster_id": ["c1", "c2"], "label": ["gold", "noise"]})
    t = RL.q2_table({"train": ed}, {"old": R(cluster_label="old"), "0.5": R("exclude", "pattern", "0.5"),
                                    "0.7": R("exclude", "pattern", "0.7")}, {"other_gold": {}})
    assert {"label_old", "label_0.5", "label_0.7", "differs_from_old", "top_share"} <= set(t.columns)
    assert not t["differs_from_old"].any()


def test_role_pairs_file():
    assert RL.role_pairs() == [("departure", "destination"), ("leave at", "arrive by")]
    assert RL.role_pairs(entity="hotel") == []
    assert RL.role_pairs(entity="taxi") == RL.role_pairs()


def test_other_entity_wrong_entity_and_frequent():
    # "Cambridge" is another entity's gold value; with wrong_entity it is neither real nor noise and counts against the top share
    ed = make([("c1", "Stansted", "Train destination", "train"), ("c1", "Cambridge", "", ""),
               ("c1", "Cambridge", "", ""), ("c2", "Ely", "", "")], {"c1": "gold", "c2": "noise"})
    base = R("exclude", "pattern")
    old = list(RL.mention_class(ed, base, {"other_gold": OTHER}))
    assert old[1:3] == ["other_entity:hotel"] * 2
    new = SimpleNamespace(**vars(base), other_entity="wrong_entity")
    assert list(RL.mention_class(ed, new, {"other_gold": OTHER}))[1:3] == ["wrong_entity"] * 2
    # frequent value: stays as in old
    freq = RL.mention_class(ed, new, {"other_gold": OTHER, "frequent": {"cambridge"}})
    assert list(freq)[1:3] == ["other_entity:hotel"] * 2
    # the class is not an attribute: top share 1/3 (below 0.6), noise share 0 -> mixed
    row = RL.cluster_labels(ed, new, {"other_gold": OTHER}).set_index("cluster_id").loc["c1"]
    assert row["n_counted"] == 3 and row["top_attr"] == "Train destination" and row["label"] == "mixed"


def test_frequent_values():
    gv = pd.DataFrame({"dialogue_id": ["d1", "d2", "d3", "d4", "d5", "d6", "d1"],
                       "value": ["Cambridge", "Cambridge", "Ely", "Bath", "Bath", "Bath", "Ely"],
                       "entity_gold": ["hotel", "train", "hotel", "hotel", "hotel", "hotel", "hotel"]})
    shared = SimpleNamespace(gv=gv, docs={f"d{i}": None for i in range(1, 11)})
    # Cambridge: 2 entities; Bath: 3/10 dialogues (0.3), 3/15 is 0.2 too; Ely: 2/10 dialogues (0.2 counts)
    assert RL.frequent_values(shared) == {"cambridge", "bath", "ely"}
    shared.docs = {f"d{i}": None for i in range(1, 16)}  # Bath 3/15 = 0.2 stays, Ely 2/15 goes
    assert RL.frequent_values(shared) == {"cambridge", "bath"}
