"""wf_v4: assemble the finished chains of a Colab batch into canonical JSON, SQL and operations (also callable on Colab).

python scripts/assemble_v4.py [--dir results/wf_v4/colab] [--score]
Writes <dir>/final/<run>/{canonical.json, schema.sql, operations.json} for every finished chain and (e) call, <dir>/final/status.json, and for
the placement chains canonical_<j>.json per step. --score (laptop; needs gt/, handover/, results/wf_v4/gt, the gt_levels files) also writes
<dir>/final/scores.csv (every canonical schema against the full and the reachable GT) and <dir>/final/placement_vs_gt.csv.
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v4 as B  # noqa: E402


def score_runs(out, status):
    import score_v4 as SC
    from s1a import step4_inputs as I
    from s1a import step4_score as S
    gt = SC.load(ROOT / "gt" / "schema_gt_v1.yaml", ROOT / "results" / "wf_v4" / "gt", B.SETS)
    rows = []
    for r in status:
        if r["ok"] and r["kind"] in ("main", "base", "e"):
            set_name = r["run"].split("_")[1] if r["kind"] == "e" else next(c["set"] for c in B.all_chains(out) if c["id"] == r["run"])
            rows += SC.score_rows(r["run"], B.read_json(out / "final" / r["run"] / "canonical.json"), gt, set_name, ROOT / "handover")
    SC.write_rows(out / "final" / "scores.csv", rows)
    plc = B.read_json(out / "placement.json")
    prow = []
    for mode in B.MODES:
        run = next((r for r in status if r["run"] == f"place_{mode}"), None)
        if not run:
            continue
        schemas, answers, err = B.place_state(out, mode, len(plc["steps"]))
        first, last = {}, {}
        for j, st in enumerate(plc["steps"]):
            first.setdefault(st["attr"], j)
            last[st["attr"]] = j
        done = [i for i in range(len(plc["attributes"])) if i in last and last[i] < len(schemas)]
        res = S.placement_vs_gt([schemas[last[i]] for i in done], [answers[first[i]] for i in done], [plc["attributes"][i] for i in done], gt,
                                plc["set"], ROOT / "handover", ROOT / I.GT_LEVELS[plc["set"]])
        prow += [{"mode": mode, **r} for r in res]
    SC.write_rows(out / "final" / "placement_vs_gt.csv", prow)
    return rows, prow


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=ROOT / "results" / "wf_v4" / "colab")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    status = B.assemble_all(a.dir, ROOT)
    bad = [r for r in status if not r["ok"]]
    print(f"{len(status)} runs, {len(status) - len(bad)} assembled, {len(bad)} not:", *[f"{r['run']}: {r['error']}" for r in bad[:5]], sep="\n  ")
    if a.score:
        rows, prow = score_runs(a.dir, status)
        print(len(rows), "score rows,", len(prow), "placement rows")


if __name__ == "__main__":
    main()
