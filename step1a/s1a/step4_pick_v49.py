"""wf_v4.9 V3: the coded pick rule over the Step 4 variants (user-approved) and the hotel-table check it needs.

in_hotel_table: a table's main entity = the strictly most common Step 1a entity (prefix of a column's `source` "<entity>:<cid>") among its columns;
a hotel table is one whose main entity is a hotel entity (the entities of the set's loop-2 internet / parking columns, read from the columns).
pick(df): rule 1 (every seed, both sets: finished, >= 3 tables, internet and parking in a hotel table), rule 2 (GT columns placed within
0.05 of the best variant on each set), rule 3 (highest table F1 + grouping F1, mean over seeds, summed over the sets).
"""
from collections import Counter

MIN_TABLES = 3
TOL = 0.05


def main_entity(table):
    """Most common source entity of the table's columns; None if no column has a source or the top count is tied."""
    top = Counter(x["source"].split(":")[0] for x in table["columns"] if x.get("source")).most_common(2)
    return top[0][0] if top and (len(top) == 1 or top[0][1] > top[1][1]) else None


def in_hotel_table(canonical, keys, hotel):
    """True if any column source in `keys` sits in a table whose main entity is in `hotel` (a column in "unused" or missing = False)."""
    return any(x.get("source") in keys for t in canonical["tables"] if main_entity(t) in hotel for x in t["columns"])


def pick(df, seeds=(0, 1, 2), tol=TOL):
    """(chosen variant or None, {variant: {"rule1": (ok, reason), "rule2": (ok, reason), "score": float or None}}).
    df: one row per variant x set x seed with variant, set, seed, finished, tables, internet_hotel, parking_hotel, placed, table_f1, grouping_f1.
    A variant with no row for a set / seed (not run) fails rule 1."""
    sets = sorted(df["set"].unique())
    res = {}
    for v in sorted(df["variant"].unique()):
        why = []
        for dev in sets:
            d = df[(df["variant"] == v) & (df["set"] == dev)]
            for s in seeds:
                r = d[(d["seed"] == s) & d["finished"].astype(bool)]
                if r.empty:
                    why.append(f"{dev} s{s}: not finished / not run")
                    continue
                r = r.iloc[0]
                if r["tables"] < MIN_TABLES:
                    why.append(f"{dev} s{s}: collapse ({int(r['tables'])} tables)")
                for n in ("internet", "parking"):
                    if not r[f"{n}_hotel"]:
                        why.append(f"{dev} s{s}: {n} not in a hotel table")
        res[v] = {"rule1": (not why, "; ".join(why) or "ok")}
    fin = df[df["finished"].astype(bool)]
    mean = fin.groupby(["variant", "set"])[["placed", "table_f1", "grouping_f1"]].mean()
    for v in res:
        why = []
        for dev in sets:
            if (v, dev) not in mean.index:
                why.append(f"{dev}: no finished chain")
                continue
            best = mean.xs(dev, level="set")["placed"].max()
            gap = round(best - mean.loc[(v, dev), "placed"], 6)
            if gap > tol:
                why.append(f"{dev}: placed {mean.loc[(v, dev), 'placed']:.3f} is {gap:.3f} below the best {best:.3f}")
        res[v]["rule2"] = (not why, "; ".join(why) or "ok")
        got = [(v, dev) for dev in sets if (v, dev) in mean.index]
        res[v]["score"] = sum(mean.loc[k, "table_f1"] + mean.loc[k, "grouping_f1"] for k in got) if len(got) == len(sets) else None
    ok = {v: r["score"] for v, r in res.items() if r["rule1"][0] and r["rule2"][0] and r["score"] is not None}
    return (max(ok, key=ok.get) if ok else None), res
