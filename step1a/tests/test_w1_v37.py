import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import a_s012_v37 as AS  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import columns_v37 as CV  # noqa: E402
from s1a import exit_v37 as EX  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import stability_v37 as ST  # noqa: E402
from s1a import v34_data as D  # noqa: E402

TRAIN = ["Train departure", "Train destination", "Train leave at", "Train arrive by", "Train price", "Train id",
         "Train fee", "Train day", "Train time"]


def toy(clusters, variants=None, train=TRAIN, level=2):
    """EntityData at `level` from clusters {cluster_id: [gold attr, ...]} ("" = no label: a noise mention at v1.1)."""
    rows, mid = [], 0
    for cid, golds in clusters.items():
        for g in golds:
            rows.append({"mention_id": str(mid), "cluster_id": cid, "gold_attr": g, "entity_gold": "train" if g else "",
                         "is_choice": False, "is_request": False, "norm_value": f"v{mid}", "text": f"v{mid}"})
            mid += 1
    m = pd.DataFrame(rows)
    ctx = SimpleNamespace(train=list(train), entity="E1")
    return D.EntityData("train", "E1", ["train"], sorted(clusters), m, pd.DataFrame(), ctx, ctx, variants or {}, {}, {},
                        level=level)


def variant(ed, groups, marked=(), names=None, split=()):
    """VariantOut: groups {cluster_id: group id}; marked = group ids with status not_attribute."""
    assign = {int(r["mention_id"]): groups[r["cluster_id"]] for _, r in ed.mentions.iterrows() if r["cluster_id"] in groups}
    ids = sorted(set(groups.values()))
    attrs = pd.DataFrame({"attr_id": ids, "name": [(names or {}).get(g, g) for g in ids],
                          "clusters": [";".join(c for c, x in groups.items() if x == g) for g in ids],
                          "status": ["not_attribute" if g in marked else "keep" for g in ids],
                          "source": ["split" if g in split else "keep" for g in ids], "description": ""})
    dec = pd.DataFrame({"cluster_id": list(groups), "action": ["not_attribute" if groups[c] in marked else "keep"
                                                               for c in groups]})
    return D.VariantOut(dec, attrs, assign, {})


CLUSTERS = {
    "c1": ["Train leave at"] * 6 + ["Train arrive by"] * 6,                # mixed roles at Step 1a
    "c2": ["Train price"] * 4,                                            # recoverable
    "c3": ["Train time"] * 3 + [""] * 7,                                  # diluted: 3 of 10 labelled, rest noise
    "c4": ["Train id"] * 6, "c5": ["Train fee"] * 6,                       # recoverable, merged wrongly by A r1
    "c6": ["Train departure"] * 10, "c7": ["Train destination"] * 10,     # recoverable, merged by A r1: role partner
}


def test_rules_v11():
    r = SR.Rules.parse("v1.1")
    assert r.noise_kind == "mwoz" and r == SR.Rules.v1_1()
    assert SR.Rules.default().noise_kind == "pattern" and SR.Rules.parse("default").noise_kind == "pattern"
    assert SR.Rules.parse("v1.1,found=cov25").found == "cov25"
    assert SR.Rules.v1_1() == SR.Rules(**{**SR.DEFAULT, "noise_kind": "mwoz"})
    with pytest.raises(ValueError):
        SR.Rules.parse("v9")


def test_ceiling_table_reasons_and_counts():
    ed = toy(CLUSTERS)
    t = CE.ceiling_table({"train": ed}, 2).set_index("attr")
    assert list(t["present"]) == [True, True, True, True, True, True, True, False, True]
    rec = set(t.index[t["recoverable"]])
    assert rec == {"Train price", "Train id", "Train fee", "Train departure", "Train destination"}
    assert t.loc["Train price", "best_cluster"] == "c2" and t.loc["Train price", "best_coverage"] == 1.0
    assert t.loc["Train day", "step1a_reason"] == "never_found" and t.loc["Train day", "best_cluster"] == ""
    assert t.loc["Train leave at", "step1a_reason"] == "mixed_roles" and t.loc["Train leave at", "top_other"] == "Train arrive by"
    assert t.loc["Train arrive by", "step1a_reason"] == "mixed_roles"
    assert t.loc["Train time", "step1a_reason"] == "diluted"  # 3 of 10 mentions: noise mentions count under v1.1
    assert (t.loc[t["recoverable"], "step1a_reason"] == "").all()
    c = CE.ceiling_counts(t.reset_index().assign(ent="train")).set_index("ent").loc["total"]
    assert (c["n"], c["present"], c["recoverable"], c["never_found"], c["mixed_roles"], c["diluted"]) == (9, 8, 5, 1, 2, 1)


