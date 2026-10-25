import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import gold as G  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import units as U  # noqa: E402
from chk.data import make_doc  # noqa: E402

CFG = {"normalize": True, "alpha": 0.5, "by_type": True, "linkage": "average", "t": 0.45,
       "cannot_link": True}
TABLE = {"headers": ["Train destination", "Train day", "Hotel stars"],
         "rows": [[["cambridge"], ["monday"], ["4"]]]}


class FakeEnc:
    """Deterministic 16-d vectors per text; no model."""

    def encode(self, texts):
        out = []
        for t in texts:
            seed = int(hashlib.sha1(t.encode()).hexdigest()[:8], 16)
            out.append(np.random.RandomState(seed).randn(16))
        x = np.array(out, dtype=np.float32).reshape(len(texts), 16)
        return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-9)


def doc():
    dlg = {"id": "D1",
           "turns": ["User: I need a train to (cambridge) on monday, please.",
                     "System: Which time would you like to leave?",
                     "User: Also a hotel for 2 nights, \"quiet\" one."],
           "domains": ["train", "train", "hotel"]}
    return make_doc("D1", [dlg])


def mention(d, text, label, turn, verbatim=True, value=None):
    s = d.text.index(text) if verbatim else -1
    e = s + len(text) if verbatim else -1
    return G.Mention("mention", d.doc_id, label, text, s, e, turn, labels=frozenset({label}),
                     raw_labels=frozenset({label}), verbatim=verbatim, value=value or text.lower())


def span(d, text, turn, score=0.9):
    s = d.text.index(text)
    u = U.Unit("span", d.doc_id, "", text, s, s + len(text), turn)
    u.score = score
    return u


def segment(d, t0, t1):
    s, e = d.spans[t0][0], d.spans[t1][1]
    return U.Unit("chroma", d.doc_id, "", d.text[s:e], s, e)


def toy_inputs(d):
    ms = [mention(d, "cambridge", "Train destination", 0), mention(d, "monday", "Train day", 0),
          mention(d, "4", "Hotel stars", -1, verbatim=False)]
    spans = [span(d, "cambridge", 0), span(d, "monday", 0), span(d, "2 nights", 2, 0.6)]
    segs = [segment(d, 0, 0), segment(d, 1, 1), segment(d, 2, 2)]
    return MN.Inputs(mentions=ms, tables={"D1": TABLE}, spans=spans, segs=segs, cfg_spans=CFG, cfg_gold=CFG)


def test_left_word_and_context_strip_speaker():
    d = doc()
    t0 = d.text.index("(cambridge)") + 1
    assert MN.left_word(d, 0, t0) == "to"           # "(" is punctuation of the mention's own token
    assert MN.left_word(d, 0, d.text.index("I need")) == ""  # first word after "User:"
    assert MN.left_word(d, 2, d.text.index("2 nights")) == "for"
    s = d.text.index("monday")
    ctx = MN.context(d, 0, s, s + 6)
    assert ctx == "I need a train to (cambridge) on monday, please."
    assert "User" not in ctx
    k = MN.context(d, 0, s, s + 6, k=2)
    assert k == "(cambridge) on monday, please."


def test_context_stays_inside_turn():
    d = doc()
    s = d.text.index("Which")
    ctx = MN.context(d, 1, s, s + 5)
    assert ctx == "Which time would you like to leave?" and "train" not in ctx


def test_cluster_id_format():
    ids = MN.cluster_ids(["E2", "E2", "E0", "E2", ""], ["a", "b", "x", "a", "y"])
    assert ids == ["E2#0", "E2#1", "E0#0", "E2#0", ""]


