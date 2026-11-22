import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_pick_v49 as PK  # noqa: E402


def col(src):
    return {"name": "c", "source": src}


def canon(*tables):
    return {"tables": [{"name": n, "columns": [col(s) for s in srcs]} for n, srcs in tables], "unused": []}


def toy(**over):
    """Variants X, Y, Z, two sets, three seeds, all passing; over = {variant: {column: value}} overrides on every row of the variant."""
    rows = []
    for v, f1 in (("X", 0.6), ("Y", 0.7), ("Z", 0.5)):
        for dev in ("d1", "d2"):
            for s in range(3):
                rows.append({"variant": v, "set": dev, "seed": s, "finished": True, "tables": 5, "internet_hotel": True,
                             "parking_hotel": True, "placed": 0.9, "table_f1": f1, "grouping_f1": 0.5, **over.get(v, {})})
    return pd.DataFrame(rows)


def test_hotel_table():
    c = canon(("hotel", ["acc:1", "acc:2", "food:3"]), ("food", ["food:1", "food:2", "acc:9"]), ("tie", ["acc:5", "food:5"]))
    assert PK.main_entity(c["tables"][0]) == "acc" and PK.main_entity(c["tables"][2]) is None
    assert PK.in_hotel_table(c, {"acc:2"}, {"acc"})
    assert not PK.in_hotel_table(c, {"acc:9"}, {"acc"})        # sits in the food table
    assert not PK.in_hotel_table(c, {"acc:5"}, {"acc"})        # tied table
    assert not PK.in_hotel_table(c, {"acc:77"}, {"acc"})       # missing / unused


def test_all_pass_and_tie_break_by_f1_sum():
    chosen, res = PK.pick(toy())
    assert chosen == "Y" and abs(res["Y"]["score"] - 2.4) < 1e-9


def test_collapse_fails():
    chosen, res = PK.pick(toy(Y={"tables": 2}))
    assert chosen == "X" and not res["Y"]["rule1"][0] and "collapse" in res["Y"]["rule1"][1]


def test_one_bad_seed_is_enough():
    df = toy()
    df.loc[(df.variant == "Y") & (df.set == "d2") & (df.seed == 1), "internet_hotel"] = False
    chosen, res = PK.pick(df)
    assert chosen == "X" and "d2 s1: internet not in a hotel table" in res["Y"]["rule1"][1]


def test_placed_gap_over_005_fails_and_equal_005_passes():
    chosen, res = PK.pick(toy(Y={"placed": 0.84}, X={"placed": 0.9}, Z={"placed": 0.86}))
    assert chosen == "X" and not res["Y"]["rule2"][0] and res["Z"]["rule2"][0]
    chosen, _ = PK.pick(toy(Y={"placed": 0.85}))
    assert chosen == "Y"


def test_not_run_fails_and_none_when_all_fail():
    df = toy()
    df = df[~((df.variant == "Y") & (df.set == "d1") & (df.seed == 2))]
    chosen, res = PK.pick(df)
    assert chosen == "X" and "d1 s2: not finished / not run" in res["Y"]["rule1"][1]
    assert PK.pick(toy(X={"tables": 1}, Y={"tables": 1}, Z={"tables": 1}))[0] is None
