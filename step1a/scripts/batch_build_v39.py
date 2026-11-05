"""wf_v3.9 Colab batch, stage 1 builder (contract WF_V39_BATCH.md): prompts, manifest, tables. No GPU, no LLM.

python scripts/batch_build_v39.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--out results/loop1_v39/colab] [--seed 0]
Columns of A s012 with the split pass (Step 1a v2.2, dev50 and dev50b) as scripts/batch_build_v38.py loads them (stops when the
counts are not 67 / 56). Jobs:
- reconcile (T4): one per split-pass part of A s012 that has mentions x 2 candidate orders (seed 0, 1);
- a_cue (T8): A's v2 prompt + one cue line, 3 orders x 3 entities x 2 sets.
Stage 2 (scripts/batch_stage2_v39.py, on Colab after the reconcile responses) adds the 12 duplicate checks.
Writes <out>/{prompts/*.txt + *.schema.json, manifest.json (stage 1), columns.json (columns + parts, read by stage 2), parts.csv,
reconcile_examples.csv, examples.csv (A-cue examples, the v3.7 format), prompt_stats.md, prompt_samples.md}.
Needs results/graph_v22_dev50{,b}/spans/vectors.npz (not in git).
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dashboard_v38 as D  # noqa: E402
from batch_build_v38 import EXPECT_COLUMNS, SetInput, columns_of, example_lines  # noqa: E402
from pilot_build_v31 import TOKEN_LIMIT, max_tokens  # noqa: E402
from pilot_build_v36 import earlier_output  # noqa: E402
from pilot_build_v37 import ORDERS, RunInput, a_prompts  # noqa: E402
from score_t14_v37 import GT  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402

from s1a import batch_v38 as BT  # noqa: E402
from s1a import batch_v39 as B9  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

LABEL = D.VOTE                       # "A s012"
SEEDS = (0, 1)                       # reconcile candidate orders
RUN_KEY = {"dev50": "v22d50", "dev50b": "v22d50b"}
SPLIT_DIR = {"dev50": ("results/loop1_v31/responses", ""), "dev50b": ("results/loop1_v37/colab/responses", "_v22d50b")}
V36_RESPONSES = "results/loop1_v36/colab/responses"
EST_OUT_RECONCILE = 70               # tokens: a 25-word reason (~40) + the JSON frame and a column name (~30)
EXAMPLE_COLS = ["job", "example id", "mention_id", "cluster_id", "part", "value", "candidate order seed"]
ENT_RUN_COLS = ["ex_id", "entity", "cluster_id", "mention_id", "variant"]   # as results/loop1_v37/colab/examples.csv
FAMILIES = ("reconcile", "a_cue", "dupcheck_rc")


def parser():
    ap = D.parser()
    ap.set_defaults(out=Path("results/loop1_v39/colab"))
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    return ap


def split_roles(set_name, ent):
    """{(cluster id, raw part name): role} from the v3.1 split responses of the set (the part description)."""
    root, infix = SPLIT_DIR[set_name]
    res = PV.load_split_results(paths.ROOT / root).get((f"{ent}{infix}", "r1"), {})
    return {(cid, p["name"]): p.get("role", "") for cid, obj in res.items() for p in obj.get("parts") or []
            if isinstance(p, dict) and p.get("name")}


def ser_columns(cols):
    """JSON-able columns (value_types dropped: the reconciled columns do not carry it)."""
    return [{k: v for k, v in c.items() if k != "value_types"} for c in cols]


class Stage1:
    """Collects the jobs and their tables."""

    def __init__(self, out):
        self.out = out
        (out / "prompts").mkdir(parents=True, exist_ok=True)
        self.jobs, self.stats, self.examples, self.a_examples = [], [], [], []

    def emit(self, job, text, schema, est_out, max_tok, **extra):
        if "multiwoz" in text.lower():
            raise ValueError(f"{job['job']}: dataset name in the prompt")
        name = job["job"]
        write(self.out / "prompts" / f"{name}.txt", text)
        write(self.out / "prompts" / f"{name}.schema.json", json.dumps(schema, indent=1))
        n = PIN.est_tokens(text)
        self.jobs.append({"stage": 1, "round": 0, "carry_from": [], **job, "prompt": f"prompts/{name}.txt",
                          "schema": f"prompts/{name}.schema.json", "max_tokens": max_tok, "est_prompt_tokens": n, **extra})
        self.stats.append((job["family"], name, len(text), n, est_out))


def build_reconcile(st, si, set_name, ent, entity, cols, parts, cent, seed):
    by_id = {c["cid"]: c for c in cols}
    for p in parts:
        near = B9.nearest_columns(cent, BT.centroids([{"cid": 0, "mention_ids": p["mention_ids"]}], si.export.ids, si.export.x)[0],
                                  p["cid"])
        pool = [(key, items) for key, items in by_id[p["cid"]]["pools"] if key == p["key"]]
        picked = BT.sample_examples(pool, B9.N_PART_EXAMPLES, seed, f"part{p['pid']}")
        numbered = [(i, mid) for i, (mid, _) in enumerate(picked, 1)]
        lines = example_lines(si, numbered)
        for order in SEEDS:
            order_cids = B9.shuffled_order(near, order, f"{set_name}{ent}{p['pid']}")
            cands = [by_id[c] for c in order_cids]
            name = f"reconcile_{set_name}_{ent}_{p['pid'].replace('#', '-').replace('/', 'p')}_o{order}"
            st.emit({"job": name, "ent": ent, "entity": entity, "family": "reconcile", "set": set_name, "format": "reconcile",
                     "run_tag": f"o{order}", "pid": p["pid"], "column": p["cid"], "order_seed": order,
                     "candidates": [{"cid": c["cid"], "name": c["name"]} for c in cands]},
                    B9.render_reconcile(p, cands, lines), B9.schema_reconcile(p["pid"], [c["name"] for c in cands]),
                    EST_OUT_RECONCILE, B9.MAX_TOKENS["reconcile"])
            for i, mid in numbered:
                r = si.rows.loc[mid]
                st.examples.append((name, i, mid, r["cluster_id"], p["pid"], r["text"], order))


def build_a_cue(st, set_name, ent_outputs):
    ri = RunInput(D.SETS[set_name]["run"], 0)
    for ent in DB.ENTS:
        entity, k, inp, texts = a_prompts(ri, ent)
        exs = [(ex, c.cluster_id, mid) for c in inp.clusters for ex, mid in c.examples]
        schema = B9.schema_a_cue(PIN.schema_v2(inp))
        for s in ORDERS:
            name = f"{ent}_acue_{set_name}_s{s}"
            text = B9.render_a_cue(texts[s])
            st.emit({"job": name, "ent": ent, "entity": entity, "family": "a_cue", "set": set_name, "variant": "v2",
                     "run_tag": f"s{s}", "kind": "entity", "nbhd": None, "cluster_id": "", "format": "v2", "run": RUN_KEY[set_name],
                     "k": k}, text, schema, ent_outputs[ent], max_tokens(PIN.est_tokens(text)))
            st.a_examples.extend((ex, entity, c, mid, name) for ex, c, mid in exs)


def stats_md(st, rc_stats, seed):
    """prompt_stats.md text and per-family (calls, prompt, output) totals; rc_stats = stage 2 estimates."""
    allrows = st.stats + rc_stats
    rows, tot = [], [0, 0, 0]
    for f in FAMILIES:
        s = [x for x in allrows if x[0] == f]
        vals = [len(s), sum(x[3] for x in s), sum(x[4] for x in s)]
        tot = [a + b for a, b in zip(tot, vals)]
        rows.append(f"| {f}{' (stage 2, estimate)' if f == 'dupcheck_rc' else ''} | {vals[0]} | {vals[1]:,} | "
                    f"{vals[1] // max(vals[0], 1):,} | {max(x[3] for x in s):,} | {vals[2]:,} | {vals[2] // max(vals[0], 1):,} |")
    rows.append(f"| total | {tot[0]} | {tot[1]:,} | {tot[1] // tot[0]:,} | {max(x[3] for x in allrows):,} | {tot[2]:,} | "
                f"{tot[2] // tot[0]:,} |")
    big = max(allrows, key=lambda x: x[3])
    md = [f"# wf_v3.9 Colab batch prompts (seed {seed})", "",
          "Tokens are estimated as chars / 3.5 (the notebook counts exact tokens and stops above 30,000), the method of "
          "v3.8. Output tokens are estimates: reconcile flat 70 per call (a reason of at most 25 words plus the JSON frame); "
          "a_cue = the v3.6 A answer of the same entity (`<ent>_v2_s2`, exact tokens of its response); a duplicate check "
          "has no earlier answer to measure, flat 200 per call as in v3.8. The stage 2 duplicate checks do not exist yet: "
          "their prompt size is the v3.8 with-split duplicate check of the same entity and set (every part kept, so an "
          "upper bound; a join only shortens the list). max_tokens: reconcile 256, a_cue per A job as v3.7, dupcheck 1024.", "",
          "| family | calls | est. prompt tokens | per call | largest prompt | est. output tokens | per call |",
          "|---|---|---|---|---|---|---|", *rows, "",
          f"Largest prompt: {big[1]}, {big[3]:,} est. tokens (limit 30,000).", "",
          "| job | family | chars | est. prompt tokens | est. output tokens |", "|---|---|---|---|---|",
          *[f"| {n} | {f} | {c} | {t} | {o} |" for f, n, c, t, o in allrows], ""]
    return "\n".join(md), tot


def samples_md(st):
    """prompt_samples.md: one prompt per family (the dupcheck sample is the stage 2 shape, every part kept)."""
    def read(name):
        return (st.out / "prompts" / f"{name}.txt").read_text(encoding="utf-8")
    rc = next(j["job"] for j in st.jobs if j["family"] == "reconcile" and j["set"] == "dev50b" and j["ent"] == "hotel")
    ac = next(j["job"] for j in st.jobs if j["family"] == "a_cue" and j["set"] == "dev50" and j["ent"] == "train")
    return (f"# wf_v3.9 prompt samples (verbatim)\n\n## {rc}\n\n```text\n{read(rc)}```\n\n## {ac} (first 2,600 chars of the "
            f"instruction part, then the rest is as the v3.7 A prompt)\n\n```text\n{read(ac)[:2600]}\n...```\n\n"
            f"## dupcheck on reconciled columns (stage 2; shape shown on the unchanged dev50 train columns)\n\n```text\n"
            f"{st.dup_sample}```\n")


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in GT.items()}
    st, tables, part_rows, rc_stats = Stage1(a.out), {}, [], []
    a_out = {e: earlier_output(paths.ROOT / V36_RESPONSES / f"{e}_v2_s2.jsonl") for e in DB.ENTS}
    st.dup_sample = ""
    for set_name in D.SETS:
        pb = DB.prepare(set_name, D.load_v22(a, set_name), gts[set_name])
        per_ent = columns_of(pb)
        n = sum(len(c) for _, c in per_ent.values())
        if n != EXPECT_COLUMNS[(set_name, "split")]:
            raise SystemExit(f"STOP: {set_name}: {n} columns, expected {EXPECT_COLUMNS[(set_name, 'split')]}")
        si = SetInput(set_name)
        for ent, (entity, cols) in per_ent.items():
            attrs = pb["lev"][ent].variants[LABEL].attrs.to_dict("records")
            parts = B9.part_records(cols, attrs, split_roles(set_name, ent))
            cent = BT.centroids(cols, si.export.ids, si.export.x)
            tables.setdefault(set_name, {})[ent] = {"entity": entity, "columns": ser_columns(cols), "parts": parts}
            part_rows += [(set_name, ent, p["pid"], p["name"], p["description"], p["cid"], len(p["mention_ids"])) for p in parts]
            build_reconcile(st, si, set_name, ent, entity, cols, parts, cent, a.seed)
            text = BT.render_dupcheck(cols)
            if not st.dup_sample:
                st.dup_sample = text
            rc_stats += [("dupcheck_rc", f"dupcheck_{set_name}_rc{o}_{ent}", len(text), PIN.est_tokens(text),
                          BT.est_output_tokens("dupcheck", len(cols))) for o in SEEDS]
        print(f"{set_name}: column counts ok", flush=True)
        build_a_cue(st, set_name, a_out)
    write(a.out / "manifest.json", json.dumps({"seed": a.seed, "jobs": st.jobs}, indent=1))
    write(a.out / "columns.json", json.dumps(tables, indent=1))
    write_csv(pd.DataFrame(part_rows, columns=["set", "ent", "part id", "column", "description", "column id", "n mentions"]),
              a.out / "parts.csv")
    write_csv(pd.DataFrame(st.examples, columns=EXAMPLE_COLS), a.out / "reconcile_examples.csv")
    write_csv(pd.DataFrame(st.a_examples, columns=ENT_RUN_COLS), a.out / "examples.csv")
    md, tot = stats_md(st, rc_stats, a.seed)
    write(a.out / "prompt_stats.md", md)
    write(a.out / "prompt_samples.md", samples_md(st))
    print(md.split("\n\n")[2])
    print({f: sum(1 for j in st.jobs if j["family"] == f) for f in FAMILIES[:2]}, "totals incl. stage 2", tot)
    if max(x[3] for x in st.stats + rc_stats) >= TOKEN_LIMIT:
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
