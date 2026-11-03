"""wf_v3.7 T4: train stability of Oracle and C across the 3 orders. No models, no LLM.

Group agreement = `rules_names.agreement` with agreement=split (mean over clusters of orders agreeing with the most common
choice / 3; groups and names over clusters not marked in any order, noise over all).

Role-pair flip (defined exactly): take the two-role train clusters (`oracle_v35.two_roles`: both slots of a pair from
config/role_pairs.json, each >= 20% of the cluster's labelled mentions; the clusters of the Step-1a export, also for
Oracle). In one order, the *side* of a mention = the role slot of the pair that is the majority L2 label of the final
group the mention sits in; "other" when the mention has no group, the group is marked, or its majority is no slot of
the pair. The *sides* of a cluster in an order = the set of the sides of its mentions. A cluster flips between two
orders when its sides differ. Reported: clusters that flip in at least one pair of orders (of the two-role clusters)
and flips over all (cluster, pair of orders) cases. No gold role is used to build a group; gold only names the sides.
"""

from dataclasses import replace
from itertools import combinations

import pandas as pd

from . import oracle_v35 as OR
from . import pilot_score as PS
from . import pilot_verify as PV
from . import rules_names as RN

ORDERS = (0, 1, 2)
OTHER = "other"


def with_seed_labels(ed, labels):
    """ed with seed_decs {"C s<k>": the decision table of variant labels[k]} (what rules_names.agreement reads); the
    labels are the three orders of one run, e.g. ("A r1", "A r2", "A s2")."""
    return replace(ed, seed_decs={f"C s{k}": ed.variants[lab].dec for k, lab in enumerate(labels)})


def with_seed_decs(ed, prefix):
    """ed with seed_decs {"C s<k>": the decision table of variant "<prefix> s<k>"} (what rules_names.agreement reads)."""
    return with_seed_labels(ed, [f"{prefix} s{k}" for k in ORDERS])


def agreement(ed, prefix, rules, extra):
    """{agree_groups, agree_noise, agree_names} of the 3 orders of variant `prefix` (C | Oracle)."""
    return RN.agreement(with_seed_decs(ed, prefix), rules, extra)


def two_role(ed_level):
    """{cluster_id: pair} of the entity's clusters (level data: gold_attr = L2 labels)."""
    mm = ed_level.mentions
    return OR.two_roles(mm, pd.Series(list(mm["gold_attr"]), index=mm.index))[1]


def sides(ed_level, label, mention_ids, pair):
    """frozenset of the sides (a slot of `pair`, or OTHER) of the mentions `mention_ids` in variant `label`."""
    vo = ed_level.variants[label]
    gold = {int(i): g for i, g in zip(ed_level.mentions["mention_id"], ed_level.mentions["gold_attr"])}
    status = vo.attrs.set_index("attr_id")["status"].to_dict()
    cache, out = {}, set()
    for i in mention_ids:
        gid = vo.assign.get(int(i), "")
        if gid not in cache:
            slot = PS._slot(PS._majority_gold(vo.assign, gid, gold), ed_level.gold_ents) if gid else ""
            cache[gid] = OTHER if not gid or status.get(gid) in PV.MARKED or slot not in pair else slot
        out.add(cache[gid])
    return frozenset(out)


def role_flips(ed_level, prefix, two, mention_ids):
    """DataFrame, one row per two-role cluster: cluster, pair, sides s0 / s1 / s2 (text), flips (pairs of orders whose
    sides differ, of 3). `mention_ids` {cluster_id: mention ids of the Step-1a cluster} (the export's clusters)."""
    rows = []
    for cid, pair in sorted(two.items()):
        per = [sides(ed_level, f"{prefix} s{k}", mention_ids[cid], pair) for k in ORDERS]
        rows.append({"cluster": cid, "pair": "/".join(pair), **{f"s{k}": "+".join(sorted(per[k])) for k in ORDERS},
                     "flips": sum(per[i] != per[j] for i, j in combinations(range(len(ORDERS)), 2))})
    return pd.DataFrame(rows, columns=["cluster", "pair", "s0", "s1", "s2", "flips"])


def stability_md(agree, flips, notes=()):
    """agree {name: {agree_*}}, flips {name: role_flips table}."""
    lines = ["# wf_v3.7 train stability: Oracle and C over 3 orders (L2, rules v1.1)", "",
             "Train only. Group agreement = `agreement=split` (mean over clusters of orders that agree with the most "
             "common choice / 3). Role-pair flip: see `s1a/stability_v37.py`. Side of a mention = the role slot of the pair "
             "that is the majority L2 label of its final group (other: no group, a marked group, or a majority that is no "
             "slot of the pair); sides of a cluster = the set of its mentions' sides; a cluster flips between two orders "
             "when its sides differ.", "",
             "| variant | agree groups | agree noise | agree names | two-role clusters flipping (>= 1 pair of orders) | "
             "flips (cluster x pair of orders) |", "|---|---|---|---|---|---|"]
    for name, a in agree.items():
        f = flips[name]
        lines.append(f"| {name} | {a['agree_groups']:.3f} | {a['agree_noise']:.3f} | {a['agree_names']:.3f} | "
                     f"{int((f['flips'] > 0).sum())}/{len(f)} | {int(f['flips'].sum())}/{3 * len(f)} |")
    for name, f in flips.items():
        lines += ["", f"## {name}: sides per order of the two-role clusters", "", "| cluster | pair | s0 | s1 | s2 | flips |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| {r['cluster']} | {r['pair']} | {r['s0']} | {r['s1']} | {r['s2']} | {r['flips']}/3 |"
                  for _, r in f.iterrows()]
    lines += [""] + [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"
