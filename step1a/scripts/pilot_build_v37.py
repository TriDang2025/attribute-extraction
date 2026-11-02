"""wf_v3.7 Colab batch, T14: A (the v3.1 v2 entity prompt) in 3 orders and its split pass on three more Step 1a runs.

python scripts/pilot_build_v37.py [--ents train,hotel,restaurant] [--out results/loop1_v37/colab] [--seed 0]
  -> <out>/{prompts/*.txt + *.schema.json, examples.csv, manifest.json, prompt_stats.md}
Runs (RUNS): v23d50 = results/graph_v23_dev50, v22d50b = results/graph_v22_dev50b, v23d50b = results/graph_v23_dev50b.
(dev50 v2.2 is the old loop1_v31 / loop1_v36 data.) Per run and entity:
- <ent>_a_<run>_s{0,1,2}: A as pilot_build_v31 / pilot_build_v36 build it (k from the same fit, the same max_tokens
  rule). Orders: s0 = order_seed None (A r1), s1 = SHUFFLE_SEED 1 (A r2, as v3.6 order_seed(1)), s2 = seed 2 (A s2).
- <ent>_<run>_split_<cid>_r1: the v3.1 split pass (render_split, k 16) for every cluster with >= 8 mentions. The name
  makes pilot_verify.load_split_results read it as ent "<ent>_<run>", tag r1.
Manifest: `family` a | split; every row has `run`; the rows of other families (W3's baseline) are kept as they are and the
rows of this builder are replaced. Reads <run>/{docs.jsonl, spans/*}. No encoder, no LLM.
Check (printed, in prompt_stats.md): the same builder on results/graph_v22_dev50 reproduces loop1_v31 <ent>_v2.txt /
<ent>_v2_r2.txt and loop1_v36 <ent>_v2_s2.txt byte for byte (LF text).
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import graph as GR  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from pilot_build_v31 import K_FALLBACK, SHUFFLE_SEED, SPLIT_MAX_TOKENS, TOKEN_LIMIT, max_tokens  # noqa: E402
from pilot_build_v32 import order_seed  # noqa: E402
from pilot_build_v36 import earlier_output, v31_check  # noqa: E402

RUNS = {"v23d50": "results/graph_v23_dev50", "v22d50b": "results/graph_v22_dev50b", "v23d50b": "results/graph_v23_dev50b"}
CHECK_RUN = "results/graph_v22_dev50"
ORDERS = (0, 1, 2)          # A r1 / A r2 / A s2
FAMILIES = ("a", "split", "baseline")
OLD_BATCH = (46, 385_398, 101_931)   # calls, est. prompt tokens, est. output tokens of the v3.6 batch
ENT_RUN_COLS = ["ex_id", "entity", "cluster_id", "mention_id", "variant"]


def a_name(ent, run, s):
    return f"{ent}_a_{run}_s{s}"


def split_name(ent, run, cid):
    """File stem of a split job; pilot_verify.load_split_results reads it as ent "<ent>_<run>", cluster cid, tag r1."""
    return f"{ent}_{run}_split_{cid.replace('#', '-')}"


def merge_manifest(old, new_rows, runs):
    """Manifest dict: the rows of `old` whose family is not a builder family (kept as they are, in order) followed by
    `new_rows`; the top-level keys of `old` stay and `runs` is added. `old` may be None or a plain list."""
    old = {"jobs": old} if isinstance(old, list) else dict(old or {"jobs": []})
    kept = [j for j in old["jobs"] if j.get("family") not in ("a", "split")]
    return {**{k: v for k, v in old.items() if k != "jobs"}, "runs": runs, "jobs": kept + new_rows}


def family_rows(rows):
    """Markdown rows and totals [calls, prompt, output] from [(family, est prompt, est output)]."""
    out, tot = [], [0, 0, 0]
    for f in FAMILIES:
        r = [x for x in rows if x[0] == f]
        if r:
            vals = [len(r), sum(x[1] for x in r), sum(int(x[2]) for x in r)]
            out.append(f"| {f} | {vals[0]} | {vals[1]} | {vals[2]} |")
            tot = [a + b for a, b in zip(tot, vals)]
    out.append(f"| total | {tot[0]} | {tot[1]} | {tot[2]} |")
    return out, tot


class RunInput:
    """Docs, export and example inputs of one run dir (cached per (entity, k))."""

    def __init__(self, run_dir, seed):
        run = paths.ROOT / run_dir
        self.docs, _, _ = MN.load_shared(run)
        self.export = MN.load(run / "spans")
        pkl = run / "spans" / "graphs.pkl"
        self.graphs = GR.load(pkl) if pkl.exists() else None
        self.seed, self._inputs = seed, {}

    def inp(self, entity, k):
        if (entity, k) not in self._inputs:
            self._inputs[(entity, k)] = PIN.build_input(self.export, self.docs, entity, k, self.seed, self.graphs)
        return self._inputs[(entity, k)]


def a_prompts(ri, ent):
    """(entity, k, inp, {order: prompt text}) of A for one entity of a run: k from the fit of pilot_build_v31 (the first k
    of K_FALLBACK whose order-None prompt is under TOKEN_LIMIT, else the last)."""
    entity = PIN.find_pilot_entity(ri.export.mentions, ent)
    for k in K_FALLBACK:
        inp = ri.inp(entity, k)
        text0 = PIN.render_v2(inp, ri.export, ri.docs, "v2")
        if PIN.est_tokens(text0) < TOKEN_LIMIT:
            break
    texts = {0: text0}
    for s in ORDERS[1:]:
        texts[s] = PIN.render_v2(inp, ri.export, ri.docs, "v2", order_seed=order_seed(s))
    return entity, k, inp, texts


def reproduction_check(ents, v31, v36, seed):
    """[(entity, check, result)] for the builder on CHECK_RUN against the v3.1 / v3.6 prompt files."""
    ri = RunInput(CHECK_RUN, seed)
    rows = []
    for ent in ents:
        _, _, _, texts = a_prompts(ri, ent)
        old = ((v31, f"loop1_v31/prompts/{ent}_v2.txt", f"{ent}_v2.txt"),
               (v31, f"loop1_v31/prompts/{ent}_v2_r2.txt", f"{ent}_v2_r2.txt"),
               (v36, f"loop1_v36/colab/prompts/{ent}_v2_s2.txt", f"{ent}_v2_s2.txt"))
        rows += [(ent, f"order {s} vs {label}", v31_check(texts[s], root, fname)) for s, (root, label, fname) in zip(ORDERS, old)]
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v37/colab")
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    ap.add_argument("--v31", default="results/loop1_v31")
    ap.add_argument("--v36", default="results/loop1_v36/colab")
    a = ap.parse_args()
    out, v31, v36 = paths.ROOT / a.out, paths.ROOT / a.v31, paths.ROOT / a.v36
    ents = a.ents.split(",")
    (out / "prompts").mkdir(parents=True, exist_ok=True)

    # estimated output tokens: A = the v3.6 A answer of the same entity (<ent>_v2_s2); split = mean of the v3.1 split answers
    a_out = {e: earlier_output(v36 / "responses" / f"{e}_v2_s2.jsonl") for e in ents}
    sp = [earlier_output(p) for p in sorted((v31 / "responses").glob("*_split_*.jsonl"))]
    split_out = round(sum(sp) / len(sp)) if sp else 0

    jobs, ex_rows, stat_rows, est = [], [], [], []

    def emit(name, text, schema, job, exs, k, est_out):
        (out / "prompts" / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
        (out / "prompts" / f"{name}.schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8", newline="\n")
        n = PIN.est_tokens(text)
        fixed = job.pop("max_tokens_fixed", None)
        jobs.append({**job, "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
                     "max_tokens": fixed or max_tokens(n)})
        ex_rows.extend((ex, job["entity"], c, mid, job["job"]) for ex, c, mid in exs)
        est.append((job["family"], n, est_out))
        stat_rows.append(f"| {job['job']} | {job['run']} | {job['entity']} | {k} | {len(text)} | {n} | {est_out} | "
                         f"{'OVER LIMIT' if n >= TOKEN_LIMIT else 'ok'} |")

    for run, run_dir in RUNS.items():
        ri = RunInput(run_dir, a.seed)
        for ent in ents:
            entity, k, inp, texts = a_prompts(ri, ent)
            exs = [(ex, c.cluster_id, mid) for c in inp.clusters for ex, mid in c.examples]
            for s in ORDERS:
                emit(a_name(ent, run, s), texts[s], PIN.schema_v2(inp),
                     {"job": a_name(ent, run, s), "entity": entity, "ent": ent, "variant": "v2", "run_tag": f"s{s}",
                      "kind": "entity", "stage": 1, "nbhd": None, "cluster_id": "", "format": "v2", "round": 0,
                      "carry_from": [], "family": "a", "run": run}, exs, k, a_out[ent])
            for cid in PIN.split_candidates(ri.export, entity, min_share=0.0):
                text, sx = PIN.render_split(ri.export, ri.docs, entity, cid, 16, a.seed)
                name = split_name(ent, run, cid)
                emit(name, text, PIN.schema_split(cid, [e for e, _ in sx]),
                     {"job": f"{name}_r1", "entity": entity, "ent": ent, "variant": f"split_{cid.replace('#', '-')}",
                      "run_tag": "r1", "kind": "split", "stage": 1, "nbhd": None, "cluster_id": cid, "format": "split",
                      "round": 0, "carry_from": [], "family": "split", "run": run, "max_tokens_fixed": SPLIT_MAX_TOKENS},
                     [(e, cid, m) for e, m in sx], 16, split_out)
            print(f"{run} {ent}: entity {entity}, k {k}", flush=True)

    mpath = out / "manifest.json"
    old = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else None
    manifest = merge_manifest(old, jobs, RUNS)
    base = [j for j in manifest["jobs"] if j.get("family") == "baseline"]
    est += [("baseline", j["est_prompt_tokens"], 1000) for j in base]   # output 1,000 per call: W3's estimate
    mpath.write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    pd.DataFrame(ex_rows, columns=ENT_RUN_COLS).to_csv(out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")

    fam, tot = family_rows(est)
    d = [t - o for t, o in zip(tot, OLD_BATCH)]
    check = reproduction_check(ents, v31, v36, a.seed)
    md = [f"# wf_v3.7 Colab batch prompts (seed {a.seed})", "",
          f"Tokens are estimated as chars / 3.5 (baseline: the est_prompt_tokens of W3's manifest rows). k drops 8 -> 6 -> 5 "
          f"when a prompt reaches {TOKEN_LIMIT}. Output tokens: A = the v3.6 A answer of the same entity "
          f"(`<ent>_v2_s2`, exact tokens of its response); split = mean of the v3.1 split answers ({split_out}; estimate: "
          f"new clusters); baseline = 1,000 per call (W3's estimate). Runs: "
          + ", ".join(f"`{r}` = `{p}`" for r, p in RUNS.items()) + ".", "",
          "| job | run | entity | k | chars | est. prompt tokens | est. output tokens | status |",
          "|---|---|---|---|---|---|---|---|", *stat_rows, "",
          "## Estimated calls and tokens per family", "",
          "| family | calls | est. prompt tokens | est. output tokens |", "|---|---|---|---|", *fam, "",
          f"v3.6 batch: {OLD_BATCH[0]} calls, {OLD_BATCH[1]:,} prompt, {OLD_BATCH[2]:,} output tokens. Change: {d[0]:+d} calls, "
          f"{d[1]:+,} prompt, {d[2]:+,} output tokens.", "",
          f"## Byte check: this builder on `{CHECK_RUN}` against the old files (LF text)", "",
          "| entity | check | result |", "|---|---|---|", *[f"| {e} | {c} | {r} |" for e, c, r in check], ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md[-12:]))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)
    if any(r != "identical" for _, _, r in check):
        print("WARNING: an A prompt differs from its old file", file=sys.stderr)


if __name__ == "__main__":
    main()
