"""wf_v3.7 T14: A in 3 orders on Step 1a v2.2 and v2.3, on dev50 and dev50b, at L2 under rules v1.1. Pure functions of
already-scored data (scripts/score_t14_v37.py loads and scores). No models, no LLM.

Role-correct = the existing "role right / base" column of the v3.5 / v3.6 tables (rules_names.name_scores with
names=l2rated at L2): base = the L2 base attributes whose slot is in a role pair of config/role_pairs.json (departure /
destination, leave at / arrive by; train and taxi slots), right = those with at least one group that two blind raters
rated "right" against its L2 slot name. An unrated name counts as not right.

Decision (diary T14): keep v2.3 if, on both sets, (i) no entity's worst A order on v2.3 has fewer found attributes than
the worst A order of that entity on v2.2 (same set), and (ii) role-correct of A s012 or the train group agreement over
the 3 orders is higher on v2.3 than on v2.2.
"""

import pandas as pd

from . import columns_v37 as CV
from . import score_rules as SR

ENTS = ("train", "hotel", "restaurant")
ROW_COLS = ["set", "version", "variant", "kind", "found_train", "found_hotel", "found_restaurant", "found_n", "gold_n",
            "role_right", "role_base", "names_right", "names_base", "names_unrated", "columns", "dup_mean", "dup_max",
            "dup_attrs", "noise_n", "noise_marked", "marked_n", "marked_noise", "marked_real", "agree_groups",
            "recoverable", "present", "ceil_n"]


def _num(g, col):
    return int(pd.to_numeric(g[col], errors="coerce").sum())


def run_rows(set_name, version, orders, vote, scores, noise, columns, dup, ceil, agree=None):
    """DataFrame (ROW_COLS), one row per label of `orders` + `vote` that has score rows. scores: score rows at L2 with
    names=l2rated (ent, variant, found_n, gold_n, role_*, name_*, names_unrated); noise: noise_v36.noise_l2_rows output;
    columns: {label: columns over the entities}; dup: columns_v37.dup_rows rows; ceil: ceiling_table of the run;
    agree: {agree_groups: ..} over the orders (put on the vote row) or None."""
    rows = []
    for label in (*orders, vote):
        g, nz = scores[scores["variant"] == label], noise[noise["variant"] == label]
        if not len(g) or not len(nz):
            continue
        s = CV.dup_summary(dup[dup["variant"] == label])
        found = {e: int(g.loc[g["ent"] == e, "found_n"].iloc[0]) for e in ENTS}
        rows.append({
            "set": set_name, "version": version, "variant": label, "kind": "vote" if label == vote else "order",
            **{f"found_{e}": found[e] for e in ENTS}, "found_n": _num(g, "found_n"), "gold_n": _num(g, "gold_n"),
            "role_right": _num(g, "role_right"), "role_base": _num(g, "role_base"), "names_right": _num(g, "name_right"),
            "names_base": _num(g, "name_base"), "names_unrated": _num(g, "names_unrated"), "columns": columns[label],
            "dup_mean": s["mean"], "dup_max": s["max"], "dup_attrs": s["dup"],
            **{c: _num(nz, c) for c in ("noise_n", "noise_marked", "marked_n", "marked_noise", "marked_real")},
            "agree_groups": (agree or {}).get("agree_groups") if label == vote else None,
            "recoverable": int(ceil["recoverable"].sum()), "present": int(ceil["present"].sum()), "ceil_n": len(ceil)})
    return pd.DataFrame(rows, columns=ROW_COLS)


def _worst(rows, set_name, version):
    """{ent: min found over the A orders} of one (set, version); None when it has no order rows."""
    o = rows[(rows["set"] == set_name) & (rows["version"] == version) & (rows["kind"] == "order")]
    return {e: int(o[f"found_{e}"].min()) for e in ENTS} if len(o) else None


def _vote(rows, set_name, version):
    v = rows[(rows["set"] == set_name) & (rows["version"] == version) & (rows["kind"] == "vote")]
    return v.iloc[0] if len(v) else None


