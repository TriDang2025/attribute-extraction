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
