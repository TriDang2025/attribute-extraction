"""wf_v3.6 TEAR columns on dev50 (GT_V36_CONTRACT.md, W2 part 3): map every column of a TEAR output to a
MultiWOZ 2.2 attribute by value, and by name where the values do not decide.

TEAR output rows: {id, table: {headers, rows: [[cell, ...]]}} (cell = list of spans). A column is one header pooled
over all dialogues (TEAR's schema is fixed, so a header is one column of the variant).

Value mapping: a cell value (gt_ext.norm_value) is matched to the span values of the same dialogue (mwoz22_spans.csv,
no request rows). A cell votes for the (domain, slot) of its matching spans, 1 / k each for k candidates; candidates
of the header's own domain come first (a "booking" span belongs to the header's domain). The column label is the
majority (domain, slot) over the matched cells; a tie or fewer than MIN_CELLS matched cells gives "unmatched".
Unmatched columns get a second try against the 2.4 DB columns of the header's domain (source "db", L3).
Name mapping: a sheet of the unmatched columns for 2 blind raters (candidates = GT attrs of the header's domain).
Final label = the value label, else the name label.

Kinds (the T38 vocabulary of checks_v35.KINDS, so the table has the extras_table.md format): gt_found (label is a
TEAR/L1 attribute), extra_L2 (a non-L1 schema slot; also a rated name), extra_L3 (DB column), extra_none (no label),
wrong_extra (label of another domain, or `choice`). gt_partial is never used for TEAR.
"""

import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import gt_ext as G

MIN_CELLS = 2
SAMPLE_N = 5
NONE = "none"
KINDS = ("gt_found", "gt_partial", "extra_L2", "extra_L3", "extra_none", "wrong_extra")
COLUMN_COLS = ["column", "ent", "n_cells", "n_matched", "value_label", "value_ent", "value_source", "name_label",
               "final_label", "final_source", "kind"]
SHEET_COLS = ["row_id", "column", "sample_values", "candidates"]
RATER_COLS = ["row_id", "label"]


def header_domain(header, tear_map):
    """Domain of a TEAR header: from tear_to_mwoz ("Train day" -> train), else its first word lowercased."""
    slot = tear_map.get(header)
    return slot.partition("-")[0] if slot else re.split(r"\s+", str(header).strip().lower())[0]


def tear_cells(rows):
    """[(dialogue_id, header, [span, ...])] of every cell of the TEAR output rows."""
    out = []
    for r in rows:
        t = r.get("table") or {}
        for row in t.get("rows") or []:
            for header, cell in zip(t.get("headers") or [], row):
                spans = [cell] if isinstance(cell, str) else list(cell or [])
                out.append((G.dialogue_key(r["id"]), header, [str(s) for s in spans]))
    return out


def span_index(spans):
    """{dialogue_id: {norm value: [(domain, slot), ...]}} of the span rows of mwoz22_spans.csv (request rows skipped)."""
    idx = defaultdict(lambda: defaultdict(list))
    for r in spans.itertuples():
        if r.source == "request" or pd.isna(r.value):
            continue
        key = (str(r.domain), str(r.slot))
        nv = G.norm_value(r.value)
        if nv and key not in idx[G.dialogue_key(r.dialogue_id)][nv]:
            idx[G.dialogue_key(r.dialogue_id)][nv].append(key)
    return idx


def _candidates(cands, domain):
    """Candidates in the header's domain ("booking" counts as the header's domain), else all of them."""
    mine = [(domain if d == "booking" else d, s) for d, s in cands if d in (domain, "booking")]
    return mine or list(cands)


def _majority(votes):
    """(label, matched count) of a Counter of weighted votes: the unique top key, None on a tie or no votes."""
    if not votes:
        return None
    top = votes.most_common(2)
    return top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else None


def value_labels(cells, spans, tear_map, db_idx=None):
    """DataFrame, one row per header: column, n_cells (cells with a value), n_matched, value_label (attr name or ""),
    value_ent, value_source (span | db | ""). `spans` = mwoz22_spans DataFrame, `db_idx` = gt_ext.db_index(db) or None."""
    idx = span_index(spans)
    by = defaultdict(list)
    for did, header, values in cells:
        by[header] += [(did, v) for v in values if G.norm_value(v)]
    rows = []
    for header, vals in by.items():
        dom = header_domain(header, tear_map)
        votes, db_votes, n_span, n_db = Counter(), Counter(), 0, 0
        for did, v in vals:
            nv = G.norm_value(v)
            cands = _candidates(idx.get(did, {}).get(nv, []), dom)
            if cands:
                n_span += 1
                for c in cands:
                    votes[c] += 1 / len(cands)
            elif db_idx and nv in db_idx.get(dom, {}):
                n_db += 1
                db_votes[(dom, db_idx[dom][nv][0])] += 1
        label, source, n = None, "", 0
        if n_span >= MIN_CELLS:
            label, source, n = _majority(votes), "span", n_span
        if label is None and n_db >= MIN_CELLS:
            label, source, n = _majority(db_votes), "db", n_db
        if label is None:
            source, n = "", max(n_span, n_db)
        if label is None:
            name = ent = ""
        elif source == "db":
            name, ent = G.column_name(label[0], label[1], tear_map), label[0]
        else:
            name, ent = G.slot_name(label[0], label[1], tear_map), label[0]
            if label[1] == "choice":
                name = "choice"
        rows.append({"column": header, "n_cells": len(vals), "n_matched": n, "value_label": name, "value_ent": ent,
                     "value_source": source})
    return pd.DataFrame(rows, columns=["column", "n_cells", "n_matched", "value_label", "value_ent", "value_source"])


