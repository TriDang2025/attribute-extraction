import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import combos, combos23, fold  # noqa: E402
from s1a import paths  # noqa: E402, F401
from s1a import value_types as VT  # noqa: E402
from test_cue import FakeEnc  # noqa: E402
from chk.data import make_doc  # noqa: E402


@dataclass
class Sp:
    doc_id: str
    text: str
    start: int
    end: int
    turn: int


def _doc_spans():
    turns = ["User: I need a train from Cambridge please.", "User: it should go to London.",
             "User: leave at 9:00, 8.08GBP", "User: arrive by 10:00"]
    doc = make_doc("D1", [{"id": "a", "turns": turns, "domains": ["train"] * 4}])
    spans = []
    for t, s in ((0, "Cambridge"), (1, "London"), (2, "9:00"), (2, "8.08GBP"), (3, "10:00")):
        pos = doc.text.find(s)
        spans.append(Sp("D1", s, pos, pos + len(s), t))
    return {"D1": doc}, spans


def test_value_types_moved_and_reexported():
    from s1a import checks_v35 as CK
    assert CK.value_type_v35 is VT.value_type_v35
    assert VT.value_type_v35("8.08GBP") == "price" and VT.value_type_v35("105 minutes") == "duration"


def test_span_lefts():
    docs, spans = _doc_spans()
    out = combos23.span_lefts(spans, docs)
    assert out[0] == ["a", "train", "from"] and out[1] == ["should", "go", "to"]   # speaker prefix not included
    assert out[2][-1] == "at"


def test_type_fn_default_unchanged_and_used():
    docs, spans = _doc_spans()
    groups, books = [0] * len(spans), [("D1", 0)] * len(spans)
    seen = []

    def tf(t):
        seen.append(t)
        return "x"

    old = combos.V21.cluster_fn(spans, docs, FakeEnc(), groups, books)[1]
    same = combos._v("t", type_fn=None).cluster_fn(spans, docs, FakeEnc(), groups, books)[1]
    assert old == same and not seen
    combos._v("t", type_fn=tf).cluster_fn(spans, docs, FakeEnc(), groups, books)
    assert len(seen) == len(spans)
    fold.cluster_fn(spans, docs, FakeEnc(), groups, books, min_size=2, type_fn=tf)
    assert len(seen) >= 2 * len(spans)


def test_v23_variants_registered_and_split():
    assert set(combos23.CONFIGS) == {"V23", "V23_NOJ"}
    docs, spans = _doc_spans()
    # one cluster: J splits it by the cue words; the spans with no cue word go to the unknown part
    old = combos23._FOLD
    combos23._FOLD = lambda *a, **k: (None, ["c"] * len(spans))
    try:
        _, lab = combos23.cluster_fn(spans, docs, FakeEnc(), [0] * len(spans), [])
    finally:
        combos23._FOLD = old
    # Cambridge: from (start); London: to (end); 9:00 and 8.08GBP: none; 10:00: by (end)
    assert lab == [("c", 0), ("c", 1), ("c", 2), ("c", 2), ("c", 1)]
    assert [s["unknown"] for s in combos23.LAST_SPLIT] == [2]
