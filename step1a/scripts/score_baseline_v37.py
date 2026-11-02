"""wf_v3.7 T11 (prep): rating sheet and table of the LLM-only baseline (contract: WF_V37_CONTRACT.md, W3). No LLM, no model.

python scripts/score_baseline_v37.py --mwoz C:/Users/nguye/data/MultiWOZ_2.2 \
    [--set dev50 results/graph_v22_dev50 results/loop1_v35] [--set dev50b results/graph_v22_dev50b results/loop1_v37/dev50b/gt]
Reads <colab>/responses/baseline_<ent>_<set>_<v0|v1|v2>.jsonl (last row of each file; `llm_cache.parse_baseline`).
Writes <out>/names_to_rate_baseline.csv (blind, shuffled) + names_to_rate_baseline_key.csv, then, when the answers
<out>/names_baseline_rater1.csv / names_baseline_rater2.csv (row,label; rubric: results/loop1_v36/names_l2_rubric.md)
exist, <out>/baseline_v37.{md,csv}: baseline (each version and the union) next to A at L2 (all_variants_v36.csv).
Per set the L2 base and the L2 spans come from <run>/{gold_values.csv, gold_attrs.txt, spans/mentions.csv, docs.jsonl} and
<gt>/gt_levels.csv. The counts and the support check are defined in s1a/baseline_v37.py.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import baseline_prompt_v37 as BP  # noqa: E402
from s1a import baseline_v37 as BL  # noqa: E402
from s1a import names_l2 as NL  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import v34_data  # noqa: E402
from pilot_eval_v31 import GOLD_ENTS  # noqa: E402

A_VARIANTS = ("A r1", "A r2", "A s2")


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")


def last_raw(path):
    """`raw` of the last row of a response file; None when the file is missing or empty."""
    p = Path(path)
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    return rows[-1].get("raw") if rows else None


def set_data(run, gt):
    """(base {ent: [attrs]}, attrs_with_span set, docs {dialogue_id: text}) of one set at L2."""
    run, gt = Path(run), Path(gt)
    gold_values = read_csv(run / "gold_values.csv")
    gold_attrs = [x for x in (run / "gold_attrs.txt").read_text(encoding="utf-8").splitlines() if x]
    lv = read_csv(gt / "gt_levels.csv")
    m = read_csv(run / "spans" / "mentions.csv")[["mention_id", "dialogue_id"]].merge(
        lv[["mention_id", "gt_L2", "ent_L2"]], on="mention_id", how="left").fillna("")
    full = m.rename(columns={"gt_L2": "gold_attr", "ent_L2": "entity_gold"})
    base = {ent: v34_data.level_attrs(full, GOLD_ENTS[ent], PS.train_attrs(gold_values, gold_attrs, GOLD_ENTS[ent]))
            for ent in BP.ENTITY_WORD}
    with_span = {c for g in full["gold_attr"] for c in PS._classes(g)}
    docs = {}
    for line in (run / "docs.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        docs[r["dialogue_id"]] = r["text"]
    return base, with_span, docs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", nargs=3, action="append", metavar=("NAME", "RUN", "GT"),
                    help="a set: name, run dir, GT dir (default: dev50 results/graph_v22_dev50 results/loop1_v35)")
    ap.add_argument("--colab", type=Path, default=Path("results/loop1_v37/colab"))
    ap.add_argument("--mwoz", required=True, type=Path, help="MultiWOZ 2.2 folder (schema.json)")
    ap.add_argument("--tear-map", type=Path, default=Path("config/tear_to_mwoz.json"))
    ap.add_argument("--all-variants", type=Path, default=Path("results/loop1_v36/all_variants_v36.csv"))
    ap.add_argument("--a-setting", default="default", help="`setting` column of all_variants for the A rows")
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v37"))
    a = ap.parse_args()
    sets = a.set or [["dev50", "results/graph_v22_dev50", "results/loop1_v35"]]
    a.out.mkdir(parents=True, exist_ok=True)

    schema = json.loads((a.mwoz / "schema.json").read_text(encoding="utf-8"))
    slot_desc = {s["name"]: s["description"] for svc in schema for s in svc["slots"]}
    tear_map = {k: v for k, v in json.loads(a.tear_map.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    manifest_ids = json.loads((a.colab / "baseline" / "dialogues_used.json").read_text(encoding="utf-8"))

    data, raw = {}, {}
    for name, run, gt in sets:
        data[name] = set_data(run, gt)
        for ent in BP.ENTITY_WORD:
            for v in BP.VERSIONS:
                r = last_raw(a.colab / "responses" / f"baseline_{ent}_{name}_{v}.jsonl")
                if r is not None:
                    raw[(name, ent, v)] = r
    lists, notes = BL.attribute_lists(raw)
    if not lists:
        sys.exit(f"no baseline responses in {a.colab / 'responses'}")
    slots_by_ent = {ent: {x: (NL.slot_key(x, tear_map), slot_desc.get(NL.slot_key(x, tear_map), ""))
                          for x in data[next(iter(data))][0][ent]} for ent in BP.ENTITY_WORD}
    base_by = {ent: set() for ent in BP.ENTITY_WORD}
    for name in data:
        for ent in BP.ENTITY_WORD:
            base_by[ent] |= set(data[name][0][ent])
    for ent, attrs in base_by.items():   # a set may add base attrs: its slots are shown too
        for x in attrs - set(slots_by_ent[ent]):
            slots_by_ent[ent][x] = (NL.slot_key(x, tear_map), slot_desc.get(NL.slot_key(x, tear_map), ""))

    rater, key = BL.rating_sheet(lists, slots_by_ent)
    rater.to_csv(a.out / "names_to_rate_baseline.csv", index=False, encoding="utf-8", lineterminator="\n")
    key.to_csv(a.out / "names_to_rate_baseline_key.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(f"sheet: {len(rater)} rows; notes: {notes}")

    files = [a.out / f"names_baseline_rater{i}.csv" for i in (1, 2)]
    if not all(f.exists() for f in files):
        print("not rated yet:", [f.name for f in files if not f.exists()])
        return
    labels = BL.read_ratings([read_csv(f) for f in files])
    base = {ent: data[next(iter(data))][0][ent] for ent in BP.ENTITY_WORD}
    spans_by, ctx_by = {}, {}
    for name, (_, with_span, docs) in data.items():
        for ent in BP.ENTITY_WORD:
            ids = sorted({i for v in BP.VERSIONS for i in manifest_ids.get(f"baseline_{ent}_{name}_{v}", [])})
            spans_by[(name, ent)] = with_span
            ctx_by[(name, ent)] = BL.dialogue_kinds_turns([t for i in ids for t in docs[i].split("\n")])
    scores = BL.score_rows(key, labels, base, spans_by, ctx_by)
    scores.to_csv(a.out / "baseline_v37.csv", index=False, encoding="utf-8", lineterminator="\n")
    _, md = BL.table(scores)
    ref = BL.a_reference(read_csv(a.all_variants), A_VARIANTS, a.a_setting)
    lines = ["# wf_v3.7 LLM-only baseline at L2", "",
             "Names rated by two blind raters against the lexically closest L2 slot (lower label wins); counts are summed over "
             "train, hotel and restaurant. Definitions: `s1a/baseline_v37.py`. `union` = the distinct names of v0, v1 and v2.",
             "", md, "", f"## A at L2 (all_variants_v36.csv, setting `{a.a_setting}`, dev50)", "",
             "| variant | right names (names L2 rated) | found attributes |", "|---|---|---|",
             *[f"| {r.variant} | {r.right}/{r.base_n} | {r.found}/{r.gold_n} |" for r in ref.itertuples()], "",
             "Partly, wrong, extras, no-support and column counts of A are not in that file; compute them from the A "
             "decisions (W1 tables) to compare.", ""]
    if notes:
        lines += ["Notes:", *[f"- {n}" for n in notes], ""]
    (a.out / "baseline_v37.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
