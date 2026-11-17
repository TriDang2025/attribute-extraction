"""wf_v4.6 Y4: loop 2 (Step 1b -> evidence check -> Step 3 naming -> merge) on a finished loop-1 run folder (logic in s1a/loop2_v46.py).

Loops: `--loops 1` = the loop-1 pipeline only (scripts/run_pipeline.py / pipeline_v46.run_pipeline(loops=1)); loop 2 runs after it on the same
output folder. This script is the loop-2 half: python scripts/loop2_v46.py --run <loop-1 out> --set <set name> --model fake. The GPU run
(Llama-3.1-8B, s1a/log_v44.VllmBackend44) is started from the notebook / pipeline_v46 (`loops=2` calls run_loop2); this script runs the fake model.

python scripts/loop2_v46.py --run results/wf_v45/w2/n50 --set c_n50 --model fake [--k 40 --threshold 0.3 --min-dialogues 3
        --min-support 0.05 --max-overlap 0.5 --min-votes 2]
  -> <run>/loop2/ (files listed in s1a/loop2_v46.py); real bge-m3 + GLiNER (chunking venv), fake LLM answers (laptop plumbing, not a result).
Config: config/wf_v46_loop2.json; the flags override single values.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import loop2_v46 as L  # noqa: E402


def config_from(args):
    ev = {k: v for k, v in (("k", args.k), ("threshold", args.threshold), ("min_dialogues", args.min_dialogues),
                            ("min_support", args.min_support), ("max_overlap", args.max_overlap)) if v is not None}
    s1 = {"min_votes": args.min_votes} if args.min_votes is not None else {}
    return L.load_config(evidence=ev, step1b=s1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True, help="loop-1 output folder (pipeline_v45 layout)")
    ap.add_argument("--set", required=True, help="set name of the run (results/graph_v22_<set>/)")
    ap.add_argument("--model", choices=["fake"], required=True, help="the laptop runs the fake model only")
    ap.add_argument("--k", type=int)
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--min-dialogues", type=int)
    ap.add_argument("--min-support", type=float)
    ap.add_argument("--max-overlap", type=float)
    ap.add_argument("--min-votes", type=int)
    a = ap.parse_args()
    from run import encoder as make_encoder
    from s1a import spans as SP
    enc = make_encoder()
    info = L.run_loop2(a.run, a.set, L.FakeLoop2LLM(), enc, SP.load, config_from(a))
    enc.save()
    print(json.dumps(info, indent=1, default=str))


if __name__ == "__main__":
    main()
