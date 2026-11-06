"""wf_v4 task 2: the seven Step-4 inputs -> results/wf_v4/inputs/<set>/, token counts, scores of the no-LLM baselines d and f.

python scripts/inputs_v4.py [--sets dev50,dev50b] [--examples 5 --width 80]
Writes per set: {a,b,c1,c2}.columns.json (column dicts, input order), d.canonical.json, f.canonical.json,
e_v{0,1,2}.prompt.txt, dialogues_used.json; and results/wf_v4/inputs/token_counts.{csv,md} (est. tokens of the first prompt:
4.1 for a, b, c1, c2; the e prompt; the check is < 20,000) and results/wf_v4/scores/baselines_df.csv (d and f against the full and the
reachable GT). When a first prompt is over the limit, all inputs are rebuilt with 3 examples and width 50 (the same cut for all).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

import score_v4 as SC  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402
from s1a.pilot_input import est_tokens  # noqa: E402

OUT = ROOT / "results" / "wf_v4"


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def build_set(set_name, gt, k, width):
    """{input name: columns / schema / prompt} of one set and its token rows."""
    mentions = I.load_mentions(set_name)
    cols_a = I.main_columns(I.load_handover(set_name), mentions, k, width)
    levels = G.read_gt_levels(ROOT / I.GT_LEVELS[set_name])
    reach = I.load_reachable_yes(set_name)
    c1 = I.gt_columns(gt, levels, mentions, k, width)
    return {"a": cols_a, "b": I.with_signals(cols_a, I.load_cards(set_name)), "c1": c1,
            "c2": I.gt_columns(gt, levels, mentions, k, width, reachable=reach)}


def token_rows(set_name, cols, e_prompts):
    rows = [{"set": set_name, "input": n, "columns": len(c), "est_tokens": est_tokens(I.first_prompt(c)[0])} for n, c in cols.items()]
    rows += [{"set": set_name, "input": f"e_{v}", "columns": "", "est_tokens": est_tokens(p)} for v, p in e_prompts.items()]
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", default="dev50,dev50b")
    ap.add_argument("--examples", type=int, default=I.N_EXAMPLES)
    ap.add_argument("--width", type=int, default=I.WIDTH)
    ap.add_argument("--gt", type=Path, default=ROOT / "gt" / "schema_gt_v1.yaml")
    a = ap.parse_args()
    sets = a.sets.split(",")
    gt = SC.load(a.gt, OUT / "gt", sets)
    k, width = a.examples, a.width
    for attempt in range(2):
        built = {s: build_set(s, gt, k, width) for s in sets}
        e_data = {}
        for s in sets:
            ids, texts = I.load_docs(s)
            e_data[s] = {v: I.fill_dialogues(texts, ids, v) for v in I.VERSIONS}
        rows = [r for s in sets for r in token_rows(s, built[s], {v: e_data[s][v][1] for v in I.VERSIONS})]
        over = [r for r in rows if r["est_tokens"] >= I.FIRST_LIMIT and not str(r["input"]).startswith("e_")]
        if not over or attempt:
            break
        print(f"over {I.FIRST_LIMIT}: {over}; rebuilding with 3 examples, width 50", flush=True)
        k, width = 3, 50
    score_rows = []
    for s in sets:
        d = OUT / "inputs" / s
        for name, cols in built[s].items():
            write_json(d / f"{name}.columns.json", cols)
        flat = I.flat_schema(built[s]["a"])
        write_json(d / "d.canonical.json", flat)
        sig = I.load_signals_schema(s)
        write_json(d / "f.canonical.json", sig)
        for v in I.VERSIONS:
            (d / f"e_{v}.prompt.txt").write_text(e_data[s][v][1], encoding="utf-8", newline="\n")
        write_json(d / "dialogues_used.json", {v: {"ids": e_data[s][v][0], "n": len(e_data[s][v][0]),
                                                  "est_tokens": est_tokens(e_data[s][v][1])} for v in I.VERSIONS})
        for tag, schema in (("d", flat), ("f", sig)):
            score_rows += SC.score_rows(f"{tag}_{s}", schema, gt, s, ROOT / "handover")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "inputs" / "token_counts.csv", index=False, lineterminator="\n")
    md = [f"# wf_v4 inputs: est. tokens of the first prompt (examples {k}, context width {width}; limit {I.FIRST_LIMIT:,})", "",
          "| set | input | columns | est. tokens |", "|---|---|---|---|",
          *[f"| {r['set']} | {r['input']} | {r['columns']} | {r['est_tokens']:,} |" for r in rows], ""]
    (OUT / "inputs" / "token_counts.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    SC.write_rows(OUT / "scores" / "baselines_df.csv", score_rows)
    print("\n".join(md))
    print("scores ->", OUT / "scores" / "baselines_df.csv")


if __name__ == "__main__":
    main()
