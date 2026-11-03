"""wf_v3.8 Phase 1, W2 (tasks 5 and 6): wrong merges of A s012 on Step 1a v2.2, and what A did with the J-split parts of v2.3.
No models, no LLM.

python scripts/merges_v38.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--merges-out results/loop1_v38/merges]
Reads the same runs as scripts/score_t14_v37.py (RUNS, load_old / load_new, rules v1.1 at L2; rated names from --out, default
results/loop1_v37, only read). Writes <merges-out>/{merges_wrong_<set>.csv, j_parts_<set>.csv, merges.md}.
"""

import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import a_s012_v37 as AS  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import merges_v38 as M  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import rules_groups as RG  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from s1a import v36_data as V36  # noqa: E402
import score_t14_v37 as T  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402

LEVEL = 2
NM = "A+namemerge s012"


def parser():
    ap = T.parser()
    ap.add_argument("--merges-out", type=Path, default=Path("results/loop1_v38/merges"))
    return ap


def load(a, key_pair, repairs):
    """(shared, bundle at the A orders + vote, plus the +namemerge copy of the vote, notes) of one (set, version)."""
    run_dir, key = T.RUNS[key_pair]
    shared, bundle, notes = T.load_old(a, repairs) if key is None else T.load_new(a, Path(run_dir), key, repairs)
    out = {}
    for ent, ed in bundle.items():
        variants = dict(ed.variants)
        V36._add(variants, "A s012", ed.variants["A s012"].dec, shared.e, ed.ctx_a, ed.entity)  # adds A+namemerge s012
        out[ent] = replace(ed, variants={k: v for k, v in variants.items() if k in (*ed.variants, NM)})
    return shared, out, notes


def maps_names(ed, orders, vote):
    labels = (*orders, vote, NM)
    return ({lab: M.cluster_groups(ed.variants[lab].attrs) for lab in labels},
            {lab: M.decision_names(ed.variants[lab].dec) for lab in labels})


def wrong_rows(set_name, version, lev, rules, orders):
    """(rows of A s012, rows of the name merge that A s012 does not have, {ent: found count}, counts of all merges)."""
    rows, nm_rows, found, tot = [], [], {}, {"merges": 0, "nm_merges": 0, "nm_wrong": 0, "unjudged": 0, "right_blocked": 0}
    for ent, ed in lev.items():
        maps, names = maps_names(ed, orders, "A s012")
        ctx = {"set": set_name, "version": version, "ent": ent}
        mg, mg_nm = RG.merges(ed, "A s012", rules, {}), RG.merges(ed, NM, rules, {})
        men = RG._mentions(ed, "A s012", rules, {})
        rows += M.wrong_merge_rows(ctx, mg, men, orders, "A s012", maps, names, "A prompt")
        nm_rows += M.wrong_merge_rows(ctx, mg_nm, RG._mentions(ed, NM, rules, {}), orders, "A s012", maps, names,
                                      "name merge", variant=NM, skip_attrs=set(mg["attr_id"]))
        tot["right_blocked"] += M.blocked_right(mg, names, orders, "A s012")
        found[ent] = int(RG.found(ed, "A s012", rules, {})["found"].sum())
        tot["merges"] += int(mg["judged"].sum())
        tot["unjudged"] += int((~mg["judged"].astype(bool)).sum())
        tot["nm_merges"] += int(mg_nm["judged"].sum())
        tot["nm_wrong"] += int((mg_nm["judged"].astype(bool) & ~mg_nm["right"].astype(bool)).sum())
    return rows, nm_rows, found, tot


def role_table(set_name, version, lev, rules, rated, ceil):
    """Rows (set, version, ent, attr, found, recoverable, groups, cause) for the role base attributes of A s012."""
    got = RN._rated_by_key(rated, RN.L2_LABELS)
    out = []
    for ent, ed in lev.items():
        base = [x for x in ed.ctx_a.train if PS._slot(x, ed.gold_ents) in PS.ROLE_SLOTS]
        rows = [r for r, _ in RN._level_rows(ed, "A s012")]
        status = M.role_status(rows, got, base)
        fnd = RG.found(ed, "A s012", rules, {}).set_index("attr")
        rec = ceil[ceil["ent"] == ent].set_index("attr")["recoverable"].to_dict()
        attrs = ed.variants["A s012"].attrs.set_index("attr_id")["name"].to_dict()
        for attr in base:
            f = bool(fnd.loc[attr, "found"])
            bg = fnd.loc[attr, "best_group"]
            out.append({"set": set_name, "version": version, "ent": ent, "attr": attr, "found": f,
                        "recoverable": bool(rec.get(attr, False)), "best_group": bg, "best_name": attrs.get(bg, "-") if bg else "-",
                        "best_purity": round(float(fnd.loc[attr, "purity"]), 2),
                        "best_coverage": round(float(fnd.loc[attr, "coverage"]), 2),
                        "groups": " | ".join(f"{i}: {n} [{lab}]" for i, n, lab in status[attr]) or "-",
                        "cause": M.role_cause(status[attr], f, bool(rec.get(attr, False)))})
    return out


