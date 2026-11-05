"""wf_v3.9 Phase 1 (RULES_V1_3.md): role-pure columns, noise rules 2a / 2b, rescore of J. No GPU, no LLM.

python scripts/score_v39_p1.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--out results/loop1_v39/p1]
Task 1: role-pure columns of A s012 and A s012 + dupcheck (v3.8 dupcheck joins rebuilt as scripts/score_v38.py does; the columns and
the guard numbers are checked against results/loop1_v38/scores/dashboard.csv). Task 2: marks of every v3.8 dashboard row (both
dashboard.csv files); the old marks are reproduced first (stops on a mismatch). Task 3: A s012 on Step 1a v2.3 vs v2.2.
Writes <out>/{p1.md, role_pure_summary.csv, role_columns.csv, noise_marks.csv, noise_changed.csv, j_rescore.csv}.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dashboard_v38 as D  # noqa: E402
import merges_v38 as MS  # noqa: E402
import score_t14_v37 as T  # noqa: E402
import score_v38 as SV  # noqa: E402
from s1a import a_s012_v37 as AS  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import columns_v37 as CV  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a import rules_labels as RL  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import score_v39 as S39  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402

ROLES = ("departure", "destination", "leave at", "arrive by")
VOTE, JOINED = SV.LABEL, SV.JOINED
RULES = CE.rules_v11(2)


def parser():
    ap = D.parser()
    ap.set_defaults(out=Path("results/loop1_v39/p1"))
    ap.add_argument("--dash-old", type=Path, default=Path("results/loop1_v38/dash/dashboard.csv"))
    ap.add_argument("--scores-old", type=Path, default=Path("results/loop1_v38/scores/dashboard.csv"))
    ap.add_argument("--colab38", type=Path, default=Path("results/loop1_v38/colab"))
    ap.add_argument("--ratings", type=Path, default=Path("results/loop1_v37"), help="folder of the v3.7 / t14 name ratings")
    return ap


# ---- task 1: role-pure columns

def role_column_rows(pb, label, row, set_name):
    """One dict per role column of variant `label` (final columns of the L2 bundle): set, row, ent, column, n_mentions, count per
    role slot, n_role, top_share, pure."""
    out = []
    for ent, ed in pb["lev"].items():
        vo = ed.variants[label]
        gc = CV.group_columns(ed, label)
        col_of = dict(zip(gc["attr_id"], gc["column"]))
        m = ed.mentions
        by_col = {}
        for mid, g in zip(m["mention_id"].astype(int), m["gold_attr"]):
            col = col_of.get(vo.assign.get(mid, ""))
            if col is not None:
                by_col.setdefault(col, []).append(g)
        for col, golds in sorted(by_col.items()):
            cnt = S39.role_counts(golds, ed.gold_ents)
            pure = S39.is_role_pure(cnt)
            if pure is None:
                continue
            n = sum(cnt.values())
            out.append({"set": set_name, "row": row, "ent": ent, "column": col, "n_mentions": len(golds),
                        **{r: cnt.get(r, 0) for r in ROLES}, "n_role": n, "top_share": round(max(cnt.values()) / n, 3),
                        "pure": pure})
    return out


def role_correct(lev_a, rated, set_name, version):
    """(right, base) of role-correct for A s012 as scripts/merges_v38.py counts it (cause == right); `lev_a` = L2 bundle that holds
    A s012."""
    ceil = CE.ceiling_table(lev_a, 2, RULES)
    rr = pd.DataFrame(MS.role_table(set_name, version, lev_a, RULES, rated, ceil))
    return int((rr["cause"] == "right").sum()), len(rr)


def add_dupcheck(pb, set_name, manifest, responses):
    """Add variant JOINED to the prepared bundle `pb` (split config) as scripts/score_v38.py main() does; returns the join rows."""
    per_ent = SV.BB.columns_of(pb)
    lab_all = SV.gt_info(pb, VOTE)
    rows = []
    for ent, (_, cols) in per_ent.items():
        job = next(j for j in manifest["jobs"] if j["job"] == f"dupcheck_{set_name}_split_{ent}")
        r, kept = SV.score_joins(set_name, "split", ent, pb["lev"][ent], cols, responses[job["job"]]["parsed"]["joins"], lab_all[ent])
        finals, _ = SV.final_columns(cols, kept)
        SV.joined_variant(pb, ent, finals, cols)
        rows += r
    return rows


def summary_row(set_name, row, rc, rcorrect):
    df = pd.DataFrame(rc)
    pure, n = int(df["pure"].sum()), len(df)
    return {"set": set_name, "row": row, "role_columns": n, "role_pure": pure, "share": round(pure / n, 3) if n else float("nan"),
            "role_correct": rcorrect}


# ---- task 2: noise marks

def noise_inputs(raw, gt, label):
    """{ent: (clusters {cid: (label, [classes])}, marked set, has_cue, top values {cid: str})} of one variant of a raw bundle.
    Classes: the mwoz mention classes at L2 (rules_labels.mention_class); a mention with an L2 label whose entity is not the
    entity's own becomes "wrong_entity" (the mwoz classes have no other-entity class)."""
    rules, extra, out = NV.mwoz_rules(2), {"gt_levels": gt}, {}
    for ent, ed in raw.items():
        led = SR.level_entity(ed, rules, extra)
        cl = RL.cluster_labels(led, rules, extra)
        lab = dict(zip(cl["cluster_id"], cl["label"]))
        cls = RL.mention_class(led, rules, extra)
        own = set(led.gold_ents) | {""}
        m = led.mentions
        classes = ["wrong_entity" if g and e not in own else cls[int(i)]
                   for i, g, e in zip(m["mention_id"], m["gold_attr"], m["entity_gold"])]
        per = {c: [x for x, cc in zip(classes, m["cluster_id"]) if cc == c] for c in lab}
        top = m.groupby("cluster_id")["norm_value"].agg(lambda s: "|".join(v for v, _ in Counter(s).most_common(3)))
        dec = ed.variants[label].dec
        marked = {c for c in dec.loc[dec["action"].isin(PV.MARKED), "cluster_id"] if c in lab}
        out[ent] = ({c: (lab[c], per[c]) for c in lab}, marked, bool((dec["action"] == "attribute_cue").any()), top.to_dict())
    return out


