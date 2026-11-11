"""wf_v4.2 (diary Nov 10) T2: Step 4 v4.1 with Llama on input c1 (all GT attributes) and input a (Qwen's frozen Step 3 handover;
user choice 2026-11-10, since Llama's own Step 3 fails, T1). dev50 and dev50b, seeds 0-2 = 12 chains, stages 4.1 -> 4.4.

python scripts/t2_step4_v42.py --fake [--keyed] [--out DIR]   -> all stages with the fake model (laptop plumbing test only)
--keyed / run(..., keyed=True): option B (s1a/keyed_v42.py), keyed "exactly once" schemas for 4.1, 4.2 and 4.4, in
results/wf_v42/t2b_step4_keyed.
On Colab, colab/S1A_wf42_colab.ipynb cell 8 calls run(OUT, backend) (nov16_v41.run_chains with nov16_v41.VllmBackend).
Scoring of the answers (T7 scorers, PK rules a and b) is a separate laptop step after the run.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import keyed_v42 as K  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402

OUT = ROOT / "results" / "wf_v42" / "t2_step4"
OUT_KEYED = ROOT / "results" / "wf_v42" / "t2b_step4_keyed"
RUNS = tuple((inp, s) for inp in ("c1", "a") for s in NV.SETS)


def chains():
    return NV.step4_chains({}, runs=RUNS)


def run(out, llm, keyed=False):
    info = NV.run_chains(out, K.KeyedLLM(llm) if keyed else llm, chains(), ROOT)
    B.write_json(Path(out) / "run_info.json", info)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true", required=True)
    ap.add_argument("--keyed", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    out = a.out or (OUT_KEYED if a.keyed else OUT)
    print(run(out, K.fake_keyed() if a.keyed else NV.FakeLLM(), keyed=a.keyed))


if __name__ == "__main__":
    main()
