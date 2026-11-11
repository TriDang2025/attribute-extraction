"""wf_v4.1 diary Nov 7 task 7: helpers of the Nov 16 run (scripts/nov16_v41.py, notebook colab/S1A_nov16_v41_colab.ipynb).

- parse_answer: the one answer parser of the run, the dry runs and the fake model (plain JSON for the wf_v4.1 formats, llm_cache.parse_job
  for the frozen ones).
- step4_chains / a2_columns: the Step 4 v4.1 chains of the run (user choice 2026-11-08: the v0 set a dev50 / dev50b, b dev50, c1 dev50
  plus a2 dev50 / dev50b, seeds 0-2 = 18 chains). a2 = input a + the new loop-2 columns (status "new" in columns_l2.json), each added at
  the end of its entity block, examples and value type as input a (step4_inputs.examples_of / dominant_type).
- FakeLLM: the no-GPU stand-in. It replays a saved answer when the same job name has the same prompt in a replay folder (the dry runs:
  Step 1b and the seed-0 Step 4 chains are byte-identical), else writes a minimal valid answer (Step 3 A: one attribute per cluster;
  duplicate check: no joins; Step 4 and placement: batch_v4_fake). Its rows are marked "fake".
- State: <run>/state.json lists the finished stages; a rerun skips them, and an LLM stage skips the jobs that already have a response.
- model_setting (task 9): the model settings of config/wf_v41_models.json (Qwen2.5-32B-AWQ, Llama-3.1-8B); prompts are the same for all.
"""
import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from . import batch_v4 as B
from . import batch_v4_fake as F
from . import llm_cache as LC
from . import step4_inputs as I

STAGES = ("step1b", "loop2", "step3_l2", "dupcheck", "step4", "contamination", "task13")
PLAIN_FORMATS = ("s1b", "contam", "judge")
SETS = ("dev50", "dev50b")
STEP4_RUNS = (("a", "dev50"), ("a", "dev50b"), ("b", "dev50"), ("c1", "dev50"), ("a2", "dev50"), ("a2", "dev50b"))
SEEDS = (0, 1, 2)
MODELS_CONFIG = Path(__file__).resolve().parents[1] / "config" / "wf_v41_models.json"
SETTING_KEYS = ("model", "revision", "quantization", "min_gpu_gb", "copy_v4_base")


def model_setting(name, path=MODELS_CONFIG):
    """The model setting `name` of config/wf_v41_models.json: {model, revision, quantization, min_gpu_gb, copy_v4_base}."""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    names = [k for k in cfg if not k.startswith("_")]
    if name not in names:
        raise ValueError(f"unknown model setting {name!r}; choose one of {names}")
    missing = [k for k in SETTING_KEYS if k not in cfg[name]]
    if missing:
        raise ValueError(f"model setting {name!r} misses {missing}")
    return cfg[name]


def chat_text(tok, text):
    """The prompt as the model sees it: one user message in the model's chat template."""
    return tok.apply_chat_template([{"role": "user", "content": text}], tokenize=False, add_generation_prompt=True)


def prompt_tokens(tok, job_name, text, limit):
    """Token count of the chat-wrapped prompt; ValueError over `limit`."""
    n = len(tok(chat_text(tok, text), add_special_tokens=False).input_ids)
    if n > limit:
        raise ValueError(f"{job_name}: prompt has {n} tokens, over the limit {limit}")
    return n


def parse_answer(raw, job, schema):
    """(parsed, errors) of a raw answer: plain JSON for PLAIN_FORMATS (errors = JSON errors), llm_cache.parse_job for the others.
    A job marked "keyed" (wf_v4.2 option B, s1a/keyed_v42.py) is first turned back into the frozen list format."""
    if job.get("keyed"):
        from . import keyed_v42 as K
        raw, schema = K.unkey(job["format"], raw), K.parse_schema(job["format"], schema)
    if job["format"] in PLAIN_FORMATS:
        try:
            return json.loads(raw), []
        except json.JSONDecodeError:
            return LC._obj_errors(raw, [], lambda o, e: None)
    return LC.parse_job(raw, job["format"], schema)[:2]


# ---------------------------------------------------------------- Step 4 chains and input a2
def step4_chains(a2_files, runs=STEP4_RUNS, seeds=SEEDS):
    """Chain dicts (batch_v4 format, prompt_version v41). a2_files = {set: input file relative to the step1a root}."""
    out = []
    for inp, s in runs:
        for d in seeds:
            ch = {"id": B.chain_id(inp, s, d), "kind": "main", "input": inp, "set": s, "seed": d, "exclude": [], "prompt_version": "v41"}
            if inp == "a2":
                ch["columns_file"] = a2_files[s]
            out.append(ch)
    return out


def run_chains(out, llm, chains, root):
    """Step 4 chains 4.1 -> 4.4 under `out`, one stage at a time (each stage built from the answers before it); llm.run(out, jobs)
    answers a stage. Returns {"chains", "stage1".."stage4", "finished": "ok/n"} (main chains)."""
    info = {"chains": len(chains), "stage1": llm.run(out, B.build_chains_stage1(out, chains, root).save())}
    for k in (2, 3, 4):
        info[f"stage{k}"] = llm.run(out, B.build_stage(out, k, root))
    status = [r for r in B.assemble_all(out, root) if r["kind"] == "main"]
    info["finished"] = f"{sum(r['ok'] for r in status)}/{len(status)}"
    return info


