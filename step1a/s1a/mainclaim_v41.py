"""wf_v4.1 task 9 (diary): scoring for the main claim. Compare the attribute lists of loop 1, loop 2 and TEAR with the gold L2 attributes
(rules v1.3: 40 attributes on dev50, 41 on dev50b) and list the new attributes (not in the gold list) for a blind human check.

Units: an *item* is one column (loop 1 handover column, TEAR header) or one kept cluster (loop 2); it holds the label lists of its mentions
(gt_L2 per mention, "A;B" = two labels, [] = none), grouped into *groups*, and the mention values.
- Found (loop 1 and loop 2): the rule of rules_groups.found, v1.1 / v1.3 (purity 0.6, coverage 0.10 over the entity's clustered mentions;
  every mention counts in the purity denominator, also an empty one). A group is what A s012 called an attribute group: the member clusters
  of a handover column that share a `members[].group` id (a split part is a group of its own), rebuilt from the column's mention ids. This is
  why the numbers equal STEP3.md (dev50 31/40, dev50b 29/41); the purity of a whole column is lower (28/40, 28/41). A loop-2 cluster is one
  group. Loop 2 = loop 1 groups + the kept loop-2 clusters; its mentions that are already loop-1 mentions (same dialogue, turn and
  normalised value) are not added to the coverage denominator.
- Found (TEAR): a TEAR column whose final label (tear_cols.final_columns) is a gold attribute of its entity (header domain; taxi counts for
  restaurant); TEAR has no groups.
- Gold list per entity: v34_data.level_attrs over gt_L2 (the L1 attributes of the entity plus the L2 attributes with their entity in
  GOLD_ENTS), as ctx.train of the L2 scoring.
- New attribute: an item whose most common label (an empty label counts; ties by name) is empty or is no gold attribute of any entity.
- Loop-2 mention labels: the gt_L2 of the loop-1 mention with the same (dialogue, turn, normalised value), else the (domain, slot) of a
  MultiWOZ 2.2 span with that value in the same dialogue (the cluster's domain first; slot `choice` = none), named as TEAR's attributes
  (gt_ext.slot_name); [] without a spans table.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import gt_ext as G
from . import step4_gt as SG
from . import tear_cols as TC
from . import v34_data as VD

ROOT = Path(__file__).resolve().parents[1]
ENTITIES = SG.ENTITIES
PURITY = 0.6      # rules_groups.PURE
COVERAGE = 0.10   # rules v1.1 "cov10"
STEP3_FOUND = {"dev50": (31, 40), "dev50b": (29, 41)}   # STEP3.md, the exit-bar table of the frozen handover
DOMAIN_ENTITY = {"train": "train", "hotel": "hotel", "restaurant": "restaurant", "taxi": "restaurant"}
SOURCES = ("loop1", "loop2", "tear")
SHEET_COLS = ["row_id", "attribute", "entity", "source", "example_values", "n_mentions", "real"]
KEY_COLS = ["row_id", "source", "entity", "attribute", "majority_gt_L2", "purity", "item_id"]


# ---------------------------------------------------------------- label helpers (pure)
def top_label(label_lists):
    """(label, share) of the most common label over the mentions: every label of a mention counts once, a mention without one counts as ""
    (ties by name; "" ranks like any name). Share = its count / number of mentions; ("", 0.0) for no mention."""
    cnt = Counter(lab for ls in label_lists for lab in (ls or [""]))
    if not cnt:
        return "", 0.0
    lab, k = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return lab, k / len(label_lists)


def totals(label_lists):
    """Counter attr -> number of mentions that carry it."""
    return Counter(lab for ls in label_lists for lab in set(ls))


def found_in_groups(groups, total, gold, purity=PURITY, coverage=COVERAGE):
    """Set of gold attributes found by the groups (lists of mention label lists): purity of the group >= `purity` (over all its mentions) and
    its share of the attribute's total mentions >= `coverage`. `total` = Counter of the entity's mentions per attribute."""
    out = set()
    for g in groups:
        if not g:
            continue
        for attr, k in totals(g).items():
            if attr in gold and k / len(g) >= purity and total[attr] and k / total[attr] >= coverage:
                out.add(attr)
    return out


def gold_lists(gt_levels, l1_attrs):
    """{entity: [gold attribute, ...]}: gt_levels = DataFrame with gt_L2 and ent_L2; l1_attrs = the L1 attribute names of the set
    (gold_attrs.txt). The list of an entity = its L1 attributes (name's first word in GOLD_ENTS[entity]) + v34_data.level_attrs."""
    ments = pd.DataFrame({"gold_attr": gt_levels["gt_L2"].fillna(""), "entity_gold": gt_levels["ent_L2"].fillna("")})
    out = {}
    for ent in ENTITIES:
        ents = VD.GOLD_ENTS[ent]
        first = sorted(a for a in l1_attrs if a.split()[0].lower() in ents)
        out[ent] = VD.level_attrs(ments, ents, first)
    return out


# ---------------------------------------------------------------- items
def item(source, entity, name, item_id, groups, values):
    """An item (see the module doc): groups = [[label list per mention]], values = [value per mention]."""
    return {"source": source, "entity": entity, "name": name, "id": item_id, "groups": groups, "values": values}


def item_labels(it):
    return [ls for g in it["groups"] for ls in g]


def is_new(it, gold_all):
    """(bool, majority label, share): new = the majority label is empty or no gold attribute of any entity."""
    lab, share = top_label(item_labels(it))
    return (not lab or lab not in gold_all), lab, share


def rebuild_groups(column, cluster_of):
    """Groups of a handover column: [[mention ids]]. Member clusters that share a `group` id form a group; two groups that hold the same cluster
    (two parts of a split cluster in one column) are merged; a mention goes to the group of its cluster."""
    groups = []   # [set of clusters]
    for gid in dict.fromkeys(m["group"] for m in column["members"]):
        cl = {m["cluster"] for m in column["members"] if m["group"] == gid}
        for g in [g for g in groups if g & cl]:
            cl |= g
            groups.remove(g)
        groups.append(cl)
    out = [[i for i in column["mention_ids"] if cluster_of.get(i) in g] for g in groups]
    return [ids for ids in out if ids]


def loop1_items(handover, mention_table, labels):
    """Items of the handover columns. handover = {entity: parsed handover file}; mention_table = DataFrame indexed by mention_id with
    cluster_id and norm_value; labels = {mention_id: [gt_L2 labels]}."""
    cluster_of = mention_table["cluster_id"].to_dict()
    out = []
    for ent, doc in handover.items():
        for c in doc["columns"]:
            ids = c["mention_ids"]
            out.append(item("loop1", ent, c["name"], f"{ent}:{c['id']}",
                            [[labels.get(i, []) for i in g] for g in rebuild_groups(c, cluster_of)],
                            [mention_table["norm_value"].get(i, "") for i in ids]))
    return out


def load_set(set_name, root=ROOT):
    """(handover {entity: doc}, mention table, labels {mention_id: [gt_L2]}, gold_by_ent) of a set from the committed files: handover/<set>/,
    results/graph_v22_<set>/{spans/mentions.csv, gold_attrs.txt}, the set's gt_levels.csv (step4_inputs.GT_LEVELS)."""
    from . import step4_inputs as I
    root = Path(root)
    handover = I.load_handover(set_name, root)
    mt = pd.read_csv(root / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False,
                     usecols=["mention_id", "dialogue_id", "turn", "norm_value", "cluster_id", "entity"])
    mt["mention_id"] = mt["mention_id"].astype(int)
    mt["turn"] = mt["turn"].astype(int)
    mt = mt.set_index("mention_id")
    gt = pd.read_csv(root / I.GT_LEVELS[set_name], keep_default_na=False)
    labels = {int(i): [x for x in SG.split_labels(v) if x] for i, v in zip(gt["mention_id"], gt["gt_L2"])}
    l1 = (root / "results" / f"graph_v22_{set_name}" / "gold_attrs.txt").read_text(encoding="utf-8").splitlines()
    return handover, mt, labels, gold_lists(gt, [a for a in l1 if a])


def entity_totals(handover, mention_table, labels):
    """{entity: Counter} over the clustered mentions of the entity (all mentions of the stage-1 entity with a cluster; the columns' mention ids
    plus the mentions of dropped clusters)."""
    out = {}
    for ent, doc in handover.items():
        stage1 = doc["stage1_entity"]
        ids = mention_table.index[(mention_table["entity"] == stage1) & (mention_table["cluster_id"] != "")]
        out[ent] = totals([labels.get(i, []) for i in ids])
    return out


def summarize_loop(source, items, total_by_ent, gold_by_ent):
    """Summary dict of loop-1 / loop-2 items: found per entity (found_in_groups), new items, item count per entity."""
    gold_all = {a for g in gold_by_ent.values() for a in g}
    found = {e: found_in_groups([g for it in items if it["entity"] == e for g in it["groups"]], total_by_ent.get(e, Counter()), set(gold_by_ent[e]))
             for e in gold_by_ent}
    return {"source": source, "found": found, "new": [it for it in items if is_new(it, gold_all)[0]],
            "n_items": dict(Counter(it["entity"] for it in items))}


# ---------------------------------------------------------------- loop 2 (one adapter for the output format)
def read_loop2(path, stage1_to_entity=None):
    """Clusters of a loop-2 clusters.json as [{id, entity, name, keep, mentions: [{dialogue_id, turn, text, norm_value}]}]. Accepts a list or
    {"clusters": [...]}; entity may be an entity name or a stage-1 id (mapped with `stage1_to_entity`); name falls back to label, then id; the
    mention's norm_value falls back to its text. Fails fast on a missing id, entity, keep or mentions."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = doc.get("clusters") if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        raise ValueError(f"{path}: expected a list of clusters or {{'clusters': [...]}}")
    out = []
    for i, c in enumerate(rows):
        miss = [k for k in ("id", "entity", "keep", "mentions") if k not in c]
        if miss:
            raise ValueError(f"{path}: cluster {i} misses {miss}")
        ent = (stage1_to_entity or {}).get(c["entity"], c["entity"])
        ms = [{"dialogue_id": G.dialogue_key(m["dialogue_id"]), "turn": int(m["turn"]), "text": str(m["text"]),
               "norm_value": str(m.get("norm_value") or m["text"]).lower()} for m in c["mentions"]]
        out.append({"id": str(c["id"]), "entity": ent, "name": str(c.get("name") or c.get("label") or c["id"]), "keep": bool(c["keep"]),
                    "mentions": ms})
    return out


def label_mention(m, entity, known, span_idx, tear_map):
    """gt_L2 labels (list) of a loop-2 mention (see the module doc). known = {(dialogue_id, turn, norm_value): labels of a loop-1 mention}."""
    hit = known.get((m["dialogue_id"], m["turn"], m["norm_value"]))
    if hit is not None:
        return list(hit)
    cands = (span_idx or {}).get(m["dialogue_id"], {}).get(G.norm_value(m["text"]), [])
    cands = sorted(cands, key=lambda dc: dc[0] not in (entity, "booking"))   # stable: the entity's own domain first
    if not cands:
        return []
    dom, slot = cands[0]
    if slot == "choice":
        return []
    return [G.slot_name(entity if dom == "booking" else dom, slot, tear_map)]


def known_labels(mention_table, labels):
    """{(dialogue_id, turn, norm_value): labels} of the loop-1 mentions (the first non-empty labels win)."""
    out = {}
    for i, r in zip(mention_table.index, mention_table.itertuples()):
        key = (G.dialogue_key(r.dialogue_id), int(r.turn), str(r.norm_value))
        if not out.get(key):
            out[key] = labels.get(i, [])
    return out


def loop2_items(clusters, known, span_idx, tear_map):
    """(kept items, all-mention label lists per entity [kept or not], n unlabelled loop-2 mentions) of the loop-2 clusters. Only keep == True
    clusters become items; the label lists of every cluster feed the coverage denominator when the mention is not a loop-1 mention."""
    items, extra, unlabeled = [], defaultdict(list), 0
    for c in clusters:
        lab = [label_mention(m, c["entity"], known, span_idx, tear_map) for m in c["mentions"]]
        unlabeled += sum(not ls for ls in lab)
        extra[c["entity"]] += [ls for m, ls in zip(c["mentions"], lab) if (m["dialogue_id"], m["turn"], m["norm_value"]) not in known]
        if c["keep"]:
            items.append(item("loop2", c["entity"], c["name"], c["id"], [lab], [m["norm_value"] for m in c["mentions"]]))
    return items, dict(extra), unlabeled


# ---------------------------------------------------------------- TEAR
def tear_items(cols, values, gold_by_ent):
    """(found {entity: set}, new items, skipped) of the TEAR columns (tear_cols.final_columns DataFrame). values = {header: [cell values]}.
    A column of a domain with no gold entity (attraction) is skipped (counted)."""
    gold_all = {a for g in gold_by_ent.values() for a in g}
    found, new, skipped = {e: set() for e in gold_by_ent}, [], 0
    for r in cols.to_dict("records"):
        ent = DOMAIN_ENTITY.get(r["ent"])
        if ent is None:
            skipped += 1
            continue
        label = r["final_label"] or ""
        if label in gold_by_ent[ent]:
            found[ent].add(label)
        if not label or label not in gold_all:
            vals = values.get(r["column"], [])
            new.append(item("tear", ent, r["column"], r["column"], [[[label] if label else [] for _ in range(int(r["n_cells"]))]], vals))
    return found, new, skipped


def tear_values(rows):
    """{header: [normalised cell values]} of TEAR output rows (tear_cols.tear_cells)."""
    out = defaultdict(list)
    for _, header, spans in TC.tear_cells(rows):
        out[header] += [G.norm_value(s) for s in spans if G.norm_value(s)]
    return dict(out)


# ---------------------------------------------------------------- compare
def compare_rows(set_name, gold_by_ent, summaries):
    """Rows (list of dicts) of compare.csv: per source and entity (and "all") the found count k/n and the new attributes."""
    rows = []
    for s in summaries:
        tot = Counter()
        for ent in [*gold_by_ent, "all"]:
            ents = list(gold_by_ent) if ent == "all" else [ent]
            k = sum(len(s["found"].get(e, set()) & set(gold_by_ent[e])) for e in ents)
            n = sum(len(gold_by_ent[e]) for e in ents)
            new = [it for it in s["new"] if it["entity"] in ents]
            rows.append({"set": set_name, "source": s["source"], "entity": ent, "found_k": k, "gold_n": n, "found_share": k / n if n else None,
                         "items": sum(s["n_items"].get(e, 0) for e in ents), "new_items": len(new),
                         "new_mentions": sum(len(item_labels(it)) for it in new)})
    return rows


def sheet_rows(summaries, gold_all):
    """(sheet DataFrame, key DataFrame) of the new attributes of every source. The sheet has no GT label; the key has the majority label."""
    rows, seen = [], set()
    for s in summaries:
        for it in s["new"]:
            if (it["source"], it["entity"], it["id"]) in seen:   # the loop-2 summary holds the loop-1 items too
                continue
            seen.add((it["source"], it["entity"], it["id"]))
            _, lab, share = is_new(it, gold_all)
            top = [v for v, _ in sorted(Counter(v for v in it["values"] if v).items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
            rows.append({"attribute": it["name"], "entity": it["entity"], "source": it["source"], "example_values": " | ".join(top),
                         "n_mentions": len(item_labels(it)), "real": "", "_lab": lab, "_share": share, "_id": it["id"]})
    rows.sort(key=lambda r: (r["entity"], SOURCES.index(r["source"]), r["attribute"], r["_id"]))
    for i, r in enumerate(rows, 1):
        r["row_id"] = i
    sheet = pd.DataFrame(rows, columns=SHEET_COLS)
    key = pd.DataFrame([{"row_id": r["row_id"], "source": r["source"], "entity": r["entity"], "attribute": r["attribute"],
                         "majority_gt_L2": r["_lab"], "purity": r["_share"], "item_id": r["_id"]} for r in rows], columns=KEY_COLS)
    return sheet, key


def _fmt(k, n):
    return f"{k}/{n} ({k / n:.3f})" if n else f"{k}/0"


def compare_md(set_name, gold_by_ent, summaries, rows, notes):
    """compare.md: the found / new table, the per-attribute matrix and the notes."""
    srcs = [s["source"] for s in summaries]
    by = {(r["source"], r["entity"]): r for r in rows}
    ents = [*gold_by_ent, "all"]
    lines = [f"# wf_v4.1 main claim: attribute lists on {set_name} (gold = L2, rules v1.3)", "",
             "Found = gold attributes found (rules_groups.found: purity 0.6, coverage 0.10); new = items whose majority label is empty or no gold "
             "attribute (to be checked by hand, `human_check_sheet.csv`).", "",
             "| source | " + " | ".join(f"{e} found" for e in ents) + " | new items | new mentions |",
             "|---|" + "---|" * (len(ents) + 2)]
    for s in srcs:
        a = by[(s, "all")]
        lines.append(f"| {s} | " + " | ".join(_fmt(by[(s, e)]["found_k"], by[(s, e)]["gold_n"]) for e in ents) + f" | {a['new_items']} | {a['new_mentions']} |")
    lines += ["", "## Gold attributes found by source", "", "| entity | gold attribute | " + " | ".join(srcs) + " |", "|---|---|" + "---|" * len(srcs)]
    for e, attrs in gold_by_ent.items():
        for a in attrs:
            lines.append(f"| {e} | {a} | " + " | ".join("yes" if a in s["found"].get(e, set()) else "no" for s in summaries) + " |")
    lines += ["", "## Notes", ""] + [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"
