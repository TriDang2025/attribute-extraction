"""wf_v4.2 (diary Nov 10) T1, option A of the T0 report: the frozen Step 3 A prompt with Llama, unchanged; count the failures.

python scripts/t1_step3_v42.py --build [--out DIR]   -> DIR/manifest.json + prompts (default results/wf_v42/t1_step3)
python scripts/t1_step3_v42.py --fake  [--out DIR]   -> nov16_v41.FakeLLM answers (laptop plumbing test only)
python scripts/t1_step3_v42.py --check [--out DIR]   -> DIR/check.md + check.csv (s1a/check_v42.py)
On Colab, colab/S1A_wf42_colab.ipynb cell 7 runs the jobs with nov16_v41.VllmBackend between --build and --check.

18 jobs = 3 entities x 3 orders x 2 sets, the prompt and schema files copied byte for byte from the Qwen runs that STEP3.md is built on:
- dev50 (Step 1a v2.2): order s0 = loop1_v31 {ent}_v2, s1 = loop1_v31 {ent}_v2_r2, s2 = loop1_v36/colab {ent}_v2_s2
  (score_t14_v37 OLD_ORDERS A r1 / A r2 / A s2); job names {ent}_a_v22d50_s{0,1,2}, run key v22d50.
- dev50b (v2.2): loop1_v37/colab {ent}_a_v22d50b_s{0,1,2}, manifest rows as they are.
Only the A calls; the split pass, reconcile and duplicate check of STEP3.md need A answers that parse.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import check_v42 as C  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402

OUT = ROOT / "results" / "wf_v42" / "t1_step3"
R = ROOT / "results"
ENTS = ("train", "hotel", "restaurant")
DEV50_SRC = ((R / "loop1_v31", "{ent}_v2"), (R / "loop1_v31", "{ent}_v2_r2"), (R / "loop1_v36" / "colab", "{ent}_v2_s2"))
DEV50B_DIR = R / "loop1_v37" / "colab"


def manifest_jobs(d):
    m = B.read_json(d / "manifest.json")
    return m["jobs"] if isinstance(m, dict) else m


def copy_job(src_dir, job, out, name=None):
    """Copy the prompt + schema of `job` from src_dir to out/prompts (renamed to `name` when given); returns the new manifest row."""
    row = dict(job)
    for k, ext in (("prompt", ".txt"), ("schema", ".schema.json")):
        dst = f"prompts/{name}{ext}" if name else job[k]
        (out / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_dir / job[k], out / dst)
        row[k] = dst
    return row


def build(out):
    out, jobs = Path(out), []
    for ent in ENTS:
        for s, (d, stem) in enumerate(DEV50_SRC):
            src = next(j for j in manifest_jobs(d) if j["prompt"] == f"prompts/{stem.format(ent=ent)}.txt" and j["format"] == "v2")
            name = f"{ent}_a_v22d50_s{s}"
            row = copy_job(d, src, out, name)
            row.update(job=name, run_tag=f"s{s}", family="a", run="v22d50", source=f"{d.relative_to(ROOT).as_posix()}/{src['job']}")
            jobs.append(row)
    jobs += [copy_job(DEV50B_DIR, j, out) for j in manifest_jobs(DEV50B_DIR) if j.get("family") == "a" and j.get("run") == "v22d50b"]
    if len(jobs) != 18:
        raise ValueError(f"expected 18 A jobs, got {len(jobs)}")
    B.write_json(out / "manifest.json", {"stage": 1, "jobs": jobs})
    return jobs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true")
    g.add_argument("--fake", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if a.build:
        print(f"{len(build(a.out))} jobs in {a.out}")
    elif a.fake:
        print(NV.FakeLLM().run(a.out, B.read_json(a.out / "manifest.json")["jobs"]))
    else:
        rows, _ = C.write_check(a.out, "wf_v4.2 T1: frozen Step 3 A prompt with Llama (18 calls)")
        print((a.out / "check.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