def decide(rows, base="v2.2", new="v2.3"):
    """(keep: True / False / None, [text per set], summary line). None while a set lacks the A rows of either version."""
    keeps, lines = [], []
    for s in dict.fromkeys(rows["set"]):
        w0, w1, v0, v1 = _worst(rows, s, base), _worst(rows, s, new), _vote(rows, s, base), _vote(rows, s, new)
        if w0 is None or w1 is None or v0 is None or v1 is None:
            lines.append(f"{s}: missing A rows ({base}: {'ok' if w0 is not None and v0 is not None else 'missing'}, "
                         f"{new}: {'ok' if w1 is not None and v1 is not None else 'missing'}); not decided.")
            keeps.append(None)
            continue
        below = [e for e in ENTS if w1[e] < w0[e]]
        role = v1["role_right"] > v0["role_right"]
        a0, a1 = v0["agree_groups"], v1["agree_groups"]
        agree = pd.notna(a0) and pd.notna(a1) and a1 > a0
        ok = not below and (role or agree)
        keeps.append(ok)
        lines.append(f"{s}: worst-order found per entity {new} {w1} vs {base} {w0}"
                     + (f", below {base}: {', '.join(below)}" if below else ", none below")
                     + f"; role-correct A s012 {int(v1['role_right'])}/{int(v1['role_base'])} vs {int(v0['role_right'])}/"
                     f"{int(v0['role_base'])} ({'better' if role else 'not better'}); train group agreement "
                     f"{a1:.3f} vs {a0:.3f} ({'better' if agree else 'not better'}) -> {'pass' if ok else 'FAIL'}.")
    keep = None if any(k is None for k in keeps) or not keeps else all(keeps)
    word = "undecided (A responses missing)" if keep is None else "KEEP v2.3" if keep else "DROP v2.3 (keep v2.2)"
    return keep, lines, (f"**Decision: {word}.** Rule: keep v2.3 if, on both sets, no entity's worst A order on v2.3 finds "
                         f"fewer attributes than its worst A order on v2.2, and role-correct (A s012) or train group "
                         f"agreement improves.")


def _rng(vals, fmt=str):
    lo, hi = min(vals), max(vals)
    return fmt(lo) if lo == hi else f"{fmt(lo)}-{fmt(hi)}"


def ceiling_lines(ceils):
    """Markdown table of the ceiling per run: ceils {(set, version): ceiling_table}."""
    lines = ["## Ceiling per run (L2: base attributes that some single cluster makes recoverable)", "",
             "| set | version | train | hotel | restaurant | total | present |", "|---|---|---|---|---|---|---|"]
    for (s, v), c in ceils.items():
        cnt = c.groupby("ent", sort=False)[["recoverable", "present"]].sum().join(c.groupby("ent", sort=False).size().rename("n"))
        cell = lambda e: SR.fmt_count(cnt.loc[e, "recoverable"], cnt.loc[e, "n"]) if e in cnt.index else "n/a"  # noqa: E731
        lines.append(f"| {s} | {v} | {cell('train')} | {cell('hotel')} | {cell('restaurant')} | "
                     f"{SR.fmt_count(c['recoverable'].sum(), len(c))} | {SR.fmt_count(c['present'].sum(), len(c))} |")
    return lines


def t14_md(rows, decision, ceils=None, missing=(), notes=()):
    head = ["found train + hotel + restaurant", "ceiling (recoverable)", "role-correct", "columns", "columns per found (dup)",
            "attrs with >= 2 columns", "noise caught", "precision of marks", "real marked noise", "train group agreement"]
    lines = ["# wf_v3.7 T14: A on Step 1a v2.2 and v2.3, dev50 and dev50b (L2, rules v1.1)", "",
             "A in 3 orders (range over the orders) and the vote A s012. Found = purity >= 0.6 and coverage >= 10%. Ceiling = "
             "base attributes that some single cluster makes recoverable (ceiling_v37). Role-correct = role right / base "
             "(names=l2rated, see s1a/t14_v37.py; unrated names count as not right). Columns = distinct output attribute "
             "names of unmarked groups; dup = columns per found attribute. Noise = the model-free mwoz noise set of the run's "
             "own GT (n varies by set). Train group agreement = agreement=split over the 3 orders.", "",
             "| set | version | row | " + " | ".join(head) + " |", "|---|---|---|" + "---|" * len(head)]
    for (s, v), g in rows.groupby(["set", "version"], sort=False):
        o, vt = g[g["kind"] == "order"], g[g["kind"] == "vote"]
        c = g.iloc[0]
        ceil = f"{c['recoverable']}/{c['ceil_n']} (present {c['present']})"

        def cells(r, rng=False):
            d = (lambda col, f=str: _rng(list(r[col]), f)) if rng else (lambda col, f=str: f(r[col]))
            tot = f"{d('found_n')}/{c['gold_n']}"
            fnd = " + ".join(d(f"found_{e}") for e in ENTS)
            ag = "" if rng or pd.isna(r["agree_groups"]) else f"{r['agree_groups']:.3f}"
            return [f"{fnd} = {tot}", ceil, f"{d('role_right')}/{d('role_base')}", d("columns"),
                    d("dup_mean", lambda x: f"{x:.3f}"), d("dup_attrs"), f"{d('noise_marked')}/{d('noise_n')}",
                    f"{d('marked_noise')}/{d('marked_n')}", d("marked_real"), ag]
        if len(o):
            lines.append(f"| {s} | {v} | A, {len(o)} orders (range) | " + " | ".join(cells(o, True)) + " |")
        for _, r in vt.iterrows():
            lines.append(f"| {s} | {v} | {r['variant']} | " + " | ".join(cells(r)) + " |")
    lines += ["", "## Decision", ""] + [f"- {x}" for x in decision[1]] + ["", decision[2]]
    if ceils:
        lines += [""] + ceiling_lines(ceils)
    if missing:
        lines += ["", "## Missing responses", ""] + [f"- {m}" for m in missing]
    return "\n".join(lines + [""] + [f"- {n}" for n in notes]) + "\n"
