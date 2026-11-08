import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import loop2_v41 as L2  # noqa: E402

CFG = dict(k=3, threshold=0.3, min_dialogues=2, min_support=0.05, max_overlap=0.5)


class FakeEnc:
    """Vectors by keyword: 'price' -> axis 0, 'phone' -> axis 1, anything else axis 2 (normalised)."""

    def encode(self, texts):
        out = np.zeros((len(texts), 3))
        for i, t in enumerate(texts):
            out[i, 0 if "price" in t or "pound" in t else 1 if "phone" in t else 2] = 1.0
        return out


def doc(did, turns):
    text, spans, pos = "", [], 0
    for i, t in enumerate(turns):
        line = ("User" if i % 2 == 0 else "System") + ": " + t
        spans.append((pos, pos + len(line)))
        text += line + "\n"
        pos += len(line) + 1
    return SimpleNamespace(doc_id=did, text=text.rstrip("\n"), spans=spans)


DOCS = {
    "D1": doc("D1", ["I need a train", "The price is 12 pounds", "ok", "phone 0123"]),
    "D2": doc("D2", ["hello", "ticket price 9 pounds"]),
    "D3": doc("D3", ["hello there", "nothing here"]),
}


def fake_predict(texts, label, threshold):
    """Spans = a number followed by 'pounds' (label price) or a digit run (label other)."""
    import re
    out = []
    for t in texts:
        pat = r"\d+ pounds" if label == "price" else r"\d{4}"
        out.append([dict(start=m.start(), end=m.end(), score=0.9, text=m.group()) for m in re.finditer(pat, t)])
    return out


INST = pd.DataFrame([("D1|0", "E1", "D1", 0, 3), ("D2|0", "E1", "D2", 0, 1), ("D3|0", "E2", "D3", 0, 1)],
                    columns=["instance_id", "entity", "dialogue_id", "start_turn", "end_turn"])


def mention_table():
    return pd.DataFrame([dict(mention_id=1, dialogue_id="D1", instance_id="D1|0", char_start=0, char_end=3),
                         dict(mention_id=2, dialogue_id="D2", instance_id="D2|0", char_start=0, char_end=1)])


COLUMNS = [dict(name="leaving", mention_ids=[1, 2])]


def lab(label="price", ent="train"):
    return dict(entity=ent, name=label, label=label, description="d " + label, value_type="price")


def test_check_labels_fails_fast():
    L2.check_labels([lab()])
    with pytest.raises(ValueError):
        L2.check_labels([])
    with pytest.raises(ValueError):
        L2.check_labels([{"entity": "x", "name": "n"}])


def test_turn_items_one_per_turn_without_speaker():
    items = L2.turn_items(DOCS)
    assert len(items) == 4 + 2 + 2
    assert items[0] == dict(doc_id="D1", turn=0, start=6, end=20, text="I need a train")


def test_entity_filter_and_retrieve_respect_scope():
    items = L2.turn_items(DOCS)
    vecs = FakeEnc().encode([it["text"] for it in items])
    allowed = L2.entity_turn_filter(INST, "E1")
    assert ("D3", 0) not in allowed and allowed[("D1", 3)] == "D1|0"
    q = FakeEnc().encode(["price: x"])[0]
    hits = L2.retrieve(items, vecs, q, 2, allowed)
    assert [(h["doc_id"], h["turn"]) for h, _ in hits] == [("D1", 1), ("D2", 1)]
    assert len(L2.retrieve(items, vecs, q, 100, None)) == len(items)


def test_run_label_builds_cluster_with_evidence():
    items = L2.turn_items(DOCS)
    vecs = FakeEnc().encode([it["text"] for it in items])
    c = L2.run_label(lab(), 0, DOCS, items, vecs, FakeEnc(), fake_predict, mention_table(), INST, COLUMNS, "E1", 100, CFG)
    assert c["id"] == "L2_train#0" and c["n_mentions"] == 2 and c["n_dialogues"] == 2
    assert [m["mention_id"] for m in c["mentions"]] == [100, 101]
    assert c["mentions"][0]["text"] == "12 pounds" and c["mentions"][0]["norm_value"]
    assert c["evidence"]["support"] == 1.0 and c["evidence"]["cohesion"] == pytest.approx(1.0)
    assert c["value_type"]["dominant"] == "price"
    assert c["keep"] and c["retrieval"]["scope"] == "entity segments"


def test_overlap_marks_not_new_and_drops():
    ms = [dict(dialogue_id="D1", instance_id="D1|0", char_start=0, char_end=5, norm_value="a", score=1.0),
          dict(dialogue_id="D2", instance_id="D2|0", char_start=0, char_end=5, norm_value="b", score=1.0)]
    ev = L2.evidence(ms, ["D1|0", "D2|0"], COLUMNS, mention_table(), FakeEnc())
    assert ev["overlap"] == 1.0 and ev["overlap_column"] == "leaving"
    assert ev["connection"] == {"leaving": 2}
    keep, reason = L2.decide(ev, CFG)
    assert not keep and "overlap" in reason


def test_decide_lists_every_failed_threshold():
    ev = dict(n_dialogues=1, support=0.01, overlap=0.0, overlap_column="")
    keep, reason = L2.decide(ev, CFG)
    assert not keep and "n_dialogues" in reason and "support" in reason and "overlap" not in reason


def test_no_spans_is_dropped_and_support_falls_back_to_dialogues():
    items = L2.turn_items(DOCS)
    vecs = FakeEnc().encode([it["text"] for it in items])
    c = L2.run_label(lab("phone", "hotel"), 3, DOCS, items, vecs, FakeEnc(), lambda t, l, th: [[] for _ in t],
                     mention_table(), INST, [], None, 100, CFG)
    assert c["id"] == "L2_hotel#3" and not c["keep"] and c["reason"] == "no spans"
    assert c["retrieval"]["scope"] == "all turns" and c["evidence"]["support_unit"].startswith("dialogues")


def test_cohesion_range():
    assert L2.cohesion(["a"], FakeEnc()) is None
    assert L2.cohesion(["price a", "phone b"], FakeEnc()) == pytest.approx(0.0)


def test_outputs_render():
    items = L2.turn_items(DOCS)
    vecs = FakeEnc().encode([it["text"] for it in items])
    c = L2.run_label(lab(), 0, DOCS, items, vecs, FakeEnc(), fake_predict, mention_table(), INST, COLUMNS, "E1", 100, CFG)
    rows = L2.evidence_rows([c])
    assert rows[0]["id"] == "L2_train#0" and rows[0]["keep"]
    md = L2.summary_md([c], "dev50", CFG, "labels.json", 1.0)
    assert "min_support=0.05" in md and "| train | 1 | 1 | 0 |" in md
