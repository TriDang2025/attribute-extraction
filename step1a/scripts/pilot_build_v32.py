"""wf_v3.2 Step-3 pilot prompts, stage 1 (contract: PILOT_V32_CONTRACT.md).

python scripts/pilot_build_v32.py [--run results/graph_v22_dev50] [--ents train,hotel,restaurant]
                                  [--out results/loop1_v32] [--seed 0]
  -> <out>/{prompts/*.txt + *.schema.json, neighbourhoods.csv, examples.csv, stage2_inputs.json,
            stage2_vectors.npz, generic.json, manifest.json, prompt_stats.md}
Jobs: entity (neighbourhood groups x order seeds 0,1,2), noise (per cluster), gate and split (per split
candidate). Reconcile prompts (stage 2) are built later by pilot_combine.build_stage2. Reads <run>/{docs.jsonl,
spans/*}. No encoder, no LLM.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import graph as GR  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from pilot_build_v31 import K_FALLBACK, SPLIT_MAX_TOKENS, TOKEN_LIMIT, max_tokens  # noqa: E402

SEEDS = (0, 1, 2)
PROBE_MAX_TOKENS = 1500   # noise and gate answers are one short object


def order_seed(seed):
    """Seed 0 keeps the id order (as v3.1 r1); seeds 1 and 2 shuffle the clusters with that seed."""
    return None if seed == 0 else seed


def block_lines(text):
    """(head line, example lines) of the cluster block of a noise / gate prompt (2nd paragraph)."""
    block = text.split("\n\n")[1].splitlines()
    return block[0], block[2:]


def cost_rows(jobs, tok):
    """Markdown rows: calls and est. prompt tokens per entity and variant B / C / D (contract, token stats).
    D counts every split job (the gate decides later which run) and no reconcile jobs (stage 2)."""
    rows = []
    for ent in dict.fromkeys(j["ent"] for j in jobs):
        mine = [j for j in jobs if j["ent"] == ent]
        pick = {"B": [j for j in mine if (j["kind"] == "entity" and j["run_tag"] == "s0") or j["kind"] == "split"],
                "C": [j for j in mine if j["kind"] in ("entity", "split")],
                "D": mine}
        for v, js in pick.items():
            rows.append(f"| {ent} | {v} | {len(js)} | {sum(tok[j['job']] for j in js)} |")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v32")
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    docs, _, _ = MN.load_shared(run)
    export = MN.load(run / "spans")
    pkl = run / "spans" / "graphs.pkl"
    graphs = GR.load(pkl) if pkl.exists() else None
    (out / "prompts").mkdir(parents=True, exist_ok=True)

    inputs = {}

    def inp_for(entity, k):
        if (entity, k) not in inputs:
            inputs[(entity, k)] = PIN.build_input(export, docs, entity, k, a.seed, graphs)
        return inputs[(entity, k)]

    jobs, tok, ex_rows, stat_rows, nb_rows = [], {}, [], [], []
    s2, s2_cid, s2_cx, s2_eid, s2_ex = {}, [], [], [], []
    cents = GR.centroids(export)
    generic = PC.generic_flags(export.mentions)   # over all entities of the run
    generic_out = {}
    pos = {int(i): j for j, i in enumerate(export.ids)}

    def emit(ent, entity, variant, tag, kind, fname, text, schema, fmt, exs, k, nbhd=None, cid="", fixed=None):
        """Write prompt + schema, add the stage-1 manifest job, example rows and a stats row."""
        (out / "prompts" / f"{fname}.txt").write_text(text, encoding="utf-8", newline="\n")
        (out / "prompts" / f"{fname}.schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8",
                                                             newline="\n")
        n = PIN.est_tokens(text)
        tok[fname] = n
        jobs.append({"job": fname, "entity": entity, "ent": ent, "variant": variant, "run_tag": tag, "kind": kind,
                     "stage": 1, "nbhd": nbhd, "cluster_id": cid, "prompt": f"prompts/{fname}.txt",
                     "schema": f"prompts/{fname}.schema.json", "max_tokens": fixed or max_tokens(n), "format": fmt})
        ex_rows.extend((ex, entity, c, mid, fname) for ex, c, mid in exs)
        stat_rows.append(f"| {fname} | {entity} | {k} | {len(text)} | {n} | "
                         f"{'OVER LIMIT' if n >= TOKEN_LIMIT else 'ok'} |")

    for ent in a.ents.split(","):
        entity = PIN.find_pilot_entity(export.mentions, ent)
        groups = PIN.neighbourhoods(export, entity)
        print(f"{ent}: entity {entity}, groups {[len(g) for g in groups]}")
        nb_rows += [(ent, entity, gi, c) for gi, g in enumerate(groups) for c in g]
        for gi, grp in enumerate(groups):
            outside, target = PIN.outside_context(export, groups, gi), PIN.nbhd_target(len(grp))
            for k in K_FALLBACK:   # k from the seed-0 prompt; the other orders keep it
                inp = inp_for(entity, k)
                if PIN.est_tokens(PIN.render_v3(inp, export, docs, grp, outside, target)) < TOKEN_LIMIT:
                    break
            exs = [(ex, c.cluster_id, mid) for c in inp.clusters if c.cluster_id in grp for ex, mid in c.examples]
            for seed in SEEDS:
                text = PIN.render_v3(inp, export, docs, grp, outside, target, order_seed(seed))
                emit(ent, entity, "nbhd", f"s{seed}", "entity", f"{ent}_nbhd{gi}_s{seed}", text,
                     PIN.schema_v3(inp, grp), "v3", exs, k, nbhd=gi)
        clusters, split_ex = {}, {}
        for cid in (c for g in groups for c in g):
            fcid = cid.replace("#", "-")
            text, exs = PIN.render_noise(export, docs, entity, cid, PIN.NOISE_K, a.seed)
            emit(ent, entity, "noise", "r1", "noise", f"{ent}_noise_{fcid}", text, PIN.schema_noise(cid), "noise",
                 [(e, cid, m) for e, m in exs], PIN.NOISE_K, cid=cid, fixed=PROBE_MAX_TOKENS)
            head, lines = block_lines(text)
            clusters[cid] = {"head": head, "lines": lines}
            s2_cid.append(cid)
            s2_cx.append(cents[cid])
        for cid in PIN.split_candidates(export, entity, min_share=0.0):   # every cluster with >= 8 mentions
            fcid = cid.replace("#", "-")
            text, exs = PIN.render_gate(export, docs, entity, cid, PIN.GATE_K, a.seed)
            emit(ent, entity, "gate", "r1", "gate", f"{ent}_gate_{fcid}", text, PIN.schema_gate(cid), "gate",
                 [(e, cid, m) for e, m in exs], PIN.GATE_K, cid=cid, fixed=PROBE_MAX_TOKENS)
            text, exs = PIN.render_split(export, docs, entity, cid, 16, a.seed)
            emit(ent, entity, "split", "r1", "split", f"{ent}_split_{fcid}", text,
                 PIN.schema_split(cid, [e for e, _ in exs]), "split", [(e, cid, m) for e, m in exs], 16,
                 cid=cid, fixed=SPLIT_MAX_TOKENS)
            lines = text.split("\n\n")[1].splitlines()[2:]   # the example lines of the split prompt
            split_ex[cid] = {e: ln for (e, _), ln in zip(exs, lines)}
            s2_eid += [e for e, _ in exs]
            s2_ex += [export.x[pos[int(m)]] for _, m in exs]
        generic_out[ent] = sorted((c for g in groups for c in g if c in generic), key=PIN._cluster_number)
        nbhd_of = {c: gi for gi, g in enumerate(groups) for c in g}
        pm = export.mentions[(export.mentions["entity"] == entity) & (export.mentions["cluster_id"] != "")]
        by_inst = pm.groupby("instance_id")["cluster_id"].agg(lambda s: sorted(set(s), key=PIN._cluster_number))
        cooccur = sorted({(a, b) for cs in by_inst for i, a in enumerate(cs) for b in cs[i + 1:]})
        s2[ent] = {"entity": entity, "clusters": clusters, "split_examples": split_ex,
                   "options": [t for t, _ in inp_for(entity, K_FALLBACK[0]).options], "nbhd": nbhd_of,
                   "cooccur": [list(p) for p in cooccur]}

    dim = export.x.shape[1]
    np.savez(out / "stage2_vectors.npz", cluster_ids=np.array(s2_cid), cluster_x=np.array(s2_cx, dtype=np.float32),
             ex_ids=np.array(s2_eid), ex_x=np.array(s2_ex, dtype=np.float32).reshape(-1, dim))
    (out / "generic.json").write_text(json.dumps(generic_out, indent=1), encoding="utf-8", newline="\n")
    (out / "stage2_inputs.json").write_text(json.dumps(s2, indent=1), encoding="utf-8", newline="\n")
    pd.DataFrame(nb_rows, columns=["ent", "entity", "nbhd", "cluster_id"]).to_csv(
        out / "neighbourhoods.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.DataFrame(ex_rows, columns=["ex_id", "entity", "cluster_id", "mention_id", "variant"]).to_csv(
        out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "manifest.json").write_text(json.dumps(jobs, indent=1), encoding="utf-8", newline="\n")
    md = [f"# wf_v3.2 pilot prompts, stage 1 (run `{a.run}`, seed {a.seed})", "",
          f"Tokens are estimated as chars / 3.5; k drops 8 -> 6 -> 5 when a nbhd prompt reaches {TOKEN_LIMIT}.", "",
          "| prompt | entity | k | chars | est. tokens | status |", "|---|---|---|---|---|---|", *stat_rows, "",
          "## Estimated prompt tokens per variant (stage 1)", "",
          "B = seed-0 entity jobs + all split jobs; C = 3 orders + all split jobs; D = C + noise + gate jobs "
          "(upper bound: all split jobs are counted although only gate-failed clusters run; reconcile jobs "
          "are stage 2 and not counted).", "",
          "| entity | variant | calls | est. prompt tokens |", "|---|---|---|---|", *cost_rows(jobs, tok), ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
