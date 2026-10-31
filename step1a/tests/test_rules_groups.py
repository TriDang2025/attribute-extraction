import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import rules_groups as RG  # noqa: E402
from s1a.score_rules import Rules  # noqa: E402

PAIRS = [("departure", "destination")]


def make_ed(rows, assign, dec_rows=(), train=("Train departure", "Train destination", "Train price"),
            entity_gold_of=None, names=None):
    """rows: (mention_id, cluster_id, gold_attr, entity_gold, class); assign {mention_id: attr_id}."""
    m = pd.DataFrame([r[:4] for r in rows], columns=["mention_id", "cluster_id", "gold_attr", "entity_gold"])
    classes = pd.Series([r[4] for r in rows], index=[r[0] for r in rows])
    attrs = pd.DataFrame({"attr_id": sorted(set(assign.values()))})
    attrs["name"] = [(names or {}).get(a, a) for a in attrs["attr_id"]]
    dec = pd.DataFrame(list(dec_rows), columns=["cluster_id", "action", "placement"])
    vo = SimpleNamespace(assign=assign, attrs=attrs, dec=dec)
    ctx = SimpleNamespace(train=list(train),
                          entity_gold_of=entity_gold_of or {"E1": "train", "E0": "hotel"})
    ed = SimpleNamespace(ent="train", entity="E1", gold_ents=["train"], mentions=m, variants={"v": vo}, ctx_r=ctx)
    return ed, {"classes": classes, "pairs": PAIRS}


def rows_of(cluster, attr, n, start, cls=None, ent="train"):
    return [(start + i, cluster, attr, ent, cls or attr or "unlabeled") for i in range(n)]


def test_found_cov10_drops_single_mention():
    # price: 1 mention alone in g1 (pure, 1 of 15 = 7% coverage); the other 14 sit in gx with 26 departures (impure)
    rows3 = rows_of("c1", "Train price", 1, 0) + rows_of("c9", "Train departure", 12, 10)
    rows3 += [(100 + i, "c2", "Train price", "train", "Train price") for i in range(14)]
    assign3 = {r[0]: "g1" if r[1] == "c1" else "g9" if r[1] == "c9" else "gx" for r in rows3}
    # price mentions: 1 alone in g1 (pure), 14 in gx mixed with 26 departures -> 14/40 impure
    rows3 += [(200 + i, "c2", "Train departure", "train", "Train departure") for i in range(26)]
    assign3.update({200 + i: "gx" for i in range(26)})
    ed3, extra3 = make_ed(rows3, assign3)
    d0 = RG.found(ed3, "v", Rules(found="cov0"), extra3).set_index("attr")
    d10 = RG.found(ed3, "v", Rules(found="cov10"), extra3).set_index("attr")
    assert d0.loc["Train price", "found"] and d0.loc["Train price", "best_group"] == "g1"
    assert not d10.loc["Train price", "found"] and d10.loc["Train price", "case"] == "tiny_pure"
    assert d0.loc["Train price", "case"] == ""


def test_found_cases_and_old_equals_cov0():
    # departure spread over two pure groups (3 + 3 of 6): cov25 finds both groups at 50%; destination only mixed
    rows = rows_of("c1", "Train departure", 3, 0) + rows_of("c2", "Train departure", 3, 10)
    rows += rows_of("c3", "Train destination", 2, 20) + rows_of("c3", "Train price", 3, 30)
    assign = {r[0]: r[1] for r in rows}
    ed, extra = make_ed(rows, assign)
    d = RG.found(ed, "v", Rules(found="cov25"), extra).set_index("attr")
    assert d.loc["Train departure", "found"]
    assert not d.loc["Train destination", "found"] and d.loc["Train destination", "case"] == "mixed_only"
    assert d.loc["Train price", "found"]  # 3 of 5, purity exactly 0.6
    # spread: pure groups too small a share of the attribute
    rows = rows_of("c1", "Train departure", 2, 0) + rows_of("c2", "Train departure", 2, 10)
    rows += rows_of("c3", "Train departure", 2, 20) + rows_of("c4", "Train departure", 2, 30)
    rows += rows_of("c5", "Train departure", 2, 40)
    ed, extra = make_ed(rows, {r[0]: r[1] for r in rows})
    d = RG.found(ed, "v", Rules(found="cov25"), extra).set_index("attr")
    assert not d.loc["Train departure", "found"] and d.loc["Train departure", "case"] == "spread"
    old = RG.found(ed, "v", Rules(found="old"), extra)
    cov0 = RG.found(ed, "v", Rules(found="cov0"), extra)
    assert old.equals(cov0)


def test_found_unlabeled_excluded_from_denominator():
    rows = rows_of("c1", "Train price", 3, 0) + rows_of("c1", "", 4, 10)
    assign = {r[0]: "g" for r in rows}
    ed, extra = make_ed(rows, assign)
    assert not RG.found(ed, "v", Rules(found="cov0", unlabeled="old"), extra).set_index("attr").loc["Train price", "found"]
    assert RG.found(ed, "v", Rules(found="cov0", unlabeled="exclude"), extra).set_index("attr").loc["Train price", "found"]


