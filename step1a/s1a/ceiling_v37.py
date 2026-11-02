"""wf_v3.7 T1: what Step 1a makes recoverable (ceiling) and where each missed attribute is lost (loss table).
WF_V37_CONTRACT.md, W1. No models, no LLM; pure functions of EntityData, so the same code runs on dev50 and dev50b.

Ceiling: the found rule of rules v1 (`rules_groups.found`: purity >= 0.6 and coverage >= 10%) applied to "identity
decisions", i.e. a variant in which every Step-1a cluster is its own attribute and nothing is marked. A base attribute
is recoverable when some single cluster passes the rule. Nothing of the rule is re-implemented here.

`ceiling_table(entity_data, gt_level)`: `entity_data` = {ent: EntityData} already read at the GT level
(`v34_data.with_level`; `ceiling_for(data, gt, level)` does that step). The EntityData needs no variants: only
mentions with cluster ids, the level labels and `ctx_r.train` (the level's base attributes).
"""

from collections import Counter
from dataclasses import replace

import pandas as pd

from . import pilot_score as PS
from . import pilot_verify as PV
from . import rules_groups as RG
from . import score_rules as SR
from . import v34_data as VD

IDENTITY = "identity"
REASONS = ("never_found", "mixed_roles", "diluted")
CEILING_COLS = ["ent", "attr", "present", "recoverable", "best_cluster", "best_purity", "best_coverage", "n_mentions",
                "case", "top_other", "step1a_reason"]
LOSS_COLS = ["ent", "attr", "variant", "order", "found", "stage", "reason", "best_cluster", "group", "group_name",
             "group_purity", "top_other", "missed_orders", "missed_k"]
STEP1A, STEP3 = "Step 1a", "Step 3"


def rules_v11(level=2):
    """Rules v1.1 at GT level `level` (the setting of every v3.7 table)."""
    return replace(SR.Rules.v1_1(), gt=f"L{level}")


def identity_variant(ed):
    """VariantOut with every cluster of the entity as its own attribute (attr_id = cluster id), status keep, no
    decision rows: the input that makes `rules_groups.found` measure the clusters alone."""
    cids = sorted(c for c in ed.mentions["cluster_id"].unique() if c)
    attrs = pd.DataFrame({"attr_id": cids, "name": cids, "clusters": cids, "status": "keep", "source": "keep",
                          "description": ""})
    assign = {int(m): c for m, c in zip(ed.mentions["mention_id"], ed.mentions["cluster_id"]) if c}
    return VD.VariantOut(pd.DataFrame(columns=PV.DEC_COLS), attrs, assign, {})


def _top_other(golds, attr):
    """Most common attribute other than `attr` in a list of per-mention gold lists ("" when none)."""
    c = Counter(a for g in golds for a in set(g) if a != attr)
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if c else ""


def _is_role_partner(ed, attr, other, rules, extra):
    """True when the slots of `attr` and `other` are the two slots of a role pair (config/role_pairs.json)."""
    if not other:
        return False
    slot = lambda a: PS._slot(a, ed.gold_ents)  # noqa: E731
    return frozenset((slot(attr), slot(other))) in RG._pairs(ed, rules, extra)


def ceiling_table(entity_data, gt_level, rules=None, extra=None):
    """One row per base attribute (ctx_r.train at the level) of every entity: ent, attr, present (a mention with that
    label sits in a cluster of the entity), recoverable (some cluster passes the found rule), best_cluster,
    best_purity, best_coverage (of the best cluster), n_mentions (clustered mentions with the label), case
    (rules_groups.found's case for a non-recoverable attribute), top_other (the best cluster's most common other
    attribute) and step1a_reason for a non-recoverable one: never_found (no mention carries it), mixed_roles (the best
    cluster's top other attribute is the role partner) or diluted (anything else)."""
    rules = rules or rules_v11(gt_level)
    extra = {} if extra is None else extra
    rows = []
    for ent, ed in entity_data.items():
        if ed.level != gt_level:
            raise ValueError(f"{ent}: entity data is at GT level {ed.level}, expected {gt_level} (use ceiling_for)")
        ident = replace(ed, variants={IDENTITY: identity_variant(ed)})
        fnd = RG.found(ident, IDENTITY, rules, extra).set_index("attr")
        m = RG._mentions(ident, IDENTITY, rules, extra)
        m = m[m["group"] != ""]
        count = Counter(a for golds in m["golds"] for a in set(golds))
        for attr in ed.ctx_r.train:
            f = fnd.loc[attr]
            present, rec = count[attr] > 0, bool(f["found"])
            best = f["best_group"]
            top = _top_other(m.loc[m["group"] == best, "golds"], attr) if best else ""
            reason = ""
            if not rec:
                reason = "never_found" if not present else "mixed_roles" if _is_role_partner(ed, attr, top, rules, extra) \
                    else "diluted"
            rows.append({"ent": ent, "attr": attr, "present": present, "recoverable": rec, "best_cluster": best,
                         "best_purity": f["purity"], "best_coverage": f["coverage"], "n_mentions": count[attr],
                         "case": f["case"], "top_other": top, "step1a_reason": reason})
    return pd.DataFrame(rows, columns=CEILING_COLS)


