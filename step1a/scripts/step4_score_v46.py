"""wf_v4.6 Y3 / Y8: score the Step 4 chains (seed 0) of the v4.6 runs, with the v4.5 W2 seed-0 chain as the dev50 baseline.

python scripts/step4_score_v46.py  -> results/wf_v46/step4/{scores.csv, step4.md}
Rows: chain x GT view (full GT; Y1 rule = step4_gt.reachable_by_annotations). Mapping: step4_gt.map_handover over every entity file of the
run's score map (wf_v4.6 Y1 fix). Also tables per chain, Step 4 calls, prompt / output tokens and the largest prompt (log_v44 call rows).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import score_v4 as SCR  # noqa: E402
from s1a import log_v44 as LOG  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_score as S  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402

Y3 = ROOT / "results" / "wf_v46" / "y3"
OUT = ROOT / "results" / "wf_v46" / "step4"
CHAINS = [  # (label, dev set, run name, step 4 folder)
    ("v4.5 keyword names", "dev50", "c_n50", ROOT / "results" / "wf_v45" / "w2" / "n50" / "step4"),
    ("v4.6 LLM names", "dev50", "c_n50", Y3 / "dev50" / "step4"),
    ("v4.6 LLM names, p2 batches of 20", "dev50", "c_n50", Y3 / "dev50" / "step4_p2b20"),
    ("v4.6 LLM names", "dev50b", "c_n50b", Y3 / "dev50b" / "step4"),
    ("v4.6 LLM names, p2 batches of 20", "dev50b", "c_n50b", Y3 / "dev50b" / "step4_p2b20"),
]
METRICS = ("table_f1", "grouping_f1", "gt_columns_placed", "pk_right", "pk_right_b")


def score_chain(gt, label, dev, run, folder):
    chain = f"a_llama44_{run}_s0"
    c = json.loads((folder / "final" / chain / "canonical.json").read_text(encoding="utf-8"))
    full = G.map_handover(folder / "score_map" / "a_llama44", run, ROOT / SCR.GT_LEVELS[dev], G.gt_names(gt))
    srcs = {x["source"] for t in c["tables"] for x in t["columns"] if x.get("source")} | {u["source"] for u in c.get("unused", [])}
    mapping = {s: full.get(s) or {"gt": None, "purity": 0.0, "n": 0, "entity": s.split(":")[0]} for s in srcs}
    calls = [r for r in LOG.call_rows(folder) if str(r["job"]).startswith(chain)]
    base = {"label": label, "set": dev, "tables": len(c["tables"]), "table_names": " ".join(t["name"] for t in c["tables"]),
            "calls": len(calls), "prompt_tokens": sum(int(r["prompt_tokens"]) for r in calls),
            "output_tokens": sum(int(r["output_tokens"]) for r in calls), "max_prompt": max(int(r["prompt_tokens"]) for r in calls)}
    rows = []
    old = gt["reachable"].get(dev)
    for view, reach in (("full", None), ("Y1 rule", G.reachable_by_annotations(gt, dev))):
        gt["reachable"][dev] = reach
        rows.append({**base, "gt_view": view, **S.flat(S.score(c, gt, dev, reach is not None, mapping))})
    gt["reachable"][dev] = old
    return rows


def cell(r, k):
    if f"{k}_n" in r:
        n = int(r[f"{k}_n"])
        return f"{int(r[f'{k}_k'])}/{n} ({r[f'{k}_k'] / n:.3f})" if n else "n/a"
    return f"{r[k]:.3f}" if pd.notna(r[k]) else "n/a"


def main():
    gt = SC43.load_gt(ROOT)
    rows = [r for ch in CHAINS if (ch[3] / "final").exists() for r in score_chain(gt, *ch)]
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
    head = ["set", "run", "GT view", "tables", *METRICS, "calls", "prompt / output tokens", "largest prompt"]
    lines = ["# Step 4 (v4.3, seed 0) on the v4.6 runs", "", "| " + " | ".join(head) + " |", "|---" * len(head) + "|"]
    for r in df.to_dict("records"):
        lines.append(f"| {r['set']} | {r['label']} | {r['gt_view']} | {r['tables']} | " + " | ".join(cell(r, k) for k in METRICS)
                     + f" | {r['calls']} | {r['prompt_tokens']:,} / {r['output_tokens']:,} | {r['max_prompt']:,} |")
    lines += ["", "Tables per chain:", ""] + [f"- {r['set']} {r['label']}: {r['table_names']}" for r in df[df.gt_view == "full"].to_dict("records")]
    (OUT / "step4.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
