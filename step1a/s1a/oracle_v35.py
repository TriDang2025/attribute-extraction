"""wf_v3.5 T14 / T19 helpers (batch contract: PILOT_V35_BATCH.md). No LLM.

T14 oracle role split: every two-role cluster (roles_v35.two_role_clusters) is split by gold role into `<cid>.a`
(first slot of its pair, e.g. departure) and `<cid>.b` (second slot). Mentions without a role of that pair stay in the
larger part. The export copy has the new cluster ids and cluster table, so the prompt builders run on it unchanged.
T19: how many shown examples of a cluster have each gold role.
"""

import copy

import pandas as pd

from . import mentions as MN
from . import roles_v35 as RV


def split_ids(mentions, gold_role_s, two_role):
    """Series (index of `mentions`) of the oracle cluster id of every mention. `two_role` {cluster_id: pair}
    (roles_v35.two_role_clusters). A mention with role pair[0] goes to `<cid>.a`, pair[1] to `<cid>.b`, any other
    mention to the part with more role mentions (a tie: `.a`). Other clusters keep their id."""
    out = mentions["cluster_id"].copy()
    for cid, pair in two_role.items():
        g = mentions.index[mentions["cluster_id"] == cid]
        roles = gold_role_s.loc[g]
        n = [int((roles == s).sum()) for s in pair]
        rest = "a" if n[0] >= n[1] else "b"
        out.loc[g] = [f"{cid}.{'a' if r == pair[0] else 'b' if r == pair[1] else rest}" for r in roles]
    return out


def oracle_export(export, new_ids):
    """Copy of `export` whose mentions carry `new_ids` (aligned to export.mentions) and whose cluster table has one
    row per new id (rows of unsplit clusters are kept as they were). Vectors, instances and ids are shared."""
    mm = export.mentions.copy()
    old = export.mentions["cluster_id"]
    mm["cluster_id"] = new_ids
    changed = sorted(set(new_ids[new_ids != old]))
    out = copy.copy(export)
    out.mentions = mm
    if not changed:
        out.clusters = export.clusters
        return out
    # cluster_table sorts by "<entity>#<int>": give the new parts temporary integer ids and map them back
    tmp = {c: f"{c.split('#')[0]}#{i}" for i, c in enumerate(changed)}
    sub = mm[mm["cluster_id"].isin(changed)].copy()
    sub["cluster_id"] = sub["cluster_id"].map(tmp)
    table = MN.cluster_table(sub)
    table["cluster_id"] = table["cluster_id"].map({v: k for k, v in tmp.items()})
    split_old = set(old[new_ids != old])
    keep = export.clusters[~export.clusters["cluster_id"].isin(split_old)]
    out.clusters = pd.concat([keep, table], ignore_index=True)
    return out


def oracle_rows(mentions, gold_role_s, new_ids):
    """DataFrame written to oracle_clusters.csv: one row per mention with a cluster."""
    keep = mentions["cluster_id"] != ""
    return pd.DataFrame({"mention_id": mentions.loc[keep, "mention_id"].astype(int),
                         "entity": mentions.loc[keep, "entity"],
                         "orig_cluster_id": mentions.loc[keep, "cluster_id"],
                         "oracle_cluster_id": new_ids[keep], "gold_role": gold_role_s[keep]}).reset_index(drop=True)


def example_role_counts(mentions, example_mids, gold_role_s, two_role):
    """Rows (cluster_id, slot, shown, total) for every two-role cluster that has examples in `example_mids`
    {cluster_id: [mention ids]}: for each slot of its pair, the shown examples and all mentions with that gold role."""
    by_mid = pd.Series(gold_role_s.values, index=mentions["mention_id"].astype(int).values)
    rows = []
    for cid, pair in two_role.items():
        shown = [int(m) for m in example_mids.get(cid, [])]
        total = mentions.loc[mentions["cluster_id"] == cid, "mention_id"].astype(int)
        for s in pair:
            rows.append({"cluster_id": cid, "slot": s, "shown": sum(1 for m in shown if by_mid.get(m) == s),
                         "total": int((by_mid.reindex(total.values) == s).sum())})
    return pd.DataFrame(rows, columns=["cluster_id", "slot", "shown", "total"])


def two_roles(mentions, gold_l2, pairs=None):
    """(gold role Series, {cluster_id: pair}) of the clustered mentions. gold_l2: Series aligned to `mentions` with the
    gt_L2 label ("" without one); the roles come from roles_v35.gold_role, the clusters from two_role_clusters."""
    roles = RV.gold_role(gold_l2.fillna(""), pairs)
    labelled = gold_l2.fillna("") != ""
    clustered = mentions["cluster_id"] != ""
    two = RV.two_role_clusters(mentions[clustered], roles[clustered], labelled[clustered], pairs)
    return roles, two