def test_ceiling_needs_level_data():
    with pytest.raises(ValueError):
        CE.ceiling_table({"train": toy(CLUSTERS, level=1)}, 2)


def test_ceiling_is_the_found_rule_on_identity_decisions():
    ed = toy(CLUSTERS)
    ident = CE.identity_variant(ed)
    assert set(ident.assign.values()) == set(CLUSTERS) and (ident.attrs["status"] == "keep").all()
    assert len(ident.dec) == 0


def with_variants(ed, **variants):
    """ed with the variants {label: VariantOut}; labels with "_" for the space ("A_r1" -> "A r1")."""
    return replace(ed, variants={k.replace("_", " "): v for k, v in variants.items()})


def loss_data():
    ed = toy(CLUSTERS)
    r1 = variant(ed, {"c1": "g1", "c2": "g2", "c3": "g3", "c4": "g45", "c5": "g45", "c6": "g67", "c7": "g67"}, marked={"g2"})
    r2 = variant(ed, {"c1": "g1", "c2": "g2", "c3": "g3", "c4": "g4", "c5": "g5", "c6": "g6", "c7": "g7"})
    return with_variants(ed, A_r1=r1, A_r2=r2)


def test_loss_table_stages():
    ed = loss_data()
    ceil = CE.ceiling_table({"train": ed}, 2)
    loss = CE.loss_table({"train": ed}, ceil, ("A r1", "A r2")).set_index(["attr", "variant"])
    # A r2 keeps every recoverable cluster apart: it finds all five recoverable attributes; A r1 loses all five
    assert loss.loc[("Train price", "A r1"), "stage"] == "Step 3" and loss.loc[("Train price", "A r1"), "reason"] == "marked_not_attribute"
    assert loss.loc[("Train price", "A r2"), "found"] and loss.loc[("Train price", "A r2"), "stage"] == ""
    assert loss.loc[("Train price", "A r2"), "missed_orders"] == "1/2"
    assert loss.loc[("Train id", "A r1"), "reason"] == "merged_wrongly" and loss.loc[("Train id", "A r1"), "group"] == "g45"
    assert loss.loc[("Train id", "A r1"), "group_purity"] == 0.5
    assert loss.loc[("Train departure", "A r1"), "reason"] == "mixed_roles"
    assert loss.loc[("Train departure", "A r1"), "top_other"] == "Train destination"
    # Step 1a losses are the ceiling's: both orders miss the mixed cluster's attributes
    for v in ("A r1", "A r2"):
        assert loss.loc[("Train leave at", v), "stage"] == "Step 1a" and loss.loc[("Train leave at", v), "reason"] == "mixed_roles"
        assert loss.loc[("Train time", v), "reason"] == "diluted" and loss.loc[("Train leave at", v), "missed_orders"] == "2/2"
    assert ("Train day", "A r1") in loss.index  # present False: never_found, a Step 1a loss
    assert loss.loc[("Train day", "A r1"), "reason"] == "never_found"
    md = CE.loss_md(loss.reset_index(), ("A r1", "A r2"), ceil)
    assert "Step 3: merged_wrongly" in md and "Step 1a: never_found" in md
    assert "Set: dev50" in CE.ceiling_md(ceil)


