"""wf_v4.6 Y3 / Y7: main-claim scoring (found L2, new attributes, blind human-check sheet) of the v4.6 pipeline runs, loop 1 and loop 1 + 2.

python scripts/mainclaim_v46.py [--sets dev50,dev50b]  -> results/wf_v46/mainclaim/<set>/{compare.md, compare.csv, human_check_sheet.csv,
                                                          human_check_key.csv, entity_map.json}
Same rules and code as scripts/mainclaim_v41.py (rules v1.3: found = purity 0.6, coverage 0.10 over A s012 groups). The run's columns
(results/wf_v46/y3/<set>/step3/scores/final_columns.json) replace handover/<set>/; loop 2 = the run's loop2/evidence/clusters.json.
Scoring only (never fed back): each predicted entity is matched to the GT entity that most of its mentions belong to (ent_L2 of the set's
gt_levels.csv); only entities matched to a gold-list entity (train, hotel, restaurant) are scored, as in STEP3.md. The raw-corpus runs have
the same mention ids as results/graph_v22_<set> (checked for c_n50 in wf_v4.5 W2 and for c_n50b in wf_v4.6).
A filled sheet is kept on a rerun (mainclaim_v41.merge_answers).
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import mainclaim_v41 as MC  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402

RUNS = ROOT / "results" / "wf_v46" / "y3"
OUT = ROOT / "results" / "wf_v46" / "mainclaim"
RUN_OF = {"dev50": "c_n50", "dev50b": "c_n50b"}
GOLD_ENTITIES = ("train", "hotel", "restaurant")


def entity_map(set_name, keys, root=ROOT):
    """{run entity key: (stage-1 id, GT entity, share)}: the GT entity most of the stage-1 entity's mentions belong to (ent_L2; empty = none)."""
    mt = pd.read_csv(root / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False,
                     usecols=["mention_id", "entity"])
    gt = pd.read_csv(root / I.GT_LEVELS[set_name], dtype=str, keep_default_na=False, usecols=["mention_id", "ent_L2"])
    j = mt.merge(gt, on="mention_id", how="left").fillna("")
    out = {}
    for key, e in keys.items():
        cnt = Counter(j.loc[j["entity"] == e, "ent_L2"])
        lab, k = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        out[key] = (e, lab, round(k / sum(cnt.values()), 3))
    return out


def handover(final_cols, emap):
    """{GT entity: handover-format doc} from the run's final columns (members "cluster@group"); only gold-list GT entities. Two run entities
    on one GT entity: ValueError (not met so far; would need a merge rule)."""
    docs = {}
    for key, cols in final_cols.items():
        stage1, ent, _ = emap[key]
        if ent not in GOLD_ENTITIES:
            continue
        if ent in docs:
            raise ValueError(f"run entities {docs[ent]['run_key']} and {key} both match GT entity {ent}")
        docs[ent] = {"run_key": key, "stage1_entity": stage1, "columns": [
            {"id": c["cid"], "name": c["name"], "mention_ids": [int(i) for i in c["mention_ids"]],
             "members": [dict(zip(("cluster", "group"), m.split("@"))) for m in c["members"]]} for c in cols]}
    return docs


def loop2_file(run_dir, emap, out):
    """The run's loop-2 clusters of the scored entities, with entity = stage-1 id (mainclaim maps it with the handover), to <out>/loop2_clusters.json."""
    doc = json.loads((run_dir / "loop2" / "evidence" / "clusters.json").read_text(encoding="utf-8"))
    rows = doc.get("clusters") if isinstance(doc, dict) else doc
    keep = {emap[k][0] for k in emap if emap[k][1] in GOLD_ENTITIES}
    rows = [{**c, "entity": c["stage1_entity"]} for c in rows if c["stage1_entity"] in keep]
    p = out / "loop2_clusters.json"
    p.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return p


def split_values(step3_dir, run_key, run, group):
    """Values of the examples the split answer gave to part `group` ("E0#6/3"), read from the [[...]] marks of the split prompt."""
    cl, part = group.split("/")
    job = f"{run_key}_{run}_split_{cl.replace('#', '-')}_r1"
    parsed = json.loads((step3_dir / "responses" / f"{job}.jsonl").read_text(encoding="utf-8").splitlines()[0])["parsed"]
    marks = dict(re.findall(r"^- (\S+) .*?\[\[(.+?)\]\]", (step3_dir / "prompts" / f"{job}.txt").read_text(encoding="utf-8"), re.M))
    return [marks[s].lower() for s in parsed["parts"][int(part)]["examples"] if s in marks]


def fill_empty_examples(set_name, run_dir, ho, out):
    """Sheet rows with no example values (split parts whose values all sit in another part, so 0 mentions): show the values of the part's
    split examples, marked "(no mentions)". Display only; the scoring is unchanged."""
    d = Path(out) / set_name
    sheet = pd.read_csv(d / "human_check_sheet.csv", dtype=str, keep_default_na=False)
    key = pd.read_csv(d / "human_check_key.csv", dtype=str, keep_default_na=False).set_index("id")
    final = json.loads((run_dir / "step3" / "scores" / "final_columns.json").read_text(encoding="utf-8"))[RUN_OF[set_name]]
    for i in sheet.index[sheet["example_values"] == ""]:
        ent, cid = key.loc[sheet.at[i, "id"], "item_id"].split(":")
        run_key = ho[ent]["run_key"]
        col = next(c for c in final[run_key] if str(c["cid"]) == cid)
        vals = [v for g in col["groups"] for v in split_values(run_dir / "step3", run_key, RUN_OF[set_name], g)]
        top = [v for v, _ in Counter(vals).most_common(MC.M.N_EXAMPLES)]
        sheet.at[i, "example_values"] = " | ".join(top) + " (no mentions)" if top else "(no mentions)"
    sheet.to_csv(d / "human_check_sheet.csv", index=False, encoding="utf-8", lineterminator="\n")


def run(set_name, runs=RUNS, out=OUT):
    run_dir = Path(runs) / set_name
    keys = json.loads((run_dir / "entities.json").read_text(encoding="utf-8"))        # {key: stage-1 id}
    emap = entity_map(set_name, keys)
    final = json.loads((run_dir / "step3" / "scores" / "final_columns.json").read_text(encoding="utf-8"))[RUN_OF[set_name]]
    d = Path(out) / set_name
    d.mkdir(parents=True, exist_ok=True)
    (d / "entity_map.json").write_text(json.dumps({k: {"stage1": v[0], "gt_entity": v[1], "share": v[2]} for k, v in emap.items()}, indent=1) + "\n",
                                       encoding="utf-8", newline="\n")
    ho = handover(final, emap)
    md, _ = MC.run(set_name, loop2_file(run_dir, emap, d), None, MC.SPANS, out, handover=ho)
    fill_empty_examples(set_name, run_dir, ho, out)
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", default="dev50,dev50b")
    a = ap.parse_args()
    for s in a.sets.split(","):
        print(run(s.strip()))


if __name__ == "__main__":
    main()
