"""wf_v4 task 0: build the schema-GT files from gt/schema_gt_v1.yaml.

python scripts/gt_build_v4.py [--gt gt/schema_gt_v1.yaml] [--out results/wf_v4/gt] [--handover handover]
Writes <out>/{schema_gt_v1.json, schema_gt_v1.sql, schema_gt_v1.canonical.json, schema_gt_v1.canonical_<alt>.json (7 alternative designs),
reachable_dev50.csv, reachable_dev50b.csv, check.txt, gt_questions.md}. Reachability = fallback of final_v39's found rule (see check.txt).
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_gt as G  # noqa: E402

GT_LEVELS = {"dev50": "results/loop1_v35/gt_levels.csv", "dev50b": "results/loop1_v37/dev50b/gt/gt_levels.csv"}
FINAL_ROWS = "results/loop1_v39/final/final_rows.csv"


def write(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def reach_lines(gt, set_name, rows, mapping, lev):
    """Check-file lines: counts per table and per entity, and the comparison with final_rows.csv found_*."""
    L = [f"## Reachable on {set_name} (fallback method, see the method note; label share >= {G.PURITY})", ""]
    ent_of = {t: v["entity"] for t, v in gt["tables"].items()}
    tot = Counter()
    for tn in gt["tables"]:
        rs = [r for r in rows if r["gt_table"] == tn and r["reachable"] != "added"]
        yes = sum(r["reachable"] == "yes" for r in rs)
        n_added = sum(r["reachable"] == "added" for r in rows if r["gt_table"] == tn)
        L.append(f"- {tn}: {yes}/{len(rs)} attribute columns reachable (+{n_added} added)")
        tot[ent_of[tn]] += yes
    L += ["", f"Per entity (sum of the tables): {dict(tot)}; all: {sum(tot.values())}/{sum(r['reachable'] != 'added' for r in rows)}"]
    fr = pd.read_csv(FINAL_ROWS)
    fr = fr[(fr["set"] == set_name) & (fr["row"] == "Final v3.9")].iloc[0]
    L.append(f"final_rows.csv (Final v3.9, rules v1.3): train {fr['found_train']}, hotel {fr['found_hotel']}, restaurant {fr['found_restaurant']}, "
             f"total {fr['found_total']}/{fr['gold_total']}.")
    mine = {e: tot[e] for e in G.ENTITIES}
    L.append(f"This method, same three entities (table counts of an entity summed): {mine}, total {sum(mine.values())}. "
             f"{'Counts match.' if sum(mine.values()) == fr['found_total'] else 'Counts do NOT match (see the method note).'}")
    mp = Counter(m["entity"] for m in mapping.values() if any(k / m["n_labelled"] >= G.PURITY for k in m["labels"].values() if m["n_labelled"]))
    L.append(f"Handover columns with a label on >= {G.PURITY} of their labelled mentions: {dict(mp)} of {len(mapping)}.")
    unknown = sorted({v for v in {l for v in set(lev) for l in G.split_labels(v)} if v and G.norm(v) not in G.gt_names(gt)})
    L.append(f"gt_L2 values that are not GT column names (after case/space normalisation): {unknown or 'none'}.")
    return L + [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", type=Path, default=Path("gt/schema_gt_v1.yaml"))
    ap.add_argument("--out", type=Path, default=Path("results/wf_v4/gt"))
    ap.add_argument("--handover", type=Path, default=Path("handover"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    gt = G.load_gt(a.gt)
    problems = G.check(gt)
    canon = G.to_canonical(gt)
    write(a.out / "schema_gt_v1.json", json.dumps(gt, indent=1, ensure_ascii=False))
    write(a.out / "schema_gt_v1.sql", G.to_sql(canon))
    write(a.out / "schema_gt_v1.canonical.json", json.dumps(canon, indent=1, ensure_ascii=False))
    for d in gt["alternatives"]:
        c = G.to_canonical(gt, d)
        write(a.out / f"schema_gt_v1.canonical_{d['name'].replace(':', '_')}.json", json.dumps(c, indent=1, ensure_ascii=False))
    lines = ["# schema GT v1 check", "", f"Designs: 1 main + {len(gt['alternatives'])} alternatives. Tables (main): {len(gt['tables'])}, "
             f"columns {sum(len(t['columns']) for t in gt['tables'].values())}, FKs {len(gt['foreign_keys'])}.", "",
             "## Problems", ""] + ([f"- {p}" for p in problems] or ["none"]) + [""]
    for s, p in GT_LEVELS.items():
        lev = G.read_gt_levels(p)
        mapping = G.map_handover(a.handover, s, lev, G.gt_names(gt))
        rows = G.reachable_rows(gt, mapping)
        write_csv(a.out / f"reachable_{s}.csv", rows, ["gt_table", "gt_column", "level", "reachable", "found_by"])
        lines += reach_lines(gt, s, rows, mapping, set(lev))
    lines += ["## Method note", "",
              "final_v39.py needs the v3.3/v3.2 run directories, Colab responses and models (it rebuilds every group), so it was not reused. "
              "Fallback used: a GT column is reachable when some handover column of the same entity has that gt_L2 label (multi-label, split on ';') "
              "on >= 0.6 of its LABELLED mentions (mentions with a non-empty gt_L2). It reproduces final_rows.csv found_* on dev50 "
              "and is one hotel column higher on dev50b; the exact rule (rules_groups.found, v1.3) counts mentions by label class.", ""]
    write(a.out / "check.txt", "\n".join(lines))
    write(a.out / "gt_questions.md", "# GT questions for the user\n\n" + "\n".join(f"- {q}" for q in G.questions(gt)) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
