"""wf_v4.4 T9 prep: quick cost check, 50 vs more dialogues from the TEAR Conversation TRAINING pool (diary Nov 14). Nothing here runs a GPU.

python scripts/t9_cost_v44.py plan  [--sizes 50,300] [--seed 0] [--out results/wf_v44/t9]
    -> sample_<n>.json (ids), plan.md: corpus tokens, TEAR estimate (TEAR is not run), the Step 1a + 2 commands, the time estimate
python scripts/t9_cost_v44.py step1a --n 50 [--seed 0] --out results/wf_v44/t9/graph_n50
    Step 1a (GLiNER spans, 5/25 segments) + Step 2 (adopted v2.2 clustering F_m2_t06_bk) on the sample: scripts/export_mentions.py with
    split.dialogues replaced by the sample (that script has no id list). Needs the data of `get_conversation_data.py`; run on Colab / CPU.
python scripts/t9_cost_v44.py count --n 50 --run results/wf_v44/t9/graph_n50 --llm-dirs <step3 run> <step4 run> --columns <columns.json>
    -> counts of a finished run (reads the logs): corpus tokens, calls, tokens in / out, clusters, final columns

Facts behind the choices:
- The TEAR labeled pool (tear/data/conversation/pool.jsonl: 200 `train` + 100 `val` rows, both TEAR training data) has 300 dialogues, so 500 is not possible without test.jsonl (never read here):
  the default sizes are 50 and 300 (6x). `sample_ids` refuses a size above the pool. The 50 is a subset of the 300 (one seeded shuffle).
- Step 1a + 2 run on new dialogues with the current code. Step 3 and Step 4 do NOT yet: `run_data_v37.entity_ids` looks up exactly three
  entities (train / hotel / restaurant) through the gold labels, `step3_v43` / `pilot_build_*` build their prompts from the frozen A prompts
  of the two dev sets, and the Step 4 inputs are read from the dev50 / dev50b folders. So the LLM part of T9 is "not done" (see plan.md).
"""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

POOL = REPO / "tear" / "data" / "conversation" / "pool.jsonl"        # the TEAR training pool; test.jsonl is never read
TEAR_RESULTS = REPO / "tear" / "results" / "conversation"
DATASET = "Conversation"
DEMOS = 8                       # demonstration_count of the measured TEAR run (3 shots per utility, merged)
VARIANT = "F_m2_t06_bk"         # adopted Step 1a v2.2 clustering
SIZES = (50, 300)
# Time assumptions (minutes), see time_estimate: per 50 dialogues.
STEP1A_MIN = (2, 25)            # low: export_mentions on dev50 with the GLiNER cache seeded (117 s, export.log); high: entity_seg.py on CPU (AGENTS.md)
GPU_MIN = (1.5, 2.5)            # v4.3 Step 3 + 4, 100 dialogues, 4.4 min of job seconds (T8, a lower bound), one order instead of three -> per 50
LOAD_MIN = (2, 5)               # model loading: not logged in v4.3 (T8); the v4.4 notebook writes results/wf_v44/model_load.json


# ---------------------------------------------------------------- sample and corpus
def load_pool(path=POOL):
    """[{id, text, table, split}] of the TEAR labeled pool (pool.jsonl: 200 `train` + 100 `val` rows, both are TEAR's training data); raises
    on any other split label. The path is fixed to pool.jsonl by the default; the test file is never opened."""
    rows = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    bad = [r["id"] for r in rows if r.get("split") not in ("train", "val")]
    if bad:
        raise ValueError(f"{path} has rows outside the pool splits: {bad[:3]}")
    return rows


def sample_ids(ids, n, seed):
    """First n ids of one seeded shuffle of `ids` (so the sample of 50 is inside the sample of 300). Raises when n > len(ids)."""
    if n > len(ids):
        raise ValueError(f"asked for {n} dialogues but the training pool has {len(ids)} (test.jsonl is not allowed)")
    order = list(ids)
    random.Random(seed).shuffle(order)
    return order[:n]


def tokenizer():
    """The local Llama-3.1 tokenizer, or None (then 4 characters per token)."""
    snaps = sorted((Path.home() / ".cache" / "huggingface" / "hub" / "models--meta-llama--Llama-3.1-8B-Instruct" / "snapshots").glob("*"))
    if not snaps:
        return None
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(snaps[0]), local_files_only=True)


