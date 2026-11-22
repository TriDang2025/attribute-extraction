"""wf_v4.9 V4: sensitivity of loop-2 fix F3 (l1_share) on the cached v4.7 run-1 loop-2 output. No LLM, no gold.

python scripts/replay_v49.py [--sets dev50,dev50b] [--l1-share 0.1,0.25,0.5]
  -> results/wf_v49/v4/l1s_<x>/<set>/   replay_v48 outputs with config/wf_v48_loop2.json, only loop1_embed.l1_share changed
     results/wf_v49/v4/v4.csv, v4.md    new columns per set and value (names, example values, internet / parking separate, real)
real = hand judgement: W1 sheet (results/wf_v48/w1/sheets/<set>_human_check_sheet.csv, real column) matched by attribute name + entity,
else the tag of the W2 table in results/wf_v48/w2/w2.md, else "NEW - needs judgement".
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import replay_v48 as R  # noqa: E402

OUT = ROOT / "results" / "wf_v49" / "v4"
W1 = ROOT / "results" / "wf_v48" / "w1" / "sheets"
W2_MD = ROOT / "results" / "wf_v48" / "w2" / "w2.md"
COARSE = (("accommodation", "hotel"), ("train", "train"), ("restaurant", "restaurant"), ("establishment", "restaurant"), ("taxi", "taxi"))
NEW = "NEW - needs judgement"


def coarse(entity):
    return next((c for k, c in COARSE if k in entity), entity)


def key(entity, name):
    return coarse(entity), re.sub(r"\s*\(#\d+\)|\s*\(\+.*\)", "", name).replace("_", " ").strip()


def hand_tags(set_name):
    """({(entity, name): W1 real}, {(entity, name): W2 tag}) for one set."""
    sheet = pd.read_csv(W1 / f"{set_name}_human_check_sheet.csv", dtype=str, keep_default_na=False)
    w1 = {(coarse(r.entity), r.attribute): r.real for r in sheet.itertuples()}
    w2 = {}
    for line in W2_MD.read_text(encoding="utf-8").splitlines():
        p = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(p) == 6 and p[0] == set_name:
            w2[key(p[1], p[2])] = p[5]
    return w1, w2


def separate(rows, a, b):
    """internet / parking test: a and b are both new columns of their own name, and no other column joined or duplicates into either."""
    own = {k: [r for r in rows if r["status"] == "new" and r["name"] == k] for k in (a, b)}
    taken = [r for r in rows if any(k in r["joined"] or k in r["duplicate_of"] for k in (a, b)) and r["name"] not in (a, b)]
    joined_own = [r for r in rows if r["name"] in (a, b) and (b if r["name"] == a else a) in r["joined"]]
    return bool(own[a] and own[b]) and not taken and not joined_own


def report(sets, values):
    rows = []
    for s in sets:
        w1, w2 = hand_tags(s)
        for x in values:
            cols = pd.read_csv(OUT / f"l1s_{x}" / s / "new_columns.csv", dtype=str, keep_default_na=False).to_dict("records")
            new = [r for r in cols if r["status"] == "new"]
            sep = separate(cols, "internet", "parking")
            for r in new:
                k = key(r["entity"], r["name"])
                rows.append({"set": s, "l1_share": x, "entity": r["entity"], "name": r["name"], "joined": r["joined"], "n_mentions": r["n_mentions"],
                             "mix": r["mix"], "top_values": r["top_values"], "n_new_columns": len(new), "internet_parking_separate": sep,
                             "real": w1.get(k) or NEW, "w2_tag": w2.get(k, "")})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "v4.csv", index=False, encoding="utf-8", lineterminator="\n")
    md = ["# wf_v4.9 V4: F3 l1_share sensitivity (loop-2 replay, no LLM, no gold)", "",
          "real: W1 sheet (attribute + entity), `NEW` = not in the W1 sheet. w2 tag: W2 table in w2.md where listed.", "",
          "| set | l1_share | new columns | internet and parking separate |", "|---|---|---|---|"]
    for (s, x), g in df.groupby(["set", "l1_share"], sort=False):
        md.append(f"| {s} | {x} | {len(g)} | {'yes' if g.internet_parking_separate.iloc[0] else 'no'} |")
    md += ["", "| set | l1_share | entity | column (joined) | mentions | example values | real | w2 tag |", "|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        name = r.name + (f" (+ {r.joined})" if r.joined else "")
        md.append(f"| {r.set} | {r.l1_share} | {r.entity} | {name} | {r.n_mentions} | {r.top_values.replace(' | ', ', ')} | {r.real} | {r.w2_tag} |")
    pending = sorted({(r.set, r.entity, r.name) for r in df.itertuples() if r.real == NEW})
    md += ["", "Needs a new judgement:", *[f"- {s}: {e} / {n}" for s, e, n in pending]]
    (OUT / "v4.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return pending


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", default="dev50,dev50b")
    ap.add_argument("--l1-share", default="0.1,0.25,0.5")
    a = ap.parse_args()
    cfg = json.loads(R.CONFIG.read_text(encoding="utf-8"))
    sets = [s.strip() for s in a.sets.split(",")]
    values = [x.strip() for x in a.l1_share.split(",")]
    from run import encoder as make_encoder
    enc = make_encoder()
    try:
        for x in values:
            c = {**cfg, "loop1_embed": {**cfg["loop1_embed"], "l1_share": float(x)}}
            for s in sets:
                R.run_set(s, c, enc, out=OUT / f"l1s_{x}")
                print(f"l1_share {x} {s} done", flush=True)
                if float(x) == cfg["loop1_embed"]["l1_share"]:
                    same = (OUT / f"l1s_{x}" / s / "new_columns.csv").read_text(encoding="utf-8") == (R.OUT / s / "new_columns.csv").read_text(encoding="utf-8")  # text mode: git may check out CRLF
                    print(f"  new_columns.csv identical to results/wf_v48/w2/{s}: {same}", flush=True)
    finally:
        enc.save()
    print("needs judgement:", report(sets, values))


if __name__ == "__main__":
    main()
