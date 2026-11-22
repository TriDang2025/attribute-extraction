"""wf_v5.1 R5 GPU job (diary Nov 24), called by the notebook colab/S1A_wf51_colab.ipynb (one session, model loaded once). Laptop: --prepare | --fake.

The v5.0 pipeline with the two adopted wf_v5.1 switches, per set (dev50, dev50b), everything guided (a guided call with finish_reason "error", or
a cached row that is not guided, raises and stops the session: no unguided fallback anywhere):
 0. guided smoke test (smoke_test), once per session, before any set.
 1. Step 3 in full, the frozen v4.4 code (step3_v44.run via pipeline_v45.step3) on the corpus, entities and frozen A prompts of the v4.6 Y3 loop 1
    (results/wf_v46/y3/<set>/{entities.json, a_prompts}; the LLM entity names are not asked again), with naming_context (R4: 3 context snippets per
    cluster in the naming prompt) and name_clash (R3: closed question for same-named clusters) on -> results/wf_v51/r5/<set>/step3/.
 2. Context split big40 (ctxsplit_v50, left-context bge-m3 vectors) on the new final columns -> <set>/ctxsplit/final_columns.json; the columns it
    changed get a G4-style rename (one names call per entity, gpu_v50.g4_jobs, with R4 snippets in the prompt); then the R3 clash question on
    columns that now share a name (v5.0: G4 named both train time parts "departure time") -> rename/<set>/ and the loop-1 run folder
    rename/run/<set>/.
 3. Loop 2 frozen: the wf_v4.8 W2 CPU replay on the cached v4.7 z4 run-1 loop-2 files (gpu_v50.build_inputs). It is replayed, NOT re-asked.
    Writes rename/w2/<set>/ and the Step 4 input <set>/input/a_llama44/<run>/a.columns.json.
 4. Step 4 v5.0 frozen = variant ARMg (A + p2_reask + p2_reask2 + merge_same_entity), seeds 0-2 -> <set>/step4_ARMg/.
 5. settings.json (cost_report: calls, tokens, time, finish reasons, guided share per stage and set) by the notebook.
All folders are new (the response cache key ignores guided: never reuse a v5.0 folder).
Laptop --prepare writes <set>/vectors.npz (bge-m3 vectors of the replay texts and of the left-context texts; Colab uses CachedEnc so the cosines
are the laptop ones, a text without a vector goes to the GPU bge-m3 and is counted). --fake: full flow with fakes into a temp dir + regression.
"""
import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import gpu_v46 as G46  # noqa: E402
import gpu_v48 as G48  # noqa: E402
import gpu_v50 as G50  # noqa: E402
import replay_v48 as R48  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import ctxsplit_v50 as CS  # noqa: E402
from s1a import log_v44 as L44  # noqa: E402
from s1a import loop2_fix_v48 as F  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import rolenames_v51 as RN  # noqa: E402
from s1a import step3_v44 as S3  # noqa: E402

R5 = ROOT / "results" / "wf_v51" / "r5"
SETS, SEEDS, Y3, LOOP1 = G48.SETS, G48.SEEDS, G48.Y3, G48.LOOP1
SWITCHES = {"naming_context": True, "name_clash": True}      # adopted in R5 (config/wf_v51_roles.json holds their settings)
CTX = (2, 99, 40)                                            # big40 of v5.0 = g3_ctxsplit_v50.VARIANTS["big40"]: (min_parts, max_parts, min_size)
VARIANT = "ARMg"                                             # Step 4 v5.0 frozen (gpu_v50.VARIANTS)
LIMITS = {"step3": 900, "rename": 60, "step4": 140}          # calls per set and stage; over it = stop and tell Claude (diary: Step 3 ~600)
STAGES = (("step3", lambda root, dev: Path(root) / dev / "step3"), ("rename", lambda root, dev: Path(root) / "rename" / dev),
          ("step4", lambda root, dev: Path(root) / dev / f"step4_{VARIANT}"))


class GuidedError(RuntimeError):
    """Guided decoding was lost (finish_reason "error", an unguided row, a failed smoke test): stop the session."""


class CallLimit(RuntimeError):
    """A stage needs more calls than its MAX_CALLS: stop and tell Claude."""


