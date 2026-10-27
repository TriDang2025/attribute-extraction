"""T5 input: the Step-3 pilot prompts for the predicted entity whose majority gold entity is --entity-gold.

python scripts/pilot_build.py [--run results/graph_v22_dev50] [--entity-gold train] [--k 8] [--seed 0]
                              [--out results/loop1_check/pilot_train]
  -> <out>/{prompts/full.txt, prompts/nocontext.txt, prompts/nohints.txt, examples.csv, prompt_stats.md}
Reads <run>/{docs.jsonl, spans/*} (graphs.pkl when present). No encoder, no LLM.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import graph as GR  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402

MAX_TOKENS = 30_000


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--entity-gold", default="train")
    ap.add_argument("--k", type=int, default=PIN.K_EXAMPLES)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/loop1_check/pilot_train")
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    docs, _, _ = MN.load_shared(run)
    export = MN.load(run / "spans")
    pkl = run / "spans" / "graphs.pkl"
    graphs = GR.load(pkl) if pkl.exists() else None
    entity = PIN.find_pilot_entity(export.mentions, a.entity_gold)
    inp = PIN.build_input(export, docs, entity, a.k, a.seed, graphs)
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    PIN.examples_table(inp).to_csv(out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    rows, warn = [], False
    for v in PIN.VARIANTS:
        text = PIN.render(inp, export, docs, v)
        (out / "prompts" / f"{v}.txt").write_text(text, encoding="utf-8", newline="\n")
        tok = PIN.est_tokens(text)
        warn |= tok >= MAX_TOKENS
        rows.append(f"| {v} | {len(text)} | {tok} | {'OVER LIMIT' if tok >= MAX_TOKENS else 'ok'} |")
    n_ex = sum(len(c.examples) for c in inp.clusters)
    md = [f"# Pilot prompts: entity {entity} (majority gold {a.entity_gold})", "",
          f"Run `{a.run}`, k {a.k}, seed {a.seed}: {len(inp.clusters)} clusters, {n_ex} examples, "
          f"{sum(c.low_conf for c in inp.clusters)} low-confidence clusters.", "",
          f"Tokens are estimated as chars / 3.5; the limit is {MAX_TOKENS}.", "",
          "| variant | chars | est. tokens | status |", "|---|---|---|---|", *rows, ""]
    (out / "prompt_stats.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md))
    if warn:
        print(f"WARNING: a prompt is over {MAX_TOKENS} estimated tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
