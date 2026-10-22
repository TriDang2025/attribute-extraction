import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import paths  # noqa: E402,F401
from s1a import spacy_spans as SS  # noqa: E402
from chk.data import make_doc  # noqa: E402


def _doc():
    dlg = {"id": "D1", "turns": ["User: I need a cheap hotel.", "System: The Alpha has 5 rooms."],
           "domains": ["hotel", "hotel"]}
    return make_doc("D1", [dlg])


def test_offset_mapping_with_prefix():
    doc = _doc()
    bodies = SS.turn_bodies(doc.text, doc.spans)
    assert [b for _, b in bodies] == ["I need a cheap hotel.", "The Alpha has 5 rooms."]
    off, body = bodies[1]
    s, e = SS.to_dialogue(off, body.index("5"), body.index("5") + 1)
    assert doc.text[s:e] == "5"


def test_strip_determiner():
    t = "a cheap hotel"
    assert SS.strip_determiner(t, 0, len(t)) == (2, len(t))
    t = "The Alpha"
    assert t[slice(*SS.strip_determiner(t, 0, len(t)))] == "Alpha"
    t = "hotel"
    assert SS.strip_determiner(t, 0, 5) == (0, 5)


def test_pronoun_drop():
    for t in ("it", "That", "the one", "you"):
        assert SS.strip_determiner(t, 0, len(t)) is None


def test_union_longest_wins_and_dedup():
    a = [[0, 5, "gliner", 0.9], [10, 12, "gliner", 0.8]]
    b = [[0, 9, "spacy:np", ""], [3, 6, "spacy:ner", ""], [10, 12, "spacy:num", ""], [20, 25, "spacy:np", ""]]
    out = SS.union(a, b)
    assert [x[:3] for x in out] == [[0, 9, "spacy:np"], [10, 12, "gliner"], [20, 25, "spacy:np"]]


def test_cache_round_trip(tmp_path):
    doc = _doc()
    p = tmp_path / "s.jsonl"
    s = doc.text.index("cheap hotel")
    spans = [[s, s + 5, "ner", "X"], [s, s + 11, "np", ""]]
    p.write_text(json.dumps({"doc_id": "D1", "spans": spans}) + "\n", encoding="utf-8")
    us = SS.load_spacy_cache(p, {"D1": doc})
    assert [(u.text, u.tag, u.score, u.kind) for u in us] == [("cheap hotel", "np", 1.0, "span")]
    us = SS.load_spacy_cache(p, {"D1": doc}, dedup=False, sources={"ner"})
    assert [u.text for u in us] == ["cheap"]
