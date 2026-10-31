"""Regression: the "old" setting reproduces the OLD_COLS of results/loop1_v32/summary.md (needs real data)."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SUMMARY = ROOT / "results" / "loop1_v32" / "summary.md"

pytestmark = [pytest.mark.slow,
              pytest.mark.skipif(not SUMMARY.exists(), reason="results/loop1_v32/summary.md missing"),
              pytest.mark.skipif(importlib.util.find_spec("s1a.v34_data") is None, reason="s1a.v34_data not written yet")]


def test_old_setting_matches_v32_summary():
    import score_v34 as S
    from s1a import score_rules as SR
    from s1a import v34_data

    run, dir32, dir31 = (ROOT / "results" / d for d in ("graph_v22_dev50", "loop1_v32", "loop1_v31"))
    shared, data = v34_data.load_all(run, dir32, dir31)
    extra = SR.load_extra(ROOT / "results" / "loop1_v34", dir32)
    bad = S.check_old(S.score_setting("old", data, shared, extra), SUMMARY)
    assert not bad, bad
