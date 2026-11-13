"""wf_v4.3 (diary Nov 13) U2: Step 3 v4.3 with Llama-3.1-8B (s1a/step3_v43.py): one name per cluster id (no free attribute list), batches of 5
clusters, 3 orders + the frozen vote, U1 worked examples, then the frozen split pass, reconcile and v3.8 duplicate check (U0's post steps).

python scripts/u2_step3_v43.py --build [--out DIR]   -> DIR (default results/wf_v43/u2): names prompts + schemas, manifest_names.json,
                                                        the 54 frozen split prompts, examples.csv, manifest.json
python scripts/u2_step3_v43.py --fake  [--out DIR]   -> every stage with the fake model (laptop plumbing test only; no result)
python scripts/u2_step3_v43.py --score [--out DIR]   -> DIR/scores/*, DIR/a_llama43/<set>/a.columns.json (Step 4 input), DIR/fig_train_attrs.json
Notebook: `run(out, backend)` with nov16_v41.VllmBackend (Llama-3.1-8B-Instruct, temperature 0, guided JSON), then `score_all(out)`.
Stage by stage (what run() does): backend.run(out, names_jobs(out) + step3_post_v43.stage_jobs(out, "split")); step3_v43.assemble_a(out);
backend.run(out, step3_post_v43.stage_jobs(out, "reconcile")); backend.run(out, step3_post_v43.stage_jobs(out, "dupcheck")).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step3_post_v43 as PP  # noqa: E402
from s1a import step3_v43 as S3  # noqa: E402

OUT = S3.OUT
build, run, names_jobs, assemble_a = S3.build, S3.run, S3.names_jobs, S3.assemble_a


def score_all(out):
    """score(out) + summary.md + the Step 4 input a_llama43 + the figure data; returns (score result, a_llama43 sizes)."""
    res = PP.score(out)
    text = PP.summary_md(res, "wf_v4.3 U2: Step 3 v4.3 (names only, batches of 5) on Llama-3.1-8B")
    names = Path(out) / "names_stats.csv"
    if names.exists():
        import pandas as pd
        n = pd.read_csv(names)
        text += (f"\n## Names stage\n\n{len(n)} (set, entity, order) answers; batches {int(n['batches'].sum())}, valid {int(n['batches_ok'].sum())}; "
                 f"names merged across batches {int(n['merged_across_batches'].sum())}; names no cluster uses {int(n['names_no_cluster'].sum())}; "
                 f"`_end`-style names {int(n['end_names'].sum())}; error lines {int(n['errors'].sum())}.\n")
    (Path(out) / "scores" / "summary.md").write_text(text, encoding="utf-8", newline="\n")
    sizes = S3.write_a_llama43(out)
    S3.fig_train_attrs(out)
    return res, sizes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for k in ("build", "fake", "score"):
        g.add_argument(f"--{k}", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.build:
        names, jobs = build(a.out)
        print(f"{len(names)} names jobs, {len(jobs)} manifest jobs in {a.out}")
    elif a.fake:
        print(run(a.out, PP.FakeStep3()))
    else:
        res, sizes = score_all(a.out)
        print((a.out / "scores" / "summary.md").read_text(encoding="utf-8"))
        print("a_llama43 columns:", sizes)


if __name__ == "__main__":
    main()
