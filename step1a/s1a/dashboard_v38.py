"""wf_v3.8 task 1-3: the precision dashboard, the no-split variant and the duplicate-column list. No models, no LLM.

Everything is read through the existing scorer pieces (rules v1.1 at L2): found = rules_groups.found, columns and duplicate
columns = columns_v37, merges = rules_groups.merges, noise = noise_v36.noise_l2_rows. New here:
- columns of a variant are classified at column level (all groups with the same normalised name pooled, then the rules
  v1.1 cluster-label rule: rules_labels.cluster_labels with the column as the "cluster"):
  noise      = label noise (>= 60% of the counted mentions are noise);
  wrong      = label real and the top attribute is not in the entity's L2 base (an attribute of another entity);
  gt         = label real and the top attribute is in the base;
  no_gt      = label mixed / unknown: no L2 attribute reaches 60% and not noise (an extra with no GT). Under noise_kind=mwoz a
               mention with no L2 label and no request act is noise, so a "real value without gold" cannot exist; request-only
               columns land here.
- wrong columns = wrong + noise; duplicate columns = sum over found attributes of (columns - 1); review edits = their sum.
- the recall guard of RULES_V1_2.md per entity (GUARD).
A bundle is {ent: EntityData} as loaded (raw); `prepare` reads it at L2 once.
"""

from collections import Counter
from dataclasses import replace
from itertools import combinations

import pandas as pd

from . import ceiling_v37 as CE
from . import columns_v37 as CV
from . import noise_v36 as NV
from . import pilot_score as PS
from . import rules_groups as RG
from . import rules_labels as RL
from . import v34_data as VD
from .labels import _classes

ENTS = ("train", "hotel", "restaurant")
GUARD = {"dev50": {"train": 8, "hotel": 12, "restaurant": 11}, "dev50b": {"train": 8, "hotel": 10, "restaurant": 11}}  # RULES_V1_2.md
CPF_BAR = 1.2                  # columns per found attribute, exit bar (c)
PARTNER_MAX = 0.2              # share of a column's labelled mentions in the partner role that still counts as "same role"
ENTITY_WORDS = frozenset({"train", "hotel", "restaurant", "taxi", "attraction"})
CAUSES = ("split_pass", "neighbourhood", "wording", "other")
KINDS = ("gt", "wrong", "noise", "no_gt")
ROW_COLS = ["set", "row", "n_runs", "found_train", "found_hotel", "found_restaurant", "found_total", "gold_total", "columns",
            "columns_per_found", "dup_columns", "wrong_columns", "wrong_entity_columns", "noise_columns", "extras_no_gt",
            "merges_right", "merges_judged", "noise_caught", "noise_n", "marks_right", "marks_n", "review_edits",
            "guard", "guard_detail", "cpf_bar"]


# ---- pure helpers

def guard_check(set_name, found):
    """(pass, detail) of the recall guard: `found` {ent: attributes found}; pass when no entity is below GUARD[set_name]."""
    need = GUARD[set_name]
    bad = [e for e in ENTS if found.get(e, 0) < need[e]]
    detail = ", ".join(f"{e} {found.get(e, 0)}/{need[e]}" for e in ENTS)
    return not bad, detail + (f"; below: {', '.join(bad)}" if bad else "")


def column_kind(label, top_attr, base):
    """Kind (KINDS) of a column from its cluster label (real / noise / mixed / unknown), top attribute and the entity's base set."""
    if label == "noise":
        return "noise"
    if label == "real":
        return "gt" if top_attr in base else "wrong"
    return "no_gt"


def name_tokens(name):
    """Content words of a column name: lower case, entity words dropped, a trailing plural s removed."""
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in str(name).lower().replace("_", " ").replace("-", " ").split()
            if w not in ENTITY_WORDS}


def pair_cause(split_a, split_b, name_a, name_b):
    """Cause of a duplicate pair: split_pass when either column comes from a split part; wording when the two names share a
    content word (the same thing worded twice); otherwise other. (neighbourhood is in CAUSES for the diary's list: A reads one
    entity prompt, so it has no neighbourhood groups and never gets it.)"""
    if split_a or split_b:
        return "split_pass"
    return "wording" if name_tokens(name_a) & name_tokens(name_b) else "other"


def fmt(k, n):
    return f"{k}/{n}"


def span(vals, f=str):
    lo, hi = min(vals), max(vals)
    return f(lo) if lo == hi else f"{f(lo)}-{f(hi)}"


# ---- columns of a variant

def prepare(set_name, raw, gt):
    """dict(set, raw, gt, lev): the bundle {ent: EntityData} read at L2 (v34_data.with_level)."""
    return {"set": set_name, "raw": raw, "gt": gt, "lev": VD.with_level(raw, gt, 2)}


