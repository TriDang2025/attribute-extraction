import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import cue as C  # noqa: E402
from s1a import paths  # noqa: E402, F401
from chk.data import make_doc  # noqa: E402

sys.path.insert(0, str(paths.ROOT / "scripts"))
import relabel as RL  # noqa: E402


class FakeEnc:
    """Deterministic unit vectors seeded by a hash of the text."""
    def encode(self, texts):
        out = []
        for t in texts:
            seed = int(hashlib.md5(t.encode()).hexdigest()[:8], 16)
            v = np.random.default_rng(seed).normal(size=32)
            out.append(v / np.linalg.norm(v))
        return np.array(out, dtype=np.float32)


@dataclass
class Sp:
    doc_id: str
    text: str
    start: int
    end: int
    turn: int = -1


def _setup():
    turns = ["User: I need a train from Cambridge to Cambridge.",
             "User: leave at 20:30 and arrive by 20:30 please."]
    doc = make_doc("D1", [{"id": "a", "turns": turns, "domains": ["train", "train"]}])
    spans = []
    for s in ("Cambridge", "20:30"):
        pos = 0
        while (pos := doc.text.find(s, pos)) >= 0:
            spans.append(Sp("D1", s, pos, pos + len(s)))
            pos += len(s)
    return {"D1": doc}, spans


def test_cue_vectors_shape_and_split():
    docs, spans = _setup()
    v = C.cue_vectors(spans, docs, FakeEnc(), 1)
    assert v.shape == (4, 32)
    assert not np.allclose(v[0], v[1])  # "from <<..>>" vs "to <<..>>"


def test_beta_zero_is_string_only():
    docs, spans = _setup()
    enc, groups = FakeEnc(), [0] * len(spans)
    x, lab = C.cluster_fn(spans, docs, enc, groups, [0] * len(spans), beta=0, t=0.4)
    ref = RL.stage2(enc.encode([u.text for u in spans]), groups, 0.4)
    assert lab == ref
    assert lab[0] == lab[1] and lab[2] == lab[3]


def test_cue_splits_identical_strings():
    docs, spans = _setup()
    enc, groups = FakeEnc(), [0] * len(spans)
    _, lab = C.cluster_fn(spans, docs, enc, groups, [0] * len(spans), beta=0.9, t=0.4)
    assert lab[0] != lab[1] and lab[2] != lab[3]


def test_by_type_separates_types_and_cannot_link_runs():
    docs, spans = _setup()
    enc, groups = FakeEnc(), [0] * len(spans)
    _, lab = C.cluster_fn(spans, docs, enc, groups, [0] * 4, beta=0.5, by_type=True, t=2.0)
    assert lab[0] == lab[1] and lab[2] == lab[3] and lab[0] != lab[2]
    _, lab = C.cluster_fn(spans, docs, enc, groups, [0] * 4, beta=0.5, by_type=True, t=2.0, cannot_link=True)
    assert len(lab) == 4


def test_configs():
    assert 0 < len(C.CONFIGS) <= 16
    assert all(v.cluster_fn for v in C.CONFIGS.values())
