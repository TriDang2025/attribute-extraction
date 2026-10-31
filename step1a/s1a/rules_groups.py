"""wf_v3.4 group scoring (SCORER_V34_CONTRACT.md, W4): Q5 found attributes, Q6 merge precision, Q9 placement.

Every function takes ed (v34_data.EntityData), a variant label, rules (score_rules.Rules) and extra (dict of files
read once). Mention classes come from extra["classes"] (Series mention_id -> class) or rules_labels.mention_class;
role pairs from extra["pairs"] / extra["role_pairs"] or rules_labels.role_pairs. No LLM, no models.
"""

from collections import Counter
from dataclasses import replace

import pandas as pd

from . import pilot_score as PS
from .labels import _classes

PURE = 0.6                  # purity needed to call a group a found attribute (same as recall.recall_table strict)
COVERAGE = {"old": 0.0, "cov0": 0.0, "cov10": 0.10, "cov25": 0.25}
NOISE_MAX = {"old": 0.20, "n10": 0.10, "n20": 0.20, "n30": 0.30}  # "old" has no noise rule; n20 is used
NOISE_CLASSES = ("noise", "cue")
FOUND_COLS = ["attr", "found", "best_group", "purity", "coverage", "case"]
MERGE_COLS = ["attr_id", "name", "members", "member_attrs", "member_roles", "noise_share", "right", "reason"]
FOUND_RULES = ("cov0", "cov10", "cov25")
MERGE_RULES = ("n10", "n20", "n30")
Q5_VARIANTS = ("A r1", "B s0", "C s012", "D s012")


# ---- shared inputs

def _classes_of(ed, rules, extra):
    """Series mention_id -> class (rules_labels.mention_class), cached in extra["_classes"] per entity and rules."""
    if "classes" in extra:
        return extra["classes"]
    cache = extra.setdefault("_classes", {})
    key = (ed.ent, rules)
    if key not in cache:
        from . import rules_labels
        cache[key] = rules_labels.mention_class(ed, rules, extra)
    return cache[key]


def _pairs(ed, rules, extra):
    """Role slot pairs as a set of frozensets: extra["pairs"] (tests), else the Q10 config pairs of this entity when
    rules.role_pairs == "config", else the old two (PS.SPLIT_KINDS)."""
    pairs = extra.get("pairs")
    if pairs is None and rules.role_pairs == "config":
        from . import rules_labels
        pairs = rules_labels.role_pairs(entity=ed.ent)
    if pairs is None:
        pairs = PS.SPLIT_KINDS
    return {frozenset(p.lower() for p in pair) for pair in pairs}


def _mentions(ed, label, rules, extra):
    """ed.mentions plus group (attr id of the variant, "" if unassigned), cls (mention class), counted (bool)."""
    m = ed.mentions.copy()
    mid = m["mention_id"].astype(int)
    assign = ed.variants[label].assign
    m["group"] = [assign.get(i, "") for i in mid]
    m["cls"] = _classes_of(ed, rules, extra).reindex(mid).fillna("unlabeled").values
    m["counted"] = (m["cls"] != "unlabeled") if rules.unlabeled == "exclude" else True
    m["golds"] = [_classes(g) for g in m["gold_attr"]]
    return m


def _top(counter):
    """Most common key (ties: name order), "" when empty."""
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if counter else ""


# ---- Q5

def found(ed, label, rules, extra):
    """One row per gold attr of the entity (ctx.train): found = some group has purity >= 0.6 and coverage >= the rule's
    threshold (old = cov0). best_group is that group, else the group with the highest purity. A split part is a group."""
    thr = COVERAGE[rules.found]
    m = _mentions(ed, label, rules, extra)
    m = m[m["group"] != ""]
    size = m[m["counted"]].groupby("group").size().to_dict()
    n_attr = Counter((g, a) for g, golds in zip(m["group"], m["golds"]) for a in set(golds))
    total = Counter(a for golds in m["golds"] for a in set(golds))
    rows = []
    for attr in ed.ctx_r.train:
        cands = [(g, n, n / size[g], n / total[attr]) for (g, a), n in n_attr.items() if a == attr and size.get(g)]
        ok = [c for c in cands if c[2] >= PURE and c[3] >= thr]
        pick = ok or cands
        best = max(pick, key=lambda c: (c[2], c[1], [-ord(ch) for ch in c[0]])) if pick else None
        case = ""
        if cands and not ok:
            pure = [c for c in cands if c[2] >= PURE]
            case = "mixed_only" if not pure else "tiny_pure" if max(c[1] for c in pure) == 1 else "spread"
        rows.append({"attr": attr, "found": bool(ok), "best_group": best[0] if best else "",
                     "purity": best[2] if best else 0.0, "coverage": best[3] if best else 0.0, "case": case})
    return pd.DataFrame(rows, columns=FOUND_COLS)


# ---- Q6

def _merge_reason(tops, slots, pairs, noise, noise_max, no_gold=False):
    if len(tops) > 1:
        names = sorted(tops)
        role = all(frozenset((slots[a], slots[b])) in pairs for i, a in enumerate(names) for b in names[i + 1:])
        return "wrong_role" if role else "wrong_attr"
    if no_gold:  # a member with no gold attr is not "the same attribute"
        return "no_gold_member"
    return "noise" if noise >= noise_max else ""


