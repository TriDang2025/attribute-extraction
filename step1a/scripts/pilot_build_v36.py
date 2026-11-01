"""wf_v3.6 Colab batch: A s2, AE, F2 (fixed delex) plus the v3.5 oracle and g jobs (contract: GT_V36_CONTRACT.md, W1).

python scripts/pilot_build_v36.py [--run results/graph_v22_dev50] [--ents train,hotel,restaurant]
                                  [--out results/loop1_v36/colab] [--seed 0]
  -> <out>/{prompts/*.txt + *.schema.json (+ *.tmpl.txt for carry jobs), neighbourhoods.csv, examples.csv,
            delex_map.json, manifest.json, prompt_stats.md}
Jobs (manifest format of v3.5, `family` per job):
- a_s2     <ent>_v2_s2        A (format v2, v3.1 prompt) in a third order: render_v2(order_seed=2).
- ae       <ent>_ae_s{0,1,2}  A plus the noise rule of E (INSTRUCTION_V2_AE), orders None / 1 / 2.
- f2       <ent>_f2_nbhd<g>_s0  E (cue text, role-aware examples, carry-over) seed 0 on de-lexicalised prompts; the map has
           only real entity names (delex.build_map_v2). Carry jobs have a `.tmpl.txt`; `pilot_combine.fill_carry` fills them.
- oracle / g  copied from results/loop1_v35/colab (6 + 21 jobs, prompt and schema byte for byte).
The A prompt is built as pilot_build_v31 does; the builder checks that order_seed None / 1 reproduce the v3.1
`<ent>_v2.txt` / `<ent>_v2_r2.txt` (LF text) and prints the result. Reads <run>/{docs.jsonl, spans/*}. No encoder, no LLM.
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
from pilot_build_v31 import K_FALLBACK, SHUFFLE_SEED, TOKEN_LIMIT, max_tokens  # noqa: E402
from pilot_build_v32 import order_seed  # noqa: E402
from pilot_build_v33 import CARRY_TOKENS  # noqa: E402
from pilot_build_v35 import lf  # noqa: E402

A_SEED = 2                  # the new A order
AE_SEEDS = (0, 1, 2)
FAMILIES = ("a_s2", "ae", "f2", "oracle", "g")
REUSED = ("oracle", "g")
OLD_BATCH = (28, 158886, 45943)   # calls, est. prompt tokens, est. output tokens of the v3.5 batch
DB_ZIP = paths.ROOT.parent / "chunking" / "data" / "MULTIWOZ2.4.zip"


def f2_plan(ent, n_groups):
    """[(job name, group, round, carry_from)] of F2 for one entity: seed 0, groups 0..n-1; the job of group g > 0 has
    round g and carries the attributes of the jobs of groups 0..g-1 (as the v3.3 f jobs)."""
    names = [f"{ent}_f2_nbhd{g}_s0" for g in range(n_groups)]
    return [(names[g], g, g, names[:g]) for g in range(n_groups)]


def v31_check(text, v31_dir, name):
    """'identical' / 'DIFFERENT' / 'missing' for `text` against the v3.1 prompt file `name` (LF text)."""
    p = Path(v31_dir) / "prompts" / name
    if not p.exists():
        return "missing"
    return "identical" if lf(p.read_bytes()).decode("utf-8") == text else "DIFFERENT"


def earlier_output(path):
    """Output tokens of the last row of an earlier response file (output_tokens, else raw chars / 3.5); 0 if missing."""
    p = Path(path)
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    return (rows[-1].get("output_tokens") or PIN.est_tokens(rows[-1].get("raw") or "")) if rows else 0


def old_stats(path, names):
    """{job: (est prompt tokens, est output tokens)} from the table of a v3.5 prompt_stats.md, for the jobs in `names`."""
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) == 7 and c[0] in names:
            out[c[0]] = (int(c[4]), int(c[5]))
    return out


def reuse_v35(src, out):
    """Copy the oracle and g jobs of the v3.5 batch (prompt + schema files as LF bytes). Returns (manifest rows,
    neighbourhood rows, example rows, {job: (prompt, output) estimates})."""
    src = Path(src)
    rows = [j for j in json.loads((src / "manifest.json").read_text(encoding="utf-8"))["jobs"]
            if j.get("family") in REUSED]
    for j in rows:
        for key in ("prompt", "schema"):
            (out / j[key]).write_bytes(lf((src / j[key]).read_bytes()))
    names = {j["job"] for j in rows}
    nb = pd.read_csv(src / "neighbourhoods.csv", keep_default_na=False)
    ex = pd.read_csv(src / "examples.csv", keep_default_na=False)
    return rows, nb, ex[ex["variant"].isin(names)], old_stats(src / "prompt_stats.md", names)


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


def map_report(mp, old_map_path):
    """Markdown lines on the F2 map: size, stop list, the old v3.3 F map for comparison."""
    lines = [f"- F2 map: {len(mp)} strings (database names of hotel, restaurant, attraction, train stations, minus "
             f"STOP, plus TR ids in the prompts).",
             f"- STOP ({len(DX.STOP)}): {', '.join(sorted(DX.STOP))}."]
    p = Path(old_map_path)
    if p.exists():
        old = json.loads(p.read_text(encoding="utf-8"))
        gone = sorted(set(old) - set(mp))
        lines += [f"- v3.3 F map: {len(old)} strings; {len(set(old) & set(mp))} also in F2; {len(gone)} only in F "
                  f"(span strings, generic words, misspellings): {', '.join(gone)}."]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v36/colab")
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    ap.add_argument("--v31", default="results/loop1_v31")
    ap.add_argument("--v33", default="../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33")
    ap.add_argument("--v35", default="results/loop1_v35/colab")
    ap.add_argument("--db-zip", default=str(DB_ZIP))
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    v31, v33 = paths.ROOT / a.v31, (paths.ROOT / a.v33).resolve()
    docs, _, _ = MN.load_shared(run)
    export = MN.load(run / "spans")
    pkl = run / "spans" / "graphs.pkl"
    graphs = GR.load(pkl) if pkl.exists() else None
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    mm = export.mentions
    roles = {int(i): (w if isinstance(w, str) else "") for i, w in zip(mm["mention_id"], mm["left_word"])}

    inputs = {}

    def inp_for(entity, k, with_roles):
        if (entity, k, with_roles) not in inputs:
            inputs[(entity, k, with_roles)] = PIN.build_input(export, docs, entity, k, a.seed, graphs,
                                                              roles if with_roles else None)
        return inputs[(entity, k, with_roles)]

    specs, nb_rows, checks = [], [], []   # specs: one dict per new job with the raw (not yet de-lexicalised) text
    for ent in a.ents.split(","):
        entity = PIN.find_pilot_entity(mm, ent)
        # A and AE: the input of pilot_build_v31 (k from the v2 prompt, no roles)
        for k in K_FALLBACK:
            inp = inp_for(entity, k, False)
            text0 = PIN.render_v2(inp, export, docs, "v2")
            if PIN.est_tokens(text0) < TOKEN_LIMIT:
                break
        exs = [(ex, c.cluster_id, mid) for c in inp.clusters for ex, mid in c.examples]
        checks.append((ent, "A order None vs v2.txt", v31_check(text0, v31, f"{ent}_v2.txt")))
        checks.append((ent, f"A order {SHUFFLE_SEED} vs v2_r2.txt",
                       v31_check(PIN.render_v2(inp, export, docs, "v2", order_seed=SHUFFLE_SEED), v31,
                                 f"{ent}_v2_r2.txt")))
        schema = PIN.schema_v2(inp)
        specs.append(dict(family="a_s2", name=f"{ent}_v2_s{A_SEED}", ent=ent, entity=entity, var="v2",
                          tag=f"s{A_SEED}", text=PIN.render_v2(inp, export, docs, "v2", order_seed=A_SEED),
                          schema=schema, exs=exs, k=k, fmt="v2", rnd=0, src=[], gi=None,
                          out=earlier_output(v31 / "responses" / f"{ent}_v2_r1.jsonl")))
        for seed in AE_SEEDS:
            specs.append(dict(family="ae", name=f"{ent}_ae_s{seed}", ent=ent, entity=entity, var="ae",
                              tag=f"s{seed}", text=PIN.render_v2(inp, export, docs, "v2", order_seed=order_seed(seed),
                                                                 noise_rule=True),
                              schema=schema, exs=exs, k=k, fmt="v2", rnd=0, src=[], gi=None,
                              out=earlier_output(v31 / "responses" / f"{ent}_v2_r1.jsonl")))
        # F2: the v3.3 F prompts (E, seed 0, carry-over), de-lexicalised below
        groups = PIN.neighbourhoods(export, entity)
        print(f"{ent}: entity {entity}, groups {[len(g) for g in groups]}")
        nb_rows += [("f2", ent, entity, gi, c) for gi, g in enumerate(groups) for c in g]
        for name, gi, rnd, src in f2_plan(ent, len(groups)):
            grp = groups[gi]
            outside, target = PIN.outside_context(export, groups, gi), PIN.nbhd_target(len(grp))
            carry = PIN.CARRY_PLACEHOLDER if gi else None
            for k in K_FALLBACK:
                inp = inp_for(entity, k, True)
                n = PIN.est_tokens(PIN.render_v3(inp, export, docs, grp, outside, target, None, carry, True))
                if n + (CARRY_TOKENS if gi else 0) < TOKEN_LIMIT:
                    break
            text = PIN.render_v3(inp, export, docs, grp, outside, target, None, carry, True)
            specs.append(dict(family="f2", name=name, ent=ent, entity=entity, var="f2", tag="s0", text=text,
                              schema=PIN.schema_v3(inp, grp), k=k, fmt="v3", rnd=rnd, src=src, gi=gi,
                              exs=[(f"{c.cluster_id}:f2s0e{j}", c.cluster_id, mid)
                                   for c in inp.clusters if c.cluster_id in grp for j, (_, mid) in enumerate(c.examples)],
                              out=earlier_output(v33 / "responses" / f"{ent}_f_nbhd{gi}_s0.jsonl")))

    mp = DX.build_map_v2(DX.db_names(a.db_zip), [s["text"] for s in specs if s["family"] == "f2"])
    jobs, ex_rows, stat_rows, est = [], [], [], []
    for s in specs:
        text = DX.apply(s["text"], mp) if s["family"] == "f2" else s["text"]
        name, carry = s["name"], bool(s["src"])
        (out / "prompts" / f"{name}{'.tmpl' if carry else ''}.txt").write_text(text, encoding="utf-8", newline="\n")
        (out / "prompts" / f"{name}.schema.json").write_text(json.dumps(s["schema"], indent=1), encoding="utf-8",
                                                            newline="\n")
        n = PIN.est_tokens(text) + (CARRY_TOKENS if carry else 0)
        jobs.append({"job": name, "entity": s["entity"], "ent": s["ent"], "variant": s["var"], "run_tag": s["tag"],
                     "kind": "entity", "stage": 1, "nbhd": s["gi"], "cluster_id": "", "prompt": f"prompts/{name}.txt",
                     "schema": f"prompts/{name}.schema.json", "max_tokens": max_tokens(n), "format": s["fmt"],
                     "round": s["rnd"], "carry_from": s["src"], "family": s["family"]})
        ex_rows.extend((ex, s["entity"], c, mid, name) for ex, c, mid in s["exs"])
        est.append((s["family"], n, s["out"]))
        stat_rows.append(f"| {name} | {s['entity']} | {s['k']} | {len(text)} | {n} | {int(s['out'])} | "
                         f"{'OVER LIMIT' if n >= TOKEN_LIMIT else 'ok'} |")

    old_jobs, old_nb, old_ex, old_est = reuse_v35(paths.ROOT / a.v35, out)
    for j in old_jobs:
        p, o = old_est[j["job"]]
        est.append((j["family"], p, o))
        stat_rows.append(f"| {j['job']} | {j['entity']} | reused | - | {p} | {o} | ok |")
    pd.concat([old_nb, pd.DataFrame(nb_rows, columns=old_nb.columns)]).to_csv(
        out / "neighbourhoods.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.concat([old_ex, pd.DataFrame(ex_rows, columns=old_ex.columns)]).to_csv(
        out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "delex_map.json").write_text(json.dumps(mp, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    (out / "manifest.json").write_text(json.dumps({"run": a.run, "seed": a.seed, "jobs": jobs + old_jobs}, indent=1),
                                       encoding="utf-8", newline="\n")

    fam, tot = family_rows(est)
    d = [t - o for t, o in zip(tot, OLD_BATCH)]
    md = [f"# wf_v3.6 Colab batch prompts (run `{a.run}`, seed {a.seed})", "",
          f"Tokens are estimated as chars / 3.5, plus {CARRY_TOKENS} for the carry block of F2 carry jobs (their `.txt` is "
          f"written on Colab). k drops 8 -> 6 -> 5 when a prompt reaches {TOKEN_LIMIT}. Output tokens: A and AE = the "
          f"v3.1 A answer of the entity (`<ent>_v2_r1`); F2 = the v3.3 F answer of the same job; oracle and g = the "
          f"v3.5 estimates (copied).", "",
          "| prompt | entity | k | chars | est. prompt tokens | est. output tokens | status |",
          "|---|---|---|---|---|---|---|", *stat_rows, "",
          "## Estimated calls and tokens per family", "",
          "| family | calls | est. prompt tokens | est. output tokens |", "|---|---|---|---|", *fam, "",
          f"v3.5 batch: {OLD_BATCH[0]} calls, {OLD_BATCH[1]} prompt, {OLD_BATCH[2]} output tokens. Change: "
          f"{d[0]:+d} calls, {d[1]:+d} prompt, {d[2]:+d} output tokens (the T8 rerun is dropped).", "",
          "## F2 de-lexicalisation map", "", *map_report(mp, v33 / "delex_map.json"), "",
          "## Byte check of A against v3.1 (LF text)", "", "| entity | check | result |", "|---|---|---|",
          *[f"| {e} | {c} | {r} |" for e, c, r in checks], ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)
    if any(r != "identical" for _, _, r in checks):
        print("WARNING: an A prompt differs from its v3.1 file", file=sys.stderr)


if __name__ == "__main__":
    main()
