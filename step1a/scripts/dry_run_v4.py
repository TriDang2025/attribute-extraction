"""wf_v4 laptop dry run: build every stage of the Colab batch with a fake model (s1a/batch_v4_fake) and summarise the calls and tokens.

python scripts/dry_run_v4.py [--dir results/wf_v4/colab]
Stage 1 is read from <dir> (scripts/batch_build_v4.py); stages 2.. are built in a temporary copy from fake answers, so <dir> gets no
responses. Writes <dir>/manifest_summary.md and <dir>/manifest_dry.csv (one row per job: stage, family, est. prompt tokens, est. output tokens).
Prompt sizes of stages 2.. depend on the fake answers (one group per heading, no relationships), so they are lower bounds for the real run.
Output tokens (guesses, not measured): 4.1 = 10 per column + 300, 4.4 = 40 per column + 150 (columns counted in the prompt), 4.2 500,
4.3 600, e 2,500, placement 120 per call.
"""
import argparse
import csv
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import batch_v4_fake as F  # noqa: E402

FLAT_OUT = {"s4_42": 500, "s4_43": 600, "s4_e": 2500, "s4_place": 120}
PER_COLUMN_OUT = {"s4_41": (10, 300), "s4_44": (40, 150)}


def est_output(job, prompt):
    if job["family"] in PER_COLUMN_OUT:
        each, base = PER_COLUMN_OUT[job["family"]]
        return each * len(re.findall(r"^\[", prompt, re.M)) + base
    return FLAT_OUT[job["family"]]


def run(src, tmp):
    """Stages 1.. in `tmp` (a copy of `src`'s stage 1); returns the manifest rows with est_out added."""
    shutil.copytree(src, tmp, dirs_exist_ok=True)
    jobs = B.read_json(tmp / "manifest.json")["jobs"]
    rows = []
    k = 1
    while jobs:
        bad = F.run_jobs(tmp, jobs)
        assert not bad, f"fake answers with parse errors in stage {k}"
        for j in jobs:
            rows.append({**j, "est_output_tokens": est_output(j, (tmp / j["prompt"]).read_text(encoding="utf-8"))})
        k += 1
        if k > 4 + B.n_place_steps(tmp):
            break
        jobs = B.build_stage(tmp, k, ROOT)
    return rows


def summary(rows):
    by = defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        for key in ((r["stage"], r["family"]), ("total", "all")):
            a = by[key]
            a[0] += 1
            a[1] += r["est_prompt_tokens"]
            a[2] += r["est_output_tokens"]
            a[3] = max(a[3], r["est_prompt_tokens"])
    lines = ["# wf_v4 Colab batch: calls and estimated tokens (dry run with a fake model)", "",
             "Tokens estimated as chars / 3.5; the notebook counts exact tokens (stop above 20,000 for first prompts, 30,000 for any). "
             "Prompts of stages 2+ come from fake answers (lower bounds); output tokens: see scripts/dry_run_v4.py.", "",
             "| stage | family | calls | est. prompt tokens | per call | largest prompt | est. output tokens |", "|---|---|---|---|---|---|---|"]
    for key in sorted((k for k in by if k[0] != "total"), key=lambda k: (k[0], k[1])):
        c, p, o, mx = by[key]
        lines.append(f"| {key[0]} | {key[1]} | {c} | {p:,} | {p // c:,} | {mx:,} | {o:,} |")
    c, p, o, mx = by[("total", "all")]
    lines.append(f"| total | | {c} | {p:,} | {p // c:,} | {mx:,} | {o:,} |")
    return "\n".join(lines) + "\n", (c, p, o)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=ROOT / "results" / "wf_v4" / "colab")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as t:
        rows = run(a.dir, Path(t) / "colab")
    md, tot = summary(rows)
    B.write(a.dir / "manifest_summary.md", md)
    fields = ["job", "stage", "family", "set", "run_tag", "est_prompt_tokens", "est_output_tokens", "max_tokens"]
    with open(a.dir / "manifest_dry.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(md)


if __name__ == "__main__":
    main()
