"""wf_v3.6 tables on top of score_v35 rows: the order range of A (and AE), the Q8 gain verdict against that range and
the oracle decision. Pure functions of score rows (DataFrames with level, ent, variant, found_n, gold_n, ... as written
by score_rules.score_entity); no data loading.
"""

import numpy as np
import pandas as pd

from . import rules_names as RN
from . import score_rules as SR

ENTS = ("train", "hotel", "restaurant")
A_ORDERS = ("A r1", "A r2", "A s2")
AE_ORDERS = ("AE s0", "AE s1", "AE s2")
# (k column, n column) of the pooled table cells after the three found cells
POOLED = (("merge_right", "merge_n"), ("name_right", "name_base"), ("role_right", "role_base"),
          ("cue_request", "cue_clusters"))
ORACLE_PASS_GAIN = 2


def _num(g, col):
    v = pd.to_numeric(g[col], errors="coerce")
    return None if v.isna().all() else float(v.sum())


def cell_numbers(g, invalid=()):
    """[(k, n)] of one variant's table cells (entity rows `g`): found per entity, noise pooled, merge, names, role, cue.
    (None, None) where a cell has no number; entities in `invalid` are left out. Same cells as score_v35.variant_cells."""
    out = []
    for ent in ENTS:
        r = g[g["ent"] == ent]
        out.append((None, None) if ent in invalid or not len(r)
                   else (float(r["found_n"].iloc[0]), float(r["gold_n"].iloc[0])))
    g = g[~g["ent"].isin(invalid)]
    pooled = SR.pooled_noise(g)
    out.append((float(pooled["marked"]), float(pooled["n"])))
    out += [(_num(g, k), _num(g, n)) for k, n in POOLED]
    return out


def _span(vals, as_int=True):
    lo, hi = min(vals), max(vals)
    f = (lambda x: str(int(x))) if as_int else str
    return f(lo) if lo == hi else f"{f(lo)}–{f(hi)}"


def fmt_range(pairs):
    """"29–31/40" from [(k, n)] of the orders (one pair per order); a single value when the orders agree, "n/a" when
    any order has no number."""
    if any(k is None or n is None or np.isnan(k) or np.isnan(n) for k, n in pairs):
        return SR.NA
    return f"{_span([k for k, _ in pairs])}/{_span([n for _, n in pairs])}"


def range_cells(groups, invalid=()):
    """Table cells of a range row: for every cell, the min–max of k over the orders (`groups` = one entity-row
    DataFrame per order) over n."""
    per = [cell_numbers(g, invalid) for g in groups]
    return [fmt_range([p[i] for p in per]) for i in range(len(per[0]))]


# ---- Q8 gain against the A range

def found_table(rows, invalid):
    """ent x variant found_n of one level (rules_names._found_table, so invalid runs are NaN)."""
    return RN._found_table(rows, invalid)


def order_totals(t, orders):
    """Series of the total found over the entities for each order in `orders` (NaN when an entity of it is NaN)."""
    cols = [o for o in orders if o in t.columns]
    return t[cols].sum(min_count=len(t)) if cols else pd.Series(dtype=float)


GAIN_COLS = ["level", "variant", "found train", "found hotel", "found restaurant", "total", "A range total",
             "gain over A max", "loss under A min", "entities below A min", "verdict"]


def gain_vs_range(t, variants, orders=A_ORDERS, level=0, gain_min=RN.GAIN_MIN):
    """One row per variant of `variants` (columns of the found table `t`): its found per entity, the total, the A range of
    the total (min–max over the 3 orders), gain over A's max, loss under A's min and the entities that fall under
    their own A minimum. Verdict: gain only above A's max (total - A max >= gain_min and no entity under its A min);
    loss only below A's min (total < A min); else within A range. NaN totals (invalid run): n/a."""
    orders = [o for o in orders if o in t.columns]
    tot = order_totals(t, orders)
    lo_e, hi_e = t[orders].min(axis=1), t[orders].max(axis=1)
    rows = []
    for v in variants:
        if v not in t.columns:
            continue
        total = t[v].sum(min_count=len(t))
        under = [e for e in t.index if not np.isnan(t.loc[e, v]) and t.loc[e, v] < lo_e[e]]
        gain, loss = total - tot.max(), total - tot.min()
        if np.isnan(total):
            verdict = "n/a (invalid run)"
        elif gain >= gain_min and not under:
            verdict = "gain"
        elif total < tot.min():
            verdict = "loss"
        elif gain >= gain_min:
            verdict = f"within A range (an entity is under its A min: {', '.join(under)})"
        elif gain > 0:
            verdict = f"within A range (+{int(gain)} over A max, below the {gain_min} needed)"
        else:
            verdict = "within A range"
        rows.append({"level": level, "variant": v, **{f"found {e}": t.loc[e, v] for e in ENTS if e in t.index},
                     "total": total, "A range total": f"{int(tot.min())}–{int(tot.max())}",
                     "gain over A max": gain, "loss under A min": loss, "entities below A min": ";".join(under),
                     "verdict": verdict})
    return pd.DataFrame(rows, columns=GAIN_COLS)


# ---- oracle decision

def oracle_decision(t, oracle="Oracle s012", base="C s012", gain_min=ORACLE_PASS_GAIN):
    """(passed, diff Series per entity, total) of one level's found table: Oracle - base. PASS when the total gain is
    >= gain_min and no entity loses one."""
    d = t[oracle] - t[base]
    total = float(d.sum())
    return bool(total >= gain_min and (d.dropna() >= 0).all()), d, total
