"""wf_v3.6 scoring of the Colab batch (results/loop1_v36/colab): A s2, AE, oracle, g, F2 next to the v3.5 rows, at GT level 1
and 2 with rules v1, plus the A order range and gain verdict, the oracle decision, g's role examples and role guard, noise
at L2, column precision, F2 vs E s0 and the name sheet for the new variants. No LLM, no models.

python scripts/score_v36.py --dir33 ../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 --dir36 results/loop1_v36/colab
         --gt results/loop1_v35 --out results/loop1_v36 --invalid config/invalid_runs_v36.json]
Writes <out>/{all_variants_v36.md, all_variants_v36.csv, gain_v36.csv, oracle_decision.md, g_roles.md, noise_l2_v36.md,
noise_l2_v36.csv, column_precision_v36.md, column_precision_v36.csv, f2_delex.md, names_to_rate_l2_new.csv,
names_to_rate_l2_new_key.csv, repairs_v36.csv}. All v3.6 responses are read with the parse repair on (llm_cache.repair_undeclared),
A r1 / A r2 too; the older v3.3 rows are read as saved. A r1 / A r2 / A s2 = A orders 0 / 1 / 2; AE s0 / s1 / s2 = AE orders.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import checks_v35 as CK  # noqa: E402
from s1a import g_roles_v36 as GR  # noqa: E402
from s1a import names_l2 as NL  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import oracle_v35 as OR  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import precision_v36 as PR  # noqa: E402
from s1a import range_v36 as RV  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import v34_data, v35_data, v36_data  # noqa: E402
from checks_v35 import prepare_extra as checks_extra  # noqa: E402
from pilot_eval_v32 import _jobs, _objs  # noqa: E402
from precision_v36 import COMPARE, INVALID_F, extras_rows, f_delex_md, score_rows  # noqa: E402
from score_v35 import HEAD, repairs_frame, score_levels, variant_cells  # noqa: E402

LEVELS = (1, 2)
DISPLAY = {"A r1": "A r1 (order 0)", "A r2": "A r2 (order 1)", "A s2": "A s2 (order 2)"}
NEW = ["E s0", "F2 s0", "AE s0", "AE s1", "AE s2", "AE s012", "Oracle s0", "Oracle s1", "Oracle s2", "Oracle s012",
       "g s0", "g s1", "g s2", "g s012"]
ROWS = ["A r1", "A r2", "A s2", ("range", "A"), "B s0", "C s0", "C s1", "C s2", "C s012", "D s012", "C33 s012", "E s012",
        "E1 s012", "E2 s012", "E s0", "F2 s0", "AE s0", "AE s1", "AE s2", ("range", "AE"), "AE s012", "Oracle s0",
        "Oracle s1", "Oracle s2", "Oracle s012", "g s0", "g s1", "g s2", "g s012"]
VARIANTS = [r for r in ROWS if isinstance(r, str)]
RANGES = {"A": RV.A_ORDERS, "AE": RV.AE_ORDERS}
GAIN_VARIANTS = [v for v in VARIANTS if v not in RV.A_ORDERS]


def show(label):
    return DISPLAY.get(label, label)


def write(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def write_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


# ---- data

def load_bundles(a, repairs):
    """(shared, {name: {ent: EntityData}}, notes): the v3.4 bundle (A r1 / r2 repaired), the v3.3 bundle with E s0, F s0 and
    F2 s0, the v3.6 batch (A s2, AE, g) and the oracle bundle."""
    shared, data = v34_data.load_all(a.run, a.dir32, a.dir31, repairs)
    data33, notes = v35_data.load_v33(shared, data, a.dir33, a.dir32)
    data33, n = PR.seed0_variants(data33, shared, a.dir33, [("E", "e"), ("F", "f")])
    notes += n
    data33, n = PR.seed0_variants(data33, shared, a.dir36, [("F2", "f2")], repairs)
    notes += n
    data36, n = v36_data.load_v36(shared, data, a.dir36, a.dir32, a.dir31, repairs)
    notes += n
    oracle, n = v36_data.load_oracle(shared, data, a.dir36, a.dir32, a.gt / "oracle_clusters.csv", repairs)
    notes += n
    return shared, {"v34": data, "v33": data33, "v36": data36, "oracle": oracle}, notes


# ---- tables

def variant_rows(df):
    """{variant: entity rows} of one level."""
    return {v: g for v, g in df.groupby("variant", sort=False)}


L2_NAMES = "names L2 rated"


def agreement(out):
    """(k, n) of rows where the two raters of names_l2_new_rater{1,2}.csv give the same label."""
    a, b = (pd.read_csv(out / f"names_l2_new_rater{i}.csv") for i in (1, 2))
    m = a.merge(b, on="row")
    return int((m["label_x"] == m["label_y"]).sum()), len(m)


def all_variants_md(df, invalid, notes, df_l2r=None, levels=LEVELS, rows=ROWS, title="wf_v3.6 all variants",
                    rules="Rules v1"):
    bad = invalid
    lines = [f"# {title}", "",
             f"{rules}, GT level 1 = TEAR gold, 2 = + MultiWOZ 2.2 schema slots (choice mentions are noise at every level). "
             "Counts are k/n (share); noise, merge, names, role and cue are summed over the 3 entities. A r1 / A r2 / A s2 "
             "are A's orders 0 / 1 / 2 (A r2 now parse-repaired, so no run is invalid); AE s0 / s1 / s2 are AE's orders. "
             "Range rows give the min\u2013max of each count over the 3 orders (n as it varies). The names column uses the v34 "
             "rule (rated sheet of v3.4 / v3.5; unrated groups count as not right; at L2 a valid_extra group counts as right, "
             "an approximation). At L2, `names L2 rated` is the names=l2rated switch (2 raters, name vs L2 slot, "
             "names_l2_rater{1,2}.csv); unrated groups count as not right.", ""]
    for level in levels:
        by = variant_rows(df[df["level"] == level])
        l2r = variant_rows(df_l2r) if level == 2 and df_l2r is not None else None
        head = HEAD + ([L2_NAMES] if l2r else [])
        lines += [f"## Level {level}", "", "| variant | " + " | ".join(head) + " |", "|---|" + "---|" * len(head)]
        for row in rows:
            if isinstance(row, tuple):
                orders = [by[v] for v in RANGES[row[1]] if v in by]
                if len(orders) == 3:
                    cells = RV.range_cells(orders) + ([RV.range_cells([l2r[v] for v in RANGES[row[1]]])[5]] if l2r else [])
                    lines.append(f"| {row[1]} range (3 orders) | " + " | ".join(cells) + " |")
            elif row in by:
                inv = {r["ent"] for r in bad if r["variant"] == row}
                cells = variant_cells(by[row], inv) + ([variant_cells(l2r[row], inv)[5]] if l2r else [])
                lines.append(f"| {show(row)} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"


def gain_tables(df, invalid):
    """DataFrame of gain_vs_range rows for every level, and its markdown block."""
    parts = []
    for level in LEVELS:
        t = RV.found_table(df[df["level"] == level], invalid)
        parts.append(RV.gain_vs_range(t, GAIN_VARIANTS, RV.A_ORDERS, level))
    out = pd.concat(parts, ignore_index=True)
    out["variant"] = out["variant"].map(show)
    lines = ["## Gain against A's order range (Q8)", "",
             "Found attributes per entity and in total. A range = min\u2013max of A's 3 orders' totals. Gain only above A's "
             f"max (total - A max >= {RN.GAIN_MIN} and no entity under its own A min); loss only below A's min; else within "
             "the A range.", ""]
    cols = ["variant", "found train", "found hotel", "found restaurant", "total", "A range total", "gain over A max",
            "loss under A min", "verdict"]
    for level, g in out.groupby("level"):
        lines += [f"### Level {level}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        lines += ["| " + " | ".join(str(int(r[c])) if isinstance(r[c], float) and r[c] == r[c] else str(r[c])
                                    for c in cols) + " |" for _, r in g.iterrows()]
        lines.append("")
    return out, lines


def oracle_md(df):
    lines = ["# wf_v3.6 oracle role split (T14): decision for J", "",
             "Oracle = the v3.2 C prompt on the cluster table where every two-role cluster is split by gold role (train: 9 "
             "clusters; hotel and restaurant have none, so their oracle rows are the C rows). C = the same prompt without "
             "the split (v3.2). Found = gold attributes with a group of purity >= 0.6 and coverage >= 10%. Rule: build J "
             f"only if oracle gains >= {RV.ORACLE_PASS_GAIN} attributes at L2 and no entity loses one.", ""]
    verdict = {}
    for level in sorted(LEVELS, reverse=True):
        t = RV.found_table(df[df["level"] == level], [])
        gold = df[(df["level"] == level) & (df["variant"] == "C s012")].set_index("ent")["gold_n"]
        lines += [f"## Level {level}", "", "| variant | found train | found hotel | found restaurant | total |",
                  "|---|---|---|---|---|"]
        for v in ("C s0", "Oracle s0", "C s1", "Oracle s1", "C s2", "Oracle s2", "C s012", "Oracle s012"):
            cells = [f"{int(t.loc[e, v])}/{int(gold[e])}" for e in RV.ENTS]
            lines.append(f"| {v} | " + " | ".join(cells) + f" | {int(t[v].sum())}/{int(gold.sum())} |")
        passed, d, total = RV.oracle_decision(t)
        order = ", ".join(f"{o} {int(t[f'Oracle {o}'].sum() - t[f'C {o}'].sum()):+d}" for o in ("s0", "s1", "s2"))
        lines += ["", f"Oracle s012 minus C s012: " + ", ".join(f"{e} {int(d[e]):+d}" for e in RV.ENTS)
                  + f", total {int(total):+d}. Per order (total): {order}.", ""]
        verdict[level] = (passed, d, total)
    for level in sorted(LEVELS, reverse=True):
        passed, d, total = verdict[level]
        lines.append(f"**Decision at L{level}** (build J only if oracle gains >= {RV.ORACLE_PASS_GAIN} attributes and no entity "
                     f"loses one): **{'PASS' if passed else 'FAIL'}** (total {int(total):+d}; " +
                     ", ".join(f"{e} {int(d[e]):+d}" for e in RV.ENTS) + ")" + ("" if level != 1 else " (L1 shown for reference)"))
        lines.append("")
    return "\n".join(lines) + "\n"


# ---- g: role examples and role guard

def gold_roles(shared, gt):
    """(Series mention_id -> gold L2 role, {cluster_id: role pair}) over all clustered mentions (as pilot_build_v35)."""
    mm = shared.e.mentions
    gold_l2 = mm["mention_id"].astype(int).map(dict(zip(gt["mention_id"].astype(int), gt["gt_L2"]))).fillna("")
    role, two = OR.two_roles(mm, gold_l2)
    return pd.Series(role.values, index=mm["mention_id"].astype(int).values), two


def g_report(shared, data, a, gt):
    """(rows DataFrame per order, cluster, md lines) of g's role_examples against gold L2 roles and the role-guard counts."""
    role, two = gold_roles(shared, gt)
    jobs36, jobs32 = _jobs(a.dir36), _jobs(a.dir32)
    ex_all = pd.read_csv(a.dir36 / "examples.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    rows, guard = [], []
    for ent, ed in data.items():
        split32 = _objs(a.dir32, [j for j in jobs32 if j["ent"] == ent], "split")
        for s in range(3):
            jobs = [j for j in jobs36 if j["ent"] == ent and j["variant"] == "g" and j["run_tag"] == f"s{s}"]
            items, texts = [], {}
            for j in jobs:
                obj = PC.load_obj(a.dir36, j, [])
                ex = ex_all[ex_all["variant"] == j["job"]]
                ex_role = {x: role.get(int(m), "") for x, m in zip(ex["ex_id"], ex["mention_id"])}
                items += [(c, ex_role) for c in (obj or {}).get("clusters") or []]
                texts.update(GR.cluster_texts(obj))
            rows += [{"ent": ent, "order": s, **r} for r in GR.cluster_rows(items, two)]
            dec = PC.decisions_b(a.dir36, ent, s, split32, variant="g", repairs=[])
            examined, blocked = GR.guard_counts(dec, PS.name_merge(dec, ed.mentions, ed.entity), texts)
            guard.append({"ent": ent, "order": s, "examined": examined, "blocked": blocked,
                          "own": GR.own_blocked(dec, texts)})
    return pd.DataFrame(rows), guard, two


def g_roles_md(rows, guard, two):
    n_two = len(two)
    lines = ["# wf_v3.6 variant g: role examples vs gold L2 roles", "",
             f"g = the v3.2 C prompt with the role-aware example picker, the mixed instruction asking for `role_examples` "
             "(an attribute and its example ids per role) and an optional `role_examples` field. Two-role clusters "
             f"(gold L2 roles of both slots of a pair, each >= 20%): {n_two}, all in train ({', '.join(sorted(two))}). "
             "Accuracy: each role_examples group takes the majority gold role of its examples (a tie takes none); the "
             "largest group claims a role first and a later group with a role already claimed gets none; k = examples "
             "whose gold role is their group's role, n = examples with a gold role of the pair.", "",
             "| order | two-role clusters flagged mixed | with role_examples | roles told apart | role accuracy k/n | "
             "mixed flags elsewhere |", "|---|---|---|---|---|---|"]
    for s in range(3):
        o = rows[rows["order"] == s]
        t, other = o[o["two_role"]], o[~o["two_role"]]
        lines.append(f"| g s{s} | {int(t['mixed'].sum())}/{len(t)} | {int(t['has_role_examples'].sum())}/{len(t)} | "
                     f"{int(t['separated'].sum())}/{int(t['has_role_examples'].sum())} | "
                     f"{SR.fmt_count(t['k'].sum(), t['n'].sum())} | {int(other['mixed'].sum())}/{len(other)} |")
    t = rows[rows["two_role"]]
    lines += [f"| all 3 orders | {int(t['mixed'].sum())}/{len(t)} | {int(t['has_role_examples'].sum())}/{len(t)} | "
              f"{int(t['separated'].sum())}/{int(t['has_role_examples'].sum())} | "
              f"{SR.fmt_count(t['k'].sum(), t['n'].sum())} | |", "",
              "## Two-role clusters (per order: mixed / role_examples groups / k/n)", "",
              "| cluster | roles | " + " | ".join(f"s{s}" for s in range(3)) + " |", "|---|---|---|---|---|"]
    for cid in sorted(two, key=lambda c: int(c.split("#")[1])):
        cells = []
        for s in range(3):
            r = rows[(rows["order"] == s) & (rows["cluster_id"] == cid)].iloc[0]
            cells.append(f"{'mixed' if r['mixed'] else 'not mixed'} / {r['groups']} groups / {int(r['k'])}/{int(r['n'])}")
        lines.append(f"| {cid} | {' vs '.join(two[cid])} | " + " | ".join(cells) + " |")
    lines += ["", "## Role guard on g's cross-group name merge", "",
              "`role_guard.forbidden_merge` on the cluster pairs that `PS.name_merge` (same normalized name and placement, as "
              "in v3.2 C+namemerge) newly joins across the responses; text = attribute name + role. A merge across a role "
              "pair (departure / destination, leave at / arrive by, location / address) would be blocked. There is no "
              "reconcile job in this batch, so only the name merge is checked; `own` = the same check on the merges inside "
              "each response.", "", "| order | name-merge pairs examined | blocked | own merges blocked |", "|---|---|---|---|"]
    for s in range(3):
        g = [x for x in guard if x["order"] == s]
        lines.append(f"| g s{s} | {sum(x['examined'] for x in g)} | {sum(len(x['blocked']) for x in g)} | "
                     f"{sum(len(x['own']) for x in g)} |")
    blocked = [(x["ent"], x["order"], p) for x in guard for p in x["blocked"] + x["own"]]
    if blocked:
        lines += ["", "Blocked pairs: " + "; ".join(f"{e} s{s} {p[0]} + {p[1]}" for e, s, p in blocked)]
    return "\n".join(lines) + "\n"


# ---- noise, precision, F2, names

def noise_part(shared, bundles, gt, a, invalid, out):
    extra = NV.prepare_extra(shared, list(bundles.values()), a.gt, a.dir32, gt_levels=gt)
    rows = pd.concat([NV.noise_l2_rows(b, extra, VARIANTS, invalid) for b in bundles.values()], ignore_index=True)
    rows = rows.assign(order=rows["variant"].map(VARIANTS.index)).sort_values(["order", "ent"]).drop(columns="order")
    rows["variant"] = rows["variant"].map(show)
    write_csv(rows, out / "noise_l2_v36.csv")
    table = NV.noise_l2_table(rows)
    write(out / "noise_l2_v36.md", NV.noise_l2_md(table, invalid).replace("# wf_v3.6 noise at L2", "# wf_v3.6 noise at L2, with the Colab batch"))
    return table


def precision_part(shared, bundles, gt, a, invalid, out, notes, extra):
    labels = VARIANTS + ["F s0"]
    extras = {k: checks_extra(shared, b, Path("results/loop1_v34"), a.dir32) for k, b in bundles.items()}
    rows = pd.concat([r for k, b in bundles.items() for r in extras_rows(b, labels, gt, extras[k])], ignore_index=True)
    order = [v for v in labels if v in set(rows["variant"])]
    table = PR.precision_table(rows, invalid, order)
    table["variant"] = [show(f"{v}") + (" (invalid)" if v in INVALID_F else "") for v in table["variant"]]
    write_csv(table, out / "column_precision_v36.csv")
    inv = [f"{r['variant']} {r['ent']} left out ({r.get('reason', 'invalid')})" for r in invalid]
    inv += [f"{v} is shown but invalid: {why}" for v, why in INVALID_F.items()]
    write(out / "column_precision_v36.md", PR.precision_md(table, inv))
    kinds = rows[rows["variant"].isin(COMPARE)]
    ktable = CK.extras_table(kinds)
    ktable.index = [f"{v} (invalid)" if v in INVALID_F else v for v in ktable.index]
    scores = score_rows(bundles["v33"], COMPARE, shared, dict(extra))  # the same extra (rated names, GT levels) as the main table
    knotes = [f"F: {INVALID_F['F s0']}.", "F2 = the same job set with the fixed delex map (only real entity names: DB names, "
              "stations, TR ids; generic words stopped).",
              "E s0 = same prompt without delex; all three are one order (seed 0), no gate or split.",
              "Extras = distinct final attributes per kind (T38); the kinds are the GT levels of the attribute's majority label."]
    knotes += [f"Note: {n}" for n in notes if "F2" in n]
    write(out / "f2_delex.md", f_delex_md(ktable, scores, knotes).replace("task 11: F de-lexicalisation", "F2 (fixed delex) vs E s0 and F"))
    return table, ktable, scores


def names_part(bundles, gt, a, out):
    """names_to_rate_l2_new.csv (+ key): the (ent, name, description, L2 slot) groups of the new rows that are not on the
    rated sheet (names_to_rate_l2_key.csv). Row ids continue after the old sheet, so the rater files can be appended."""
    tear_map = {k: v for k, v in json.loads(a.tear_map.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    schema = json.loads((a.mwoz / "schema.json").read_text(encoding="utf-8"))
    slot_desc = {s["name"]: s["description"] for svc in schema for s in svc["slots"]}
    old = pd.read_csv(out / "names_to_rate_l2_key.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    rows = NL.l2_group_rows([PR.only(b, NEW) if k == "v33" else b for k, b in bundles.items()], gt)
    seen = set(map(tuple, old[RN.JOIN_KEYS].values))
    rows = rows[[tuple(r) not in seen for r in rows[RN.JOIN_KEYS].values]]
    if not len(rows):  # everything is on the (extended) rated sheet: leave the new-sheet files as they are
        return 0, len(old)
    rater, key = NL.rating_sheet(rows, tear_map, slot_desc)
    start = int(old["row"].astype(int).max()) + 1
    rater["row"], key["row"] = rater["row"] + start, key["row"] + start
    write_csv(rater, out / "names_to_rate_l2_new.csv")
    write_csv(key, out / "names_to_rate_l2_new_key.csv")
    return len(rater), len(old)


def make_parser(out=Path("results/loop1_v36"), doc=__doc__):
    """The command line of this script; score_v37 builds its own on the same arguments (other --out default)."""
    ap = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=Path("results/graph_v22_dev50"))
    ap.add_argument("--dir32", type=Path, default=Path("results/loop1_v32"))
    ap.add_argument("--dir31", type=Path, default=Path("results/loop1_v31"))
    ap.add_argument("--dir33", required=True, type=Path)
    ap.add_argument("--dir36", type=Path, default=Path("results/loop1_v36/colab"))
    ap.add_argument("--gt", type=Path, default=Path("results/loop1_v35"))
    ap.add_argument("--mwoz", required=True, type=Path, help="MultiWOZ 2.2 folder (schema.json)")
    ap.add_argument("--tear-map", type=Path, default=Path("config/tear_to_mwoz.json"))
    ap.add_argument("--out", type=Path, default=out)
    ap.add_argument("--invalid", type=Path, default=Path("config/invalid_runs_v36.json"))
    return ap


def main():
    a = make_parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    invalid = RN.invalid_runs(a.invalid)

    repairs = []
    shared, bundles, notes = load_bundles(a, repairs)
    gt = v34_data.read_gt_levels(a.gt / "gt_levels.csv")
    extra = SR.load_extra(a.gt, a.dir32)
    extra["gt_levels"] = gt
    df = pd.concat([score_levels("default", LEVELS, bundles["v34"], shared, extra, bundles["v33"]),
                    score_levels("default", LEVELS, bundles["v36"], shared, extra),
                    score_levels("default", LEVELS, bundles["oracle"], shared, extra)], ignore_index=True)
    extra_l2 = SR.load_extra(a.gt, a.dir32, l2_dir=a.out)   # names=l2rated: names_l2_rater{1,2}.csv + names_to_rate_l2_key.csv
    extra_l2["gt_levels"] = gt
    rules = "default,names=l2rated"
    df_l2r = pd.concat([score_levels(rules, (2,), bundles["v34"], shared, extra_l2, bundles["v33"]),
                        score_levels(rules, (2,), bundles["v36"], shared, extra_l2),
                        score_levels(rules, (2,), bundles["oracle"], shared, extra_l2)], ignore_index=True)
    df = df.assign(display=df["variant"].map(show))
    df = df.merge(df_l2r[["ent", "variant", "name_right", "name_base", "names_unrated"]].rename(columns={
        "name_right": "name_right_l2rated", "name_base": "name_base_l2rated", "names_unrated": "names_unrated_l2rated"}),
        on=["ent", "variant"], how="left")
    write_csv(df, a.out / "all_variants_v36.csv")
    gain, gain_lines = gain_tables(df, invalid)
    write_csv(gain, a.out / "gain_v36.csv")
    md_notes = [f"Note: {n}" for n in notes] + [
        "AE s0 / s1 / s2 and A s2 are read like A r1 / r2 (the v3.1 split pass, first tag, is the fallback split); AE s012 is "
        "the 3-order vote like C s012. g is read like v3.2 C (v3.2 split pass, vote).",
        "Oracle: train on the oracle cluster table (T14); hotel and restaurant have no two-role cluster, so their oracle rows "
        "are the C rows. E s0 / F2 s0: one order, no gate or split, cue spread on (as v3.3 E / F).",
        f"Repairs: {len(repairs)} responses needed the parse repair (repairs_v36.csv)."]
    write(a.out / "all_variants_v36.md", all_variants_md(df, invalid, md_notes, df_l2r) + "\n" + "\n".join(gain_lines))
    write(a.out / "oracle_decision.md", oracle_md(df))
    rows, guard, two = g_report(shared, bundles["v34"], a, gt)
    write(a.out / "g_roles.md", g_roles_md(rows, guard, two))
    noise = noise_part(shared, bundles, gt, a, invalid, a.out)
    precision, ktable, scores = precision_part(shared, bundles, gt, a, invalid, a.out, notes, extra)
    n_new, n_old = names_part(bundles, gt, a, a.out)
    write_csv(repairs_frame(repairs), a.out / "repairs_v36.csv")
    print("rater agreement on the new names: %d/%d" % agreement(a.out))
    print(f"rows {len(df)}; repairs {len(repairs)}; names_to_rate_l2_new.csv {n_new} rows (the old sheet has {n_old})")
    for n in notes:
        print("note:", n)


if __name__ == "__main__":
    main()
