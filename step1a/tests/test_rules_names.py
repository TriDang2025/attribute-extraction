import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import rules_names as RN  # noqa: E402
from s1a.score_rules import Rules  # noqa: E402

DEC_COLS = ["cluster_id", "name", "action", "merge_with", "split"]


def dec(*rows):
    """rows: (cluster_id, name, action, merge_with list)."""
    return pd.DataFrame([{"cluster_id": c, "name": n, "action": a, "merge_with": json.dumps(m), "split": ""}
                         for c, n, a, m in rows], columns=DEC_COLS)


def variant(attrs, assign):
    a = pd.DataFrame(attrs, columns=["attr_id", "name", "description", "clusters", "source", "status"])
    return SimpleNamespace(attrs=a, assign=assign, dec=None)


def toy():
    # E1#0: Train departure (cambridge, london); E1#1: Train id codes (no gold); E1#2: yes/ok noise
    men = pd.DataFrame({
        "cluster_id": ["E1#0", "E1#0", "E1#1", "E1#1", "E1#2"], "mention_id": ["0", "1", "2", "3", "4"],
        "gold_attr": ["Train departure", "Train departure", "", "", ""],
        "norm_value": ["cambridge", "london", "tr1234", "tr5678", "yes"],
        "text": ["Cambridge", "London", "TR1234", "TR5678", "yes"]})
    attrs = [["E1#0", "departure_station", "d", "E1#0", "keep", "keep"],
             ["E1#1", "train_id", "d", "E1#1", "keep", "keep"],
             ["E1#2", "", "", "E1#2", "keep", "not_attribute"]]
    assign = {0: "E1#0", 1: "E1#0", 2: "E1#1", 3: "E1#1"}
    vs = {k: variant(attrs, assign) for k in ("A r1", "A r2", "B s0", "C s0", "C s1", "C s2", "C s012", "D s012")}
    vs["B s0"] = variant([["E1#0", "station", "d", "E1#0", "keep", "keep"]] + attrs[1:], assign)
    ctx = SimpleNamespace(train=["Train departure", "Train destination"])
    labels = pd.DataFrame({"cluster_id": ["E1#0", "E1#1", "E1#2"], "label": ["gold", "valid_new", "noise"]})
    return SimpleNamespace(ent="train", entity="E1", gold_ents=["train"], mentions=men, labels=labels, variants=vs,
                           ctx_a=ctx, ctx_r=ctx)


def test_sheet_and_rate(monkeypatch):
    ed = toy()
    monkeypatch.setattr("s1a.v34_data.VARIANTS", ["A r1", "B s0"], raising=False)
    old = pd.DataFrame([{"variant": "A", "run_tag": "r1", "attr_id": "E1#0", "final": "exact"}])
    cl = {"train": pd.DataFrame({"cluster_id": ["E1#0", "E1#1", "E1#2"], "label": ["real", "real", "noise"]})}
    s = RN.name_sheet({"train": ed}, old, {"cluster_labels": cl})
    assert len(s) == 6 and list(s.columns) == RN.SHEET_COLS
    a = s[(s["variant label"] == "A r1") & (s["attr_id"] == "E1#0")].iloc[0]
    assert a["old_final"] == "exact" and a["majority_gold_attr"] == "Train departure" and a["role"] == "departure"
    assert a["cluster_label"] == "real" and a["top_values"] == "cambridge|london"
    tid = s[(s["variant label"] == "A r1") & (s["attr_id"] == "E1#1")].iloc[0]
    assert tid["valid_extra_candidate"] and tid["freq"] == 2 and tid["old_final"] == ""
    marked = s[s["attr_id"] == "E1#2"]
    assert (marked["row"] == "").all() and (marked["cluster_label"] == "noise").all()
    rate = RN.names_to_rate(s)
    assert len(rate) == 3 and list(rate.columns) == ["row"] + RN.RATE_COLS
    assert sorted(s["row"][s["row"] != ""].unique()) == [0, 1, 2]


def test_name_scores():
    ed = toy()
    rated = pd.DataFrame({"ent": ["train", "train"], "name": ["departure_station", "train_id"],
                          "description": ["d", "d"], "majority_gold_attr": ["Train departure", ""],
                          "label": ["right", "valid_extra"]})
    r = RN.name_scores(ed, "A r1", Rules.default(), {"names_rated": rated})
    assert r == {"name_right": 1, "name_base": 2, "name_acc": 0.5, "valid_extra": 1, "role_right": 1, "role_base": 2}
    # the station name was never rated right for B: no credit; two ratings of one key keep the lower label
    both = pd.concat([rated, rated.iloc[[0]].assign(label="wrong")], ignore_index=True)
    assert RN.name_scores(ed, "A r1", Rules.default(), {"names_rated": both})["name_right"] == 0
    assert RN.name_scores(ed, "A r1", Rules.default(), {}) == {}
    with pytest.raises(ValueError):
        RN.name_scores(ed, "A r1", Rules.default(), {"names_rated": rated.assign(label="exact")})


