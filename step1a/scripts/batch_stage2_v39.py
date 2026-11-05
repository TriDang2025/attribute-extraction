"""wf_v3.9 Colab batch, stage 2 builder (contract WF_V39_BATCH.md). Runs inside the notebook after the reconcile responses.

python scripts/batch_stage2_v39.py [--dir results/loop1_v39/colab] [--allow-missing]
Reads <dir>/{manifest.json, columns.json, responses/reconcile_*.jsonl}. For every set x entity x candidate order it takes the
answers of the reconcile jobs, applies the joins with s1a/batch_v39.apply_reconcile (role pairs blocked, "none" keeps the part)
and builds the v3.8 duplicate check on the reconciled columns: 3 entities x 2 sets x 2 orders = 12 jobs.
Writes <dir>/{prompts/dupcheck_<set>_rc<order>_<ent>.txt + .schema.json, manifest_stage2.json, reconciled_columns.json,
reconcile_joins.csv, stage2_stats.md}. Stops when a reconcile response is missing (--allow-missing: that part stays).
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import batch_v38 as BT  # noqa: E402
from s1a import batch_v39 as B9  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402

JOIN_COLS = ["set", "ent", "order", "part id", "column", "from column", "to column", "status", "reason", "same_as"]


def last_row(path):
    """Last JSON row of a response file, or None when the file is missing or empty."""
    p = Path(path)
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    return rows[-1] if rows else None


def write(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=Path("results/loop1_v39/colab"))
    ap.add_argument("--allow-missing", action="store_true")
    a = ap.parse_args()
    manifest = json.loads((a.dir / "manifest.json").read_text(encoding="utf-8"))
    tables = json.loads((a.dir / "columns.json").read_text(encoding="utf-8"))
    rc_jobs = [j for j in manifest["jobs"] if j["family"] == "reconcile"]
    rows = {j["job"]: last_row(a.dir / "responses" / f"{j['job']}.jsonl") for j in rc_jobs}
    missing = [n for n, r in rows.items() if r is None]
    if missing and not a.allow_missing:
        sys.exit(f"STOP: {len(missing)} reconcile responses missing, e.g. {missing[:3]}")
    jobs, joins, reconciled, stats = [], [], {}, []
    for set_name, ents in tables.items():
        for ent, t in ents.items():
            cols, by_id = t["columns"], {c["cid"]: c for c in t["columns"]}
            for order in sorted({j["order_seed"] for j in rc_jobs}):
                mine = {j["pid"]: j for j in rc_jobs if (j["set"], j["ent"], j["order_seed"]) == (set_name, ent, order)}
                choices, answers = {}, {}
                for pid, j in mine.items():
                    r = rows[j["job"]]
                    choices[pid] = B9.choice_from_response(r["parsed"], r["errors"], j["candidates"]) if r else None
                    answers[pid] = r["parsed"].get("reason", "") if r and not r["errors"] else "(no valid response)"
                new, report = B9.apply_reconcile(cols, t["parts"], choices)
                for p, rep in zip(t["parts"], report):
                    to = by_id.get(rep["to"])
                    joins.append([set_name, ent, order, p["pid"], p["name"], p["cid"], to["name"] if to else "", rep["status"],
                                  answers[p["pid"]], (rows[mine[p["pid"]]["job"]] or {}).get("parsed", {}).get("same_as", "")])
                stats += [(set_name, order, r["status"]) for r in report]
                name = f"dupcheck_{set_name}_rc{order}_{ent}"
                text = BT.render_dupcheck(new)
                (a.dir / "prompts" / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
                write(a.dir / "prompts" / f"{name}.schema.json", json.dumps(BT.schema_dupcheck([c["cid"] for c in new]), indent=1))
                jobs.append({"job": name, "ent": ent, "entity": t["entity"], "family": "dupcheck_rc", "set": set_name,
                             "order_seed": order, "format": "dupcheck", "run_tag": f"rc{order}", "stage": 2, "round": 0,
                             "carry_from": [], "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
                             "max_tokens": B9.MAX_TOKENS["dupcheck"], "n_columns": len(new),
                             "est_prompt_tokens": PIN.est_tokens(text)})
                reconciled.setdefault(set_name, {}).setdefault(ent, {})[str(order)] = {"columns": new, "report": report}
    write(a.dir / "manifest_stage2.json", json.dumps({"jobs": jobs}, indent=1))
    write(a.dir / "reconciled_columns.json", json.dumps(reconciled, indent=1))
    with (a.dir / "reconcile_joins.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(JOIN_COLS)
        w.writerows(joins)
    cnt = Counter(stats)
    lines = ["# wf_v3.9 stage 2: joins applied", "", "| set | order | joined | none | blocked | invalid |", "|---|---|---|---|---|---|",
             *[f"| {s} | {o} | " + " | ".join(str(cnt[(s, o, k)]) for k in ("joined", "none", "blocked", "invalid")) + " |"
               for s in tables for o in sorted({j["order_seed"] for j in rc_jobs})], "",
             f"Duplicate checks: {len(jobs)}, estimated prompt tokens {sum(j['est_prompt_tokens'] for j in jobs):,}, largest "
             f"{max(j['est_prompt_tokens'] for j in jobs):,}. Reconcile responses missing: {len(missing)}.", ""]
    write(a.dir / "stage2_stats.md", "\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
