"""wf_v3.7 T2: A s012 = PC.vote over A's three orders (A r1 / A r2 / A s2 = orders 0 / 1 / 2), read the same way as AE s012
in `v36_data` (`v36_data._add`: the voted decision table, then the usual final attributes and the +namemerge copy),
scored next to AE s012 and the three A orders, and the keep-AE / drop-AE decision. No models, no LLM.
"""

from dataclasses import replace

import pandas as pd

from . import names_l2 as NL
from . import noise_v36 as NV
from . import pilot_combine as PC
from . import rules_names as RN
from . import score_rules as SR
from . import v36_data as V36

A_ORDERS = ("A r1", "A r2", "A s2")
NAMES_V37_FILES = ("names_l2_v37_rater1.csv", "names_l2_v37_rater2.csv")
NAMES_V37_KEY = "names_to_rate_l2_v37_key.csv"


def merge_variants(*bundles):
    """{ent: EntityData} with the variants of every bundle ({ent: EntityData} each, same entity data underneath: the
    v3.4 and v3.6 A / AE bundles) in one dict; the first bundle's data is kept."""
    out = {}
    for ent, ed in bundles[0].items():
        variants = dict(ed.variants)
        for b in bundles[1:]:
            variants.update(b[ent].variants)
        out[ent] = replace(ed, variants=variants)
    return out


def add_a_s012(shared, a_bundle):
    """Add "A s012" and "A+namemerge s012" to the variants of `a_bundle` (a bundle that holds A r1 / A r2 / A s2): the
    3-order vote of their decision tables. A bundle without the three orders for an entity is left as it is."""
    for ed in a_bundle.values():
        if all(v in ed.variants for v in A_ORDERS):
            dec, ed.vote_stats = PC.vote([ed.variants[v].dec for v in A_ORDERS])
            V36._add(ed.variants, "A s012", dec, shared.e, ed.ctx_a, ed.entity)
    return a_bundle


def bundle_with_a_s012(shared, v34, v36):
    """The v3.6 bundle ({ent: EntityData}) with "A s012" and "A+namemerge s012" added (voted from A r1 / A r2 of the v3.4
    bundle and A s2 of the v3.6 one)."""
    merged = add_a_s012(shared, merge_variants(v34, v36))
    new = ("A s012", "A+namemerge s012")
    return {ent: replace(ed, variants={**ed.variants, **{k: merged[ent].variants[k] for k in new if k in merged[ent].variants}})
            for ent, ed in v36.items()}


# ---- names of A s012 for the blind L2 sheet

def read_l2_rated(dir36, dir37):
    """DataFrame (JOIN_KEYS + label) of the v3.6 L2 ratings plus the v3.7 ones (names_l2_v37_rater{1,2}.csv with
    names_to_rate_l2_v37_key.csv in dir37) when they exist; the lower label wins. None when the v3.6 files are absent."""
    base = RN.read_l2_rated(dir36)
    new = RN.read_l2_rated(dir37, NAMES_V37_FILES, NAMES_V37_KEY)
    frames = [f for f in (base, new) if f is not None]
    if not frames:
        return None
    got = RN._rated_by_key(pd.concat(frames, ignore_index=True), RN.L2_LABELS)
    return pd.DataFrame([dict(zip(RN.JOIN_KEYS, k), label=lab) for k, lab in got.items()], columns=RN.JOIN_KEYS + ["label"])


def unrated_names(bundle, label, rated, gt):
    """The (JOIN_KEYS, top_values) rows of `label`'s groups at L2 that have no rating in `rated` (read_l2_rated), for the
    blind sheet. `bundle` is {ent: EntityData} as loaded; names_l2.l2_group_rows reads it at L2 itself."""
    rows = NL.l2_group_rows([{ent: replace(ed, variants={label: ed.variants[label]}) for ent, ed in bundle.items()}], gt)
    seen = set(map(tuple, rated[RN.JOIN_KEYS].values)) if rated is not None else set()
    return rows[[tuple(r) not in seen for r in rows[RN.JOIN_KEYS].values]]


def sheet_files(rows, key_old, tear_map, slot_desc):
    """(rater, key) of the blind v3.7 sheet: the unrated rows through names_l2.rating_sheet, with row ids continuing after
    the largest id of the v3.6 key `key_old` (so rater files and keys can be appended)."""
    rater, key = NL.rating_sheet(rows, tear_map, slot_desc)
    start = int(key_old["row"].astype(int).max()) + 1
    rater["row"], key["row"] = rater["row"] + start, key["row"] + start
    return rater, key


# ---- the comparison table

COLS = ["variant", "found", "found_n", "gold_n", "noise_marked", "noise_n", "marked_n", "marked_noise", "marked_real",
        "names_right", "names_base", "names_unrated", "columns"]


