"""wf_v3.8 Colab batch builder (contract WF_V38_BATCH.md): prompts, manifest, columns table, example table. No GPU, no LLM.

python scripts/batch_build_v38.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--out results/loop1_v38/colab] [--seed 0]
Columns of A s012 (3 orders + vote, Step 1a v2.2) on dev50 and dev50b, with the split pass and without it, loaded as
scripts/dashboard_v38.py loads them (stops when the counts are not 67 / 56 with and 32 / 35 without the split pass).
Jobs: dupcheck (set x config x entity), example and neighbour (every with-split column).
Writes <out>/{prompts/*.txt + *.schema.json, manifest.json, columns.csv, examples.csv, prompt_stats.md, prompt_samples.md}.
Needs results/graph_v22_dev50{,b}/spans/vectors.npz (not in git) for the neighbours; the run on Colab reads only the files above.
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dashboard_v38 as D  # noqa: E402
from s1a import batch_v38 as BT  # noqa: E402
from s1a import columns_v37 as CV  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from score_t14_v37 import GT  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402

LABEL = D.VOTE                      # "A s012"
CONFIGS = ("split", "nosplit")
EXPECT_COLUMNS = {("dev50", "split"): 67, ("dev50b", "split"): 56, ("dev50", "nosplit"): 32, ("dev50b", "nosplit"): 35}
V37 = (124, 565_921, 109_867)       # calls, prompt tokens, output tokens of the v3.7 batch (exact)
FAMILIES = ("dupcheck", "example", "neighbour")
FORMAT = {"dupcheck": "dupcheck", "example": "evidence", "neighbour": "evidence"}
COLUMN_COLS = ["set", "config", "ent", "column id", "name", "description", "members", "n mentions", "n dialogues",
               "distinct values", "value types"]
EXAMPLE_COLS = ["job", "example id", "mention_id", "cluster_id", "column", "value", "source column"]


def parser():
    ap = D.parser()
    ap.set_defaults(out=Path("results/loop1_v38/colab"))
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    return ap


class SetInput:
    """Docs, export and mention table of one set's run dir."""

    def __init__(self, set_name):
        run = paths.ROOT / D.SETS[set_name]["run"]
        self.docs, _, _ = MN.load_shared(run)
        self.export = MN.load(run / "spans")
        self.rows = self.export.mentions.set_index("mention_id")


def columns_of(pb):
    """{ent: (entity id, [column dicts])} of A s012 in the prepared bundle."""
    out = {}
    for ent, ed in pb["lev"].items():
        v = ed.variants[LABEL]
        gc = CV.group_columns(ed, LABEL)
        cols = BT.column_table(v.attrs, v.assign, ed.mentions, gc)
        if len(cols) != CV.n_columns(ed, LABEL):
            raise ValueError(f"{pb['set']} {ent}: {len(cols)} columns vs columns_v37 {CV.n_columns(ed, LABEL)}")
        out[ent] = (ed.entity, cols)
    return out


def example_lines(si, items):
    """Prompt lines of [(example id, mention_id)] (the line format of the v3.1 prompts)."""
    ci = PIN.ClusterInput("", 0, 0, False, items)
    return PIN._example_lines(si.export, si.docs, ci, True)


class Batch:
    """Collects jobs, files and tables."""

    def __init__(self, out):
        self.out = out
        (out / "prompts").mkdir(parents=True, exist_ok=True)
        self.jobs, self.examples, self.stats = [], [], []

    def emit(self, job, text, schema, est_out, **extra):
        if "multiwoz" in text.lower():
            raise ValueError(f"{job['job']}: dataset name in the prompt")
        name = job["job"]
        write(self.out / "prompts" / f"{name}.txt", text)
        write(self.out / "prompts" / f"{name}.schema.json", json.dumps(schema, indent=1))
        n = PIN.est_tokens(text)
        self.jobs.append({**job, "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
                          "max_tokens": BT.MAX_TOKENS[job["family"]], "format": FORMAT[job["family"]], "round": 0,
                          "carry_from": [], "run_tag": "v0", "est_prompt_tokens": n, **extra})
        self.stats.append((job["family"], name, len(text), n, est_out))


def build_dupcheck(batch, set_name, config, ent, entity, cols):
    ids = [c["cid"] for c in cols]
    batch.emit({"job": f"dupcheck_{set_name}_{config}_{ent}", "ent": ent, "entity": entity, "family": "dupcheck",
                "set": set_name, "config": config}, BT.render_dupcheck(cols), BT.schema_dupcheck(ids),
               BT.est_output_tokens("dupcheck", len(cols)), n_columns=len(cols))


def build_evidence(batch, si, set_name, ent, entity, cols, cent, seed):
    by_id = {c["cid"]: c for c in cols}
    for c in cols:
        if not c["mention_ids"]:
            continue
        own = [(mid, c["cid"]) for mid, _ in BT.sample_examples(c["pools"], BT.N_EXAMPLES, seed, f"col{c['cid']}")]
        neigh = BT.nearest(cent, c["cid"])
        cos = [round(float(cent[c["cid"]] @ cent[n]), 4) for n in neigh]
        for family, items, extra in (("example", own, {}),
                                     ("neighbour", BT.neighbour_examples(by_id, c["cid"], neigh, BT.N_PER_NEIGHBOUR, seed),
                                      {"neighbours": neigh, "neighbour_cos": cos})):
            if not items:
                continue
            numbered = [(i, mid) for i, (mid, _) in enumerate(items, 1)]
            name = f"{family}_{set_name}_{ent}_c{c['cid']:02d}"
            text = BT.render_evidence(c["name"], c["description"], example_lines(si, numbered))
            batch.emit({"job": name, "ent": ent, "entity": entity, "family": family, "set": set_name, "config": "split",
                        "column": c["cid"]}, text, BT.schema_evidence([i for i, _ in numbered]),
                       BT.est_output_tokens(family, len(items)), **extra)
            for (i, mid), (_, src) in zip(numbered, items):
                r = si.rows.loc[mid]
                batch.examples.append((name, i, mid, r["cluster_id"], c["cid"], r["text"], src))


