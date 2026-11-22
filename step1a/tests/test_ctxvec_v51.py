from types import SimpleNamespace

import numpy as np

from s1a import ctxvec_v51 as CV
from s1a import fold


class FakeEnc:
    """Context texts (they hold the value mask "<<") get one vector per cue word, every value string the same vector."""

    def encode(self, texts):
        out = []
        for t in texts:
            v = np.array([0.0, 1.0, 0.0]) if "<<" in t and "from" in t else np.array([0.0, 0.0, 1.0]) if "<<" in t else np.array([1.0, 0.0, 0.0])
            out.append(v)
        return np.stack(out)


def _docs():
    texts = ["User: I want to leave from Cambridge please", "User: a train going to Cambridge please"] * 2
    docs, spans = {}, []
    for k, t in enumerate(texts):
        did = f"d{k}"
        docs[did] = SimpleNamespace(text=t, spans=[(0, len(t))])
        a = t.index("Cambridge")
        spans.append(SimpleNamespace(doc_id=did, turn=0, start=a, end=a + 9, text="Cambridge"))
    return docs, spans


def _run(fn):
    docs, spans = _docs()
    _x, lab = fn(spans, docs, FakeEnc(), [0] * 4, [(s.doc_id, 0) for s in spans])
    return lab


def test_window_extraction():
    docs, spans = _docs()
    doc, u = docs["d0"], spans[0]
    assert CV.context_text(doc, u, [u]) == "want to leave from <<[TEXT]>> please"   # 4 words left (speaker cut), the mask, 1 word right (only one exists)
    assert CV.context_text(doc, u, [u], left=1, right=0) == "from <<[TEXT]>>"
    d2, u2 = docs["d1"], spans[1]
    assert CV.context_text(d2, u2, [u2], left=2, right=1) == "going to <<[TEXT]>> please"


def test_alpha_zero_is_the_adopted_clustering():
    assert _run(CV.cluster_fn(0.0)) == _run(fold.CONFIGS["F_m2_t06_bk"].cluster_fn)
    assert len(set(_run(CV.cluster_fn(0.0)))) == 1          # same value, one cluster


def test_context_separates_roles_that_share_a_value():
    lab = _run(CV.cluster_fn(0.7))
    assert lab[0] == lab[2] and lab[1] == lab[3] and lab[0] != lab[1]


def test_match_clusters_strict_and_lenient():
    old = {"a": {1, 2, 3, 4, 5}, "b": {6, 7}}
    new = {"x": {1, 2, 3, 4, 5}, "y": {6}, "z": {7}}
    assert CV.match_clusters(old, new) == {"x": "a"}                       # y: Jaccard 0.5, z: 0.5
    assert CV.match_clusters(old, new, lenient=True) == {"x": "a", "y": "b", "z": "b"}


def test_carry_columns_identity_and_drop():
    cols = [{"cid": 1, "name": "n", "members": ["c@c/0"], "groups": ["c/0"], "mention_ids": [1, 2], "n_mentions": 2},
            {"cid": 2, "name": "empty", "members": ["c@c/1"], "groups": ["c/1"], "mention_ids": [], "n_mentions": 0},
            {"cid": 3, "name": "m", "members": ["d@d/0"], "groups": ["d/0"], "mention_ids": [3], "n_mentions": 1}]
    old_of = {1: "c", 2: "c", 3: "d"}
    same = CV.carry_columns(cols, old_of, old_of, {"c": "c", "d": "d"})
    assert same == cols
    new_of = {1: "x", 2: "x", 3: "y"}                                      # d changed beyond Jaccard 0.8: unmatched -> dropped
    out = CV.carry_columns(cols, old_of, new_of, {"x": "c"})
    assert [c["name"] for c in out] == ["n", "empty"] and out[0]["members"] == ["x@c/0"]


def test_role_clusters_fragmented_and_s3():
    labels = {i: ["A"] for i in (1, 2, 3)} | {i: ["B"] for i in (4, 5, 6)} | {i: ["A"] for i in (7, 8, 9)}
    cl = {"c0": [1, 2, 3, 4, 5, 6], "c1": [7, 8, 9]}
    assert CV.role_clusters(cl, labels, {"A", "B"}) == {"c0": ("A", "B")}
    assert CV.fragmented(cl, labels, {"A", "B"}) == {"A": ["c0", "c1"]}
    assert CV.s3_attrs({"c0": [1, 2, 3, 4, 5, 6]}, labels, {"B"}, {"B": 3}, lambda a: True) == {"B"}   # purity 0.5 < 0.6
