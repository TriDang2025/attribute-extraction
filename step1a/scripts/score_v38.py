"""wf_v3.8 scoring of the Colab batch (diary 2 Nov tasks 7-11). No GPU, no LLM.

python scripts/score_v38.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--colab results/loop1_v38/colab] [--out results/loop1_v38/scores]
Rules: RULES_V1_2.md (recall guard, verdict rule v0, thresholds fixed); batch contract WF_V38_BATCH.md. Reads the columns of A s012
(with and without the split pass) as scripts/batch_build_v38.py built them, the 256 responses, and rebuilds the dashboard rows
through dashboard_v38.rows_for.
Writes <out>/{step0.md, joins.csv, dashboard.csv, dashboard.md, cards_dev50.csv, cards_dev50b.csv, cards.md, checker.md, tokens.md}.
"""

import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import batch_build_v38 as BB  # noqa: E402
import dashboard_v38 as D  # noqa: E402
from s1a import batch_v38 as BT  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import columns_v37 as CV  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import rules_groups as RG  # noqa: E402
from s1a import score_v38 as S  # noqa: E402
from score_t14_v37 import GT  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

LABEL = D.VOTE                         # "A s012"
JOINED = "A s012 + dupcheck"
ROW_NAMES = {"split": ("A s012", "A s012 + dupcheck"), "nosplit": ("A s012 nosplit", "A s012 nosplit + dupcheck")}
V37 = BB.V37                           # calls, prompt, output tokens of the v3.7 batch (exact)
FAMILIES = BB.FAMILIES
RULES = CE.rules_v11(2)
CARD_COLS = ["set", "level", "ent", "column id", "joined from", "name", "support yes", "support n", "support", "fit yes", "fit n",
             "neighbour fit", "neighbours (yes/n)", "mixed roles", "verdict", "mentions", "dialogues", "distinct values",
             "dominant type", "dominant share", "gt kind", "gt attribute", "label"]
JOIN_COLS = ["set", "config", "ent", "columns", "names", "reason", "code check", "GT status", "why"]


def parser():
    ap = BB.parser()
    ap.set_defaults(out=Path("results/loop1_v38/scores"))
    ap.add_argument("--colab", type=Path, default=Path("results/loop1_v38/colab"))
    return ap


# ---- inputs

def read_responses(colab):
    """{job: response row}: the last row of every responses/<job>.jsonl."""
    out = {}
    for f in sorted((colab / "responses").glob("*.jsonl")):
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
        out[f.stem] = rows[-1]
    return out


def step0(manifest, examples, responses):
    """(DataFrame of the evidence jobs with S.answer_check counts, list of problems). Every job must have a response."""
    ex = examples.groupby("job")
    rows, bad = [], []
    for j in manifest["jobs"]:
        r = responses.get(j["job"])
        if r is None:
            bad.append(f"{j['job']}: no response")
            continue
        if r["finish_reason"] != "stop" or r["errors"]:
            bad.append(f"{j['job']}: finish {r['finish_reason']}, errors {r['errors']}")
        if j["format"] == "evidence":
            c = S.answer_check(set(ex.get_group(j["job"])["example id"]), r["parsed"])
            rows.append({"job": j["job"], "family": j["family"], "set": j["set"], **{k: v for k, v in c.items()
                                                                                       if k in ("expected", "answered")},
                         "missing": len(c["missing"]), "extra": len(c["extra"]), "repeated": len(c["repeated"])})
    return pd.DataFrame(rows), bad


def check_columns(per_ent, colcsv, set_name, config):
    """Stop when the rebuilt column tables differ from columns.csv (name, mentions) of the batch."""
    got = [(ent, c["cid"], c["name"], c["n_mentions"]) for ent, (_, cols) in per_ent.items() for c in cols]
    g = colcsv[(colcsv["set"] == set_name) & (colcsv["config"] == config)]
    want = list(zip(g["ent"], g["column id"], g["name"], g["n mentions"]))
    if got != want:
        raise SystemExit(f"STOP: {set_name} {config}: rebuilt columns differ from columns.csv")