def summary_rows(df_l2, df_l2r, noise_rows, columns, variants):
    """One dict per variant label of `variants` (a label that is missing from the data is skipped): pooled found
    (found_n / gold_n), per-entity found text, noise (noise_n, noise_marked), precision of marks (marked_noise /
    marked_n), real clusters marked noise (marked_real: marked clusters labelled real), names right of the rated
    sheet at L2 (names_right / names_base, names_unrated), columns (`columns` {variant: count over entities}).
    df_l2: score rows at L2; df_l2r: the same with names=l2rated; noise_rows: noise_v36.noise_l2_rows output."""
    rows = []
    for v in variants:
        g, gr, nz = df_l2[df_l2["variant"] == v], df_l2r[df_l2r["variant"] == v], noise_rows[noise_rows["variant"] == v]
        if not len(g) or not len(nz):
            continue
        num = lambda d, c: int(pd.to_numeric(d[c], errors="coerce").sum())  # noqa: E731
        rows.append({"variant": v, "found": " + ".join(f"{int(r['found_n'])}" for _, r in g.set_index("ent").loc[
            ["train", "hotel", "restaurant"]].iterrows()), "found_n": num(g, "found_n"), "gold_n": num(g, "gold_n"),
            **{c: num(nz, c) for c in ("noise_marked", "noise_n", "marked_n", "marked_noise", "marked_real")},
            "names_right": num(gr, "name_right"), "names_base": num(gr, "name_base"),
            "names_unrated": num(gr, "names_unrated"), "columns": columns[v]})
    return pd.DataFrame(rows, columns=COLS)


def decision(t, a="A s012", ae="AE s012"):
    """(keep AE?, text). Keep AE only if AE s012 catches more of the noise clusters than A s012 and finds no fewer
    attributes at L2; otherwise drop AE."""
    ra, rae = t.set_index("variant").loc[a], t.set_index("variant").loc[ae]
    keep = bool(rae["noise_marked"] > ra["noise_marked"] and rae["found_n"] >= ra["found_n"])
    text = (f"AE s012 catches {rae['noise_marked']}/{rae['noise_n']} noise clusters, {a} {ra['noise_marked']}/{ra['noise_n']}; "
            f"found at L2: {ae} {rae['found_n']}/{rae['gold_n']}, {a} {ra['found_n']}/{ra['gold_n']}. Rule: keep AE only if "
            f"AE s012 catches more noise clusters and finds no fewer attributes; else drop AE. **Decision: "
            f"{'KEEP AE' if keep else 'DROP AE'}.**")
    return keep, text


def _range(t, col, orders):
    v = [int(t.loc[t["variant"] == o, col].iloc[0]) for o in orders if (t["variant"] == o).any()]
    return f"{min(v)}-{max(v)}" if v and min(v) != max(v) else str(v[0]) if v else "n/a"


def a_s012_md(t, notes=(), orders=A_ORDERS):
    """Markdown of the T2 table: the A orders as one range row, A s012, AE s012 (+ the single orders after the table)."""
    def cells(r):
        return [r["found"] + f" = {r['found_n']}/{r['gold_n']}", SR.fmt_count(r["noise_marked"], r["noise_n"]),
                SR.fmt_count(r["marked_noise"], r["marked_n"]), str(r["marked_real"]),
                SR.fmt_count(r["names_right"], r["names_base"]) + (f" [{r['names_unrated']} unrated]" if r["names_unrated"] else ""),
                str(r["columns"])]
    head = ["found train + hotel + restaurant", "noise clusters caught", "precision of noise marks",
            "real clusters marked noise", "names right (L2 rated)", "columns"]
    lines = ["# wf_v3.7 A s012 against AE s012 (L2, rules v1.1)", "",
             "A s012 = the 3-order vote of A (orders 0 / 1 / 2 = A r1 / A r2 / A s2), read like AE s012. Rules v1.1: noise = "
             "the MultiWOZ-only noise set (13 clusters at L2). Found = purity >= 0.6 and coverage >= 10%. Noise caught = noise "
             "clusters marked not_attribute / unsure / attribute_cue; precision = marked clusters that are noise; real marked = "
             "marked clusters whose majority is an L2 attribute. Names right = base attributes with a group rated right "
             "against its L2 slot (names=l2rated); unrated names count as not right. Columns = distinct output attribute "
             "names of unmarked groups.", "", "| variant | " + " | ".join(head) + " |", "|---|" + "---|" * len(head)]
    present = [o for o in orders if (t["variant"] == o).any()]
    if len(present) == len(orders):
        lines.append("| A, 3 orders (range) | " + " | ".join([
            f"{_range(t, 'found_n', orders)}/{int(t.loc[t['variant'] == orders[0], 'gold_n'].iloc[0])}",
            f"{_range(t, 'noise_marked', orders)}/{int(t.loc[t['variant'] == orders[0], 'noise_n'].iloc[0])}",
            f"{_range(t, 'marked_noise', orders)} of {_range(t, 'marked_n', orders)} marks",
            _range(t, "marked_real", orders), f"{_range(t, 'names_right', orders)}/{int(t.loc[t['variant'] == orders[0], 'names_base'].iloc[0])}",
            _range(t, "columns", orders)]) + " |")
    for v in ("A s012", "AE s012"):
        if (t["variant"] == v).any():
            lines.append(f"| {v} | " + " | ".join(cells(t[t["variant"] == v].iloc[0])) + " |")
    lines += ["", "## The single orders", "", "| variant | " + " | ".join(head) + " |", "|---|" + "---|" * len(head)]
    lines += [f"| {r['variant']} | " + " | ".join(cells(r)) + " |" for _, r in t.iterrows()
              if r["variant"] in orders or r["variant"].startswith("AE s") and r["variant"] != "AE s012"]
    if {"A s012", "AE s012"} <= set(t["variant"]):
        lines += ["", "## Decision", "", decision(t)[1]]
    return "\n".join(lines + [""] + [f"- {n}" for n in notes]) + "\n"


def noise_rows_for(bundles, extra, variants):
    """noise_v36.noise_l2_rows over every bundle ({ent: EntityData}) in `bundles`, one frame."""
    return pd.concat([NV.noise_l2_rows(b, extra, variants, []) for b in bundles], ignore_index=True)
