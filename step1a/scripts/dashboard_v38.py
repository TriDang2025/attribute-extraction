"""wf_v3.8 W1 tasks 1-3: precision dashboard, A s012 without the split pass, list of duplicate columns. No GPU, no LLM.

python scripts/dashboard_v38.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--out results/loop1_v38/dash]
Step 0 (printed, stops on a mismatch): A s012 on Step 1a v2.2 reproduces results/loop1_v37/t14.md (found 31/40 and 29/41,
columns 67 / 56, columns per found 1.742 / 1.552).
Writes <out>/{dashboard.csv, dashboard.md, dups_dev50.csv, dups_dev50b.csv, dups.md, split_pass_decision.md}.
Later phases: `from dashboard_v38 import load_v22, rows_for` and add rows with rows_for(prepared bundle, labels, names);
`DB.prepare(set, raw bundle, gt)` (s1a/dashboard_v38.py) makes the prepared bundle of any {ent: EntityData}.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import score_t14_v37 as T14S  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import nosplit_v38 as NS  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402

OLD_ORDERS, NEW_ORDERS, VOTE = T14S.OLD_ORDERS, T14S.NEW_ORDERS, T14S.VOTE
SETS = {"dev50": {"run": "results/graph_v22_dev50", "key": None, "orders": OLD_ORDERS},
        "dev50b": {"run": "results/graph_v22_dev50b", "key": "v22d50b", "orders": NEW_ORDERS}}
EXPECT = {"dev50": {"found": (8, 12, 11), "columns": 67, "cpf": 1.742},
          "dev50b": {"found": (8, 10, 11), "columns": 56, "cpf": 1.552}}


def parser():
    ap = T14S.parser()
    ap.set_defaults(out=Path("results/loop1_v38/dash"))
    return ap


def load_v22(a, set_name):
    """Raw bundle {ent: EntityData} of A on Step 1a v2.2 for the set: the three orders and the vote A s012."""
    s = SETS[set_name]
    repairs = []
    load = T14S.load_old(a, repairs) if s["key"] is None else T14S.load_new(a, Path(s["run"]), s["key"], repairs)
    return load[1]


def load_both(a, gts):
    """{(set, "split" | "nosplit"): prepared bundle}."""
    out = {}
    for name in SETS:
        out[(name, "split")] = DB.prepare(name, load_v22(a, name), gts[name])
        with NS.no_split():
            out[(name, "nosplit")] = DB.prepare(name, load_v22(a, name), gts[name])
    return out


def rows_for(pb, labels, names):
    """DataFrame of dashboard rows for `labels` of one prepared bundle, shown as `names` (same length)."""
    return pd.DataFrame([DB.dashboard_row(pb, l, n) for l, n in zip(labels, names)], columns=DB.ROW_COLS)


def check_step0(rows):
    """List of mismatches against EXPECT for the A s012 rows (empty when it reproduces)."""
    bad = []
    for s, e in EXPECT.items():
        r = rows[(rows["set"] == s) & (rows["row"] == "A s012")].iloc[0]
        got = (int(r["found_train"]), int(r["found_hotel"]), int(r["found_restaurant"]))
        if got != e["found"] or int(r["columns"]) != e["columns"] or abs(float(r["columns_per_found"]) - e["cpf"]) > 5e-4:
            bad.append(f"{s}: got found {got}, columns {r['columns']}, cpf {r['columns_per_found']}; expected {e}")
    return bad


def decision(rows):
    """(lines, drop?) of the split-pass decision: drop when the nosplit vote passes the recall guard on both sets and its
    columns per found attribute are lower than the vote with the split pass on both sets."""
    lines, ok = [], True
    for s in SETS:
        a = rows[(rows["set"] == s) & (rows["row"] == "A s012")].iloc[0]
        b = rows[(rows["set"] == s) & (rows["row"] == "A s012 nosplit")].iloc[0]
        g = b["guard"] == "pass"
        lower = float(b["columns_per_found"]) < float(a["columns_per_found"])
        ok &= g and lower
        lines.append(f"- {s}: A s012 found {a['found_total']}/{a['gold_total']} ({a['guard_detail']}), columns per found "
                     f"{a['columns_per_found']}, dup {a['dup_columns']}, columns {a['columns']}; nosplit found {b['found_total']}/"
                     f"{b['gold_total']} ({b['guard_detail']}), columns per found {b['columns_per_found']}, dup {b['dup_columns']}, "
                     f"columns {b['columns']}. Guard {b['guard']}; columns per found {'down' if lower else 'NOT down'}.")
    return lines, ok


def dups_md(counts):
    lines = ["# wf_v3.8 duplicate columns of A s012, with and without the split pass (L2, rules v1.1)", "",
             "A pair = two columns (distinct normalised output names) whose groups have the same found attribute as majority L2 "
             "label (a found attribute with k columns gives k(k-1)/2 pairs). Causes, in this order: **split_pass** = a column "
             "comes from a split part (group id `cluster/k`); **neighbourhood** = columns from different neighbourhood groups: "
             "always 0 for A, which reads one entity prompt and has no neighbourhoods; **wording** = unsplit columns whose names "
             "share a content word (entity word dropped, plural s removed), the same thing worded twice; **other** = unsplit "
             "columns whose names share no word. Same role = both columns have <= 20% of their L2-labelled mentions in the "
             "role-pair partner slot of the attribute (config/role_pairs.json).", ""]
    for s, g in counts.groupby("set", sort=False):
        lines += [f"## {s}", "", "| row | split_pass | neighbourhood | wording | other | pairs | same role |", "|---|---|---|---|---|---|---|"]
        lines += [f"| {r['row']} | {r['split_pass']} | {r['neighbourhood']} | {r['wording']} | {r['other']} | {r['pairs']} | "
                  f"{r['same_role_pairs']}/{r['pairs']} |" for _, r in g.iterrows()]
        lines.append("")
    lines += ["Full lists: dups_dev50.csv, dups_dev50b.csv (columns set, row, ent, attr, col_a, col_b, cause, same_role, partner "
              "shares, top values, groups).", ""]
    return "\n".join(lines)


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in T14S.GT.items()}
    pbs = load_both(a, gts)
    frames, pair_frames = [], []
    for s in SETS:
        orders = list(SETS[s]["orders"])
        ns_orders = [f"{o} nosplit" for o in orders]
        sp, ns = pbs[(s, "split")], pbs[(s, "nosplit")]
        df = rows_for(sp, orders + [VOTE], orders + ["A s012"])
        d2 = rows_for(ns, orders + [VOTE], ns_orders + ["A s012 nosplit"])
        both = pd.concat([df, d2], ignore_index=True)
        rng = pd.DataFrame([DB.range_row(both, orders, "A, 3 orders (range)"),
                            DB.range_row(both, ns_orders, "A, 3 orders nosplit (range)")])
        frames.append(pd.concat([df[df["row"] == "A s012"], d2[d2["row"] == "A s012 nosplit"], rng,
                                 df[df["row"] != "A s012"], d2[d2["row"] != "A s012 nosplit"]], ignore_index=True))
        pair_frames.append(pd.concat([DB.dup_pair_rows(sp, VOTE, "A s012"), DB.dup_pair_rows(ns, VOTE, "A s012 nosplit")],
                                     ignore_index=True))
    rows = pd.concat(frames, ignore_index=True)
    bad = check_step0(rows)
    if bad:
        print("STEP 0 FAILED:\n" + "\n".join(bad))
        write_csv(rows, a.out / "dashboard_step0_failed.csv")
        sys.exit(1)
    print("step 0 ok: A s012 reproduces t14.md")
    write_csv(rows, a.out / "dashboard.csv")
    write(a.out / "dashboard.md", DB.dashboard_md(rows, notes=[
        "Columns = distinct normalised output names of unmarked groups. Columns per found attribute = columns whose group majority is "
        "a found attribute / found attributes (t14.md). Duplicate columns = sum over found attributes of (columns - 1). Wrong columns "
        "= columns with label noise (>= 60% noise mentions) + columns with label real whose top attribute is another entity's. Extras "
        "with no GT = columns with no L2 attribute at >= 60% and not noise (mixed / unknown). Review edits = duplicate + wrong columns. "
        "Merges: rules v1.1 merge rule, judged merges only. Noise: the model-free noise set; marks right = marked clusters that are "
        "noise. Recall guard: RULES_V1_2.md per entity; range rows are n/a (the guard is on the vote).",
        "Orders: dev50 = A r1 / A r2 / A s2, dev50b = A s0 / A s1 / A s2."]))
    for s, p in zip(SETS, pair_frames):
        write_csv(p, a.out / f"dups_{s}.csv")
    allp = pd.concat(pair_frames, ignore_index=True)
    counts = pd.concat([DB.cause_counts(g).assign(set=s) for s, g in allp.groupby("set", sort=False)], ignore_index=True)
    write(a.out / "dups.md", dups_md(counts))
    lines, drop = decision(rows)
    write(a.out / "split_pass_decision.md",
          "# wf_v3.8 A s012 without the split pass\n\nVariant: every cluster keeps its A decision (the v3.1 split prompts are not read: "
          "`s1a/nosplit_v38.py`); the 3 orders and the vote are rebuilt, nothing else changes. Rule: drop the split pass if the "
          "nosplit vote passes the recall guard (RULES_V1_2.md, per entity) and columns per found attribute go down, on both sets.\n\n"
          + "\n".join(lines) + f"\n\n**Decision: {'DROP the split pass' if drop else 'KEEP the split pass'}.**\n")
    print("\n".join(lines))
    print("drop split pass:", drop)


if __name__ == "__main__":
    main()
