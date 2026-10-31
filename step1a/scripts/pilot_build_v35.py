"""wf_v3.5 Colab batch: prompts for T8, T14 and T18-T20 (contract: PILOT_V35_BATCH.md).

python scripts/pilot_build_v35.py [--run results/graph_v22_dev50] [--ents train,hotel,restaurant]
                                  [--out results/loop1_v35/colab] [--seed 0]
  -> <out>/{prompts/*.txt + *.schema.json, neighbourhoods.csv, examples.csv, manifest.json, prompt_stats.md}
     results/loop1_v35/oracle_clusters.csv
Jobs:
- T8   restaurant_v2_r2_rerun: the v3.1 job restaurant_v2_r2, same prompt and schema (copied byte for byte).
- T14  <ent>_oracle_nbhd<g>_s<seed>: v3.2 C prompts on the cluster table in which every two-role cluster is split by gold
       role (<cid>.a / <cid>.b); only entities that have a two-role cluster.
- T18-T20  <ent>_g_nbhd<g>_s<seed>: v3.2 C prompts with the role_examples instruction (T18) and role-aware examples
       (T19), seeds 0/1/2, every entity. The reconcile prompt and the merge check of T20 are code
       (pilot_input.render_reconcile_v35, role_guard); no reconcile job is built here.
Reads <run>/{docs.jsonl, spans/*}, results/loop1_v35/gt_levels.csv, results/loop1_v31 and loop1_v32. No encoder, no LLM.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import graph as GR  # noqa: E402
from s1a import llm_cache as LC  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import oracle_v35 as OR  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from pilot_build_v31 import K_FALLBACK, TOKEN_LIMIT, max_tokens  # noqa: E402
from pilot_build_v32 import order_seed  # noqa: E402

SEEDS = (0, 1, 2)
G_EXTRA_OUT = 40          # est. extra output tokens of one two-role cluster in g (the role_examples list)
T8_JOB = "restaurant_v2_r2_rerun"
FAMILIES = ("t8", "oracle", "g")


def job_name(ent, tag, gi, seed):
    return f"{ent}_{tag}_nbhd{gi}_s{seed}"


def entity_specs(export, docs, graphs, ent, entity, tag, ex_seed=0, roles=None, role_examples=False):
    """(specs, group rows) of the neighbourhood jobs of one entity, seeds 0/1/2, v3.2 settings (no carry, no cue rule).
    `roles` {mention_id: left word} turns on the role-aware example picker; `role_examples` the T18 instruction and
    schema field. Each spec: dict(name, ent, entity, tag, gi, seed, text, schema, exs, k, n_clusters)."""
    groups = PIN.neighbourhoods(export, entity)
    inputs, specs = {}, []
    for gi, grp in enumerate(groups):
        outside, target = PIN.outside_context(export, groups, gi), PIN.nbhd_target(len(grp))
        for k in K_FALLBACK:   # k from the seed-0 prompt; the other orders keep it
            if k not in inputs:
                inputs[k] = PIN.build_input(export, docs, entity, k, ex_seed, graphs, roles)
            inp = inputs[k]
            n = PIN.est_tokens(PIN.render_v3(inp, export, docs, grp, outside, target, role_examples=role_examples))
            if n < TOKEN_LIMIT:
                break
        exs = [(ex, c.cluster_id, mid) for c in inp.clusters if c.cluster_id in grp for ex, mid in c.examples]
        for seed in SEEDS:
            text = PIN.render_v3(inp, export, docs, grp, outside, target, order_seed(seed), role_examples=role_examples)
            specs.append(dict(name=job_name(ent, tag, gi, seed), ent=ent, entity=entity, tag=tag, gi=gi, seed=seed,
                              text=text, schema=PIN.schema_v3(inp, grp, role_examples), exs=exs, k=k,
                              n_clusters=len(grp)))
    return specs, [(ent, entity, gi, c) for gi, g in enumerate(groups) for c in g]


def out_rate(pairs):
    """Output tokens per cluster from [(n clusters, output tokens)] of earlier runs."""
    n = sum(p[0] for p in pairs)
    return sum(p[1] for p in pairs) / n if n else 0.0


def v32_rates(root):
    """{ent: output tokens per cluster} of the v3.2 C entity jobs (rows without token fields: raw chars / 3.5)."""
    d = Path(root)
    pairs = {}
    for j in json.loads((d / "manifest.json").read_text(encoding="utf-8")):
        f = d / "responses" / f"{j['job']}.jsonl"
        if j["kind"] != "entity" or not f.exists():
            continue
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
        if rows:
            ids = LC.schema_enum(json.loads((d / j["schema"]).read_text(encoding="utf-8")), "cluster_id") or []
            row = rows[-1]
            pairs.setdefault(j["ent"], []).append((len(ids), row.get("output_tokens") or PIN.est_tokens(row["raw"])))
    return {e: out_rate(p) for e, p in pairs.items()}


def lf(data):
    """bytes with CRLF turned into LF."""
    return data.replace(b"\r\n", b"\n")


def t8_job(src, out):
    """Copy the v3.1 job restaurant_v2_r2 (prompt and schema byte for byte); (manifest job, prompt text, est. output
    tokens of the earlier answer)."""
    old = next(j for j in json.loads((src / "manifest.json").read_text(encoding="utf-8")) if j["job"] == "restaurant_v2_r2")
    text = lf((src / old["prompt"]).read_bytes())   # a Windows checkout may hold CRLF; the run used LF
    (out / "prompts" / f"{T8_JOB}.txt").write_bytes(text)
    (out / "prompts" / f"{T8_JOB}.schema.json").write_bytes(lf((src / old["schema"]).read_bytes()))
    rows = [json.loads(x) for x in (src / "responses" / "restaurant_v2_r2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    job = {**old, "job": T8_JOB, "variant": "v2_rerun", "stage": 1, "nbhd": None, "round": 0, "carry_from": [],
           "prompt": f"prompts/{T8_JOB}.txt", "schema": f"prompts/{T8_JOB}.schema.json"}
    return job, text.decode("utf-8"), PIN.est_tokens(rows[-1]["raw"]) if rows else 0


def manifest_job(s, family):
    return {"job": s["name"], "entity": s["entity"], "ent": s["ent"], "variant": s["tag"], "run_tag": f"s{s['seed']}",
            "kind": "entity", "stage": 1, "nbhd": s["gi"], "cluster_id": "", "prompt": f"prompts/{s['name']}.txt",
            "schema": f"prompts/{s['name']}.schema.json", "max_tokens": max_tokens(PIN.est_tokens(s["text"])),
            "format": "v3", "round": 0, "carry_from": [], "family": family}


def family_rows(rows):
    """Markdown rows (family, calls, est. prompt tokens, est. output tokens) and the total row from
    [(family, est prompt, est output)]."""
    out, tot = [], [0, 0, 0]
    for f in FAMILIES:
        r = [x for x in rows if x[0] == f]
        if r:
            vals = [len(r), sum(x[1] for x in r), sum(int(x[2]) for x in r)]
            out.append(f"| {f} | {vals[0]} | {vals[1]} | {vals[2]} |")
            tot = [a + b for a, b in zip(tot, vals)]
    out.append(f"| total | {tot[0]} | {tot[1]} | {tot[2]} |")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v35/colab")
    ap.add_argument("--levels", default="results/loop1_v35/gt_levels.csv")
    ap.add_argument("--oracle-out", default="results/loop1_v35/oracle_clusters.csv")
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    docs, _, _ = MN.load_shared(run)
    export = MN.load(run / "spans")
    pkl = run / "spans" / "graphs.pkl"
    graphs = GR.load(pkl) if pkl.exists() else None
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    mm = export.mentions
    assert mm.index.is_unique
    lv = pd.read_csv(paths.ROOT / a.levels, keep_default_na=False)
    gold_l2 = mm["mention_id"].map(dict(zip(lv["mention_id"], lv["gt_L2"]))).fillna("")
    gold_role, two_role = OR.two_roles(mm, gold_l2)
    left = {int(i): (w if isinstance(w, str) else "") for i, w in zip(mm["mention_id"], mm["left_word"])}
    print(f"two-role clusters: {two_role}")

    # T14 oracle table
    new_ids = OR.split_ids(mm, gold_role, two_role)
    oexport = OR.oracle_export(export, new_ids)
    orows = OR.oracle_rows(mm, gold_role, new_ids)
    (paths.ROOT / a.oracle_out).parent.mkdir(parents=True, exist_ok=True)
    orows.to_csv(paths.ROOT / a.oracle_out, index=False, encoding="utf-8", lineterminator="\n")

    jobs, specs, nb_rows, est = [], [], [], []   # est: (family, est prompt tokens, est output tokens)
    rates = v32_rates(paths.ROOT / "results/loop1_v32")
    job8, text8, o8 = t8_job(paths.ROOT / "results/loop1_v31", out)
    p8 = PIN.est_tokens(text8)
    jobs.append({**job8, "family": "t8"})
    est.append(("t8", p8, o8))
    stat_rows = [f"| {T8_JOB} | {job8['entity']} | - | {len(text8)} | {p8} | {o8} | "
                 f"{'OVER LIMIT' if p8 >= TOKEN_LIMIT else 'ok'} |"]
    ex_rows, g_first = [], {}
    for ent in a.ents.split(","):
        entity = PIN.find_pilot_entity(mm, ent)
        mine = {c: p for c, p in two_role.items() if c.split("#")[0] == entity}
        todo = [("g", export, graphs, left, True)]
        if mine:
            todo.insert(0, ("oracle", oexport, None, None, False))
        for tag, ex_, gr_, roles_, rex in todo:
            sp, nb = entity_specs(ex_, docs, gr_, ent, entity, tag, a.seed, roles_, rex)
            print(f"{ent} {tag}: {len(sp)} jobs, groups {[s['n_clusters'] for s in sp if s['seed'] == 0]}")
            nb_rows += [(tag,) + r for r in nb]
            fam = tag
            for s in sp:
                n = PIN.est_tokens(s["text"])
                n_two = len({c for _, c, _ in s["exs"] if c in mine}) if tag == "g" else 0
                o = rates.get(ent, 0.0) * s["n_clusters"] + G_EXTRA_OUT * n_two * (tag == "g")
                est.append((fam, n, o))
                specs.append(s)
                jobs.append(manifest_job(s, fam))
                stat_rows.append(f"| {s['name']} | {entity} | {s['k']} | {len(s['text'])} | {n} | {int(o)} | "
                                 f"{'OVER LIMIT' if n >= TOKEN_LIMIT else 'ok'} |")
                ex_rows.extend((ex, entity, c, mid, s["name"]) for ex, c, mid in s["exs"])
                if tag == "g" and s["seed"] == 0:
                    for _, c, mid in s["exs"]:
                        g_first.setdefault(c, []).append(mid)
    for s in specs:
        (out / "prompts" / f"{s['name']}.txt").write_text(s["text"], encoding="utf-8", newline="\n")
        (out / "prompts" / f"{s['name']}.schema.json").write_text(json.dumps(s["schema"], indent=1), encoding="utf-8",
                                                                 newline="\n")
    pd.DataFrame(nb_rows, columns=["variant", "ent", "entity", "nbhd", "cluster_id"]).to_csv(
        out / "neighbourhoods.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.DataFrame(ex_rows, columns=["ex_id", "entity", "cluster_id", "mention_id", "variant"]).to_csv(
        out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "manifest.json").write_text(json.dumps({"run": a.run, "seed": a.seed, "jobs": jobs}, indent=1),
                                       encoding="utf-8", newline="\n")

    cov = OR.example_role_counts(mm, g_first, gold_role, two_role)
    cov_rows = [f"| {r.cluster_id} | {r.slot} | {r.shown} / {r.total} | {'ok' if r.shown >= 1 else 'MISSING'} |"
                for r in cov.itertuples()]
    md = [f"# wf_v3.5 Colab batch prompts (run `{a.run}`, seed {a.seed})", "",
          f"Tokens are estimated as chars / 3.5 (T8: its own prompt file); k drops 8 -> 6 -> 5 when a nbhd prompt reaches "
          f"{TOKEN_LIMIT}. Output tokens: v3.2 C tokens per cluster of the entity x clusters of the group, plus "
          f"{G_EXTRA_OUT} per two-role cluster in g; T8: its earlier answer, raw chars / 3.5.", "",
          "| prompt | entity | k | chars | est. prompt tokens | est. output tokens | status |",
          "|---|---|---|---|---|---|---|", *stat_rows, "",
          "## Estimated calls and tokens per family", "",
          "| family | calls | est. prompt tokens | est. output tokens |", "|---|---|---|---|", *family_rows(est), "",
          "## T19: examples shown per gold role of each two-role cluster (g prompts, shown / mentions with that role)", "",
          "| cluster | gold role | shown / total | status |", "|---|---|---|---|", *cov_rows, ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)
    if any("MISSING" in r for r in cov_rows):
        print("WARNING: a two-role cluster shows no example for one of its roles", file=sys.stderr)


if __name__ == "__main__":
    main()
