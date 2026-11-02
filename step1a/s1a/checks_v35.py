"""wf_v3.5 no-LLM checks (GT_V35_CONTRACT.md, W5): T23 noise vote 2 of 3, T26 value types, T35 attribute counts,
T38 extras by GT level. Pure functions of EntityData (ed) and plain DataFrames; no models.

A levels table (gt_levels.csv) has mention_id, gt_L1/L2/L3, ent_L1/L2/L3, is_request, is_choice.
"""

from collections import Counter
from dataclasses import replace
from itertools import combinations

import pandas as pd

from . import pilot_verify as PV
from . import rules_groups as RG
from . import rules_labels as RL
from . import score_rules as SR
from . import step2 as S2
from . import v34_data as VD
from .labels import _classes
from .value_types import value_type_v35  # noqa: F401  (T26; moved to value_types.py, re-exported)

LEVELS = (1, 2, 3)
MAJ = 0.6                                  # share of a group's mentions a label needs to be its majority (= Q5 purity)
WRONG = ("noise", "cue", "wrong_entity")   # mention classes that make a group a wrong extra (plus other_entity:*)
KINDS = ("gt_found", "gt_partial", "extra_L2", "extra_L3", "extra_none", "wrong_extra")
EXTRAS_COLS = ["attr_id", "name", "majority_L1", "majority_L2", "majority_L3", "kind"]
COUNT_COLS = ["attr_id", "name", "n_mentions", "n_dialogues", "n_distinct", "variety", "one_type", "types"]


# ---- T23: noise vote

def noise_vote_2of3(seed_decs, need=2):
    """Series cluster_id -> bool: marked (action in PV.MARKED) in >= `need` of the given orders (C s0/s1/s2 decs)."""
    marked = pd.concat([d.set_index("cluster_id")["action"].isin(PV.MARKED).rename(k) for k, d in seed_decs.items()],
                       axis=1)
    return (marked.fillna(False).astype(int).sum(axis=1) >= need).rename("marked")


def at_level(ed, levels, level):
    """ed read at GT level 1-3 (v34_data.with_level; level 1 too, so choice mentions are noise as in all_variants)."""
    return VD.with_level({ed.ent: ed}, levels, level)[ed.ent]


def _marked_by(dec):
    return set(dec.loc[dec["action"].isin(PV.MARKED), "cluster_id"])


def noise_vote_scores(ed, rules, extra, levels=None, need=2, current="C s012"):
    """One row per level (1 always, 2/3 when `levels` is given) and method (current C vote, 2-of-3 vote):
    noise_n (clusters labelled noise at that level), noise_marked (of them marked), noise_marked_v (share, like the
    scorer), marked_n (clusters marked), marked_<label> (of the marked, by cluster label), precision (marked_noise /
    marked_n). Cluster labels come from rules_labels.cluster_labels under `rules` on the level's mentions."""
    vote = noise_vote_2of3(ed.seed_decs, need)
    methods = {current: _marked_by(ed.variants[current].dec),
               f"{need}of{len(ed.seed_decs)}": set(vote.index[vote])}
    rows = []
    for level in LEVELS if levels is not None else (1,):
        cl = RL.cluster_labels(ed if levels is None else at_level(ed, levels, level), rules, extra)
        label = dict(zip(cl["cluster_id"], cl["label"]))
        noise = {c for c, lab in label.items() if lab == "noise"}
        for method, marked in methods.items():
            marked = marked & set(label)
            by = Counter(label[c] for c in marked)
            rows.append({"ent": ed.ent, "level": level, "method": method, "noise_n": len(noise),
                         "noise_marked": len(noise & marked),
                         "noise_marked_v": len(noise & marked) / len(noise) if noise else float("nan"),
                         "marked_n": len(marked), **{f"marked_{k}": by.get(k, 0) for k in
                                                     ("noise", "real", "mixed", "unknown")},
                         "precision": by.get("noise", 0) / len(marked) if marked else float("nan")})
    return pd.DataFrame(rows)