def test_loss_split_and_not_in_response():
    ed = toy({"c2": ["Train price"] * 4, "c3": ["Train id"] * 4})
    v = variant(ed, {"c2": "c2/0", "c3": "c2/0"}, split={"c2/0"})  # an impure split part: price is not found
    ed = with_variants(ed, A_r1=v, A_r2=variant(ed, {}))
    loss = CE.loss_table({"train": ed}, CE.ceiling_table({"train": ed}, 2), ("A r1", "A r2"))
    r = loss[(loss["attr"] == "Train price")].set_index("variant")
    assert r.loc["A r1", "reason"] == "split" and r.loc["A r2", "reason"] == "not_in_response"


def columns_data():
    ed = toy({"c1": ["Train price"] * 4, "c2": ["Train price"] * 4, "c3": ["Train id"] * 5, "c4": ["Train fee"] * 5,
              "c5": ["Train fee"] * 5})
    v = variant(ed, {"c1": "g1", "c2": "g2", "c3": "g3", "c4": "g4", "c5": "g5"}, marked={"g5"},
                names={"g1": "price", "g2": "Price", "g3": "train_id", "g4": "fee", "g5": "fee_x"})
    return with_variants(ed, A_r1=v)


def test_dup_columns():
    ed = columns_data()
    rules = CE.rules_v11(2)
    rows = CV.dup_rows(ed, "A r1", rules, {}).set_index("attr")
    assert rows.loc["Train price", "n_columns"] == 1 and rows.loc["Train price", "n_groups"] == 2  # "price" = "Price"
    assert rows.loc["Train id", "n_columns"] == 1
    assert rows.loc["Train fee", "n_columns"] == 1 and rows.loc["Train fee", "columns"] == "fee"  # g5 is marked
    s = CV.dup_summary(rows.reset_index())
    assert s == {"found": 3, "mean": 1.0, "max": 1, "dup": 0}
    assert CV.n_columns(ed, "A r1") == 3
    ed2 = with_variants(ed, A_r1=variant(ed, {"c1": "g1", "c2": "g2", "c3": "g3", "c4": "g4", "c5": "g5"},
                                         names={"g1": "price", "g2": "cost", "g3": "id", "g4": "fee", "g5": "fee"}))
    rows2 = CV.dup_rows(ed2, "A r1", rules, {}).set_index("attr")
    assert rows2.loc["Train price", "n_columns"] == 2 and rows2.loc["Train price", "columns"] == "cost | price"
    assert rows2.loc["Train fee", "n_columns"] == 1  # two groups, one name
    assert "Train price" in CV.dup_md(rows2.reset_index(), ["A r1"])


def test_stability_sides_and_flips():
    ed = toy({"c1": ["Train departure"] * 6 + ["Train destination"] * 6, "c2": ["Train departure"] * 5,
              "c3": ["Train destination"] * 5})
    both = variant(ed, {"c1": "g1", "c2": "g1", "c3": "g3"})     # c1 sits with the departures
    other = variant(ed, {"c1": "g3", "c2": "g2", "c3": "g3"})    # c1 sits with the destinations
    marked = variant(ed, {"c1": "g1", "c2": "g1", "c3": "g3"}, marked={"g1"})
    ed = with_variants(ed, C_s0=both, C_s1=both, C_s2=other, M_s0=marked)
    two = ST.two_role(ed)
    assert two == {"c1": ("departure", "destination")}
    ids = {"c1": [int(i) for i in ed.mentions.index[ed.mentions["cluster_id"] == "c1"]]}
    assert ST.sides(ed, "C s0", ids["c1"], two["c1"]) == frozenset({"departure"})
    assert ST.sides(ed, "C s2", ids["c1"], two["c1"]) == frozenset({"destination"})
    assert ST.sides(ed, "M s0", ids["c1"], two["c1"]) == frozenset({"other"})  # marked group
    f = ST.role_flips(ed, "C", two, ids)
    assert list(f["flips"]) == [2] and f.loc[0, "s2"] == "destination" and f.loc[0, "pair"] == "departure/destination"
    assert "1/1" in ST.stability_md({"C": {"agree_groups": 1.0, "agree_noise": 1.0, "agree_names": 1.0}}, {"C": f})
    assert list(ST.with_seed_decs(ed, "C").seed_decs) == ["C s0", "C s1", "C s2"]