def stats_md(batch, seed):
    """prompt_stats.md text and (calls, prompt, output) totals."""
    rows, tot = [], [0, 0, 0]
    for f in FAMILIES:
        s = [x for x in batch.stats if x[0] == f]
        vals = [len(s), sum(x[3] for x in s), sum(x[4] for x in s)]
        tot = [a + b for a, b in zip(tot, vals)]
        rows.append(f"| {f} | {vals[0]} | {vals[1]:,} | {vals[1] // max(vals[0], 1):,} | {max(x[3] for x in s):,} | {vals[2]:,} | "
                    f"{vals[2] // max(vals[0], 1):,} |")
    rows.append(f"| total | {tot[0]} | {tot[1]:,} | {tot[1] // tot[0]:,} | {max(x[3] for x in batch.stats):,} | {tot[2]:,} | "
                f"{tot[2] // tot[0]:,} |")
    big = max(batch.stats, key=lambda x: x[3])
    d = [t - o for t, o in zip(tot, V37)]
    md = [f"# wf_v3.8 Colab batch prompts (seed {seed})", "",
          "Tokens are estimated as chars / 3.5 (the notebook counts exact tokens and stops above 30,000). Output tokens are "
          "estimates: an evidence answer is about 12 tokens (8 + 12 per example); a duplicate check has no earlier answer to "
          "measure, flat 200 per call. max_tokens: dupcheck 1024, example and neighbour 512.", "",
          "| family | calls | est. prompt tokens | per call | largest prompt | est. output tokens | per call |",
          "|---|---|---|---|---|---|---|", *rows, "",
          f"v3.7 batch (exact): {V37[0]} calls, {V37[1]:,} prompt, {V37[2]:,} output tokens ({V37[1] // V37[0]:,} / "
          f"{V37[2] // V37[0]:,} per call). v3.8 change: {d[0]:+d} calls, {d[1]:+,} prompt, {d[2]:+,} output tokens (estimates vs exact). "
          f"Largest prompt: {big[1]}, {big[3]:,} est. tokens.", "",
          "| job | family | chars | est. prompt tokens | est. output tokens |", "|---|---|---|---|---|",
          *[f"| {n} | {f} | {c} | {t} | {o} |" for f, n, c, t, o in batch.stats], ""]
    return "\n".join(md), tot


def samples_md(batch):
    """prompt_samples.md: the dupcheck prompt of train dev50 (with split) and the first example prompt of train dev50."""
    def read(name):
        return (batch.out / "prompts" / f"{name}.txt").read_text(encoding="utf-8")
    ex = next(j["job"] for j in batch.jobs if j["family"] == "example" and j["set"] == "dev50" and j["ent"] == "train")
    return ("# wf_v3.8 prompt samples (verbatim)\n\n## dupcheck_dev50_split_train\n\n```text\n" + read("dupcheck_dev50_split_train")
            + f"```\n\n## {ex}\n\n```text\n" + read(ex) + "```\n")


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in GT.items()}
    pbs = D.load_both(a, gts)
    batch, col_rows = Batch(a.out), []
    for set_name in D.SETS:
        si = SetInput(set_name)
        for config in CONFIGS:
            per_ent = columns_of(pbs[(set_name, config)])
            n = sum(len(c) for _, c in per_ent.values())
            if n != EXPECT_COLUMNS[(set_name, config)]:
                raise SystemExit(f"STOP: {set_name} {config}: {n} columns, expected {EXPECT_COLUMNS[(set_name, config)]}")
            for ent, (entity, cols) in per_ent.items():
                col_rows += [(set_name, config, ent, c["cid"], c["name"], c["description"], len(c["members"]), c["n_mentions"],
                              c["n_dialogues"], c["n_values"], c["value_types"]) for c in cols]
                build_dupcheck(batch, set_name, config, ent, entity, cols)
                if config == "split":
                    cent = BT.centroids(cols, si.export.ids, si.export.x)
                    build_evidence(batch, si, set_name, ent, entity, cols, cent, a.seed)
        print(f"{set_name}: column counts ok", flush=True)
    write(a.out / "manifest.json", json.dumps({"seed": a.seed, "jobs": batch.jobs}, indent=1))
    write_csv(pd.DataFrame(col_rows, columns=COLUMN_COLS), a.out / "columns.csv")
    write_csv(pd.DataFrame(batch.examples, columns=EXAMPLE_COLS), a.out / "examples.csv")
    md, tot = stats_md(batch, a.seed)
    write(a.out / "prompt_stats.md", md)
    write(a.out / "prompt_samples.md", samples_md(batch))
    print(md.split("\n\n")[2])
    print({f: sum(1 for j in batch.jobs if j["family"] == f) for f in FAMILIES}, "totals", tot)
    if max(x[3] for x in batch.stats) >= 30_000:
        print("WARNING: a prompt is over 30,000 estimated tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
