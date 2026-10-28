"""wf_v3.1 Step-3 pilot prompts for 3 predicted entities (contract: PILOT_V31_CONTRACT.md).

python scripts/pilot_build_v31.py [--run results/graph_v22_dev50] [--ents train,hotel,restaurant]
                                  [--out results/loop1_v31] [--seed 0] [--hints-cache <window_vectors.npz>] [--no-hints]
  -> <out>/{prompts/*.txt + *.schema.json, examples.csv, manifest.json, prompt_stats.md}  (hints.csv: scripts/hint_check.py)
Reads <run>/{docs.jsonl, spans/*}. No encoder, no LLM. v2_hints needs the window vector cache (skipped with a
warning when missing).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import graph as GR  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402

TOKEN_LIMIT = 28_000
K_FALLBACK = (8, 6, 5)
LONG_K = 16
CTX = 32768
SPLIT_MAX_TOKENS = 3000
SHUFFLE_SEED = 1


def max_tokens(tok):
    return max(2000, min(12000, int(CTX - tok * 1.15 - 64)))


def window_matrix(export, cache):
    """Window vectors aligned to export.ids, or None when the cache file is missing."""
    if not Path(cache).exists():
        return None
    z = np.load(cache)
    pos = {int(i): j for j, i in enumerate(z["ids"])}
    return z["x"][[pos[int(i)] for i in export.ids]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v31")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--hints-cache", default=None)
    ap.add_argument("--no-hints", action="store_true", help="skip v2_hints (wf_v3.1: window hints were 8%% right)")
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    cache = Path(a.hints_cache) if a.hints_cache else run / "spans" / "window_vectors.npz"
    docs, _, _ = MN.load_shared(run)
    export = MN.load(run / "spans")
    pkl = run / "spans" / "graphs.pkl"
    graphs = GR.load(pkl) if pkl.exists() else None
    window_x = None if a.no_hints else window_matrix(export, cache)
    if window_x is None:
        print(f"WARNING: {cache} missing; v2_hints and window hints skipped", file=sys.stderr)
    (out / "prompts").mkdir(parents=True, exist_ok=True)

    inputs = {}

    def inp_for(entity, k):
        if (entity, k) not in inputs:
            inputs[(entity, k)] = PIN.build_input(export, docs, entity, k, a.seed, graphs)
        return inputs[(entity, k)]

    jobs, ex_rows, stat_rows = [], [], []

    def emit(ent, entity, variant, tag, kind, cid, text, schema, fmt, inp_exs, k, fname=None, fixed_tokens=None):
        """Write prompt + schema, add the manifest job, example rows and a stats row."""
        name = f"{ent}_{variant}"
        fname = fname or name
        (out / "prompts" / f"{fname}.txt").write_text(text, encoding="utf-8", newline="\n")
        (out / "prompts" / f"{fname}.schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8",
                                                             newline="\n")
        tok = PIN.est_tokens(text)
        jobs.append({"job": f"{name}_{tag}", "entity": entity, "ent": ent, "variant": variant, "run_tag": tag,
                     "kind": kind, "cluster_id": cid, "prompt": f"prompts/{fname}.txt",
                     "schema": f"prompts/{fname}.schema.json",
                     "max_tokens": fixed_tokens or max_tokens(tok), "format": fmt})
        ex_rows.extend((ex, entity, c, mid, name) for ex, c, mid in inp_exs)
        status = "OVER LIMIT" if tok >= TOKEN_LIMIT else "ok"
        stat_rows.append(f"| {fname} | {entity} | {k} | {len(text)} | {tok} | {status} |")

    def entity_exs(inp):
        return [(ex, c.cluster_id, mid) for c in inp.clusters for ex, mid in c.examples]

    for ent in a.ents.split(","):
        entity = PIN.find_pilot_entity(export.mentions, ent)
        print(f"{ent}: entity {entity}")

        def fit(render, ks):
            """First k whose prompt is under the limit (else the last one): (k, inp, text)."""
            for k in ks:
                inp = inp_for(entity, k)
                text = render(inp)
                if PIN.est_tokens(text) < TOKEN_LIMIT:
                    break
            return k, inp, text

        k, inp, text = fit(lambda i: PIN.render(i, export, docs, "nohints"), K_FALLBACK)
        emit(ent, entity, "nohints", "r1", "entity", "", text, PIN.schema_v1(inp), "v1", entity_exs(inp), k)
        if ent == "train":
            inp = inp_for(entity, LONG_K)
            text = PIN.render(inp, export, docs, "nohints")
            emit(ent, entity, "nohints_long", "r1", "entity", "", text, PIN.schema_v1(inp), "v1",
                 entity_exs(inp), LONG_K)
        for variant in ("v2", "v2_nocontext"):
            k, inp, text = fit(lambda i: PIN.render_v2(i, export, docs, variant), K_FALLBACK)
            emit(ent, entity, variant, "r1", "entity", "", text, PIN.schema_v2(inp), "v2", entity_exs(inp), k)
            if variant == "v2":
                text2 = PIN.render_v2(inp, export, docs, "v2", order_seed=SHUFFLE_SEED)
                emit(ent, entity, "v2", "r2", "entity", "", text2, PIN.schema_v2(inp), "v2", entity_exs(inp), k,
                     fname=f"{ent}_v2_r2")
        if window_x is not None:
            from s1a import hints as HN  # written by another worker; imported lazily
            hints = HN.merge_hints(export, entity, "filtered", window_x)
            k, inp, text = fit(lambda i: PIN.render_v2(i, export, docs, "v2_hints", hints), K_FALLBACK)
            emit(ent, entity, "v2_hints", "r1", "entity", "", text, PIN.schema_v2(inp), "v2", entity_exs(inp), k)
        for cid in PIN.split_candidates(export, entity, min_share=0.0):  # every cluster with >= 8 mentions
            text, exs = PIN.render_split(export, docs, entity, cid, 16, a.seed)
            fcid = cid.replace("#", "-")
            emit(ent, entity, f"split_{fcid}", "r1", "split", cid, text,
                 PIN.schema_split(cid, [e for e, _ in exs]), "split", [(e, cid, m) for e, m in exs], 16,
                 fixed_tokens=SPLIT_MAX_TOKENS)

    pd.DataFrame(ex_rows, columns=["ex_id", "entity", "cluster_id", "mention_id", "variant"]).to_csv(
        out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "manifest.json").write_text(json.dumps(jobs, indent=1), encoding="utf-8", newline="\n")
    md = [f"# wf_v3.1 pilot prompts (run `{a.run}`, seed {a.seed})", "",
          f"Tokens are estimated as chars / 3.5; k drops 8 -> 6 -> 5 when a prompt reaches {TOKEN_LIMIT}.", "",
          "| prompt | entity | k | chars | est. tokens | status |", "|---|---|---|---|---|---|", *stat_rows, ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