def n_tokens(texts, tok):
    """(tokens, "tok" | "est.") of texts (cost_v43.corpus_tokens)."""
    from s1a import cost_v43 as C
    return C.corpus_tokens(texts, tok)


# ---------------------------------------------------------------- TEAR estimate (TEAR is not run)
def _tear():
    """The TEAR prompt builders (tear/tear_reproduction, imported by path)."""
    sys.path.insert(0, str(REPO / "tear"))
    from tear_reproduction import prompts as TP
    from tear_reproduction import retrieval as TR
    from tear_reproduction import schema as TS
    return TP, TR, TS


def _rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def measured_tear(tok, res=TEAR_RESULTS):
    """Measured per-text facts of the 200-text TEAR run (results/conversation): calls per text with retries, mean output tokens of the
    extraction table and of the discovery pseudo-table (JSON as TEAR writes it), and the corpus-level calls of the L1 run per text."""
    _, _, TS = _tear()
    te, disc = _rows(res / "te_tear_Lfull_s0.jsonl"), _rows(res / "disc_L1_s0.jsonl")
    ar = json.loads((res / "ar_L1_s0.json").read_text(encoding="utf-8"))
    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    dump = lambda t: json.dumps(TS.table_to_json(t, DATASET), ensure_ascii=False)  # noqa: E731
    return {"texts": len(te), "extraction_attempts": mean([c["attempts"] for r in te for c in r["calls"]]),
            "discovery_attempts": mean([c["attempts"] for r in disc for c in r["calls"]]),
            "extraction_out_tokens": n_tokens([dump(r["table"]) for r in te], tok)[0] / len(te),
            "discovery_out_tokens": n_tokens([dump(r["pseudo_table"]) for r in disc], tok)[0] / len(disc),
            "definitions_per_text": len(ar["definitions"]) / len(disc), "judgements_per_text": ar["llm_calls"] / len(disc)}


def tear_prompts(row, pool, seed):
    """(extraction prompt, discovery prompt) for one dialogue row. Stand-ins (TEAR itself retrieves them): DEMOS random other pool rows as
    demonstrations, and the gold table as the extracted table and the source of the hints. Prompt sizes only."""
    TP, TR, TS = _tear()
    demos = random.Random(f"{seed}:{row['id']}").sample([p for p in pool if p["id"] != row["id"]], DEMOS)
    headers, values = row["table"]["headers"], TR.table_values(row["table"])
    ext = TP.extraction_prompt(row["text"], TS.full_schema(DATASET), DATASET, [{"text": d["text"], "table": d["table"]} for d in demos],
                               headers, values)
    dis = TP.discovery_prompt(row["text"], row["table"], DATASET, [{"text": d["text"], **TR.split_table(d["table"], headers)} for d in demos])
    return ext, dis


def integration_prompts(rows):
    """(definition prompt, judge prompt) of a typical integration call: 3 contexts from sample texts / 2 concepts of 25 words each."""
    TP, TR, TS = _tear()
    ctx = [{"text": r["text"], "values": TR.table_values(r["table"])[:3]} for r in rows[:3]]
    concept = {"name": "attribute name", "definition": "word " * 25}
    return TP.definition_prompt("attribute name", ctx, DATASET), TP.judge_prompt(TS.full_schema(DATASET), [concept, concept])


def tear_estimate(rows, pool, seed, tok, measured):
    """dict for the dialogues `rows`: calls and tokens in / out of extraction, discovery, definitions and judgements. Extraction and discovery
    prompts come from TEAR's own builders (stand-in demonstrations), times the measured attempts per call; outputs = measured mean output
    tokens; definition / judge calls = the measured calls per text x n (a linear upper bound: the proposals of more texts overlap more)."""
    ext, dis = zip(*[tear_prompts(r, pool, seed) for r in rows])
    n = len(rows)
    ae, ad = measured["extraction_attempts"], measured["discovery_attempts"]
    d_calls, j_calls = measured["definitions_per_text"] * n, measured["judgements_per_text"] * n
    dprompt, jprompt = integration_prompts(rows)
    tin = {"extraction": n_tokens(ext, tok)[0] * ae, "discovery": n_tokens(dis, tok)[0] * ad,
           "definitions": d_calls * n_tokens([dprompt], tok)[0], "judgements": j_calls * n_tokens([jprompt], tok)[0]}
    calls = {"extraction": n * ae, "discovery": n * ad, "definitions": d_calls, "judgements": j_calls}
    tout = {"extraction": n * ae * measured["extraction_out_tokens"], "discovery": n * ad * measured["discovery_out_tokens"],
            "definitions": d_calls * 40, "judgements": j_calls * 2}            # definition < 50 words, judge answers "One" / "Two"
    parts = {k: {"calls": round(calls[k], 1), "tokens_in": round(tin[k]), "tokens_out": round(tout[k])} for k in calls}
    return {"n": n, "parts": parts, **{k: round(sum(p[k] for p in parts.values()), 1 if k == "calls" else 0) for k in ("calls", "tokens_in", "tokens_out")}}


