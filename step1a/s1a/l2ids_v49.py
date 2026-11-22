"""wf_v4.9 V1: make the loop-2 columns scorable in the Step 4 scorer (scoring only, no gold in any fix).

Cause: loop-2 mention ids continue after the loop-1 mention table (loop2_v46.run_evidence, next_id = max + 1), but gt_levels only cover the
loop-1 ids, and step4_gt.map_handover keeps only ids in the gt_levels index, so a loop-2 column got no GT label (and gpu_v48.prepare gave
it mention_ids []). Fix: every loop-2 mention gets the string id "L2_<mention id>", labelled by mainclaim_v41.label_mention (the gt_L2 of the
loop-1 mention with the same dialogue / turn / value, else the MultiWOZ 2.2 span with that value); the labels extend the gt_L2 Series and the
loop-2 columns of the score map carry the L2_ ids. Second view: a loop-2 column without a span label takes the gold attribute that the W1
human check (human_check_key name_match of its clusters) gave it.
"""
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from . import mainclaim_v41 as M
from . import step4_gt as G


def l2_id(mention_id):
    return f"L2_{int(mention_id)}"


def loop2_columns(merged):
    """{"<entity>:<cid>": column row} of the loop-2 columns of a merged_columns.json ({entity: rows}); rows carry clusters and mention_ids."""
    return {f"{e}:{r['cid']}": r for e, rows in merged.items() for r in rows if r["source"] == "loop2"}


def column_ids(cols):
    """{column key: [L2_ ids]} of loop2_columns."""
    return {k: [l2_id(i) for i in r["mention_ids"]] for k, r in cols.items()}


def loop2_labels(clusters_file, entity_of, known, span_idx, tear_map):
    """{mention_id: gt_L2 label list} of every mention of the loop-2 evidence clusters (mainclaim_v41.label_mention). entity_of = {run entity:
    GT entity} (the cluster's domain for the span lookup; mainclaim_v41.read_loop2 maps it). known as mainclaim_v41.known_labels."""
    doc = json.loads(Path(clusters_file).read_text(encoding="utf-8"))
    raw = doc.get("clusters") if isinstance(doc, dict) else doc
    out = {}
    for rc, c in zip(raw, M.read_loop2(clusters_file, entity_of)):   # same order, same mention order
        for rm, m in zip(rc["mentions"], c["mentions"]):
            out[int(rm["mention_id"])] = M.label_mention(m, c["entity"], known, span_idx, tear_map)
    return out


def extend(gt_l2, labels, cols):
    """gt_L2 Series (mention_id -> "A;B") + one L2_<id> entry per mention of the loop-2 columns (labels {mention_id: [labels]}; none = "")."""
    ids = sorted({int(i) for r in cols.values() for i in r["mention_ids"]})
    ext = pd.Series([";".join(labels.get(i, [])) for i in ids], index=[l2_id(i) for i in ids], dtype=object)
    return pd.concat([gt_l2.astype(object), ext])


def fallback(cols, key_rows, names):
    """{column key: GT attribute} from the human-check key rows (dicts with source, item_id, name_match): the most common non-empty name_match
    of the column's loop-2 clusters (ties by name), written as the GT name (names {norm: GT name}). Columns without one are left out."""
    nm = {r["item_id"]: r["name_match"] for r in key_rows if r["source"] == "loop2" and r["name_match"]}
    out = {}
    for k, r in cols.items():
        cnt = Counter(nm[c] for c in r["clusters"] if c in nm)
        if cnt:
            top = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            out[k] = names.get(G.norm(top), top)
    return out


def apply_fallback(mapping, override):
    """New mapping where each column of `override` that has no GT label (gt None) takes the override attribute (purity 1)."""
    out = dict(mapping)
    for k, name in override.items():
        m = out.get(k)
        if m is not None and m["gt"] is None:
            out[k] = {**m, "gt": name, "purity": 1.0, "labels": {name: m["n"]}, "n_labelled": m["n"]}
    return out
