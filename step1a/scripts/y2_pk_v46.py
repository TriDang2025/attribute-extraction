"""wf_v4.6 Y2 (diary Nov 16): why PK rule (a) falls from 6/11 (frozen v4.3 a_llama43, dev50) to 0/9 (wf_v4.5 one command, dev50).
Table by table: matched GT table, the model's PK, what the scorer credits it as, and whether the GT PK column is already in the table.

python scripts/y2_pk_v46.py  -> results/wf_v46/y2/pk.md   (no LLM, no models)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import score_v4 as SCR  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_score as S  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402
from s1a import step4_v44 as V  # noqa: E402

SET = "dev50"
RUNS = [("frozen v4.3", ROOT / "results" / "wf_v43" / "u4", "a_llama43", f"a_llama43_{SET}_s{i}") for i in range(3)] + \
       [("one command v4.5", ROOT / "results" / "wf_v45" / "w2" / "n50" / "step4_as_dev50", "a_llama44", f"a_llama44_c_n50_s{i}") for i in range(3)]
OUT = ROOT / "results" / "wf_v46" / "y2"


def pk_rows(gt, label, out, inp, run):
    """One row per matched output table of the chain (best design, full GT), replaying score_design's match + credit_new."""
    c = json.loads((out / "final" / run / "canonical.json").read_text(encoding="utf-8"))
    mapping = S.map_columns(c, SET, V.score_map_dir(out, inp, ROOT), ROOT / SCR.GT_LEVELS[SET], gt)
    res = S.score(c, gt, SET, False, mapping)
    v = S.view(next(d for d in G.all_designs(gt) if d["name"] == res["design"]), None)
    o = S.resolve(c, G.gt_names(gt), mapping)
    match = S.match_tables(o, v)
    S.credit_new(o, v, match)
    rows = []
    for t in o["tables"]:
        if t["name"] not in match or not t["pk"]:
            continue
        g = match[t["name"]]
        cols = {x["name"]: x for x in t["cols"]}
        natural = {x["gt"] for x in t["cols"] if x["gt"] and not x["credited"]}
        rows.append({"run": label, "chain": run, "design": res["design"], "table": t["name"], "gt_table": g, "gt_pk": ", ".join(v["tables"][g]["pk"]),
                     "model_pk": ", ".join(t["pk"]), "credited_as": ", ".join(str(cols[k]["gt"]) for k in t["pk"]),
                     "pk_new": all(cols[k]["new"] for k in t["pk"]),
                     "gt_pk_in_table": all(p in natural for p in v["tables"][g]["pk"]),
                     "rule_a": {cols[k]["gt"] for k in t["pk"]} == set(v["tables"][g]["pk"])})
    return rows


def main():
    gt = SC43.load_gt(ROOT)
    rows = [r for args in RUNS for r in pk_rows(gt, *args)]
    head = ["run", "chain", "table", "gt_table", "gt_pk", "model_pk", "credited_as", "gt_pk_in_table", "rule_a"]
    lines = ["# Y2: PK rule (a), frozen v4.3 vs one command v4.5 (dev50, full GT, best design per chain)", "",
             "| " + " | ".join(head) + " |", "|---" * len(head) + "|"]
    lines += ["| " + " | ".join(str(r[h]) for h in head) + " |" for r in rows]
    for label in dict.fromkeys(r["run"] for r in rows):
        sub = [r for r in rows if r["run"] == label]
        k = sum(r["rule_a"] for r in sub)
        new = sum(r["pk_new"] for r in sub)
        lines += ["", f"- {label}: rule (a) {k}/{len(sub)}; model PKs that are new id columns: {new}/{len(sub)}; "
                      f"tables that already hold the GT PK column: {sum(r['gt_pk_in_table'] for r in sub)}/{len(sub)}"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pk.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
