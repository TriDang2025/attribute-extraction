import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gold import doc, ms  # noqa: E402
from s1a import metrics as M  # noqa: E402
from s1a.units import Unit  # noqa: E402
from hbe.metrics import bcubed  # noqa: E402


def test_bcubed_multi_equals_single():
    rng = np.random.RandomState(0)
    true = [f"a{x}" for x in rng.randint(0, 6, 300)]
    pred = rng.randint(0, 9, 300)
    assert np.allclose(M.bcubed_multi(true, pred), bcubed(true, pred))
    assert np.allclose(M.bcubed_multi([{t} for t in true], pred), bcubed(true, pred))


def test_bcubed_multi_hand():
    p, r, _ = M.bcubed_multi([{"a"}, {"a", "b"}, {"b"}], [0, 0, 1])
    assert p == pytest.approx(1.0) and r == pytest.approx((1 + 2 / 3 + 1 / 2) / 3)
    p, r, _ = M.bcubed_multi([{"a"}, {"b"}, {"a", "b"}], [0, 0, 0])
    assert p == pytest.approx(7 / 9) and r == pytest.approx(1.0)


def _span(text, sub, nth=0):
    s = -1
    for _ in range(nth + 1):
        s = text.index(sub, s + 1)
    return Unit("span", "D1", "", sub, s, s + len(sub))


def test_match_all_two_labels():
    text, men = doc().text, ms()
    sp = [_span(text, "cambridge on monday"), _span(text, "Book"), _span(text, "Acorn Guest House")]
    used = M.match_all(sp, men)
    assert sp[0].labels == {"Train destination", "Train day"} and sp[0].hidden[2]
    assert sp[0].label == "Train day|Train destination" and len(sp[0].matched) == 2
    assert sp[1].labels == frozenset() and sp[1].label == ""
    assert sp[2].labels == {"Hotel name"}
    assert len(used) == 3


def test_span_recall_mention_vs_value():
    text, men = doc().text, ms()
    r = M.span_recall([_span(text, "cambridge")], men)
    assert r["n_mentions"] == 7 and r["n_values"] == 4
    assert r["mention"] == pytest.approx(1 / 7) and r["value"] == pytest.approx(1 / 4)
    assert (r["n_gold_values"], r["n_verbatim_values"], r["n_nonverbatim_values"]) == (7, 4, 3)
    assert r["per_class"]["Train destination"]["mention"] == pytest.approx(1 / 3)
    assert r["per_class"]["Train destination"]["value"] == 1.0
    assert r["hidden_L2"]["n_mentions"] == 3 and r["visible_L2"]["mention"] == 0.0
    assert r["tight_mention"] == r["mention"]
    long = _span(text, "cambridge")
    long.end = min(len(text), long.end + 10)
    r = M.span_recall([long], men)
    assert r["mention"] > 0 and r["tight_mention"] == 0.0


def test_report_block_keys_and_split():
    men = [m for m in ms() if m.verbatim]
    extra = Unit("span", "D1", "", "hello", 0, 5)
    extra.labels, extra.hidden = frozenset(), {}
    units = men + [extra]
    pred = [0 if m.value == "cambridge" else 1 for m in men] + [2]
    d = M.report_block(units, pred)
    assert d["n"] == 7 and d["K"] == 3 and d["all"]["f"] < 1
    assert d["hidden_L2"]["n"] == 3 and d["hidden_L2"]["f"] == pytest.approx(1.0)
    assert d["visible_L2"]["n"] == 4 and d["visible_L1"]["n"] == 7 and d["hidden_L1"]["n"] == 0
    assert set(d["per_class"]) == {"Train destination", "Hotel name", "Hotel requested day", "Train day"}
    assert d["confused"] and d["nongold_clusters"][0]["texts"] == ["hello"]
    assert "### test" in M.format_block(d, "test")
    lo, hi = M.bootstrap_ci(units, pred, n_boot=20)
    assert lo <= hi
