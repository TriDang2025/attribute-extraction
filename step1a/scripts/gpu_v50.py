"""wf_v5.0 G4 + G5 GPU job, called by the notebook colab/S1A_wf50_colab.ipynb (one session, model loaded once). Laptop: --prepare | --fake.

Laptop --prepare also writes g4/<set>/w2_vectors.npz (laptop bge-m3 vectors of the replay texts; Colab uses CachedEnc so the replay cosines are
the laptop ones) and g4/run/<set>/ without renames.
G4: rename the loop-1 columns whose mentions the G3 context split changed (results/wf_v50/g3/ctxsplit/big40/<set>/final_columns.json): one
    frozen Step 3 names prompt (step3_v43.render_names, the entity's "other entities" lines from its s0 A prompt) per entity, each changed column
    as one block (id "<stage-1 entity>#col<cid>", up to 8 examples by pilot_input.select_examples). Jobs written by --prepare to
    results/wf_v50/g4/<set>/{manifest_names.json, prompts/}; answers -> responses/; a valid name (step3_v43.validate_names, not "not_attribute")
    replaces the column name -> results/wf_v50/g4/run/<set>/step3/scores/final_columns.json + renames.csv.
Input build (CPU, after G4): the loop-1 Step 4 input a_llama44 (step3_v43.a_columns, checked to rebuild v4.9 exactly), then the wf_v4.8 W2
    loop-2 replay (scripts/replay_v48.run_set, bge-m3) on run/<set>/ (= wf_v47 z4 run 1 with the new loop-1 files) -> g4/w2/<set>/, then
    gpu_v48.prepare -> results/wf_v50/g5/<set>/input/a_llama44/<run>/a.columns.json.
G5: Step 4 variant ARM = A+R (p2_batch 20, p2_reask) + p2_reask2 (s1a/step4_reask_v50.py) + merge_same_entity (B+M), seeds 0-2, dev50 and
    dev50b -> results/wf_v50/g5/<set>/step4_ARM/. Scoring on the laptop afterwards.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import gpu_v46 as G46  # noqa: E402
import gpu_v48 as G48  # noqa: E402
import replay_v48 as R48  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import step3_v43 as S3  # noqa: E402
from s1a import step3_v44 as S3_44  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402

RES = ROOT / "results" / "wf_v50"
G3_FINAL = RES / "g3" / "ctxsplit" / "big40"
G4 = RES / "g4"
G5 = RES / "g5"
SETS, SEEDS, Y3, LOOP1 = G48.SETS, G48.SEEDS, G48.Y3, G48.LOOP1
G48.VARIANTS["ARM"] = {**G48.VARIANTS["A"], "p2_reask": True, "p2_reask2": True, "merge_same_entity": True}
# The first G5 run (2026-11-22, step4_ARM) got finish_reason "error" on every guided Step 4 call and used the unguided fallback, so it is not
# comparable with v4.9; the rerun writes step4_ARMg (same settings) and must be guided throughout (unguided_rows / guided_smoke).
G48.VARIANTS["ARMg"] = dict(G48.VARIANTS["ARM"])


# ---------------------------------------------------------------- G4 prompts (laptop)
def changed_columns(old, new):
    """{entity: [new column dicts]} whose set of mention ids differs between the two final_columns of one set."""
    out = {}
    for ent, cols in new.items():
        before = {c["cid"]: set(c["mention_ids"]) for c in old[ent]}
        out[ent] = [c for c in cols if set(c["mention_ids"]) != before.get(c["cid"], set())]
    return {e: cs for e, cs in out.items() if cs}


def block_id(entity, cid):
    return f"{entity}#col{cid}"


def column_block(export, docs, entity, col, k=PIN.K_EXAMPLES, seed=0, context=None):
    """(block id, block text) of a column as one names-prompt cluster block (same lines as a frozen A prompt block). context(block id, column)
    -> snippet lines (wf_v5.1 R4) added after the example lines; None = the v5.0 block."""
    bid = block_id(entity, col["cid"])
    m = export.mentions
    g = m[m["mention_id"].astype(int).isin({int(i) for i in col["mention_ids"]})].assign(cluster_id=bid)
    exs = [(f"{bid}:{j}", int(mid)) for j, mid in enumerate(PIN.select_examples(g, k, seed))]
    ci = PIN.ClusterInput(bid, len(g), g["norm_value"].nunique(), False, exs)
    block = "\n".join([PIN._cluster_head(ci), "Examples:", *PIN._example_lines(export, docs, ci, True)])
    if context is not None:
        from s1a import rolenames_v51 as RN
        block = RN.add_context(block, context(bid, col))
    return bid, block


def g4_jobs(dev, run, out=G4, old=None, new=None, context=None, variant=None):
    """Names jobs (one per entity with changed columns) of one set -> <out>/<dev>/{manifest_names.json, prompts/, changed.json}.
    old / new = final_columns.json files to compare (default: the v4.9 loop-1 columns and the G3 context split); context: see column_block.
    variant: step3_v44 names schema variant (None = the v4.3 schema with the regex pattern, as v5.0 G4). wf_v5.1 passes the frozen "v1" (no
    pattern): the R5 run of 2026-11-27 got finish_reason "error" on the guided dev50 rename with the pattern."""
    if variant not in (None, "v0", "v1"):
        raise ValueError(f"g4_jobs supports names variants v0/v1 (keys keep '#'), got {variant!r}")
    import pilot_build_v37 as PB
    d = Path(out) / dev
    (d / "prompts").mkdir(parents=True, exist_ok=True)
    old = B.read_json(old or LOOP1 / dev / "step3" / "scores" / "final_columns.json")[run]
    new = B.read_json(new or G3_FINAL / dev / "final_columns.json")[run]
    ents = B.read_json(Y3 / dev / "entities.json")
    ri = PB.RunInput(Path("results") / f"graph_v22_{dev}", 0)
    jobs, changed = [], {}
    for ent, cols in changed_columns(old, new).items():
        entity = ents[ent]
        fp = S3.parse_frozen_prompt((Y3 / dev / "a_prompts" / "prompts" / f"{ent}_a_{run}_s0.txt").read_text(encoding="utf-8"))
        blocks = [column_block(ri.export, ri.docs, entity, c, context=context) for c in cols]
        name = f"{ent}_rename_{run}"
        prompt = S3.render_names(entity, 1, 1, len(blocks), fp["others"], blocks)
        (d / "prompts" / f"{name}.txt").write_text(prompt, encoding="utf-8", newline="\n")
        ids = [b for b, _ in blocks]
        B.write_json(d / "prompts" / f"{name}.schema.json", S3_44.names_schema_v44(ids, variant) if variant else S3.names_schema(ids))
        jobs.append({"job": name, "entity": entity, "ent": ent, "set": dev, "run": run, "family": "names", "format": "judge",
                     "format43": "names_v43", "run_tag": "g4", "order": 0, "batch": 1, "cluster_ids": [b for b, _ in blocks],
                     "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": S3.NAMES_MAX_TOKENS,
                     "est_prompt_tokens": PIN.est_tokens(prompt)})
        changed[ent] = {block_id(entity, c["cid"]): {"cid": c["cid"], "name": c["name"]} for c in cols}
    B.write_json(d / "manifest_names.json", {"stage": "g4", "jobs": jobs})
    B.write_json(d / "changed.json", changed)
    return jobs


# ---------------------------------------------------------------- G4 run + apply (Colab or fake)
def g4(backend, out=G4, log=print):
    """Run the names jobs of both sets, apply the valid names. Returns {dev: [rename rows]}."""
    res = {}
    for dev, run in SETS.items():
        d = Path(out) / dev
        jobs = B.read_json(d / "manifest_names.json")["jobs"]
        info = backend.run(d, jobs) if jobs else {}
        res[dev] = apply_names(dev, run, out)
        log(f"g4 {dev}: {info} | renamed {sum(r['renamed'] for r in res[dev])}/{len(res[dev])}")
    return res


def apply_names(dev, run, out=G4, new=None):
    """Loop-1 run folder <out>/run/<dev> = wf_v47 z4 run 1 with the G3 columns (`new`: another final_columns.json), renamed by the G4 answers,
    and its rebuilt a_llama44 input."""
    d = Path(out) / dev
    changed = B.read_json(d / "changed.json")
    new = B.read_json(new or G3_FINAL / dev / "final_columns.json")[run]
    rows = []
    for job in B.read_json(d / "manifest_names.json")["jobs"]:
        raw = _raw(d / "responses" / f"{job['job']}.jsonl")
        names, _errs = S3.validate_names(raw, job["cluster_ids"]) if raw is not None else ({}, ["no response"])
        for bid, c in changed[job["ent"]].items():
            nm = names.get(bid, "")
            ok = bool(nm) and nm != S3.NOT_ATTRIBUTE
            rows.append({"set": dev, "entity": job["ent"], "cid": c["cid"], "old": c["name"], "answer": nm, "renamed": ok,
                         "new": nm.replace("_", " ") if ok else c["name"]})
    by = {(r["entity"], r["cid"]): r["new"] for r in rows}
    final = {e: [{**c, "name": by.get((e, c["cid"]), c["name"])} for c in cs] for e, cs in new.items()}
    build_run_dir(dev, run, final, out)
    pd.DataFrame(rows).to_csv(d / "renames.csv", index=False, encoding="utf-8", lineterminator="\n")
    return rows


def build_run_dir(dev, run, final, out=G4):
    """<out>/run/<dev>: the wf_v47 z4 run-1 loop-2 files plus the loop-1 columns `final` ({entity: [column dicts]}) and their a_llama44 input."""
    rd = run_dir(dev, out)
    if rd.exists():
        shutil.rmtree(rd)
    shutil.copytree(LOOP1 / dev / "loop2", rd / "loop2")
    B.write_json(rd / "step3" / "scores" / "final_columns.json", {run: final})
    with PL.use_corpus(run, B.read_json(Y3 / dev / "entities.json"), Y3 / dev / "a_prompts"):
        cols = S3.a_columns(final, I.load_mentions(run, ROOT))
    B.write_json(S3_44.a_llama44_file(run, rd / "step3"), cols)
    return rd


def _raw(path):
    if not path.exists():
        return None
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return rows[-1].get("raw") if rows else None


def run_dir(dev, out=G4):
    return Path(out) / "run" / dev


# ---------------------------------------------------------------- replay vectors (laptop) so Colab gives the laptop cosines
class CachedEnc:
    """.encode(texts) from the vectors computed on the laptop (<out>/<dev>/<fname> of every set); a text without a vector goes to `fallback`
    (an encoder with .encode, counted in .fallback_texts) or, without one, raises."""

    def __init__(self, out=G4, fname="w2_vectors.npz", fallback=None):
        self.vec, self.fallback, self.fallback_texts = {}, fallback, 0
        for dev in SETS:
            z = np.load(Path(out) / dev / fname, allow_pickle=False)
            self.vec.update(zip(z["texts"].tolist(), z["x"]))

    def encode(self, texts):
        missing = sorted({t for t in texts if t not in self.vec})
        if missing and self.fallback is None:
            raise KeyError(f"{len(missing)} texts have no laptop vector, e.g. {missing[:3]}")
        if missing:
            self.fallback_texts += len(missing)
            self.vec.update(zip(missing, np.asarray(self.fallback.encode(missing), dtype=np.float32)))
        return np.stack([self.vec[t] for t in texts])


def save_vectors(dev, run, encoder, out=G4):
    """Vectors of the W2 replay texts of one set (G3 columns before G4; names do not change the values) -> <out>/<dev>/w2_vectors.npz."""
    apply_names(dev, run, out)                          # no responses yet: every column keeps its name
    runs0 = R48.RUNS
    R48.RUNS = Path(out) / "run"
    try:
        _rd, _finals, columns_l2, clusters, loop1 = R48.inputs(dev)
    finally:
        R48.RUNS = runs0
    texts = sorted(set(R48.all_texts(columns_l2, clusters, loop1)) - {""})
    np.savez(Path(out) / dev / "w2_vectors.npz", texts=np.array(texts), x=np.asarray(encoder.encode(texts), dtype=np.float32))
    return len(texts)


# ---------------------------------------------------------------- Step 4 input (CPU) and G5
def build_inputs(encoder, out=G4, g5=G5):
    """W2 replay on the G4 run folders, then the G5 Step 4 inputs. Returns {dev: input path}."""
    cfg = json.loads(R48.CONFIG.read_text(encoding="utf-8"))
    runs0 = R48.RUNS
    R48.RUNS = Path(out) / "run"
    try:
        for dev in SETS:
            R48.run_set(dev, cfg, encoder, out=Path(out) / "w2")
    finally:
        R48.RUNS = runs0
    return {dev: G48.prepare(dev, run, g5, w2=Path(out) / "w2", loop1=Path(out) / "run") for dev, run in SETS.items()}


def g5(backend, root=G5, variant="ARMg", **kw):
    """Step 4 variant ARM (rerun name ARMg) on each set (gpu_v48.w3 into results/wf_v50/g5). Returns {(variant, dev): final/status.json rows}."""
    return G48.w3(backend, variants=(variant,), root=root, **kw)


def unguided_rows(folder):
    """Response files of a Step 4 folder whose cached row did not come from guided decoding (must be [] for a valid run)."""
    bad = []
    for f in sorted(Path(folder).glob("responses/*.jsonl")):
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
        if rows and rows[-1].get("guided") is not True:
            bad.append(f.name)
    return bad


def guided_smoke(engine, sampling, chat):
    """One tiny guided call; returns (finish_reason, text). A valid session gives "stop" and a JSON object with key "a"."""
    schema = {"type": "object", "properties": {"a": {"enum": ["x", "y"]}}, "required": ["a"], "additionalProperties": False}
    o = engine.generate([chat('Return {"a": "x"} as JSON.')], sampling(20, schema))[0].outputs[0]
    return o.finish_reason, o.text


# ---------------------------------------------------------------- laptop checks
def regression_check(encoder, tmp):
    """The input build on the unchanged v4.9 loop-1 columns must give the v4.8 W2 a2.columns.json exactly. Returns {dev: True}."""
    res = {}
    for dev, run in SETS.items():
        rd = Path(tmp) / "run" / dev
        shutil.copytree(LOOP1 / dev, rd, dirs_exist_ok=True)
    runs0 = R48.RUNS
    R48.RUNS = Path(tmp) / "run"
    try:
        cfg = json.loads(R48.CONFIG.read_text(encoding="utf-8"))
        for dev in SETS:
            R48.run_set(dev, cfg, encoder, out=Path(tmp) / "w2")
            res[dev] = B.read_json(Path(tmp) / "w2" / dev / "a2.columns.json") == B.read_json(G48.W2 / dev / "a2.columns.json")
    finally:
        R48.RUNS = runs0
    return res


def fake_check(tmp, encoder):
    """G4 (fake names) + input build + G5 (fake Step 4) into `tmp`; raises on any failure."""
    tmp = Path(tmp)
    for dev, run in SETS.items():
        shutil.copytree(G4 / dev, tmp / "g4" / dev, dirs_exist_ok=True, ignore=shutil.ignore_patterns("responses", "renames.csv"))
    ren = g4(G46.Fakes(), out=tmp / "g4", log=lambda *_: None)
    build_inputs(encoder, out=tmp / "g4", g5=tmp / "g5")
    res = g5(G46.Fakes(), root=tmp / "g5", log=lambda *_: None)
    assert all(len(rows) == len(SEEDS) and all(r["ok"] for r in rows) for rows in res.values()), res
    return {"renamed": {d: sum(r["renamed"] for r in rs) for d, rs in ren.items()},
            "g5": {k: [(r["tables"], r["repair_kinds"]) for r in rows] for k, rows in res.items()}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true", help="write the G4 names jobs (laptop, before the GPU session)")
    ap.add_argument("--fake", action="store_true", help="laptop check with fakes + the input regression check (no GPU)")
    ap.add_argument("--out", type=Path, default=Path(__import__("tempfile").gettempdir()) / "wf_v50_fake_check")
    a = ap.parse_args()
    from run import encoder as make_encoder
    if a.prepare:
        enc = make_encoder()
        for dev, run in SETS.items():
            print(dev, [(j["job"], j["cluster_ids"], j["est_prompt_tokens"]) for j in g4_jobs(dev, run)], "| vectors", save_vectors(dev, run, enc))
        enc.save()
    elif a.fake:
        enc = make_encoder()
        if a.out.exists():
            shutil.rmtree(a.out)
        print("regression (v4.9 input rebuilt exactly):", regression_check(enc, a.out / "regression"))
        print(fake_check(a.out, CachedEnc()))
    else:
        ap.error("the real run is the notebook colab/S1A_wf50_colab.ipynb; give --prepare or --fake")


if __name__ == "__main__":
    main()
