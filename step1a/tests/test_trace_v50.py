from s1a import trace_v50 as T


def test_best_picks_passing_group():
    groups = [[["A"], ["B"], ["B"]], [["A"], ["A"]]]
    ok, pur, cov, i = T.best(groups, "A", 3)
    assert ok and i == 1 and pur == 1.0


def test_trace_split_rescues_then_join_loses():
    labels = {1: ["A"], 2: ["A"], 3: ["B"], 4: ["B"], 5: ["B"]}
    cps = {"clusters": {"c": [1, 2, 3, 4, 5]},            # mixed: purity 0.4 -> S3
           "split": {"c/0": [1, 2], "c/1": [3, 4, 5]},    # split rescues A
           "columns": {"x:c/0": [1, 2], "y:c/1": [3, 4, 5]},
           "final": {"x#0": [1, 2, 3, 4, 5]}}             # joined again -> S6
    row = T.trace("A", "e", cps, labels, 2, set())
    assert row["stop"] == "S3" and row["stop_last"] == "S6"


def test_trace_dropped_column_is_s4_s5():
    labels = {1: ["A"], 2: ["A"], 3: ["B"]}
    cps = {"clusters": {"c": [1, 2], "d": [3]}, "split": {"c": [1, 2], "d": [3]},
           "columns": {"y:d": [3]}, "final": {"y#0": [3]}}
    row = T.trace("A", "e", cps, labels, 2, set())
    assert row["stop"] == "S4/S5" and row["columns_kept_share"] == 0.0
