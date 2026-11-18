"""wf_v4.7 Z4 (diary Nov 17) GPU job, called by the notebook colab/S1A_wf47_colab.ipynb (one session, model loaded once).

z4: loop 2 v4.7 (s1a/loop2_v46.run_loop2 with config/wf_v47_loop2.json) on the v4.6 Y3 loop-1 output of dev50 and dev50b, 3 full runs.
    Loop 1 is not rerun: each run folder results/wf_v47/z4/run<r>/<set>/ gets a copy of the loop-1 files loop 2 reads (LOOP1_FILES) from
    results/wf_v46/y3/<set>/; Step 1a-2 = results/graph_v22_<run> from git. Every run has its own responses/ cache, so runs 2 and 3 are
    new model calls (same prompts), not cache hits.
agreement(root): per set, the share of jobs whose raw answer is the same in every run (Step 1b, Step 3 names, duplicate check).
Scoring is on the laptop afterwards (Z5, Z6). Laptop check of the driver: python scripts/gpu_v47.py --fake (no GPU).
"""
import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import gpu_v46 as G46  # noqa: E402
from s1a import loop2_v46 as L2  # noqa: E402

SRC = ROOT / "results" / "wf_v46" / "y3"
OUT = ROOT / "results" / "wf_v47" / "z4"
SETS = G46.SETS
RUNS = (1, 2, 3)
LOOP1_FILES = ("step3/scores/final_columns.json", "step3/a_llama44/{run}/a.columns.json", "step3/a_llama44/{run}/a.premerge.columns.json")


def run_dir(r, dev, root=OUT):
    return Path(root) / f"run{r}" / dev


def prepare(r, dev, run, root=OUT, src=SRC):
    """Copy the loop-1 files of `dev` into run folder `r` (kept if already there: a rerun after a crash keeps the cache). Returns the folder."""
    d = run_dir(r, dev, root)
    for rel in LOOP1_FILES:
        a, b = Path(src) / dev / rel.format(run=run), d / rel.format(run=run)
        if a.exists() and not b.exists():
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(a, b)
    if not (d / "step3" / "scores" / "final_columns.json").exists():
        raise FileNotFoundError(f"no loop-1 output for {dev} in {src}")
    return d


def z4(backend, enc_1a, gliner_loader, runs=RUNS, sets=SETS, root=OUT, src=SRC, cfg=None, log=print):
    """Loop 2 v4.7 `len(runs)` times on each set. Returns {run: {dev: run_loop2 info}}."""
    cfg = cfg or L2.load_config(L2.CONFIG_V47)
    res = {}
    for r in runs:
        for dev, run in sets.items():
            info = L2.run_loop2(prepare(r, dev, run, root, src), run, backend, enc_1a, gliner_loader, cfg, log=log)
            res.setdefault(r, {})[dev] = info
            log(f"z4 run {r} {dev}: {json.dumps({k: v for k, v in info.items() if k != 'cost'})} | cost {info['cost']['total']}")
    return res


def agreement(runs=RUNS, sets=SETS, root=OUT):
    """{dev: {step: (jobs with the same raw answer in every run, jobs answered in every run)}}; step = the loop2 subfolder of the job."""
    out = {}
    for dev in sets:
        raws = defaultdict(dict)                    # (step, job file) -> {run: raw}
        for r in runs:
            for p in (run_dir(r, dev, root) / "loop2").glob("*/responses/*.jsonl"):
                rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
                if rows:
                    raws[(p.parent.parent.name, p.name)][r] = rows[-1].get("raw")
        steps = defaultdict(lambda: [0, 0])
        for (step, _), by_run in raws.items():
            if len(by_run) == len(runs):
                steps[step][1] += 1
                steps[step][0] += len(set(by_run.values())) == 1
        out[dev] = {s: tuple(v) for s, v in sorted(steps.items())}
    return out


def fake_check(root):
    """z4 + agreement with the laptop fakes into `root`; raises on any failure."""
    sets = {k: v for k, v in SETS.items() if (SRC / k / "step3" / "scores" / "final_columns.json").exists()}
    res = z4(G46.Fakes(), G46.FakeEnc(), G46.NoGliner, sets=sets, root=root, log=lambda *_: None)
    ag = agreement(sets=sets, root=root)
    for dev, steps in ag.items():
        assert steps["step1b"][1] > 0 and steps["step1b"][0] == steps["step1b"][1], (dev, steps)   # the fake answers the same every run
    return {r: {d: i["suggested"] for d, i in v.items()} for r, v in res.items()}, ag


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true", help="laptop check with fakes (no GPU)")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v47" / "fake_check")
    a = ap.parse_args()
    if not a.fake:
        ap.error("the real run is the notebook colab/S1A_wf47_colab.ipynb; give --fake for the laptop check")
    print(fake_check(a.out))


if __name__ == "__main__":
    main()
