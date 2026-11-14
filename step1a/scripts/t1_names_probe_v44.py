"""wf_v4.4 (diary Nov 14) T1: why do the guided names answers fail, and which schema variant fixes it?

python scripts/t1_names_probe_v44.py --build [--out DIR]   -> DIR (default results/wf_v44/t1): 3 names jobs per variant (v1, v2, v3, v4, v0;
                                                              the first v4.3 batch of train / hotel / restaurant, dev50, order 0)
python scripts/t1_names_probe_v44.py --fake  [--out DIR]   -> run + choice.json with the fake model (laptop plumbing test only)
python scripts/t1_names_probe_v44.py --eval  [--out DIR]   -> choice.json + guided_raw.jsonl from the saved answers
Notebook: `run_probe(out, backend)` with log_v44.VllmBackend44 (Llama-3.1-8B-Instruct, temperature 0, guided JSON) -> (choice, info);
results/wf_v44/t1/choice.json = {"chosen", "passed", "variants": {v: {jobs, ok, retried, errors, finish}}}, read by T4
(step3_v44.names_variant). guided_raw.jsonl holds the guided text of every probe job, also the failed ones.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step3_v44 as S  # noqa: E402

OUT = S.OUT_T1
run_probe, probe_jobs, evaluate_probe = S.run_probe, S.probe_jobs, S.evaluate_probe


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for k in ("build", "fake", "eval"):
        g.add_argument(f"--{k}", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.build:
        print(f"{len(probe_jobs(a.out))} probe jobs in {a.out}")
    elif a.fake:
        print(run_probe(a.out, S.FakeStep44()))
    else:
        print(evaluate_probe(a.out))


if __name__ == "__main__":
    main()