# ---- column facts and joins

def gt_info(pb, label):
    """{ent: DataFrame (column name, cid-free: label, top_attr, kind)} of the columns of variant `label` (dashboard_v38)."""
    return {e: DB._column_labels(ed, label, RULES, {}).set_index("column") for e, ed in pb["lev"].items()}


NO_LABEL = {"label": "unknown", "top_attr": "", "kind": "no_gt"}   # a column with no mention has no label


def label_of(labels, name):
    """Row (label, top_attr, kind) of column `name` in a gt_info frame; NO_LABEL when the column has no mention."""
    return labels.loc[name] if name in labels.index else NO_LABEL


def column_info(ed, label, col, labels):
    """dict (name, label, top_attr, partner) of one column dict for join_right; partner = share of its labelled mentions in the
    role-partner slot of its top attribute (dashboard_v38._col_facts), 0 for a column with no L2 attribute."""
    r = label_of(labels, col["name"])
    partner = DB._col_facts(ed, label, col["groups"], RULES, {}, r["top_attr"])["partner_share"] if r["label"] == "real" else 0.0
    return {"name": col["name"], "label": r["label"], "top_attr": r["top_attr"], "partner": partner}


def score_joins(set_name, config, ent, ed, cols, joins, labels):
    """(rows of JOIN_COLS, kept joins): every join of the dupcheck answer after the code check and against the GT."""
    by_id = {c["cid"]: c for c in cols}
    kept, rejected = BT.check_joins(joins, by_id)
    rejected_ids = {id(j) for j in rejected}
    rows = []
    for j in joins:
        info = [column_info(ed, LABEL, by_id[c], labels) for c in j["columns"]]
        status, why = S.join_right(info)
        rows.append({"set": set_name, "config": config, "ent": ent, "columns": ";".join(map(str, j["columns"])),
                     "names": " | ".join(by_id[c]["name"] for c in j["columns"]), "reason": j["reason"],
                     "code check": "rejected" if id(j) in rejected_ids else "accepted", "GT status": status, "why": why})
    return rows, kept


def final_columns(cols, kept):
    """(final column dicts, {final cid: joined pre-join cids}): kept joins united (transitive); a joined column is named after
    its biggest member (S.join_base)."""
    by_id = {c["cid"]: c for c in cols}
    comps = S.union_joins(kept)
    inside = {c for comp in comps for c in comp}
    final = [{**c, "joined": [c["cid"]]} for c in cols if c["cid"] not in inside]
    for comp in comps:
        final.append(S.join_columns([by_id[c] for c in comp], S.join_base(by_id, comp)))
    final.sort(key=lambda c: c["cid"])
    return final, {c["cid"]: c["joined"] for c in final}


def add_variant(pb, ent, label, vo):
    """Put variant `label` into the raw and the L2 EntityData of `ent` (they may share the variants dict)."""
    for bundle in (pb["raw"], pb["lev"]):
        bundle[ent].variants[label] = vo


def joined_variant(pb, ent, finals, cols):
    """Add variant JOINED: every group of a joined column carries the base column's name; membership is unchanged."""
    ed = pb["lev"][ent]
    vo = ed.variants[LABEL]
    by_id = {c["cid"]: c for c in cols}
    rename = {g: f["name"] for f in finals if len(f["joined"]) > 1 for c in f["joined"] for g in by_id[c]["groups"]}
    add_variant(pb, ent, JOINED, replace(vo, attrs=S.renamed_attrs(vo.attrs, rename)))


# ---- cards

