import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import pilot_score as PS  # noqa: E402
from test_pilot_score import ctx, decisions, run  # noqa: E402


def test_placement_baseline_is_the_share_of_current_entity_clusters():
    c, _ = ctx()
    dec = decisions()
    base, n = PS.placement_baseline(dec, c)
    right, n_right = PS._placement_checks(dec, c)["place_right"]
    assert n == n_right
    # rows with a placement and a gold entity that a predicted entity has: E1#0, 1, 2, 3, 4, 7; all gold "train" = E1
    assert (base, n) == (1.0, 6)
    assert right == pytest.approx(5 / 6)  # E1#1 was placed in E2 (hotel)


def test_placement_baseline_counts_clusters_of_other_gold_entities():
    c, _ = ctx()
    c.cluster_gold["E1#1"] = "hotel"  # now a hotel cluster sitting in E1
    base, n = PS.placement_baseline(decisions(), c)
    assert (base, n) == (pytest.approx(5 / 6), 6)


def test_placement_current_share():
    c, _ = ctx()
    share, n = PS.placement_current(decisions(), c)
    # placements: E1#0 current, E1#1 E2, E1#2 sub-entity, E1#3 current, E1#4 separate table, E1#7 current
    assert (share, n) == (pytest.approx(5 / 6), 6)


def test_score_file_carries_the_new_measures():
    c, _ = ctx()
    r = run(c, decisions())[0]
    assert r["place_base"] == 1.0 and r["place_base_n"] == 6
    assert r["place_current"] == pytest.approx(5 / 6) and r["place_current_n"] == 6


def role_mentions():
    spec = [("E1#0", ["Train departure"] * 3 + ["Train destination"]),
            ("E1#1", ["Train leave at"] * 2 + ["Train arrive by"] * 2 + [""]),
            ("E1#2", ["Train day"] * 4),
            ("E2#0", ["Hotel area"]),
            ("E1#3", ["Train departure;Train destination"])]
    rows = [(cid, cid[:2], g) for cid, gs in spec for g in gs]
    return pd.DataFrame({"mention_id": range(len(rows)), "cluster_id": [r[0] for r in rows],
                         "entity": [r[1] for r in rows], "gold_attr": [r[2] for r in rows]})


def test_role_table_counts_a_known_mix():
    t = PS.role_table(role_mentions(), "E1")
    assert list(t.columns) == ["entity", "cluster_id", "n", "departure", "destination", "leave_at", "arrive_by",
                               "role_kind", "major_role", "major_share"]
    assert list(t["cluster_id"]) == ["E1#0", "E1#1", "E1#3"]  # no role mention: E1#2; other entity: E2#0
    r0, r1, r3 = (t.iloc[i] for i in range(3))
    assert (r0["n"], r0["departure"], r0["destination"], r0["role_kind"], r0["major_role"]) == (4, 3, 1, "place", "departure")
    assert r0["major_share"] == pytest.approx(0.75)
    assert (r1["n"], r1["leave_at"], r1["arrive_by"], r1["role_kind"], r1["major_role"]) == (5, 2, 2, "time", "leave_at")
    assert r1["major_share"] == pytest.approx(0.5)
    assert (r3["departure"], r3["destination"], r3["major_role"]) == (1, 1, "departure")  # multi-class counts for each


def test_role_table_empty_entity_has_the_columns():
    assert list(PS.role_table(role_mentions(), "E9").columns) == PS.ROLE_COLS


def sheet_inputs():
    m = pd.DataFrame({"mention_id": range(8), "cluster_id": ["E1#0", "E1#0", "E1#1", "E1#1", "E1#2", "E1#3", "E2#0", ""],
                      "entity": ["E1"] * 6 + ["E2", ""], "norm_value": ["a", "a", "b", "c", "d", "e", "f", "g"]})
    labels = pd.DataFrame({"cluster_id": ["E1#0", "E1#1", "E1#2", "E1#3", "E2#0"],
                           "label": ["noise", "gold", "valid_new", "noise", "gold"], "gold_attr": ["", "x", "", "", "y"],
                           "purity": 0.5, "label_by": "model"})
    d1 = pd.DataFrame({"variant": "v2", "run_tag": "r1", "cluster_id": ["E1#0", "E1#1", "E1#2"],
                       "action": ["not_attribute", "keep", "unsure"], "ent": "train"})
    d2 = pd.DataFrame({"variant": "A", "run_tag": "s0", "cluster_id": ["E1#0", "E1#1", "E1#2", "E2#0"],
                       "action": ["not_attribute", "not_attribute", "keep", "keep"], "ent": ["train"] * 3 + ["hotel"]})
    return m, labels, [d1, d2]


