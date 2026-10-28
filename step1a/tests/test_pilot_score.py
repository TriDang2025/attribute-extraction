import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import pilot_score as PS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402

# (cluster, entity, entity_gold, gold_attr, basis vector index, n)
SPEC = [("E1#0", "E1", "train", "Train day", 0, 3), ("E1#1", "E1", "train", "Train day", 0, 3),
        ("E1#2", "E1", "train", "Train leave at", 1, 3), ("E1#3", "E1", "train", "Train arrive by", 2, 3),
        ("E1#4", "E1", "train", "Train departure", 3, 2), ("E1#4", "E1", "train", "Train destination", 4, 2),
        ("E1#5", "E1", "", "", 6, 2), ("E1#6", "E1", "", "", 6, 2),
        ("E1#7", "E1", "train", "Train price", 5, 3), ("E1#8", "E1", "train", "Train price", 5, 3),
        ("E2#0", "E2", "hotel", "Hotel area", 7, 2)]
ATTRS = ["Train day", "Train leave at", "Train arrive by", "Train departure", "Train destination", "Train price",
         "Hotel area"]
CIDS = [f"E1#{i}" for i in range(9)]


def ctx():
    rows, vec = [], []
    for cid, ent, eg, ga, b, n in SPEC:
        for _ in range(n):
            rows.append((cid, ent, eg, ga))
            vec.append(np.eye(8)[b])
    k = len(rows)
    m = pd.DataFrame({"mention_id": range(k), "dialogue_id": "d1", "char_start": [10 * i for i in range(k)],
                      "char_end": [10 * i + 5 for i in range(k)], "cluster_id": [r[0] for r in rows],
                      "entity": [r[1] for r in rows], "entity_gold": [r[2] for r in rows],
                      "gold_attr": [r[3] for r in rows], "norm_value": "v"})
    gold = m[m["gold_attr"] != ""]
    gv = pd.DataFrame({"dialogue_id": "d1", "gold_attr": gold["gold_attr"], "entity_gold": gold["entity_gold"],
                       "char_start": gold["char_start"], "char_end": gold["char_end"], "verbatim": True})
    lab = {"E1#0": "gold", "E1#1": "gold", "E1#2": "gold", "E1#3": "gold", "E1#4": "unlabelled", "E1#5": "noise",
           "E1#6": "noise", "E1#7": "gold", "E1#8": "gold", "E2#0": "gold"}
    ga = m.groupby("cluster_id")["gold_attr"].first().to_dict()
    labels = pd.DataFrame({"cluster_id": list(lab), "label": list(lab.values()),
                           "gold_attr": [ga[c] if v == "gold" else "" for c, v in lab.items()]})
    c4 = m.index[m["cluster_id"] == "E1#4"].tolist()  # dep, dep, dest, dest
    ex = pd.DataFrame({"ex_id": [f"E1#4:{j}" for j in range(4)], "cluster_id": "E1#4", "mention_id": c4})
    return PS.Ctx(m, labels, gv, ATTRS, m["mention_id"].to_numpy(), np.array(vec, float), ex, "E1"), m


def obj(cid, name, action, **kw):
    return {"cluster_id": cid, "name": name, "action": action, **kw}


def decisions(c2_merge=True):
    return PV.decisions_table([
        obj("E1#0", "day", "merge", merge_with=["E1#1"], placement="current entity (E1)"),
        obj("E1#1", "day", "keep", placement="E2 (hotel)"),
        obj("E1#2", "time", "merge" if c2_merge else "keep", merge_with=["E1#3"] if c2_merge else [],
            placement="sub-entity of E1"),
        obj("E1#3", "arrive", "keep", placement="current entity (E1)"),
        obj("E1#4", "mixed", "split", placement="separate table",
            split=[{"name": "departure", "examples": ["E1#4:0", "E1#4:1", "E1#4:2"]},
                   {"name": "destination", "examples": ["E1#4:3"]}]),
        obj("E1#5", "x", "not_attribute"),
        obj("E1#6", "junk", "keep"),
        obj("E1#7", "price", "keep", placement="current entity (E1)"),
        obj("E1#8", "price", "keep")], CIDS, "full", "r1")


