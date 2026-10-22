import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import segment as S  # noqa: E402
from chk.data import make_doc  # noqa: E402


def _doc():
    dlg = {"id": "D1",
           "turns": ["User: I need a taxi from cambridge.",
                     "System: Sure, where to?",
                     "User: Also a train to cambridge on monday.",
                     "System: TR1 leaves at 10:00."],
           "domains": ["taxi", "taxi", "train", "train"]}
    return make_doc("D1", [dlg])


def _check(doc, sp):
    assert sp[0][0] == 0 and sp[-1][1] == len(doc.text)
    assert all(a[1] == b[0] for a, b in zip(sp, sp[1:]))
    assert all(doc.text[s:e].strip() for s, e in sp)


def test_snap_moves_cut_to_nearest_turn_start():
    doc = _doc()
    starts = [s for s, _ in doc.spans]
    n = len(doc.text)
    c1 = starts[1] + 3          # just after turn 1 starts -> turn 1 start
    c2 = starts[3] - 2          # end of turn 2 -> turn 3 start
    sp = S.snap_to_turns(doc, [(0, c1), (c1, c2), (c2, n)])
    _check(doc, sp)
    assert [s for s, _ in sp] == [0, starts[1], starts[3]]


def test_snap_tie_goes_earlier_and_dedupes():
    doc = _doc()
    starts = [s for s, _ in doc.spans]
    mid = (starts[1] + starts[2]) / 2
    assert mid == int(mid)  # exact tie in this toy doc
    mid = int(mid)
    sp = S.snap_to_turns(doc, [(0, mid - 1), (mid - 1, mid), (mid, len(doc.text))])
    _check(doc, sp)
    assert sp == [(0, starts[1]), (starts[1], len(doc.text))]


def test_snap_drops_cut_at_text_start():
    doc = _doc()
    sp = S.snap_to_turns(doc, [(0, 2), (2, len(doc.text))])
    assert sp == [(0, len(doc.text))]


class FakeEnc:
    """Pieces mentioning 'train' get vector (0, 1), others (1, 0) -> cos 1 within a kind, 0 across."""
    def encode(self, texts):
        return np.array([[0.0, 1.0] if "train" in t else [1.0, 0.0] for t in texts])


def test_merge_keywords_vs_similarity_only():
    text = "a taxi here. b taxi there. c train now."
    i = text.index("b"), text.index("c")
    spans = [(0, i[0]), (i[0], i[1]), (i[1], len(text))]
    enc = FakeEnc()
    # pieces 1 and 2 are similar and share keywords -> merge either way
    assert S.merge_adjacent(text, spans, enc, 0.5) == [(0, i[1]), (i[1], len(text))]
    assert S.merge_adjacent(text, spans, enc, 0.5, use_keywords=False) == [(0, i[1]), (i[1], len(text))]
    # similar but the second adds a new entity word
    t2 = "a taxi here. b cab there."
    j = t2.index("b")
    sp2 = [(0, j), (j, len(t2))]

    class Same:
        def encode(self, texts):
            return np.ones((len(texts), 2)) / np.sqrt(2)

    t3 = "a taxi here. b hotel there."
    k = t3.index("b")
    sp3 = [(0, k), (k, len(t3))]
    assert S.merge_adjacent(t3, sp3, Same(), 0.5) == sp3
    assert S.merge_adjacent(t3, sp3, Same(), 0.5, use_keywords=False) == [(0, len(t3))]
    assert S.merge_adjacent(t2, sp2, Same(), None) == sp2