# ---------------------------------------------------------------- guards
def check_rows(folder, jobs):
    """Raises GuidedError when the cached row of a job has finish_reason "error" (also the one of the guided call of a retried row) or is not guided."""
    for j in jobs:
        row = B.last_row(Path(folder) / "responses" / f"{j['job']}.jsonl")
        if row is None:
            continue
        if "error" in (row.get("finish_reason"), row.get("guided_finish_reason")):
            raise GuidedError(f"{j['job']}: finish_reason error (guided decoding lost); stop, copy the output and tell Claude")
        if row.get("guided") is not True:
            raise GuidedError(f"{j['job']}: row is not guided (unguided fallback); stop, copy the output and tell Claude")


def assert_guided(folder):
    """After a stage: every cached row of the folder is guided (gpu_v50.unguided_rows == [])."""
    bad = G50.unguided_rows(folder)
    if bad:
        raise GuidedError(f"{folder}: {len(bad)} unguided rows, e.g. {bad[:3]}; stop and tell Claude")


class Guarded:
    """Decorator around a backend (.run(folder, jobs), other attributes passed on): counts the jobs of one stage against `max_calls`
    (CallLimit before a run that would pass it) and checks the rows after every run (check_rows)."""

    def __init__(self, backend, max_calls, label=""):
        self.backend, self.max_calls, self.label, self.calls = backend, max_calls, label, 0

    def run(self, folder, jobs):
        if self.calls + len(jobs) > self.max_calls:
            raise CallLimit(f"{self.label}: {self.calls} calls done, {len(jobs)} more would pass MAX_CALLS {self.max_calls}; stop and tell Claude")
        self.calls += len(jobs)
        info = self.backend.run(folder, jobs)
        check_rows(folder, jobs)
        return info

    def __getattr__(self, name):
        return getattr(self.backend, name)


def smoke_test(engine, sampling, chat):
    """gpu_v50.guided_smoke; raises GuidedError unless the call ends with "stop" and a JSON object with key "a". Returns (finish, text)."""
    fin, txt = G50.guided_smoke(engine, sampling, chat)
    try:
        ok = fin == "stop" and json.loads(txt).get("a") in ("x", "y")
    except (ValueError, AttributeError):
        ok = False
    if not ok:
        raise GuidedError(f"guided smoke test failed: finish {fin!r}, text {txt!r}; stop and tell Claude (do not run anything else)")
    return fin, txt


def need():
    """Files the R5 run reads from git; [] = all there."""
    files = [ROOT / "config" / "wf_v51_roles.json", ROOT / "config" / "wf_v48_loop2.json", ROOT / "results" / "wf_v44" / "t1" / "choice.json"]
    for dev, run in SETS.items():
        files += [Y3 / dev / "entities.json", Y3 / dev / "a_prompts" / "manifest.json", LOOP1 / dev / "loop2", R5 / dev / "vectors.npz"]
        files += [ROOT / "results" / f"graph_v22_{x}" / f for x in (dev, run) for f in ("docs.jsonl", "spans/mentions.csv", "spans/vectors.npz")]
    return [str(p) for p in files if not p.exists()]


# ---------------------------------------------------------------- 1. Step 3
def step3_stage(backend, enc3, root=R5, sets=SETS, max_calls=LIMITS["step3"], switches=None, log=print):
    """Step 3 (frozen v4.4 + the R3 / R4 switches) on each set -> <root>/<set>/step3. enc3 = name encoder of the merge booster. Returns {dev: info}."""
    switches = SWITCHES if switches is None else switches
    res = {}
    for dev, run in sets.items():
        out = Path(root) / dev / "step3"
        cfg = S3.load_config(switches=switches)
        bk = Guarded(backend, max_calls, f"step3 {dev}")
        with PL.use_corpus(run, B.read_json(Y3 / dev / "entities.json"), Y3 / dev / "a_prompts"):
            snips = {run: RN.set_snippets(run)} if switches.get("naming_context") else None
            res[dev], sizes = PL.step3(run, out, bk, enc3, cfg=cfg, snips=snips)
        assert_guided(out)
        for f in ("entities.json", "entity_names.json"):          # the loop-1 entity files of v5.0, copied beside the new Step 3 for the scorers
            shutil.copy2(Y3 / dev / f, Path(root) / dev / f)
        log(f"step3 {dev}: {bk.calls} calls | columns {sizes} | clash {res[dev].get('clash_q')}")
    return res


