"""wf_v4 Colab batch, stage 1 builder (contract WF_V4_BATCH.md). No GPU, no LLM.

python scripts/batch_build_v4.py [--out results/wf_v4/colab]
Needs results/wf_v4/inputs/ (scripts/inputs_v4.py) and config/wf_v4_placement.json. Writes <out>/{prompts/*.txt + *.schema.json,
manifest.json (stage 1: 24 main chains + the placement base chain = 25 calls of 4.1, and 6 (e) calls), chains.json, placement.json}.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v4" / "colab")
    a = ap.parse_args()
    jobs = B.build_stage1(ROOT, a.out)
    print(len(jobs), "stage-1 jobs:", dict(Counter(j["family"] for j in jobs)), "largest prompt", max(j["est_prompt_tokens"] for j in jobs), "est tokens")
    big = [j["job"] for j in jobs if j["family"] in B.FIRST_STEPS and j["est_prompt_tokens"] >= B.LIMIT_FIRST]
    if big:
        print("WARNING: first prompt over", B.LIMIT_FIRST, "est tokens:", big, file=sys.stderr)


if __name__ == "__main__":
    main()
