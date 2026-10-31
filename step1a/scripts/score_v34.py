"""wf_v3.4 scorer (SCORER_V34_CONTRACT.md): variants A-D under one rule setting, a sweep over the rules, a regression
check of the "old" setting against the v3.2 summary, and the report tables.

python scripts/score_v34.py --run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 \
    --out results/loop1_v34 --setting default            # -> <out>/scores_<slug>.csv
  --sweep         old, default and every single change from default -> <out>/sweep.csv, sweep.md
  --check-old     "old" setting vs <dir32>/summary.md (OLD_COLS, 3 decimals); prints mismatches, exit 1 if any
  --report-tables write the q*_table outputs of the stage-2 modules as CSV/PNG to <out>
Settings: "old", "default", "default,found=cov25,merge=n10" (s1a.score_rules.Rules.parse).
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import score_rules as SR  # noqa: E402
from s1a.score_rules import NEW_COLS, OLD_COLS, Rules  # noqa: E402

COLS = ["setting", "ent", "variant"] + OLD_COLS + NEW_COLS
SWEEP_SHOWN = ["recall", "noise_marked_v", "merge_prec", "place_acc", "name_acc"]


def slug(setting):
    return re.sub(r"[^A-Za-z0-9.]+", "_", setting).strip("_")


def score_setting(setting, data, shared, extra):
    """DataFrame (COLS) of all entities and variants under one setting."""
    rules = Rules.parse(setting)
    rows = [{"setting": setting, **r} for ed in data.values() for r in SR.score_entity(ed, shared, rules, extra)]
    return pd.DataFrame(rows, columns=COLS)


def _recall_cell(r):
    """"n/m" when found_n and gold_n are numbers (stage 2 present), else the recall value."""
    if isinstance(r["found_n"], str) or isinstance(r["gold_n"], str):
        return SR.fmt(r["recall_v"])
    return f"{int(r['found_n'])}/{int(r['gold_n'])}"


def sweep_md(df):
    """One markdown table per entity: a row per setting and variant, five shown measures."""
    lines = ["# wf_v3.4 sweep", "", "recall = found_n/gold_n (recall_v when stage 2 is missing); rest as in score_v34.py.", ""]
    for ent, g in df.groupby("ent", sort=False):
        lines += [f"## {ent}", "", "| setting | variant | " + " | ".join(SWEEP_SHOWN) + " |",
                  "|---|---|" + "---|" * len(SWEEP_SHOWN)]
        for _, r in g.iterrows():
            cells = [_recall_cell(r)] + [SR.fmt(r[c]) for c in SWEEP_SHOWN[1:]]
            lines.append(f"| {r['setting']} | {r['variant']} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def read_summary(path):
    """{(ent, "<variant> <run>"): {col: text}} from the markdown table of a v3.2 summary.md."""
    rows, header = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if header and rows:
                break  # the table ended
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] == "ent":
            header = cells
        elif header and not set(cells[0]) <= {"-"}:
            r = dict(zip(header, cells))
            rows[(r["ent"], f"{r['variant']} {r['run']}")] = r
    return rows


def check_old(df, summary_path):
    """Mismatch rows (ent, variant, col, summary, mine) between the old setting and the v3.2 summary (OLD_COLS)."""
    ref, mine = read_summary(summary_path), {(r["ent"], r["variant"]): r for _, r in df.iterrows()}
    bad = []
    for (ent, label), r in ref.items():
        if (ent, label) not in mine:
            bad.append((ent, label, "(row)", "present", "missing"))
            continue
        for c in OLD_COLS:
            got = SR.fmt(mine[(ent, label)][c], c == "noise_kept")
            if got != r[c]:
                bad.append((ent, label, c, r[c], got))
    return bad


def _write(df, path):
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


# (module, function) that --report-tables calls; the arguments are built in report_tables
REPORT = [("rules_labels", "q3_tables"), ("rules_labels", "q1_table"), ("rules_labels", "q2_table"),
          ("rules_labels", "q10_tables"), ("rules_groups", "q5_table"), ("rules_groups", "q6_table"),
          ("rules_groups", "q9_table")]


def report_tables(data, shared, extra, out):
    """Write each q*_table result (DataFrame, or dict / list of DataFrames) as CSV to `out`; skip missing functions."""
    default = Rules.default()
    other = extra.setdefault("_other_gold", {})
    for ent, ed in data.items():
        if ent not in other:
            other[ent] = SR._call("rules_labels", "other_gold_values", shared, ed)
    q2_settings = {"old": Rules.parse("default,cluster_label=old"),
                   **{t: Rules.parse(f"default,cluster_label={t}") for t in ("0.5", "0.6", "0.7")}}
    args = {"q3_tables": (data,), "q1_table": (data, shared), "q10_tables": (data,), "q9_table": (data,),
            "q2_table": (data, q2_settings, extra, out / "q2_top_share.png"),
            "q5_table": (data, default, extra), "q6_table": (data, default, extra)}
    for module, name in REPORT:
        fn = SR._lookup(module, name)
        if fn is None:
            print(f"skip {name}: not found in s1a.{module}")
            continue
        res = fn(*args[name])
        parts = res if isinstance(res, dict) else dict(enumerate(res)) if isinstance(res, (list, tuple)) else {"": res}
        for key, df in parts.items():
            if isinstance(df, pd.DataFrame):
                path = out / (f"{name}.csv" if key == "" else f"{name}_{key}.csv")
                _write(df, path)
                print(f"wrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--dir32", required=True, type=Path)
    ap.add_argument("--dir31", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--setting", default="default")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--check-old", action="store_true")
    ap.add_argument("--report-tables", action="store_true")
    a = ap.parse_args()

    from s1a import v34_data  # noqa: E402  (W1; imported late so --help works without it)
    shared, data = v34_data.load_all(a.run, a.dir32, a.dir31)
    a.out.mkdir(parents=True, exist_ok=True)
    extra = SR.load_extra(a.out, a.dir32)

    if a.check_old:
        bad = check_old(score_setting("old", data, shared, extra), a.dir32 / "summary.md")
        for ent, label, col, want, got in bad:
            print(f"MISMATCH {ent} {label} {col}: summary {want}, scored {got}")
        print(f"check-old: {len(bad)} mismatches")
        sys.exit(1 if bad else 0)
    if a.sweep:
        df = pd.concat([score_setting(s, data, shared, extra) for s in SR.single_changes()], ignore_index=True)
        _write(df, a.out / "sweep.csv")
        (a.out / "sweep.md").write_text(sweep_md(df), encoding="utf-8", newline="\n")
        print(f"wrote sweep.csv and sweep.md in {a.out} ({df['setting'].nunique()} settings)")
    if a.report_tables:
        report_tables(data, shared, extra, a.out)
    if not (a.sweep or a.report_tables):
        df = score_setting(a.setting, data, shared, extra)
        path = a.out / f"scores_{slug(a.setting)}.csv"
        _write(df, path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
