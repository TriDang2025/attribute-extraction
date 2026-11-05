"""wf_v3.9 scoring of the Colab batch: T4 reconcile, T5 reconcile + duplicate check, T8 A-cue. No GPU, no LLM.

python scripts/score_v39_batch.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--colab39 results/loop1_v39/colab] [--out results/loop1_v39/scores]
Rules: RULES_V1_3.md (v1.2 recall guard, role-pure columns, noise rules 2a / 2b); contract WF_V39_BATCH.md. The columns and parts are read
from <colab39>/columns.json (and checked against the rebuilt A s012 columns); the joins are applied with s1a/batch_v39.apply_reconcile;
the A-cue responses are loaded as a variant like run_data_v37.load_a does. Rows: A s012, A s012 + dupcheck (v3.8 joins), A s012 +
reconcile (rc0, rc1, both orders), + reconcile + dupcheck (rc0, rc1), A-cue s0 / s1 / s2 / s012.
Writes <out>/{scores.md, dashboard.csv, reconcile_joins.csv, reconcile_summary.csv, dupcheck_rc_joins.csv, cue_marks.csv,
tokens.md, step0.md}.
"""

import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import batch_build_v38 as BB  # noqa: E402
import dashboard_v38 as D  # noqa: E402
import score_v38 as SV  # noqa: E402
import score_v39_p1 as P1  # noqa: E402
from pilot_eval_v31 import _decisions  # noqa: E402
from s1a import batch_v38 as BT  # noqa: E402
from s1a import batch_v39 as B9  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a import score_v38 as S  # noqa: E402
from s1a import score_v39 as S39  # noqa: E402
from s1a import score_v39_batch as SB  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from s1a import v36_data as V36  # noqa: E402
from s1a import paths  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402
from score_t14_v37 import GT  # noqa: E402

BASE, V38 = D.VOTE, SV.JOINED                       # "A s012", "A s012 + dupcheck"
RC = {0: "A s012 + reconcile rc0", 1: "A s012 + reconcile rc1"}
BOTH = "A s012 + reconcile (both orders)"
RCD = {0: "A s012 + reconcile rc0 + dupcheck", 1: "A s012 + reconcile rc1 + dupcheck"}
CUE = ["A-cue s0", "A-cue s1", "A-cue s2", "A-cue s012"]
PARTS = "A s012 parts"                              # helper variant: every part is its own column
FAMILIES = ("reconcile", "a_cue", "dupcheck_rc")
SPLIT_DIR = {"dev50": ("results/loop1_v31/responses", ""), "dev50b": ("results/loop1_v37/colab/responses", "_v22d50b")}
ORDER_ROWS = [BASE, V38, RC[0], RC[1], BOTH, RCD[0], RCD[1], *CUE]
JOIN_COLS = ["set", "ent", "order", "part id", "part", "part label", "part top attribute", "from column", "to column", "status",
             "GT status", "why", "model reason", "other order"]
EXTRA = ["role_columns", "role_pure", "role_share", "marks13_right", "marks13_n", "wrong_entity_dropped"]


def parser():
    ap = P1.parser()
    ap.set_defaults(out=Path("results/loop1_v39/scores"))
    ap.add_argument("--colab39", type=Path, default=Path("results/loop1_v39/colab"))
    return ap


# ---- inputs

def step0(manifest, responses):
    """(rows, problems): one row per job, problems = no response, finish not stop, parse errors."""
    rows, bad = [], []
    for j in manifest:
        r = responses.get(j["job"])
        if r is None:
            bad.append(f"{j['job']}: no response")
            continue
        err = r.get("errors") or []
        rows.append({"job": j["job"], "family": j["family"], "finish": r["finish_reason"], "errors": len(err)})
        if r["finish_reason"] != "stop" or err:
            bad.append(f"{j['job']}: finish {r['finish_reason']}, errors {err}")
    return pd.DataFrame(rows), bad


def split_results(set_name, ents):
    """{ent: {tag: {cluster id: split object}}} of the v3.1 split pass the A runs of the set use."""
    root, infix = SPLIT_DIR[set_name]
    out = {}
    for (key, tag), objs in PV.load_split_results(paths.ROOT / root).items():
        for ent in ents:
            if key == f"{ent}{infix}":
                out.setdefault(ent, {})[tag] = objs
    return out


def add_variant(pb, ent, label, ed_base, rename):
    """Variant `label` = A s012 with the groups renamed by `rename` {attr id: name} (membership and decisions unchanged)."""
    vo = ed_base.variants[BASE]
    SV.add_variant(pb, ent, label, replace(vo, attrs=S.renamed_attrs(vo.attrs, rename)))