def ceiling_for(data, gt, level=2, rules=None, extra=None):
    """ceiling_table of `data` ({ent: EntityData} as loaded) read at GT level `level` (gt = read_gt_levels table)."""
    return ceiling_table(VD.with_level(data, gt, level), level, rules, extra)


def ceiling_counts(ceil):
    """DataFrame per entity plus a total row: n (base attributes), present, recoverable, and the Step-1a reasons."""
    rows = []
    for ent, g in list(ceil.groupby("ent", sort=False)) + [("total", ceil)]:
        rows.append({"ent": ent, "n": len(g), "present": int(g["present"].sum()), "recoverable": int(g["recoverable"].sum()),
                     **{r: int((g["step1a_reason"] == r).sum()) for r in REASONS}})
    return pd.DataFrame(rows)


# ---- loss table

def _step3_reason(ed, label, best, attr, rules, extra):
    """(reason, group id, group name, group purity for attr, top other) of the Step-3 loss of `attr`: the variant's
    handling of its best recoverable cluster `best`. marked_not_attribute: the cluster's group is marked; not_in_response:
    the decision table has no row for it; split: the group is a split part; mixed_roles: the group's purity fails and its
    top other attribute is the role partner; merged_wrongly: purity fails for any other reason; other: nothing fails."""
    vo = ed.variants[label]
    m = RG._mentions(ed, label, rules, extra)
    mine = m[(m["cluster_id"] == best) & (m["group"] != "")]
    if not len(mine):
        return "not_in_response", "", "", float("nan"), ""
    gid = mine["group"].value_counts().idxmax()
    a = vo.attrs[vo.attrs["attr_id"] == gid].iloc[0]
    g = m[(m["group"] == gid) & m["counted"]]
    pur = sum(attr in set(x) for x in g["golds"]) / len(g) if len(g) else float("nan")
    top = _top_other(g["golds"], attr)
    if a["status"] in PV.MARKED:
        reason = "marked_not_attribute"
    elif a["status"] == "missing":
        reason = "not_in_response"
    elif a["source"] == "split":
        reason = "split"
    elif pur < RG.PURE:
        reason = "mixed_roles" if _is_role_partner(ed, attr, top, rules, extra) else "merged_wrongly"
    else:
        reason = "other"
    return reason, gid, a["name"], pur, top


def loss_table(entity_data, ceil, variants, rules=None, extra=None):
    """One row per (attribute, variant) of every attribute that some variant of `variants` (the A orders, in order 0 / 1
    / 2) does not find: ent, attr, variant, order, found, stage ("" when found), reason, best_cluster, group, group_name,
    group_purity, top_other, missed_orders ("k/n") and missed_k. A missed attribute is stage "Step 1a" when it is not
    recoverable (reason as in the ceiling table) and "Step 3" when it is (reason from _step3_reason, on the best
    recoverable cluster: other recoverable clusters of the same attribute are not looked at). `entity_data` is read at
    the level of `ceil`."""
    rules = rules or rules_v11(next(iter(entity_data.values())).level)
    extra = {} if extra is None else extra
    rows = []
    for ent, ed in entity_data.items():
        c = ceil[ceil["ent"] == ent].set_index("attr")
        per = {v: RG.found(ed, v, rules, extra).set_index("attr")["found"] for v in variants if v in ed.variants}
        for attr in c.index:
            miss = [v for v in per if not per[v][attr]]
            if not miss:
                continue
            for order, v in enumerate(per):
                r = {"ent": ent, "attr": attr, "variant": v, "order": order, "found": bool(per[v][attr]), "stage": "",
                     "reason": "", "best_cluster": c.loc[attr, "best_cluster"], "group": "", "group_name": "",
                     "group_purity": float("nan"), "top_other": "", "missed_orders": f"{len(miss)}/{len(per)}",
                     "missed_k": len(miss)}
                if v in miss and not c.loc[attr, "recoverable"]:
                    r.update(stage=STEP1A, reason=c.loc[attr, "step1a_reason"], top_other=c.loc[attr, "top_other"])
                elif v in miss:
                    reason, gid, name, pur, top = _step3_reason(ed, v, c.loc[attr, "best_cluster"], attr, rules, extra)
                    r.update(stage=STEP3, reason=reason, group=gid, group_name=name, group_purity=pur, top_other=top)
                rows.append(r)
    return pd.DataFrame(rows, columns=LOSS_COLS)


