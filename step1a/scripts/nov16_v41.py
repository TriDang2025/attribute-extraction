"""wf_v4.1 diary Nov 7 task 7: the Nov 16 run. Seven stages in order, saved after each one, restartable after a crash.

python scripts/nov16_v41.py --model fake [--run results/wf_v41/nov16/fake] [--stop-after loop2]
    no GPU: the fake model (s1a/nov16_v41.FakeLLM). Loop 2 runs for real, so use the chunking venv (gliner, sentence-transformers).
python scripts/nov16_v41.py --calls results/wf_v41/nov16/<tag>      -> rewrites <run>/calls.csv and calls.md (calls and tokens per stage)
On Colab, colab/S1A_nov16_v41_colab.ipynb makes an s1a/nov16_v41.VllmBackend and calls run_all(run_dir, backend, on_saved=push).

Stages (all output under <run>/; state.json lists the finished ones, a rerun skips them; an LLM stage skips the jobs that already have
a response, so a crash costs at most the batch in flight):
  step1b         step1b/: prompts, responses, labels_<set>.json, check.md                      (scripts/step1b_v41.py)
  loop2          loop2/<set>/: clusters.json, evidence.csv, summary.md, run_info.json         (scripts/loop2_v41.py; GLiNER + bge-m3)
  step3_l2       step3_loop2/<set>/: frozen Step 3 A prompts, 3 orders per entity with kept clusters, answers.md (scripts/step3_loop2_v41.py)
  dupcheck       step3_loop2/<set>/: v3.8 duplicate check, 2 orders, columns_l2.json, dupcheck.md
  step4          step4/: inputs/<set>/a2.columns.json, Step 4 v4.1 chains 4.1-4.4 (18 chains), final/ (batch_v4.assemble_all)
  contamination  contamination/: the probe prompt, its answer, scores.{csv,md}                 (s1a/contamination_v41.py)
  task13         task13/: the v4 placement test: base chain copied from results/wf_v4/colab (real Qwen answers), placement stages 5-9
"""
import argparse
import csv
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

from s1a import batch_v4 as B  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402

REPLAY = [ROOT / "results" / "wf_v41" / d for d in ("step1b", "step4_dryrun", "step4_dryrun_a")]   # the fake model's saved answers
V4_COLAB = ROOT / "results" / "wf_v4" / "colab"
LOOP2_CONFIG = ROOT / "config" / "wf_v41_loop2.json"
GT = ROOT / "gt" / "schema_gt_v1.yaml"


def _ns(**kw):
    return type("A", (), kw)()