def noise_row(inputs):
    """dict: old marks (label noise), new marks (rules 1.3), noise caught / n (unchanged), and the changed clusters."""
    new = Counter()
    old_right = old_n = caught = noise_n = 0
    changed = []
    for ent, (clusters, marked, has_cue, top) in inputs.items():
        res = S39.marks_v13(clusters, marked, has_cue)
        new.update(res)
        noise = {c for c, (lab, _) in clusters.items() if lab == "noise"}
        caught += len(noise & marked)
        noise_n += len(noise)
        old_right += len(marked & noise)
        old_n += len(marked)
        for c in sorted(marked):
            lab, cls = clusters[c]
            o = "right" if lab == "noise" else "wrong"
            n = S39.mark_outcome(lab, cls, has_cue)
            if o != n:
                changed.append({"ent": ent, "cluster": c, "label": lab, "n": len(cls), "old": o,
                                "new": "wrong entity, dropped" if n == "wrong_entity_dropped" else n,
                                "classes": ", ".join(f"{k} {v}" for k, v in sorted(Counter(cls).items())), "top_values": top.get(c, "")})
    return {"old_marks_right": old_right, "old_marks_n": old_n, "marks_right": new["marks_right"], "marks_n": new["marks_n"],
            "wrong_entity_dropped": new["wrong_entity_dropped"], "noise_caught": caught, "noise_n": noise_n}, changed


def span_str(vals):
    return DB.span(list(vals))


def noise_tables(pbs, old_dash, old_scores):
    """(noise_marks DataFrame, changed DataFrame). Every row of both old dashboards; the old marks are asserted equal."""
    computed, changed = {}, []
    for (s, config), pb in pbs.items():
        for label in [*D.SETS[s]["orders"], VOTE]:
            row = label if config == "split" else f"{label} nosplit"
            res, ch = noise_row(noise_inputs(pb["raw"], pb["gt"], label))
            computed[(s, row)] = res
            changed += [{"set": s, "row": row, **c} for c in ch]
    rows = []
    for src, old in (("dash", old_dash), ("scores", old_scores)):
        for _, r in old.iterrows():
            s, name = r["set"], r["row"]
            base = name.replace(" + dupcheck", "")
            if base in {k[1] for k in computed if k[0] == s}:
                c = computed[(s, base)]
                new = {k: c[k] for k in ("marks_right", "marks_n", "wrong_entity_dropped", "noise_caught", "noise_n")}
                old_r, old_n = c["old_marks_right"], c["old_marks_n"]
                new = {k: str(v) for k, v in new.items()}
                old_r, old_n = str(old_r), str(old_n)
            else:  # a range row: the span of its member rows
                members = [k[1] for k in computed if k[0] == s and (("nosplit" in k[1]) == ("nosplit" in name)) and k[1] != VOTE
                           and k[1] != f"{VOTE} nosplit"]
                cs = [computed[(s, m)] for m in members]
                new = {k: span_str(c[k] for c in cs) for k in ("marks_right", "marks_n", "wrong_entity_dropped", "noise_caught", "noise_n")}
                old_r, old_n = span_str(c["old_marks_right"] for c in cs), span_str(c["old_marks_n"] for c in cs)
            if (str(r["marks_right"]), str(r["marks_n"])) != (old_r, old_n):
                raise SystemExit(f"STEP 0 FAILED: {src} {s} {name}: file marks {r['marks_right']}/{r['marks_n']}, recomputed {old_r}/{old_n}")
            if (str(r["noise_caught"]), str(r["noise_n"])) != (new["noise_caught"], new["noise_n"]):
                raise SystemExit(f"STEP 0 FAILED: {src} {s} {name}: noise caught changed")
            rows.append({"file": src, "set": s, "row": name, "old_marks_right": old_r, "old_marks_n": old_n,
                         "new_marks_right": new["marks_right"], "new_marks_n": new["marks_n"],
                         "wrong_entity_dropped": new["wrong_entity_dropped"], "noise_caught": new["noise_caught"],
                         "noise_n": new["noise_n"]})
    return pd.DataFrame(rows), pd.DataFrame(changed, columns=["set", "row", "ent", "cluster", "label", "n", "old", "new", "classes",
                                                             "top_values"])