def md_table(df, cols):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in df.iterrows()]
    return lines


def wrong_section(wrong, verdicts):
    """Markdown lines for task 5."""
    lines = ["## Task 5: wrong merges of A s012 on Step 1a v2.2", "",
             "Wrong merge = judged merge (>= 2 members with a gold top attribute) whose members disagree on the top L2 attribute "
             "(`wrong_attr`) or role slot (`wrong_role`), or whose noise share is >= 20% (`noise`). Step: A's attributes come "
             "from the model's own answer (clusters given the same name inside one prompt; A has no neighbourhood groups). "
             "The scorer's +namemerge copy of the vote is the only name merge across groups. Source: orders that put all "
             "judged members into one group. Guard (name) = role guard on the vote names (members share one name, so it "
             "cannot fire); guard (orders) = role guard on any name the cluster got in the 3 orders or the vote.", "",
             "| set | judged merges | wrong | name merge: extra merges | name merge: extra wrong | right merges the guard (orders) would block |",
             "|---|---|---|---|---|---|"]
    for (s, v), (found, tot, nw, nnm) in ((k, x) for k, x in verdicts.items() if len(k) == 2):
        lines.append(f"| {s} | {tot['merges']} (+{tot['unjudged']} unjudged) | {nw}/{tot['merges']} | "
                     f"{tot['nm_merges'] - tot['merges']} | {nnm} | {tot['right_blocked']}/{tot['merges'] - nw} |")
    lines += ["", "Wrong merges per cause (reason x source), with how many each guard would block:", ""]
    ct = M.cause_table(wrong.to_dict("records"))
    lines += md_table(ct, ["set", "step", "reason", "source", "n", "guard_name", "guard_orders"]) + [""]
    tot = wrong.groupby("set").agg(n=("attr_id", "size"), g=("guard_orders", "sum"))
    lines += ["Per set: " + "; ".join(f"{s}: {r['n']} wrong, guard (orders) blocks {int(r['g'])}/{r['n']}"
                                    for s, r in tot.iterrows()) + ".", "",
              "Every wrong merge (members: cluster, top L2 attribute, mentions; odd = members off the plurality attribute):", ""]
    for _, r in wrong.iterrows():
        mem = r["members"].split(";")
        top, n = r["member_attrs"].split(";"), r["member_n"].split(";")
        odd = set(r["odd_members"].split(";")) - {""}
        shown = [f"{c} {a} ({k})" for c, a, k in zip(mem, top, n) if c in odd] if len(mem) > 4 else             [f"{c} {a} ({k})" + (" *odd*" if c in odd else "") for c, a, k in zip(mem, top, n)]
        lines.append(f"- {r['set']} {r['ent']} `{r['column']}` ({r['reason']}, noise {r['noise_share']}, {r['n_members']} members, "
                     f"{r['source']}, guard orders {'YES ' + r['guard_pairs'] if r['guard_orders'] else 'no'}): "
                     + ("odd members: " if len(mem) > 4 else "") + "; ".join(shown))
    return lines


