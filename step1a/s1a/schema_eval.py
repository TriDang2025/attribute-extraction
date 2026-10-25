"""Task 8: score a draft schema (s1a/draft_schema.py) against the gold attributes."""
import pandas as pd

from s1a.draft_schema import entities


def _share(hit, n):
    return hit / n if n else float("nan")


def _schema_nodes(schema):
    """{entity: [cluster_id, ...]} of the nodes sitting in each schema entity."""
    return {e: [s["identifier"]["cluster_id"]] + [a["cluster_id"] for a in s["attributes"].values()]
            for e, s in entities(schema).items()}


def evaluate(schema, nodes, labels, mentions, gold_attrs):
    kept = set(nodes.loc[nodes["status"] == "kept", "cluster_id"])
    lab = labels.drop_duplicates("cluster_id").set_index("cluster_id")
    kl = lab[lab.index.isin(kept)]
    gold = kl[kl["label"] == "gold"]
    covered = set(gold["gold_attr"]) & set(gold_attrs)
    real = int(kl["label"].isin(["gold", "valid_new"]).sum())
    labelled = int(kl["label"].isin(["gold", "valid_new", "noise"]).sum())

    # right_entity: entity of a gold node's gold_attr vs majority entity_gold of its schema entity
    ent_gold = mentions[mentions["entity_gold"] != ""]
    hit = n_ent = 0
    for ids in _schema_nodes(schema).values():
        m = ent_gold.loc[ent_gold["cluster_id"].isin(ids), "entity_gold"]
        if m.empty:
            continue
        maj = m.value_counts().idxmax()
        for cid in ids:
            if cid in gold.index:
                n_ent += 1
                hit += gold.loc[cid, "gold_attr"].split()[0].lower() == maj

    def pair_stats(key, same):
        n = ok = 0
        for s in entities(schema).values():
            for h in s[key]:
                a, b = h["nodes"]
                if a in gold.index and b in gold.index:
                    n += 1
                    ok += (gold.loc[a, "gold_attr"] == gold.loc[b, "gold_attr"]) == same
        return ok, n

    mh, mn = pair_stats("merge_hints", True)
    kh, kn = pair_stats("keep_apart", False)
    return {
        "attr_coverage_n": len(covered), "attr_coverage": len(covered) / len(gold_attrs),
        "precision": _share(real, labelled), "precision_n": labelled,
        "K": len(kept), "K_gold": len(gold_attrs),
        "right_entity": _share(hit, n_ent), "right_entity_n": n_ent,
        "merge_precision": _share(mh, mn), "merge_precision_n": mn,
        "role_pairs_correct": _share(kh, kn), "role_pairs_correct_n": kn,
    }


def as_table(results_by_input):
    return pd.DataFrame(results_by_input).T.rename_axis("input")
