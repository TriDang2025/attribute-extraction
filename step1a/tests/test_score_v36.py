"""wf_v3.6 scoring of the Colab batch: repair flag on the v3 / C / E loaders, A range, gain verdict, oracle decision, g role
examples, role guard, oracle table helpers. Toy data only."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from s1a import g_roles_v36 as G  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import range_v36 as RV  # noqa: E402
from s1a import v36_data as V  # noqa: E402
from test_pilot_combine import CIDS, folder, v3, write_job  # noqa: E402


# ---- repair flag on the v3 / C / E loaders
def undeclared_obj():
    obj = v3({c: "leave" for c in CIDS})
    obj["clusters"][1]["attribute"] = "day"            # never declared
    obj["clusters"][2]["attribute"] = "attribute_cue"  # allowed
    return obj


def test_load_obj_repairs_flag_default_off(tmp_path):
    jobs = folder(tmp_path, [{c: "leave" for c in CIDS}] * 3)
    job = jobs[0]
    write_job(tmp_path, job, undeclared_obj(), {})
    assert [a["name"] for a in PC.load_obj(tmp_path, job)["attributes"]] == ["leave"]   # as saved
    rows = []
    fixed = PC.load_obj(tmp_path, job, rows)
    assert [a["name"] for a in fixed["attributes"]] == ["leave", "day"] and fixed["attributes"][1]["repaired"]
    assert rows == [{"job": job["job"], "repaired_names": ["day"]}]   # attribute_cue is not repaired
    rows.clear()
    PC.load_obj(tmp_path, {**job, "format": "split"}, rows)
    assert rows == []   # only v2 / v3 responses are repaired


def test_decisions_b_repairs(tmp_path):
    jobs = folder(tmp_path, [{c: "leave" for c in CIDS}] * 3)
    for j in jobs:
        write_job(tmp_path, j, undeclared_obj(), json.loads((tmp_path / j["schema"]).read_text(encoding="utf-8")))
    plain = PC.decisions_b(tmp_path, "train", 0).set_index("cluster_id")
    rows = []
    fixed = PC.decisions_b(tmp_path, "train", 0, repairs=rows).set_index("cluster_id")
    assert plain.loc["E1#1", "action"] == "unsure" and fixed.loc["E1#1", "action"] in ("keep", "merge")
    assert fixed.loc["E1#2", "action"] == "attribute_cue" and [r["repaired_names"] for r in rows] == [["day"], ["day"]]


# ---- A range and gain
def rows_for(variant, found, gold=(7, 11, 12), merge=(4, 8), names=(20, 30)):
    return pd.DataFrame([{"ent": e, "variant": variant, "found_n": f, "gold_n": g, "noise_n": 5, "noise_marked_v": 0.6,
                          "merge_right": merge[0], "merge_n": merge[1], "name_right": names[0], "name_base": names[1],
                          "role_right": 1, "role_base": 2, "cue_request": 0, "cue_clusters": 0}
                         for e, f, g in zip(RV.ENTS, found, gold)])


def test_range_cells_min_max():
    orders = [rows_for("A r1", (4, 9, 8)), rows_for("A r2", (3, 9, 8), merge=(3, 7)),
              rows_for("A s2", (4, 9, 9), names=(18, 30))]
    cells = RV.range_cells(orders)
    assert cells[:3] == ["3–4/7", "9/11", "8–9/12"]
    assert cells[3] == "9/15"                  # noise pooled: 3 marked of 5 per entity, per order
    assert cells[4] == "9–12/21–24"                     # merge summed over the 3 entities, n varies
    assert cells[5] == "54–60/90"
    assert RV.fmt_range([(None, None), (1.0, 2.0)]) == "n/a"
    assert RV.range_cells([rows_for("X", (1, 2, 3))], invalid={"train"})[0] == "n/a"


def found(**cols):
    return pd.DataFrame(cols, index=list(RV.ENTS))


def test_gain_vs_range_verdicts():
    t = found(**{"A r1": [4, 9, 8], "A r2": [3, 9, 8], "A s2": [4, 9, 9],      # totals 21, 20, 22; entity min 3 / 9 / 8
                 "up": [4, 10, 10],     # 24 = max + 2, nobody under their min: gain
                 "up1": [4, 9, 10],     # 23 = max + 1: not enough
                 "mixed": [2, 12, 10],  # 24 but train under its A min
                 "down": [3, 9, 7],     # 19 < 20: loss
                 "same": [4, 9, 8]})    # 21 inside
    g = RV.gain_vs_range(t, ["up", "up1", "mixed", "down", "same"]).set_index("variant")
    assert g.loc["up", "verdict"] == "gain" and g.loc["up", "gain over A max"] == 2
    assert g.loc["up", "A range total"] == "20–22"
    assert g.loc["up1", "verdict"].startswith("within A range (+1")
    assert "under its A min: train" in g.loc["mixed", "verdict"] and g.loc["mixed", "entities below A min"] == "train"
    assert g.loc["down", "verdict"] == "loss" and g.loc["down", "loss under A min"] == -1
    assert g.loc["same", "verdict"] == "within A range"
    t["bad"] = [np.nan, 9, 8]
    assert RV.gain_vs_range(t, ["bad"]).iloc[0]["verdict"].startswith("n/a")


def test_oracle_decision_pass_and_fail():
    t = found(**{"C s012": [3, 9, 9], "Oracle s012": [5, 9, 9]})
    passed, d, total = RV.oracle_decision(t)
    assert passed and total == 2 and list(d) == [2, 0, 0]
    assert not RV.oracle_decision(found(**{"C s012": [3, 9, 9], "Oracle s012": [4, 9, 9]}))[0]   # +1 only
    assert not RV.oracle_decision(found(**{"C s012": [3, 9, 9], "Oracle s012": [6, 8, 9]}))[0]   # an entity loses one


# ---- g role examples and role guard
def test_role_accuracy_rules():
    pair = ("departure", "destination")
    assert G.role_accuracy([("a", ["departure"] * 3), ("b", ["destination"] * 2)], pair) == (5, 5)
    assert G.role_accuracy([("a", ["departure", "departure", "destination"])], pair) == (2, 3)             # one group
    assert G.role_accuracy([("a", ["departure"] * 3), ("b", ["departure", "destination"])], pair) == (3, 5)  # claimed twice
    assert G.role_accuracy([("a", ["departure", "destination", "other"])], pair) == (0, 2)                  # tie: none
    assert G.role_accuracy([], pair) == (0, 0)
    assert G.separates([("a", ["departure"]), ("b", ["destination"])], pair)
    assert not G.separates([("a", ["departure"]), ("b", ["departure"])], pair)


def test_cluster_rows():
    two = {"E1#0": ("departure", "destination")}
    ex_role = {"E1#0:0": "departure", "E1#0:1": "destination", "E1#0:2": "departure"}
    mixed = {"cluster_id": "E1#0", "mixed": True, "role_examples": [
        {"attribute": "from", "examples": ["E1#0:0", "E1#0:2"]}, {"attribute": "to", "examples": ["E1#0:1"]}]}
    plain = {"cluster_id": "E1#1", "mixed": False}
    rows = G.cluster_rows([(mixed, ex_role), (plain, {})], two)
    assert rows[0] == {"cluster_id": "E1#0", "two_role": True, "mixed": True, "has_role_examples": True, "groups": 2,
                       "k": 3, "n": 3, "separated": True}
    assert rows[1]["two_role"] is False and rows[1]["has_role_examples"] is False and rows[1]["n"] == 0


def test_guard_counts_and_texts():
    obj = {"attributes": [{"name": "departure_station", "role": "origin"}, {"name": "arrival_station", "role": "end"}],
           "clusters": [{"cluster_id": "E1#0", "attribute": "departure_station"},
                        {"cluster_id": "E1#1", "attribute": "arrival_station"},
                        {"cluster_id": "E1#2", "attribute": "Departure Station"}]}
    texts = G.cluster_texts(obj)
    assert texts["E1#0"] == "departure_station origin" and texts["E1#2"].endswith("origin")
    cols = ["variant", "run_tag", "cluster_id", "name", "description", "value_type", "action", "merge_with", "split",
            "placement", "evidence"]

    def table(links):
        return pd.DataFrame([{**dict.fromkeys(cols, ""), "cluster_id": c, "action": "merge" if links.get(c) else "keep",
                              "merge_with": json.dumps(links.get(c, []))} for c in ("E1#0", "E1#1", "E1#2")], columns=cols)

    dec = table({})
    ok = table({"E1#0": ["E1#2"], "E1#2": ["E1#0"]})    # same name: allowed
    bad = table({"E1#0": ["E1#1"], "E1#1": ["E1#0"]})   # departure + arrival: forbidden
    assert G.guard_counts(dec, ok, texts) == (1, [])
    assert G.guard_counts(dec, bad, texts) == (1, [("E1#0", "E1#1")])
    assert G.own_blocked(bad, texts) == [("E1#0", "E1#1")] and G.own_blocked(ok, texts) == []


# ---- oracle table helpers
def test_oracle_ids_and_labels(tmp_path):
    p = tmp_path / "o.csv"
    p.write_text("mention_id,entity,orig_cluster_id,oracle_cluster_id,gold_role\n1,E1,E1#0,E1#0.a,departure\n"
                 "2,E1,E1#0,E1#0.b,destination\n3,E1,E1#1,E1#1,\n", encoding="utf-8")
    ids = V.oracle_ids(p)
    assert ids == {1: "E1#0.a", 2: "E1#0.b", 3: "E1#1"}
    m = pd.DataFrame({"mention_id": ["1", "2", "3", "9"], "cluster_id": ["E1#0", "E1#0", "E1#1", "E1#7"]})
    assert list(V.with_oracle_ids(m, ids)["cluster_id"]) == ["E1#0.a", "E1#0.b", "E1#1", "E1#7"]
    lab = pd.DataFrame({"cluster_id": ["E1#0", "E1#1"], "label": ["gold", "noise"], "gold_attr": ["Train departure", ""]})
    out = V.oracle_labels(lab, ["E1#0.a", "E1#0.b", "E1#1"])
    assert list(out["cluster_id"]) == ["E1#0.a", "E1#0.b", "E1#1"] and list(out["label"]) == ["gold", "gold", "noise"]
    assert list(out.columns) == ["cluster_id", "label", "gold_attr"]