# ---- T26: value types

def _majority_type(types):
    return sorted(Counter(types).items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def value_type_changes(mentions):
    """mentions: ent, cluster_id, text. Returns (per-cluster DataFrame, summary dict).
    Per cluster: n, type_old / type_new (majority), one_type_old / one_type_new, n_changed (mentions whose type
    differs). Summary: mentions changed, clusters whose majority type changed, and cluster pairs (same entity)
    whose type agreement (equal majority types) changes: gained (differ -> agree), lost (agree -> differ)."""
    t = mentions.assign(old=[S2.value_type(v) for v in mentions["text"]],
                        new=[value_type_v35(v) for v in mentions["text"]])
    rows = []
    for (ent, cid), g in t.groupby(["ent", "cluster_id"], sort=True):
        rows.append({"ent": ent, "cluster_id": cid, "n": len(g), "type_old": _majority_type(g["old"]),
                     "type_new": _majority_type(g["new"]), "one_type_old": g["old"].nunique() == 1,
                     "one_type_new": g["new"].nunique() == 1, "n_changed": int((g["old"] != g["new"]).sum())})
    cl = pd.DataFrame(rows)
    gained = lost = pairs = 0
    for _, g in cl.groupby("ent"):
        for a, b in combinations(g.itertuples(), 2):
            pairs += 1
            before, after = a.type_old == b.type_old, a.type_new == b.type_new
            gained += after and not before
            lost += before and not after
    return cl, {"mentions": len(t), "mentions_changed": int((t["old"] != t["new"]).sum()), "clusters": len(cl),
                "clusters_type_changed": int((cl["type_old"] != cl["type_new"]).sum()), "pairs": pairs,
                "pairs_changed": gained + lost, "pairs_gained": gained, "pairs_lost": lost}


# ---- final attributes of a variant

def _attr_mentions(ed, label):
    """[(attr row, mention rows)] for the final attributes with mentions (status not in PV.MARKED)."""
    vo = ed.variants[label]
    m = ed.mentions.assign(group=[vo.assign.get(int(i), "") for i in ed.mentions["mention_id"]])
    by = {g: s for g, s in m[m["group"] != ""].groupby("group")}
    return [(a, by[a["attr_id"]]) for _, a in vo.attrs.iterrows()
            if a["status"] not in PV.MARKED and a["attr_id"] in by]


# ---- T35: attribute counts

def attr_counts(ed, label):
    """Per final attribute: n_mentions, n_dialogues, n_distinct (norm_value), variety (distinct / mentions), one_type
    (all value_type_v35 equal), types ("type:count;..." most common first)."""
    rows = []
    for a, g in _attr_mentions(ed, label):
        types = Counter(value_type_v35(v) for v in g["text"])
        rows.append({"attr_id": a["attr_id"], "name": a["name"], "n_mentions": len(g),
                     "n_dialogues": g["dialogue_id"].nunique(), "n_distinct": g["norm_value"].nunique(),
                     "variety": g["norm_value"].nunique() / len(g), "one_type": len(types) == 1,
                     "types": ";".join(f"{k}:{v}" for k, v in sorted(types.items(), key=lambda kv: (-kv[1], kv[0])))})
    return pd.DataFrame(rows, columns=COUNT_COLS)


# ---- T38: extras by GT level

def _majority(label_lists, n):
    """Label held by >= MAJ of the n mentions (each list holds one mention's labels), else ""."""
    c = Counter(x for ls in label_lists for x in set(ls))
    if not c:
        return ""
    top, k = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return top if k / n >= MAJ else ""


def _level_view(led, rules, extra):
    """(gold labels, counted flags, classes), all Series indexed by mention_id, of a level copy of the entity.
    Counted = not unlabeled when rules.unlabeled == "exclude" (as the Q5 purity)."""
    cls = RL.mention_class(led, rules, extra)
    gold = pd.Series(list(led.mentions["gold_attr"]), index=cls.index)
    counted = cls != "unlabeled" if rules.unlabeled == "exclude" else pd.Series(True, index=cls.index)
    return gold, counted, cls


def extras_by_level(ed, label, gt_levels, rules=None, extra=None):
    """Per final attribute (not group): majority GT label at L1 / L2 / L3 (>= 60% of its counted mentions at that
    level, unlabeled left out as in the Q5 purity; else "") and kind: gt_found (the attribute is the best group of
    some L1 attr that rules_groups.found counts as found), wrong_extra (>= 60% of its counted mentions are noise /
    cue / wrong_entity / other_entity), gt_partial (an L1 majority, or a majority that is an L1 gold attr, that the Q5
    rule does not count as found), extra_L2 / extra_L3 (no L1 majority; majority at L2 / L3 that is no L1 gold attr),
    extra_none. gt_levels needs the with_level columns (v34_data.read_gt_levels)."""
    rules = rules or SR.Rules.default()
    extra = {} if extra is None else extra
    extra.setdefault("_level", {})
    ex = {**extra, "gt_levels": gt_levels}  # shares the level cache of `extra`
    views = {k: _level_view(SR.level_entity(ed, replace(rules, gt=f"L{k}"), ex), rules, ex) for k in LEVELS}
    fnd = RG.found(SR.level_entity(ed, replace(rules, gt="L1"), ex), label, rules, ex)
    found_groups = set(fnd.loc[fnd["found"], "best_group"])
    gold = set(ed.ctx_r.train)
    rows = []
    for a, g in _attr_mentions(ed, label):
        mid = g["mention_id"].astype(int)
        maj = []
        for k in LEVELS:
            labels, counted, _ = views[k]
            ids = mid[counted.reindex(mid).fillna(False).values]
            maj.append(_majority([_classes(x) for x in labels.reindex(ids)], len(ids)))
        _, counted, cls = views[1]
        cls_c = cls.reindex(mid)[counted.reindex(mid).fillna(False).values]
        wrong = sum(c in WRONG or c.startswith("other_entity") for c in cls_c)
        if a["attr_id"] in found_groups:
            kind = "gt_found"
        elif len(cls_c) and wrong / len(cls_c) >= MAJ:
            kind = "wrong_extra"
        elif maj[0] or maj[1] in gold or maj[2] in gold:
            kind = "gt_partial"
        else:
            kind = "extra_L2" if maj[1] else "extra_L3" if maj[2] else "extra_none"
        rows.append({"attr_id": a["attr_id"], "name": a["name"], "majority_L1": maj[0], "majority_L2": maj[1],
                     "majority_L3": maj[2], "kind": kind})
    return pd.DataFrame(rows, columns=EXTRAS_COLS)


def _extra_key(r):
    """Identity of an attribute inside its entity and variant: its majority label at the kind's level, else its name."""
    level = {"gt_found": "majority_L1", "gt_partial": "majority_L1", "extra_L2": "majority_L2",
             "extra_L3": "majority_L3"}.get(r["kind"])
    return r[level] if level and r[level] else PV.norm_name(r["name"])


def extras_table(rows):
    """Counts per variant x kind of distinct attributes (same entity, variant, kind and key counted once) from rows =
    extras_by_level outputs with ent and variant columns. Columns: KINDS, total."""
    keys = rows.assign(key=[_extra_key(r) for _, r in rows.iterrows()])
    distinct = keys.drop_duplicates(["variant", "ent", "kind", "key"])
    out = distinct.groupby(["variant", "kind"]).size().unstack(fill_value=0).reindex(columns=list(KINDS), fill_value=0)
    out["total"] = out.sum(axis=1)
    return out.reindex(list(dict.fromkeys(rows["variant"])))