# ---- markdown

def ceiling_md(ceil, title="wf_v3.7 Step 1a ceiling at L2", set_name="dev50"):
    counts = ceiling_counts(ceil)
    tot = counts[counts["ent"] == "total"].iloc[0]
    lines = [f"# {title}", "",
             f"Set: {set_name}. Base = the L2 base attributes of each entity (ctx.train at L2: the L1 attributes plus the "
             "MultiWOZ 2.2 slots that occur in the set). **present** = some mention with that label is in a Step-1a cluster "
             "of the entity. **recoverable** = some single cluster passes the found rule of rules v1 (purity >= 0.6 and "
             "coverage >= 10%); measured by scoring identity decisions (every cluster its own attribute, nothing marked) "
             "through `rules_groups.found`, with the v1.1 mention classes. Reasons for a non-recoverable attribute: "
             "never_found (no mention carries it), mixed_roles (the best cluster's top other attribute is its role "
             "partner), diluted (anything else).", "",
             "| entity | base | present | recoverable | never_found | mixed_roles | diluted |", "|---|---|---|---|---|---|---|"]
    for _, r in counts.iterrows():
        lines.append(f"| {r['ent']} | {r['n']} | {SR.fmt_count(r['present'], r['n'])} | "
                     f"{SR.fmt_count(r['recoverable'], r['n'])} | {r['never_found']} | {r['mixed_roles']} | {r['diluted']} |")
    lines += ["", f"Total: present {SR.fmt_count(tot['present'], tot['n'])}, recoverable "
              f"{SR.fmt_count(tot['recoverable'], tot['n'])}.", "", "## Non-recoverable attributes", "",
              "| ent | attribute | present | reason | best cluster | purity | coverage | top other attribute |",
              "|---|---|---|---|---|---|---|---|"]
    for _, r in ceil[~ceil["recoverable"]].iterrows():
        lines.append(f"| {r['ent']} | {r['attr']} | {r['present']} | {r['step1a_reason']} | {r['best_cluster'] or '-'} | "
                     f"{r['best_purity']:.2f} | {r['best_coverage']:.2f} | {r['top_other'] or '-'} |")
    return "\n".join(lines) + "\n"


def loss_md(loss, variants, ceil, set_name="dev50"):
    lines = ["# wf_v3.7 loss table: where A loses each missed attribute (L2)", "",
             f"Set: {set_name}. Orders: " + ", ".join(f"{v} = order {i}" for i, v in enumerate(variants)) + ". An attribute "
             "A does not find in an order is lost at **Step 1a** when no cluster makes it recoverable (reason as in the "
             "ceiling table) and at **Step 3** when some cluster does (the best one is followed): marked_not_attribute "
             "(its group is marked), merged_wrongly (its group's purity fails because of a merge), mixed_roles (merged with "
             "the role partner), split (its group is a split part), not_in_response (A gave the cluster no decision), other.",
             "", "## Stage and reason per order (attribute-orders)", "", "| variant | missed | Step 1a | Step 3 | reasons |",
             "|---|---|---|---|---|"]
    for v in variants:
        g = loss[(loss["variant"] == v) & ~loss["found"]]
        why = Counter(f"{r['stage']}: {r['reason']}" for _, r in g.iterrows())
        lines.append(f"| {v} | {len(g)} | {int((g['stage'] == STEP1A).sum())} | {int((g['stage'] == STEP3).sum())} | "
                     + "; ".join(f"{k} {n}" for k, n in sorted(why.items())) + " |")
    lines += ["", "## Attributes missed in at least one order", "", "| ent | attribute | missed | "
              + " | ".join(variants) + " |", "|---|---|---|" + "---|" * len(variants)]
    for (ent, attr), g in loss.groupby(["ent", "attr"], sort=False):
        cell = lambda v: (lambda r: "found" if r["found"] else f"{r['stage']}: {r['reason']}")(  # noqa: E731
            g[g["variant"] == v].iloc[0])
        lines.append(f"| {ent} | {attr} | {g['missed_orders'].iloc[0]} | " + " | ".join(cell(v) for v in variants) + " |")
    n3 = loss[(loss["stage"] == STEP3)]
    lines += ["", f"Attributes with a Step-3 loss in at least one order: {n3.groupby(['ent', 'attr']).ngroups}; "
              f"all missed attributes: {loss.groupby(['ent', 'attr']).ngroups}; recoverable at Step 1a: "
              f"{int(ceil['recoverable'].sum())}/{len(ceil)}."]
    return "\n".join(lines) + "\n"