def run(c, dec, ver=None):
    assign, attrs, parts = PV.final_attributes(dec, c.mentions, c.ids, c.x, c.examples, c.entity)
    names = PS.name_check_table({("full", "r1"): (attrs, assign)}, c.mentions)
    ver = pd.DataFrame(columns=PV.VERIFY_COLS) if ver is None else ver
    return PS.score_file(dec, attrs, assign, parts, c, ver, names), attrs, assign, parts, names


def test_every_check_has_known_value(monkeypatch):
    monkeypatch.setattr(PS, "SPLIT_MIN_SIZE", 1)  # the toy split cluster is smaller than k = 8
    c, _ = ctx()
    r, attrs, *_ = run(c, decisions())
    assert (r["merge_pure"], r["merge_pure_n"]) == (0.5, 2)         # {c0,c1} pure; {c2,c3} mixes two classes
    assert (r["merge_frag"], r["merge_frag_n"]) == (0.5, 2)         # day fragments merged, price fragments not
    assert (r["split_done"], r["split_done_n"]) == (1.0, 1)         # the departure/destination cluster
    assert (r["split_side"], r["split_side_n"]) == (0.75, 4)        # part 0 holds dep, dep, dest
    assert (r["noise_marked"], r["noise_marked_n"]) == (0.5, 2)
    assert r["noise_kept"] == 1
    assert r["place_right"] == pytest.approx(5 / 6) and r["place_right_n"] == 6  # c1 placed in E2; sub-entity ok
    assert r["sugg_right"] == 0.5 and r["sugg_right_n"] == 2
    assert r["recall_before"] == pytest.approx(4 / 6)
    assert r["recall_after"] == pytest.approx(4 / 6)                # split gains dep + dest, bad merge loses 2
    assert r["recall_after_kept"] == pytest.approx(4 / 6)
    assert r["p1_after"] == pytest.approx(16 / 22)
    assert attrs.set_index("attr_id").loc["E1#5", "status"] == "not_attribute"


def test_without_bad_merge_all_classes_strict():
    c, _ = ctx()
    r, *_ = run(c, decisions(c2_merge=False))
    assert r["recall_after"] == pytest.approx(1.0) and r["merge_pure"] == 1.0 and r["merge_pure_n"] == 1


def test_name_check_auto_and_manual_override():
    c, _ = ctx()
    *_, names = run(c, decisions())
    n = names.set_index("name")
    assert n.loc["time", "majority_gold_attr"] == "Train arrive by" and n.loc["time", "auto_right"] == 0
    assert n.loc["departure", "auto_right"] == 1 and n.loc["junk", "auto_right"] == 0
    assert n.loc["day", "auto_right"] == 1
    t = names.copy()
    t.loc[t["name"] == "time", "manual"] = "1"
    t.loc[t["name"] == "day", "manual"] = "n"
    t = PS.apply_manual(t)
    assert t.set_index("name").loc["time", "right"] == 1 and t.set_index("name").loc["day", "right"] == 0
    assert (t.set_index("name").loc["price", "right"] == 1).all()
    again = PS.apply_manual(names, t)  # a re-run keeps what was filled in
    assert again.set_index("name").loc["time", "manual"] == "1"


def test_jaccard_right_vs_wrong_names():
    c, _ = ctx()
    _, attrs, assign, parts, names = run(c, decisions())
    ids = dict(zip(attrs["name"], attrs["attr_id"]))
    ver = pd.DataFrame({"variant": "full", "run_tag": "r1", "attr_id": [ids["day"], ids["time"], ids["departure"]],
                        "jaccard": [0.5, 0.1, 0.3]})
    r = PS.score_file(decisions(), attrs, assign, parts, c, ver, names)
    assert r["j_right"] == pytest.approx(0.4) and r["j_wrong"] == pytest.approx(0.1)
    assert (r["j_right_n"], r["j_wrong_n"]) == (2, 1)


def test_placement_entity():
    assert PS.placement_entity("current entity (E1)", "E1") == "E1"
    assert PS.placement_entity("relationship(E1, E2)", "E1") == "E1"
    assert PS.placement_entity("sub-entity of E1", "E1") == "E1"
    assert PS.placement_entity("E3: other (top values a, b)", "E1") == "E3"
    assert PS.placement_entity("", "E1") is None


def test_merge_hints_nearest_first():
    c, m = ctx()
    h = PS.merge_hints(m, c.ids, c.x, "E1", k=3)
    assert h["E1#0"][0] == "E1#1" and h["E1#7"][0] == "E1#8" and len(h["E1#0"]) == 3


