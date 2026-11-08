"""wf_v4.1 task 4: dry run of the v4.1 Step-4 prompts (chain 4.1 -> 4.4) on input c1 (all GT attributes), dev50, seed 0.

DRY RUN, not a result (Gemini, user choice 2026-11-07). One stage at a time, each stage built from the answers of the stages before it:
  python scripts/step4_v41.py --build 1            -> results/wf_v41/step4_dryrun/{chains.json, manifest.json, prompts/}
  python scripts/dryrun_v41.py --dir results/wf_v41/step4_dryrun                       (stage 1 answers)
  python scripts/step4_v41.py --build 2 ; python scripts/dryrun_v41.py --dir results/wf_v41/step4_dryrun --manifest manifest_stage2.json
  ... the same for 3 and 4, then
  python scripts/step4_v41.py --report             -> final/<chain>/canonical.json, scores.csv, report.md (v4.1 vs the v0 Qwen run of the chain)
--fake runs all four stages with the wf_v4 fake model instead (code test; no Gemini).
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v4 as B  # noqa: E402
from s1a import batch_v4_fake as F  # noqa: E402

OUT = ROOT / "results" / "wf_v41" / "step4_dryrun"
def chains(inp="c1", sets=("dev50",), seed=0):
    return [{"id": B.chain_id(inp, s, seed), "kind": "main", "input": inp, "set": s, "seed": seed, "exclude": [], "prompt_version": "v41"}
            for s in sets]


CHAINS = chains()
V0_SCORES = ROOT / "results" / "wf_v4" / "colab" / "final" / "scores.csv"
SHOW = ["table_f1", "grouping_f1", "gt_columns_placed", "placement", "pk_right_b", "pk_right", "rel_recall", "rel_precision", "types_right",
        "unused_real", "duplicates"]


def build(out, k, chs=None):
    if k == 1:
        return B.build_chains_stage1(out, chs or CHAINS).save()
    return B.build_stage(out, k)


def shape(c):
    """Plain facts of a canonical schema: tables, links, unused."""
    links = len(c.get("relationships", [])) + sum(len(t.get("foreign_keys", [])) for t in c["tables"])
    return {"tables": len(c["tables"]), "links": links, "unused": len(c.get("unused", [])),
            "table_names": ", ".join(t["name"] for t in c["tables"])}


def fmt(row, m):
    if f"{m}_k" in row:
        return f"{row[f'{m}_k']}/{row[f'{m}_n']}"
    v = row.get(m, "")
    return f"{float(v):.3f}" if v not in ("", None) else "n/a"


def report(out):
    import score_v4 as SC
    status = [r for r in B.assemble_all(out, ROOT) if r["kind"] == "main"]
    gt = SC.load(ROOT / "gt" / "schema_gt_v1.yaml", ROOT / "results" / "wf_v4" / "gt", B.SETS)
    set_of = {c["id"]: c["set"] for c in B.read_json(out / "chains.json")}
    rows = []
    for r in status:
        if r["ok"]:
            rows += SC.score_rows(r["run"], B.read_json(out / "final" / r["run"] / "canonical.json"), gt, set_of[r["run"]], ROOT / "handover")
    SC.write_rows(out / "final" / "scores.csv", rows)
    v0 = {(x["schema"], x["reachable_only"]): x for x in csv.DictReader(open(V0_SCORES, encoding="utf-8"))}
    lines = [f"# wf_v4.1: v4.1 Step-4 prompts, dry run on {', '.join(set_of)}", "",
             "**DRY RUN, not a result.** v4.1 answers come from Gemini; the v0 column is the real Qwen2.5-32B run of the same chain "
             "(different models, so the comparison only shows whether the prompt changes work as intended).", ""]
    for r in status:
        lines.append(f"- chain {r['run']}: {'ok' if r['ok'] else 'stopped: ' + str(r['error'])}, repairs {r['repairs']}")
    for r in [x for x in status if x["ok"]]:
        new = shape(B.read_json(out / "final" / r["run"] / "canonical.json"))
        old = shape(B.read_json(ROOT / "results" / "wf_v4" / "colab" / "final" / r["run"] / "canonical.json"))
        lines += ["", "| | v0 (Qwen) | v4.1 (Gemini dry run) |", "|---|---|---|"]
        lines += [f"| {k} | {old[k]} | {new[k]} |" for k in ("tables", "links", "unused", "table_names")]
        new_row = next(x for x in rows if x["schema"] == r["run"] and str(x["reachable_only"]) == "False")
        old_row = v0.get((r["run"], "False"), {})
        lines += [f"| {m} (full GT) | {fmt(old_row, m) if old_row else 'n/a'} | {fmt(new_row, m)} |" for m in SHOW]
    B.write(out / "report.md", "\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=OUT)
    ap.add_argument("--build", type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--input", default="c1", choices=B.INPUTS, help="Step-4 input (diary Nov 7 task 2: a = real Step-3 handover)")
    ap.add_argument("--sets", default="dev50", help="comma list, e.g. dev50,dev50b")
    a = ap.parse_args()
    chs = chains(a.input, tuple(a.sets.split(",")))
    if a.fake:
        for k in (1, 2, 3, 4):
            F.run_jobs(a.dir, build(a.dir, k, chs))
        report(a.dir)
        return
    if a.build:
        jobs = build(a.dir, a.build, chs)
        print(f"stage {a.build}: {len(jobs)} jobs")
    if a.report:
        report(a.dir)


if __name__ == "__main__":
    main()
