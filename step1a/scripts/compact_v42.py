"""wf_v4.2 compact A prompts (diary Nov 7 task 10): build them on dev50 / dev50b and measure them. No GPU, no LLM.

python scripts/compact_v42.py [--out results/wf_v42/compact] [--tokenizer meta-llama/Meta-Llama-3-8B-Instruct]

- Checks first that s1a/batch_v42.render_compact with every switch off gives the frozen A prompt (pilot_build_v37.a_prompts).
- Answer size: every saved A answer (dev50 A r1 / r2 / s2, dev50b A s0 / s1 / s2) rewritten in the compact format (C3:
  no evidence, placement codes) and counted; answer_tokens(n) = ceil(max tokens per cluster * MARGIN * n) + BASE.
- Per set, entity and order: the prompt in the model's chat template, counted with the tokenizer, for the full prompt, C1,
  C1+C2 and C1+C2+C3; then the C5 plan (one call, or neighbourhood parts) under the 7,500-token budget.
Writes <out>/prompts/*.txt + *.schema.json, manifest.json (format v2c, max_tokens = budget - prompt tokens), sizes.csv,
answer_sizes.csv and stats.md.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pilot_build_v32 import order_seed  # noqa: E402
from pilot_build_v37 import ORDERS, RunInput, a_prompts  # noqa: E402

from s1a import batch_v42 as C  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402

SETS = {"dev50": "results/graph_v22_dev50", "dev50b": "results/graph_v22_dev50b"}
ENTS = ("train", "hotel", "restaurant")
ANSWERS = {"dev50": ["results/loop1_v31/responses/{ent}_v2_r1.jsonl", "results/loop1_v31/responses/{ent}_v2_r2.jsonl",
                     "results/loop1_v36/colab/responses/{ent}_v2_s2.jsonl"],
           "dev50b": [f"results/loop1_v37/colab/responses/{{ent}}_a_v22d50b_s{s}.jsonl" for s in ORDERS]}
TOKENIZER = ("meta-llama/Meta-Llama-3-8B-Instruct", "8afb486c1db24fe5011ec46dfbe5b5dccdb575c2")
MARGIN, BASE = 1.25, 200
STEPS = {"full": dict(window=False, n_examples=None, compact_answer=False), "c1": dict(window=True, n_examples=None, compact_answer=False),
         "c12": dict(window=True, n_examples=C.N_EXAMPLES, compact_answer=False), "c123": {}}


def compact_answer(parsed, entity):
    """A saved v2 answer in the compact format (C3), as the model would write it."""
    return {"attributes": parsed.get("attributes", []),
            "clusters": [{"cluster_id": c["cluster_id"], "attribute": c["attribute"], "mixed": c["mixed"],
                          "placement": C.code_of(c["placement"])} for c in parsed.get("clusters", [])]}


def answer_sizes(count):
    rows = []
    for set_name, pats in ANSWERS.items():
        for ent in ENTS:
            for pat in pats:
                p = paths.ROOT / pat.format(ent=ent)
                row = json.loads(p.read_text(encoding="utf-8").splitlines()[-1])
                raw, parsed = row["raw"], row["parsed"]
                n = len(parsed["clusters"])
                comp = json.dumps(compact_answer(parsed, ""), ensure_ascii=False)
                rows.append({"set": set_name, "ent": ent, "file": p.name, "clusters": n, "full_tokens": count(raw, chat=False),
                             "compact_tokens": count(comp, chat=False)})
    df = pd.DataFrame(rows)
    df["compact_per_cluster"] = (df["compact_tokens"] / df["clusters"]).round(1)
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=paths.ROOT / "results" / "wf_v42" / "compact")
    ap.add_argument("--tokenizer", default=TOKENIZER[0])
    ap.add_argument("--revision", default=TOKENIZER[1])
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer, revision=a.revision)

    def count(text, chat=True):
        if chat:
            text = tok.apply_chat_template([{"role": "user", "content": text}], tokenize=False, add_generation_prompt=True)
        return len(tok(text, add_special_tokens=False).input_ids)

    ans = answer_sizes(count)
    per_cluster = float(ans["compact_per_cluster"].max())

    def answer_tokens(n):
        return math.ceil(per_cluster * MARGIN * n) + BASE

    out = a.out
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    sizes, jobs = [], []
    for set_name, run in SETS.items():
        ri = RunInput(run, 0)
        for ent in ENTS:
            entity, k, inp, texts = a_prompts(ri, ent)
            for s in ORDERS:   # the switches-off render is the frozen prompt
                if C.render_compact(inp, ri.export, ri.docs, order_seed(s), **STEPS["full"]) != texts[s]:
                    raise SystemExit(f"{set_name} {ent} s{s}: render_compact with the switches off differs from the frozen A prompt")
            n = len(inp.clusters)
            row = {"set": set_name, "ent": ent, "entity": entity, "clusters": n, "k": k}
            for step, sw in STEPS.items():
                row[f"prompt_{step}"] = count(C.render_compact(inp, ri.export, ri.docs, **sw))
            row["answer_est"] = answer_tokens(n)
            plan = C.plan_calls(inp, ri.export, ri.docs, count, answer_tokens)
            row["calls"] = len(plan)
            row["parts"] = " / ".join(str(len(g)) for g, _ in plan) if plan[0][0] else str(n)
            worst = 0
            for s in ORDERS:
                for g, part in plan:
                    text = C.render_compact(inp, ri.export, ri.docs, order_seed(s), group_ids=g, part=part)
                    pt = count(text)
                    worst = max(worst, pt + answer_tokens(len(g or inp.clusters)))
                    name = f"{ent}_ac_{set_name}_s{s}" + (f"_p{part[0]}" if part else "")
                    (out / "prompts" / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
                    (out / "prompts" / f"{name}.schema.json").write_text(json.dumps(C.schema_compact(inp, g), indent=1),
                                                                         encoding="utf-8", newline="\n")
                    jobs.append({"job": name, "ent": ent, "entity": entity, "family": "a_compact", "set": set_name,
                                 "format": C.FORMAT, "run_tag": f"s{s}", "part": part, "clusters": g or [c.cluster_id for c in inp.clusters],
                                 "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "prompt_tokens": pt,
                                 "max_tokens": C.BUDGET - pt})
            row["worst_total"] = worst
            sizes.append(row)
            print(f"{set_name} {ent}: {n} clusters, full {row['prompt_full']} -> compact {row['prompt_c123']} tokens, "
                  f"{row['calls']} call(s), worst prompt + answer {worst}", flush=True)
    df = pd.DataFrame(sizes)
    (out / "manifest.json").write_text(json.dumps({"tokenizer": [a.tokenizer, a.revision], "budget": C.BUDGET,
                                                   "answer_tokens": {"per_cluster": per_cluster, "margin": MARGIN, "base": BASE},
                                                   "jobs": jobs}, indent=1), encoding="utf-8", newline="\n")
    df.to_csv(out / "sizes.csv", index=False, lineterminator="\n")
    ans.to_csv(out / "answer_sizes.csv", index=False, lineterminator="\n")
    (out / "stats.md").write_text(stats_md(df, ans, per_cluster, a.tokenizer, len(jobs)), encoding="utf-8", newline="\n")
    print(f"{len(jobs)} jobs -> {out}")


def stats_md(df, ans, per_cluster, tokenizer, n_jobs):
    lines = [f"# Compact A prompts (wf_v4.2, C1-C3 + C5), tokens of {tokenizer}", "",
             f"Budget {C.BUDGET} tokens per call (prompt in the chat template + max answer). Answer estimate: "
             f"{per_cluster} tokens per cluster (the largest compact rewrite of a saved answer) x {MARGIN} + {BASE}.", "",
             "| set | entity | clusters | full | C1 | C1+C2 | C1+C2+C3 | change | answer est. | calls (parts) | worst total |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        ch = r.prompt_c123 / r.prompt_full - 1
        lines.append(f"| {r.set} | {r.ent} | {r.clusters} | {r.prompt_full:,} | {r.prompt_c1:,} | {r.prompt_c12:,} | {r.prompt_c123:,} | "
                     f"{ch:+.0%} | {r.answer_est:,} | {r.calls} ({r.parts}) | {r.worst_total:,} |")
    lines += ["", f"{n_jobs} compact A jobs (3 orders).", "", "## Saved A answers rewritten in the compact format", "",
              "| set | entity | file | clusters | full tokens | compact tokens | per cluster |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {r.set} | {r.ent} | {r.file} | {r.clusters} | {r.full_tokens:,} | {r.compact_tokens:,} | {r.compact_per_cluster} |"
              for r in ans.itertuples()]
    lines.append(f"\nTotal: full {ans.full_tokens.sum():,} -> compact {ans.compact_tokens.sum():,} tokens "
                 f"({ans.compact_tokens.sum() / ans.full_tokens.sum() - 1:+.0%}).")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
