"""wf_v3.8 scoring of the Colab batch (tasks 7-11, contract WF_V38_BATCH.md, rules RULES_V1_2.md): pure functions, no I/O.

- answer_check / yes_no / counts_by_source: step 0 and the yes counts of an evidence answer list.
- union_joins / join_base / join_columns / renamed_attrs / marked_attrs: the dupcheck joins after the code check, the pooled
  column and the variants (joined; columns marked out) that the dashboard row builder reads.
- join_right: is a join right by the GT (same L2 attribute and same role).
- neighbour_evidence / pooled_support / verdict: the evidence card (support, neighbour fit, mixed roles) and verdict rule v0.
- gt_kinds / checker_table / filter_decision: task 11.
"""

from collections import Counter

import pandas as pd

from . import batch_v38 as BT
from . import role_guard as RGD

SUPPORT_NOISE = 0.4     # verdict rule v0, fixed before scoring (RULES_V1_2.md)
FIT_GENERAL = 0.5
SUPPORT_REAL = 0.7
FIT_REAL = 0.3
NEIGHBOUR_YES = 0.6     # a neighbour "fits" the column when >= 3/5 of its examples do (share form, for fewer examples)
PARTNER_MAX = 0.2       # same role: share of labelled mentions in the role-partner slot (dashboard_v38.PARTNER_MAX)
VERDICTS = ("real", "unsure", "noise", "too general", "mixed roles")
REJECTED = ("noise", "too general")   # the filter set; "mixed roles" is reported next to it
GT_KINDS = ("gt", "duplicate", "wrong", "no_gt")
JOIN_STATUS = ("right", "wrong", "no_gt")
YES, NO = "yes", "no"


# ---- step 0 and answers

def answer_check(expected, parsed):
    """dict(expected, answered, missing, extra, repeated) for one evidence job: `expected` = example ids of its prompt,
    `parsed` = the response's parsed object. Missing = unanswered (never counted as "no")."""
    ids = [a["id"] for a in (parsed or {}).get("answers", [])]
    seen = Counter(ids)
    exp = set(expected)
    return {"expected": len(exp), "answered": len(exp & set(ids)), "missing": sorted(exp - set(ids)),
            "extra": sorted(set(ids) - exp), "repeated": sorted(i for i, n in seen.items() if n > 1)}


def yes_no(parsed, expected=None):
    """{example id: bool} (fits == yes); ids outside `expected` (when given) are left out; a repeated id keeps its first answer."""
    out = {}
    for a in (parsed or {}).get("answers", []):
        if (expected is None or a["id"] in expected) and a["id"] not in out:
            out[a["id"]] = a["fits"] == YES
    return out


def counts_by_source(answers, source_of):
    """{source column: (yes, answered)} of one neighbour job: `answers` {example id: bool}, `source_of` {example id: source}."""
    out = {}
    for i, fits in answers.items():
        y, n = out.get(source_of[i], (0, 0))
        out[source_of[i]] = (y + int(fits), n + 1)
    return out


def share(yes, n):
    return yes / n if n else None


# ---- joins

def union_joins(joins):
    """Transitive closure of joins ([{"columns": [ids]}]): a list of sorted id lists (>= 2 ids), ordered by first id."""
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for j in joins:
        ids = list(j["columns"])
        for c in ids[1:]:
            parent[find(c)] = find(ids[0])
    groups = {}
    for c in list(parent):
        groups.setdefault(find(c), []).append(c)
    return sorted((sorted(g) for g in groups.values() if len(g) > 1), key=lambda g: g[0])


def join_base(cols_by_id, ids):
    """Id of the column that gives the joined column its name: the most mentions, ties the lower id."""
    return min(ids, key=lambda c: (-cols_by_id[c]["n_mentions"], c))


def _types(value_types):
    return {t: int(n) for t, n in (x.split(":") for x in value_types.split("|") if x)}


