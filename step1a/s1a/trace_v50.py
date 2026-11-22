"""wf_v5.0 G2: where is each missed gold attribute lost? Pure functions over the mention labels (gt_L2) and the group lists of each
pipeline checkpoint; the found rule is the scorer's own (mainclaim_v41.found_in_groups: purity >= 0.6, coverage >= 0.10 of the entity's
clustered mentions of the attribute). Gold is used only to trace, never fed back.

Checkpoints of the scored entity (the stage-1 entity mapped to the attribute's gold entity), in pipeline order:
  clusters  Step 1a clusters (mentions.csv cluster_id)                       fail -> S3 (mixed / diluted cluster)
  split     split parts of split clusters + unsplit clusters (columns.json)  fail -> S3 (the split mixed it)
  columns   Step 3 named columns (columns.json: names, not_attribute, rescue, merge)
            fail -> S4/S5 when the best split group's mentions are in no column (dropped), else S6 (joined)
  final     scorer groups of the final columns (reconcile + duplicate check) fail -> S6
  scorer    found by the scorer                                              fail -> S9
Before the checkpoints: no pipeline mention -> S2; most mentions in another stage-1 entity -> S1.
Loop 2 (separate column, only for attributes lost in loop 1): S7 never suggested, S8 suggested but failed (stage + reason), "added" =
suggested and kept but still not credited.
"""

from collections import Counter

from . import mainclaim_v41 as MC

CHECKPOINTS = ("clusters", "split", "columns", "final")
STOP_OF = {"clusters": "S3", "split": "S3", "final": "S6"}
S1_SHARE = 0.5   # S1 when less than this share of the attribute's clustered mentions sit in the scored entity


def best(groups, attr, total):
    """(passes, purity, coverage, index) of the group with the most mentions of `attr` (ties: higher purity)."""
    top = (False, 0.0, 0.0, -1)
    for i, g in enumerate(groups):
        k = sum(attr in ls for ls in g)
        if not k:
            continue
        pur, cov = k / len(g), (k / total if total else 0.0)
        ok = pur >= MC.PURITY and cov >= MC.COVERAGE
        cand = (ok, round(pur, 3), round(cov, 3), i)
        if (cand[0], cov, pur) > (top[0], top[2], top[1]):
            top = cand
    return top


def ids_groups_clusters(mt, entity):
    """{cluster id: [mention ids]} of a stage-1 entity (mt: DataFrame indexed by mention_id with entity, cluster_id)."""
    sub = mt[(mt["entity"] == entity) & (mt["cluster_id"] != "")]
    return {c: list(ix) for c, ix in sub.groupby("cluster_id").groups.items()}


def ids_groups_split(clusters, parts):
    """Split parts (columns.json parts: pid, cluster, mention_ids) plus the clusters that were not split."""
    split = {p["cluster"] for p in parts}
    out = {p["pid"]: [int(i) for i in p["mention_ids"]] for p in parts}
    out.update({c: ids for c, ids in clusters.items() if c not in split})
    return out


def ids_groups_columns(columns, split_groups):
    """One group per column group string ("E1#8/1", "E1#19|E1#23"): the union of its parts / clusters."""
    out = {}
    for col in columns:
        for g in col["groups"]:
            out[f"{col['name']}:{g}"] = [i for t in g.split("|") for i in split_groups.get(t, [])]
    return out


def as_labels(id_groups, labels):
    keys = list(id_groups)
    return keys, [[labels.get(i, []) for i in id_groups[k]] for k in keys]


def entity_share(mt, labels, attr, entity):
    """(share of the attribute's clustered mentions in `entity`, Counter over stage-1 entities)."""
    sub = mt[mt["cluster_id"] != ""]
    cnt = Counter(e for i, e in zip(sub.index, sub["entity"]) if attr in labels.get(i, []))
    n = sum(cnt.values())
    return (cnt.get(entity, 0) / n if n else 0.0), cnt


def trace(attr, entity, checkpoints, labels, total, found):
    """Row dict: the best group at each checkpoint and the first stop point. checkpoints = {name: {group key: [mention ids]}}."""
    row, stop, prev_ids = {}, "", None
    for cp in CHECKPOINTS:
        keys, groups = as_labels(checkpoints[cp], labels)
        ok, pur, cov, i = best(groups, attr, total)
        row[f"{cp}_best"] = f"{keys[i]} p{pur:.2f} c{cov:.2f}" if i >= 0 else "-"
        row[f"{cp}_ok"] = ok
        if not ok and cp == "columns" and prev_ids is not None:
            in_cols = {m for ids in checkpoints["columns"].values() for m in ids}
            row["columns_kept_share"] = round(sum(m in in_cols for m in prev_ids) / len(prev_ids), 2)
        if not ok and not stop:
            if cp == "columns" and prev_ids is not None:
                stop = "S4/S5" if row["columns_kept_share"] < 0.5 else "S6"
            else:
                stop = STOP_OF[cp]
        if ok and i >= 0:
            prev_ids = checkpoints[cp][keys[i]]
    if not stop:
        stop = "S9" if attr not in found else ""
    row["stop"] = stop
    row["stop_last"] = last_loss(row, stop)
    return row


def last_loss(row, stop):
    """Stop point of the checkpoint right after the last one that passed (the split can rescue a cluster that a later step loses again);
    the first stop when nothing passed."""
    oks = [cp for cp in CHECKPOINTS if row.get(f"{cp}_ok")]
    if not oks:
        return stop
    nxt = CHECKPOINTS.index(oks[-1]) + 1
    if nxt == len(CHECKPOINTS):
        return stop if stop == "S9" else ""
    cp = CHECKPOINTS[nxt]
    return ("S4/S5" if row.get("columns_kept_share", 1) < 0.5 else "S6") if cp == "columns" else STOP_OF[cp]


def loop2_status(attr, gold_entity, suggestions, gold_by_ent, cfg):
    """(S7 | S8 | added, detail) from the loop-2 suggestions of the gold entity (rows with gt_entity, name, passed, stage, reason)."""
    hits = [s for s in suggestions if s["gt_entity"] == gold_entity and MC.name_match(s["name"], gold_entity, gold_by_ent, cfg) == attr]
    if not hits:
        return "S7", ""
    kept = [s for s in hits if s["passed"]]
    s = (kept or hits)[0]
    return ("added" if kept else "S8"), f"{s['name']}: {s['stage']} ({s['reason']})"