def evidence_tables(manifest, examples, responses):
    """(support {(set, ent, cid): (yes, n)}, src {(set, ent, cid): {source: (yes, n)}}, neigh {(set, ent, cid): [neighbour cids]})
    from the example and neighbour jobs (with-split columns)."""
    source = {j: dict(zip(g["example id"], g["source column"])) for j, g in examples.groupby("job")}
    support, src, neigh = {}, {}, {}
    for j in manifest["jobs"]:
        if j["format"] != "evidence":
            continue
        key = (j["set"], j["ent"], j["column"])
        ans = S.yes_no(responses[j["job"]]["parsed"], set(source[j["job"]]))
        if j["family"] == "example":
            support[key] = (sum(ans.values()), len(ans))
        else:
            src[key] = S.counts_by_source(ans, source[j["job"]])
            neigh[key] = j["neighbours"]
    return support, src, neigh


def card_row(set_name, level, ent, col, names, ev, gt):
    """dict (CARD_COLS) of one column: ev = (support (yes, n) or None, neighbour entries, mixed flag)."""
    (sy, sn), entries, mixed = ev
    fy, fn = sum(e["yes"] for e in entries), sum(e["n"] for e in entries)
    sup, fit = S.share(sy, sn), S.share(fy, fn)
    dom, dsh = S.dominant_share(col["value_types"])
    return {"set": set_name, "level": level, "ent": ent, "column id": col["cid"],
            "joined from": ";".join(map(str, col["joined"])) if len(col.get("joined", [])) > 1 else "", "name": col["name"],
            "support yes": sy, "support n": sn, "support": None if sup is None else round(sup, 3), "fit yes": fy, "fit n": fn,
            "neighbour fit": None if fit is None else round(fit, 3),
            "neighbours (yes/n)": "; ".join(f"{' + '.join(names[c] for c in e['cids'])} {e['yes']}/{e['n']}" for e in entries),
            "mixed roles": mixed, "verdict": S.verdict(sup, fit, mixed), "mentions": col["n_mentions"],
            "dialogues": col["n_dialogues"], "distinct values": col["n_values"], "dominant type": dom,
            "dominant share": round(dsh, 3), "gt kind": gt["kind4"], "gt attribute": gt["top_attr"], "label": gt["label"]}


def cards_of(set_name, ent, cols, finals, support, src, neigh, nearest, gt_pre, gt_fin):
    """(prejoin card rows, final card rows) of one entity of the split config. nearest: {final cid: its nearest final cids}."""
    names = {c["cid"]: c["name"] for c in cols}
    sup_e = {c: v for (s, en, c), v in support.items() if s == set_name and en == ent}
    src_e = {c: v for (s, en, c), v in src.items() if s == set_name and en == ent}
    by_final = {f["cid"]: f for f in finals}
    pre, fin = [], []

    def evidence(members, neighbours):
        entries = S.neighbour_evidence(members, members[0], neighbours, src_e)
        for e in entries:
            e["names"] = [names[c] for c in e["cids"]]
        return (S.pooled_support(members, sup_e), entries, S.mixed_roles([names[m] for m in members], entries))

    for c in cols:
        nb = [[n] for n in neigh.get((set_name, ent, c["cid"]), [])]
        pre.append(card_row(set_name, "prejoin", ent, {**c, "joined": [c["cid"]]}, names, evidence([c["cid"]], nb), gt_pre[c["cid"]]))
    for f in finals:
        members = [f["cid"]] + [m for m in f["joined"] if m != f["cid"]]
        if len(members) == 1:
            nb = [[n] for n in neigh.get((set_name, ent, f["cid"]), [])]
        else:
            nb = [by_final[n]["joined"] for n in nearest[f["cid"]]]
        fin.append(card_row(set_name, "final", ent, f, names, evidence(members, nb), gt_fin[f["cid"]]))
    return pre, fin


def kinds_of(frame, labels):
    """{cid: dict(kind4, top_attr, label)} of the columns of `frame` (dicts with cid, name) from the column labels frame."""
    rows = [label_of(labels, c["name"]) for c in frame]
    k4 = S.gt_kinds(pd.DataFrame({"cid": [c["cid"] for c in frame], "kind": [r["kind"] for r in rows],
                                  "top_attr": [r["top_attr"] for r in rows]}))
    return {c["cid"]: {"kind4": k, "top_attr": r["top_attr"], "label": r["label"]} for c, r, k in zip(frame, rows, k4)}