def join_columns(cols, base):
    """One pooled column dict from the column dicts `cols` (batch_v38.column_table): name and description of `base`'s column
    (cid `base`), groups / members / mentions united; dialogues and distinct values counted on the union, value types summed.
    Members hold disjoint mentions, so sums are exact."""
    by_id = {c["cid"]: c for c in cols}
    b = by_id[base]
    items = [x for c in cols for _, ms in c["pools"] for x in ms]
    types = Counter()
    for c in cols:
        types.update(_types(c["value_types"]))
    return {"cid": base, "name": b["name"], "description": b["description"], "groups": sorted(g for c in cols for g in c["groups"]),
            "members": sorted(m for c in cols for m in c["members"]), "mention_ids": [m for c in cols for m in c["mention_ids"]],
            "n_mentions": sum(c["n_mentions"] for c in cols), "n_dialogues": len({x[1] for x in items}),
            "n_values": len({x[2] for x in items}),
            "value_types": "|".join(f"{t}:{n}" for t, n in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))),
            "pools": [p for c in cols for p in c["pools"]], "joined": sorted(c["cid"] for c in cols)}


def renamed_attrs(attrs, rename):
    """Copy of the variant attrs (attr_id, name, ...) with the name of every group in `rename` {attr_id: name} replaced."""
    out = attrs.copy()
    out["name"] = [rename.get(a, n) for a, n in zip(out["attr_id"], out["name"])]
    return out


def marked_attrs(attrs, groups, status="not_attribute"):
    """Copy of the variant attrs with the status of every group in `groups` set to a marked status (a group that is no column;
    rules_groups.found then skips it, marked_found=skip)."""
    out = attrs.copy()
    out["status"] = [status if a in set(groups) else s for a, s in zip(out["attr_id"], out["status"])]
    return out


def join_right(info):
    """(status, why) of a join by the GT, status in JOIN_STATUS. info = [{"name", "label", "top_attr", "partner"}] one per joined
    column. right: every column is labelled real, all have the same top L2 attribute and every partner-role share is <= PARTNER_MAX.
    wrong: a noise column is in the join, or the real columns differ in attribute, or a column mixes roles. no_gt: otherwise
    (a column has no L2 attribute at 60%: the GT cannot say)."""
    if any(i["label"] == "noise" for i in info):
        return "wrong", "noise column (" + ", ".join(i["name"] for i in info if i["label"] == "noise") + ")"
    if any(i["label"] != "real" for i in info):
        return "no_gt", "no L2 attribute (" + ", ".join(f"{i['name']}: {i['label']}" for i in info if i["label"] != "real") + ")"
    attrs = sorted({i["top_attr"] for i in info})
    if len(attrs) > 1:
        return "wrong", "different attributes: " + " vs ".join(attrs)
    if any(i["partner"] > PARTNER_MAX for i in info):
        return "wrong", "role mix inside a column"
    return "right", "same attribute, same role"


# ---- evidence and verdict

def pooled_support(members, support):
    """(yes, answered) summed over the example jobs of `members` ({column id: (yes, answered)}, a column without a job adds nothing)."""
    ys = [support[c] for c in members if c in support]
    return sum(y for y, _ in ys), sum(n for _, n in ys)


def neighbour_evidence(members, base, neighbours, src_counts):
    """Neighbour evidence of a column made of pre-join columns `members` (base first when it is a join).
    neighbours: its nearest columns, each a list of pre-join ids; src_counts: {pre-join column: {source: (yes, answered)}} from
    the neighbour jobs. Per source the answer of the base's job is used, else the first other member's that has it (one answer
    per example, no double count). Returns [{"cids", "yes", "n"}] one per neighbour (n = 0: no job asked about it)."""
    order = [base] + [m for m in members if m != base]
    out = []
    for cids in neighbours:
        y = n = 0
        for s in cids:
            for m in order:
                if s in src_counts.get(m, {}):
                    ys, ns = src_counts[m][s]
                    y, n = y + ys, n + ns
                    break
        out.append({"cids": list(cids), "yes": y, "n": n})
    return out