def _jobs(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["jobs"] if Path(path).exists() else []


# ---------------------------------------------------------------- stages
def stage_step1b(run, llm, ctx):
    import step1b_v41 as S
    out = run / "step1b"
    res = llm.run(out, S.build(out))
    S.check(out, dry=None)
    labels = {s: len(B.read_json(out / f"labels_{s}.json")) for s in NV.SETS}
    return {**res, "labels": labels}


def stage_loop2(run, llm, ctx):
    import loop2_v41 as L
    from s1a import spans as SP
    cfg = json.loads(LOOP2_CONFIG.read_text(encoding="utf-8"))
    enc = ctx["encoder"]()
    predict = L.GlinerPredictor(SP.load())
    kept = {}
    for s in NV.SETS:
        cl = L.probe(s, run / "step1b" / f"labels_{s}.json", cfg, enc, predict, run / "loop2" / s)
        kept[s] = sum(c["keep"] for c in cl)
    enc.save()
    return {"kept": kept}


def _step3_script(run):
    import step3_loop2_v41 as SC
    SC.RUN_ROOT = run
    return SC


def stage_step3_l2(run, llm, ctx):
    from s1a import step3_loop2_v41 as S3
    SC, info = _step3_script(run), {}
    for s in NV.SETS:
        clusters = json.loads((run / "loop2" / s / "clusters.json").read_text(encoding="utf-8"))
        if not S3.select_clusters(clusters):
            info[s] = "no kept cluster"
            continue
        a = _ns(set=s, include_dropped=False, seed=0)
        SC.build(a)
        info[s] = llm.run(SC.out_dir(s), _jobs(SC.out_dir(s) / "manifest.json"))
        SC.check(a)
    return info


def stage_dupcheck(run, llm, ctx):
    SC, info = _step3_script(run), {}
    for s in NV.SETS:
        if not (SC.out_dir(s) / "manifest.json").exists():
            info[s] = "no Step 3 jobs"
            continue
        a = _ns(set=s)
        SC.dupcheck_build(a)
        info[s] = llm.run(SC.out_dir(s), _jobs(SC.out_dir(s) / "manifest_dupcheck.json"))
        SC.dupcheck_apply(a)
    return info


def a2_inputs(run):
    """Write step4/inputs/<set>/a2.columns.json (+ a2_added.json); returns {set: path relative to ROOT}."""
    files = {}
    for s in NV.SETS:
        a_cols = B.read_json(ROOT / B.INPUT_DIR / s / "a.columns.json")
        fin = run / "step3_loop2" / s / "columns_l2.json"
        final = B.read_json(fin) if fin.exists() else {}
        clusters = {c["id"]: c for c in B.read_json(run / "loop2" / s / "clusters.json")}
        cols, added = NV.a2_columns(a_cols, final, clusters)
        p = run / "step4" / "inputs" / s / "a2.columns.json"
        B.write_json(p, cols)
        B.write_json(p.with_name("a2_added.json"), [{"id": i, "name": n, "clusters": c} for i, n, c in added])
        files[s] = Path(os.path.relpath(p, ROOT)).as_posix()
    return files


def stage_step4(run, llm, ctx):
    out = run / "step4"
    chains = NV.step4_chains(a2_inputs(run))
    info = {"chains": len(chains), "stage1": llm.run(out, B.build_chains_stage1(out, chains, ROOT).save())}
    for k in (2, 3, 4):
        info[f"stage{k}"] = llm.run(out, B.build_stage(out, k, ROOT))
    status = [r for r in B.assemble_all(out, ROOT) if r["kind"] == "main"]
    info["finished"] = f"{sum(r['ok'] for r in status)}/{len(status)}"
    return info


def stage_contamination(run, llm, ctx):
    from s1a import contamination_v41 as C
    from s1a.step4_gt import load_gt
    out = run / "contamination"
    text, schema = C.build()
    B.write(out / "prompts" / "contamination.txt", text)          # names the dataset on purpose: not via batch_v4.Jobs
    B.write_json(out / "prompts" / "contamination.schema.json", schema)
    job = {"job": "contamination", "family": "s4_e", "format": "s4_e", "run_tag": "contamination", "stage": 1, "round": 0,
           "prompt": "prompts/contamination.txt", "schema": "prompts/contamination.schema.json", "max_tokens": B.MAX_TOKENS["s4_e"]}
    B.write_json(out / "manifest.json", {"stage": 1, "jobs": [job]})
    res = llm.run(out, [job])
    sc = C.score_answer(C.load_answer(out / "responses" / "contamination.jsonl"), load_gt(GT))
    pd.DataFrame([C.flat(sc)]).to_csv(out / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
    B.write(out / "scores.md", C.report_md(sc))
    return {**res, "columns_named": f"{sc['columns_named']['k']}/{sc['columns_named']['n']}"}


def stage_task13(run, llm, ctx):
    """The v4 placement test (gpu_todo.md): base chain answers copied from the v4 Qwen run, then one stage per held-out column."""
    out = run / "task13"
    base = [c for c in B.read_json(V4_COLAB / "chains.json") if c["kind"] == "base"]
    B.write_json(out / "chains.json", base)
    shutil.copy(V4_COLAB / "placement.json", out / "placement.json")
    for k in (1, 2, 3, 4):
        name = f"{base[0]['id']}_4{k}.jsonl"
        (out / "responses").mkdir(parents=True, exist_ok=True)
        shutil.copy(V4_COLAB / "responses" / name, out / "responses" / name)
    info = {}
    for k in range(5, 5 + B.n_place_steps(out)):
        info[f"stage{k}"] = llm.run(out, B.build_stage(out, k, ROOT))
    st = [r for r in B.assemble_all(out, ROOT) if r["kind"] == "place"]
    info["placement"] = {r["run"]: "ok" if r["ok"] else r["error"] for r in st}
    return info


STAGE_FN = {"step1b": stage_step1b, "loop2": stage_loop2, "step3_l2": stage_step3_l2, "dupcheck": stage_dupcheck, "step4": stage_step4,
            "contamination": stage_contamination, "task13": stage_task13}
assert tuple(STAGE_FN) == NV.STAGES


# ---------------------------------------------------------------- calls table
def call_rows(run):
    """One row per answered job of the run: stage, folder, job, family, guided, errors, tokens, seconds (batch_seconds / batch_size)."""
    rows = []
    for p in sorted(Path(run).rglob("responses/*.jsonl")):
        r = B.last_row(p)
        if r is None:
            continue
        rel = p.relative_to(run).parts
        copied = rel[0] == "task13" and p.stem.startswith("base_")      # the v4 base chain, not a call of this run
        rows.append({"stage_dir": "/".join(rel[:-2]), "job": p.stem, "format": r.get("format", ""), "model": r.get("model", ""),
                     "copied": copied, "guided": r.get("guided"), "errors": len(r.get("errors") or []),
                     "prompt_tokens": r.get("prompt_tokens", 0), "output_tokens": r.get("output_tokens", 0),
                     "seconds": round(r["batch_seconds"] / r["batch_size"], 2) if r.get("batch_size") else ""})
    return rows


def write_calls(run):
    rows = call_rows(run)
    if not rows:
        return rows
    with open(Path(run) / "calls.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    df = pd.DataFrame(rows)
    df = df[~df["copied"]]
    g = df.groupby(df["stage_dir"].str.split("/").str[0]).agg(calls=("job", "size"), errors=("errors", lambda x: int((x > 0).sum())),
                                                               prompt_tokens=("prompt_tokens", "sum"), output_tokens=("output_tokens", "sum"))
    lines = ["# Calls of this run", "", "| folder | calls | with parse errors | prompt tokens | output tokens |", "|---|---|---|---|---|"]
    lines += [f"| {i} | {r.calls} | {r.errors} | {r.prompt_tokens:,} | {r.output_tokens:,} |" for i, r in g.iterrows()]
    lines.append(f"| total | {int(g.calls.sum())} | {int(g.errors.sum())} | {int(g.prompt_tokens.sum()):,} | {int(g.output_tokens.sum()):,} |")
    B.write(Path(run) / "calls.md", "\n".join(lines) + "\n")
    return rows


# ---------------------------------------------------------------- run
def run_all(run, llm, encoder=None, on_saved=None, stop_after=None, log=print):
    """Run the stages not yet in state.json; after each one mark it done, rewrite calls.csv and call on_saved(stage) (the notebook
    commits and pushes there). encoder() makes the bge-m3 encoder of loop 2 (default scripts/run.py encoder)."""
    run = Path(run)
    run.mkdir(parents=True, exist_ok=True)
    if encoder is None:
        from run import encoder
    ctx = {"encoder": encoder}
    for stage in NV.STAGES:
        if stage in NV.load_state(run)["done"]:
            log(f"== {stage}: done before, skipped")
        else:
            log(f"== {stage}")
            t0 = time.time()
            info = STAGE_FN[stage](run, llm, ctx)
            NV.mark_done(run, stage, {"seconds": round(time.time() - t0, 1), "model": llm.model_id, **(info or {})})
            write_calls(run)
            log(f"== {stage} done in {time.time() - t0:.0f} s: {json.dumps(info, default=str)[:600]}")
            if on_saved:
                on_saved(stage)
        if stage == stop_after:
            break
    return NV.load_state(run)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", choices=["fake"], help="the laptop runs the fake model only; Qwen / Llama run in the notebook")
    ap.add_argument("--run", type=Path)
    ap.add_argument("--stop-after", choices=NV.STAGES)
    ap.add_argument("--calls", type=Path, help="rewrite calls.csv / calls.md of a run folder")
    a = ap.parse_args()
    if a.calls:
        write_calls(a.calls)
        print((a.calls / "calls.md").read_text(encoding="utf-8"))
        return
    if not a.model:
        ap.error("give --model fake or --calls <run>")
    run = a.run or ROOT / "results" / "wf_v41" / "nov16" / "fake"
    fake = NV.FakeLLM(REPLAY)
    state = run_all(run, fake, stop_after=a.stop_after)
    print(f"done: {state['done']}; fake answers replayed {fake.n_replayed}, made {fake.n_made}")


if __name__ == "__main__":
    main()
