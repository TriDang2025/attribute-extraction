"""wf_v3.7 T3: duplicate columns. A column is a distinct output attribute name (PV.norm_name) of a variant; a group
marked not_attribute / unsure / attribute_cue is no column. For every attribute that the variant finds
(`rules_groups.found`, rules v1.1), the number of columns whose group has that attribute as its majority label
(`rules_names._variant_rows`, read at the entity data's GT level). No models, no LLM.
"""

import pandas as pd

from . import pilot_verify as PV
from . import rules_groups as RG
from . import rules_names as RN

DUP_COLS = ["variant", "ent", "attr", "n_columns", "n_groups", "columns"]
UNNAMED = "(unnamed)"


def group_columns(ed, label):
    """DataFrame (attr_id, column, majority) of the groups of `label` that are columns: status not marked. `column` is
    the normalised group name (UNNAMED for an empty one); majority = the group's majority label at the level ("" none)."""
    status = ed.variants[label].attrs.set_index("attr_id")["status"].to_dict()
    rows = [{"attr_id": r["attr_id"], "column": PV.norm_name(r["name"]) or UNNAMED, "majority": r["majority_gold_attr"]}
            for r in RN._variant_rows(ed, label, {}) if status.get(r["attr_id"]) not in PV.MARKED]
    return pd.DataFrame(rows, columns=["attr_id", "column", "majority"])


def n_columns(ed, label):
    """Distinct column names of the variant (all groups that are columns)."""
    return group_columns(ed, label)["column"].nunique()


def dup_rows(ed, label, rules, extra):
    """One row per found attribute of the entity (DUP_COLS): n_columns = distinct column names among the groups whose
    majority label is the attribute, n_groups = those groups, columns = the names joined by " | "."""
    cols = group_columns(ed, label)
    fnd = RG.found(ed, label, rules, extra)
    rows = []
    for attr in fnd.loc[fnd["found"], "attr"]:
        g = cols[cols["majority"] == attr]
        names = sorted(g["column"].unique())
        rows.append({"variant": label, "ent": ed.ent, "attr": attr, "n_columns": len(names), "n_groups": len(g),
                     "columns": " | ".join(names)})
    return pd.DataFrame(rows, columns=DUP_COLS)


def dup_summary(rows):
    """dict: found (attributes), mean (columns per found attribute), max, dup (attributes with >= 2 columns)."""
    n = len(rows)
    return {"found": n, "mean": rows["n_columns"].sum() / n if n else float("nan"),
            "max": int(rows["n_columns"].max()) if n else 0, "dup": int((rows["n_columns"] >= 2).sum())}


def dup_md(rows, variants):
    lines = ["# wf_v3.7 duplicate columns at L2 (rules v1.1)", "",
             "Column = a distinct output attribute name (case, `_`, `-` and space equal) of a group that is not marked "
             "not_attribute / unsure / attribute_cue. Columns per found attribute = the number of distinct column names "
             "whose group has that found attribute as majority L2 label (a group with no L2 majority is in no count). "
             "Found = purity >= 0.6 and coverage >= 10% (rules v1). Pooled over train, hotel, restaurant.", "",
             "| variant | found | columns per found attribute (mean) | max | attributes with >= 2 columns |",
             "|---|---|---|---|---|"]
    for v in variants:
        s = dup_summary(rows[rows["variant"] == v])
        lines.append(f"| {v} | {s['found']} | {s['mean']:.3f} | {s['max']} | {s['dup']} |")
    lines += ["", "## Attributes with 2 or more columns", "", "| variant | ent | attribute | columns |", "|---|---|---|---|"]
    for v in variants:
        for _, r in rows[(rows["variant"] == v) & (rows["n_columns"] >= 2)].iterrows():
            lines.append(f"| {v} | {r['ent']} | {r['attr']} | {r['n_columns']}: {r['columns']} |")
    return "\n".join(lines) + "\n"