def parts_section(verdicts, role_rows, n_total):
    """Markdown lines for task 6."""
    lines = ["", "## Task 6: what A named J's parts (v2.3)", ""]
    allp = []
    for s in T.GT:
        rows = verdicts[(s, "v2.3", "parts")]
        allp.append(pd.DataFrame(rows))
        df = pd.DataFrame(rows)
        v = M.split_verdicts(rows)
        cnt = pd.Series(list(v.values())).value_counts().to_dict()
        has = df[df["gold_side"] != ""]
        ok = {k: int((has["name_ok_vote"] == k).sum()) for k in (True, False)}
        unnamed = int((has["name_vote"] == "").sum())
        neutral = len(has) - ok[True] - ok[False] - unnamed
        kinds = "; ".join(f"{k}: right {int((g['name_ok_vote'] == True).sum())}, wrong {int((g['name_ok_vote'] == False).sum())}, "  # noqa: E712
                          f"other {int(g['name_ok_vote'].isna().sum())}" for k, g in has.groupby("part"))
        order_ok = [int(has["name_ok_orders"].str.split(";").str[j].eq("True").sum()) for j in range(3)]
        lines.append(f"- **{s}**: J made {n_total[s]} splits; A saw {len(v)} of them (the other {n_total[s] - len(v)} are in "
                     f"stage-1 entities that A is not run on). Verdicts: " + ", ".join(f"{k} {n}/{len(v)}" for k, n in sorted(cnt.items()))
                     + f". Part clusters with a gold role: {len(has)}; vote name on the right side {ok[True]}/{len(has)}, on the wrong "
                     f"side {ok[False]}/{len(has)} (by part, vote name: {kinds}), no side word {neutral}/{len(has)}, unnamed (marked) {unnamed}/{len(has)}; "
                     f"right side per order s0/s1/s2: {order_ok[0]}/{order_ok[1]}/{order_ok[2]} of {len(has)}. Part clusters "
                     f"re-joined by the vote: {int(df['joined_back'].sum())}/{len(df)} (across roles: "
                     f"{sum(1 for x in v.values() if x == 're-merged across roles')} splits).")
    for s in T.GT:
        n, tot, by, found, nm_extra = verdicts[(s, "v2.3", "wrong")]
        old = verdicts[(s, "v2.2")]
        lines.append(f"- {s} wrong merges: v2.2 {old[2]}/{old[1]['merges']}, v2.3 {n}/{tot} {by}; found (A s012) v2.2 "
                     f"{sum(old[0].values())} vs v2.3 {found}; the name merge adds {nm_extra} merges on v2.3.")
    lines += ["", "Role-correct (A s012, names rated, one group rated right per attribute) per role base attribute:", ""]
    rr = pd.DataFrame(role_rows)
    rr["right"] = rr["cause"] == "right"
    summ = rr.groupby(["set", "version", "ent"]).agg(right=("right", "sum"), base=("right", "size")).reset_index()
    tab = summ.pivot_table(index=["set", "version"], columns="ent", values=["right", "base"], aggfunc="sum").reset_index()
    for (s, v), g in rr.groupby(["set", "version"], sort=False):
        lines.append(f"- {s} {v}: role-correct {int(g['right'].sum())}/{len(g)} (train {int(g[g.ent == 'train']['right'].sum())}/"
                     f"{int((g.ent == 'train').sum())}, restaurant/taxi {int(g[g.ent == 'restaurant']['right'].sum())}/"
                     f"{int((g.ent == 'restaurant').sum())})")
    lines += [""] + md_table(rr[rr["version"] == "v2.3"], ["set", "ent", "attr", "found", "recoverable", "best_name", "best_purity",
                                                        "best_coverage", "cause"])
    lines += ["", "Same table for v2.2 (cause only): " + "; ".join(
        f"{r['set']} {r['attr']}: {r['cause']}" for _, r in rr[rr["version"] == "v2.2"].iterrows())]
    return lines


def answers(wrong, verdicts, role_rows, n_total):
    """Short answers (markdown lines) to the two questions, with the counts of the tables below."""
    lines = ["## Answers", "", "**Task 5, why A's merges are wrong.**"]
    for s in T.GT:
        w = wrong[(wrong["set"] == s) & (wrong["variant"] == "A s012")]
        tot = verdicts[(s, "v2.2")][1]["merges"]
        by = w["reason"].value_counts().to_dict()
        src = w["source"].str.split(" (", regex=False).str[0].value_counts().to_dict()
        lines.append(f"- {s}: {len(w)}/{tot} merges wrong: " + ", ".join(f"{k} {n}" for k, n in sorted(by.items()))
                     + f". Source: " + ", ".join(f"{k} {n}" for k, n in sorted(src.items()))
                     + f". Role guard flags {int(w['guard_orders'].sum())}/{len(w)} (role pairs: "
                     f"{int(((w['reason'] == 'wrong_role') & w['guard_orders']).sum())}/{int((w['reason'] == 'wrong_role').sum())} "
                     f"wrong_role; the rest are location / address name pairs) and wrongly flags "
                     f"{verdicts[(s, 'v2.2')][1]['right_blocked']}/{tot - len(w)} right merges; name merge adds "
                     f"{verdicts[(s, 'v2.2')][1]['nm_merges'] - tot} merges.")
    lines += ["", "**Task 6, why role-correct stayed the same with v2.3.**"]
    rr = pd.DataFrame(role_rows)
    for s in T.GT:
        a, b = (rr[(rr["set"] == s) & (rr["version"] == v)] for v in ("v2.2", "v2.3"))
        same = int((a["cause"].values == b["cause"].values).sum())
        miss = b[b["cause"] != "right"]["cause"].value_counts().to_dict()
        lines.append(f"- {s}: role-correct {int((a['cause'] == 'right').sum())}/{len(a)} on v2.2 and "
                     f"{int((b['cause'] == 'right').sum())}/{len(b)} on v2.3; the per-attribute cause is the same for {same}/{len(a)} "
                     f"attributes. The {len(miss) and int(sum(miss.values()))} misses on v2.3: " + ", ".join(f"{k} {n}" for k, n in miss.items()) + ".")
    return lines


