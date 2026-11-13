"""wf_v4.3 U6: cost table (calls, tokens, GPU minutes, loading time, corpus tokens) of option B (wf_v4.2) vs v4.3, per set and for both sets.

Reads the cached rows of a run folder with log_v43.call_rows (VllmBackend rows: prompt / output tokens, batch_seconds, retried). Facts the
numbers depend on:
- A retried row (guided answer with parse errors, rerun once unguided) holds the tokens of both calls, so calls = jobs + retries.
- Rows of one batch share batch_seconds; a batch counts once. Batches are told apart by (stage, batch_seconds): stage = the _41 .. _44 suffix of a
  Step 4 job file, else one stage. Two batches of one stage with the same seconds (2 decimals) would be merged (not expected). The seconds of
  an unguided retry are only kept when the retry answer is the better one, so GPU minutes can be a little low where retries happened.
- GPU time of a batch cannot be split by set (the sets run in one batch), so it is given for both sets together.
- Model loading time is only reported if a run_info.json holds a key with "load" in its name; else "not logged".
"""
import json
import re
from pathlib import Path

from .log_v43 import call_rows, call_totals

SETS = ("dev50", "dev50b")
NOT_RUN = "not run"
NOT_LOGGED = "not logged"


def set_of(job):
    """dev50 / dev50b of a job name (Step 3 'hotel_a_v22d50b_s0', Step 4 'c1_dev50b_s0_41'); "other" if it names neither."""
    j = str(job or "")
    if re.search(r"(dev50b|d50b)", j):
        return "dev50b"
    return "dev50" if re.search(r"(dev50|d50)", j) else "other"


def stage_of(file):
    """Stage of a response file path: the _41 .. _44 suffix of a Step 4 job, else "all"."""
    m = re.search(r"_(4[1-4])\.jsonl$", str(file))
    return m.group(1) if m else "all"


def gpu_seconds(rows):
    """Model seconds of call rows with each batch counted once (see the module doc); rows without batch_seconds add nothing."""
    batches = {}
    for r in rows:
        if r["batch_seconds"] is not None:
            batches[(stage_of(r["file"]), r["batch_seconds"])] = r["batch_seconds"]
    return sum(batches.values())


def totals(rows):
    """{calls (jobs + retries), jobs, retries, prompt_tokens, output_tokens} of call rows."""
    t = call_totals(rows)
    return {"calls": t["calls"] + t["retried"], "jobs": t["calls"], "retries": t["retried"],
            "prompt_tokens": t["prompt_tokens"], "output_tokens": t["output_tokens"]}


def run_stats(out):
    """Per-set totals + the GPU seconds of a run folder: {"rows": n, "gpu_seconds": s, "dev50": totals, "dev50b": totals, "both": totals}.
    None if the folder has no response rows (not run). Rows under a folder named "fake" (fake-model dry runs) are not counted."""
    rows = [r for r in (call_rows(out) if Path(out).exists() else []) if "fake" not in r["file"].split("/")]
    if not rows:
        return None
    return {"rows": len(rows), "gpu_seconds": gpu_seconds(rows), **{s: totals([r for r in rows if set_of(r["job"]) == s]) for s in SETS},
            "both": totals(rows)}


def load_seconds(*dirs):
    """Sum of the numeric run_info.json values whose key has "load" in it, under the folders; None if there is none."""
    found = []
    for d in dirs:
        for p in sorted(Path(d).glob("**/run_info.json")) if Path(d).exists() else []:
            found += [v for k, v in json.loads(p.read_text(encoding="utf-8")).items() if "load" in k.lower() and isinstance(v, (int, float))]
    return sum(found) if found else None


def corpus_tokens(texts, tok=None):
    """(tokens, "tok" | "est.") of texts: exact with a tokenizer (no special tokens), else 4 characters per token."""
    if tok is not None:
        return sum(len(tok(t, add_special_tokens=False).input_ids) for t in texts), "tok"
    return round(sum(len(t) for t in texts) / 4), "est."


def _fmt(n, digits=0):
    return n if isinstance(n, str) else f"{n:,.{digits}f}"


