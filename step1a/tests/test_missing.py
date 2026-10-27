import pandas as pd
import pytest

from s1a.missing import COLUMNS, FIX, cause_of, missing_table


def gold(attr, ent, spans, nonverbatim=0, doc="d1"):
    rows = [dict(dialogue_id=doc, gold_attr=attr, entity_gold=ent, value="v", char_start=s, char_end=e, verbatim=True)
            for s, e in spans]
    rows += [dict(dialogue_id=doc, gold_attr=attr, entity_gold=ent, value="v", char_start=-1, char_end=-1,
                  verbatim=False) for _ in range(nonverbatim)]
    return rows


def mention(mid, s, e, cid, entity, entity_gold):
    return dict(mention_id=mid, dialogue_id="d1", char_start=s, char_end=e, cluster_id=cid, entity=entity,
                entity_gold=entity_gold)


GOLD = pd.DataFrame(
    gold("imp", "train", [(0, 4)], nonverbatim=3)       # 3 of 4 implicit
    + gold("mis", "train", [(100, 104), (110, 114)])                    # no span at all
    + gold("wro", "hotel", [(200, 204), (210, 214)])                    # covered by a train-majority entity
    + gold("mix", "train", [(300, 304), (310, 314)])                    # covered, purity 0.4
    + gold("dil", "train", [(400, 404), (410, 414)])                    # covered, purity 0.1
    + gold("both", "train", [(500, 504)], nonverbatim=4)                # implicit and missed: implicit wins
    + gold("unclus", "train", [(600, 604), (610, 614)]))                # spans exist but unclustered, no best cluster: diluted
MENT = pd.DataFrame([
    # E0 (majority train): clusters E0#0 (holds the hotel attr "wro"), E0#1
    mention(0, 200, 204, "E0#0", "E0", "hotel"), mention(1, 210, 214, "E0#0", "E0", "hotel"),
    mention(2, 700, 704, "E0#0", "E0", "train"), mention(3, 710, 714, "E0#0", "E0", "train"),
    mention(4, 720, 724, "E0#0", "E0", "train"), mention(5, 730, 734, "E0#0", "E0", "train"),
    mention(6, 300, 304, "E0#1", "E0", "train"), mention(7, 310, 314, "E0#1", "E0", "train"),
    mention(8, 400, 404, "E0#1", "E0", "train"), mention(9, 410, 414, "E0#1", "E0", "train"),
    mention(10, 0, 4, "E0#1", "E0", "train"),
    # unclustered spans on "unclus"
    mention(11, 600, 604, "", "E0", ""), mention(12, 610, 614, "", "E0", ""),
])
REC = pd.DataFrame([
    dict(gold_attr="imp", strict=False, best_cluster="E0#1", best_purity=0.1),
    dict(gold_attr="mis", strict=False, best_cluster=float("nan"), best_purity=float("nan")),
    dict(gold_attr="wro", strict=False, best_cluster="E0#0", best_purity=0.3),
    dict(gold_attr="mix", strict=False, best_cluster="E0#1", best_purity=0.4),
    dict(gold_attr="dil", strict=False, best_cluster="E0#1", best_purity=0.1),
    dict(gold_attr="both", strict=False, best_cluster="E0#1", best_purity=0.1),
    dict(gold_attr="unclus", strict=False, best_cluster=float("nan"), best_purity=float("nan")),
    dict(gold_attr="ok", strict=True, best_cluster="E0#1", best_purity=0.9),
])


def test_each_cause_fires_once_and_strict_rows_dropped():
    t = missing_table(MENT, GOLD, REC).set_index("gold_attr")
    assert list(missing_table(MENT, GOLD, REC).columns) == COLUMNS
    assert "ok" not in t.index and len(t) == 7
    assert t.loc["imp", "cause"] == "implicit"
    assert t.loc["mis", "cause"] == "missed"
    assert t.loc["wro", "cause"] == "wrong_entity"
    assert t.loc["mix", "cause"] == "mixed"
    assert t.loc["dil", "cause"] == "diluted"
    # two conditions match (implicit and missed): the first in order wins
    assert t.loc["both", "cause"] == "implicit"
    assert t.loc["unclus", "cause"] == "diluted"  # found by GLiNER, never clustered, no best cluster
    assert t["cause"].value_counts().to_dict() == {"implicit": 2, "missed": 1, "wrong_entity": 1, "mixed": 1, "diluted": 2}


def test_every_row_has_one_cause_and_fix():
    t = missing_table(MENT, GOLD, REC)
    assert t["cause"].isin(FIX).all()
    assert (t["planned_fix"] == t["cause"].map(FIX)).all()


def test_columns_values():
    t = missing_table(MENT, GOLD, REC).set_index("gold_attr")
    w = t.loc["wro"]
    assert (w.gold_entity, w.n_verbatim, w.n_nonverbatim) == ("hotel", 2, 0)
    assert w.gliner_cov == 1.0 and w.cluster_cov == 1.0
    assert (w.best_cluster, w.best_size, w.best_pred_entity, w.best_entity_majority_gold) == ("E0#0", 6, "E0", "train")
    u = t.loc["unclus"]
    assert u.gliner_cov == 1.0 and u.cluster_cov == 0.0 and u.best_cluster == "" and u.best_size == 0
    assert t.loc["imp", "n_nonverbatim"] == 3


@pytest.mark.parametrize("args,cause", [
    ((1, 3, 0.9, "c", 0.1, "x", "y"), "implicit"),
    ((4, 1, 0.2, "c", 0.1, "x", "y"), "missed"),
    ((4, 1, 0.9, "c", 0.1, "x", "y"), "wrong_entity"),
    ((4, 1, 0.9, "c", 0.4, "y", "y"), "mixed"),
    ((4, 1, 0.9, "c", 0.1, "y", "y"), "diluted"),
    ((4, 1, 0.9, "c", 0.6, "y", "y"), "diluted"),  # not reachable with strict == False; falls through
])
def test_cause_of(args, cause):
    assert cause_of(*args) == cause