def a2_columns(a_cols, final, clusters, k=I.N_EXAMPLES, width=I.WIDTH):
    """Input a2: input a plus one column per new loop-2 column. final = {entity: [columns_l2.json rows]}; clusters = {L2 id: cluster}.
    Returns (columns, added [(id, name, clusters)])."""
    blocks = {}
    for c in a_cols:
        blocks.setdefault(c["id"].split(":")[0], []).append(c)
    added = []
    for ent, rows in final.items():
        block = blocks.setdefault(ent, [])
        n = max((int(c["id"].split(":")[1]) for c in block), default=0)
        for r in [r for r in rows if r["status"] == "new"]:
            ms = sorted((m for cid in r["clusters"] for m in clusters[cid]["mentions"]), key=lambda m: m["mention_id"])
            df = pd.DataFrame(ms, columns=["mention_id", "dialogue_id", "text", "norm_value", "context"])
            n += 1
            block.append({"id": f"{ent}:{n}", "name": r["name"], "description": r["description"], "role": "",
                          "value_type": I.dominant_type(df["text"]), "examples": I.examples_of(df, k, width), "n_mentions": len(df),
                          "n_dialogues": int(df["dialogue_id"].nunique()), "signal": "", "flag": ""})
            added.append((f"{ent}:{n}", r["name"], r["clusters"]))
    return [c for b in blocks.values() for c in b], added


# ---------------------------------------------------------------- state
def load_state(run_dir):
    p = Path(run_dir) / "state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"done": []}


def mark_done(run_dir, stage, info=None):
    st = load_state(run_dir)
    if stage not in st["done"]:
        st["done"].append(stage)
    st.setdefault("info", {})[stage] = info or {}
    B.write_json(Path(run_dir) / "state.json", st)
    return st


def todo_jobs(out, jobs):
    """The jobs of `jobs` without a response row under <out>/responses (a rerun after a crash skips the answered ones)."""
    return [j for j in jobs if B.last_row(Path(out) / "responses" / f"{j['job']}.jsonl") is None]


# ---------------------------------------------------------------- fake model
def fake_a(schema):
    """Minimal valid Step 3 A answer (format v2): every cluster its own attribute, the first placement option."""
    clu = schema["properties"]["clusters"]["items"]["properties"]
    ids, place = clu["cluster_id"]["enum"], clu["placement"]["enum"][0]
    names = [f"fake attribute {i}" for i in range(1, len(ids) + 1)]
    return json.dumps({"attributes": [{"name": n, "description": f"fake description of {n}", "role": "fake"} for n in names],
                       "clusters": [{"cluster_id": c, "attribute": n, "evidence": "fake", "mixed": False, "placement": place}
                                    for c, n in zip(ids, names)]})


class FakeLLM:
    """run(out, jobs): answers the jobs without a response (replay first, then a minimal valid answer)."""
    model_id = "fake"

    def __init__(self, replay_dirs=(), tok=None, limit=30000):
        """tok: the tokenizer of a model setting; each job's prompt is then counted and checked against `limit` as on the GPU."""
        self.replay_dirs = [Path(d) for d in replay_dirs]
        self.n_replayed = self.n_made = 0
        self.tok, self.limit, self.max_prompt_tokens = tok, limit, 0

    def replayed(self, job, prompt):
        for d in self.replay_dirs:
            p, r = d / job["prompt"], d / "responses" / f"{job['job']}.jsonl"
            if p.exists() and r.exists() and p.read_text(encoding="utf-8") == prompt:
                row = B.last_row(r)
                if row and row.get("raw"):
                    return row["raw"]
        return None

    def respond(self, job, prompt, schema):
        raw = self.replayed(job, prompt)
        if raw is not None:
            self.n_replayed += 1
            return raw
        self.n_made += 1
        if job["family"] == "a":
            return fake_a(schema)
        if job["family"] == "dupcheck_l2":
            return json.dumps({"joins": []})
        if job["family"] == "s1b":
            raise ValueError(f"{job['job']}: no saved Step 1b answer with the same prompt to replay")
        return F.respond(job, prompt, schema)

    def run(self, out, jobs):
        todo = todo_jobs(out, jobs)
        if self.tok is not None:
            for j in todo:
                n = prompt_tokens(self.tok, j["job"], (Path(out) / j["prompt"]).read_text(encoding="utf-8"), self.limit)
                self.max_prompt_tokens = max(self.max_prompt_tokens, n)

        def model(job, prompt, schema):
            return self.respond(job, prompt, schema)
        model.last = {"model": "fake", "guided": True, "finish_reason": "stop"}   # F.run_jobs copies it into each row
        bad = F.run_jobs(out, todo, model=model, parse=parse_answer) if todo else 0
        return {"jobs": len(jobs), "run": len(todo), "parse_errors": bad}