# ---------------------------------------------------------------- Step 1a + 2 on the sample
def step1a_commands(n, seed, out):
    """The shell commands that produce the Step 1a + 2 run of a sample (and nothing after it)."""
    return ["python scripts/get_conversation_data.py            # once: gitignored data (conversation_ids.txt, MULTIWOZ2.4.zip)",
            f"python scripts/t9_cost_v44.py step1a --n {n} --seed {seed} --out {out}"]


def run_step1a(n, seed, out, variant=VARIANT):
    """scripts/export_mentions.py (spans input only, variant `variant`) on the seeded sample of n training dialogues: replaces
    split.dialogues by the sample, then runs export_mentions.main. No gold / label stage: those need GT files the sample does not have."""
    import export_mentions as EM
    from s1a import split as SPL
    ids = sample_ids([r["id"] for r in load_pool()], n, seed)
    by_id = {d["id"]: d for d in SPL.load_dialogues(SPL.N_DEV)}
    SPL.dialogues = lambda split, limit=None, unseal=False: [by_id[i] for i in ids]
    sys.argv = ["export_mentions.py", "--split", "dev", "--limit", str(n), "--input", "spans", "--out", str(out), "--variant", variant]
    EM.main()


# ---------------------------------------------------------------- the counter (reads the logs of a finished run)
def count_run(llm_dirs, run_dir, columns_file, corpus_tokens):
    """{corpus_tokens, calls, jobs, retries, tokens_in, tokens_out, clusters, entities, final_columns} of a finished run: calls and tokens from
    the cached rows under each llm dir (log_v44.call_rows; calls = jobs + unguided retries, cost_v43.totals), clusters and entities from
    <run>/spans/clusters.csv, final columns = the length of the columns file (a JSON list)."""
    import csv
    from s1a import cost_v43 as C
    from s1a import log_v44 as L
    rows = [r for d in llm_dirs for r in L.call_rows(d) if "fake" not in r["file"].split("/")]
    with open(Path(run_dir) / "spans" / "clusters.csv", encoding="utf-8", newline="") as f:
        cl = list(csv.DictReader(f))
    cols = json.loads(Path(columns_file).read_text(encoding="utf-8"))
    t = C.totals(rows)
    return {"corpus_tokens": corpus_tokens, "calls": t["calls"], "jobs": t["jobs"], "retries": t["retries"], "tokens_in": t["prompt_tokens"],
            "tokens_out": t["output_tokens"], "clusters": len(cl), "entities": len({r["entity"] for r in cl}), "final_columns": len(cols)}


def growth(small, big):
    """{key: big / small} of two count dicts (the 10x question: values far below the size ratio mean sublinear growth)."""
    return {k: round(big[k] / small[k], 2) for k in small if isinstance(small[k], (int, float)) and small[k]}


# ---------------------------------------------------------------- time estimate
def time_estimate(n):
    """{part: (low, high) minutes} for one run of n dialogues (linear in n from the per-50 assumptions above; clusters grow more slowly than
    dialogues, so the GPU part is an upper bound)."""
    k = n / 50
    return {"Step 1a + 2 (CPU, Colab)": tuple(round(x * k, 1) for x in STEP1A_MIN), "Step 3 + 4 calls (GPU)": tuple(round(x * k, 1) for x in GPU_MIN),
            "model loading (GPU, once)": LOAD_MIN}


