"""wf_v4.7 Z4 driver (scripts/gpu_v47.py) with the laptop fakes: 3 runs in separate folders, agreement over the runs."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import gpu_v47 as G  # noqa: E402

pytestmark = pytest.mark.skipif(not (G.SRC / "dev50" / "step3" / "scores" / "final_columns.json").exists(), reason="v4.6 Y3 output missing")


def test_fake_z4_runs_three_times_in_own_folders(tmp_path):
    res, ag = G.fake_check(tmp_path)
    assert sorted(res) == [1, 2, 3]
    for r in G.RUNS:
        for dev in res[r]:
            cfg = json.loads((G.run_dir(r, dev, tmp_path) / "loop2" / "evidence" / "run_info.json").read_text(encoding="utf-8"))["config"]
            assert cfg == G.L2.load_config(G.L2.CONFIG_V47)["evidence"]
            assert (G.run_dir(r, dev, tmp_path) / "loop2" / "step1b" / "responses").is_dir()     # own cache per run
    assert all(st["step1b"][0] == st["step1b"][1] for st in ag.values())


def test_prepare_keeps_an_existing_copy(tmp_path):
    d = G.prepare(1, "dev50", "c_n50", tmp_path)
    f = d / "step3" / "scores" / "final_columns.json"
    f.write_text("{}", encoding="utf-8")
    G.prepare(1, "dev50", "c_n50", tmp_path)
    assert f.read_text(encoding="utf-8") == "{}"
    with pytest.raises(FileNotFoundError):
        G.prepare(1, "nope", "c_n50", tmp_path)