def cost_rows(steps, corpus, loading):
    """The cost table. steps = {column: {"step3": stats|None, "step4": stats|None, "post": stats|None}} for the columns (e.g. "option B",
    "v4.3"), each a run_stats result; corpus = {set: (tokens, "tok"|"est.")}; loading = {column: seconds|None}.
    Returns rows [{row, <column> <set>..., note}] with the sets dev50, dev50b, both for every column."""
    cols = [(c, s) for c in steps for s in (*SETS, "both")]
    rows = []

    def add(name, fn, note=""):
        rows.append({"row": name, **{f"{c} {s}": fn(c, s) for c, s in cols}, "note": note})

    def stat(c, step, s, key):
        st = steps[c].get(step)
        return NOT_RUN if st is None else st[s][key]

    for step, label in (("step3", "Step 3"), ("step4", "Step 4"), ("post", "Post-step (U0)")):
        if step == "post" and all(steps[c].get("post") is None for c in steps):
            continue
        for key, what, note in (("calls", "calls", "jobs + unguided retries"), ("retries", "of which unguided retries", ""),
                                ("prompt_tokens", "tokens in", ""), ("output_tokens", "tokens out", "")):
            add(f"{label} {what}", lambda c, s, step=step, key=key: stat(c, step, s, key), note)
        add(f"{label} GPU minutes", lambda c, s, step=step: NOT_RUN if steps[c].get(step) is None else "n/a (batches shared)" if s != "both"
            else round(steps[c][step]["gpu_seconds"] / 60, 1), "both sets together")

    def llm_total(c, s, key=None):
        parts = [steps[c].get(k) for k in ("step3", "step4", "post")]
        if all(p is None for p in parts):
            return None
        keys = (key,) if key else ("prompt_tokens", "output_tokens")
        return sum(p[s][k] for p in parts if p for k in keys)

    def gpu(c, s):
        parts = [steps[c].get(k) for k in ("step3", "step4", "post")]
        if all(p is None for p in parts):
            return NOT_RUN
        return "n/a (batches shared)" if s != "both" else round(sum(p["gpu_seconds"] for p in parts if p) / 60, 1)

    add("GPU minutes total (model time, batches counted once)", gpu, "both sets together; from batch_seconds")
    def load(c, s):
        if s != "both":
            return "n/a"
        if llm_total(c, "both") is None:
            return NOT_RUN
        return NOT_LOGGED if loading.get(c) is None else round(loading[c] / 60, 1)

    add("Model loading time", load, "minutes, from run_info.json")
    add("LLM tokens (in + out)", lambda c, s: NOT_RUN if llm_total(c, s) is None else llm_total(c, s), "Steps 3 + 4 (+ post-step)")
    add("Corpus tokens", lambda c, s: corpus[s][0] if s in corpus else sum(v[0] for v in corpus.values()),
        "dialogue turns, Llama-3.1 tokenizer where marked tok, else est. (4 chars/token): " + ", ".join(f"{s} {v[1]}" for s, v in corpus.items()))
    add("LLM tokens / corpus tokens (in + out)", lambda c, s: NOT_RUN if llm_total(c, s) is None else
        round(llm_total(c, s) / (corpus[s][0] if s in corpus else sum(v[0] for v in corpus.values())), 1), "")
    add("Output tokens / corpus tokens", lambda c, s: NOT_RUN if llm_total(c, s, "output_tokens") is None else
        round(llm_total(c, s, "output_tokens") / (corpus[s][0] if s in corpus else sum(v[0] for v in corpus.values())), 2), "")
    return rows


def to_markdown(rows):
    """Markdown table of cost_rows (numbers with thousands separators; the note column last)."""
    head = [k for k in rows[0] if k != "note"]
    lines = ["| " + " | ".join(head) + " | note |", "|" + "---|" * (len(head) + 1)]
    for r in rows:
        cells = [r["row"]] + [_fmt(r[k], 1 if isinstance(r[k], float) else 0) if r[k] is not None else NOT_RUN for k in head[1:]]
        lines.append("| " + " | ".join(cells) + f" | {r['note']} |")
    return "\n".join(lines) + "\n"
