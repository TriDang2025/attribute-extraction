"""wf_v4.3 U4: scoring and summary of the Step 4 v4.3 chains with the T7 scorers (scripts/score_v4.score_rows -> s1a/step4_score.score: table F1,
grouping F1, GT columns placed, PK right under rule (a) and (b), relationship recall / precision). The same code and GT as the files
results/wf_v4/colab/final/scores.csv and results/wf_v42/*/final/scores.csv (scripts/assemble_v4.py --score).

- score_chains(out): reads <out>/final/<chain>/canonical.json -> <out>/scores.csv (the scorer's columns, then input, seed, n_tables, repairs).
- summary(out): <out>/summary.md (counts and decimals per input and set, full GT; chains finished, tables per chain min-max, repairs per chain,
  call totals from log_v43.call_rows / call_totals) and <out>/calls.csv.
- figure_data(out): <out>/fig_schema_a_dev50_s0.json, the model schema of chain a_dev50_s0 next to the GT main design (tables, columns, keys, links).
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from . import batch_v4 as B
from . import step4_gt as G
from . import step4_score as S
from .log_v43 import CALL_FIELDS, call_rows, call_totals

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
FIG_CHAIN = "a_dev50_s0"
METRICS = (("gt_columns_placed", "GT columns placed"), ("pk_right", "PK right (a)"), ("pk_right_b", "PK right (b)"),
           ("rel_recall", "relationship recall"), ("rel_precision", "relationship precision"))
_JOB_SUFFIX = re.compile(r"_(p1|p2|r\d+_\d+|k\d+)$")


def load_gt(root=ROOT, gt_path=None):
    import score_v4 as SC
    return SC.load(gt_path or Path(root) / "gt" / "schema_gt_v1.yaml", Path(root) / "results" / "wf_v4" / "gt", B.SETS)


def score_chains(out, root=ROOT, gt_path=None):
    """Score every finished chain of <out>/final/status.json; writes <out>/scores.csv and returns its rows (reachable_only False and True)."""
    import score_v4 as SC
    out, root = Path(out), Path(root)
    gt = load_gt(root, gt_path)
    rows = []
    for r in B.read_json(out / "final" / "status.json"):
        if not r["ok"]:
            continue
        c = B.read_json(out / "final" / r["run"] / "canonical.json")
        extra = {"input": r["input"], "seed": r["seed"], "n_tables": len(c["tables"]), "repairs": r["repairs"]}
        rows += [{**x, **extra} for x in SC.score_rows(r["run"], c, gt, r["set"], root / "handover")]
    SC.write_rows(out / "scores.csv", rows)
    return rows


def _kn(rows, m):
    k, n = sum(int(r[f"{m}_k"]) for r in rows), sum(int(r[f"{m}_n"]) for r in rows)
    return f"{k}/{n} ({k / n:.3f})" if n else "n/a"


def _mean(rows, m):
    v = [float(r[m]) for r in rows if r.get(m) not in (None, "")]
    return f"{sum(v) / len(v):.3f}" if v else "n/a"


def _rng(xs):
    return f"{min(xs)}-{max(xs)}" if xs else "n/a"


def calls(out):
    """Call rows of the run in <out> (the fake run under <out>/fake is left out)."""
    return [r for r in call_rows(out) if not r["file"].startswith("fake/")]


def summary(out, scores=None):
    """Write <out>/summary.md and <out>/calls.csv; returns the text. `scores` = rows of score_chains (read from scores.csv when None)."""
    out = Path(out)
    status = B.read_json(out / "final" / "status.json")
    if scores is None:
        with open(out / "scores.csv", encoding="utf-8") as f:
            scores = list(csv.DictReader(f))
    full = [r for r in scores if str(r["reachable_only"]) == "False"]
    lines = ["# wf_v4.3 U4: Step 4 v4.3 (Llama-3.1-8B, small closed questions)", "",
             "Scores with the T7 scorers (full GT, not reachable-only; `scores.csv` has both). Counts are summed over the finished chains of each row, "
             "F1 values are means over them. Chains finished = chains whose p1 and p2 answers parsed and whose assembled schema passed the Step 4 "
             "validators.", "",
             "| input | set | chains finished | table F1 | grouping F1 | " + " | ".join(n for _, n in METRICS) + " | tables per chain | repairs per chain |",
             "|" + "---|" * (7 + len(METRICS))]
    inputs = list(dict.fromkeys(r["input"] for r in status))
    groups = [(i, s, [r for r in status if r["input"] == i and r["set"] == s]) for i in inputs for s in sorted({r["set"] for r in status if r["input"] == i})]
    groups += [(i, "all", [r for r in status if r["input"] == i]) for i in inputs]
    for inp, s, st in groups:
        ids = {r["run"] for r in st if r["ok"]}
        rs = [r for r in full if r["schema"] in ids]
        rep = [r["repairs"] for r in st]
        lines.append(f"| {inp} | {s} | {len(ids)}/{len(st)} ({len(ids) / len(st):.3f}) | {_mean(rs, 'table_f1')} | {_mean(rs, 'grouping_f1')} | "
                     + " | ".join(_kn(rs, m) for m, _ in METRICS)
                     + f" | {_rng([r['tables'] for r in st if r['ok']])} | {sum(rep) / len(rep):.1f} ({_rng(rep)}) |")
    bad = [r for r in status if not r["ok"]]
    lines += ["", f"Chains not finished: {len(bad)}" + "".join(f"\n- {r['run']}: {r['error']}" for r in bad), ""]
    if (out / "repairs.json").exists():
        rep = B.read_json(out / "repairs.json")
        lines += [f"Repairs (all chains): {rep['total']}", "", "| type | count |", "|---|---|"]
        lines += [f"| {k} | {n} |" for k, n in sorted(rep["counts"].items(), key=lambda kv: -kv[1])] + [""]
    rows = calls(out)
    tot = call_totals(rows)
    per = Counter(_JOB_SUFFIX.sub("", r["job"]) for r in rows)
    lines += ["Calls (log_v43.call_totals):",
              f"- {tot['calls']} calls ({tot['calls'] / max(len(status), 1):.1f} per chain), prompt tokens {tot['prompt_tokens']} (max per call "
              f"{max([r['prompt_tokens'] or 0 for r in rows], default=0)}), output tokens {tot['output_tokens']}, finish {tot['finish']}, retried {tot['retried']}",
              f"- calls per chain: {_rng(list(per.values()))}"]
    text = "\n".join(lines) + "\n"
    B.write(out / "summary.md", text)
    with open(out / "calls.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(CALL_FIELDS) + ["file"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return text


# ---------------------------------------------------------------- figure data
def _schema_view(c, mapping=None):
    """Tables of a canonical schema for drawing: columns with key marks (pk / fk -> table) and the GT attribute name each column maps to."""
    tables = []
    for t in c["tables"]:
        fk = {col: f["ref_table"] for f in t["foreign_keys"] for col in f["columns"]}
        cols = []
        for col in t["columns"]:
            m = (mapping or {}).get(col.get("source")) if col.get("source") else None
            cols.append({"name": col["name"], "type": col.get("type"), "source": col.get("source"), "new": bool(col.get("new")),
                         "gt_attribute": col.get("gt") or (m["gt"] if m else None), "pk": col["name"] in t["primary_key"],
                         "fk": fk.get(col["name"])})
        tables.append({"name": t["name"], "primary_key": list(t["primary_key"]), "columns": cols,
                       "foreign_keys": [{"columns": f["columns"], "ref_table": f["ref_table"], "ref_columns": f["ref_columns"]}
                                        for f in t["foreign_keys"]]})
    return {"tables": tables, "links": [{"from": r["from"], "to": r["to"], "kind": r["kind"]} for r in c["relationships"]]}


def figure_data(out, root=ROOT, gt_path=None, chain=FIG_CHAIN):
    """Write <out>/fig_schema_<chain>.json: {"chain", "set", "finished", "error", "model": schema view, "gt": view of the GT main design,
    "design", "match": {model table: GT table}} (scorer's best design and table match, full GT). An unfinished chain gives finished false
    and its error."""
    import score_v4 as SC
    out, root = Path(out), Path(root)
    set_name = chain.split("_")[1]
    gt = load_gt(root, gt_path)
    res = {"chain": chain, "set": set_name, "finished": False, "error": None, "model": None, "design": None, "match": None,
           "gt": _schema_view(G.to_canonical(gt))}
    row = next((r for r in B.read_json(out / "final" / "status.json") if r["run"] == chain), None)
    if row is None or not row["ok"]:
        res["error"] = "chain not in the run" if row is None else row["error"]
    else:
        c = B.read_json(out / "final" / chain / "canonical.json")
        mapping = S.map_columns(c, set_name, root / "handover", SC.GT_LEVELS[set_name], gt)
        sc = SC.score_rows(chain, c, gt, set_name, root / "handover")[0]
        res.update(finished=True, model=_schema_view(c, mapping), design=sc["design"],
                   match=dict(p.split("=", 1) for p in sc["match"].split(";")) if sc.get("match") else {})
    B.write_json(out / f"fig_schema_{chain}.json", res)
    return res
