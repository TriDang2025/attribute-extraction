"""wf_v4.4 (diary Nov 14) T6: runner of Step 4 v4.4 (s1a/step4_v44.py) for Llama-3.1-8B.

python scripts/t6_step4_v44.py --fake [--out DIR]    all stages with the fake model (laptop plumbing test; default out results/wf_v44/t6/fake)
python scripts/t6_step4_v44.py --score [--out DIR]   score the finished chains of DIR with the v4.3 scorers (single seeds and the voted schema)
                                                     -> DIR/scores.csv, DIR/summary.md, DIR/calls.csv (default out results/wf_v44/t6)
Options: --inputs a_llama44,c1 (priority order; a_llama43 is accepted as a stand-in before a_llama44 exists; a missing column file skips that input
with a message), --sets dev50,dev50b, --seeds 0,1,2, --a-llama44-dir DIR / --a-llama43-dir DIR (the folders that hold <set>/a.columns.json, default
results/wf_v44/t4/a_llama44 and results/wf_v43/u2/a_llama43; the Step 3 scores/final_columns.json two levels up gives the mention ids, see step4_v44),
--gt gt/schema_gt_v1.yaml, --legacy-mapping (map a_llama4x columns through the Qwen handover, as v4.3 did).
The real run is on Colab: t6_step4_v44.run(backend, inputs=("a_llama44",)), then run(backend, inputs=("c1",)), with
backend = log_v44.VllmBackend44(...) (Llama-3.1-8B-Instruct, guided JSON, temperature 0); finished jobs are cached, so a rerun continues.
Point it at a_llama44 elsewhere with run(backend, step3_dirs={"a_llama44": Path(".../a_llama44")}). Then on the laptop: score(out).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step4_fake_v44 as F  # noqa: E402
from s1a import step4_v44 as S  # noqa: E402

OUT = S.OUT_T6


def run(backend, out=OUT, inputs=S.INPUTS, sets=S.SETS, seeds=S.SEEDS, cfg=None, step3_dirs=None, log=print):
    """All stages of the chains of `inputs` (12 chains per input: 2 sets x 3 seeds, plus the 2 vote chains), see step4_v44.run. Returns its info."""
    return S.run(out, backend, inputs, sets, seeds, cfg, step3_dirs, ROOT, log)


def score(out=OUT, gt_path=None, legacy_mapping=False):
    """Score the finished chains of `out`; writes scores.csv, summary.md, calls.csv; returns the score rows."""
    rows = S.score_chains(out, ROOT, gt_path, legacy_mapping)
    S.summary(out, rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--inputs", default=",".join(S.INPUTS))
    ap.add_argument("--sets", default=",".join(S.SETS))
    ap.add_argument("--seeds", default=",".join(map(str, S.SEEDS)))
    ap.add_argument("--a-llama44-dir", type=Path)
    ap.add_argument("--a-llama43-dir", type=Path)
    ap.add_argument("--gt", type=Path)
    ap.add_argument("--legacy-mapping", action="store_true")
    a = ap.parse_args()
    if not (a.fake or a.score):
        ap.error("give --fake and/or --score (the real run is the Colab notebook calling t6_step4_v44.run)")
    out = a.out or (OUT / "fake" if a.fake else OUT)
    if a.fake:
        dirs = {k: v for k, v in (("a_llama44", a.a_llama44_dir), ("a_llama43", a.a_llama43_dir)) if v}
        info = run(F.FakeV44(), out, tuple(a.inputs.split(",")), tuple(a.sets.split(",")), tuple(int(x) for x in a.seeds.split(",")), step3_dirs=dirs)
        print("run:", info["finished"], "chains finished")
    if a.score:
        rows = score(out, a.gt, a.legacy_mapping)
        print(len(rows), "score rows ->", out / "scores.csv", out / "summary.md")


if __name__ == "__main__":
    main()
