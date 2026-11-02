"""wf_v3.7 T7: the exit bar for freezing Step 3 as v1 (RULES_V1_1.md). Pure functions of already-scored data; the run and GT
directories are read by `scripts/score_v37.exit_bar_from_dirs(args)`, so the bar can be rerun on dev50b and on the baseline.

(a) Step 3 finds >= 90% of the attributes that Step 1a makes recoverable (ceiling_v37, same found rule);
(b) the found attributes change by <= 1 across the orders (range of the totals over the orders);
(c) <= 1.2 columns per found attribute (columns_v37, mean);
(d) >= 9 of the 13 noise clusters caught, with >= 70% of the noise marks right;
(e) it beats the LLM-only baseline (pending the baseline).
"""

import pandas as pd

from . import rules_groups as RG
from . import score_rules as SR

A_MIN = 0.90
B_MAX = 1
C_MAX = 1.2
D_NOISE_MIN = 9
D_PRECISION_MIN = 0.70
CRITERIA = ("a", "b", "c", "d")


def found_set(ed, label, rules, extra):
    """{(ent, attr)} of the base attributes that variant `label` finds (rules_groups.found)."""
    f = RG.found(ed, label, rules, extra)
    return {(ed.ent, a) for a in f.loc[f["found"], "attr"]}


def run_metrics(found, ceil, noise, dup):
    """dict of one run (one order or a vote). found: set of (ent, attr) the run finds; ceil: ceiling table (recoverable
    column); noise: dict(noise_n, noise_marked, marked_n, marked_noise) pooled; dup: columns per found attribute."""
    rec = {(r["ent"], r["attr"]) for _, r in ceil[ceil["recoverable"]].iterrows()}
    return {"found": len(found), "recoverable": len(rec), "found_recoverable": len(found & rec),
            "found_not_recoverable": len(found - rec), **{k: int(noise[k]) for k in
                                                          ("noise_n", "noise_marked", "marked_n", "marked_noise")},
            "columns_per_found": dup}


def verdicts(m):
    """{criterion: bool} for one run; (b) is None for a single run (a vote has no orders)."""
    prec = m["marked_noise"] / m["marked_n"] if m["marked_n"] else 0.0
    return {"a": m["found_recoverable"] / m["recoverable"] >= A_MIN if m["recoverable"] else False, "b": None,
            "c": m["columns_per_found"] <= C_MAX, "d": m["noise_marked"] >= D_NOISE_MIN and prec >= D_PRECISION_MIN}


def _span(vals, fmt):
    lo, hi = min(vals), max(vals)
    return fmt(lo) if lo == hi else f"{fmt(lo)}-{fmt(hi)}"


def bar_rows(runs, groups):
    """DataFrame, one row per `groups` entry {name: [run labels]}: cells for (a)-(d) with a pass flag. A group of several
    runs (the orders) shows min-max and passes a criterion only when its worst run does; (b) = range of the found totals
    over the runs (single run: n/a, the orders' range applies). `runs`: {label: run_metrics dict}."""
    rows = []
    for name, labels in groups.items():
        ms = [runs[v] for v in labels]
        vd = [verdicts(m) for m in ms]
        frac = [m["found_recoverable"] / m["recoverable"] for m in ms]
        prec = [m["marked_noise"] / m["marked_n"] if m["marked_n"] else 0.0 for m in ms]
        totals = [m["found"] for m in ms]
        b = None if len(ms) == 1 else max(totals) - min(totals) <= B_MAX
        rows.append({
            "run": name, "a_found_recoverable": _span([m["found_recoverable"] for m in ms], str),
            "a_recoverable": ms[0]["recoverable"], "a_share": _span(frac, lambda x: f"{x:.3f}"),
            "a_pass": all(v["a"] for v in vd), "found_total": _span(totals, str),
            "b_range": max(totals) - min(totals) if len(ms) > 1 else None, "b_pass": b,
            "c_columns": _span([m["columns_per_found"] for m in ms], lambda x: f"{x:.3f}"), "c_pass": all(v["c"] for v in vd),
            "d_caught": _span([m["noise_marked"] for m in ms], str), "d_noise_n": ms[0]["noise_n"],
            "d_precision": _span(prec, lambda x: f"{x:.3f}"), "d_pass": all(v["d"] for v in vd)})
    return pd.DataFrame(rows)


def _ok(flag):
    return "n/a" if flag is None else "pass" if flag else "FAIL"


def exit_md(table, runs, notes=()):
    lines = ["# wf_v3.7 exit bar for freezing Step 3 as v1 (L2, rules v1.1)", "",
             "Bar (RULES_V1_1.md): (a) finds >= 90% of the attributes that Step 1a makes recoverable (ceiling table: some "
             "single cluster passes purity >= 0.6 and coverage >= 10%); (b) found attributes change by <= 1 across orders; "
             "(c) <= 1.2 columns per found attribute; (d) >= 9 of the 13 noise clusters caught with >= 70% of the noise "
             "marks right; (e) beats the LLM-only baseline: **pending the baseline**. A row of several orders shows "
             "min-max and passes only when its worst order does. (b) is the range of the found totals over the orders; a "
             "vote (A s012) is one result, so (b) is n/a and the orders' range applies.", "",
             "| run | (a) found of recoverable | (a) share | (b) found total, range | (c) columns per found | (d) noise caught | "
             "(d) precision of marks | a | b | c | d | e |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in table.iterrows():
        lines.append(f"| {r['run']} | {r['a_found_recoverable']}/{r['a_recoverable']} | {r['a_share']} | {r['found_total']}"
                     + (f", range {int(r['b_range'])}" if pd.notna(r["b_range"]) else "") + f" | {r['c_columns']} | "
                     f"{r['d_caught']}/{r['d_noise_n']} | {r['d_precision']} | {_ok(r['a_pass'])} | {_ok(r['b_pass'])} | "
                     f"{_ok(r['c_pass'])} | {_ok(r['d_pass'])} | pending the baseline |")
    lines += ["", "## Single runs", "", "| run | found | of which recoverable | found, not recoverable | columns per found | "
              "noise caught | marks right |", "|---|---|---|---|---|---|---|"]
    for v, m in runs.items():
        lines.append(f"| {v} | {m['found']} | {SR.fmt_count(m['found_recoverable'], m['recoverable'])} | "
                     f"{m['found_not_recoverable']} | {m['columns_per_found']:.3f} | "
                     f"{SR.fmt_count(m['noise_marked'], m['noise_n'])} | {SR.fmt_count(m['marked_noise'], m['marked_n'])} |")
    return "\n".join(lines + [""] + [f"- {n}" for n in notes]) + "\n"
