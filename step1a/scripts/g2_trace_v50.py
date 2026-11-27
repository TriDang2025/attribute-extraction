"""wf_v5.0 G2: miss trace. For every gold L2 attribute not found by wf_v4.9 (loop 1 + 2, human check), the first pipeline step where it is
lost (s1a/trace_v50.py), 2 example mentions and the loop-2 status. dev50 and dev50b only.

python scripts/g2_trace_v50.py  -> results/wf_v50/g2/{trace_<set>.csv, g2_table.csv, g2.md}
Runs: loop 1 = results/wf_v46/y3/<set>/step3/{columns.json, scores/final_columns.json} (the run the v4.8 W1 / v4.9 V2 scoring reads),
loop 2 = results/wf_v47/z4/run1/<set>/loop2/suggestions.csv; entity map = results/wf_v48/w1/<set>/entity_map.json.
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
from s1a import step4_gt as SG  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402
from s1a import trace_v50 as T  # noqa: E402

OUT = ROOT / "results" / "wf_v50" / "g2"
SETS = ("dev50", "dev50b")
STOPS = ["S1", "S2", "S3", "S4/S5", "S6", "S7", "S8", "S9"]


def load(set_name, step3=None):
    """Data of a set; `step3` = another Step 3 folder (default: the v4.6 Y3 run), e.g. the wf_v5.1 R5 Step 3."""
    run = Path(step3) if step3 else ROOT / "results" / "wf_v46" / "y3" / set_name / "step3"
    key = M46.RUN_OF[set_name]
    mt = pd.read_csv(ROOT / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
    mt["mention_id"] = mt["mention_id"].astype(int)
    mt = mt.set_index("mention_id")
    gt = pd.read_csv(ROOT / I.GT_LEVELS[set_name], keep_default_na=False)
    labels = {int(i): [x for x in SG.split_labels(v) if x] for i, v in zip(gt["mention_id"], gt["gt_L2"])}
    emap = {k: (v["stage1"], v["gt_entity"], v["share"]) for k, v in
            json.loads((ROOT / "results" / "wf_v48" / "w1" / set_name / "entity_map.json").read_text(encoding="utf-8")).items()}
    cols = json.loads((run / "columns.json").read_text(encoding="utf-8"))[key]
    final = json.loads((run / "scores" / "final_columns.json").read_text(encoding="utf-8"))[key]
    sugg = pd.read_csv(ROOT / "results" / "wf_v47" / "z4" / "run1" / set_name / "loop2" / "suggestions.csv", keep_default_na=False)
    sugg["gt_entity"] = [emap[e][1] if e in emap else "" for e in sugg["entity"]]
    sugg["passed"] = sugg["passed"].astype(str) == "True"
    return mt, labels, emap, cols, final, sugg.to_dict("records")


def examples(mt, labels, attr, k=2):
    ids = [i for i in mt.index if attr in labels.get(i, [])][:k]
    return " | ".join(f"{mt.at[i, 'text'] if 'text' in mt.columns else mt.at[i, 'norm_value']} ({mt.at[i, 'dialogue_id']} t{mt.at[i, 'turn']})"
                      for i in ids)


def checkpoints(mt, entity, key, cols, final, labels):
    clusters = T.ids_groups_clusters(mt, entity)
    split = T.ids_groups_split(clusters, cols[key]["parts"])
    columns = T.ids_groups_columns(cols[key]["columns"], split)
    doc = M46.handover({key: final[key]}, {key: (entity, "train", 1.0)})["train"]   # any gold entity name: only the columns are used
    cluster_of = mt["cluster_id"].to_dict()
    fin = {f"{c['name']}#{j}": ids for c in doc["columns"] for j, ids in enumerate(MC.rebuild_groups(c, cluster_of))}
    return {"clusters": clusters, "split": split, "columns": columns, "final": fin}


def trace_set(set_name, cfg, data=None, found_gold=None):
    """Trace table of a set. data = load(...) tuple (default: v4.6 Y3), found_gold = ({"loop2": found attrs}, {gold attr: entity}) (default:
    wf_v4.9 found_v49): the misses are the gold attributes that are not in found["loop2"]."""
    mt, labels, emap, cols, final, sugg = data or load(set_name)
    found, gold = found_gold or M49.found_v49(set_name)
    gold_by_ent = {}
    for a, e in gold.items():
        gold_by_ent.setdefault(e, []).append(a)
    key_of = {gt: k for k, (_s1, gt, _sh) in emap.items() if gt in M46.GOLD_ENTITIES}
    rows = []
    for attr in sorted(set(gold) - found["loop2"]):
        ent = gold[attr]
        key = key_of.get(ent)
        if key is None:      # no predicted entity is matched to the gold entity (taxi rule on, dev50): S1, there is nothing to trace
            cnt = T.entity_share(mt, labels, attr, "")[1]
            loop2, detail = T.loop2_status(attr, ent, sugg, gold_by_ent, cfg)
            rows.append({"set": set_name, "attr": attr, "gold_entity": ent, "scored_entity": "none", "n_pipe": sum(cnt.values()), "share_in_scored": 0.0,
                         "entities": "; ".join(f"{e}={n}" for e, n in cnt.most_common()), "examples": examples(mt, labels, attr), "stop": "S1",
                         "stop_last": "S1", "stop_in_entity": "", "if_majority_scored": "no predicted entity matched to " + ent,
                         "loop2": loop2, "loop2_detail": detail})
            continue
        stage1 = emap[key][0]
        n_pipe = sum(attr in labels.get(i, []) for i in mt.index)
        share, cnt = T.entity_share(mt, labels, attr, stage1)
        total = sum(attr in labels.get(i, []) for i in mt.index[(mt["entity"] == stage1) & (mt["cluster_id"] != "")])
        row = {"set": set_name, "attr": attr, "gold_entity": ent, "scored_entity": f"{key} ({stage1})", "n_pipe": n_pipe,
               "share_in_scored": round(share, 2),
               "entities": "; ".join(f"{e}={n}" for e, n in cnt.most_common()), "examples": examples(mt, labels, attr)}
        row.update(T.trace(attr, ent, checkpoints(mt, stage1, key, cols, final, labels), labels, total, found["loop2"]))
        trace_stop = row["stop"]
        if n_pipe == 0:
            row["stop"] = "S2"
        elif share < T.S1_SHARE:
            row["stop"] = "S1"
        row["stop_in_entity"] = trace_stop
        row["if_majority_scored"] = majority_trace(attr, ent, cnt, stage1, emap, mt, cols, final, labels) if row["stop"] == "S1" else ""
        row["loop2"], row["loop2_detail"] = T.loop2_status(attr, ent, sugg, gold_by_ent, cfg)
        rows.append(row)
    return pd.DataFrame(rows)


def majority_trace(attr, ent, cnt, stage1, emap, mt, cols, final, labels):
    """S1 cases: the trace in the stage-1 entity that holds most of the attribute's mentions, as if that entity were scored for `ent`
    ("found" or its stop point)."""
    major = cnt.most_common(1)[0][0]
    key = next((k for k, v in emap.items() if v[0] == major), None)
    if major == stage1 or key is None:
        return ""
    total = sum(attr in labels.get(i, []) for i in mt.index[(mt["entity"] == major) & (mt["cluster_id"] != "")])
    r = T.trace(attr, ent, checkpoints(mt, major, key, cols, final, labels), labels, total, set())
    return f"{key}: " + ("found" if r["final_ok"] else f"{r['stop']} ({r['final_best']})")


def stop_table(tabs):
    """Stop points (rows) x set first / last (columns) from {set: trace_set DataFrame}; S7 / S8 are the loop-2 statuses."""
    table = pd.DataFrame({"stop point": STOPS})
    for s, df in tabs.items():
        table[f"{s} first"] = [int((df["loop2"] == st).sum()) if st in ("S7", "S8") else int((df["stop"] == st).sum()) for st in STOPS]
        last = df["stop"].where(df["stop"].isin(["S1", "S2"]), df["stop_last"])
        table[f"{s} last"] = [int((df["loop2"] == st).sum()) if st in ("S7", "S8") else int((last == st).sum()) for st in STOPS]
    return table


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(MC.NAME_MATCH.read_text(encoding="utf-8"))
    tabs = {s: trace_set(s, cfg) for s in SETS}
    for s, df in tabs.items():
        df.to_csv(OUT / f"trace_{s}.csv", index=False, encoding="utf-8", lineterminator="\n")
    table = pd.DataFrame({"stop point": STOPS})
    for s, df in tabs.items():
        table[f"{s} first"] = [int((df["loop2"] == st).sum()) if st in ("S7", "S8") else int((df["stop"] == st).sum()) for st in STOPS]
        last = df["stop"].where(df["stop"].isin(["S1", "S2"]), df["stop_last"])
        table[f"{s} last"] = [int((df["loop2"] == st).sum()) if st in ("S7", "S8") else int((last == st).sum()) for st in STOPS]
    table.to_csv(OUT / "g2_table.csv", index=False, encoding="utf-8", lineterminator="\n")
    cols = ["attr", "n_pipe", "share_in_scored", "stop", "stop_last", "stop_in_entity", "if_majority_scored", "clusters_best", "split_best", "columns_best", "final_best",
            "loop2", "loop2_detail", "examples"]
    lines = ["# wf_v5.0 G2: miss trace (first stop point; loop 2 counted separately as S7/S8)", "", table.to_markdown(index=False), ""]
    for s, df in tabs.items():
        lines += [f"## {s}", "", df[cols].to_markdown(index=False), ""]
    (OUT / "g2.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(table.to_string(index=False))
    for s, df in tabs.items():
        print(df[["set", "attr", "n_pipe", "stop", "stop_last", "if_majority_scored", "clusters_best", "split_best", "columns_best",
                  "final_best", "loop2"]].to_string(index=False))


if __name__ == "__main__":
    main()