def test_stability_counts_action_merge_with_and_name_changes():
    a, b = decisions(), decisions(c2_merge=False)
    b.loc[b["cluster_id"] == "E1#3", "name"] = "Arrive"       # case only: same
    b.loc[b["cluster_id"] == "E1#7", "name"] = "cost"         # different
    v, n = PS.stability(a, b)
    assert n == 9 and v == pytest.approx(2 / 9)               # E1#2 (action, merge_with) and E1#7


def test_render_scores_blocks_targets_and_context():
    c, _ = ctx()
    r, *_ = run(c, decisions())
    r2, *_ = run(c, decisions(c2_merge=False))
    md = PS.render_scores({"full r1": r, "full r2": r2, "nocontext r1": r},
                          PS.stability(decisions(), decisions(False)), "E1")
    for h in ("## Merges", "## Splits", "## Noise", "## Placement", "## Train attributes", "## Suggestions",
              "## Verification", "## Comparison", "## Context", "## Stability"):
        assert h in md
    assert "Target: >= 0.8" in md and "Target: <= 2" in md and "FAIL" in md
    assert "| measure | full | nocontext | delta |" in md



# ---------------------------------------------------------------- wf_v3.1: name_merge, generic classes, rubric
def test_name_merge_keeps_instance_exclusivity():
    # (cluster, instance ids of its mentions)
    spec = [("E1#0", ["i1", "i2"]), ("E1#1", ["i3"]), ("E1#2", ["i1"]), ("E1#3", ["i4"]), ("E1#4", ["i5"]),
            ("E1#5", ["i6"]), ("E1#6", ["i7"])]
    m = pd.DataFrame([{"mention_id": 10 * k + j, "cluster_id": c, "entity": "E1", "instance_id": i}
                      for k, (c, ins) in enumerate(spec) for j, i in enumerate(ins)])
    dec = PV.decisions_table([
        obj("E1#0", "Day", "keep", placement="current entity (E1)"),
        obj("E1#1", "day", "keep", placement="Current  entity (E1)"),       # same name + placement, other instance
        obj("E1#2", "day", "keep", placement="current entity (E1)"),        # shares instance i1 with E1#0: no
        obj("E1#3", "day", "keep", placement="sub-entity of E1"),           # other placement: no
        obj("E1#4", "arrive_by", "keep", placement="p"), obj("E1#5", "Arrive by", "keep", placement="p"),
        obj("E1#6", "junk", "not_attribute")], [f"E1#{i}" for i in range(7)], "v2", "r1")
    out = PS.name_merge(dec, m, "E1").set_index("cluster_id")
    assert set(out["variant"]) == {"v2+namemerge"} and len(out) == len(dec)
    assert out["action"].to_dict() == {"E1#0": "merge", "E1#1": "merge", "E1#2": "keep", "E1#3": "keep",
                                       "E1#4": "merge", "E1#5": "merge", "E1#6": "not_attribute"}
    assert json.loads(out.at["E1#0", "merge_with"]) == ["E1#1"] and json.loads(out.at["E1#5", "merge_with"]) == ["E1#4"]
    assert dec.set_index("cluster_id").at["E1#0", "action"] == "keep"  # the input table is untouched


def test_name_merge_keeps_and_extends_the_response_groups():
    m = pd.DataFrame([{"mention_id": k, "cluster_id": c, "entity": "E1", "instance_id": i}
                      for k, (c, i) in enumerate([("E1#0", "i1"), ("E1#1", "i2"), ("E1#2", "i3")])])
    dec = PV.decisions_table([obj("E1#0", "x", "merge", merge_with=["E1#1"], placement="p"),
                              obj("E1#1", "y", "keep", placement="p"), obj("E1#2", "Y", "keep", placement="p")],
                             ["E1#0", "E1#1", "E1#2"], "v1", "r1")
    out = PS.name_merge(dec, m, "E1").set_index("cluster_id")
    assert [json.loads(out.at[c, "merge_with"]) for c in ("E1#0", "E1#1", "E1#2")] == [
        ["E1#1", "E1#2"], ["E1#0", "E1#2"], ["E1#0", "E1#1"]]


