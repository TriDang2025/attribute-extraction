"""wf_v4.3 (diary Nov 13) U0, the baseline: the rest of frozen Step 3 (3-order vote, split pass, reconcile, duplicate check) on the
Llama-3.1-8B option B A answers of wf_v4.2 (results/wf_v42/t1b_step3_keyed), scored like the Qwen 31/40 and 29/41 of STEP3.md.

python scripts/u0_step3_post_v43.py --build [--out DIR]   -> DIR (default results/wf_v43/u0): the 18 option B answers copied in (not rerun),
                                                            the 54 frozen split prompts, examples.csv, manifest.json
python scripts/u0_step3_post_v43.py --fake  [--out DIR]   -> every stage with the fake model (laptop plumbing test only; no result)
python scripts/u0_step3_post_v43.py --score [--out DIR]   -> DIR/scores/{rows.csv, orders.csv, stats.json, calls.json, a_answers.csv,
                                                            final_columns.json, summary.md}
Notebook: `run(out, backend)` with nov16_v41.VllmBackend (Llama-3.1-8B-Instruct, temperature 0, guided JSON) runs split -> reconcile ->
dupcheck, each built from the answers before it (step3_post_v43.stage_jobs); then `score(out)`.
The scorer is the one behind the Qwen numbers: dashboard_v38.rows_for -> found_total / gold_total of final_v39's variants (A s012 after the
split pass reproduces t14.md 31/40 and 29/41, dashboard_v38.check_step0), through run_data_v37.load_a (parse repair on).
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step3_post_v43 as PP  # noqa: E402

OUT = ROOT / "results" / "wf_v43" / "u0"


def build(out):
    """Copy the option B A jobs (prompts, keyed schemas, answers) and add the frozen split jobs; returns the jobs."""
    out = Path(out)
    a_rows = []
    for j in PP.t1b_a_jobs():
        for k in ("prompt", "schema"):
            (out / j[k]).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PP.T1B / j[k], out / j[k])
        (out / "responses").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PP.T1B / "responses" / f"{j['job']}.jsonl", out / "responses" / f"{j['job']}.jsonl")
        a_rows.append({**j, "reused": True})
    examples = [x for s in PP.SETS for x in PP.a_example_rows(s, [j for j in a_rows if j["set"] == s])]
    return PP.build_common(out, a_rows, examples)


def run(out, backend):
    """All post stages on `backend`; returns {stage: backend info}."""
    return PP.run_post(out, backend)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for k in ("build", "fake", "score"):
        g.add_argument(f"--{k}", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.build:
        print(f"{len(build(a.out))} jobs in {a.out}")
    elif a.fake:
        print(run(a.out, PP.FakeStep3()))
    else:
        res = PP.score(a.out)
        text = PP.summary_md(res, "wf_v4.3 U0: frozen Step 3 on Llama-3.1-8B option B A answers")
        (a.out / "scores" / "summary.md").write_text(text, encoding="utf-8", newline="\n")
        print(text)


if __name__ == "__main__":
    main()