# ---------------------------------------------------------------- vLLM backend (used by the Colab notebook)
class VllmBackend:
    """run(out, jobs) on a loaded vLLM engine, as the v4 notebook's run_stage: temperature 0, guided JSON from each job's schema file,
    batches of `batch`; if guided decoding fails for a batch each job reruns alone, and a job whose own schema fails runs unguided; a
    guided answer with parse errors is retried once unguided (the better row is kept, both calls' tokens counted). One cached row per
    job, keyed by model@revision, params, prompt and run_tag (llm_cache.key), so a rerun after a crash skips the answered jobs.
    `sampling(max_tokens, schema or None)` makes the vLLM SamplingParams (the notebook passes it, so this module needs no vLLM)."""

    def __init__(self, engine, model, revision, sampling, max_len=32768, batch=64, limit=30000, vllm_version="", log=print):
        self.engine, self.tok, self.sampling = engine, engine.get_tokenizer(), sampling
        self.model, self.revision, self.model_id = model, revision, f"{model}@{revision}"
        self.max_len, self.batch, self.limit, self.vllm_version, self.log = max_len, batch, limit, vllm_version, log

    def chat(self, text):
        return chat_text(self.tok, text)

    def _generate(self, texts, items):
        try:
            return self.engine.generate(texts, [self.sampling(it["max_tokens"], it["schema"]) for it in items]), [True] * len(items)
        except Exception as e:  # noqa: BLE001 - vLLM raises many kinds on a bad schema
            self.log(f"  guided decoding failed for the batch, rerunning its jobs one by one: {type(e).__name__} {str(e)[:200]}")
        outs, guided = [], []
        for t, it in zip(texts, items):
            try:
                outs.append(self.engine.generate([t], self.sampling(it["max_tokens"], it["schema"]))[0])
                guided.append(True)
            except Exception as e:  # noqa: BLE001
                self.log(f"  {it['job']['job']}: guided failed ({type(e).__name__}), unguided")
                outs.append(self.engine.generate([t], self.sampling(it["max_tokens"], None))[0])
                guided.append(False)
        return outs, guided

    def _row(self, it, out, guided, tf):
        o = out.outputs[0]
        parsed, errors = parse_answer(o.text, it["job"], it["schema"])
        return {"prompt_sha": hashlib.sha256(it["prompt"].encode("utf-8")).hexdigest(), "model": self.model, "revision": self.revision,
                "vllm": self.vllm_version, "params": it["params"], "run_tag": it["job"]["run_tag"], "job": it["job"]["job"],
                "format": it["job"]["format"], "guided": guided, "finish_reason": o.finish_reason, "raw": o.text, "parsed": parsed,
                "errors": errors, **tf}

    def run(self, out, jobs):
        out, todo = Path(out), []
        for j in jobs:
            prompt = (out / j["prompt"]).read_text(encoding="utf-8")
            schema = json.loads((out / j["schema"]).read_text(encoding="utf-8"))
            n = prompt_tokens(self.tok, j["job"], prompt, self.limit)
            max_tokens = min(j["max_tokens"], self.max_len - n - 64)
            schema_sha = hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            params = {"temperature": 0, "max_tokens": max_tokens, "guided_json": j["schema"], "schema_sha": schema_sha}
            k, path = LC.key(self.model_id, params, prompt, j["run_tag"]), out / "responses" / f"{j['job']}.jsonl"
            if LC.get(path, k) is None:
                todo.append({"job": j, "prompt": prompt, "schema": schema, "max_tokens": max_tokens, "params": params, "key": k, "path": path})
        self.log(f"{len(jobs) - len(todo)} cached, {len(todo)} to run in batches of {self.batch}")
        bad = 0
        for b0 in range(0, len(todo), self.batch):
            items = todo[b0:b0 + self.batch]
            t0 = time.time()
            outs, flags = self._generate([self.chat(it["prompt"]) for it in items], items)
            secs = time.time() - t0
            for it, o, guided in zip(items, outs, flags):
                row = self._row(it, o, guided, LC.token_fields(o, secs, len(items)))
                if row["errors"] and guided:
                    t1 = time.time()
                    o2 = self.engine.generate([self.chat(it["prompt"])], self.sampling(it["max_tokens"], None))[0]
                    row2 = self._row(it, o2, False, LC.token_fields(o2, time.time() - t1, 1))
                    best = row2 if len(row2["errors"]) < len(row["errors"]) else row
                    best.update(retried=True, prompt_tokens=row["prompt_tokens"] + row2["prompt_tokens"],
                                output_tokens=row["output_tokens"] + row2["output_tokens"])
                    row = best
                bad += bool(row["errors"])
                LC.put(it["path"], it["key"], row)
                self.log(f"{it['job']['job']}: tokens in {row['prompt_tokens']} out {row['output_tokens']}, errors {len(row['errors'])}, "
                         f"guided {row['guided']}, finish {row['finish_reason']}")
            self.log(f"batch of {len(items)} took {secs:.0f} s ({b0 + len(items)}/{len(todo)} done)")
        return {"jobs": len(jobs), "run": len(todo), "parse_errors": bad}
