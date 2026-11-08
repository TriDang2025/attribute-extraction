"""wf_v4.1 dry runs: run the jobs of a manifest with Gemini (or the fake model) and write the response rows like the Colab notebook.

DRY RUN, not a result: these answers test prompts and code only (diary 6 Nov rules; Gemini instead of ChatGPT, user 2026-11-07).

python scripts/dryrun_v41.py --dir <job dir> [--manifest manifest.json] [--model gemini-2.5-pro | fake] [--jobs a,b]
python scripts/dryrun_v41.py --list-models
Needs GEMINI_API_KEY in the environment for Gemini. The model name defaults to config/wf_v41_gemini.json "model".
Calls are cached in <dir>/gemini_cache/ (one file per prompt + settings); responses go to <dir>/responses/<job>.jsonl.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4_fake as F  # noqa: E402
from s1a import gemini_v41 as GM  # noqa: E402

CONFIG = ROOT / "config" / "wf_v41_gemini.json"


def parsers():
    """{format: parse(raw, job, schema) -> (parsed, errors)} for the wf_v4.1 formats; others go to llm_cache.parse_job."""
    from s1a import llm_cache as LC

    def plain_json(raw, job, schema):
        try:
            return json.loads(raw), []
        except json.JSONDecodeError:
            obj, errs = LC._obj_errors(raw, [], lambda o, e: None)
            return obj, errs
    return {"s1b": plain_json, "contam": plain_json, "judge": plain_json}


def run(out, manifest, model_name, jobs_filter=None):
    out = Path(out)
    jobs = json.loads((out / manifest).read_text(encoding="utf-8"))["jobs"]
    if jobs_filter:
        jobs = [j for j in jobs if j["job"] in jobs_filter]
    if model_name == "fake":  # the wf_v4 fake knows the Step-4 formats only
        model = F.respond
    else:
        model = GM.responder(model_name, out / "gemini_cache")
    ps = parsers()

    def parse(raw, job, schema):
        if job["format"] in ps:
            return ps[job["format"]](raw, job, schema)
        from s1a import llm_cache as LC
        return LC.parse_job(raw, job["format"], schema)[:2]
    bad = 0
    for job in jobs:
        bad += F.run_jobs(out, [job], model=model, parse=parse)
        print(f"{job['job']}: done" + (f" ({model.last['output_tokens']} output tokens, cached {model.last['cached']})"
                                       if getattr(model, "last", None) else ""), flush=True)
    return len(jobs), bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path)
    ap.add_argument("--manifest", default="manifest.json")
    ap.add_argument("--model", default=None)
    ap.add_argument("--jobs", default="")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()
    if a.list_models:
        print("\n".join(GM.list_models()))
        return
    model = a.model or json.loads(CONFIG.read_text(encoding="utf-8"))["model"]
    n, bad = run(a.dir, a.manifest, model, set(filter(None, a.jobs.split(","))))
    print(f"{n} jobs, {bad} with parse errors; model {model}; DRY RUN, not a result")


if __name__ == "__main__":
    main()
