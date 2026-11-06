import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_signals as S  # noqa: E402
from s1a.graph import _npmi  # noqa: E402

# toy: train instances i1..i4 (docs d1, d1, d2, d3), hotel instance h1 in d1, h2 in d2
# columns: train:1 name (distinct per instance, first), train:2 price (fixed by name), train:3 day (varies)
ROWS = []


def add(mid, dlg, inst, val, turn, cs=0):
    ROWS.append(dict(mention_id=mid, dialogue_id=dlg, instance_id=inst, norm_value=val, turn=turn, char_start=cs))


# instance, train name, price, day
data = [("i1", "d1", "t100", "5", "mon"), ("i2", "d1", "t200", "7", "mon"),
        ("i3", "d2", "t100", "5", "tue"), ("i4", "d3", "t100", "5", "wed")]
mid = 0
N, P, D = [], [], []
for inst, dlg, n, p, d in data:
    add(mid, dlg, inst, n, 0); N.append(mid); mid += 1
    add(mid, dlg, inst, p, 2); P.append(mid); mid += 1
    add(mid, dlg, inst, d, 1); D.append(mid); mid += 1
# a second, different price mention in i1 (several values per instance)
add(mid, "d1", "i1", "9", 3); P.append(mid); mid += 1
H = []
for inst, dlg, v in (("h1", "d1", "ritz"), ("h2", "d2", "ritz")):
    add(mid, dlg, inst, v, 0); H.append(mid); mid += 1
MENT = pd.DataFrame(ROWS)
COLS = {"train": [{"id": 1, "name": "train id", "mention_ids": N},
                  {"id": 2, "name": "price", "mention_ids": P},
                  {"id": 3, "name": "day", "mention_ids": D}],
        "hotel": [{"id": 1, "name": "hotel name", "mention_ids": H}]}


@pytest.fixture(scope="module")
def out():
    return S.compute(COLS, MENT)


def row(out, key):
    return out["columns"].set_index("column_id").loc[key]


def test_npmi_edges():
    assert _npmi(5, 5, 5, 5) == 1.0          # always together
    assert _npmi(2, 4, 4, 8) == pytest.approx(0.0)  # independent
    assert _npmi(1, 4, 4, 8) < 0             # less than chance


def test_counts(out):
    r = row(out, "train:1")
    assert (r.n_mentions, r.n_dialogues, r.n_instances, r.n_distinct) == (4, 3, 4, 2)
    r = row(out, "train:2")
    assert r.n_mentions == 5 and r.n_distinct == 3  # values 5, 7, 9
    assert r.n_multi_value_instances == 1 and r.share_multi_value == pytest.approx(0.25)
    assert r.values_per_instance_mean == pytest.approx(5 / 4)


def test_repetition(out):
    r = row(out, "train:1")  # t100 in 3 instances, t200 in 1
    assert r.n_repeated_values == 1 and r.share_repeated_values == pytest.approx(1 / 2)


def test_name_ordering(out):
    # the hotel name is alone in its entity; in train the id column outranks the repeated-value ones
    assert row(out, "hotel:1").name_rank == 1
    ranks = {k: row(out, k).name_rank for k in ("train:1", "train:2", "train:3")}
    assert sorted(ranks.values()) == [1, 2, 3]
    assert ranks["train:1"] == 1 and row(out, "train:1").name_score == pytest.approx(2 / 3)  # coverage 1 x (0.5 + 0.5 + 1) / 3
    # the name is at turn 0, before price (2) and day (1): first in all 4 instances
    assert row(out, "train:1").n_first == 4
    assert row(out, "train:1").share_first == 1.0


def test_first_share_value():
    assert S.name_score(1.0, 0.0, 1.0, 1.0) == 1.0
    assert S.name_score(2.0, 1.0, 0.0, 1.0) == pytest.approx(1 / 3)  # ratio capped at 1
    assert S.name_score(1.0, 0.0, 1.0, 0.1) == pytest.approx(0.1)  # rare column is discounted


def test_pairs(out):
    p = out["pairs"]
    same = p[(p.scope == "same_entity") & (p.col_a == "train:1") & (p.col_b == "train:2")].iloc[0]
    assert same["count"] == 4 and same["n_units"] == 4 and same["npmi"] == 1.0
    cross = p[p.scope == "cross_entity"]
    c = cross[(cross.col_a == "hotel:1") & (cross.col_b == "train:1")].iloc[0]
    assert c["count"] == 2 and c["n_units"] == 3  # d1, d2 of d1..d3
    assert (p["count"] >= 1).all()


def test_fd_too_few():
    r = S.fd_check(["a", "a"], ["x", "x"])
    assert r["status"] == "too_few" and r["n"] == 2


def test_fd_holds_fails_trivial():
    assert S.fd_check(["a", "a", "b", "b"], ["1", "1", "2", "2"])["status"] == "holds"
    assert S.fd_check(["a", "a", "a", "a"], ["1", "2", "1", "2"])["status"] == "fails"
    assert S.fd_check(["a", "b", "c"], ["1", "1", "1"])["status"] == "trivial"
    r = S.fd_check(["a"] * 10, ["1"] * 9 + ["2"])
    assert r["share"] == pytest.approx(0.9) and r["status"] == "holds"


def test_fd_table(out):
    fd = out["fd"]
    d = fd[(fd.x == "train:1") & (fd.y == "train:2")].iloc[0]
    assert d.n == 4 and d.share == 1.0 and d.status == "holds"  # t100 -> 5, t200 -> 7
    d = fd[(fd.x == "train:2") & (fd.y == "train:3")].iloc[0]
    assert d.status != "holds"  # price 5 -> mon/tue/wed
    assert row(out, "train:1").dependants == 1 and row(out, "train:2").dependants == 1


def test_cross_fd_needs_single_instances(out):
    fd = out["fd"]
    c = fd[(fd.scope == "cross_entity") & (fd.x == "train:1") & (fd.y == "hotel:1")]
    # d1 has two train instances, so only d2 (and no d3 hotel) qualifies: one unit
    assert len(c) == 1 and c.iloc[0].n == 1 and c.iloc[0].status == "too_few"


def test_card_has_counts_and_no_ids(out):
    card = out["cards"]["train:1"]
    assert "4 mentions in 3 dialogues" in card and "2 distinct values" in card
    assert "mentioned first in 4/4 bookings" in card
    assert "fixes 'price' in 4/4 bookings" in card
    assert len(card.split()) <= 60
    assert "train:1" not in card


def test_signal_card_reads_files(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "load_set", lambda s, root=None: (COLS, MENT))
    S._cards.cache_clear()
    assert "mentions in" in S.signal_card("toy", "train:2")
    S._cards.cache_clear()


def test_write_set(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "load_set", lambda s, root=None: (COLS | {"restaurant": []}, MENT))
    S.write_set("toy", tmp_path)
    for f in ("columns.csv", "pairs.csv", "fd.csv", "cards.json", "signals_summary.md"):
        assert (tmp_path / f).exists()