def plan(sizes, seed, out):
    """Write sample_<n>.json and plan.md under `out`; returns the markdown."""
    pool, tok = load_pool(), tokenizer()
    ids = sample_ids([r["id"] for r in pool], max(sizes), seed)
    by_id = {r["id"]: r for r in pool}
    measured = measured_tear(tok)
    out.mkdir(parents=True, exist_ok=True)
    est = {}
    for n in sizes:
        rows = [by_id[i] for i in ids[:n]]
        (out / f"sample_{n}.json").write_text(json.dumps({"seed": seed, "n": n, "source": "tear/data/conversation/pool.jsonl", "ids": ids[:n]}, indent=1) + "\n",
                                              encoding="utf-8", newline="\n")
        est[n] = {"corpus": n_tokens([r["text"] for r in rows], tok), "tear": tear_estimate(rows, pool, seed, tok, measured), "time": time_estimate(n)}
    lo, hi = sizes[0], sizes[-1]
    md = ["# T9 prep: quick cost check (not run)\n",
          f"**Status: not done.** Step 1a + 2 can run on a sample now; Step 3 and Step 4 cannot (see Missing). Sizes {', '.join(map(str, sizes))} "
          f"(ratio {hi / lo:g}x), seed {seed}, source `tear/data/conversation/pool.jsonl` (the 300 TEAR pool dialogues, 200 train + 100 val; 500 do not exist there, test.jsonl is not used). "
          f"Samples: `sample_<n>.json` (the {lo} are the first {lo} of the {hi}).\n", "## Corpus and TEAR (estimated, TEAR is not run)\n",
          "| dialogues | corpus tokens | TEAR calls | TEAR tokens in | TEAR tokens out | extraction / discovery tokens in | definitions + judgements calls |", "|---|---|---|---|---|---|---|"]
    for n, e in est.items():
        t, p = e["tear"], e["tear"]["parts"]
        md.append(f"| {n} | {e['corpus'][0]:,} ({e['corpus'][1]}) | {t['calls']:,.0f} | {t['tokens_in']:,} | {t['tokens_out']:,} | "
                  f"{p['extraction']['tokens_in']:,} / {p['discovery']['tokens_in']:,} | {p['definitions']['calls'] + p['judgements']['calls']:,.0f} |")
    md += [f"| ratio {hi}/{lo} | {est[hi]['corpus'][0] / est[lo]['corpus'][0]:.2f} | {est[hi]['tear']['calls'] / est[lo]['tear']['calls']:.2f} | "
           f"{est[hi]['tear']['tokens_in'] / est[lo]['tear']['tokens_in']:.2f} | {est[hi]['tear']['tokens_out'] / est[lo]['tear']['tokens_out']:.2f} | | |", "",
           f"How TEAR is estimated: per text, 1 extraction call + 1 discovery call ({measured['extraction_attempts']:.2f} / {measured['discovery_attempts']:.2f} attempts per call, "
           f"measured on {measured['texts']} texts), each prompt built with TEAR's own builders (`tear_reproduction.prompts`) with {DEMOS} stand-in demonstrations "
           "(random pool dialogues instead of the retrieved ones) and the gold table as the hints / known table; output tokens = the measured mean "
           f"({measured['extraction_out_tokens']:.0f} extraction, {measured['discovery_out_tokens']:.0f} discovery). Corpus-level calls: "
           f"{measured['definitions_per_text']:.3f} definition + {measured['judgements_per_text']:.3f} judge calls per text (measured L1 run), scaled linearly (upper bound; "
           "40 / 2 output tokens assumed). So TEAR is linear in the dialogues by construction (ratio = size ratio).\n",
           "## Our pipeline: what runs now and what is missing\n",
           "- **Runs now (current code, no GPU needed):** Step 1a + Step 2 = `scripts/export_mentions.py --variant F_m2_t06_bk` (GLiNER generic spans, 5/25 snapped segments, v2.2 clustering) through "
           "`python scripts/t9_cost_v44.py step1a`, which swaps `split.dialogues` for the seeded sample. Gives mentions, clusters, vectors (`<out>/spans/`).",
           "- **Missing for the LLM part (not written, would be new code, not a small change):**",
           "  1. Entities: `run_data_v37.entity_ids` finds exactly three entities (train / hotel / restaurant) through the gold `entity_gold` labels; 300 dialogues also hold attraction, taxi, hospital, police. Step 3 would need to iterate over all Step 1a entities without GT.",
           "  2. Step 3 prompts: `step3_v43.build` cuts the frozen A prompts of `results/wf_v42/t1b_step3_keyed` (made by `pilot_build_v37.py` for the two dev sets); a new run needs that builder (render_v2) on the new `spans/` folder.",
           "  3. Scoring-side inputs the builders read: `spans/labels.csv` (graph_run label stage) and `docs.jsonl`; the Step 4 inputs (`step4_inputs`, `inputs_v4.py`) read `results/wf_v4/inputs/<set>` of dev50 / dev50b only.",
           "  4. Counting: `count` reads `log_v44.call_rows` of the Step 3 / Step 4 run folders, `spans/clusters.csv` and the final columns file; ready.",
           f"- Data: `get_conversation_data.py` must have been run (`chunking/data/conversation_ids.txt`, `MULTIWOZ2.4.zip`; gitignored, absent in a fresh worktree).\n",
           "## Commands (Step 1a + 2 only)\n", "```", *step1a_commands(lo, seed, f"results/wf_v44/t9/graph_n{lo}"), *step1a_commands(hi, seed, f"results/wf_v44/t9/graph_n{hi}")[1:], "```", "",
           "Then, once Steps 3 / 4 are wired: `python scripts/t9_cost_v44.py count --n <n> --run results/wf_v44/t9/graph_n<n> --llm-dirs <step3 folder> <step4 folder> --columns <final columns json>` for each size, and compare the two with the `growth` ratios.\n",
           "## Time estimate (minutes, assumptions)\n", "| part | " + " | ".join(f"{n} dialogues" for n in sizes) + " |", "|---|" + "---|" * len(sizes)]
    for part in est[lo]["time"]:
        md.append(f"| {part} | " + " | ".join(f"{est[n]['time'][part][0]}-{est[n]['time'][part][1]}" for n in sizes) + " |")
    tot = {n: (sum(v[0] for v in est[n]["time"].values()), sum(v[1] for v in est[n]["time"].values())) for n in sizes}
    md += ["| **total** | " + " | ".join(f"**{tot[n][0]:.0f}-{tot[n][1]:.0f}**" for n in sizes) + " |", "",
           f"Assumptions: Step 1a + 2 {STEP1A_MIN[0]}-{STEP1A_MIN[1]} min per 50 dialogues (low = the 117 s `export_mentions` run on dev50 with the GLiNER cache seeded; high = the 25 min of `entity_seg.py` on a laptop CPU, "
           f"AGENTS.md); GPU calls {GPU_MIN[0]}-{GPU_MIN[1]} min per 50 (v4.3: 3.2 + 1.2 = 4.4 min job seconds for 100 dialogues, a lower bound for the names stage, one order instead of three; scaled linearly, so an upper bound "
           f"when clusters saturate); model loading {LOAD_MIN[0]}-{LOAD_MIN[1]} min is a guess (not logged in v4.3; v4.4 writes `results/wf_v44/model_load.json`). Not including the missing wiring. "
           "Measure the 50 first and multiply by 6.\n"]
    text = "\n".join(md)
    (out / "plan.md").write_text(text, encoding="utf-8", newline="\n")
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part", choices=("plan", "step1a", "count"))
    ap.add_argument("--sizes", default=",".join(map(str, SIZES)))
    ap.add_argument("--n", type=int)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v44" / "t9")
    ap.add_argument("--run", type=Path, help="count: Step 1a run folder (has spans/clusters.csv)")
    ap.add_argument("--llm-dirs", nargs="+", type=Path, help="count: run folders with responses/")
    ap.add_argument("--columns", type=Path, help="count: final columns JSON list")
    a = ap.parse_args()
    if a.part == "plan":
        plan(tuple(int(x) for x in a.sizes.split(",")), a.seed, a.out)
        print("T9 plan written to", a.out / "plan.md")
    elif a.part == "step1a":
        run_step1a(a.n, a.seed, a.out)
    else:
        pool, tok = load_pool(), tokenizer()
        by_id = {r["id"]: r for r in pool}
        ids = sample_ids(list(by_id), a.n, a.seed)
        counts = count_run(a.llm_dirs, a.run, a.columns, n_tokens([by_id[i]["text"] for i in ids], tok)[0])
        (a.out / f"counts_n{a.n}.json").parent.mkdir(parents=True, exist_ok=True)
        (a.out / f"counts_n{a.n}.json").write_text(json.dumps(counts, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(counts))


if __name__ == "__main__":
    main()
