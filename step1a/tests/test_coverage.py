from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from s1a.coverage import coverage_table, value_coverage

T0 = "User: book a train"
T1 = "System: train at five"
D1 = T0 + "\n" + T1
D2 = "User: hi"
DOCS = {
    "d1": {"text": D1, "turns": [[0, len(T0)], [len(T0) + 1, len(D1)]]},
    "d2": {"text": D2, "turns": [[0, len(D2)]]},
}


def span(text, word, nth=0):
    s = -1
    for _ in range(nth + 1):
        s = text.index(word, s + 1)
    return s, s + len(word)


def mention(mid, did, turn, word, nth, cid, entity, inp="spans", inst=None):
    s, e = span(DOCS[did]["text"], word, nth)
    return dict(mention_id=mid, input=inp, dialogue_id=did, turn=turn, char_start=s, char_end=e, text=word,
                cluster_id=cid, entity=entity, instance_id=inst or f"{did}|0")


def gold(did, word, nth, ent, verbatim=True):
    s, e = span(DOCS[did]["text"], word, nth) if verbatim else (-1, -1)
    return dict(dialogue_id=did, gold_attr="a", entity_gold=ent, value=word, char_start=s, char_end=e, verbatim=verbatim)


GOLD = pd.DataFrame([gold("d1", "train", 0, "train"), gold("d1", "five", 0, "hotel"),
                     gold("d1", "book", 0, "train"), gold("d1", "yes", 0, "train", False)])


def spans_export():
    m = pd.DataFrame([mention(0, "d1", 0, "train", 0, "E0#0", "E0"),
                      mention(1, "d1", 1, "five", 0, "E0#1", "E0")])
    inst = pd.DataFrame([dict(instance_id="d1|0", entity="E0", dialogue_id="d1", start_turn=0, end_turn=1),
                         dict(instance_id="d2|0", entity="E0", dialogue_id="d2", start_turn=0, end_turn=0)])
    return SimpleNamespace(mentions=m, instances=inst)


def test_spans_overall_and_entity():
    t = coverage_table(spans_export(), DOCS, GOLD)
    a = t.loc["all"]
    assert a.n_words == 7 and a.n_words_cov == 2 and a.word_cov == pytest.approx(2 / 7)
    assert a.value_cov == pytest.approx(2 / 3)  # non-verbatim ignored
    assert a.turn_cov == pytest.approx(2 / 3)
    assert a.instance_cov == pytest.approx(1 / 2)
    e = t.loc["E0"]
    assert e.word_cov == pytest.approx(2 / 7) and e.instance_cov == pytest.approx(1 / 2)
    assert np.isnan(e.value_cov)  # no gold value has entity_gold "E0"


def test_cluster_ids_restriction():
    t = coverage_table(spans_export(), DOCS, GOLD, cluster_ids=["E0#0"])
    a = t.loc["all"]
    assert a.word_cov == pytest.approx(1 / 7) and a.value_cov == pytest.approx(1 / 3)
    assert a.turn_cov == pytest.approx(1 / 3)
    assert value_coverage(spans_export().mentions, GOLD, ["E0#0"]) == pytest.approx(1 / 3)
    assert value_coverage(spans_export().mentions, GOLD) == pytest.approx(2 / 3)


def test_partial_overlap_counts():
    m = pd.DataFrame([mention(0, "d1", 0, "a trai", 0, "E0#0", "E0")])  # covers "a", partly "train"
    assert value_coverage(m, GOLD) == pytest.approx(1 / 3)  # overlaps gold "train"
    ex = SimpleNamespace(mentions=m, instances=spans_export().instances)
    assert coverage_table(ex, DOCS, GOLD).loc["all", "n_words_cov"] == 2  # "a" and "train"


def test_gold_entities_use_gold_turns():
    m = pd.DataFrame([mention(0, "d1", 0, "train", 0, "train#0", "train", "gold", "d1|train"),
                      mention(1, "d1", 1, "five", 0, "hotel#0", "hotel", "gold", "d1|hotel")])
    inst = pd.DataFrame([dict(instance_id="d1|train", entity="train", dialogue_id="d1", start_turn=0, end_turn=1),
                         dict(instance_id="d1|hotel", entity="hotel", dialogue_id="d1", start_turn=0, end_turn=1)])
    t = coverage_table(SimpleNamespace(mentions=m, instances=inst), DOCS, GOLD)
    tr, ho = t.loc["train"], t.loc["hotel"]
    assert tr.n_words == 3 and tr.n_words_cov == 1 and tr.turn_cov == 1.0  # turn 0 only
    assert tr.value_cov == pytest.approx(1 / 2)  # train hit, book missed
    assert ho.n_words == 3 and ho.word_cov == pytest.approx(1 / 3) and ho.value_cov == 1.0