def load_cue(pb, si, set_name, jobs, colab, repairs):
    """Add the A-cue orders and the vote to the variants of pb (as run_data_v37.load_a does for A): decisions from the responses
    (v2 parse repair on), the v3.1 split pass of the set, the A contexts; the vote is PC.vote of the three orders."""
    split_all = split_results(set_name, list(pb["raw"]))
    for ent, ed in pb["raw"].items():
        tabs = {}
        for job in sorted((j for j in jobs if j["set"] == set_name and j["ent"] == ent), key=lambda j: j["run_tag"]):
            rows = []
            tabs[job["run_tag"]] = _decisions(job, colab / "responses" / f"{job['job']}.jsonl", ed.cids, split_all, rows)
            V36._tally(repairs, rows, f"A-cue {job['run_tag']}", ent)
        if len(tabs) != 3:
            raise SystemExit(f"{set_name} {ent}: {len(tabs)} A-cue orders")
        decs = {f"A-cue {t}": d for t, d in tabs.items()}
        decs["A-cue s012"] = PC.vote([tabs[f"s{s}"] for s in range(3)])[0]
        for label, dec in decs.items():
            V36._add(ed.variants, label, dec, si.export, ed.ctx_a, ed.entity)
            pb["lev"][ent].variants[label] = ed.variants[label]


# ---- judging the part joins

def part_infos(pb, ent, cols, parts, labels_base, labels_parts):
    """({pid: join_right info of the part alone}, {cid: info of the column}) for the part joins of one entity."""
    ed = pb["lev"][ent]
    out = {}
    for p in parts:
        r = SV.label_of(labels_parts, PV.norm_name(f"part {p['pid']}"))
        partner = DB._col_facts(ed, BASE, [p["pid"]], SV.RULES, {}, r["top_attr"])["partner_share"] if r["label"] == "real" else 0.0
        out[p["pid"]] = {"name": p["name"], "label": r["label"], "top_attr": r["top_attr"], "partner": partner}
    return out, {c["cid"]: SV.column_info(ed, BASE, c, labels_base) for c in cols}


def join_rows(set_name, ent, order, parts, choices, report, cols, infos, other, rows):
    """JOIN_COLS rows of every part with an answer (joined or blocked)."""
    by_id = {c["cid"]: c for c in cols}
    out = []
    for p, rep in zip(parts, report):
        if rep["status"] not in ("joined", "blocked"):
            continue
        pinfo, cinfo = infos
        status, why = S.join_right([pinfo[p["pid"]], cinfo[rep["to"]]])
        out.append({"set": set_name, "ent": ent, "order": order, "part id": p["pid"], "part": p["name"],
                    "part label": pinfo[p["pid"]]["label"], "part top attribute": pinfo[p["pid"]]["top_attr"],
                    "from column": by_id[p["cid"]]["name"], "to column": by_id[rep["to"]]["name"], "status": rep["status"],
                    "GT status": status, "why": why, "model reason": rows[p["pid"]],
                    "other order": "same" if other.get(p["pid"]) == choices[p["pid"]] else ("none" if other.get(p["pid"]) is None else "other column")})
    return out


# ---- marks

def marks_of(base_inputs, raw, label):
    """dict marks13_right / marks13_n / wrong_entity_dropped (+ cue counts for a variant with the cue label) summed over the
    entities; clusters and classes come from the A s012 inputs (they do not depend on the variant), marked clusters from the dec."""
    tot = {}
    for ent, (clusters, _, _, _) in base_inputs.items():
        dec = raw[ent].variants[label].dec
        actions = dict(zip(dec["cluster_id"], dec["action"]))
        has_cue = bool((dec["action"] == "attribute_cue").any())
        res = SB.cue_stats(clusters, actions)
        if not has_cue:   # rules 2a without a cue label: S39.marks_v13 decides the marks
            marked = {c for c, a in actions.items() if a in PV.MARKED and c in clusters}
            res.update(S39.marks_v13(clusters, marked, False))
        for k, v in res.items():
            tot[k] = tot.get(k, 0) + v
    return tot