def mixed_roles(own_names, neigh):
    """True when a neighbour that fits (share >= NEIGHBOUR_YES) has a name in a role pair with one of `own_names` (the method's
    own names, word sets BT.NAME_PAIRS). neigh: [{"names": [...], "yes", "n"}]."""
    return any(x["n"] and x["yes"] / x["n"] >= NEIGHBOUR_YES
               and any(RGD.forbidden_merge(a, b, BT.NAME_PAIRS) for a in own_names for b in x["names"]) for x in neigh)


def verdict(support, fit, mixed):
    """Verdict rule v0, in this order: noise (support < 0.4); too general or mixed roles (neighbour fit > 0.5; mixed roles when a
    fitting neighbour is the role partner); real (support >= 0.7 and fit <= 0.3); else unsure. No support (no examples) is
    unsure; no neighbour fit (no neighbour examples) skips rule 2 and counts as 0 in rule 3."""
    if support is None:
        return "unsure"
    if support < SUPPORT_NOISE:
        return "noise"
    if fit is not None and fit > FIT_GENERAL:
        return "mixed roles" if mixed else "too general"
    if support >= SUPPORT_REAL and (fit or 0.0) <= FIT_REAL:
        return "real"
    return "unsure"


def dominant_share(value_types):
    """(dominant type, its share) of a "type:n|type:n" string; ("", 0.0) when empty."""
    t = _types(value_types)
    if not t:
        return "", 0.0
    top = max(t.items(), key=lambda kv: (kv[1], kv[0]))
    return top[0], top[1] / sum(t.values())


# ---- task 11

def gt_kinds(cols):
    """DataFrame `cols` (cid, kind in gt / wrong / noise / no_gt, top_attr) -> a list of GT kinds (GT_KINDS), same order: the
    first gt column (lowest cid) of an attribute is gt, further gt columns of it are duplicate; wrong = wrong entity or noise;
    no_gt = mixed / unknown."""
    seen, out = set(), []
    for cid, kind, attr in sorted(zip(cols["cid"], cols["kind"], cols["top_attr"])):
        if kind == "gt":
            out.append((cid, "duplicate" if attr in seen else "gt"))
            seen.add(attr)
        else:
            out.append((cid, "wrong" if kind in ("wrong", "noise") else "no_gt"))
    k = dict(out)
    return [k[c] for c in cols["cid"]]


def verdict_row(label, verdicts):
    """dict (gt_kind, n, one count per verdict, real_share, rejected_share, rejected_mixed_share, not_real_share) of a list of
    verdicts. rejected = noise or too general; rejected_mixed adds mixed roles; not_real = any verdict but real."""
    c = Counter(verdicts)
    n = len(verdicts)
    return {"gt_kind": label, "n": n, **{x: c.get(x, 0) for x in VERDICTS}, "real_share": share(c["real"], n),
            "rejected_share": share(sum(c[x] for x in REJECTED), n),
            "rejected_mixed_share": share(sum(c[x] for x in REJECTED + ("mixed roles",)), n), "not_real_share": share(n - c["real"], n)}


def checker_table(kinds, verdicts):
    """DataFrame of verdict_row per GT kind (GT_KINDS) from the GT kinds and verdicts of the columns."""
    return pd.DataFrame([verdict_row(k, [v for g, v in zip(kinds, verdicts) if g == k]) for k in GT_KINDS])


def filter_decision(wrong_n, wrong_rejected, guard_pass):
    """(use as filter?, line): filter only if it rejects at least half of the wrong columns and the recall guard passes."""
    ok = wrong_n > 0 and 2 * wrong_rejected >= wrong_n and guard_pass
    why = (f"rejects {wrong_rejected}/{wrong_n} wrong columns ({'>=' if 2 * wrong_rejected >= wrong_n else '<'} half), "
           f"recall guard {'pass' if guard_pass else 'FAIL'}")
    return ok, ("use as a filter: " if ok else "keep as a flag for the final review: ") + why