# ---------------------------------------------------------------- 2. context split, rename, clash on the columns
def ctx_split(dev, run, enc, root=R5):
    """Context split big40 on the Step 3 final columns of one set -> <root>/<dev>/ctxsplit/final_columns.json (returns the path)."""
    step3 = Path(root) / dev / "step3"
    final = B.read_json(step3 / "scores" / "final_columns.json")[run]
    parts = B.read_json(step3 / "columns.json")[run]
    vec, _ = CS.context_vectors(dev, CS.mention_table(dev), enc)
    after = {k: CS.apply(final[k], parts[k]["parts"], CS.reassign(parts[k]["parts"], vec, *CTX)) for k in final}
    p = Path(root) / dev / "ctxsplit" / "final_columns.json"
    B.write_json(p, {run: after})
    return p


def snippet_context(dev, cfg=None):
    """context(block id, column) -> R4 snippet lines of a column's mentions, for gpu_v50.column_block."""
    src = RN.text_source(dev)
    return lambda bid, col: RN.column_snippets(dev, {bid: col["mention_ids"]}, cfg, source=src)[bid]


def clash_state(dev, run, final, make_block):
    """(blocks.json doc, state, {block id: mention ids}) of the columns of one set that share a name inside their entity (the others cannot clash).
    state = {(run, entity, 0): {"frozen_ids", "names"}} in the form of rolenames_v51 (names snake_case); make_block(entity id, column) -> (id, block)."""
    ents = B.read_json(Y3 / dev / "entities.json")
    doc, state, ids = {}, {}, {}
    for ent, cols in final.items():
        n = Counter(c["name"] for c in cols)
        dup = [c for c in cols if n[c["name"]] > 1]
        if not dup:
            continue
        blocks = dict(make_block(ents[ent], c) for c in dup)
        doc[f"{run}/{ent}"] = {"entity": ents[ent], "blocks": blocks}
        state[(run, ent, 0)] = {"frozen_ids": list(blocks), "names": {G50.block_id(ents[ent], c["cid"]): c["name"].replace(" ", "_") for c in dup}}
        ids.update({G50.block_id(ents[ent], c["cid"]): c["mention_ids"] for c in dup})
    return doc, state, ids


def column_clash(dev, run, final, d, backend, variant, log=print):
    """R3 on final columns: one closed question per pair of same-named columns (rolenames_v51.run_clash, files in folder `d`). Returns (final with
    the new names, [rename rows], backend info). "same" or an unusable answer leaves the names as they are."""
    import pilot_build_v37 as PB
    d = Path(d)
    ri = PB.RunInput(Path("results") / f"graph_v22_{dev}", 0)
    doc, state, ids = clash_state(dev, run, final, lambda entity, c: G50.column_block(ri.export, ri.docs, entity, c))
    B.write_json(d / "blocks.json", doc)
    with PL.use_corpus(run, B.read_json(Y3 / dev / "entities.json"), Y3 / dev / "a_prompts"):
        info, new = RN.run_clash(d, backend, S3.load_config(), state, variant, None, {run: RN.column_snippets(dev, ids)})
    ents, rows, out = B.read_json(Y3 / dev / "entities.json"), [], {}
    for ent, cols in final.items():
        names = new.get((run, ent, 0), {}).get("names", {})
        out[ent] = []
        for c in cols:
            nm = names.get(G50.block_id(ents[ent], c["cid"]), "").replace("_", " ")
            if nm and nm != c["name"]:
                rows.append({"set": dev, "entity": ent, "cid": c["cid"], "old": c["name"], "new": nm})
            out[ent].append({**c, "name": nm or c["name"]})
    pd.DataFrame(rows, columns=["set", "entity", "cid", "old", "new"]).to_csv(d / "clash_renames.csv", index=False, encoding="utf-8", lineterminator="\n")
    log(f"column clash {dev}: {info} | renamed {len(rows)} columns")
    return out, rows, info