def seeded(rows0, rows1, rows2):
    ed = toy()
    ed.seed_decs = {"C s0": dec(*rows0), "C s1": dec(*rows1), "C s2": dec(*rows2)}
    ed.ctx_r = SimpleNamespace(train=["Train departure"])
    return ed


def test_order_diffs_types():
    k = ("E1#0", "departure_station", "keep", [])
    ed = seeded(
        [k, ("E1#1", "train_id", "keep", []), ("E1#2", "", "not_attribute", [])],
        [("E1#0", "departure", "keep", []), ("E1#1", "train_id", "merge", ["E1#2"]), ("E1#2", "train_id", "merge", ["E1#1"])],
        [("E1#0", "departure_city", "keep", []), ("E1#1", "train_id", "keep", []), ("E1#2", "", "not_attribute", [])])
    d = RN.order_diffs(ed).set_index("cluster_id")["type"].to_dict()
    assert d == {"E1#0": "wording", "E1#1": "membership", "E1#2": "noise"}
    meaning = seeded([("E1#0", "departure", "keep", [])] * 1, [("E1#0", "destination_city", "keep", [])],
                     [("E1#0", "departure", "keep", [])])
    assert RN.order_diffs(meaning)["type"].tolist() == ["meaning"]
    same = seeded([k], [k], [k])
    assert RN.order_diffs(same).empty


def test_agreement():
    k = ("E1#0", "departure_station", "keep", [])
    ed = seeded([k, ("E1#2", "", "not_attribute", [])],
                [k, ("E1#2", "", "not_attribute", [])],
                [("E1#0", "departure", "keep", []), ("E1#2", "x", "keep", [])])
    old = RN.agreement(ed, Rules.old(), {})
    assert old["agree_names"] == pytest.approx((2 / 3 + 2 / 3) / 2)
    new = RN.agreement(ed, Rules.default(), {})
    assert new["agree_noise"] == pytest.approx((1 + 2 / 3) / 2)
    assert new["agree_groups"] == 1.0
    assert new["agree_names"] == 1.0  # wording ignored: both names overlap Train departure
    nm = seeded([k], [k], [("E1#0", "station", "keep", [])])
    assert RN.agreement(nm, Rules.default(), {})["agree_names"] == pytest.approx(2 / 3)


ROWS = [{"ent": e, "variant": v, "found_n": f} for e, vals in
        {"train": {"A r1": 3, "A r2": 4, "C s0": 4, "C s1": 3, "C s2": 3, "B s0": 3, "C s012": 6, "D s012": 4},
         "hotel": {"A r1": 5, "A r2": 5, "C s0": 6, "C s1": 5, "C s2": 5, "B s0": 5, "C s012": 6, "D s012": 4}}.items()
        for v, f in vals.items()]


def test_order_range():
    r = RN.order_range(ROWS).set_index("ent")
    assert r.loc["train", "range"] == 1 and r.loc["hotel", "range"] == 1
    assert r.loc["all", "range_C"] == 2 and r.loc["all", "range_A"] == 1 and r.loc["all", "range"] == 2


def test_gain_verdict():
    g = RN.gain_verdict(ROWS).set_index("variant")
    assert g.loc["B s0", "total_gain"] == 0 and not g.loc["B s0", "counts"]
    assert g.loc["C s012", "total_gain"] == 4 and g.loc["C s012", "counts"]
    assert not g.loc["D s012", "counts"] and g.loc["D s012", "reason"] == "total < 2"
    # one entity loses an attribute
    rows = [dict(r, found_n=r["found_n"] + (3 if r["variant"] == "C s012" and r["ent"] == "train" else 0)
                 - (2 if r["variant"] == "C s012" and r["ent"] == "hotel" else 0)) for r in ROWS]
    h = RN.gain_verdict(rows).set_index("variant")
    assert h.loc["C s012", "reason"] == "an entity loses one"
    # n/a found_n is ignored, not a crash
    assert RN.gain_verdict([dict(r, found_n="n/a") for r in ROWS]).shape[0] == 3
