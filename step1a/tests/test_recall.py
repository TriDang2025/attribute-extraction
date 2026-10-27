import pandas as pd
import pytest

from s1a import recall as R

# d1: cluster A = {a, a, a, x}  (a: 3 of 4), cluster B = {b, b;c, "", ""} (b 2/4, c 1/4), cluster C = {s} (1 member)
# d2: cluster A gets one more "a"; cluster D = {a, "", ""}
ROWS = [("d1", "A", "a"), ("d1", "A", "a"), ("d1", "A", "a"), ("d1", "A", "x"),
        ("d1", "B", "b"), ("d1", "B", "b;c"), ("d1", "B", ""), ("d1", "B", ""),
        ("d1", "C", "s"), ("d2", "A", "a"), ("d2", "D", "a"), ("d2", "D", ""), ("d2", "D", ""),
        ("d2", "", "a")]  # last: not clustered
ATTRS = ["a", "b", "c", "s", "x", "z"]


def mentions():
    rows = [dict(mention_id=i, dialogue_id=d, char_start=i * 10, char_end=i * 10 + 5, cluster_id=c, entity="E0",
                 gold_attr=g) for i, (d, c, g) in enumerate(ROWS)]
    return pd.DataFrame(rows)


def gold():
    """Verbatim gold on mention rows: a on 6 (3 in A d1, A d2, D, + unclustered), b 2, c 1, s 1, x 1; z only unfound."""
    pos = {"a": [0, 1, 2, 9, 10, 13], "b": [4, 5], "c": [5], "s": [8], "x": [3]}
    rows = [dict(dialogue_id=ROWS[i][0], gold_attr=a, char_start=i * 10 + 1, char_end=i * 10 + 4, verbatim=True)
            for a, idx in pos.items() for i in idx]
    rows.append(dict(dialogue_id="d1", gold_attr="z", char_start=-1, char_end=-1, verbatim=False))
    return pd.DataFrame(rows)


def test_purity_multiclass_and_unlabelled():
    t = R.purity_table(mentions()).set_index(["cluster_id", "gold_attr"])
    assert t.loc[("A", "a"), "size"] == 5 and t.loc[("A", "a"), "n_class"] == 4
    assert t.loc[("A", "a"), "purity"] == pytest.approx(0.8)
    assert t.loc[("B", "b"), "purity"] == pytest.approx(0.5)  # unlabelled members stay in the denominator
    assert t.loc[("B", "c"), "n_class"] == 1 and t.loc[("B", "c"), "size"] == 4  # b;c counts for both
    assert t.loc[("D", "a"), "purity"] == pytest.approx(1 / 3)
    assert ("", "a") not in t.index  # unclustered rows are ignored


def test_inside_counts():
    s = R.inside_counts(mentions(), gold())
    assert s["a"] == 5 and s["b"] == 2 and s["c"] == 1 and "z" not in s.index  # unclustered a and non-verbatim z out
    g = gold()
    g.loc[len(g)] = dict(dialogue_id="d1", gold_attr="b;x", char_start=1, char_end=4, verbatim=True)  # inside A
    s = R.inside_counts(mentions(), g)
    assert s["b"] == 3 and s["x"] == 2  # a multi-class gold row counts for each class


def test_recall_table_classes():
    t = R.recall_table(mentions(), gold(), ATTRS).set_index("gold_attr")
    assert t.loc["a", ["strict", "recoverable", "present"]].tolist() == [True, True, True]
    assert t.loc["a", "best_cluster"] == "A" and t.loc["a", "n_inside"] == 5
    # b: best purity 0.5 (< 0.6) with 2 inside -> recoverable only
    assert t.loc["b", ["strict", "recoverable", "present"]].tolist() == [False, True, True]
    # c: purity 0.25 but 1 mention inside -> present only
    assert t.loc["c", ["strict", "recoverable", "present"]].tolist() == [False, False, True]
    assert t.loc["c", "n_inside"] == 1 and t.loc["c", "best_purity"] == pytest.approx(0.25)
    # s: exactly 1 mention inside a size-1 cluster, purity 1.0 -> strict by the purity rule
    assert t.loc["s", ["strict", "recoverable", "present"]].tolist() == [True, True, True]
    # x: purity 0.2 (1 of 5), 1 inside -> present only; z: not in any cluster
    assert t.loc["x", ["strict", "recoverable", "present"]].tolist() == [False, False, True]
    assert t.loc["z", ["strict", "recoverable", "present"]].tolist() == [False, False, False]
    assert t.loc["z", "best_cluster"] == "" and t.loc["z", "best_purity"] == 0.0
    assert (t["strict"] <= t["recoverable"]).all() and (t["recoverable"] <= t["present"]).all()


def test_thresholds():
    t = R.recall_table(mentions(), gold(), ATTRS, strict=0.5, min_inside=3).set_index("gold_attr")
    assert t.loc["b", "strict"] and not t.loc["x", "recoverable"]
    t = R.recall_table(mentions(), gold(), ATTRS, recov=0.1, min_inside=1).set_index("gold_attr")
    assert t.loc["x", "recoverable"] and t.loc["c", "recoverable"]


def test_summary():
    m = mentions()
    s = R.summary(m, R.recall_table(m, gold(), ATTRS))
    assert s == dict(K=4, strict=2, recoverable=3, present=5)


def test_bootstrap_ordered_and_in_range():
    m = mentions()
    b = R.bootstrap(m, gold(), ATTRS, n=50, seed=1)
    assert set(b) == {"strict", "recoverable", "present"}
    for lo, hi in b.values():
        assert 0 <= lo <= hi <= max(len(ATTRS), 4)
    assert b["strict"][0] <= b["recoverable"][1] and b["recoverable"][0] <= b["present"][1]
    assert R.bootstrap(m, gold(), ATTRS, n=50, seed=1) == b  # seeded


def test_bootstrap_single_dialogue_is_exact():
    m, g = mentions(), gold()
    m, g = m[m["dialogue_id"] == "d1"], g[g["dialogue_id"] == "d1"]
    t = R.recall_table(m, g, ATTRS)
    b = R.bootstrap(m, g, ATTRS, n=20)
    assert b["strict"] == (t["strict"].sum(), t["strict"].sum())
