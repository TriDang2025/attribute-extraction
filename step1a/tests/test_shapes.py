import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from s1a import shapes as SH


@pytest.mark.parametrize("text,out", [
    ("TR7213", "train id TR####"), ("tr 5713", "train id TR####"), ("Train TR8167", "train id TR####"),
    ("72ycmlxx", "reference code XXXXXXXX"), ("CUL9VZ04", "reference code XXXXXXXX"),
    ("OAEJMYOI", "reference code XXXXXXXX"), ("64UQ7M3G", "reference code XXXXXXXX"),
    ("01223 360966", "phone number 01223 ######"), ("07083984796", "phone number 01223 ######"),
    ("cb21tq", "postcode CB# #XX"), ("cb4 1er", "postcode CB# #XX"), ("CB23AP", "postcode CB# #XX"),
    ("10.10 pounds", "price ## pounds"), ("66 gbp", "price ## pounds"), ("12.80 GBP", "price ## pounds"),
    ("37.79 GPB", "price ## pounds"), ("£5", "price ## pounds"), ("2.50 pound fee", "price ## pounds"),
])
def test_positive(text, out):
    assert SH.shape(text) == out


@pytest.mark.parametrize("text", [
    "restaurant", "Cambridge", "20:30", "13:30", "7", "2 people", "5 nights", "4 stars", "156 chesterton road",
    "7 Milton Road", "unit 8", "There are only 4 trains", "49 minutes", "1 person", "cb2", "TR72", "12345678",
    "the 8:30 train", "Saint Edward's Passage", "expensive", "centre",
])
def test_negative(text):
    assert SH.shape(text) == text


def test_kinds_filter():
    assert SH.shape("66 gbp", SH.CODES) == "66 gbp"
    assert SH.shape("TR7213", SH.CODES) == "train id TR####"


class FakeEnc:
    def encode(self, texts):
        out = []
        for t in texts:
            rng = np.random.default_rng(int(hashlib.md5(t.encode()).hexdigest()[:8], 16))
            v = rng.normal(size=16)
            out.append(v / np.linalg.norm(v))
        return np.array(out)


def test_cluster_fn_merges_codes(monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    spans = [SimpleNamespace(text=t) for t in ["TR7213", "TR9016", "tr 5713", "restaurant", "cinema"]]
    x, labels = SH.CONFIGS["B_codes"].cluster_fn(spans, None, FakeEnc(), [0] * 5, None)
    assert labels[0] == labels[1] == labels[2]
    assert labels[3] != labels[0] and labels[3] != labels[4]
    assert len(x) == 5
