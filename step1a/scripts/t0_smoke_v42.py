"""wf_v4.2 (diary Nov 10) T0: smoke test of the Llama setting, 1 Step 3 call + 1 Step 4 call. Frozen prompts, no code changes.

python scripts/t0_smoke_v42.py --build [--out DIR]   -> DIR/manifest.json + prompts (default results/wf_v42/t0_smoke)
python scripts/t0_smoke_v42.py --fake  [--out DIR]   -> answers the jobs with nov16_v41.FakeLLM (laptop plumbing test only)
python scripts/t0_smoke_v42.py --check [--out DIR]   -> DIR/check.md + check.csv (s1a/check_v42.py); exit 1 when a job has no answer or a parse error
On Colab, colab/S1A_wf42_colab.ipynb runs the jobs with nov16_v41.VllmBackend between --build and --check.

Jobs:
- Step 3: the frozen A prompt (format v2) of hotel, dev50b, order s0, copied byte for byte from the v3.7 Qwen batch (results/loop1_v37/colab).
- Step 4: stage 1 (4.1) of chain c1 / dev50 / seed 0 with the v4.1 prompts (batch_v4.build_chains_stage1, as the Nov 16 runner).
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import check_v42 as C  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402

OUT = ROOT / "results" / "wf_v42" / "t0_smoke"
STEP3_DIR = ROOT / "results" / "loop1_v37" / "colab"
STEP3_JOB = "hotel_a_v22d50b_s0"
STEP4_CHAIN = {"id": B.chain_id("c1", "dev50", 0), "kind": "main", "input": "c1", "set": "dev50", "seed": 0, "exclude": [],
               "prompt_version": "v41"}


def jobs_of(out):
    return B.read_json(Path(out) / "manifest.json")["jobs"]


def build(out):
    out = Path(out)
    s3 = next(j for j in B.read_json(STEP3_DIR / "manifest.json")["jobs"] if j["job"] == STEP3_JOB)
    for k in ("prompt", "schema"):
        (out / s3[k]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(STEP3_DIR / s3[k], out / s3[k])
    s4 = B.build_chains_stage1(out, [STEP4_CHAIN], ROOT).jobs
    B.write_json(out / "manifest.json", {"stage": 1, "jobs": [s3, *s4]})
    return [s3, *s4]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true")
    g.add_argument("--fake", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.build:
        print(f"{len(build(a.out))} jobs in {a.out}")
    elif a.fake:
        print(NV.FakeLLM().run(a.out, jobs_of(a.out)))
    else:
        _, ok = C.write_check(a.out, "wf_v4.2 T0 smoke test")
        print((a.out / "check.md").read_text(encoding="utf-8"))
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
