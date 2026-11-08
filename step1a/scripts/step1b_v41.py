"""wf_v4.1 Step 1b (diary 6 Nov, task 1): build the prompts, then check the dry-run answers.

python scripts/step1b_v41.py --build      -> results/wf_v41/step1b/{prompts/step1b_<set>.{txt,schema.json}, manifest.json, token_counts.md}
python scripts/dryrun_v41.py --dir results/wf_v41/step1b          (Gemini dry run; DRY RUN, not a result)
python scripts/step1b_v41.py --check      -> results/wf_v41/dryrun/step1b_<model>_<set>.json (prompt file, raw, parsed, errors; marked DRY RUN),
                                             results/wf_v41/step1b/labels_<set>.json (loop-2 labels), results/wf_v41/step1b/check.md
Input: results/wf_v4/inputs/<set>/a.columns.json (frozen Step-3 handover columns with examples, input order).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import step1b_v41 as S1B  # noqa: E402

SETS = ("dev50", "dev50b")
OUT = ROOT / "results" / "wf_v41" / "step1b"
DRY = ROOT / "results" / "wf_v41" / "dryrun"
MAX_TOKENS = 16000


def cols_of(set_name):
    return B.read_json(ROOT / "results" / "wf_v4" / "inputs" / set_name / "a.columns.json")


def build(out=OUT):
    """Prompts, schemas and manifest of both sets under `out`; returns the jobs."""
    jobs, lines = [], ["| set | attributes | headings | est. prompt tokens |", "|---|---|---|---|"]
    for s in SETS:
        cols = cols_of(s)
        text, schema = S1B.build_prompt(cols)
        if B._DATASET_WORDS.search(text):
            raise ValueError(f"{s}: dataset name in the prompt")
        name = f"step1b_{s}"
        B.write(out / "prompts" / f"{name}.txt", text)
        B.write_json(out / "prompts" / f"{name}.schema.json", schema)
        jobs.append({"job": name, "family": "s1b", "format": "s1b", "set": s, "run_tag": name, "prompt": f"prompts/{name}.txt",
                     "schema": f"prompts/{name}.schema.json", "max_tokens": MAX_TOKENS, "est_prompt_tokens": S1B.prompt_tokens(text)})
        lines.append(f"| {s} | {len(cols)} | {len({c['id'].split(':')[0] for c in cols})} | {S1B.prompt_tokens(text):,} |")
    B.write_json(out / "manifest.json", {"stage": 1, "jobs": jobs})
    B.write(out / "token_counts.md", "# Step 1b prompt sizes (estimate: pilot_input.est_tokens)\n\n" + "\n".join(lines) + "\n")
    print("\n".join(lines))
    return jobs


def check(out=OUT, dry=DRY):
    """Labels and check.md from the responses under `out`. dry = folder for the DRY RUN copies of the answers (None for a real run)."""
    rep = ["# Step 1b check", ""] + (["**DRY RUN, not a result.** Answers come from a Gemini dry run (prompt and code test only).", ""] if dry else [])
    for s in SETS:
        name = f"step1b_{s}"
        row = B.last_row(out / "responses" / f"{name}.jsonl")
        if row is None:
            rep.append(f"## {s}\nno response\n")
            continue
        cols = cols_of(s)
        a = row["parsed"] if isinstance(row["parsed"], dict) else {}
        errs = list(row["errors"]) + (S1B.validate(a, cols) if a else [])
        model = re.sub(r"[^A-Za-z0-9.-]+", "_", (row.get("model") or "unknown").split(" (")[0]).strip("_")  # short, path-safe
        if dry is not None:
            B.write_json(dry / f"step1b_{model}_{s}.json",
                         {"note": "DRY RUN, not a result", "model": row.get("model"), "prompt": f"results/wf_v41/step1b/prompts/{name}.txt",
                          "guided": row.get("guided"), "prompt_tokens": row.get("prompt_tokens"), "output_tokens": row.get("output_tokens"),
                          "raw": row["raw"], "parsed": row["parsed"], "errors": errs})
        labs = S1B.labels(a, cols) if a else []
        B.write_json(out / f"labels_{s}.json", labs)
        rep += [f"## {s}", f"- model {row.get('model')}, guided JSON {row.get('guided')}, tokens in/out {row.get('prompt_tokens')}/{row.get('output_tokens')}",
                f"- schema and rule errors: {len(errs)}" + "".join(f"\n  - {e}" for e in errs[:30]),
                f"- loop-2 labels kept: {len(labs)}", "", "| heading | keep | rename | merge | flag | new |", "|---|---|---|---|---|---|"]
        for h, c in S1B.summary(a, cols).items():
            rep.append(f"| {h} | {c['keep']} | {c['rename']} | {c['merge']} | {c['flag']} | {c['new']} |")
        rep += ["", "New attributes (name / label / type):"]
        for h in a.get("headings", []):
            rep += [f"- {h['heading']}: {n.get('name')} / {n.get('label')} / {n.get('type')}" for n in h.get("new_attributes", [])]
        rep.append("")
    B.write(out / "check.md", "\n".join(rep) + "\n")
    print("\n".join(rep))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.check:
        check()


if __name__ == "__main__":
    main()