def rename_stage(backend, enc, root=R5, sets=SETS, max_calls=LIMITS["rename"], log=print):
    """Context split + G4-style rename of the changed columns (R4 snippets) + column clash check, per set -> <root>/rename/<set>/, run folder
    <root>/rename/run/<set>/. Returns {dev: {"renamed": rows, "clash": rows}}."""
    res, out = {}, Path(root) / "rename"
    for dev, run in sets.items():
        new = ctx_split(dev, run, enc, root)
        old = Path(root) / dev / "step3" / "scores" / "final_columns.json"
        bk = Guarded(backend, max_calls, f"rename {dev}")
        G50.g4_jobs(dev, run, out, old, new, context=snippet_context(dev))
        jobs = B.read_json(out / dev / "manifest_names.json")["jobs"]
        if jobs:
            bk.run(out / dev, jobs)
        renamed = G50.apply_names(dev, run, out, new)
        final = B.read_json(G50.run_dir(dev, out) / "step3" / "scores" / "final_columns.json")[run]
        variant = B.read_json(Path(root) / dev / "step3" / "config_used.json")["names_variant_used"]
        final, clash, _info = column_clash(dev, run, final, out / dev, bk, variant, log)
        G50.build_run_dir(dev, run, final, out)
        assert_guided(out / dev)
        res[dev] = {"renamed": renamed, "clash": clash}
        log(f"rename {dev}: {bk.calls} calls | renamed {sum(r['renamed'] for r in renamed)}/{len(renamed)} | clash renames {len(clash)}")
    return res


# ---------------------------------------------------------------- 3. loop 2 (CPU replay) and 4. Step 4
def loop2_stage(enc, root=R5):
    """The wf_v4.8 W2 replay of the cached v4.7 z4 run-1 loop-2 files on the new loop-1 columns, then the Step 4 input of each set. Replayed, not
    asked. Returns {dev: input path}."""
    return G50.build_inputs(enc, out=Path(root) / "rename", g5=root)


def step4_stage(backend, root=R5, sets=SETS, max_calls=LIMITS["step4"], log=print):
    """Step 4 v5.0 frozen (variant ARMg), seeds 0-2, on each set -> <root>/<set>/step4_ARMg. Returns {(variant, dev): final/status.json rows}."""
    res = {}
    for dev, run in sets.items():
        bk = Guarded(backend, max_calls, f"step4 {dev}")
        res.update(G50.g5(bk, root=root, variant=VARIANT, sets={dev: run}, log=log))
        assert_guided(Path(root) / dev / f"step4_{VARIANT}")
        log(f"step4 {dev}: {bk.calls} jobs")
    return res


def cost_report(root=R5, sets=SETS, csv=True):
    """{stage: {dev: {calls, prompt_tokens, output_tokens, finish, retried, guided, model_seconds}}} over the cached rows of the three LLM
    stages. Rows assembled by code (no tokens: the A answers of Step 3, the split answers) are not calls and are left out. csv: also
    <root>/calls.csv (one row per call: stage, set, job, tokens, seconds, finish reason, guided, retried)."""
    res, rows_all = {}, []
    for stage, folder in STAGES:
        for dev in sets:
            f = folder(root, dev)
            rows = [r for r in L44.call_rows(f) if r["prompt_tokens"] is not None] if f.exists() else []
            secs = [float(r["job_seconds"]) for r in rows if r["job_seconds"] not in (None, "")]
            res.setdefault(stage, {})[dev] = {**L44.call_totals(rows), "guided": sum(r["guided"] is True for r in rows),
                                              "model_seconds": round(sum(secs), 1)}
            rows_all += [{"stage": stage, "set": dev, **r} for r in rows]
    if csv:
        pd.DataFrame(rows_all).to_csv(Path(root) / "calls.csv", index=False, encoding="utf-8", lineterminator="\n")
    return res


# ---------------------------------------------------------------- laptop: vectors (--prepare)
class Recorder:
    """Encoder wrapper that keeps every vector it returns ({text: vector})."""

    def __init__(self, enc):
        self.enc, self.vec = enc, {}

    def encode(self, texts):
        x = np.asarray(self.enc.encode(texts), dtype=np.float32)
        self.vec.update(zip(texts, x))
        return x


def replay_texts(dev, run, tmp):
    """The texts the W2 replay encodes: the values of the loop-2 columns and of the loop-1 columns. The loop-1 values of the new Step 3 are a
    subset of the values of all mentions (a cluster v5.0 left out may be a column now), so every mention value is included."""
    G50.build_run_dir(dev, run, B.read_json(G50.G3_FINAL / dev / "final_columns.json")[run], tmp)
    runs0, R48.RUNS = R48.RUNS, Path(tmp) / "run"
    try:
        _rd, _finals, columns_l2, clusters, loop1 = R48.inputs(dev)
    finally:
        R48.RUNS = runs0
    texts = set(R48.all_texts(columns_l2, clusters, loop1)) | {F.norm(v) for v in CS.mention_table(dev)["norm_value"] if v}
    return sorted(texts - {""})