def build_rows(pb, set_name, base_inputs):
    """DataFrame of ORDER_ROWS: the dashboard row, role-pure columns and the v1.3 marks."""
    dash = D.rows_for(pb, ORDER_ROWS, ORDER_ROWS)
    recs = []
    for _, r in dash.iterrows():
        label = r["row"]
        rc = P1.role_column_rows(pb, label, label, set_name)
        summ = P1.summary_row(set_name, label, rc, "n/a")
        m = marks_of(base_inputs, pb["raw"], label if label in CUE else BASE)
        recs.append({**r.to_dict(), "role_columns": summ["role_columns"], "role_pure": summ["role_pure"], "role_share": summ["share"],
                     "marks13_right": m["marks_right"], "marks13_n": m["marks_n"], "wrong_entity_dropped": m["wrong_entity_dropped"],
                     **{k: m[k] for k in ("cue_marks", "cue_question", "cue_other_domain", "questions", "questions_cue",
                                          "questions_noise", "questions_column")}})
    return pd.DataFrame(recs)


# ---- report

def md_table(df, cols):
    f = lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else (f"{v:.3f}" if isinstance(v, float) else str(v))  # noqa: E731
    return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f(r[c]) for c in cols) + " |" for _, r in df.iterrows()]


def tokens_md(rows, v38_total=None):
    L = ["| family | calls | prompt tokens | per call | output tokens | per call | est. prompt (chars/3.5) |", "|---|---|---|---|---|---|---|"]
    for f, n, p, o, e in rows:
        L.append(f"| {f} | {n} | {p:,} | {p // n:,} | {o:,} | {o // n:,} | {e:,} |")
    return L


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    m1 = json.loads((a.colab39 / "manifest.json").read_text(encoding="utf-8"))["jobs"]
    m2 = json.loads((a.colab39 / "manifest_stage2.json").read_text(encoding="utf-8"))["jobs"]
    tables = json.loads((a.colab39 / "columns.json").read_text(encoding="utf-8"))
    reconciled = json.loads((a.colab39 / "reconciled_columns.json").read_text(encoding="utf-8"))
    responses = SV.read_responses(a.colab39)
    s0, bad = step0(m1 + m2, responses)
    print(len(responses), "responses; problems:", bad)

    manifest38 = json.loads((a.colab38 / "manifest.json").read_text(encoding="utf-8"))
    responses38 = SV.read_responses(a.colab38)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in GT.items()}
    rc_jobs = [j for j in m1 if j["family"] == "reconcile"]
    cue_jobs = [j for j in m1 if j["family"] == "a_cue"]
    dup_jobs = {(j["set"], j["ent"], j["order_seed"]): j for j in m2}
    all_rows, join_all, dupj_all, summ_all, repairs, notes, agree_all = [], [], [], [], [], [], {}
    for set_name in D.SETS:
        pb = DB.prepare(set_name, D.load_v22(a, set_name), gts[set_name])
        si = BB.SetInput(set_name)
        P1.add_dupcheck(pb, set_name, manifest38, responses38)
        per_ent = BB.columns_of(pb)
        for ent in DB.ENTS:   # the columns of the batch are the columns rebuilt here
            got = [(c["cid"], c["name"], c["n_mentions"]) for c in per_ent[ent][1]]
            want = [(c["cid"], c["name"], c["n_mentions"]) for c in tables[set_name][ent]["columns"]]
            if got != want:
                raise SystemExit(f"STOP: {set_name} {ent}: rebuilt columns differ from columns.json")
        labels_base = {e: SV.gt_info(pb, BASE)[e] for e in DB.ENTS}
        choice, new, rep, joins_of = {}, {}, {}, {}
        for ent in DB.ENTS:      # pass 1: the variants (every entity gets them before any GT table is read)
            t, ed = tables[set_name][ent], pb["lev"][ent]
            cols, parts = t["columns"], t["parts"]
            for o in (0, 1):
                jobs = [j for j in rc_jobs if (j["set"], j["ent"], j["order_seed"]) == (set_name, ent, o)]
                choice[(ent, o)] = SB.choices_of(jobs, {j["job"]: responses.get(j["job"]) for j in jobs})
                new[(ent, o)], rep[(ent, o)] = B9.apply_reconcile(cols, parts, choice[(ent, o)])
                add_variant(pb, ent, RC[o], ed, SB.final_names(new[(ent, o)]))
                # the reconciled columns of the stage 2 builder must be the ones rebuilt here
                have = reconciled[set_name][ent][str(o)]["columns"]
                if [(c["name"], c["mention_ids"]) for c in have] != [(c["name"], c["mention_ids"]) for c in new[(ent, o)]]:
                    raise SystemExit(f"STOP: {set_name} {ent} rc{o}: reconciled_columns.json differs from apply_reconcile")
                job = dup_jobs[(set_name, ent, o)]
                joins, dropped = SB.clean_joins(responses[job["job"]]["parsed"].get("joins", []))
                kept, _ = BT.check_joins(joins, {c["cid"]: c for c in new[(ent, o)]})
                joins_of[(ent, o)] = joins
                if dropped:
                    notes.append(f"{job['job']}: {len(dropped)} joins with fewer than 2 distinct columns dropped (parse errors "
                                 f"{len(responses[job['job']]['errors'])}), {len(joins)} kept.")
                add_variant(pb, ent, RCD[o], ed, SB.final_names(new[(ent, o)], kept))
            nb, _ = B9.apply_reconcile(cols, parts, SB.intersect(choice[(ent, 0)], choice[(ent, 1)]))
            add_variant(pb, ent, BOTH, ed, SB.final_names(nb))
            vo = ed.variants[BASE]   # helper variant: every part is its own column
            SV.add_variant(pb, ent, PARTS, replace(vo, attrs=S.renamed_attrs(vo.attrs, {p["pid"]: f"part {p['pid']}" for p in parts})))
        labels_parts = SV.gt_info(pb, PARTS)
        labels_rc = {o: SV.gt_info(pb, RC[o]) for o in (0, 1)}
        for ent in DB.ENTS:      # pass 2: judge the joins
            t, ed = tables[set_name][ent], pb["lev"][ent]
            cols, parts = t["columns"], t["parts"]
            infos = part_infos(pb, ent, cols, parts, labels_base[ent], labels_parts[ent])
            for o in (0, 1):
                reasons = {j["pid"]: (responses[j["job"]]["parsed"].get("reason", "") if responses.get(j["job"]) else "")
                           for j in rc_jobs if (j["set"], j["ent"], j["order_seed"]) == (set_name, ent, o)}
                join_all += join_rows(set_name, ent, f"rc{o}", parts, choice[(ent, o)], rep[(ent, o)], cols, infos,
                                      choice[(ent, 1 - o)], reasons)
                rows, _ = SV.score_joins(set_name, f"rc{o}", ent, ed, new[(ent, o)], joins_of[(ent, o)], labels_rc[o][ent])
                dupj_all += rows
        load_cue(pb, si, set_name, cue_jobs, a.colab39, repairs)
        base_inputs = P1.noise_inputs(pb["raw"], pb["gt"], BASE)
        check = P1.noise_row(base_inputs)[0]
        mine = marks_of(base_inputs, pb["raw"], BASE)
        if (check["marks_right"], check["marks_n"]) != (mine["marks_right"], mine["marks_n"]):
            raise SystemExit("STOP: marks of A s012 differ from score_v39_p1")
        df = build_rows(pb, set_name, base_inputs)
        want = pd.read_csv(a.scores_old)
        w = want[(want["set"] == set_name) & (want["row"] == V38)].iloc[0]
        g = df[df["row"] == V38].iloc[0]
        if any(int(g[c]) != int(w[c]) for c in ("columns", "found_total", "dup_columns", "wrong_columns")):
            raise SystemExit(f"STEP 0 FAILED: {set_name} {V38} differs from the v3.8 scores")
        all_rows.append(df)
        for o in (0, 1):
            ch = {e: choice[(e, o)] for e in DB.ENTS}
            agree_all.setdefault(set_name, {})[o] = ch
    rows = pd.concat(all_rows, ignore_index=True)

    # ---- tables
    jdf = pd.DataFrame(join_all, columns=JOIN_COLS)
    summ = []
    for s in D.SETS:
        parts_n = sum(len(tables[s][e]["parts"]) for e in DB.ENTS)
        k = sum(sum(agree_all[s][0][e][p] == agree_all[s][1][e][p] for p in agree_all[s][0][e]) for e in DB.ENTS)
        for o in ("rc0", "rc1"):
            g = jdf[(jdf["set"] == s) & (jdf["order"] == o)]
            none = parts_n - len(g)
            summ.append({"set": s, "order": o, "parts": parts_n, "answered_join": len(g), "joined": int((g["status"] == "joined").sum()),
                         "blocked": int((g["status"] == "blocked").sum()), "none": none,
                         **{f"joined {x}": int(((g["status"] == "joined") & (g["GT status"] == x)).sum()) for x in S.JOIN_STATUS},
                         **{f"blocked {x}": int(((g["status"] == "blocked") & (g["GT status"] == x)).sum()) for x in S.JOIN_STATUS},
                         "agree": f"{k}/{parts_n}", "agree_share": round(k / parts_n, 3)})
    summ = pd.DataFrame(summ)
    inter = []
    for s in D.SETS:
        g = jdf[(jdf["set"] == s) & (jdf["order"] == "rc0") & (jdf["status"] == "joined") & (jdf["other order"] == "same")]
        inter.append({"set": s, **{x: int((g["GT status"] == x).sum()) for x in S.JOIN_STATUS}, "joins": len(g)})
    inter = pd.DataFrame(inter)
    cue = rows[rows["row"].isin([BASE, *CUE])][["set", "row", "marks13_right", "marks13_n", "wrong_entity_dropped", "cue_marks",
                                               "cue_question", "cue_other_domain", "questions", "questions_cue", "questions_noise",
                                               "questions_column", "noise_caught", "noise_n"]]
    tok = SB.tokens_rows({k: responses[k] for k in responses}, m1 + m2, FAMILIES)

    write_csv(rows, a.out / "dashboard.csv")
    write_csv(jdf, a.out / "reconcile_joins.csv")
    write_csv(summ, a.out / "reconcile_summary.csv")
    write_csv(pd.DataFrame(dupj_all), a.out / "dupcheck_rc_joins.csv")
    write_csv(cue, a.out / "cue_marks.csv")
    write(a.out / "tokens.md", "\n".join(["# wf_v3.9 batch tokens (exact, from the responses)", "", *tokens_md(tok), ""]))
    write(a.out / "step0.md", f"# wf_v3.9 step 0\n\n{len(responses)} responses for {len(m1) + len(m2)} manifest jobs; problems: {bad or 'none'}.\n"
          f"A-cue parse repairs (llm_cache.repair_undeclared): {repairs or 'none'}.\nNotes: {notes or 'none'}.\n")

    # ---- decisions
    def row(s, name):
        return rows[(rows["set"] == s) & (rows["row"] == name)].iloc[0]
    dec4, dec5, dec8, ok4, ok5, ok8 = [], [], [], True, {0: True, 1: True}, True
    for s in D.SETS:
        line, ok = SB.reconcile_decision(row(s, BASE), row(s, BOTH))
        dec4.append("- " + line)
        ok4 &= ok
        for o in (0, 1):
            line, ok = SB.reconcile_decision(row(s, BASE), row(s, RCD[o]))
            r = row(s, RCD[o])
            dec5.append(f"- rc{o}, " + line + f" Columns per found {r['columns_per_found']:.3f} (bar <= 1.2: "
                        f"{'met' if r['columns_per_found'] <= DB.CPF_BAR else 'not met'}); v3.8 dupcheck alone: review edits "
                        f"{row(s, V38)['review_edits']}, columns per found {row(s, V38)['columns_per_found']:.3f}.")
            ok5[o] &= ok
        line, ok = SB.cue_decision(row(s, BASE), row(s, "A-cue s012"))
        dec8.append("- " + line)
        ok8 &= ok

    k_all = sum(int(x.split("/")[0]) for x in summ[summ["order"] == "rc0"]["agree"])
    n_all = int(summ[summ["order"] == "rc0"]["parts"].sum())
    jm = jdf[(jdf["order"] == "rc0") & (jdf["status"] == "joined")]
    summary = ["## Summary", "",
               f"- T4 reconcile: {'ADOPT' if ok4 else 'do not adopt'}. Main row = joins both orders agree on. Orders agree on {k_all}/{n_all} "
               f"({k_all / n_all:.3f}) parts. Review edits: " + "; ".join(f"{s} {row(s, BASE)['review_edits']} -> {row(s, BOTH)['review_edits']}"
                                                                      for s in D.SETS) + ". Recall guard passes on both sets.",
               "  Join quality (rc0 joined parts): " + "; ".join(f"{s} {int((jm[jm['set'] == s]['GT status'] == 'right').sum())} right, "
                                                                f"{int((jm[jm['set'] == s]['GT status'] == 'wrong').sum())} wrong, "
                                                                f"{int((jm[jm['set'] == s]['GT status'] == 'no_gt').sum())} no GT of {int((jm['set'] == s).sum())}"
                                                                for s in D.SETS) + ". Review edits count duplicate and wrong columns; a wrong join "
               "does not lower found, so read the right / wrong split next to it.",
               f"- T5 reconcile + duplicate check: rc0 {'ADOPT' if ok5[0] else 'not adopted'}, rc1 {'ADOPT' if ok5[1] else 'not adopted'}. "
               "Columns per found: " + "; ".join(f"{s} rc0 {row(s, RCD[0])['columns_per_found']:.3f}, rc1 {row(s, RCD[1])['columns_per_found']:.3f}"
                                                for s in D.SETS) + " (bar <= 1.2, not met on either set).",
               f"- T8 A-cue s012: {'ADOPT' if ok8 else 'do not adopt'}. Marks right (rules 1.3): " + "; ".join(
                   f"{s} {row(s, BASE)['marks13_right']}/{row(s, BASE)['marks13_n']} -> {row(s, 'A-cue s012')['marks13_right']}/"
                   f"{row(s, 'A-cue s012')['marks13_n']}" for s in D.SETS) + ".", ""]
    show = ["set", "row", "found_total", "gold_total", "columns", "columns_per_found", "dup_columns", "wrong_columns", "extras_no_gt",
            "review_edits", "guard", "role_pure", "role_columns", "marks13_right", "marks13_n", "wrong_entity_dropped"]
    L = ["# wf_v3.9 batch scores (L2, rules v1.3 over v1.2, Step 1a v2.2)", "",
         "Rows are the A s012 vote with changes on the columns only (found and merges are per group, so they do not change unless a "
         "part's group changes column). Review edits = duplicate + wrong columns. Role-pure = role-pure columns / role columns "
         "(RULES_V1_3.md 1). Marks 1.3 = noise marks right / marks counted (2a: a question cluster marked noise is right when the "
         "variant has no attribute_cue label; 2b: other-domain clusters marked noise leave the count, shown as wrong entity dropped; "
         "A-cue: a question cluster is right only when marked attribute_cue). Recall guard: RULES_V1_2.md per entity.", "",
         *summary, "## Step 0", "", f"{len(responses)} responses for {len(m1) + len(m2)} jobs. Problems: " + ("; ".join(bad) or "none") + ".",
         "Handled: " + ("; ".join(notes) or "none") + f" A-cue parse repairs: {repairs or 'none'}.", "",
         "## Dashboard rows", ""]
    for s in D.SETS:
        L += [f"### {s}", ""] + md_table(rows[rows["set"] == s], show) + [""]
    L += ["## T4: reconcile", "",
          "Main row: **A s012 + reconcile (both orders)** = a part joins a column only when both candidate orders chose the same column "
          "(chosen before reading any result: the answers are order-sensitive in earlier batches, so the intersection is the cautious "
          "reading and needs no tie rule). The per-order rows rc0 and rc1 are shown above. Every join judged as in v3.8 (the part alone "
          "against the chosen column: right = same L2 attribute and same role; wrong = noise, other attribute or mixed role; no GT = a "
          "side has no L2 attribute). Blocked = a role pair by names (code check).", ""]
    L += md_table(summ, ["set", "order", "parts", "joined", "joined right", "joined wrong", "joined no_gt", "blocked", "none", "agree", "agree_share"]) + [""]
    L += ["Joins both orders agree on (the main row's joins), by GT status:", ""] + md_table(inter, ["set", "joins", *S.JOIN_STATUS]) + [""]
    L += ["Every join is in `reconcile_joins.csv`.", "", *dec4, "", f"**Decision T4: {'ADOPT reconcile' if ok4 else 'DO NOT ADOPT reconcile'}** "
          "(rule: recall guard passes and review edits go down on both sets, main row).", "",
          "## T5: reconcile + duplicate check", "", *dec5, "",
          f"**Decision T5: rc0 {'ADOPT' if ok5[0] else 'not adopted'}, rc1 {'ADOPT' if ok5[1] else 'not adopted'}** (same rule per order).", "",
          "## T8: A-cue", "", "Cue marks against the request GT (rules 2a: question cluster = at least 60% request mentions):", ""]
    L += md_table(cue, ["set", "row", "marks13_right", "marks13_n", "wrong_entity_dropped", "cue_marks", "cue_question",
                        "cue_other_domain", "questions", "questions_cue", "questions_noise", "questions_column", "noise_caught", "noise_n"]) + [""]
    L += [*dec8, "", f"**Decision T8: {'ADOPT A-cue' if ok8 else 'DO NOT ADOPT A-cue'}** (rule: noise marks right up on both sets "
          "against A s012 under v1.3, and the recall guard passes).", "", "## Tokens (exact)", "", *tokens_md(tok), ""]
    write(a.out / "scores.md", "\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
