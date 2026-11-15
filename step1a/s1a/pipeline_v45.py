"""wf_v4.5 (diary Nov 15) W2: the frozen pipeline on a raw corpus, without gold (Step 1a-2: corpus_v45; Step 3 v4.4; Step 4 v4.4).

The frozen Step 3 / Step 4 code reads its sets, entities and frozen prompt folders from module constants (dev50 / dev50b, train / hotel /
restaurant). `use_corpus` registers the corpus as one more "set" by repointing those constants for the run (the frozen functions are
not edited):
- set name = run key = `set_name`; entities = every predicted Step 1a entity, named by corpus_v45.entity_names (no gold);
- the A prompts (3 orders) and split prompts are built from the corpus with the frozen builders (pilot_build_v37.a_prompts, PIN.render_split)
  into <out>/a_prompts (the layout of results/wf_v42/t1b_step3_keyed);
- gold-only inputs are empty: gold_values.csv, labels.csv (all "unlabelled"), final_v39.ROLE_FILES (used only by the old handover docs), GT
  (no Step 3 scoring here: the final columns are built with final_v39.entity_columns, as step3_post_v43.score does).
Checked on raw dev50 (corpus n50, laptop, fake LLM): the Step 1a-2 mentions, clusters and entities equal results/graph_v22_dev50, and the A
prompts of train / hotel / restaurant equal the frozen T1B prompts byte for byte (LF); the corpus run adds the entities attraction, attraction_2.
Run folders: <out>/step3 (Step 3 v4.4 layout), <out>/step4 (Step 4 v4.4 layout); outputs <out>/{schema.sql, attributes.json, cost.json}.
"""
import contextlib
import json
import time
from pathlib import Path

import pandas as pd

from . import batch_v4 as B
from . import corpus_v45 as CO
from . import log_v44 as LOG
from . import paths
from . import pilot_input as PIN
from . import run_data_v37 as RD
from . import step3_post_v43 as PP
from . import step3_v43 as S3_43
from . import step3_v44 as S3
from . import step4_v44 as S4

ROOT = paths.ROOT
ORDERS = (0, 1, 2)


def _scripts():
    return {n: PP.script(n) for n in ("pilot_build_v37", "dashboard_v38", "batch_build_v39", "final_v39", "score_t14_v37")}