# ---- task 3: J

def j_rescore(a, pbs22, gts, rated):
    """DataFrame, one row per (set, version): A s012 found per entity, guard, columns, role-pure, role-correct."""
    rows = []
    for s in D.SETS:
        run_dir, key = T.RUNS[(s, "v2.3")]
        bundles = {"v2.2": pbs22[s]["raw"], "v2.3": T.load_new(a, Path(run_dir), key, [])[1]}
        for v, raw in bundles.items():
            pb = pbs22[s] if v == "v2.2" else DB.prepare(s, raw, gts[s])
            r = DB.dashboard_row(pb, VOTE, f"A s012 {v}")
            found = {e: r[f"found_{e}"] for e in DB.ENTS}
            ok, detail = DB.guard_check(s, found)
            rc = role_column_rows(pb, VOTE, f"A s012 {v}", s)
            lev_a = VD.with_level(T.only(raw, [VOTE]), gts[s], 2)
            right, base = role_correct(lev_a, rated, s, v)
            rows.append({**summary_row(s, f"A s012 {v}", rc, f"{right}/{base}"), "version": v,
                         "found": f"{r['found_total']}/{r['gold_total']}", "found_detail": detail, "guard": "pass" if ok else "FAIL",
                         "columns": r["columns"], "columns_per_found": r["columns_per_found"]})
    return pd.DataFrame(rows)


def decision(j):
    """(lines, keep?) of the J decision: keep when role-pure share is higher on v2.3 than v2.2 on both sets and the guard passes on both."""
    lines, ok = [], True
    for s in D.SETS:
        a = j[(j["set"] == s) & (j["version"] == "v2.2")].iloc[0]
        b = j[(j["set"] == s) & (j["version"] == "v2.3")].iloc[0]
        better = b["share"] > a["share"]
        ok &= better and b["guard"] == "pass"
        lines.append(f"- {s}: role-pure v2.2 {a['role_pure']}/{a['role_columns']} ({a['share']:.3f}) -> v2.3 {b['role_pure']}/"
                     f"{b['role_columns']} ({b['share']:.3f}), {'better' if better else 'NOT better'}; role-correct {a['role_correct']} -> "
                     f"{b['role_correct']}; found {a['found']} -> {b['found']} ({b['found_detail']}); recall guard {b['guard']}.")
    return lines, ok


# ---- report

def md_table(df, cols):
    f = lambda v: f"{v:.3f}" if isinstance(v, float) else str(v)  # noqa: E731
    return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f(r[c]) for c in cols) + " |" for _, r in df.iterrows()]


