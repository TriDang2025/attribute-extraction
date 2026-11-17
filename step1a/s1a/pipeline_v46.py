"""wf_v4.6 Y3: the v4.5 pipeline with LLM entity names (entity_names_v46) instead of the MultiWOZ keyword names, and the entities with the same
name merged at the Step 4 input. Everything else is pipeline_v45 (imported, not copied): Steps 1a-2, prompts, Step 3 v4.4, Step 4 v4.3.

Order: Steps 1a-2 (corpus_v45.step1a; its keyword names are overwritten at once, never used) -> one name call per entity ->
Step 3 on the entities (unique keys name, name_2, ...) -> merge of equal names into one table of a_llama44/<set>/a.columns.json -> Step 4 ->
outputs. Extra outputs: <out>/entity_names.json (names, keys, merge map {name: [entity ids]}, fallbacks), <out>/names/ (the name calls),
cost.json["entity_names"] (calls and tokens; also counted in "total_llm"). attributes.json lists a merged table once, under its name.
loops=2 (Y4): loop 2 (loop2_v46.run_loop2: Step 1b, evidence check, Step 3 naming of new clusters) runs right after Step 3, on the
unmerged a.columns.json, and writes <out>/loop2/; Step 4 stays on the loop-1 columns (frozen v4.3; Step 4 on the final list comes later);
the loop-2 cost goes to cost.json["loop2"] (not into total_llm, which stays the loop-1 cost).
"""
import time
from pathlib import Path

from . import batch_v4 as B
from . import corpus_v45 as CO
from . import entity_names_v46 as EN
from . import log_v44 as LOG
from . import loop2_v46 as L2
from . import pipeline_v45 as PL
from . import step4_v44 as S4


def merge_attributes(out, rec):
    """attributes.json with the columns of merged entities under their common name (one list per name)."""
    out = Path(out)
    attrs = B.read_json(out / "attributes.json")
    by_key = {k: e for e, k in rec["keys"].items()}
    merged = {}
    for key, cols in attrs.items():
        merged.setdefault(rec["names"][by_key[key]], []).extend(cols)
    B.write_json(out / "attributes.json", merged)
    return merged


def add_names_cost(out, c):
    """Add the entity name calls (<out>/names) to the cost dict: c["entity_names"], and into c["total_llm"]."""
    rows = list(LOG.call_rows(Path(out) / "names"))
    t = LOG.call_totals(rows)
    secs = [r["job_seconds"] for r in rows if r.get("job_seconds") not in (None, "")]
    c["entity_names"] = {**t, "model_seconds": round(sum(float(s) for s in secs), 1) if secs else None}
    for k in ("calls", "prompt_tokens", "output_tokens"):
        c["total_llm"][k] += t[k]
    return c


def run_pipeline(corpus, out, set_name, backend, encoder, enc_1a, step4_cfg, load_seconds=None, log=print, skip_1a=False, backend4=None,
                 loops=1, names_backend=None, gliner_loader=None, loop2_cfg=None, step4_seeds=None):
    """pipeline_v45.run_pipeline with LLM entity names (names_backend: the backend of the name calls when it differs, e.g. the laptop fakes).
    step4_seeds: e.g. (0,) to run one Step 4 seed (diary Y3: saves GPU); None = the frozen seeds 0-2.
    loops=2 needs gliner_loader (loop2_v46.run_loop2) and uses enc_1a (bge-m3 .encode) for the evidence check. Returns the cost dict."""
    if loops not in (1, 2):
        raise ValueError(f"loops {loops}: 1 or 2")
    if loops == 2 and gliner_loader is None:
        raise ValueError("loops 2 needs gliner_loader")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    info1 = None if skip_1a else CO.step1a(corpus, set_name, enc_1a, log=log)
    rec = EN.names_for_run(set_name, out, names_backend or backend, log=log)
    if info1:
        info1["entities"] = rec["keys"]
    entmap = CO.entity_map(set_name)
    B.write_json(out / "entities.json", entmap)
    a_dir = out / "a_prompts"
    with PL.use_corpus(set_name, entmap, a_dir):
        PL.build_prompts(set_name, entmap, a_dir)
        log(f"step 3: {len(entmap)} entities {entmap}")
        PL.step3(set_name, out / "step3", backend, encoder)
        l2 = L2.run_loop2(out, set_name, backend, enc_1a, gliner_loader, loop2_cfg, log=log) if loops == 2 else None
        EN.merge_a_columns(out / "step3", set_name, EN.key_groups(rec, set(entmap)), log=log)
        log("step 4")
        aborted = None
        try:
            if step4_seeds is None:
                PL.step4(set_name, out / "step4", backend4 or backend, out / "step3", step4_cfg)
            else:
                S4.run(out / "step4", backend4 or backend, inputs=("a_llama44",), sets=(set_name,), seeds=tuple(step4_seeds), cfg=step4_cfg,
                       step3_dirs={"a_llama44": out / "step3" / "a_llama44"})
        except ValueError as e:      # the backend refuses a prompt over its token limit: Step 4 cannot run on this corpus
            aborted = str(e)
            log(f"step 4 aborted: {aborted}")
    c = add_names_cost(out, PL.outputs(out, set_name, info1, load_seconds))
    merge_attributes(out, rec)
    if aborted:
        c["step4_aborted"] = aborted
    if l2 is not None:
        c["loop2"] = l2.get("cost")
    c["wall_seconds"] = round(time.time() - t0, 1)
    B.write_json(out / "cost.json", c)
    return c
