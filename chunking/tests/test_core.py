"""Fast tests with a fake encoder (no model download)."""

import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chk import data, embed, methods, metrics  # noqa: E402


class FakeEnc:
    """Bag-of-words vectors: similar words -> similar vectors."""

    def encode(self, texts):
        out = []
        for t in texts:
            v = np.zeros(64, np.float32)
            for w in t.lower().split():
                v[int(hashlib.md5(w.strip(".,?!:").encode()).hexdigest(), 16) % 64] += 1
            out.append(v / (np.linalg.norm(v) or 1))
        return np.stack(out)


def _topic_text(n=40):
    cats = "User: My cat sleeps on the cat bed all day. System: Cats like warm cat beds."
    stocks = "User: The stock market fell and stock prices dropped. System: Stocks often recover."
    return "\n".join([cats] * (n // 2) + [stocks] * (n // 2))


def norm(s):
    return " ".join(s.split())


def test_rsc_limits_and_text_preserved():
    enc = FakeEnc()
    text = _topic_text()
    chunks = methods.rsc(text, enc, embed.langchain_embeddings(enc))
    assert norm(" ".join(chunks)) == norm(text)
    assert all(len(c) <= 2500 for c in chunks)
    assert len(chunks) == 1 or all(len(c) >= 350 for c in chunks)


def test_merge_goes_to_more_similar_neighbour():
    enc = FakeEnc()
    a = "cat cat cat bed " * 30
    b = "stock market price " * 30
    out = methods._merge_short(enc, [a, "cat bed", b], 350)
    assert len(out) == 2 and out[0].endswith("cat bed")
    out = methods._merge_short(enc, [a, "stock price", b], 350)
    assert len(out) == 2 and out[1].startswith("stock price")


def test_presplit_respects_t_max():
    text = "This is one sentence. " * 2000
    assert all(len(s) <= 15_000 for s in methods._presplit(text, 15_000))


def _doc():
    dlg = {"id": "X", "turns": ["User: a b c.", "System: d e.", "User: f g.", "System: h i j."],
           "domains": ["train", "train", "hotel", "hotel"], "queries": {}}
    return data.make_doc("X", [dlg])


def test_align_and_gaps():
    doc = _doc()
    chunks = ["User: a b c. System: d e.", "User: f g.  System: h i j."]  # whitespace changed
    spans, failed = metrics.align(doc.text, chunks)
    assert failed == 0 and spans[1][0] == doc.spans[2][0]
    gaps, inside = metrics.cuts_to_gaps(doc, spans)
    assert gaps == {1} == doc.gold_gaps and inside == 0
    # a cut inside turn 2, nearer its start, snaps to gap 1
    gaps, inside = metrics.cuts_to_gaps(doc, [(0, doc.spans[2][0] + 2), (doc.spans[2][0] + 2, len(doc.text))])
    assert gaps == {1} and inside == 1


def test_perfect_segmentation_scores():
    n, ref = 12, {3, 7}
    pk, wd = metrics.pk_wd(n, ref, ref)
    assert pk == 0 and wd == 0
    assert metrics.prf(*metrics.boundary_counts(ref, ref, 0)) == (1.0, 1.0, 1.0)
    assert metrics.boundary_counts(ref, {4, 7}, 1)[0] == 2
    pk, _ = metrics.pk_wd(n, ref, set())
    assert pk > 0


def test_gold_domains_on_real_dialogue():
    d = {x["id"]: x for x in data.load_dialogues(limit=1000) if x["id"] == "PMUL1270"}["PMUL1270"]
    # train for the first 6 turns, then attraction (swimming pool)
    assert d["domains"][:6] == ["train"] * 6 and d["domains"][6] == "attraction"
    assert set(d["queries"]) == {"train", "attraction"}


def test_stitched_has_dialogue_boundaries():
    dl = data.load_dialogues(limit=40)
    docs = data.stitched_docs(dl, 42)
    assert len(docs) == 2
    for doc in docs:
        for g in range(doc.n_turns - 1):
            if doc.dialogue[g] != doc.dialogue[g + 1]:
                assert g in doc.gold_gaps
        assert doc.text[doc.spans[0][0]:doc.spans[0][1]].startswith("User:")