def merge_ed(a_attr, b_attr, noise=0, n=10):
    rows = rows_of("c1", a_attr, n, 0) + rows_of("c2", b_attr, n, 100)
    rows += [(500 + i, "c2", "", "train", "noise") for i in range(noise)]
    return make_ed(rows, {r[0]: "g" for r in rows}, names={"g": "Merged"})


def test_merge_right_and_wrong_role_and_wrong_attr():
    ed, extra = merge_ed("Train price", "Train price")
    df = RG.merges(ed, "v", Rules(merge="n20"), extra)
    assert len(df) == 1 and bool(df["right"].iloc[0]) and df["reason"].iloc[0] == "" and df["name"].iloc[0] == "Merged"
    ed, extra = merge_ed("Train departure", "Train destination")
    row = RG.merges(ed, "v", Rules(merge="n20"), extra).iloc[0]
    assert not row["right"] and row["reason"] == "wrong_role" and row["member_roles"] == "departure;destination"
    ed, extra = merge_ed("Train departure", "Train price")
    assert RG.merges(ed, "v", Rules(merge="n20"), extra).iloc[0]["reason"] == "wrong_attr"


def test_merge_noise_threshold():
    ed, extra = merge_ed("Train price", "Train price", noise=5)  # 5 of 25 = 0.20
    assert RG.merges(ed, "v", Rules(merge="n30"), extra).iloc[0]["right"]
    row = RG.merges(ed, "v", Rules(merge="n20"), extra).iloc[0]
    assert not row["right"] and row["reason"] == "noise"
    ed, extra = merge_ed("Train price", "Train price", noise=2)  # 2 of 22 = 0.09
    assert RG.merges(ed, "v", Rules(merge="n10"), extra).iloc[0]["right"]


def test_merges_skip_single_cluster_groups():
    rows = rows_of("c1", "Train price", 3, 0) + rows_of("c2", "Train price", 3, 10)
    ed, extra = make_ed(rows, {r[0]: r[1] for r in rows})
    assert RG.merges(ed, "v", Rules(), extra).empty


def test_placement_majority_and_baseline():
    # c1 mostly hotel mentions, c2 train; decisions: c1 -> E0 (right), c2 -> E0 (wrong), c3 -> current (stay)
    rows = rows_of("c1", "Hotel area", 3, 0, ent="hotel") + rows_of("c1", "Train price", 1, 10)
    rows += rows_of("c2", "Train price", 4, 20) + rows_of("c3", "Train departure", 2, 30)
    dec = [("c1", "keep", "E0"), ("c2", "keep", "E0"), ("c3", "keep", "current entity E1"), ("c4", "", "E0")]
    ed, extra = make_ed(rows, {r[0]: r[1] for r in rows}, dec)
    r = RG.placement(ed, "v", Rules(placement="majority"), extra)
    assert r["place_n"] == 3 and abs(r["place_acc"] - 2 / 3) < 1e-9 and abs(r["place_base"] - 2 / 3) < 1e-9


def test_placement_booking_reference_per_entity():
    rows = rows_of("c1", "Hotel confirmed reference", 2, 0, ent="hotel") + rows_of(
        "c1", "Train confirmed reference", 3, 10, ent="train")
    dec = [("c1", "keep", "E0")]
    ed, extra = make_ed(rows, {r[0]: r[1] for r in rows}, dec)
    r = RG.placement(ed, "v", Rules(), extra)  # majority is train, but one reference attribute per entity: E0 is right
    assert r["place_acc"] == 1.0 and r["place_n"] == 1


def test_q_tables_run():
    rows = rows_of("c1", "Train price", 3, 0) + rows_of("c1", "Hotel area", 1, 10, ent="hotel")
    ed, extra = make_ed(rows, {r[0]: "g" for r in rows}, [("c1", "keep", "E1")])
    data = {"train": ed}
    q5 = RG.q5_table(data, Rules(), extra, labels=("v",))
    assert {"found_cov0", "found_cov25", "case_cov10"} <= set(q5.columns) and len(q5) == 3
    assert RG.q6_table(data, Rules(), extra, labels=("v",)).empty
    q9 = RG.q9_table(data)
    assert q9["n_other"].tolist() == [1] and q9["top_other_attr"].tolist() == ["Hotel area"]


def test_merge_with_no_gold_member_is_wrong():
    from s1a import rules_groups as RG
    assert RG._merge_reason({"Train day"}, {"Train day": "day"}, set(), 0.0, 0.2, no_gold=True) == "no_gold_member"
    assert RG._merge_reason({"Train day"}, {"Train day": "day"}, set(), 0.0, 0.2) == ""


def test_merge_with_no_gold_member_is_wrong():
    slots = {"Train day": "day"}
    assert RG._merge_reason({"Train day"}, slots, set(), 0.0, 0.2, no_gold=True) == "no_gold_member"
    assert RG._merge_reason({"Train day"}, slots, set(), 0.0, 0.2) == ""
