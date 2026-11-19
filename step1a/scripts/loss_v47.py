"""wf_v4.7 Z1: where are the loop-2 suggestions lost? Reads the v4.6 loop-2 files only (no model calls, no gold).

python scripts/loss_v47.py [--runs results/wf_v46/y3] [--out results/wf_v47/z1]
  -> <out>/<set>/loss.csv       one row per suggested name: entity, name, votes, stop point, reason
     <out>/<set>/overlap.csv    the overlap fails: 3 spans, the overlapped loop-1 column, 3 values of both, value Jaccard
     <out>/<set>/vote.csv       the vote fails (name, votes, orders, description) for the manual "real information?" tag
     <out>/z1.md                stop-point table of both sets
Stop point = the first failed test: vote, then evidence (the first reason in the evidence string: no spans, n_dialogues / support =
too few dialogues, overlap), then the duplicate check; an added name whose new column was also added by an earlier name = merged.
Loop-1 columns and values: <run>/step3/scores/final_columns.json + results/graph_v22_<set>/spans/mentions.csv (same mention ids).
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN_OF = {"dev50": "c_n50", "dev50b": "c_n50b"}
STOPS = ["vote", "name check", "overlap", "no spans", "too few dialogues", "duplicate", "merged", "added"]
N_SHOW = 3


def stop_point(row, seen_cols):
    """Stop point of one suggestions.csv row; seen_cols = set of (entity, new column) already added (updated here)."""
    if row["stage"] == "vote":
        return "vote"
    if row["stage"] == "dupcheck":
        return "duplicate"
    if row["stage"] == "added":
        key = (row["entity"], row["reason"].removeprefix("new column ").strip())
        hit = key in seen_cols
        seen_cols.add(key)
        return "merged" if hit else "added"
    if row["stage"] == "check":                     # loop2_v46.screen: repeats an existing name, too long, not generic
        return "name check"
    first = row["reason"].split(";")[0]
    if first.startswith("no spans"):
        return "no spans"
    if first.startswith(("n_dialogues", "support")):
        return "too few dialogues"
    if first.startswith("overlap"):
        return "overlap"
    raise ValueError(f"unknown evidence reason: {row['reason']}")


def top(values, n=N_SHOW):
    return [v for v, _ in Counter(v for v in values if v).most_common(n)]


def jaccard(a, b):
    a, b = set(a), set(b)
    return round(len(a & b) / len(a | b), 3) if a | b else 0.0


def overlap_rows(loss, clusters, finals, mentions):
    """One row per overlap fail: the cluster's spans and values next to the overlapped loop-1 column's values."""
    by_id = {c["id"]: c for c in clusters}
    rows = []
    for r in loss[loss["stop"] == "overlap"].itertuples():
        c = by_id[r.cluster]
        col_name = c["evidence"]["overlap_column"]
        col = next(x for x in finals[r.entity] if x["name"] == col_name)
        col_vals = [mentions.get(int(i), "") for i in col["mention_ids"]]
        new_vals = [m["norm_value"] for m in c["mentions"]]
        spans = [f"{m['context']} [{m['text']}]" for m in c["mentions"][:N_SHOW]]
        rows.append({"entity": r.entity, "name": r.name, "votes": r.votes, "overlap": round(c["evidence"]["overlap"], 3),
                     "overlap_column": col_name, "new_values": " | ".join(top(new_vals)), "column_values": " | ".join(top(col_vals)),
                     "value_jaccard": jaccard(new_vals, col_vals), "n_new_values": len(set(new_vals)), "n_column_values": len(set(col_vals)),
                     **{f"span{i + 1}": s for i, s in enumerate(spans)}})
    return pd.DataFrame(rows)


def run_set(set_name, runs, out):
    l2 = Path(runs) / set_name / "loop2"
    sug = pd.read_csv(l2 / "suggestions.csv", dtype={"reason": str}, keep_default_na=False)
    seen = set()
    sug["stop"] = [stop_point(r, seen) for r in sug.to_dict("records")]
    clusters = json.loads((l2 / "evidence" / "clusters.json").read_text(encoding="utf-8"))
    finals = json.loads((Path(runs) / set_name / "step3" / "scores" / "final_columns.json").read_text(encoding="utf-8"))[RUN_OF[set_name]]
    mt = pd.read_csv(ROOT / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False,
                     usecols=["mention_id", "norm_value"])
    mentions = dict(zip(mt["mention_id"].astype(int), mt["norm_value"]))
    d = Path(out) / set_name
    d.mkdir(parents=True, exist_ok=True)
    sug[["entity", "name", "votes", "orders", "stop", "reason", "cluster"]].to_csv(d / "loss.csv", index=False, encoding="utf-8", lineterminator="\n")
    overlap_rows(sug, clusters, finals, mentions).to_csv(d / "overlap.csv", index=False, encoding="utf-8", lineterminator="\n")
    sug[sug["stop"] == "vote"][["entity", "name", "votes", "orders", "description"]].to_csv(d / "vote.csv", index=False, encoding="utf-8",
                                                                                           lineterminator="\n")
    return sug


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=str(ROOT / "results" / "wf_v46" / "y3"))
    ap.add_argument("--out", default=str(ROOT / "results" / "wf_v47" / "z1"))
    a = ap.parse_args()
    counts = {s: run_set(s, a.runs, a.out)["stop"].value_counts() for s in RUN_OF}
    lines = [f"# Stop points of the loop-2 suggestions ({Path(a.runs).relative_to(ROOT).as_posix() if Path(a.runs).is_relative_to(ROOT) else a.runs})", "", "| stop point | " + " | ".join(RUN_OF) + " |", "|---|---|---|"]
    lines += [f"| {s} | " + " | ".join(str(counts[k].get(s, 0)) for k in RUN_OF) + " |" for s in STOPS]
    lines += ["| total | " + " | ".join(str(counts[k].sum()) for k in RUN_OF) + " |"]
    p = Path(a.out) / "z1.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
