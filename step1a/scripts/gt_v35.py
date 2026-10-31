"""T2/T3 (GT_V35_CONTRACT.md): match dev50 mentions to MultiWOZ 2.2 spans, build GT levels L1/L2/L3, coverage tables.

python scripts/gt_v35.py --run results/graph_v22_dev50 --mwoz C:/Users/nguye/data/MultiWOZ_2.2 --out results/loop1_v35
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import gt_ext as GT  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402

DB_ZIP = ROOT.parent / "chunking" / "data" / "MULTIWOZ2.4.zip"


def dev_utterances(docs, mentions):
    """{(dialogue_id, turn): raw turn text} and {(dialogue_id, turn): speaker} for the mentions' turns."""
    utt, spk = {}, {}
    for did, turn in set(zip(mentions["dialogue_id"], mentions["turn"].astype(int))):
        lo, hi = MN.turn_bounds(docs[did], turn)
        utt[(did, turn)] = docs[did].text[lo:hi]
        spk[(did, turn)] = PIN._speaker(docs[did], turn)
    return utt, spk


def md_table(df):
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mwoz", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--map", default=str(ROOT / "config" / "tear_to_mwoz.json"))
    ap.add_argument("--q34", default=str(ROOT / "results" / "loop1_v34"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    run = Path(a.run)
    mentions = pd.read_csv(run / "spans" / "mentions.csv", keep_default_na=False)
    mentions["mention_id"] = mentions["mention_id"].astype(int)
    docs, _gv, _attrs = MN.load_shared(run)
    utt, spk = dev_utterances(docs, mentions)
    # char_start/char_end in mentions.csv are offsets into the whole dialogue text; make them turn-relative
    lo = [MN.turn_bounds(docs[d], int(t))[0] for d, t in zip(mentions["dialogue_id"], mentions["turn"])]
    mentions["char_start"] = mentions["char_start"].astype(int) - lo
    mentions["char_end"] = mentions["char_end"].astype(int) - lo
    mentions["speaker"] = [spk[(d, int(t))] for d, t in zip(mentions["dialogue_id"], mentions["turn"])]

    dialogues, acts = GT.load_mwoz(a.mwoz, set(mentions["dialogue_id"]))
    spans = GT.span_table(dialogues, acts)
    mw_utts = {(GT.dialogue_key(d["dialogue_id"]), i): t["utterance"] for d in dialogues for i, t in enumerate(d["turns"])}
    matched = GT.match(mentions, spans, utt, mw_utts)
    schema = {s["name"] for svc in json.loads((Path(a.mwoz) / "schema.json").read_text(encoding="utf-8")) for s in svc["slots"]}
    tear_map = json.loads(Path(a.map).read_text(encoding="utf-8"))
    lv = GT.levels(mentions, matched, tear_map, GT.load_db(DB_ZIP), schema, utt)

    matched.to_csv(out / "mwoz_match.csv", index=False)
    lv.to_csv(out / "gt_levels.csv", index=False)
    fail = matched[matched["text_match"] == "none"].merge(mentions[["mention_id", "text", "context"]], on="mention_id")
    fail.to_csv(out / "match_failures.csv", index=False)

    q34 = Path(a.q34)
    old = {"q2": pd.read_csv(q34 / "q2_table.csv") if (q34 / "q2_table.csv").exists() else None,
           "q1": pd.read_csv(q34 / "q1_table_values.csv", keep_default_na=False) if (q34 / "q1_table_values.csv").exists() else None}
    table, extra = GT.coverage(mentions, lv, old)
    table.to_csv(out / "gt_coverage.csv", index=False)
    tm, mm = matched["text_match"].value_counts(), matched["match"].value_counts()
    md = ["# GT coverage (wf_v3.5, W1)", "",
          f"dialogues matched: {matched.loc[matched['text_match'] != 'none', 'dialogue_id'].nunique()} of {mentions['dialogue_id'].nunique()} "
          f"({len(dialogues)} found in MultiWOZ 2.2)",
          f"mentions: {len(matched)}; text_match: " + ", ".join(f"{k} {tm.get(k, 0)}" for k in ("exact", "fuzzy", "none")),
          "match: " + ", ".join(f"{k} {mm.get(k, 0)}" for k in ("span", "value", "none")),
          f"choice mentions: {int(lv['is_choice'].sum())}; request mentions: {int(lv['is_request'].sum())}", "",
          "## Labelled share per level (entity x speaker)", "", md_table(table), "",
          "## v3.4 unknown clusters and other values", "", "\n".join(f"- {k}: {v}" for k, v in extra.items())]
    (out / "gt_coverage.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