def candidate_names(domain, spans, tear_map):
    """GT attribute names of a domain (the L1 attrs plus the 2.2 slots found in the spans, `choice` left out)."""
    names = {a for a, s in tear_map.items() if not a.startswith("_") and s.partition("-")[0] == domain}
    for d, s in set(zip(spans["domain"].astype(str), spans["slot"].astype(str))):
        if d == domain and s != "choice":
            names.add(G.slot_name(d, s, tear_map))
    return sorted(names)


def name_sheet(columns, cells, spans, tear_map):
    """DataFrame (SHEET_COLS) of the columns whose value label is unmatched, for the blind name raters: the column name,
    up to SAMPLE_N most frequent values, candidate GT attrs (`;`-joined) of the column's domain, plus "none"."""
    values = defaultdict(Counter)
    for _, header, vals in cells:
        values[header].update(v for v in vals if G.norm_value(v))
    rows = []
    for c in columns.loc[columns["value_label"] == "", "column"]:
        sample = [v for v, _ in values[c].most_common(SAMPLE_N)]
        cands = candidate_names(header_domain(c, tear_map), spans, tear_map) + [NONE]
        rows.append({"row_id": len(rows), "column": c, "sample_values": " | ".join(sample), "candidates": ";".join(cands)})
    return pd.DataFrame(rows, columns=SHEET_COLS)


def read_name_labels(sheet, rater_paths):
    """(labels, disagree): labels = {column: name label} from the rater files (columns row_id, label; row_id of
    `sheet`). One rater: its label. Two raters who differ: the lower label wins; "none" is lowest, otherwise the
    candidate that comes first in the sheet's candidate list. disagree = DataFrame of the columns they rated
    differently (column, rater1, rater2, chosen). Missing files give no labels."""
    ratings = []
    for p in rater_paths:
        p = Path(p)
        if p.exists():
            d = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
            ratings.append(dict(zip(d["row_id"].astype(int), d["label"].str.strip())))
    cols = dict(zip(sheet["row_id"], sheet["column"]))
    cand = {r: c.split(";") for r, c in zip(sheet["row_id"], sheet["candidates"])}
    labels, diff = {}, []
    for rid, column in cols.items():
        got = [r[rid] for r in ratings if rid in r]
        if not got:
            continue
        rank = {c: i for i, c in enumerate([NONE] + [x for x in cand[rid] if x != NONE])}
        pick = min(got, key=lambda x: rank.get(x, len(rank)))
        labels[column] = pick
        if len(set(got)) > 1:
            diff.append({"column": column, "rater1": got[0], "rater2": got[1], "chosen": pick})
    return labels, pd.DataFrame(diff, columns=["column", "rater1", "rater2", "chosen"])


def final_columns(columns, name_labels, tear_map):
    """`columns` plus name_label, final_label, final_source (span | db | name | ""), kind, ent (the header's domain)."""
    l1 = {a for a in tear_map if not a.startswith("_")}
    out = []
    for r in columns.to_dict("records"):
        dom = header_domain(r["column"], tear_map)
        nl = name_labels.get(r["column"], "")
        label, source, ent = r["value_label"], r["value_source"], r["value_ent"]
        if not label and nl and nl != NONE:
            label, source, ent = nl, "name", dom
        if not label:
            kind = "extra_none"
        elif label == "choice" or ent != dom:
            kind = "wrong_extra"
        elif label in l1:
            kind = "gt_found"
        else:
            kind = "extra_L3" if source == "db" else "extra_L2"
        out.append({**r, "ent": dom, "name_label": nl, "final_label": label, "final_source": source, "kind": kind})
    return pd.DataFrame(out, columns=COLUMN_COLS)


def disagreements(cols, name_disagree):
    """Rows for tear_label_disagree.csv: the raters' differences, plus columns whose value label and name label both
    exist and differ (value label wins)."""
    both = cols[(cols["value_label"] != "") & (cols["name_label"] != "") & (cols["name_label"] != cols["value_label"])]
    rows = [{"column": r.column, "kind": "raters", "label_a": r.rater1, "label_b": r.rater2, "chosen": r.chosen}
            for r in name_disagree.itertuples()]
    rows += [{"column": r.column, "kind": "value_vs_name", "label_a": r.value_label, "label_b": r.name_label,
              "chosen": r.value_label} for r in both.itertuples()]
    return pd.DataFrame(rows, columns=["column", "kind", "label_a", "label_b", "chosen"])


def extras_rows(cols, variant="TEAR"):
    """Rows for checks_v35.extras_table (variant, ent, kind, name, majority_L1/L2/L3), one per column; the label sits at
    the level of its kind."""
    lvl = {"gt_found": "majority_L1", "extra_L2": "majority_L2", "extra_L3": "majority_L3"}
    rows = []
    for r in cols.to_dict("records"):
        row = {"variant": variant, "ent": r["ent"], "kind": r["kind"], "name": r["column"], "attr_id": r["column"],
               "majority_L1": "", "majority_L2": "", "majority_L3": ""}
        if r["kind"] in lvl:
            row[lvl[r["kind"]]] = r["final_label"]
        rows.append(row)
    return pd.DataFrame(rows)