# ---- reports

def join_summary(jdf):
    """DataFrame per set and config: joins, accepted (by the code check) split by GT status, rejected split the same way."""
    rows = []
    for (s, c), g in jdf.groupby(["set", "config"]):
        acc, rej = g[g["code check"] == "accepted"], g[g["code check"] == "rejected"]
        rows.append({"set": s, "config": c, "joins": len(g), "accepted": len(acc),
                     **{f"accepted {k}": int((acc["GT status"] == k).sum()) for k in S.JOIN_STATUS},
                     "rejected": len(rej), "rejected would be right": int((rej["GT status"] == "right").sum())})
    return pd.DataFrame(rows)


def dashboard_dup_verdicts(pb, finals, fin_cards, ent):
    """Verdicts of the duplicate columns by the dashboard's definition (group majority, found attributes): for every found attribute
    the columns having a group with that majority, beyond the first (lowest id) one; a column counts once per such attribute."""
    ed = pb["lev"][ent]
    gc = CV.group_columns(ed, JOINED)
    fnd = RG.found(ed, JOINED, RULES, {})
    cid_of = {f["name"]: f["cid"] for f in finals}
    verdict_of = dict(zip(fin_cards["column id"], fin_cards["verdict"]))
    out = []
    for attr in fnd.loc[fnd["found"], "attr"]:
        cols = sorted(set(gc.loc[gc["majority"] == attr, "column"]), key=lambda c: cid_of[c])
        out += [verdict_of[cid_of[c]] for c in cols[1:]]
    return out


def md_table(df, cols):
    f = lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else (f"{v:.3f}" if isinstance(v, float) else str(v))  # noqa: E731
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(f(r[c]) for c in cols) + " |" for _, r in df.iterrows()])


def cards_md(cards):
    lines = ["# wf_v3.8 evidence cards and verdicts (verdict rule v0, RULES_V1_2.md)", "",
             "One line per column: `id name | support yes/n | neighbour fit yes/n | verdict | mentions/dialogues/distinct values, "
             "dominant value type share | GT kind (attribute)`. final = columns of A s012 + dupcheck (a joined column pools its "
             "members' answers, id = the biggest member's); prejoin = the columns the batch asked about. Verdict: noise if "
             "support < 0.4; too general / mixed roles if neighbour fit > 0.5; real if support >= 0.7 and fit <= 0.3; else unsure.", ""]
    for (s, level), g in cards.groupby(["set", "level"], sort=False):
        c = Counter(g["verdict"])
        lines += [f"## {s}, {level} ({len(g)} columns)", "", "verdicts: " + ", ".join(f"{v} {c.get(v, 0)}" for v in S.VERDICTS), ""]
        for ent, e in g.groupby("ent", sort=False):
            lines.append(f"**{ent}**")
            for _, r in e.iterrows():
                sup = "n/a" if r["support n"] == 0 else f"{r['support yes']}/{r['support n']}"
                fit = "n/a" if r["fit n"] == 0 else f"{r['fit yes']}/{r['fit n']}"
                join = f" (joined {r['joined from']})" if r["joined from"] else ""
                mix = " MIXED-ROLES-FLAG" if r["mixed roles"] else ""
                lines.append(f"- {r['column id']} {r['name']}{join} | support {sup} | fit {fit}{mix} | **{r['verdict']}** | "
                             f"{r['mentions']}/{r['dialogues']}/{r['distinct values']}, {r['dominant type']} {r['dominant share']:.2f} | "
                             f"{r['gt kind']} ({r['gt attribute'] or '-'}, {r['label']})")
            lines.append("")
    return "\n".join(lines)


