"""wf_v3.5 re-score: every variant (v3.2 A-D from the v3.4 bundle, v3.3 C / E / E1 / E2) under one rule setting at GT
levels 1, 2 and 3 (results/loop1_v35/gt_levels.csv). No LLM, no models.

python scripts/score_v35.py --setting default --levels 1,2,3 --dir33 <attribute-extraction-wf-v3.3/step1a/results/loop1_v33>
        [--run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 --out results/loop1_v35]
        [--repair [--repairs-out results/loop1_v36/repairs.csv]] [--invalid config/invalid_runs_v36.json]
Writes <out>/all_variants.csv (setting, level, ent, variant + OLD_COLS + NEW_COLS, every label incl. +namemerge) and
<out>/all_variants.md (one table per level, variants x counts over the 3 entities). "default" = rules v1 (score_rules.DEFAULT);
Rules.gt is set per level. v3.3 variants are scored with the P4 cue spread (as in v3.3); the v3.2 ones without (as in v3.4).
Names of the v3.3 variants are not in the rated sheet: unrated groups count as not right and are shown as "[u unrated]".
wf_v3.6 flags (both off by default, which keeps the output above unchanged): --repair parse-repairs the A responses
(llm_cache.repair_undeclared: names used in `clusters` but not declared join the attribute list) and writes the repaired
names to --repairs-out (columns variant, ent, job, repaired_names, n_repaired); --invalid picks the invalid-runs file
that marks cells "invalid" in all_variants.md (default config/invalid_runs.json).
"""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import v34_data, v35_data  # noqa: E402
from s1a.score_rules import NEW_COLS, OLD_COLS, Rules  # noqa: E402

COLS = ["setting", "level", "ent", "variant"] + OLD_COLS + NEW_COLS
SHOWN = ["A r1", "A r2", "B s0", "C s0", "C s1", "C s2", "C s012", "D s012", "C33 s012", "E s012", "E1 s012", "E2 s012"]
ENTS = ("train", "hotel", "restaurant")


def score_levels(setting, levels, data, shared, extra, data33=None):
    """DataFrame (COLS) of every entity and variant label at each level; `data33` (v35_data.load_v33) is scored with the
    same rules, on its own copy of `extra`."""
    base = Rules.parse(setting)
    groups = [(data, extra)] + ([(data33, {k: v for k, v in extra.items() if not k.startswith("_")})] if data33 else [])
    rows = []
    for level in levels:
        rules = replace(base, gt=f"L{level}")
        for d, ex in groups:
            rows += [{"setting": setting, "level": level, **r} for ed in d.values()
                     for r in SR.score_entity(ed, shared, rules, ex)]
    return pd.DataFrame(rows, columns=COLS)


def _total(g, *cols):
    """Sum of numeric columns over the entity rows of one variant; None when a column has no number."""
    out = []
    for c in cols:
        v = pd.to_numeric(g[c], errors="coerce")
        out.append(None if v.isna().all() else float(v.sum()))
    return out


def _pair(g, k, n, extra=""):
    ks, ns = _total(g, k, n)
    return SR.NA if ks is None or ns is None else SR.fmt_count(ks, ns) + extra


def variant_cells(g, invalid=()):
    """Table cells of one variant (its entity rows `g`): found per entity, pooled noise, merge, names, role, cue.
    Entities in `invalid` show "invalid" and are left out of the pooled cells."""
    found = []
    for ent in ENTS:
        r = g[g["ent"] == ent]
        found.append("invalid" if ent in invalid else SR.fmt_count(r["found_n"].iloc[0], r["gold_n"].iloc[0])
                     if len(r) else SR.NA)
    g = g[~g["ent"].isin(invalid)]
    pooled = SR.pooled_noise(g)
    (unjudged,) = _total(g, "merge_unjudged")
    (unrated,) = _total(g, "names_unrated")
    return found + [
        SR.fmt_count(pooled["marked"], pooled["n"]),
        _pair(g, "merge_right", "merge_n", f" +{int(unjudged)} unjudged" if unjudged else ""),
        _pair(g, "name_right", "name_base", f" [{int(unrated)} unrated]" if unrated else ""),
        _pair(g, "role_right", "role_base"),
        _pair(g, "cue_request", "cue_clusters")]