def runs_toy():
    ok = {"found": 20, "recoverable": 20, "found_recoverable": 19, "found_not_recoverable": 1, "noise_n": 13, "noise_marked": 9,
          "marked_n": 12, "marked_noise": 9, "columns_per_found": 1.2}
    return {"r0": ok, "r1": {**ok, "found": 21, "found_recoverable": 18, "noise_marked": 8},
            "r2": {**ok, "found": 22, "columns_per_found": 1.3}, "v": {**ok, "found_recoverable": 17}}


def test_exit_bar():
    runs = runs_toy()
    assert EX.verdicts(runs["r0"]) == {"a": True, "b": None, "c": True, "d": True}  # 0.95, 1.2, 9 caught at 0.75
    t = EX.bar_rows(runs, {"A": ["r0", "r1", "r2"], "V": ["v"]}).set_index("run")
    a = t.loc["A"]
    assert a["found_total"] == "20-22" and a["b_range"] == 2 and not a["b_pass"]
    assert a["a_found_recoverable"] == "18-19" and a["a_pass"]  # the worst order (18/20 = 0.9) just passes
    assert not a["c_pass"] and not a["d_pass"]                      # r2 has 1.3 columns, r1 catches 8
    v = t.loc["V"]
    assert v["b_pass"] is None and not v["a_pass"] and v["c_pass"] and v["d_pass"]
    md = EX.exit_md(t.reset_index(), runs, ["a note"])
    assert "pending the baseline" in md and "FAIL" in md and "n/a" in md


def test_exit_run_metrics_and_found_set():
    ed = toy({"c2": ["Train price"] * 4})
    ed = with_variants(ed, A_r1=variant(ed, {"c2": "g2"}))
    found = EX.found_set(ed, "A r1", CE.rules_v11(2), {})
    assert found == {("train", "Train price")}
    ceil = CE.ceiling_table({"train": ed}, 2)
    noise = pd.Series({"noise_n": 13, "noise_marked": 9, "marked_n": 10, "marked_noise": 9})
    m = EX.run_metrics(found, ceil, noise, 1.0)
    assert m["found"] == 1 and m["recoverable"] == 1 and m["found_recoverable"] == 1 and m["noise_marked"] == 9


def test_a_s012_decision_and_table():
    base = {"found": "10 + 10 + 10", "found_n": 30, "gold_n": 40, "noise_n": 13, "marked_n": 12, "marked_noise": 9,
            "marked_real": 1, "names_right": 25, "names_base": 40, "names_unrated": 0, "columns": 50}
    rows = [{"variant": v, **base, "noise_marked": 9} for v in ("A r1", "A r2", "A s2")]
    rows.append({"variant": "A s012", **base, "noise_marked": 9})
    rows.append({"variant": "AE s012", **base, "noise_marked": 10})
    t = pd.DataFrame(rows, columns=AS.COLS)
    keep, text = AS.decision(t)
    assert keep and "KEEP AE" in text
    keep, text = AS.decision(t.assign(found_n=[30, 30, 30, 30, 29]))      # AE finds fewer attributes: drop
    assert not keep and "DROP AE" in text
    keep, _ = AS.decision(t.assign(noise_marked=9))                       # no more noise caught: drop
    assert not keep
    md = AS.a_s012_md(t, ["x"])
    assert "A, 3 orders (range)" in md and "| A s012 |" in md and "| AE s012 |" in md and "**Decision: KEEP AE.**" in md
    t2 = t.assign(names_unrated=[0, 0, 0, 3, 0])
    assert "[3 unrated]" in AS.a_s012_md(t2)


def test_summary_rows():
    ents = ["train", "hotel", "restaurant"]
    df = pd.DataFrame({"variant": "A s012", "ent": ents, "found_n": [10, 12, 14], "gold_n": [10, 14, 16]})
    l2r = pd.DataFrame({"variant": "A s012", "ent": ents, "name_right": [5, 6, 7], "name_base": [10, 14, 16],
                        "names_unrated": [0, 1, 0]})
    nz = pd.DataFrame({"variant": "A s012", "ent": ents, "noise_n": [4, 6, 3], "noise_marked": [3, 4, 1], "marked_n": [5, 5, 3],
                       "marked_noise": [3, 4, 1], "marked_real": [0, 1, 2], "marked_mixed": [0, 0, 0]})
    t = AS.summary_rows(df, l2r, nz, {"A s012": 40}, ["A s012", "AE s012"])
    r = t.iloc[0]
    assert len(t) == 1 and r["found"] == "10 + 12 + 14" and r["found_n"] == 36 and r["noise_marked"] == 8 and r["noise_n"] == 13
    assert r["names_right"] == 18 and r["names_unrated"] == 1 and r["marked_real"] == 3 and r["columns"] == 40