def merges(ed, label, rules, extra):
    """One row per attribute with mentions from >= 2 clusters (a reconcile part joined to an attribute counts as a
    member cluster). Right = same top gold attr in every member (a member with no gold mention makes it wrong:
    "no_gold_member"), no role-pair mix, and noise share (noise + cue over counted mentions) below the rule's limit."""
    noise_max = NOISE_MAX[rules.merge]
    pairs = _pairs(ed, rules, extra)
    name = ed.variants[label].attrs.set_index("attr_id")["name"].to_dict()
    m = _mentions(ed, label, rules, extra)
    m = m[m["group"] != ""]
    rows = []
    for gid, g in m.groupby("group", sort=True):
        members = sorted(g["cluster_id"].unique())
        if len(members) < 2:
            continue
        tops = {c: _top(Counter(a for golds in s["golds"] for a in golds)) for c, s in g.groupby("cluster_id")}
        slots = {a: PS._slot(a, ed.gold_ents) for a in tops.values() if a}
        counted = g[g["counted"]]
        noise = counted["cls"].isin(NOISE_CLASSES).mean() if len(counted) else 0.0
        reason = _merge_reason({t for t in tops.values() if t}, slots, pairs, noise, noise_max,
                               no_gold=any(t == "" for t in tops.values()))
        rows.append({"attr_id": gid, "name": name.get(gid, ""), "members": ";".join(members),
                     "member_attrs": ";".join(tops[c] for c in members),
                     "member_roles": ";".join(slots.get(tops[c], "") for c in members),
                     "noise_share": float(noise), "right": reason == "", "reason": reason})
    return pd.DataFrame(rows, columns=MERGE_COLS)


# ---- Q9

def _wants(ed):
    """{cluster_id: set of gold entities that make a placement right}: the majority entity_gold of the cluster; for a
    confirmed-reference cluster (one attribute per entity) every entity of its reference mentions."""
    out = {}
    for cid, g in ed.mentions.groupby("cluster_id"):
        golds = [_classes(a) for a in g["gold_attr"]]
        top = _top(Counter(a for gs in golds for a in gs))
        if "reference" in top.lower():
            ents = {e for e, gs in zip(g["entity_gold"], golds) if e and any("reference" in a.lower() for a in gs)}
        else:
            ents = {_top(Counter(e for e in g["entity_gold"] if e))} - {""}
        out[cid] = ents
    return out


def _placement_rows(ed, label):
    """[(cluster_id, placement entity or None, wanted entity set)] for the decision rows that count."""
    ctx = ed.ctx_r
    wants = _wants(ed)
    rows = []
    for _, r in ed.variants[label].dec.iterrows():
        want = wants.get(r["cluster_id"], set())
        if r["action"] == "" or not r["placement"] or not want & set(ctx.entity_gold_of.values()):
            continue  # no predicted entity has this gold entity (e.g. taxi): no right answer
        rows.append((r["cluster_id"], PS.placement_entity(r["placement"], ed.entity), want))
    return rows


def placement(ed, label, rules, extra):
    """dict(place_acc, place_n, place_base): share of decisions whose placement entity is a wanted gold entity (see
    _wants); base = always the current entity. Same rows for both."""
    of = ed.ctx_r.entity_gold_of
    rows = _placement_rows(ed, label)
    n = len(rows)
    ok = sum(e is not None and of.get(e, "") in want for _, e, want in rows)
    base = sum(of.get(ed.entity, "") in want for _, _, want in rows)
    return {"place_acc": ok / n if n else float("nan"), "place_n": n, "place_base": base / n if n else float("nan")}


# ---- report tables

def _variant_rows(data, labels, fn):
    frames = []
    for ent, ed in data.items():
        for label in labels:
            df = fn(ed, label)
            frames.append(df.assign(ent=ent, variant=label))
    out = pd.concat(frames, ignore_index=True)
    return out[["ent", "variant"] + [c for c in out.columns if c not in ("ent", "variant")]]


def q5_table(data, rules, extra, labels=Q5_VARIANTS):
    """Per ent, variant, gold attr: best group, purity, coverage and found / case under cov0, cov10, cov25."""
    def one(ed, label):
        runs = {r: found(ed, label, replace(rules, found=r), extra) for r in FOUND_RULES}
        base = runs["cov0"][["attr", "best_group", "purity", "coverage"]]
        for r, df in runs.items():
            base = base.assign(**{f"found_{r}": df["found"].values, f"case_{r}": df["case"].values})
        return base
    return _variant_rows(data, labels, one)


def q6_table(data, rules, extra, labels=Q5_VARIANTS):
    """Every merged attribute with its verdict under rules.merge, per ent and variant."""
    return _variant_rows(data, labels, lambda ed, label: merges(ed, label, rules, extra))


def q9_table(data):
    """Per cluster with a mention whose gold entity differs from the entity's own: n, n_other, share_other, the
    majority entity_gold and the top gold attr of the other-entity mentions."""
    rows = []
    for ent, ed in data.items():
        own = set(ed.gold_ents)
        for cid, g in ed.mentions.groupby("cluster_id"):
            other = g[(g["entity_gold"] != "") & ~g["entity_gold"].isin(own)]
            if len(other):
                rows.append({"ent": ent, "cluster_id": cid, "n": len(g), "n_other": len(other),
                             "share_other": len(other) / len(g),
                             "majority_entity": _top(Counter(e for e in g["entity_gold"] if e)),
                             "top_other_attr": _top(Counter(a for v in other["gold_attr"] for a in _classes(v)))})
    return pd.DataFrame(rows, columns=["ent", "cluster_id", "n", "n_other", "share_other", "majority_entity",
                                       "top_other_attr"])
