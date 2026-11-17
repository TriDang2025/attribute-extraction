"""wf_v4.5 W2: one command, raw dialogues -> schema.sql (s1a/pipeline_v45.py).

python scripts/run_pipeline.py --corpus data/wf_v45_corpora/n50.jsonl --out results/wf_v45/w2/n50 --set c_n50 --fake
  laptop plumbing test: real Steps 1a-2 (GLiNER, bge-m3 on CPU), fake LLM answers and a fake name encoder for Steps 3-4.
On Colab (GPU): pipeline_v45.run_pipeline(corpus, out, set_name, backend, S3.bge_m3_encoder(), encoder(), pipeline_v45.step4_config(choice))
with backend = log_v44.VllmBackend44 (Llama-3.1-8B-Instruct, guided JSON, temperature 0).
Outputs in --out: schema.sql, attributes.json, cost.json, entities.json, a_prompts/, step3/, step4/; Step 1a-2 in results/graph_v22_<set>/.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import step3_v44 as S3  # noqa: E402
from s1a import step4_fake_v44 as F4  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--set", required=True, help="run name (lowercase, digits, _): Step 1a goes to results/graph_v22_<set>")
    ap.add_argument("--step4", choices=tuple(PL.STEP4), default="v44_other_off", help="frozen Step 4 (W1 decides)")
    ap.add_argument("--p2-batch", type=int, default=0, help="Step 4 pass 2 in batches of this many columns (0 = off, the frozen single prompt)")
    ap.add_argument("--fake", action="store_true", help="fake LLM and name encoder (the real run is on Colab)")
    ap.add_argument("--skip-1a", action="store_true", help="reuse results/graph_v22_<set> from an earlier run")
    a = ap.parse_args()
    if not a.fake:
        ap.error("the real LLM run is on Colab (see the docstring); give --fake for the laptop test")
    from run import encoder
    out = a.out if a.out.is_absolute() else ROOT / a.out
    c = PL.run_pipeline(a.corpus, out, a.set, S3.FakeStep44(), S3.FakeEncoder(), encoder(), PL.step4_config(a.step4, a.p2_batch),
                        skip_1a=a.skip_1a, backend4=F4.FakeV44())
    print(json.dumps(c, indent=1))


if __name__ == "__main__":
    main()