TAXI = [("E3#0", "E3", "taxi", "Taxi leave at", 0, 5), ("E3#0", "E3", "taxi", "Taxi arrive by", 1, 5),
        ("E3#1", "E3", "restaurant", "Restaurant food", 2, 3), ("E3#2", "E3", "hotel", "Hotel area", 3, 3),
        ("E3#3", "E3", "taxi", "Taxi leave at", 0, 5), ("E3#3", "E3", "hotel", "Hotel area", 3, 5)]


def taxi_ctx(**kw):
    rows, vec = [], []
    for cid, ent, eg, ga, b, n in TAXI:
        rows += [(cid, ent, eg, ga)] * n
        vec += [np.eye(4)[b]] * n
    m = pd.DataFrame({"mention_id": range(len(rows)), "dialogue_id": "d1", "char_start": [10 * i for i in range(len(rows))],
                      "char_end": [10 * i + 5 for i in range(len(rows))], "cluster_id": [r[0] for r in rows],
                      "entity": [r[1] for r in rows], "entity_gold": [r[2] for r in rows],
                      "gold_attr": [r[3] for r in rows], "norm_value": "v"})
    gv = pd.DataFrame({"dialogue_id": "d1", "gold_attr": m["gold_attr"], "entity_gold": m["entity_gold"],
                       "char_start": m["char_start"], "char_end": m["char_end"], "verbatim": True})
    labels = pd.DataFrame({"cluster_id": ["E3#0", "E3#1", "E3#2", "E3#3"],
                           "label": ["unlabelled", "gold", "gold", "unlabelled"],
                           "gold_attr": ["", "Restaurant food", "Hotel area", ""]})
    ex = pd.DataFrame({"ex_id": ["E3#0:s0", "E3#0:s1", "E3#0:s2"], "cluster_id": "E3#0", "mention_id": [0, 5, 6]})
    attrs = ["Taxi leave at", "Taxi arrive by", "Restaurant food", "Hotel area"]
    return PS.Ctx(m, labels, gv, attrs, m["mention_id"].to_numpy(), np.array(vec, float), ex, "E3",
                  ["restaurant", "taxi"], **kw), m


def test_entity_agnostic_gold_classes_and_split_targets():
    c, _ = taxi_ctx()
    assert c.train == ["Taxi leave at", "Taxi arrive by", "Restaurant food"]  # no Hotel class for restaurant + taxi
    dec = PV.decisions_table([obj("E3#0", "when", "split", placement="current entity (E3)", split=[
        {"name": "leave", "examples": ["E3#0:s0"]}, {"name": "arrive", "examples": ["E3#0:s1", "E3#0:s2"]}]),
        obj("E3#1", "food", "keep"), obj("E3#2", "area", "keep"), obj("E3#3", "leave", "keep")],
        ["E3#0", "E3#1", "E3#2", "E3#3"], "v2", "r1")
    assign, attrs, parts = PV.final_attributes(dec, c.mentions, c.ids, c.x, c.examples, "E3")
    names = PS.name_check_table({("v2", "r1"): (attrs, assign)}, c.mentions, ["restaurant", "taxi"])
    r = PS.score_file(dec, attrs, assign, parts, c, pd.DataFrame(columns=PV.VERIFY_COLS), names)
    # E3#0 mixes two taxi classes (50%) -> target; E3#3 mixes taxi + hotel (hotel is no class of this entity) -> not
    assert (r["split_done"], r["split_done_n"]) == (1.0, 1) and (r["split_side"], r["split_side_n"]) == (1.0, 3)
    assert r["recall_before"] == pytest.approx(1 / 3)  # E3#1 is the only pure class before
    assert r["recall_after"] == pytest.approx(1.0)      # the split makes both taxi classes pure
    assert PS.train_attrs(c.gv, ["Hotel area", "Taxi leave at"], "hotel") == ["Hotel area"]
    assert PS._slot("Taxi arrive by", ["restaurant", "taxi"]) == "arrive by"


