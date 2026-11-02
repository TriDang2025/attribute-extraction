"""wf_v3.6 column precision (T41) and the v3.3 F / F2 de-lexicalisation re-score (task 11); GT_V36_CONTRACT.md, W2.

T41: every output column of a variant (a distinct attribute name per entity, not a group) gets exactly one bucket at
GT level 1 or 2, from the T38 extras (checks_v35.extras_by_level):
- gt: the column's majority label at that level is a GT attribute (L1: majority_L1; L2: majority_L1 or majority_L2);
- wrong: wrong_extra (majority noise / cue / wrong_entity / other_entity), or `choice`;
- extra_confirmed: no GT majority at that level, but a majority at a higher level (L1: L2 or L3; L2: L3);
- extra_none: everything else.
A name used by several attributes of one entity counts once, in the best bucket (gt, extra_confirmed, extra_none, wrong).

Task 11: F (v3.3, broken map) and E seed 0 read the same way: one order (seed 0), no gate or split, plus the F2 hook
(`seed0_variants` with `var="f2"` on the v3.6 Colab folder).
"""

from dataclasses import replace

import pandas as pd

from . import pilot_combine as PC
from . import pilot_verify as PV
from . import score_rules as SR
from . import v35_data as V35
from pilot_eval_v32 import _have, _jobs  # noqa: E402  (scripts/ is on sys.path via s1a.v34_data)

BUCKETS = ("gt", "extra_confirmed", "extra_none", "wrong")
PRECEDENCE = {b: i for i, b in enumerate(BUCKETS)}
LEVELS = (1, 2)


# ---- T41

def bucket(row, level):
    """Bucket of one extras row (kind, majority_L1/L2/L3) at GT level 1 or 2 (BUCKETS)."""
    m1, m2, m3 = row["majority_L1"], row["majority_L2"], row["majority_L3"]
    gt = bool(m1) if level == 1 else bool(m1 or m2)
    if row["kind"] == "gt_found" or (gt and row["kind"] != "wrong_extra"):
        return "gt"
    if row["kind"] == "wrong_extra":
        return "wrong"
    higher = bool(m2 or m3) if level == 1 else bool(m3)
    return "extra_confirmed" if higher else "extra_none"


def column_buckets(extras, level):
    """DataFrame (variant, ent, column, bucket): one row per variant, entity and distinct attribute name of `extras`
    (extras_by_level rows plus variant, ent). Same-name attributes keep the best bucket."""
    t = extras.assign(column=[PV.norm_name(n) for n in extras["name"]],
                      bucket=[bucket(r, level) for _, r in extras.iterrows()])
    t = t.assign(rank=t["bucket"].map(PRECEDENCE)).sort_values("rank", kind="stable")
    return t.drop_duplicates(["variant", "ent", "column"])[["variant", "ent", "column", "bucket"]]


def precision_table(extras, invalid=(), order=None):
    """DataFrame (level, variant, columns, + one count per bucket) pooled over entities. `invalid` = [{ent, variant}]
    runs left out. `order` = variant order."""
    skip = {(r["ent"], r["variant"]) for r in invalid}
    rows = []
    for level in LEVELS:
        b = column_buckets(extras, level)
        b = b[[(e, v) not in skip for e, v in zip(b["ent"], b["variant"])]]
        for variant in order or list(dict.fromkeys(b["variant"])):
            g = b[b["variant"] == variant]
            if len(g):
                rows.append({"level": level, "variant": variant, "columns": len(g),
                             **{k: int((g["bucket"] == k).sum()) for k in BUCKETS}})
    return pd.DataFrame(rows, columns=["level", "variant", "columns", *BUCKETS])


def precision_md(table, notes=()):
    lines = ["# wf_v3.6 column precision (T41)", "",
             "Each output column (a distinct attribute name per entity, not a group) is in exactly one bucket, pooled over "
             "train / hotel / restaurant: gt = majority label is a GT attr of the level; extra_confirmed = no GT label at "
             "that level but confirmed at a higher one (L1: L2 or L3, L2: L3); extra_none = no label; wrong = wrong entity, "
             "noise or `choice`. Counts are k/n (share of the variant's columns). Rules v1.", ""]
    lines += [f"- {n}" for n in notes] + ([""] if notes else [])
    for level, g in table.groupby("level"):
        lines += [f"## Level {level}", "", "| variant | columns | " + " | ".join(BUCKETS) + " |",
                  "|---|---|" + "---|" * len(BUCKETS)]
        for r in g.to_dict("records"):
            lines.append(f"| {r['variant']} | {r['columns']} | "
                         + " | ".join(SR.fmt_count(r[k], r["columns"]) for k in BUCKETS) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---- task 11: seed-0 variants (F, E s0, F2 hook)

def seed0_decisions(out_dir, ent, var, shared=None, repairs=None):
    """Vote table of one order (seed 0), no gate or split, of the entity jobs of variant `var` (e | f | f2 | ...) in
    `out_dir`; None when a response file is missing. Same reading as v3.3 F (decisions_e with var f).
    `repairs` (list or None): opt-in parse repair, rows {job, repaired_names} (pilot_combine.load_obj)."""
    jobs = [j for j in _jobs(out_dir) if j["ent"] == ent and j["kind"] == "entity" and j["variant"] == var
            and j["run_tag"] == "s0"]
    if not _have(out_dir, jobs):
        return None
    return PC.vote([PC.decisions_b(out_dir, ent, 0, {}, variant=var, repairs=repairs)])[0]


def seed0_variants(data33, shared, out_dir, specs, repairs=None):
    """New EntityData dict: `data33` (v35_data.load_v33 output) with one more variant per spec (label letter, job
    variant, e.g. ("F", "f"), ("E", "e"), ("F2", "f2")), labelled "<letter> s0", scored with the cue spread like the
    v3.3 variants. Entities without responses for a spec skip it; returns (data, notes). `repairs` (list or None):
    opt-in parse repair; a row {variant, ent, job, repaired_names} is appended for each repaired response."""
    left_words = PV.left_word_map(shared.e.mentions, shared.docs)
    out, notes = {}, []
    for ent, ed in data33.items():
        variants = dict(ed.variants)
        for letter, var in specs:
            rows = None if repairs is None else []
            dec = seed0_decisions(out_dir, ent, var, repairs=rows)
            if rows:
                repairs.extend({"variant": f"{letter} s0", "ent": ent, **r} for r in rows)
            if dec is None:
                notes.append(f"{ent}: {letter} s0 skipped, `{var}` seed-0 responses missing in {out_dir}")
                continue
            dec = dec.assign(variant=letter, run_tag="s0")
            variants[f"{letter} s0"] = V35._finalize_cue(dec, shared, ed.ctx_r, ed.entity, left_words)
        out[ent] = replace(ed, variants=variants)
    return out, notes


def only(data, labels):
    """Copy of {ent: EntityData} keeping only the variant labels in `labels`."""
    return {ent: replace(ed, variants={k: v for k, v in ed.variants.items() if k in labels}) for ent, ed in data.items()}


def kinds_md(title, table, notes=()):
    """Markdown of a variants x kinds table (checks_v35.extras_table output, KINDS + total columns)."""
    cols = list(table.columns)
    lines = [f"# {title}", ""] + [f"- {n}" for n in notes] + [""]
    lines += ["| variant | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    lines += [f"| {v} | " + " | ".join(str(int(r[c])) for c in cols) + " |" for v, r in table.iterrows()]
    return "\n".join(lines) + "\n"