def test_noise_sheet_lists_gold_noise_and_marked_clusters_once():
    m, labels, decs = sheet_inputs()
    seen = []
    t = PS.noise_sheet(m, labels, decs, "docs",
                       example_fn=lambda d, e, c: seen.append((d, e, c)) or [f"{c} l1", f"{c} l2"])
    assert list(t.columns) == PS.SHEET_COLS
    assert list(t["cluster_id"]) == ["E1#0", "E1#1", "E1#2", "E1#3"]  # E1#0 is gold noise and marked twice: one row
    assert seen[0] == ("docs", "E1", "E1#0")
    r = t.set_index("cluster_id")
    assert r.at["E1#0", "model_marked_by"] == "A s0;v2 r1" and r.at["E1#0", "gold_label"] == "noise"
    assert r.at["E1#1", "model_marked_by"] == "A s0" and r.at["E1#1", "gold_label"] == "gold"
    assert r.at["E1#2", "model_marked_by"] == "v2 r1"
    assert r.at["E1#3", "model_marked_by"] == "" and r.at["E1#3", "ent"] == ""  # gold noise only, in no table
    assert r.at["E1#0", "n"] == 2 and r.at["E1#0", "top_values"] == "a" and r.at["E1#1", "top_values"] == "b|c"
    assert r.at["E1#0", "examples"] == "E1#0 l1 || E1#0 l2" and r.at["E1#0", "ent"] == "train"
    assert (t["human"] == "").all()


def test_apply_human_labels_mapping():
    m, labels, decs = sheet_inputs()
    sheet = PS.noise_sheet(m, labels, decs, None, example_fn=lambda d, e, c: [])
    sheet["human"] = ["noise", "real", "mixed", "real"]  # E1#0 noise, E1#1 gold, E1#2 valid_new, E1#3 noise
    out = PS.apply_human_labels(labels, sheet).set_index("cluster_id")
    assert out.at["E1#0", "label"] == "noise"  # unchanged
    assert out.at["E1#1", "label"] == "gold"  # real on a real label: unchanged
    assert out.at["E1#2", "label"] == "mixed"
    assert out.at["E1#3", "label"] == "valid_new"  # noise -> real
    assert out.at["E2#0", "label"] == "gold"  # not in the sheet
    assert out.at["E1#3", "label_by"] == "human" and out.at["E1#0", "label_by"] == "model"
    assert labels.at[3, "label"] == "noise"  # input not modified


def test_apply_human_labels_ignores_blank_and_rejects_unknown():
    m, labels, decs = sheet_inputs()
    sheet = PS.noise_sheet(m, labels, decs, None, example_fn=lambda d, e, c: [])
    assert PS.apply_human_labels(labels, sheet).equals(labels)
    sheet["human"] = ["maybe", "", "", ""]
    with pytest.raises(ValueError):
        PS.apply_human_labels(labels, sheet)


def job(name, kind, variant, nbhd=None, cid=""):
    return {"job": name, "kind": kind, "variant": variant, "nbhd": nbhd, "cluster_id": cid, "run_tag": "s0"}


JOBS33 = ([job(f"{v}_{g}", "entity", v, g) for v in ("e", "e2") for g in (0, 1)] + [job("e1_1", "entity", "e1", 1)]
          + [job("f_0", "entity", "f", 0), job("f_1", "entity", "f", 1)]
          + [job("ga_1", "gate", "gate", None, "E1#1"), job("ga_2", "gate", "gate", None, "E1#2"),
             job("sp_1", "split", "split", None, "E1#1"), job("sp_2", "split", "split", None, "E1#2"),
             job("n_s0", "entity", "nbhd", 0)])


def names(jobs):
    return sorted(j["job"] for j in jobs)


def test_variant_jobs_v33_letters():
    assert names(PS.variant_jobs(JOBS33, "E", ["E1#2"])) == ["e_0", "e_1", "ga_1", "ga_2", "sp_2"]
    assert names(PS.variant_jobs(JOBS33, "E1", ["E1#2"])) == ["e1_1", "e_0", "ga_1", "ga_2", "sp_2"]
    assert names(PS.variant_jobs(JOBS33, "E2", [])) == ["e2_0", "e2_1", "ga_1", "ga_2"]
    assert names(PS.variant_jobs(JOBS33, "F", ["E1#2"])) == ["f_0", "f_1"]
    assert names(PS.variant_jobs(JOBS33, "C")) == ["n_s0", "sp_1", "sp_2"]  # v3.2 letters unchanged
