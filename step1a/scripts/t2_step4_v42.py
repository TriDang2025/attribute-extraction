"""wf_v4.2 (diary Nov 10) T2: Step 4 v4.1 with Llama on input c1 (all GT attributes) and input a (Qwen's frozen Step 3 handover;
user choice 2026-11-10, since Llama's own Step 3 fails, T1). dev50 and dev50b, seeds 0-2 = 12 chains, stages 4.1 -> 4.4.

python scripts/t2_step4_v42.py --fake [--out DIR]   -> all stages with nov16_v41.FakeLLM (laptop plumbing test only)
On Colab, colab/S1A_wf42_colab.ipynb cell 8 calls run(OUT, backend) (nov16_v41.run_chains with nov16_v41.VllmBackend).
Scoring of the answers (T7 scorers, PK rules a and b) is a separate laptop step after the run.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402

OUT = ROOT / "results" / "wf_v42" / "t2_step4"
RUNS = tuple((inp, s) for inp in ("c1", "a") for s in NV.SETS)


def chains():
    return NV.step4_chains({}, runs=RUNS)


def run(out, llm):
    info = NV.run_chains(out, llm, chains(), ROOT)
    B.write_json(Path(out) / "run_info.json", info)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true", required=True)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print(run(a.out, NV.FakeLLM()))


if __name__ == "__main__":
    main()