def main():
    a = parser().parse_args()
    out = a.merges_out
    out.mkdir(parents=True, exist_ok=True)
    rules = CE.rules_v11(LEVEL)
    rated = AS.read_l2_rated(a.names36, a.out)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in T.GT.items()}
    repairs = []
    lines = ["# wf_v3.8 W2: wrong merges of A s012 (v2.2) and the J-split parts (v2.3)", "",
             "Level L2, rules v1.1, A s012 = vote over the 3 orders. Scripts: `scripts/merges_v38.py`, `s1a/merges_v38.py`.", ""]
    all_wrong, role_rows, verdicts, nm_all = [], [], {}, []
    for (s, v) in T.RUNS:
        shared, bundle, notes = load(a, (s, v), repairs)
        lev = VD.with_level(bundle, gts[s], LEVEL)
        orders = T.OLD_ORDERS if T.RUNS[(s, v)][1] is None else T.NEW_ORDERS
        ceil = CE.ceiling_table({e: replace(ed, variants={k: x for k, x in ed.variants.items() if k != NM})
                                 for e, ed in lev.items()}, LEVEL, rules)
        role_rows += role_table(s, v, lev, rules, rated, ceil)
        if v == "v2.2":
            rows, nm_rows, found, tot = wrong_rows(s, v, lev, rules, orders)
            all_wrong += rows
            nm_all += nm_rows
            verdicts[(s, v)] = (found, tot, len(rows), len(nm_rows))
            print(s, v, "found", found, tot, "wrong", len(rows), "nm wrong", len(nm_rows))
        if v == "v2.3":
            rows23, _, found23, tot23 = wrong_rows(s, v, lev, rules, orders)
            verdicts[(s, v, "wrong")] = (len(rows23), tot23["merges"], pd.Series([r["reason"] for r in rows23], dtype=str)
                                         .value_counts().to_dict(), sum(found23.values()), tot23["nm_merges"] - tot23["merges"])
            run_dir = Path(T.RUNS[(s, v)][0])
            stats = json.loads((run_dir / "spans" / "j_split.json").read_text(encoding="utf-8"))
            men = pd.read_csv(run_dir / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
            prow = []
            for ent, ed in lev.items():
                ent_of = dict(zip(men["mention_id"].astype(int), men["entity"]))
                sub = [x for x in stats if ent_of[x["members"][0]] == ed.entity]
                maps, names = maps_names(ed, orders, "A s012")
                prow += M.part_rows(s, ent, ed, sub, men, orders, "A s012", maps, names, ed.gold_ents)
            verdicts[(s, v, "parts")] = prow
    wrong = pd.DataFrame(all_wrong + nm_all, columns=M.WRONG_COLS)
    n_total = {}
    for s in T.GT:
        write_csv(wrong[wrong["set"] == s], out / f"merges_wrong_{s}.csv")
        write_csv(pd.DataFrame(verdicts[(s, "v2.3", "parts")], columns=M.PART_COLS), out / f"j_parts_{s}.csv")
        n_total[s] = len(json.loads((Path(T.RUNS[(s, "v2.3")][0]) / "spans" / "j_split.json").read_text(encoding="utf-8")))
    lines += answers(wrong, verdicts, role_rows, n_total) + [""] + wrong_section(wrong, verdicts) + parts_section(verdicts, role_rows, n_total) + [""]
    text = chr(10).join(lines)
    write(out / "merges.md", text)
    print(text)


if __name__ == "__main__":
    main()