def tokens_md(responses, manifest):
    fam = {j["job"]: j["family"] for j in manifest["jobs"]}
    est = Counter()
    for j in manifest["jobs"]:
        est[j["family"]] += j["est_prompt_tokens"]
    rows, tot = [], [0, 0, 0]
    for f in FAMILIES:
        rs = [r for k, r in responses.items() if fam[k] == f]
        v = [len(rs), sum(r["prompt_tokens"] for r in rs), sum(r["output_tokens"] for r in rs)]
        tot = [a + b for a, b in zip(tot, v)]
        rows.append(f"| {f} | {v[0]} | {v[1]:,} | {v[1] // v[0]:,} | {v[2]:,} | {v[2] // v[0]:,} | {est[f]:,} |")
    rows.append(f"| total | {tot[0]} | {tot[1]:,} | {tot[1] // tot[0]:,} | {tot[2]:,} | {tot[2] // tot[0]:,} | {sum(est.values()):,} |")
    d = [t - o for t, o in zip(tot, V37)]
    return "\n".join([
        "# wf_v3.8 batch tokens (exact, from the responses)", "",
        "| family | calls | prompt tokens | per call | output tokens | per call | est. prompt (chars/3.5) |", "|---|---|---|---|---|---|---|",
        *rows, "", f"v3.7 batch: {V37[0]} calls, {V37[1]:,} prompt, {V37[2]:,} output ({V37[1] // V37[0]:,} / {V37[2] // V37[0]:,} per call).",
        f"v3.8 vs v3.7: {d[0]:+d} calls, {d[1]:+,} prompt ({d[1] / V37[1]:+.1%}), {d[2]:+,} output ({d[2] / V37[2]:+.1%}); per call "
        f"{tot[1] // tot[0] - V37[1] // V37[0]:+,} prompt, {tot[2] // tot[0] - V37[2] // V37[0]:+,} output.", ""])


def guard_rows(pb, finals_by_ent, cards_final, set_name):
    """DataFrame of dashboard rows: JOINED with the columns of verdict noise / too general marked out, and with mixed roles too."""
    out = []
    for name, drop in (("A s012 + dupcheck - noise/too general", S.REJECTED), ("A s012 + dupcheck - also mixed roles", S.REJECTED + ("mixed roles",))):
        for ent, finals in finals_by_ent.items():
            ed = pb["lev"][ent]
            c = cards_final[(cards_final["ent"] == ent)].set_index("column id")
            groups = [g for f in finals if c.loc[f["cid"], "verdict"] in drop for g in f["groups"]]
            vo = ed.variants[JOINED]
            add_variant(pb, ent, name, replace(vo, attrs=S.marked_attrs(vo.attrs, groups)))
        out.append(D.rows_for(pb, [name], [name]))
    return pd.concat(out, ignore_index=True)


def checker_md(tables, decisions, guard, notes):
    lines = ["# wf_v3.8 task 11: the checker against the GT (verdict rule v0, RULES_V1_2.md)", ""] + notes + [""]
    for s in tables:
        lines += [f"## {s}", ""]
        for level, (t, cols) in tables[s].items():
            lines += [f"### {level} columns", "", md_table(t, ["gt_kind", "n", *S.VERDICTS, "real_share", "rejected_share",
                                                              "rejected_mixed_share", "not_real_share"]), ""]
        lines += ["### Recall guard if rejected columns were removed (final columns)", "",
                  md_table(guard[s], ["row", "found_train", "found_hotel", "found_restaurant", "found_total", "columns", "dup_columns",
                                      "wrong_columns", "extras_no_gt", "guard", "guard_detail"]), "", f"**Decision, {s}: {decisions[s]}**", ""]
    return "\n".join(lines)


# ---- main

