import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import score_rules as SR  # noqa: E402
from s1a.score_rules import NA, NEW_COLS, Rules  # noqa: E402


def test_old_and_default():
    assert all(v == "old" for v in vars(Rules.old()).values())
    d = Rules.default()
    assert (d.unlabeled, d.noise_kind, d.cluster_label, d.role_pairs, d.names, d.found, d.merge, d.placement,
            d.agreement) == ("exclude", "pattern", "0.6", "config", "v34", "cov10", "n20", "majority", "split")


def test_parse():
    assert Rules.parse("old") == Rules.old()
    assert Rules.parse("default") == Rules.default()
    r = Rules.parse("default,found=cov25,merge=n10")
    assert (r.found, r.merge, r.names) == ("cov25", "n10", "v34")
    r = Rules.parse("old,unlabeled=exclude")
    assert r.unlabeled == "exclude" and r.merge == "old"
    assert Rules.parse("found=cov0").found == "cov0"
    for bad in ("nope", "default,found=cov99", "default,x=1", "default,found"):
        with pytest.raises(ValueError):
            Rules.parse(bad)


def test_single_changes():
    s = SR.single_changes()
    assert s[:2] == ["old", "default"] and len(s) == 2 + 17
    assert all(Rules.parse(x) != Rules.default() for x in s[2:])
    assert "default,found=cov25" in s and "default,found=cov10" not in s


def toy(vote=None):
    dec = pd.DataFrame({"cluster_id": ["E1#0", "E1#1"], "action": ["not_attribute", "keep"]})
    return SimpleNamespace(ent="train", variants={"C s012": SimpleNamespace(dec=dec), "A r1": SimpleNamespace(dec=dec)},
                           vote_stats=vote or {"agree_mean": 0.9})


OLD = {"noise_marked": 0.5, "recall_after": 0.4, "merge_pure": 0.7, "place_right": 0.8, "real_acc": 0.6}


def fake(monkeypatch, funcs):
    monkeypatch.setattr(SR, "_lookup", lambda module, name: funcs.get(name))


def test_missing_stage2_is_na(monkeypatch):
    fake(monkeypatch, {})
    row = SR.new_columns(toy(), "A r1", Rules.default(), {}, OLD)
    assert row == dict.fromkeys(NEW_COLS, NA)


def test_old_rules_copy_old_values(monkeypatch):
    fake(monkeypatch, {})
    row = SR.new_columns(toy(), "C s012", Rules.old(), {}, {**OLD, "agree_mean": 0.9})
    assert (row["noise_marked_v"], row["recall_v"], row["merge_prec"], row["place_acc"], row["name_acc"]) == (0.5, 0.4, 0.7, 0.8, 0.6)
    assert row["agree_groups"] == row["agree_noise"] == row["agree_names"] == 0.9
    assert row["found_n"] == NA
    other = SR.new_columns(toy(), "A r1", Rules.old(), {}, OLD)
    assert other["agree_groups"] == NA  # agreement is for C s012 only


def test_stage2_values_used_unless_rule_old(monkeypatch):
    funcs = {"found": lambda ed, label, rules, extra: pd.DataFrame({"found": [True, False, True]}),
             "merges": lambda ed, label, rules, extra: pd.DataFrame({"right": [1, 0]}),
             "placement": lambda ed, label, rules, extra: {"place_acc": 0.95, "place_n": 10, "place_base": 0.5},
             "cluster_labels": lambda ed, rules, extra: pd.DataFrame({"cluster_id": ["E1#0", "E1#1"], "label": ["noise", "noise"]}),
             "mention_class": lambda ed, rules, extra: pd.Series(["cue", "noise", "cue"])}
    fake(monkeypatch, funcs)
    row = SR.new_columns(toy(), "A r1", Rules.default(), {}, OLD)
    assert (row["found_n"], row["gold_n"]) == (2, 3) and row["recall_v"] == pytest.approx(2 / 3)
    assert (row["merge_n"], row["merge_right"], row["merge_prec"]) == (2, 1, 0.5)
    assert (row["place_acc"], row["place_n"]) == (0.95, 10)
    assert (row["noise_n"], row["noise_marked_v"], row["cue_n"]) == (2, 0.5, 2)
    assert row["name_acc"] == NA
    # the found rule stays "old": recall_v copies recall_after, found_n still comes from stage 2
    row = SR.new_columns(toy(), "A r1", Rules.parse("default,found=old"), {}, OLD)
    assert row["recall_v"] == 0.4 and row["found_n"] == 2
