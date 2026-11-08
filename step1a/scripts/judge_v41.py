"""wf_v4.1 task 8: Gemini as the second judge of Step 4 v0 (instead of ChatGPT; user choice 2026-11-07).

python scripts/judge_v41.py --build    -> results/wf_v41/judge/{prompts/, manifest.json}: the 16 blind packets as they are, plus 3 repeats
python scripts/dryrun_v41.py --dir results/wf_v41/judge
python scripts/judge_v41.py --collect  -> results/wf_v4/grading/answers/gemini_<code>[_r2].json (judge "gemini"); then
python scripts/read_grades_v4.py       (grades.csv, task11.md with Claude vs Gemini vs user)
Each packet is sent as the only message of a new call, without a JSON schema (as in a chat), at temperature 1.0 so that a repeat is a new
sample. The repeats are the codes the diary gave ChatGPT (key.json "repeats.chatgpt").
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import step4_grades as R  # noqa: E402

GRADING = ROOT / "results" / "wf_v4" / "grading"
OUT = ROOT / "results" / "wf_v41" / "judge"
JUDGE = "gemini"


def build():
    key = B.read_json(GRADING / "key.json")
    jobs = []
    packets = sorted(GRADING.glob("packets/*.md"))
    for p in packets + [q for q in packets if q.stem.split("_")[1] in key["repeats"]["chatgpt"]]:
        code = p.stem.split("_")[1]
        name = f"{JUDGE}_{code}" + ("_r2" if any(j["job"] == f"{JUDGE}_{code}" for j in jobs) else "")
        B.write(OUT / "prompts" / f"{name}.txt", p.read_text(encoding="utf-8"))
        B.write(OUT / "prompts" / f"{name}.schema.json", "null")
        jobs.append({"job": name, "family": "judge", "format": "judge", "set": p.stem.split("_")[0], "run_tag": name, "code": code,
                     "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": 8192, "temperature": 1.0})
    B.write_json(OUT / "manifest.json", {"stage": 1, "jobs": jobs})
    print(len(jobs), "judge jobs")


def collect():
    jobs = B.read_json(OUT / "manifest.json")["jobs"]
    ok, bad = 0, []
    for j in jobs:
        row = B.last_row(OUT / "responses" / f"{j['job']}.jsonl")
        if row is None:
            bad.append(f"{j['job']}: no response")
            continue
        try:
            d = R.parse_answer(row["raw"], j["code"])
        except (ValueError, json.JSONDecodeError) as e:
            bad.append(f"{j['job']}: {e}")
            continue
        d["model"] = f"{row.get('model')} (Gemini API, temperature 1.0, packet only)"
        B.write_json(GRADING / "answers" / f"{j['job']}.json", d)
        ok += 1
    print(f"{ok} answers saved, {len(bad)} not:", *bad, sep="\n  ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.collect:
        collect()


if __name__ == "__main__":
    main()
