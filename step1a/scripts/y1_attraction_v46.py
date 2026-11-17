"""wf_v4.6 Y1 (diary Nov 16): are the predicted attraction entities really attractions, and how do the wf_v4.5 dev50 Step 4 chains score
with (a) the scorer reading every entity file of the score map and (b) the annotation-based reachable rule (step4_gt.reachable_by_annotations).

python scripts/y1_attraction_v46.py  -> results/wf_v46/y1/{mentions.md, scores.csv, y1.md}
No LLM, no models. Reads the wf_v4.5 W2 run (results/wf_v45/w2/n50) and graph_v22_c_n50 (same mentions as graph_v22_dev50).
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import score_v4 as SCR  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_score as S  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402
from s1a import step4_v44 as V  # noqa: E402

RUN = ROOT / "results" / "wf_v45" / "w2" / "n50"
GRAPH = ROOT / "results" / "graph_v22_c_n50"
OUT = ROOT / "results" / "wf_v46" / "y1"
SET = "dev50"
N_SHOW = 10
METRICS = ("table_recall", "table_precision", "table_f1", "grouping_f1", "gt_columns_placed", "pk_right", "pk_right_b")


def mention_sample(names):
    """Markdown: per predicted entity named attraction*, its GT entity mix and N_SHOW mentions (text, context, GT label)."""
    m = pd.read_csv(GRAPH / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
    lv = pd.read_csv(SCR.GT_LEVELS[SET] if Path(SCR.GT_LEVELS[SET]).is_absolute() else ROOT / SCR.GT_LEVELS[SET], dtype=str, keep_default_na=False)
    j = m.merge(lv[["mention_id", "gt_L2", "ent_L2"]], on="mention_id", how="left").fillna("")
    lines = ["# Y1: mentions of the predicted attraction entities (dev50)", ""]
    for e, name in names.items():
        if not name.startswith("attraction"):
            continue
        sub = j[j.entity == e]
        mix = sub.ent_L2.replace("", "(no GT label)").value_counts()
        lines += [f"## {name} ({e}): {len(sub)} mentions", "",
                  "GT entity of the mentions: " + ", ".join(f"{k} {v}/{len(sub)} ({v / len(sub):.3f})" for k, v in mix.items()), "",
                  "| # | dialogue | mention | GT label | context |", "|---|---|---|---|---|"]
        for i, r in enumerate(sub.sample(min(N_SHOW, len(sub)), random_state=0).itertuples(), 1):
            ctx = r.context.replace("|", "/").replace("\n", " ")
            lines.append(f"| {i} | {r.dialogue_id} | {r.text} | {r.gt_L2 or '-'} | {ctx} |")
        lines.append("")
    return "\n".join(lines)


def rescore():
    """Rows: every finished chain x mapping (fixed3 = the old fixed train/hotel/restaurant list, all = every file) x GT view
    (full, reach_old = results/wf_v4/gt/reachable_dev50.csv, reach_y1 = annotation rule)."""
    out = RUN / "step4_as_dev50"
    gt = SC43.load_gt(ROOT)
    views = {"full": None, "reach_old": gt["reachable"][SET], "reach_y1": G.reachable_by_annotations(gt, SET)}
    hand = V.score_map_dir(out, "a_llama44", ROOT)
    rows = []
    for st in json.loads((out / "final" / "status.json").read_text(encoding="utf-8")):
        if not st["ok"]:
            continue
        c = json.loads((out / "final" / st["run"] / "canonical.json").read_text(encoding="utf-8"))
        names = G.gt_names(gt)
        for mname, ents in (("fixed3", G.ENTITIES), ("all", None)):
            full = G.map_handover(hand, SET, ROOT / SCR.GT_LEVELS[SET], names, entities=ents)
            mapping = {s: full.get(s) or {"gt": None, "purity": 0.0, "n": 0, "entity": s.split(":")[0]}
                       for s in {c2["source"] for t in c["tables"] for c2 in t["columns"] if c2.get("source")}
                       | {u["source"] for u in c.get("unused", [])}}
            for vname, reach in views.items():
                gt["reachable"][SET] = reach
                res = S.score(c, gt, SET, reach is not None, mapping)
                rows.append({"chain": st["run"], "mapping": mname, "gt_view": vname, **S.flat(res)})
        gt["reachable"][SET] = views["reach_old"]
    return rows


def table(rows):
    df = pd.DataFrame(rows)
    lines = ["| mapping | GT view | " + " | ".join(METRICS) + " |", "|---" * (len(METRICS) + 2) + "|"]
    for (mp, vw), g in df.groupby(["mapping", "gt_view"], sort=False):
        cells = []
        for k in METRICS:
            if f"{k}_k" in g:
                kk, nn = int(g[f"{k}_k"].sum()), int(g[f"{k}_n"].sum())
                cells.append(f"{kk}/{nn} ({kk / nn:.3f})" if nn else "n/a")
            else:
                cells.append(f"{g[k].mean():.3f}")
        lines.append(f"| {mp} | {vw} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names = json.loads((GRAPH / "entities.json").read_text(encoding="utf-8"))
    (OUT / "mentions.md").write_text(mention_sample(names) + "\n", encoding="utf-8", newline="\n")
    rows = rescore()
    SCR.write_rows(OUT / "scores.csv", rows)
    gt = SC43.load_gt(ROOT)
    old, new = gt["reachable"][SET], G.reachable_by_annotations(gt, SET)
    diff = sorted(c for c in new if old.get(c) != new[c])
    text = ["# Y1 rescore of the wf_v4.5 dev50 Step 4 chains (3 seeds, counts summed, F1 means)", "", table(rows), "",
            f"Columns whose reachable status changes (old -> Y1 rule): {len(diff)}", ""]
    text += [f"- {c}: {old.get(c)} -> {new[c]}" for c in diff]
    (OUT / "y1.md").write_text("\n".join(text) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(text))


if __name__ == "__main__":
    main()