def test_split_kinds_option_keeps_the_role_pair_rule():
    c, _ = taxi_ctx(split_kinds=PS.SPLIT_KINDS)
    assert c.split_kinds == PS.SPLIT_KINDS and taxi_ctx()[0].split_kinds is None
    dec = PV.decisions_table([obj("E3#0", "when", "keep")], ["E3#0"], "v2", "r1")
    assign, attrs, parts = PV.final_attributes(dec, c.mentions, c.ids, c.x, c.examples, "E3")
    names = PS.name_check_table({("v2", "r1"): (attrs, assign)}, c.mentions, ["restaurant", "taxi"])
    r = PS.score_file(dec, attrs, assign, parts, c, pd.DataFrame(columns=PV.VERIFY_COLS), names)
    assert (r["split_done"], r["split_done_n"]) == (0.0, 1)  # {leave at, arrive by} is a role pair: still a target, not split


def rubric_inputs():
    c, _ = ctx()
    assign, attrs, parts = PV.final_attributes(decisions(), c.mentions, c.ids, c.x, c.examples, c.entity)
    clusters = pd.DataFrame({"cluster_id": CIDS, "top_values": [f"v{i}|w{i}" for i in range(9)]})
    return c, attrs, assign, clusters


def test_rubric_sheet_columns_values_and_carry_over():
    c, attrs, assign, clusters = rubric_inputs()
    sheet = PS.rubric_sheet({("v2", "r1"): (attrs, assign)}, c.mentions, c.labels, clusters)
    assert list(sheet.columns) == PS.RUBRIC_COLS and len(sheet) == len(attrs)
    assert (sheet[["category", "rater1", "rater2", "final"]] == "").all().all()
    s = sheet.set_index("attr_id")
    assert s.loc["E1#0|E1#1", ["entity", "label", "majority_gold_attr", "top_values"]].tolist() == [
        "E1", "gold", "Train day", "v0|w0"]
    assert s.loc["E1#5", "label"] == "noise" and s.loc["E1#4/0", "majority_gold_attr"] == "Train departure"
    sheet.loc[sheet["attr_id"] == "E1#5", ["rater1", "final"]] = ["noise_marked", "noise_marked"]
    again = PS.rubric_sheet({("v2", "r1"): (attrs, assign)}, c.mentions, c.labels, clusters, old=sheet).set_index("attr_id")
    assert again.loc["E1#5", "final"] == "noise_marked" and again.loc["E1#5", "rater1"] == "noise_marked"
    assert again.loc["E1#6", "final"] == ""


def test_rubric_accuracy_real_vs_noise_and_roles():
    c, attrs, assign, clusters = rubric_inputs()
    sheet = PS.rubric_sheet({("v2", "r1"): (attrs, assign)}, c.mentions, c.labels, clusters)
    fin = {"E1#0|E1#1": "exact", "E1#2|E1#3": "wrong_role", "E1#7": "synonym", "E1#8": "too_general",
           "E1#5": "noise_marked", "E1#6": "noise_named"}  # the E1#4 split parts stay blank: not counted
    sheet["final"] = sheet["attr_id"].map(fin).fillna("")
    r = PS.rubric_accuracy(sheet)[("v2", "r1")]
    assert (r["real_acc"], r["real_n"]) == (0.5, 4)            # exact + synonym of 4 real rows
    assert (r["noise_marked"], r["noise_n"]) == (0.5, 2)
    assert (r["role_acc"], r["role_n"], r["role_wrong"]) == (0.0, 1, 1)  # only the merged leave at / arrive by attr
    assert PS.rubric_accuracy(sheet.assign(final="")) == {}


def test_render_scores_rubric_block_filled_and_not_filled():
    c, attrs, assign, clusters = rubric_inputs()
    res, *_ = run(c, decisions())
    sheet = PS.rubric_sheet({("v2", "r1"): (attrs, assign)}, c.mentions, c.labels, clusters)
    assert "Name rubric" not in PS.render_scores({"v2 r1": res}, None, "E1")           # wf_v3 callers: no block
    assert PS.render_scores({"v2 r1": res}, None, "E1", rubric=sheet).endswith("rubric not filled\n")
    sheet["final"] = sheet["attr_id"].map({"E1#5": "noise_marked", "E1#0|E1#1": "exact"}).fillna("")
    md = PS.render_scores({"v2 r1": res}, None, "E1", rubric=sheet, pair=("v2", "v2_nocontext"), stab_pair=("v2 r1", "r2"))
    assert "## Name rubric" in md and "| v2 r1 | 1.000 | 1 | 1.000 | 1 | n/a | 0 | 0 |" in md
    assert "v2 r1 or v2_nocontext r1 missing." in md and "## Stability (v2 r1 vs r2, report only)" in md
