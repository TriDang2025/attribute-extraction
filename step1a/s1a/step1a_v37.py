"""wf_v3.7 T9/T13: recall of a Step 1a run at GT level 2 and the summary of the J split (pure functions, no models).

L2 recall = recall.recall_table's strict / recoverable / present, with the L2 label of a mention (gt_levels gt_L2) as its
class and the clustered mentions with that label as its "inside" count (the L2 labels sit on mentions, not on a separate
gold-value list, so a value GLiNER missed has no L2 row). strict: some cluster has purity >= 0.6; recoverable: strict, or
>= 2 labelled mentions inside clusters and purity >= 0.25; present: >= 1 labelled mention inside a cluster.
"""

from collections import Counter

import pandas as pd

from . import recall as RC


def with_l2(mentions, gt):
    """`mentions` with gold_attr = gt_L2 of each mention_id (gt: gt_levels table; no row = no label)."""
    g = gt.drop_duplicates("mention_id")
    by = g.set_index(g["mention_id"].astype(int))["gt_L2"]
    return mentions.assign(gold_attr=mentions["mention_id"].astype(int).map(by).fillna("").astype(str))


def recall_l2(mentions, gt, attrs):
    """(table, summary) of the L2 recall of `attrs` (list of L2 class names) for a run's mentions."""
    m = with_l2(mentions, gt)
    cls, size, _ = RC._counts(m)
    inside = cls.groupby("gold_attr")["n"].sum()
    tab = RC._table(RC.purity_table(m), inside, attrs, 0.6, 0.25, 2)
    return tab, RC.summary(m, tab)


def same_spans(a, b):
    """True when two runs' mention tables hold the same spans in the same order (so one gt_levels table fits both)."""
    key = ["mention_id", "dialogue_id", "turn", "char_start", "char_end"]
    return a[key].astype(str).reset_index(drop=True).equals(b[key].astype(str).reset_index(drop=True))


def j_split_summary(stats, mentions, gt=None):
    """One row per J-split cluster: entity, the cluster ids of its start / end / unknown parts in `mentions` (the v2.3
    export, in that order), n, part sizes and learned words; with `gt` (gt_levels) also the L2 labels of each part
    ("start: Train departure 3, ...; end: ..."; "-" = no label) to see whether the split follows the roles.
    stats = combos23.LAST_SPLIT (read from j_split.json)."""
    l2 = with_l2(mentions, gt).set_index(mentions["mention_id"].astype(int))["gold_attr"] if gt is not None else None
    cid = mentions.set_index(mentions["mention_id"].astype(int))["cluster_id"]
    ent = mentions.set_index(mentions["mention_id"].astype(int))["entity"]
    rows = []
    for s in stats:
        parts = {p: sorted({cid[i] for i, q in zip(s["members"], s["parts"]) if q == p and cid[i]}) for p in (0, 1, 2)}
        row = {"entity": ent[s["members"][0]], "n": s["n"], "start": s["start"], "end": s["end"],
               "unknown": s["unknown"], "clusters": ";".join(sum(parts.values(), [])), "learned": ";".join(s["learned"])}
        if l2 is not None:
            row["l2_labels"] = "; ".join(
                f"{name}: " + ", ".join(f"{k} {v}" for k, v in Counter(l2[i] or "-" for i, q in zip(s["members"], s["parts"])
                                                                    if q == p).most_common())
                for p, name in enumerate(("start", "end", "unknown")) if p in s["parts"])
        rows.append(row)
    return pd.DataFrame(rows)
