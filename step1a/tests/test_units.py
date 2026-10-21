import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import units as U  # noqa: E402
from chk.data import make_doc  # noqa: E402


def _doc():
    dlg = {"id": "D1",
           "turns": ["User: I need a taxi from cambridge.",
                     "System: Sure, where to?",
                     "User: Also a train to cambridge on monday.",
                     "System: TR1 leaves at 10:00."],
           "domains": ["taxi", "taxi", "train", "train"]}
    return make_doc("D1", [dlg])


def test_locate_prefers_entity_turn():
    doc = _doc()
    s, e = U.locate(doc, "cambridge", "train")
    assert doc.text[s:e] == "cambridge" and U.turn_of(doc, s) == 2
    s, _ = U.locate(doc, "Cambridge", "taxi")
    assert U.turn_of(doc, s) == 0


def test_locate_word_boundary_and_missing():
    doc = _doc()
    assert U.locate(doc, "mon", "train") is None
    assert U.locate(doc, "friday", "train") is None


def test_value_units_counts():
    doc = _doc()
    table = {"headers": ["Taxi departure", "Train destination", "Train day", "Train leave at"],
             "rows": [[["cambridge"], ["cambridge"], ["monday"], ["11:00"]]]}
    units, missing = U.value_units(doc, table)
    assert len(units) == 3 and missing == 1
    assert [u.turn for u in units] == [0, 2, 2]
    assert U.value_text(doc, units[2], "window").count("[monday]") == 1
    assert U.value_text(doc, units[2], "turn").startswith("monday | User:")


def test_oracle_segments_and_majority():
    doc = _doc()
    segs = U.oracle_segments(doc)
    assert [s.label for s in segs] == ["taxi", "train"]
    assert segs[1].text.startswith("User: Also")
    assert U.majority(["a", "b", "b"]) == "b"


def test_chroma_units_label_by_overlap():
    doc = _doc()
    cut = doc.text.index("User: Also")
    units = U.chroma_units(doc, [doc.text[:cut], doc.text[cut:]])
    assert [u.label for u in units] == ["taxi", "train"]


# ------------------------------------------------------------------ entity segmentation
import numpy as np  # noqa: E402

from s1a import segment as S  # noqa: E402
from s1a import spans as SP  # noqa: E402


class _Enc:
    """Same vector for every text: every adjacent pair is maximally similar."""
    def encode(self, texts):
        return np.ones((len(texts), 2)) / np.sqrt(2)


def test_entity_words():
    assert S.entity_words("Book a taxi to the guesthouse") == {"taxi", "hotel"}
    assert S.entity_words("Thanks, bye") == set()


def test_merge_blocks_new_entity_word():
    text = "I need a train to London.\nIt leaves at 10:00.\nAlso book me a taxi."
    a, b = text.index("It"), text.index("Also")
    spans = [(0, a), (a, b), (b, len(text))]
    assert S.merge_adjacent(text, spans, _Enc(), 0.8) == [(0, b), (b, len(text))]
    assert S.merge_adjacent(text, spans, _Enc(), None) == spans


def test_piece_spans_cover_text():
    doc = _doc()
    chunks = [doc.text[:doc.spans[2][0]], doc.text[doc.spans[2][0]:]]
    sp = S.piece_spans(doc, chunks)
    assert sp[0][0] == 0 and sp[-1][1] == len(doc.text) and sp[1][0] == doc.spans[2][0]


def test_windows_cut_at_lines():
    text = "a b c\nd e\nf g h"
    w = SP.windows(text, 0, len(text), max_words=5)
    assert [text[s:e] for s, e in w] == ["a b c\nd e", "f g h"]


def test_span_match_overlap_once():
    doc = _doc()
    vals, _ = U.value_units(doc, {"headers": ["Train day"], "rows": [[["monday"]]]})
    s = doc.text.index("monday")
    sp = [U.Unit("span", "D1", "", "on monday", s - 3, s + 6),
          U.Unit("span", "D1", "", "monday", s, s + 6)]
    assert SP.match(sp, vals) == 1
    assert [u.label for u in sp] == ["Train day", ""]
