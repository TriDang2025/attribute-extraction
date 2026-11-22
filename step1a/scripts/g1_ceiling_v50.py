"""wf_v5.0 G1: which gold L2 attributes can be found at all (text ceiling), per set. dev50 and dev50b only (dev50c stays sealed).

python scripts/g1_ceiling_v50.py [--mwoz C:/Users/nguye/data/MultiWOZ_2.2]
  -> results/wf_v50/g1/{g1.md, g1_summary.csv, ceiling_<set>.csv, mentions_<set>.csv}
Gold list and found set = wf_v4.9 V2 (scripts/mainclaim_v49.found_v49, loop 1 + 2 with the human check and the confirmed mapping).
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import mainclaim_v49 as M49  # noqa: E402
from s1a import ceiling_v50 as C  # noqa: E402
from s1a import gt_ext as GT  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import step4_gt as SG  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402

OUT = ROOT / "results" / "wf_v50" / "g1"
SETS = ("dev50", "dev50b")


def turn_finder(docs):
    def turn_of(did, char):
        for i, (lo, hi) in enumerate(docs[did].spans):
            if lo <= int(char) < hi:
                return i
        return None
    return turn_of


def set_mentions(set_name, gold, mwoz_dir, tear_map):
    run = ROOT / "results" / f"graph_v22_{set_name}"
    docs, gv, _ = MN.load_shared(run)
    names = set(gold)
    dialogues, acts = GT.load_mwoz(mwoz_dir, set(docs))
    if len(dialogues) != len(docs):
        raise ValueError(f"{set_name}: {len(dialogues)} of {len(docs)} dialogues found in MultiWOZ 2.2")
    mw = C.mwoz_mentions(GT.span_table(dialogues, acts), C.booking_domains(dialogues), tear_map, names)
    mt = pd.read_csv(run / "spans" / "mentions.csv", dtype=str, keep_default_na=False,
                     usecols=["mention_id", "dialogue_id", "turn", "norm_value"])
    gt = pd.read_csv(ROOT / I.GT_LEVELS[set_name], keep_default_na=False)
    labels = {int(i): [x for x in SG.split_labels(v) if x] for i, v in zip(gt["mention_id"], gt["gt_L2"])}
    return pd.concat([C.tear_mentions(gv, turn_finder(docs), names), mw, C.pipe_mentions(mt, labels, names)], ignore_index=True)


def md(df):
    return df.to_markdown(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mwoz", default="C:/Users/nguye/data/MultiWOZ_2.2")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    tear_map = json.loads((ROOT / "config" / "tear_to_mwoz.json").read_text(encoding="utf-8"))
    summ, tables = {}, {}
    for s in SETS:
        found, gold = M49.found_v49(s)
        ments = set_mentions(s, gold, a.mwoz, tear_map)
        rows = C.ceiling_rows(gold, found["loop2"], ments)
        ments.to_csv(OUT / f"mentions_{s}.csv", index=False, encoding="utf-8", lineterminator="\n")
        rows.to_csv(OUT / f"ceiling_{s}.csv", index=False, encoding="utf-8", lineterminator="\n")
        summ[s], tables[s] = C.summary(rows), rows
    sm = pd.DataFrame(summ).rename_axis("").reset_index()
    sm.to_csv(OUT / "g1_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    lines = ["# wf_v5.0 G1: text ceiling of the gold L2 attributes", "",
             "Text mention = TEAR gold value or MultiWOZ 2.2 span (one per dialogue, turn, value). Pipeline = our Step 1a mentions "
             "with the gt_L2 label. Found = wf_v4.9 loop 1 + 2 with the human check.", "", md(sm), ""]
    for s, rows in tables.items():
        cols = ["entity", "attr", "kind", "n_text", "dialogues_text", "n_pipe", "found_v49"]
        lines += [f"## {s}: per attribute", "", md(rows[cols]), "",
                  f"### {s}: missed attributes", "", md(rows.loc[~rows["found_v49"], cols]), ""]
    (OUT / "g1.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(sm.to_string(index=False))


if __name__ == "__main__":
    main()
