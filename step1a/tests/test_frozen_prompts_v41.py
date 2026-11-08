"""Frozen prompts (diary Nov 7, user decision 2026-11-08): Step 1b and Step 4 v4.1.

Rebuilding the prompts from the dry-run inputs must give byte-for-byte the files that were dry-run in Gemini. If this test fails, a
frozen prompt changed: undo the change, or get the user's OK and re-freeze (rebuild the dry-run files) on purpose.
"""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v4 as B  # noqa: E402
from s1a import step1b_v41 as S1B  # noqa: E402

RES = ROOT / "results" / "wf_v41"
STEP4 = RES / "step4_dryrun_a"


def _read(p):
    return Path(p).read_text(encoding="utf-8")


@pytest.mark.parametrize("set_name", ["dev50", "dev50b"])
def test_step1b_prompt_frozen(set_name):
    cols = B.read_json(ROOT / "results" / "wf_v4" / "inputs" / set_name / "a.columns.json")
    text, _ = S1B.build_prompt(cols)
    assert text == _read(RES / "step1b" / "prompts" / f"step1b_{set_name}.txt")


def test_step4_v41_prompts_frozen(tmp_path):
    """All four stages, input a, dev50 and dev50b: stage k is rebuilt from the saved answers of the stages before it."""
    shutil.copytree(STEP4 / "responses", tmp_path / "responses")
    B.build_chains_stage1(tmp_path, B.read_json(STEP4 / "chains.json"), ROOT).save()
    for k in (2, 3, 4):
        B.build_stage(tmp_path, k, ROOT)   # writes its prompts and manifest itself
    frozen = sorted(p.name for p in (STEP4 / "prompts").iterdir())
    assert len(frozen) == 16   # 2 chains x 4 stages x (prompt + schema)
    assert sorted(p.name for p in (tmp_path / "prompts").iterdir()) == frozen
    for name in frozen:
        assert _read(tmp_path / "prompts" / name) == _read(STEP4 / "prompts" / name), name