def _column_labels(ed, label, rules, extra):
    """DataFrame (column, n, label, top_attr, kind) of the columns of `label`; groups with one name are pooled."""
    gc = CV.group_columns(ed, label)
    col_of = dict(zip(gc["attr_id"], gc["column"]))
    assign = ed.variants[label].assign
    m = ed.mentions.copy()
    m["cluster_id"] = [col_of.get(assign.get(int(i), ""), "") for i in m["mention_id"]]
    cl = RL.cluster_labels(replace(ed, mentions=m), rules, extra)
    cl = cl[cl["cluster_id"] != ""].rename(columns={"cluster_id": "column"})
    base = set(ed.ctx_r.train)
    cl["kind"] = [column_kind(lab, a, base) for lab, a in zip(cl["label"], cl["top_attr"])]
    return cl[["column", "n", "label", "top_attr", "kind"]]


def entity_counts(ed, label, rules, extra):
    """dict of one entity and variant: found, gold, columns, found_columns (columns of found attributes), dup (extra columns of
    found attributes), kinds {KINDS: n columns}, merges_right / merges_judged."""
    fnd = RG.found(ed, label, rules, extra)
    dup = CV.dup_rows(ed, label, rules, extra)
    mg = RG.merges(ed, label, rules, extra)
    judged = mg[mg["judged"].astype(bool)]
    kinds = Counter(_column_labels(ed, label, rules, extra)["kind"])
    return {"found": int(fnd["found"].sum()), "gold": len(fnd), "columns": CV.n_columns(ed, label),
            "found_columns": int(dup["n_columns"].sum()), "dup": int((dup["n_columns"] - 1).sum()),
            "kinds": {k: kinds.get(k, 0) for k in KINDS}, "merges_right": int(judged["right"].astype(int).sum()),
            "merges_judged": len(judged)}


def dashboard_row(pb, label, name):
    """One dict (ROW_COLS) for variant `label` of the prepared bundle `pb` (prepare), shown as `name`."""
    rules = CE.rules_v11(2)
    per = {e: entity_counts(ed, label, rules, {}) for e, ed in pb["lev"].items()}
    nz = NV.noise_l2_rows(pb["raw"], {"gt_levels": pb["gt"]}, [label])
    nz = nz[["noise_n", "noise_marked", "marked_n", "marked_noise"]].sum()
    tot = lambda f: sum(per[e][f] for e in per)  # noqa: E731
    kinds = {k: sum(per[e]["kinds"][k] for e in per) for k in KINDS}
    found = {e: per[e]["found"] for e in per}
    ok, detail = guard_check(pb["set"], found)
    cpf = tot("found_columns") / tot("found") if tot("found") else float("nan")
    wrong = kinds["wrong"] + kinds["noise"]
    return {"set": pb["set"], "row": name, "n_runs": 1, **{f"found_{e}": found[e] for e in ENTS}, "found_total": tot("found"),
            "gold_total": tot("gold"), "columns": tot("columns"), "columns_per_found": round(cpf, 3), "dup_columns": tot("dup"),
            "wrong_columns": wrong, "wrong_entity_columns": kinds["wrong"], "noise_columns": kinds["noise"],
            "extras_no_gt": kinds["no_gt"], "merges_right": tot("merges_right"), "merges_judged": tot("merges_judged"),
            "noise_caught": int(nz["noise_marked"]), "noise_n": int(nz["noise_n"]), "marks_right": int(nz["marked_noise"]),
            "marks_n": int(nz["marked_n"]), "review_edits": tot("dup") + wrong, "guard": "pass" if ok else "FAIL",
            "guard_detail": detail, "cpf_bar": "pass" if cpf <= CPF_BAR else "FAIL"}


def range_row(rows, names, name):
    """Range row over the rows of `rows` (DataFrame of dashboard rows) called `names`: min-max of every count; guard =
    n/a (the guard is on the vote)."""
    r = rows[rows["row"].isin(names)]
    out = {"set": r["set"].iloc[0], "row": name, "n_runs": len(r)}
    for c in ROW_COLS[3:]:
        if c in ("guard", "guard_detail", "cpf_bar"):
            continue
        out[c] = span(list(r[c]), (lambda x: f"{x:.3f}") if c == "columns_per_found" else str)
    out["guard"] = "n/a"
    out["guard_detail"] = "worst order per entity: " + ", ".join(f"{e} {int(r[f'found_{e}'].min())}" for e in ENTS)
    out["cpf_bar"] = "pass" if r["columns_per_found"].max() <= CPF_BAR else "FAIL" if r["columns_per_found"].min() > CPF_BAR else "mixed"
    return out


