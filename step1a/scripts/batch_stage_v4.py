"""wf_v4 Colab batch, stage k builder (contract WF_V4_BATCH.md). Runs inside the notebook after the responses of stage k-1.

python scripts/batch_stage_v4.py --dir results/wf_v4/colab --stage K
K = 2, 3, 4: prompts 4.2, 4.3, 4.4 of every chain whose earlier answers are valid; K = 5 .. 4 + n: one placement call per mode (sig, nosig)
for the K-5th held-out column, on the schema built from the base chain and the earlier placements. Writes <dir>/{prompts/, manifest_stage<K>.json,
chain_status_stage<K>.json}. A chain with a missing response, a parse error or an invalid answer stops there (listed in the status).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=ROOT / "results" / "wf_v4" / "colab")
    ap.add_argument("--stage", type=int, required=True)
    a = ap.parse_args()
    jobs = B.build_stage(a.dir, a.stage, ROOT)
    status = B.read_json(a.dir / f"chain_status_stage{a.stage}.json")
    stopped = [s for s in status if not s["ok"]]
    print(f"stage {a.stage}: {len(jobs)} jobs, {len(stopped)} chains stopped" + (f", e.g. {stopped[0]['chain']}: {stopped[0]['error']}" if stopped else ""))


if __name__ == "__main__":
    main()
