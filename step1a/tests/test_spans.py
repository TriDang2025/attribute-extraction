import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from s1a import spans as SP  # noqa: E402


def doc_of(turns):
    text, spans = "", []
    for i, t in enumerate(turns):
        if i:
            text += "\n"
        spans.append((len(text), len(text) + len(t)))
        text += t
    return SimpleNamespace(doc_id="d", text=text, spans=spans)


def test_generic_unchanged_and_hand_size(monkeypatch):
    def boom():
        raise AssertionError("gold_slot_labels called")
    monkeypatch.setattr(SP, "gold_slot_labels", boom)
    assert SP.LABEL_SETS["generic"] == ["place", "time", "date", "day", "number", "price", "name", "duration"]
    hand = SP.LABEL_SETS["hand"]
    assert len(hand) == 19 and hand[:8] == SP.LABELS and len(set(hand)) == 19
    assert set(SP.LABEL_SETS) == {"generic", "hand", "gold"}


def test_gold_labels_from_levels():
    schema = json.loads((SP.paths.TEAR_DATA / "levels.json").read_text(encoding="utf-8"))["full_schema"]
    slots = SP.gold_slot_labels()
    assert len(slots) == len(set(slots)) < len(schema)
    assert "leave at" in slots and "requested people" in slots and "price range" in slots
    gold = SP.LABEL_SETS["gold"]
    assert gold[:8] == SP.LABELS and len(gold) == len(set(gold))
    assert set(slots) <= set(gold)


def test_turn_windows_offsets():
    doc = doc_of(["User: I need a train to Ely.", "System: Sure, when?", "User: Friday"])
    wins = SP.turn_windows(doc)
    assert [doc.text[a:b] for a, b in wins] == ["I need a train to Ely.", "Sure, when?", "Friday"]


def test_turn_windows_long_turn_cut():
    body = " ".join(f"w{i}" for i in range(25))
    doc = doc_of(["User: " + body, "System: ok"])
    wins = SP.turn_windows(doc, max_words=10)
    texts = [doc.text[a:b] for a, b in wins]
    assert texts[:3] == [" ".join(f"w{i}" for i in range(j, min(j + 10, 25))) for j in (0, 10, 20)]
    assert " ".join(texts[:3]) == body and texts[3] == "ok"


def test_extract_windows_maps_offsets():
    doc = doc_of(["User: go to Ely", "System: ok"])

    class Model:
        def inference(self, texts, labels, threshold, batch_size):
            return [[{"text": "Ely", "start": t.index("Ely"), "end": t.index("Ely") + 3,
                      "label": "place", "score": 0.9}] if "Ely" in t else [] for t in texts]
    out = SP.extract_windows(Model(), doc, SP.turn_windows(doc), ["place"], 0.3)
    assert len(out) == 1 and out[0].text == "Ely" and out[0].tag == "place" and out[0].score == 0.9
    assert doc.text[out[0].start:out[0].end] == "Ely"


def test_cache_round_trip(tmp_path):
    import gliner_labels as GL
    path = tmp_path / "gliner_turn_hand.jsonl"
    GL.append_cache(path, "d1", [[1, 4, "place", 0.8]])
    GL.append_cache(path, "d2", [])
    assert GL.read_cache(path) == {"d1": [[1, 4, "place", 0.8]], "d2": []}
    assert GL.read_cache(tmp_path / "none.jsonl") == {}
