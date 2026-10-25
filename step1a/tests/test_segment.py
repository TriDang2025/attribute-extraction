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


def test_turn_pieces_one_per_turn_contiguous():
    doc = _doc()
    sp = S.turn_pieces(doc)
    _check(doc, sp)
    assert len(sp) == doc.n_turns
    assert [s for s, _ in sp[1:]] == [s for s, _ in doc.spans[1:]]


def test_boundary_ci_contains_point():
    from chk.metrics import boundary_counts, cuts_to_gaps, prf
    from s1a import metrics as M
    docs = {"D1": _doc()}
    starts = [s for s, _ in docs["D1"].spans]
    n = len(docs["D1"].text)
    sp = {"D1": [(0, starts[2]), (starts[2], n)]}
    lo, hi = M.boundary_ci(docs, sp, n_boot=50)
    tp, h, r = boundary_counts(docs["D1"].gold_gaps, cuts_to_gaps(docs["D1"], sp["D1"])[0], 0)
    assert lo <= prf(tp, h, r)[2] <= hi


def test_ent2_scores_equal_single_label_bcubed():
    from types import SimpleNamespace
    from hbe.metrics import external
    from s1a import metrics as M
    gold_l = ["hotel", "hotel", "train", "taxi", "train", "hotel"]
    pred = [0, 0, 1, 1, 1, 0]
    us = [SimpleNamespace(labels=frozenset({g})) for g in gold_l]
    p, r, f = M.ent2_scores(us, {42: pred})
    e = external(gold_l, pred)
    assert np.allclose([p, r, f], [e["bcubed_precision"], e["bcubed_recall"], e["bcubed_f1"]])


def test_plug_in_parse_seg_turn():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import plug_in
    assert plug_in.parse_seg("turn,0.4,on,on") == ("turn", 0.4, True, True)
    assert plug_in.seg_key(*plug_in.parse_seg("turn,0.40,on,on")) == "turn_m40"
    assert plug_in.parse_seg("10/50,none,off,on")[0] == (10, 50)