def prepare(enc, root=R5, sets=SETS):
    """<root>/<dev>/vectors.npz: laptop bge-m3 vectors of the replay texts and of the left-context texts of the context split. Returns counts."""
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for dev, run in sets.items():
            rec = Recorder(enc)
            _, ctx = CS.context_vectors(dev, CS.mention_table(dev), rec)
            texts = replay_texts(dev, run, tmp)
            rec.encode(texts)
            keys = sorted(rec.vec)
            d = Path(root) / dev
            d.mkdir(parents=True, exist_ok=True)
            np.savez(d / "vectors.npz", texts=np.array(keys), x=np.stack([rec.vec[k] for k in keys]))
            res[dev] = {"replay_texts": len(texts), "context_texts": len(set(ctx.values())), "vectors": len(keys), "file": str(d / "vectors.npz")}
    return res


# ---------------------------------------------------------------- laptop: fakes and checks
class Fakes51(G46.Fakes):
    """gpu_v46.Fakes whose Step 3 / rename folders also answer the R3 clash questions."""

    def __init__(self):
        super().__init__()
        self.s3 = RN.FakeStep51()


def _lf(path):
    return Path(path).read_bytes().replace(b"\r\n", b"\n")


def regression_check(tmp, sets=SETS):
    """With the R3 / R4 switches off (explicitly, or absent as in the v5.0 config) step3_v44.build writes the Step 3 prompts and schemas of v5.0
    (results/wf_v46/y3/<set>/step3/prompts, CRLF files compared as LF). Returns {dev: {built, in_v50, equal}}; raises when one differs."""
    res = {}
    for dev, run in sets.items():
        for tag, cfg in (("absent", S3.load_config()), ("off", S3.load_config(switches={k: False for k in SWITCHES}))):
            d = Path(tmp) / "regression" / tag / dev
            with PL.use_corpus(run, B.read_json(Y3 / dev / "entities.json"), Y3 / dev / "a_prompts"):
                S3.build(d, cfg, None, {run: S3.cluster_vectors(run)})
            old = Y3 / dev / "step3" / "prompts"
            built = sorted(p.name for p in (d / "prompts").iterdir())
            both = [f for f in built if (old / f).exists()]
            diff = [f for f in both if _lf(old / f) != _lf(d / "prompts" / f)]
            if diff or not both:
                raise AssertionError(f"{dev} ({tag}): prompts differ from v5.0: {diff[:5]} ({len(both)} compared)")
            res[dev] = {"built": len(built), "in_v50": len(both), "equal": len(both) - len(diff)}
    return res


def fake_check(tmp, enc=None, log=lambda *_: None):
    """The whole R5 flow with the laptop fakes (fake LLMs, fake name encoder, laptop vectors from --prepare) into `tmp`; raises on any failure.
    Returns cost_report(tmp) (calls per stage and set)."""
    tmp = Path(tmp)
    enc = enc or G50.CachedEnc(R5, "vectors.npz")
    fb = Fakes51()
    step3_stage(fb, S3.FakeEncoder(), tmp, log=log)
    rename_stage(fb, enc, tmp, log=log)
    loop2_stage(enc, tmp)
    res = step4_stage(fb, tmp, log=log)
    assert all(len(rows) == len(SEEDS) and all(r["ok"] for r in rows) for rows in res.values()), res
    return cost_report(tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true", help="write <set>/vectors.npz (laptop bge-m3, before the GPU session)")
    ap.add_argument("--fake", action="store_true", help="laptop check: regression (switches off = v5.0 prompts) + the whole flow with fakes (no GPU)")
    ap.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "wf_v51_fake_check")
    a = ap.parse_args()
    if a.prepare:
        from run import encoder as make_encoder
        enc = make_encoder()
        print(json.dumps(prepare(enc), indent=1))
        enc.save()
    elif a.fake:
        if a.out.exists():
            shutil.rmtree(a.out)
        print("regression (switches off = v5.0 Step 3 prompts):", regression_check(a.out))
        print("missing inputs:", need() or "none")
        print(json.dumps(fake_check(a.out, log=print), indent=1))
    else:
        ap.error("the real run is the notebook colab/S1A_wf51_colab.ipynb; give --prepare or --fake")


if __name__ == "__main__":
    main()