# ---------------------------------------------------------------- A and split prompts of the corpus (frozen builders)
def build_prompts(set_name, entmap, a_dir, seed=0):
    """<a_dir>/{prompts/, manifest.json, examples.csv} like pilot_build_v37.main for one run: per entity the A prompt in 3 orders
    (a_prompts: k fit, order seeds) and a split prompt per split candidate (min_share 0, k 16). entmap = {name: entity id}. Returns the jobs."""
    P = _scripts()["pilot_build_v37"]
    a_dir = Path(a_dir)
    (a_dir / "prompts").mkdir(parents=True, exist_ok=True)
    ri = P.RunInput(CO.run_dir(set_name).relative_to(ROOT), seed)
    jobs, ex_rows = [], []

    def emit(name, text, schema, job, exs, max_tokens):
        B.write(a_dir / "prompts" / f"{name}.txt", text)
        B.write_json(a_dir / "prompts" / f"{name}.schema.json", schema)
        jobs.append({**job, "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": max_tokens,
                     "est_prompt_tokens": PIN.est_tokens(text)})
        ex_rows.extend((ex, job["entity"], c, mid, job["job"]) for ex, c, mid in exs)

    find = PIN.find_pilot_entity
    PIN.find_pilot_entity = lambda mentions, ent: entmap[ent]       # predicted entity, not the gold majority
    try:
        for ent in entmap:
            entity, k, inp, texts = P.a_prompts(ri, ent)
            exs = [(ex, c.cluster_id, mid) for c in inp.clusters for ex, mid in c.examples]
            for s in ORDERS:
                name = P.a_name(ent, set_name, s)
                emit(name, texts[s], PIN.schema_v2(inp),
                     {"job": name, "entity": entity, "ent": ent, "variant": "v2", "run_tag": f"s{s}", "kind": "entity", "stage": 1, "nbhd": None,
                      "cluster_id": "", "format": "v2", "round": 0, "carry_from": [], "family": "a", "run": set_name, "k": k},
                     exs, P.max_tokens(PIN.est_tokens(texts[s])))
            for cid in PIN.split_candidates(ri.export, entity, min_share=0.0):
                text, sx = PIN.render_split(ri.export, ri.docs, entity, cid, 16, seed)
                name = P.split_name(ent, set_name, cid)
                emit(name, text, PIN.schema_split(cid, [e for e, _ in sx]),
                     {"job": f"{name}_r1", "entity": entity, "ent": ent, "variant": f"split_{cid.replace('#', '-')}", "run_tag": "r1",
                      "kind": "split", "stage": 1, "nbhd": None, "cluster_id": cid, "format": "split", "round": 0, "carry_from": [],
                      "family": "split", "run": set_name}, [(e, cid, m) for e, m in sx], P.SPLIT_MAX_TOKENS)
    finally:
        PIN.find_pilot_entity = find
    B.write_json(a_dir / "manifest.json", {"runs": {set_name: CO.run_dir(set_name).relative_to(ROOT).as_posix()}, "jobs": jobs})
    pd.DataFrame(ex_rows, columns=P.ENT_RUN_COLS).to_csv(a_dir / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    return jobs


# ---------------------------------------------------------------- the corpus as a set of the frozen code
@contextlib.contextmanager
def use_corpus(set_name, entmap, a_dir):
    """Repoint the module constants of the frozen Step 3 code at the corpus run (restored on exit)."""
    sc = _scripts()
    D, BB9, FV, T = sc["dashboard_v38"], sc["batch_build_v39"], sc["final_v39"], sc["score_t14_v37"]
    from . import dashboard_v38 as DB
    a_dir = Path(a_dir)
    ents = tuple(entmap)
    run_rel = CO.run_dir(set_name).relative_to(ROOT).as_posix()
    patches = [
        (PP, "SETS", (set_name,)), (PP, "ENTS", ents), (PP, "RUN_KEY", {set_name: set_name}), (PP, "T1B", a_dir),
        (PP, "SPLIT_SRC", {set_name: (a_dir, set_name)}),
        (PP, "A_EX_SRC", {set_name: tuple((a_dir / "examples.csv", "{ent}_a_" + set_name + f"_s{s}") for s in ORDERS)}),
        (PP, "t1b_a_jobs", lambda: [{**j, "set": set_name} for j in PP._manifest_jobs(a_dir) if j["family"] == "a"]),
        (RD, "GOLD_ENTS", {e: [e] for e in ents}), (RD, "entity_ids", lambda mentions, gold_ents=None: dict(entmap)),
        (DB, "ENTS", ents), (D, "SETS", {set_name: {"run": run_rel, "key": set_name, "orders": T.NEW_ORDERS}}),
        (BB9, "RUN_KEY", {set_name: set_name}), (BB9, "SPLIT_DIR", {set_name: (run_rel, "")}),
        (FV, "ENT_NAME", {e: e for e in ents}), (FV, "ROLE_FILES", {set_name: []}),
    ]
    old = [(m, k, getattr(m, k)) for m, k, _ in patches]
    try:
        for m, k, v in patches:
            setattr(m, k, v)
        yield
    finally:
        for m, k, v in old:
            setattr(m, k, v)


# ---------------------------------------------------------------- Step 3 (frozen v4.4) without the GT scoring
def final_columns(out, set_name):
    """scores/final_columns.json of the run folder the way step3_post_v43.score builds it, without GT: final_v39.entity_columns per entity."""
    out = Path(out)
    FV = _scripts()["final_v39"]
    jobs = PP.manifest_all(out)
    rc_jobs = [j for j in jobs if j["family"] == "reconcile"]
    dup_jobs = {(j["set"], j["ent"], j["order_seed"]): j for j in jobs if j["family"] == "dupcheck_rc"}
    tables = B.read_json(out / "columns.json")
    responses = PP.script("score_v38").read_responses(out)
    final = {set_name: {}}
    for ent in PP.ENTS:
        t = tables[set_name][ent]
        b = FV.entity_columns(set_name, ent, t, responses, rc_jobs, dup_jobs)
        final[set_name][ent] = [{k: v for k, v in c.items() if k not in ("pools", "value_types")} | {"entity": t["entity"]} for c in b["final"]]
    (out / "scores").mkdir(exist_ok=True)
    B.write_json(out / "scores" / "final_columns.json", final)
    return final


def step3(set_name, out, backend, encoder, cfg=None):
    """build -> run (names, keyed split, rescue, merge, reconcile, dupcheck) -> final columns -> a_llama44/<set>/a.columns.json."""
    cfg = cfg or S3.load_config()
    vecs = {set_name: S3.cluster_vectors(set_name)} if cfg["switches"]["similar_batches"] else None
    S3.build(out, cfg, None, vecs)
    info = S3.run(out, backend, cfg, encoder, Path(out) / "name_vecs.npz", True)
    final_columns(out, set_name)
    return info, S3.write_a_llama44(out)


# ---------------------------------------------------------------- Step 4 (frozen after W1)
def step4(set_name, out, backend, step3_out, cfg):
    return S4.run(out, backend, inputs=("a_llama44",), sets=(set_name,), cfg=cfg, step3_dirs={"a_llama44": Path(step3_out) / "a_llama44"})


# ---------------------------------------------------------------- outputs
def cost(out, step1a_info, load_seconds=None):
    """{step: calls, prompt / output tokens, retried, model seconds} from the call logs of step3 and step4, plus the Step 1a times."""
    res = {"step1a_2": {"llm_calls": 0, "seconds": step1a_info.get("seconds") if step1a_info else None}, "model_load_seconds": load_seconds}
    for step in ("step3", "step4"):
        rows = [r for r in LOG.call_rows(Path(out) / step)]
        t = LOG.call_totals(rows)
        secs = [r.get("job_seconds") for r in rows if r.get("job_seconds") not in (None, "")]
        res[step] = {**t, "model_seconds": round(sum(float(s) for s in secs), 1) if secs else None}
    res["total_llm"] = {k: sum(res[s][k] for s in ("step3", "step4")) for k in ("calls", "prompt_tokens", "output_tokens")}
    return res


def outputs(out, set_name, step1a_info=None, load_seconds=None):
    """<out>/schema.sql (the voted Step 4 schema), attributes.json ({entity: [column names]} of the Step 3 final columns), cost.json."""
    out = Path(out)
    st = B.read_json(out / "step4" / "final" / "status.json")
    ok = {r["run"] for r in st if r["ok"]}
    # the voted schema, else the first finished seed; none finished -> no schema.sql, the chain errors go to cost.json
    run = next((r for r in [f"a_llama44_{set_name}_vote"] + [f"a_llama44_{set_name}_s{s}" for s in (0, 1, 2)] if r in ok), None)
    if run:
        (out / "schema.sql").write_text((out / "step4" / "final" / run / "schema.sql").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    final = B.read_json(out / "step3" / "scores" / "final_columns.json")[set_name]
    B.write_json(out / "attributes.json", {e: [c["name"] for c in cols] for e, cols in final.items()})
    c = {**cost(out, step1a_info, load_seconds), "schema_from": run, "step4_chains_finished": f"{len(ok)}/{len(st)}",
         "step4_errors": {r["run"]: r["error"] for r in st if not r["ok"]},
         "step3_columns": sum(len(cols) for cols in final.values())}
    B.write_json(out / "cost.json", c)
    return c


# ---------------------------------------------------------------- W2 dev50 check (corpus n50 = dev50)
def compare_step3(out, set_name, frozen=ROOT / "results" / "wf_v44" / "t4", frozen_set="dev50"):
    """Markdown rows: per entity, final column names of the corpus run vs the frozen Step 3 run (entities the frozen run lacks: 'new')."""
    mine = B.read_json(Path(out) / "step3" / "scores" / "final_columns.json")[set_name]
    old = B.read_json(Path(frozen) / "scores" / "final_columns.json")[frozen_set]
    rows = ["| entity | columns (corpus) | columns (frozen) | same names | only corpus | only frozen |", "|---|---|---|---|---|---|"]
    for ent, cols in mine.items():
        a = {c["name"] for c in cols}
        b = {c["name"] for c in old.get(ent, [])} if ent in old else None
        rows.append(f"| {ent} | {len(a)} | {'new' if b is None else len(b)} | {'-' if b is None else len(a & b)} | "
                    f"{'-' if b is None else ', '.join(sorted(a - b)) or 'none'} | {'-' if b is None else ', '.join(sorted(b - a)) or 'none'} |")
    return rows


def score_step4_as(out, set_name, as_set="dev50"):
    """Score the corpus Step 4 chains as `as_set` (same dialogues) with the frozen scorer: copies final/ and score_map/ into
    <out>/step4_as_<as_set>/ with the set renamed, then t6_step4_v44.score. Returns that folder."""
    import shutil
    T6 = PP.script("t6_step4_v44")
    src, dst = Path(out) / "step4", Path(out) / f"step4_as_{as_set}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src / "final", dst / "final")
    shutil.copytree(src / "score_map" / "a_llama44" / set_name, dst / "score_map" / "a_llama44" / as_set)
    B.write_json(dst / "final" / "status.json", [{**r, "set": as_set} for r in B.read_json(src / "final" / "status.json")])
    for p in ("responses", "manifests"):
        if (src / p).exists():
            shutil.copytree(src / p, dst / p)
    T6.score(dst)
    return dst


STEP4 = {"v44_other_off": dict(off=("other_choice",)), "v43": dict(off=S4.SWITCHES)}   # W1 decides; all switches off = the v4.3 chain


def step4_config(choice):
    return S4.with_switches(S4.load_config(), **STEP4[choice])


def run_pipeline(corpus, out, set_name, backend, encoder, enc_1a, step4_cfg, load_seconds=None, log=print, skip_1a=False, backend4=None):
    """The whole command (backend4: Step 4 backend when it differs, e.g. the laptop fakes). Returns the cost dict."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    info1 = None if skip_1a else CO.step1a(corpus, set_name, enc_1a, log=log)
    entmap = CO.entity_map(set_name)
    B.write_json(out / "entities.json", entmap)
    a_dir = out / "a_prompts"
    with use_corpus(set_name, entmap, a_dir):
        build_prompts(set_name, entmap, a_dir)
        log(f"step 3: {len(entmap)} entities {entmap}")
        step3(set_name, out / "step3", backend, encoder)
        log("step 4")
        step4(set_name, out / "step4", backend4 or backend, out / "step3", step4_cfg)
    c = outputs(out, set_name, info1, load_seconds)
    c["wall_seconds"] = round(time.time() - t0, 1)
    B.write_json(out / "cost.json", c)
    return c