def test_build_gold():
    d = doc()
    e = MN.build("gold", {"D1": d}, FakeEnc(), inp=toy_inputs(d))
    m = e.mentions
    assert list(m.mention_id) == [0, 1] and set(m.input) == {"gold"}
    assert all(re.fullmatch(r"train#\d+", c) for c in m.cluster_id)
    assert list(m.entity) == list(m.entity_gold) == ["train", "train"]
    assert set(m.instance_id) == {"D1|train"} and set(m.gliner_score) == {1.0}
    assert list(m.gold_attr) == ["Train destination", "Train day"]
    assert list(m.norm_value) == ["cambridge", "monday"]
    assert e.x.shape == (2, 16) and np.allclose(np.linalg.norm(e.x, axis=1), 1, atol=1e-5)
    assert list(e.ids) == [0, 1]
    # the hotel instance has no verbatim mention but is in the table
    inst = e.instances.set_index("instance_id")
    assert set(inst.index) == {"D1|train", "D1|hotel"}
    assert (inst.loc["D1|hotel", "start_turn"], inst.loc["D1|hotel", "end_turn"]) == (2, 2)
    assert (inst.loc["D1|train", "start_turn"], inst.loc["D1|train", "end_turn"]) == (0, 1)
    assert e.clusters.n_mentions.sum() == 2


def test_build_spans_instances_without_mentions():
    d = doc()
    e = MN.build("spans", {"D1": d}, FakeEnc(), seed=7, inp=toy_inputs(d))
    m = e.mentions
    assert list(m.text) == ["cambridge", "monday", "2 nights"]
    assert all(re.fullmatch(r"E\d", x) for x in m.entity)
    assert all(re.fullmatch(r"E\d#\d+", c) and c.split("#")[0] == ent for c, ent in zip(m.cluster_id, m.entity))
    assert list(m.instance_id) == ["D1|0", "D1|0", "D1|2"]
    assert list(m.gold_attr) == ["Train destination", "Train day", ""]
    assert list(m.entity_gold) == ["train", "train", ""]
    assert list(m.gliner_score) == [0.9, 0.9, 0.6]
    assert list(m.left_word) == ["to", "on", "for"]
    # segment 1 (turn 1) holds no span but is still an instance
    inst = e.instances.set_index("instance_id")
    assert list(inst.index) == ["D1|0", "D1|1", "D1|2"]
    assert (inst.loc["D1|1", "start_turn"], inst.loc["D1|1", "end_turn"]) == (1, 1)
    assert set(inst.entity) <= {f"E{i}" for i in range(5)}
    assert e.x.shape == (3, 16)


def test_build_spans_subset_of_docs():
    d = doc()
    inp = toy_inputs(d)
    inp.spans.append(U.Unit("span", "OTHER", "", "x", 0, 1, 0))
    e = MN.build("spans", {"D1": d}, FakeEnc(), inp=inp)
    assert set(e.mentions.dialogue_id) == {"D1"}


def test_save_load_round_trip(tmp_path):
    d = doc()
    e = MN.build("spans", {"D1": d}, FakeEnc(), inp=toy_inputs(d))
    e.mentions.loc[0, "text"] = 'a, "quoted"\nvalue'
    e.mentions.loc[0, "context"] = ""
    MN.save(e, tmp_path / "spans")
    r = MN.load(tmp_path / "spans")
    assert r.mentions.equals(e.mentions) and r.clusters.equals(e.clusters) and r.instances.equals(e.instances)
    assert r.mentions.mention_id.dtype.kind == "i" and r.mentions.gliner_score.dtype.kind == "f"
    assert np.array_equal(r.ids, e.ids) and np.allclose(r.x, e.x) and r.x.dtype == np.float32
    assert b"\r" not in (tmp_path / "spans" / "mentions.csv").read_bytes()


def test_shared_round_trip(tmp_path):
    d = doc()
    inp = toy_inputs(d)
    MN.save_shared(tmp_path, {"D1": d}, inp.mentions, {"Train destination": "Train destination",
                                                       "Hotel name": "Hotel name",
                                                       "Hotel confirmed name": "Hotel name"})
    docs, gv, attrs = MN.load_shared(tmp_path)
    assert docs["D1"].text == d.text and docs["D1"].spans == d.spans
    assert list(gv.verbatim) == [True, True, False] and list(gv.char_start)[2] == -1
    assert list(gv.entity_gold) == ["train", "train", "hotel"]
    assert attrs == ["Hotel name", "Train destination"]


def test_unknown_input():
    d = doc()
    with pytest.raises(ValueError):
        MN.build("nope", {"D1": d}, FakeEnc(), inp=toy_inputs(d))
