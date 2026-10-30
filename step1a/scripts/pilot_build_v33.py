"""wf_v3.3 Step-3 pilot prompts (contract: PILOT_V33_CONTRACT.md).

python scripts/pilot_build_v33.py [--run results/graph_v22_dev50] [--ents train,hotel,restaurant]
                                  [--out results/loop1_v33] [--seed 0]
  -> <out>/{prompts/*.txt + *.schema.json (+ *.tmpl.txt for carry jobs), neighbourhoods.csv, examples.csv,
            delex_map.json, manifest.json, prompt_stats.md}
Entity jobs of variants e (cue text + role-aware examples + carry-over), e1 (e without carry-over, groups >= 1),
e2 (e without the cue text) and f (e de-lexicalised, seed 0 only). Gate / noise / split / reconcile jobs are
reused from loop1_v32. Reads <run>/{docs.jsonl, spans/*}. No encoder, no LLM.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import delex as DX  # noqa: E402
from s1a import graph as GR  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from pilot_build_v31 import K_FALLBACK, TOKEN_LIMIT, max_tokens  # noqa: E402
from pilot_build_v32 import order_seed  # noqa: E402

SEEDS = (0, 1, 2)
CARRY_TOKENS = 300     # est. tokens of the carry block that is filled in on Colab
# variant -> (first group, seeds, carry-over, cue text)
VARIANTS = {"e": (0, SEEDS, True, True), "e1": (1, SEEDS, False, True),
            "e2": (0, SEEDS, True, False), "f": (0, (0,), True, True)}


def job_name(ent, var, gi, seed):
    return f"{ent}_{var}_nbhd{gi}_s{seed}"


def job_plan(ent, n_groups):
    """[(job name, variant, group, seed, round, carry_from)] of one entity, variants in VARIANTS order.
    A carry job of group g > 0 has round g and carry_from = the same variant and seed, groups 0..g-1;
    group 0 and the jobs of a variant without carry-over have round 0 and carry_from []."""
    plan = []
    for var, (first, seeds, carry, _) in VARIANTS.items():
        for gi in range(first, n_groups):
            for seed in seeds:
                src = [job_name(ent, var, g, seed) for g in range(gi)] if carry else []
                plan.append((job_name(ent, var, gi, seed), var, gi, seed, gi if src else 0, src))
    return plan


def token_rows(jobs, tok):
    """Markdown rows: entity jobs and est. prompt tokens per entity and variant."""
    rows = []
    for ent in dict.fromkeys(j["ent"] for j in jobs):
        for var in VARIANTS:
            js = [j for j in jobs if j["ent"] == ent and j["variant"] == var]
            rows.append(f"| {ent} | {var} | {len(js)} | {sum(tok[j['job']] for j in js)} |")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v33")
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    docs, _, _ = MN.load_shared(run)
    export = MN.load(run / "spans")
    pkl = run / "spans" / "graphs.pkl"
    graphs = GR.load(pkl) if pkl.exists() else None
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    mm = export.mentions
    roles = {int(i): (w if isinstance(w, str) else "") for i, w in zip(mm["mention_id"], mm["left_word"])}

    inputs = {}

    def inp_for(entity, k):
        if (entity, k) not in inputs:
            inputs[(entity, k)] = PIN.build_input(export, docs, entity, k, a.seed, graphs, roles)
        return inputs[(entity, k)]

    specs, nb_rows = [], []   # specs: one dict per job with the raw (not yet de-lexicalised) text
    for ent in a.ents.split(","):
        entity = PIN.find_pilot_entity(mm, ent)
        groups = PIN.neighbourhoods(export, entity)
        print(f"{ent}: entity {entity}, groups {[len(g) for g in groups]}")
        nb_rows += [(ent, entity, gi, c) for gi, g in enumerate(groups) for c in g]
        plan = job_plan(ent, len(groups))
        for gi, grp in enumerate(groups):
            outside, target = PIN.outside_context(export, groups, gi), PIN.nbhd_target(len(grp))
            carry = PIN.CARRY_PLACEHOLDER if gi else None
            for k in K_FALLBACK:   # k from the longest variant (e, seed 0); all variants keep it
                inp = inp_for(entity, k)
                n = PIN.est_tokens(PIN.render_v3(inp, export, docs, grp, outside, target, None, carry, True))
                if n + (CARRY_TOKENS if gi else 0) < TOKEN_LIMIT:
                    break
            for name, var, g, seed, rnd, src in (p for p in plan if p[2] == gi):
                _, _, has_carry, cue = VARIANTS[var]
                text = PIN.render_v3(inp, export, docs, grp, outside, target, order_seed(seed),
                                     PIN.CARRY_PLACEHOLDER if (has_carry and gi) else None, cue)
                exs = [(f"{c.cluster_id}:{var}s{seed}e{j}", c.cluster_id, mid)
                       for c in inp.clusters if c.cluster_id in grp for j, (_, mid) in enumerate(c.examples)]
                specs.append(dict(name=name, ent=ent, entity=entity, var=var, gi=gi, seed=seed, rnd=rnd, src=src,
                                  text=text, schema=PIN.schema_v3(inp, grp), exs=exs, k=k))

    mp = {}
    if any(s["var"] == "f" for s in specs):
        mp = DX.build_map(mm, texts=[s["text"] for s in specs if s["var"] == "f"])
    jobs, tok, ex_rows, stat_rows = [], {}, [], []
    for s in specs:
        text = DX.apply(s["text"], mp) if s["var"] == "f" else s["text"]
        name = s["name"]
        carry = bool(s["src"])
        (out / "prompts" / f"{name}{'.tmpl' if carry else ''}.txt").write_text(text, encoding="utf-8", newline="\n")
        (out / "prompts" / f"{name}.schema.json").write_text(json.dumps(s["schema"], indent=1), encoding="utf-8",
                                                            newline="\n")
        n = PIN.est_tokens(text) + (CARRY_TOKENS if carry else 0)
        tok[name] = n
        jobs.append({"job": name, "entity": s["entity"], "ent": s["ent"], "variant": s["var"],
                     "run_tag": f"s{s['seed']}", "kind": "entity", "stage": 1, "nbhd": s["gi"], "cluster_id": "",
                     "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
                     "max_tokens": max_tokens(n), "format": "v3", "round": s["rnd"], "carry_from": s["src"]})
        ex_rows.extend((ex, s["entity"], c, mid, name) for ex, c, mid in s["exs"])
        stat_rows.append(f"| {name} | {s['entity']} | {s['k']} | {len(text)} | {n} | "
                         f"{'OVER LIMIT' if n >= TOKEN_LIMIT else 'ok'} |")

    pd.DataFrame(nb_rows, columns=["ent", "entity", "nbhd", "cluster_id"]).to_csv(
        out / "neighbourhoods.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.DataFrame(ex_rows, columns=["ex_id", "entity", "cluster_id", "mention_id", "variant"]).to_csv(
        out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "delex_map.json").write_text(json.dumps(mp, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    (out / "manifest.json").write_text(json.dumps({"run": a.run, "seed": a.seed, "jobs": jobs}, indent=1),
                                       encoding="utf-8", newline="\n")
    md = [f"# wf_v3.3 pilot prompts (run `{a.run}`, seed {a.seed})", "",
          f"Tokens are estimated as chars / 3.5, plus {CARRY_TOKENS} for the carry block of carry jobs (their "
          f"`.txt` is written on Colab). k drops 8 -> 6 -> 5 when a nbhd prompt reaches {TOKEN_LIMIT}.", "",
          "| prompt | entity | k | chars | est. tokens | status |", "|---|---|---|---|---|---|", *stat_rows, "",
          "## Estimated prompt tokens per variant (entity jobs only; gate and split jobs are reused from v3.2)", "",
          "| entity | variant | calls | est. prompt tokens |", "|---|---|---|---|", *token_rows(jobs, tok), ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
