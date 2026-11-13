"""wf_v4.3 (diary Nov 13) U4: runner of Step 4 v4.3 (s1a/step4_v43.py) for Llama-3.1-8B.

python scripts/u4_step4_v43.py --fake [--out DIR]   all stages with the fake model (laptop plumbing test; default out results/wf_v43/u4/fake)
python scripts/u4_step4_v43.py --score [--out DIR]  score the finished chains of DIR with the T7 scorers -> DIR/scores.csv, DIR/summary.md,
                                                    DIR/calls.csv, DIR/fig_schema_a_dev50_s0.json (default out results/wf_v43/u4)
Options: --inputs a,c1,a_llama43 (priority order; a missing column file skips that input with a message; a_llama43 is the Step 3 v4.3 output
of results/wf_v43/u2/a_llama43, --a-llama43-dir), --sets dev50,dev50b, --seeds 0,1,2 (seed 0 = column input order, 1 and 2 shuffle inside each
entity block, as option B), --gt gt/schema_gt_v1.yaml.
The real run is on Colab: step4_v43.run(OUT, backend, inputs=...) with nov16_v41.VllmBackend (Llama-3.1-8B-Instruct, guided JSON, temperature 0),
called once per input group, e.g. run(OUT, backend, inputs=("a",)), then ("c1",), then ("a_llama43",); finished jobs are cached, so a rerun
continues. Then on the laptop: --score.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step4_fake_v43 as F  # noqa: E402
from s1a import step4_score_v43 as SC  # noqa: E402
from s1a import step4_v43 as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--inputs", default=",".join(S.INPUTS))
    ap.add_argument("--sets", default=",".join(S.SETS))
    ap.add_argument("--seeds", default=",".join(map(str, S.SEEDS)))
    ap.add_argument("--a-llama43-dir", type=Path, default=S.A_LLAMA43_DIR)
    ap.add_argument("--gt", type=Path)
    a = ap.parse_args()
    if not (a.fake or a.score):
        ap.error("give --fake and/or --score (the real run is the Colab notebook calling step4_v43.run)")
    out = a.out or (S.OUT / "fake" if a.fake else S.OUT)
    if a.fake:
        info = S.run(out, F.FakeV43(), tuple(a.inputs.split(",")), tuple(a.sets.split(",")), tuple(int(x) for x in a.seeds.split(",")),
                     a.a_llama43_dir)
        print("run:", info["finished"], "chains finished")
    if a.score:
        rows = SC.score_chains(out, ROOT, a.gt)
        print(len(rows), "score rows ->", out / "scores.csv")
        SC.summary(out, rows)
        SC.figure_data(out, ROOT, a.gt)
        print("->", out / "summary.md", out / "fig_schema_a_dev50_s0.json")


if __name__ == "__main__":
    main()
