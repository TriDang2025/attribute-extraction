"""wf_v5.0 G3 (S6): replay the "no joins" post-step (s1a/nojoin_v50.py) on the cached wf_v4.6 Y3 final columns, dev50 (design) then
dev50b (check, unchanged). CPU only.

python scripts/g3_nojoin_v50.py  -> results/wf_v50/g3/<set>/final_columns.json (unjoin on; Step 4 input for G5)
                                    results/wf_v50/g3/{g3.md, g3.csv, columns_<set>.csv}
Found = scorer found rule (mainclaim_v41.found_in_groups) on the loop-1 groups of the scored entities. Found L2 (v4.9 -> v5.0) = the v4.9
set (loop 1 + 2, human check) minus loop-1 span finds that no-joins loses, plus new loop-1 span finds (a lost one is counted lost even
if loop 2 might still credit it: conservative).
Column kinds (gold used only to score): gold = majority gt_L2 label is a gold attribute of the entity and no bigger column of the entity
has it; dup = a bigger column already has that label; other = majority label empty or not a gold attribute (noise / new).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v49 as M49  # noqa: E402
from s1a import mainclaim_v41 as MC  # noqa: E402
from s1a import nojoin_v50 as NJ  # noqa: E402
from s1a import step4_gt as SG  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402

OUT = ROOT / "results" / "wf_v50" / "g3"
SETS = ("dev50", "dev50b")


def load(set_name):
    mt = pd.read_csv(ROOT / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
    mt["mention_id"] = mt["mention_id"].astype(int)
    mt = mt.set_index("mention_id")
    gt = pd.read_csv(ROOT / I.GT_LEVELS[set_name], keep_default_na=False)
    labels = {int(i): [x for x in SG.split_labels(v) if x] for i, v in zip(gt["mention_id"], gt["gt_L2"])}
    emap = {k: (v["stage1"], v["gt_entity"], v["share"]) for k, v in
            json.loads((ROOT / "results" / "wf_v48" / "w1" / set_name / "entity_map.json").read_text(encoding="utf-8")).items()}
    step3 = ROOT / "results" / "wf_v46" / "y3" / set_name / "step3"
    final = json.loads((step3 / "scores" / "final_columns.json").read_text(encoding="utf-8"))[M46.RUN_OF[set_name]]
    return mt, labels, emap, final, step3


def score(final, emap, mt, labels, gold_by_ent):
    """(found set, column rows) of the scored entities."""
    ho = M46.handover(final, emap)
    tot = MC.entity_totals(ho, mt, labels)
    cluster_of = mt["cluster_id"].to_dict()
    found, rows = set(), []
    for ent, doc in ho.items():
        groups = []
        cols = []
        for c in doc["columns"]:
            gs = [[labels.get(i, []) for i in g] for g in MC.rebuild_groups(c, cluster_of)]
            groups += gs
            lab, share = MC.top_label([ls for g in gs for ls in g])
            cols.append({"entity": ent, "cid": c["id"], "name": c["name"], "n": len(c["mention_ids"]), "label": lab, "share": round(share, 2)})
        found |= MC.found_in_groups(groups, tot[ent], set(gold_by_ent.get(ent, [])))
        seen = set()
        for r in sorted(cols, key=lambda r: -r["n"]):
            gold = r["label"] in gold_by_ent.get(ent, [])
            r["kind"] = ("dup" if r["label"] in seen else "gold") if gold else "other"
            seen.add(r["label"])
            rows.append(r)
    return found, rows


def run_set(set_name):
    mt, labels, emap, final, step3 = load(set_name)
    v49, gold = M49.found_v49(set_name)
    gold_by_ent = {}
    for a, e in gold.items():
        gold_by_ent.setdefault(e, []).append(a)
    names = NJ.premerge_names(step3, M46.RUN_OF[set_name])
    cluster_of = mt["cluster_id"].to_dict()
    after = {k: NJ.unjoin(cols, cluster_of, names) for k, cols in final.items()}
    d = OUT / set_name
    d.mkdir(parents=True, exist_ok=True)
    (d / "final_columns.json").write_text(json.dumps({M46.RUN_OF[set_name]: after}, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8", newline="\n")
    f0, c0 = score(final, emap, mt, labels, gold_by_ent)
    f1, c1 = score(after, emap, mt, labels, gold_by_ent)
    l2_after = (v49["loop2"] - (f0 - f1)) | (f1 - f0)
    cols = pd.DataFrame([{**r, "variant": "v4.9"} for r in c0] + [{**r, "variant": "no joins"} for r in c1])
    cols.to_csv(OUT / f"columns_{set_name}.csv", index=False, encoding="utf-8", lineterminator="\n")
    kinds = {v: g["kind"].value_counts().to_dict() for v, g in cols.groupby("variant")}
    row = {"set": set_name, "gold_n": len(gold),
           "found_span_loop1": f"{len(f0)} -> {len(f1)}", "found_L2": f"{len(v49['loop2'])} -> {len(l2_after)}",
           "gained": "; ".join(sorted(f1 - f0)), "lost": "; ".join(sorted(f0 - f1))}
    for k in ("gold", "dup", "other"):
        row[f"cols_{k}"] = f"{kinds['v4.9'].get(k, 0)} -> {kinds['no joins'].get(k, 0)}"
    row["cols_total"] = f"{len(c0)} -> {len(c1)}"
    row["new_wrong_cols"] = (kinds["no joins"].get("dup", 0) + kinds["no joins"].get("other", 0)) - \
        (kinds["v4.9"].get("dup", 0) + kinds["v4.9"].get("other", 0))
    return row


def main():
    df = pd.DataFrame([run_set(s) for s in SETS])
    df.to_csv(OUT / "g3.csv", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / "g3.md").write_text("# wf_v5.0 G3: no-joins post-step (S6), replay on cached outputs\n\n" + df.to_markdown(index=False) + "\n",
                               encoding="utf-8", newline="\n")
    print(df.T.to_string())


if __name__ == "__main__":
    main()