def _cell(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def dashboard_md(df, title="wf_v3.8 precision dashboard (L2, rules v1.1, Step 1a v2.2)", notes=()):
    """Markdown of the dashboard: one table per set."""
    lines = [f"# {title}", ""]
    for s, g in df.groupby("set", sort=False):
        lines += [f"## {s}", "",
                  "| row | found train + hotel + rest. = total | cols | cols per found (bar 1.2) | dup cols | wrong cols (entity + noise) "
                  "| extras no GT | merges right | noise caught | marks right | review edits | recall guard |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            lines.append(
                f"| {r['row']} | {r['found_train']} + {r['found_hotel']} + {r['found_restaurant']} = {r['found_total']}/{r['gold_total']} "
                f"| {r['columns']} | {_cell(r['columns_per_found'])} ({r['cpf_bar']}) | {r['dup_columns']} | {r['wrong_columns']} "
                f"({r['wrong_entity_columns']} + {r['noise_columns']}) | {r['extras_no_gt']} | "
                f"{r['merges_right']}/{r['merges_judged']} | {r['noise_caught']}/{r['noise_n']} | {r['marks_right']}/{r['marks_n']} | "
                f"{r['review_edits']} | {r['guard']} ({r['guard_detail']}) |")
        lines.append("")
    return "\n".join(lines + [f"- {n}" for n in notes]) + "\n"


# ---- duplicates (task 3)

def _col_facts(ed, label, attr_id_of_col, rules, extra, attr):
    """dict of one column: groups, split (any group is a split part), n, top values, partner_share (share of its L2-labelled
    mentions whose slot forms a role pair with the slot of `attr`)."""
    vo = ed.variants[label]
    source = vo.attrs.set_index("attr_id")["source"].to_dict()
    groups = list(attr_id_of_col)
    ids = {int(i) for i, a in vo.assign.items() if a in set(groups)}
    m = ed.mentions[ed.mentions["mention_id"].astype(int).isin(ids)]
    pairs = RG._pairs(ed, rules, extra)
    slot = PS._slot(attr, ed.gold_ents)
    slots = [PS._slot(c, ed.gold_ents) for g in m["gold_attr"] for c in _classes(g)]
    partner = sum(frozenset((s, slot)) in pairs for s in slots)
    top = [v for v, _ in Counter(m["norm_value"]).most_common(3)]
    return {"groups": groups, "split": any(source.get(g) == "split" for g in groups), "n": len(m), "top_values": "|".join(top),
            "partner_share": partner / len(slots) if slots else 0.0}


def dup_pairs(ed, label, rules, extra):
    """DataFrame with one row per pair of columns that belong to the same found attribute: ent, attr, col_a, col_b, cause
    (CAUSES), split_a / split_b, same_role (both columns' partner-role share <= PARTNER_MAX), partner_a / partner_b, n_a / n_b,
    top values and the groups of each column."""
    gc = CV.group_columns(ed, label)
    fnd = RG.found(ed, label, rules, extra)
    rows = []
    for attr in fnd.loc[fnd["found"], "attr"]:
        g = gc[gc["majority"] == attr]
        facts = {c: _col_facts(ed, label, list(s["attr_id"]), rules, extra, attr) for c, s in g.groupby("column")}
        for a, b in combinations(sorted(facts), 2):
            fa, fb = facts[a], facts[b]
            rows.append({"ent": ed.ent, "attr": attr, "col_a": a, "col_b": b,
                         "cause": pair_cause(fa["split"], fb["split"], a, b), "split_a": fa["split"], "split_b": fb["split"],
                         "same_role": fa["partner_share"] <= PARTNER_MAX and fb["partner_share"] <= PARTNER_MAX,
                         "partner_a": round(fa["partner_share"], 3), "partner_b": round(fb["partner_share"], 3),
                         "n_a": fa["n"], "n_b": fb["n"], "values_a": fa["top_values"], "values_b": fb["top_values"],
                         "groups_a": ";".join(fa["groups"]), "groups_b": ";".join(fb["groups"])})
    return pd.DataFrame(rows, columns=PAIR_COLS)


PAIR_COLS = ["ent", "attr", "col_a", "col_b", "cause", "split_a", "split_b", "same_role", "partner_a", "partner_b", "n_a", "n_b",
             "values_a", "values_b", "groups_a", "groups_b"]


def dup_pair_rows(pb, label, name):
    """dup_pairs of every entity of the prepared bundle, with the columns set and row (= `name`)."""
    rules = CE.rules_v11(2)
    frames = [dup_pairs(ed, label, rules, {}) for ed in pb["lev"].values()]
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=PAIR_COLS)
    out.insert(0, "row", name)
    out.insert(0, "set", pb["set"])
    return out


def cause_counts(pairs):
    """DataFrame (row, cause columns..., pairs, same_role_pairs): pairs per cause for every row of a dup_pair_rows frame."""
    out = []
    for name, g in pairs.groupby("row", sort=False):
        c = Counter(g["cause"])
        out.append({"row": name, **{k: c.get(k, 0) for k in CAUSES}, "pairs": len(g), "same_role_pairs": int(g["same_role"].sum())})
    return pd.DataFrame(out, columns=["row", *CAUSES, "pairs", "same_role_pairs"])