def test_merge_variants_and_add_a_s012(monkeypatch):
    ed = toy({"c2": ["Train price"] * 4})
    v = variant(ed, {"c2": "g"})
    e34 = {"train": with_variants(ed, A_r1=v, A_r2=v)}
    e36 = {"train": with_variants(ed, A_s2=v)}
    m = AS.merge_variants(e34, e36)
    assert set(m["train"].variants) == {"A r1", "A r2", "A s2"}
    seen = {}
    monkeypatch.setattr(AS.PC, "vote", lambda decs: (pd.DataFrame({"cluster_id": ["c2"]}), {"agree_mean": 1.0}) if seen.setdefault("n", len(decs)) else None)
    monkeypatch.setattr(AS.V36, "_add", lambda variants, label, dec, e, ctx, entity: variants.update({label: v, "A+namemerge s012": v}))
    out = AS.bundle_with_a_s012(SimpleNamespace(e=None), e34, e36)
    assert seen["n"] == 3 and set(out["train"].variants) == {"A s2", "A s012", "A+namemerge s012"}
    assert set(e36["train"].variants) == {"A s2"}  # the input bundle is not changed


def test_read_l2_rated_v36_plus_v37(tmp_path):
    d36, d37 = tmp_path / "v36", tmp_path / "v37"
    d36.mkdir()
    d37.mkdir()
    key = lambda rows: pd.DataFrame(rows, columns=["row", "ent", "name", "description", "majority_gold_attr", "variants", "n_variants"])  # noqa: E731
    key([[0, "train", "a", "", "Train price", "", 1], [1, "train", "b", "", "Train id", "", 1]]).to_csv(d36 / RN.L2_KEY_FILE, index=False)
    for f, labels in zip(RN.L2_FILES, (["right", "partly"], ["right", "wrong"])):
        pd.DataFrame({"row": [0, 1], "label": labels}).to_csv(d36 / f, index=False)
    assert AS.read_l2_rated(tmp_path / "none", d37) is None
    base = AS.read_l2_rated(d36, d37).set_index("name")["label"].to_dict()
    assert base == {"a": "right", "b": "wrong"}  # lower label wins
    key([[2, "train", "c", "", "Train fee", "", 1]]).to_csv(d37 / AS.NAMES_V37_KEY, index=False)
    for f in AS.NAMES_V37_FILES:
        pd.DataFrame({"row": [2], "label": ["partly"]}).to_csv(d37 / f, index=False)
    both = AS.read_l2_rated(d36, d37).set_index("name")["label"].to_dict()
    assert both == {"a": "right", "b": "wrong", "c": "partly"}


def test_unrated_names_and_sheet_rows():
    rated = pd.DataFrame([["train", "price", "", "Train price", "right"]], columns=RN.JOIN_KEYS + ["label"])
    rows = pd.DataFrame({"variant": ["A s012"] * 2, "ent": "train", "name": ["price", "fee"], "description": "",
                         "majority_gold_attr": ["Train price", "Train fee"], "top_values": "x"})
    seen = set(map(tuple, rated[RN.JOIN_KEYS].values))
    assert [tuple(r) in seen for r in rows[RN.JOIN_KEYS].values] == [True, False]
    rater, key = AS.sheet_files(rows.iloc[1:], pd.DataFrame({"row": ["0", "229"]}), {"Train fee": "train-fee"}, {"train-fee": "the fee"})
    assert list(rater["row"]) == [230] and list(key["row"]) == [230] and rater.loc[0, "l2_slot_description"] == "the fee"
    assert "variant" not in rater.columns and "variants" in key.columns