HEAD = ["found train", "found hotel", "found restaurant", "noise pooled (target >= 0.70)", "merge right/judged",
        "names right/base", "role right/base", "cue request/clusters"]


def all_variants_md(df, invalid_path=RN.INVALID_RUNS_PATH):
    lines = ["# wf_v3.5 all variants", "",
             f"Setting `{df['setting'].iloc[0]}`; GT level 1 = TEAR gold, 2 = + MultiWOZ 2.2 schema slots, 3 = + DB columns "
             "(choice mentions are noise at every level). Counts are k/n (share); noise, merge, names, role and cue are "
             "summed over the 3 entities. C33 = v3.2 C scored with the cue spread (v3.3 way). Names of the v3.3 variants "
             "are not rated: unrated groups count as not right. At L2/L3 a valid_extra group counts as right when its "
             "majority attr is a non-L1 attr of the level (approximation). Placement is not used.", ""]
    bad = RN.invalid_runs(invalid_path)
    for level, lv in df.groupby("level", sort=True):
        lines += [f"## Level {level}", "", "| variant | " + " | ".join(HEAD) + " |", "|---|" + "---|" * len(HEAD)]
        for variant in SHOWN:
            g = lv[lv["variant"] == variant]
            if len(g):
                invalid = {r["ent"] for r in bad if r["variant"] == variant}
                lines.append(f"| {variant} | " + " | ".join(variant_cells(g, invalid)) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


REPAIR_COLS = ["variant", "ent", "job", "repaired_names", "n_repaired"]


def repairs_frame(rows):
    """DataFrame (REPAIR_COLS) of repair rows [{variant, ent, job, repaired_names: [str]}]; names as a JSON list."""
    return pd.DataFrame([{**r, "repaired_names": json.dumps(r["repaired_names"]), "n_repaired": len(r["repaired_names"])}
                         for r in rows], columns=REPAIR_COLS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=Path("results/graph_v22_dev50"))
    ap.add_argument("--dir32", type=Path, default=Path("results/loop1_v32"))
    ap.add_argument("--dir31", type=Path, default=Path("results/loop1_v31"))
    ap.add_argument("--dir33", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v35"))
    ap.add_argument("--setting", default="default")
    ap.add_argument("--levels", default="1,2,3")
    ap.add_argument("--repair", action="store_true", help="parse-repair the A responses (undeclared attribute names)")
    ap.add_argument("--repairs-out", type=Path, default=Path("results/loop1_v36/repairs.csv"))
    ap.add_argument("--invalid", type=Path, default=RN.INVALID_RUNS_PATH, help="invalid-runs JSON (default config/invalid_runs.json)")
    a = ap.parse_args()

    levels = [int(x) for x in a.levels.split(",")]
    repairs = [] if a.repair else None
    shared, data = v34_data.load_all(a.run, a.dir32, a.dir31, repairs)
    data33, notes = v35_data.load_v33(shared, data, a.dir33, a.dir32)
    extra = SR.load_extra(a.out, a.dir32)
    extra["gt_levels"] = v34_data.read_gt_levels(a.out / "gt_levels.csv")
    df = score_levels(a.setting, levels, data, shared, extra, data33)
    df.to_csv(a.out / "all_variants.csv", index=False, encoding="utf-8", lineterminator="\n")
    if a.repair:
        a.repairs_out.parent.mkdir(parents=True, exist_ok=True)
        repairs_frame(repairs).to_csv(a.repairs_out, index=False, encoding="utf-8", lineterminator="\n")
        print(f"wrote {a.repairs_out} ({len(repairs)} repaired responses)")
    md = all_variants_md(df, a.invalid) + "".join(f"\nNote: {n}\n" for n in notes)
    (a.out / "all_variants.md").write_text(md, encoding="utf-8", newline="\n")
    print(f"wrote all_variants.csv and all_variants.md in {a.out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