def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((a.colab / "manifest.json").read_text(encoding="utf-8"))
    examples = pd.read_csv(a.colab / "examples.csv")
    colcsv = pd.read_csv(a.colab / "columns.csv")
    responses = read_responses(a.colab)

    s0, bad = step0(manifest, examples, responses)
    tot = s0[["expected", "answered", "missing", "extra", "repeated"]].sum()
    fam0 = s0.groupby("family")[["expected", "answered", "missing", "extra", "repeated"]].sum()
    write(a.out / "step0.md", "# wf_v3.8 step 0: do the answer lists cover the example ids of their prompts?\n\n"
          f"{len(responses)} responses for {len(manifest['jobs'])} manifest jobs; problems (no response, finish not stop, parse errors): "
          f"{bad or 'none'}.\n\n" + md_table(fam0.reset_index(), ["family", "expected", "answered", "missing", "extra", "repeated"])
          + f"\n\nTotal: {int(tot['expected'])} example ids asked, {int(tot['answered'])} answered, {int(tot['missing'])} missing "
          f"(unanswered, never read as no), {int(tot['extra'])} extra ids, {int(tot['repeated'])} repeated ids.\n")
    print(fam0, "\nproblems:", bad)

    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in GT.items()}
    pbs = D.load_both(a, gts)
    support, src, neigh = evidence_tables(manifest, examples, responses)

    join_rows, dash, cards, checks, guards, notes_join = [], [], [], {}, {}, []
    finals_all, extras = {}, {}
    for set_name in D.SETS:
        si = BB.SetInput(set_name)
        for config in BB.CONFIGS:
            pb = pbs[(set_name, config)]
            per_ent = BB.columns_of(pb)
            lab_all = gt_info(pb, LABEL)
            check_columns(per_ent, colcsv, set_name, config)
            for ent, (_, cols) in per_ent.items():
                job = next(j for j in manifest["jobs"] if j["job"] == f"dupcheck_{set_name}_{config}_{ent}")
                parsed = responses[job["job"]]["parsed"]
                labels = lab_all[ent]
                rows, kept = score_joins(set_name, config, ent, pb["lev"][ent], cols, parsed["joins"], labels)
                join_rows += rows
                finals, _ = final_columns(cols, kept)
                joined_variant(pb, ent, finals, cols)
                finals_all[(set_name, config, ent)] = (cols, finals, si)
        sp = pbs[(set_name, "split")]
        ns = pbs[(set_name, "nosplit")]
        dash += [D.rows_for(sp, [LABEL, JOINED], list(ROW_NAMES["split"])), D.rows_for(ns, [LABEL, JOINED], list(ROW_NAMES["nosplit"]))]

        # tasks 8-10 on the with-split columns
        pre_cards, fin_cards, finals_by_ent = [], [], {}
        lab_pre = gt_info(sp, LABEL)
        lab_fin = gt_info(sp, JOINED)
        for ent in DB.ENTS:
            cols, finals, _ = finals_all[(set_name, "split", ent)]
            cent = BT.centroids(finals, si.export.ids, si.export.x)
            nearest = {f["cid"]: BT.nearest(cent, f["cid"]) for f in finals if f["cid"] in cent}
            pre, fin = cards_of(set_name, ent, cols, finals, support, src, neigh, nearest, kinds_of(cols, lab_pre[ent]),
                                kinds_of(finals, lab_fin[ent]))
            pre_cards += pre
            fin_cards += fin
            finals_by_ent[ent] = finals
        cards += [pd.DataFrame(fin_cards, columns=CARD_COLS), pd.DataFrame(pre_cards, columns=CARD_COLS)]

        # task 11
        fin_df, pre_df = cards[-2], cards[-1]
        tables = {}
        for level, df in (("final", fin_df), ("prejoin", pre_df)):
            tables[level] = (S.checker_table(list(df["gt kind"]), list(df["verdict"])), df)
        dd = [v for ent in DB.ENTS for v in dashboard_dup_verdicts(sp, finals_by_ent[ent], fin_df[fin_df["ent"] == ent], ent)]
        tables["final"] = (pd.concat([tables["final"][0], pd.DataFrame([S.verdict_row("duplicate (dashboard def.)", dd)])],
                                     ignore_index=True), fin_df)
        checks[set_name] = tables
        guards[set_name] = guard_rows(sp, finals_by_ent, fin_df, set_name)
        extras[set_name] = (fin_df, pre_df)

    # outputs
    jdf = pd.DataFrame(join_rows, columns=JOIN_COLS)
    write_csv(jdf, a.out / "joins.csv")
    rows = pd.concat(dash, ignore_index=True)
    bad0 = D.check_step0(rows)
    if bad0:
        raise SystemExit("STEP 0 (dashboard) FAILED: " + "; ".join(bad0))
    write_csv(rows, a.out / "dashboard.csv")
    jn = join_summary(jdf)
    write(a.out / "dashboard.md", DB.dashboard_md(rows, title="wf_v3.8 precision dashboard with the duplicate check (L2, rules v1.1, Step 1a v2.2)", notes=[
        "Rows with + dupcheck: the dupcheck joins that pass the code check (role pairs by the method's own names) are applied; a joined "
        "column keeps all groups of its members under one name (the biggest member's). Found, merges, noise and marks are per group / "
        "cluster, so joining does not change them; only columns, columns per found, dup, wrong and extras can change. Recall guard: "
        "RULES_V1_2.md.", "Joins: " + "; ".join(f"{r['set']} {r['config']}: {r['joins']} joins, {r['accepted']} accepted "
                                                f"({r['accepted right']} right, {r['accepted wrong']} wrong, {r['accepted no_gt']} no GT), {r['rejected']} rejected" for _, r in jn.iterrows())]))
    for s, (fin_df, pre_df) in extras.items():
        write_csv(pd.concat([fin_df, pre_df], ignore_index=True), a.out / f"cards_{s}.csv")
    allc = pd.concat([x for s in extras for x in extras[s]], ignore_index=True)
    write(a.out / "cards.md", cards_md(allc))
    write(a.out / "tokens.md", tokens_md(responses, manifest))

    decisions, notes = {}, []
    for s in checks:
        fin_t = checks[s]["final"][0].set_index("gt_kind")
        wrong = fin_t.loc["wrong"]
        g = guards[s].iloc[0]
        ok, line = S.filter_decision(int(wrong["n"]), int(wrong["noise"] + wrong["too general"]), g["guard"] == "pass")
        decisions[s] = line
        g2 = guards[s].iloc[1]
        ok2, line2 = S.filter_decision(int(wrong["n"]), int(wrong["noise"] + wrong["too general"] + wrong["mixed roles"]), g2["guard"] == "pass")
        if ok2 != ok:
            decisions[s] += f" (with mixed roles also rejected the decision would flip: {line2})"
    notes = ["GT kinds (final and prejoin columns of the with-split config): gt = first column (lowest id) of an L2 attribute of the "
             "entity (column label real, top attribute in the entity's L2 base); duplicate = a further such column of an attribute that "
             "already has one; wrong = wrong entity (label real, attribute of another entity) or noise (label noise, rules v1.1 60%); "
             "no_gt = mixed / unknown. rejected = verdict noise or too general; rejected_mixed also counts mixed roles; not_real = any "
             "verdict but real (rejected or flagged). The extra row 'duplicate (dashboard def.)' (final columns) counts the duplicates as the "
             "dashboard does: for every found attribute, the columns having a group with that majority label beyond the first (a "
             "column counts once per attribute); it overlaps the other rows."]
    guard_all = {s: guards[s] for s in guards}
    write_csv(pd.concat(guards.values(), ignore_index=True), a.out / "checker_guard.csv")
    write(a.out / "checker.md", checker_md(checks, decisions, guard_all, notes))
    for s in decisions:
        print(s, decisions[s])
    print(jn.to_string())
    print(rows[["set", "row", "found_total", "columns", "columns_per_found", "dup_columns", "wrong_columns", "extras_no_gt", "review_edits", "guard"]].to_string())


if __name__ == "__main__":
    main()