def report(summ, rcols, marks, changed, j, dec_lines, keep, join_note):
    L = ["# wf_v3.9 Phase 1: scoring fixes (rules v1.3, L2, Step 1a v2.2 unless noted)", "",
         "Rules: `RULES_V1_3.md`. Scripts: `scripts/score_v39_p1.py`, `s1a/score_v39.py`. No GPU, no LLM.", "",
         "## Task 1: role-pure columns", "",
         "Role column = a final column with at least one role mention (an L2 mention of departure / destination / leave at / arrive by; a "
         "multi-class mention counts once per class). Pure = at least 80% of its role mentions hold one slot. Columns are the final "
         "columns of the row (A s012 + dupcheck: the v3.8 dupcheck joins that pass the code check, rebuilt from the 256 responses; its "
         f"column counts match v3.8: {join_note}). Role-correct (v3.7: one rightly named group per role attribute) is for A s012 only: the "
         "joins rename groups, so the name ratings do not carry over to + dupcheck.", ""]
    L += md_table(summ, ["set", "row", "role_columns", "role_pure", "share", "role_correct"]) + [""]
    for s, g in rcols[rcols["row"] == JOINED].groupby("set", sort=False):
        L += [f"Role columns of A s012 + dupcheck, {s} (mentions per slot; * = not pure):", ""]
        g = g.assign(pure_txt=["yes" if p else "NO *" for p in g["pure"]])
        L += md_table(g, ["ent", "column", *ROLES, "n_role", "top_share", "pure_txt"]) + [""]
    L += ["All role columns of both rows: `role_columns.csv`.", "",
          "## Task 2: noise marks under rules 2a / 2b", "",
          "marks right / marks n = marked clusters (action not_attribute / unsure / attribute_cue) that are right / counted. New: a question "
          "cluster (>= 60% request mentions) marked counts right when the variant has no attribute_cue label (every A row); a cluster with "
          ">= 60% other-entity mentions (an L2 label of another entity) leaves marks n and is counted as wrong entity, dropped. Noise caught "
          "is unchanged (asserted). The old marks were reproduced from the clusters first (asserted equal to both files). Rows with "
          "+ dupcheck have the same decisions as their base row.", ""]
    for f, g in marks.groupby("file", sort=False):
        L += [f"### {f} (results/loop1_v38/{'dash' if f == 'dash' else 'scores'}/dashboard.csv)", ""]
        L += md_table(g, ["set", "row", "old_marks_right", "old_marks_n", "new_marks_right", "new_marks_n", "wrong_entity_dropped",
                          "noise_caught", "noise_n"]) + [""]
    sub = changed[changed["row"].isin([VOTE, f"{VOTE} nosplit"])]
    L += [f"Clusters whose status changed: {len(changed)} cluster-row pairs over all rows (`noise_changed.csv`); A s012 and A s012 nosplit:", ""]
    L += md_table(sub, ["set", "row", "ent", "cluster", "old", "new", "classes", "top_values"]) + [""]
    L += ["## Task 3: J (Step 1a v2.3) rescored", ""]
    L += md_table(j, ["set", "row", "found", "found_detail", "guard", "columns", "role_columns", "role_pure", "share", "role_correct"]) + [""]
    L += dec_lines + ["", f"**Decision: {'KEEP J as an option' if keep else 'DROP J for good'}** "
                      "(rule: role-pure share up on both sets and the recall guard passes)."]
    return "\n".join(L) + "\n"


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in T.GT.items()}
    pbs = D.load_both(a, gts)
    old_dash, old_scores = pd.read_csv(a.dash_old), pd.read_csv(a.scores_old)
    marks, changed = noise_tables(pbs, old_dash, old_scores)
    print("noise step 0 ok")

    manifest = json.loads((a.colab38 / "manifest.json").read_text(encoding="utf-8"))
    responses = SV.read_responses(a.colab38)
    rated = AS.read_l2_rated(a.names36, a.ratings)
    summ, rcols, notes = [], [], []
    for s in D.SETS:
        pb = pbs[(s, "split")]
        add_dupcheck(pb, s, manifest, responses)
        dash = DB.dashboard_row(pb, JOINED, JOINED)
        want = old_scores[(old_scores["set"] == s) & (old_scores["row"] == JOINED)].iloc[0]
        for c in ("columns", "found_total", "dup_columns", "wrong_columns"):
            if int(dash[c]) != int(want[c]):
                raise SystemExit(f"STEP 0 FAILED: {s} {JOINED} {c}: {dash[c]} vs v3.8 {want[c]}")
        notes.append(f"{s} {dash['columns']}")
        lev_a = VD.with_level(T.only(pb["raw"], [VOTE]), gts[s], 2)
        right, base = role_correct(lev_a, rated, s, "v2.2")
        for label, name in ((VOTE, VOTE), (JOINED, JOINED)):
            rc = role_column_rows(pb, label, name, s)
            rcols += rc
            summ.append(summary_row(s, name, rc, f"{right}/{base}" if label == VOTE else "n/a"))
    summ, rcols = pd.DataFrame(summ), pd.DataFrame(rcols)
    j = j_rescore(a, {s: pbs[(s, "split")] for s in D.SETS}, gts, rated)
    lines, keep = decision(j)

    write_csv(summ, a.out / "role_pure_summary.csv")
    write_csv(rcols, a.out / "role_columns.csv")
    write_csv(marks, a.out / "noise_marks.csv")
    write_csv(changed, a.out / "noise_changed.csv")
    write_csv(j, a.out / "j_rescore.csv")
    write(a.out / "p1.md", report(summ, rcols, marks, changed, j, lines, keep, ", ".join(f"{n} columns" for n in notes)))
    print(summ.to_string())
    print("\n".join(lines))
    print("keep J:", keep)


if __name__ == "__main__":
    main()
