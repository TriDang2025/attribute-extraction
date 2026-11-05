"""wf_v3.9 Phase 2 (diary tasks 6-7): keep-apart pairs on Step 1a v2.2, and A s012 + split back. No GPU, no LLM, no gold in the split.

python scripts/splitback_v39.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--out results/loop1_v39/p2]
Task 6: graph (s1a/graph.build_graphs) and draft schema (s1a/draft_schema.build, sim_thr = the SIM_Q quantile of graph_run) of
results/graph_v22_dev50/spans and ..._dev50b/spans. Node status: dev50 = select/nodes_status.csv (also rebuilt from chosen.json as a
check); dev50b has no select/, so dev50's chosen.json is applied to its nodes.csv (the --chosen mode of graph_run select, no tuning).
Task 7: variant "A s012 + split back" (s1a/splitback_v39.py) added to the bundle as score_v38.joined_variant does, dashboard rows
(s1a/dashboard_v38), the fate of the v3.8 judged merges. Step 0: A s012 and the wrong merges reproduce v3.8.
Writes <out>/{keep_apart.csv, splits.csv, merge_fate.csv, dashboard.csv, p2.md}.
"""

import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dashboard_v38 as D  # noqa: E402
import graph_run as GRUN  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import draft_schema as DS  # noqa: E402
from s1a import graph as GR  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import merges_v38 as M  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import rules_groups as RG  # noqa: E402
from s1a import splitback_v39 as SB  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from score_t14_v37 import GT  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402
from score_v38 import add_variant  # noqa: E402

VOTE = D.VOTE
NEW_ALL, NEW_VOTE = "A s012 + split back (all names)", "A s012 + split back (vote names)"
VARIANTS = {NEW_ALL: "all", NEW_VOTE: "vote"}   # row -> which names the role test reads
V38_WRONG = Path("results/loop1_v38/merges")
ENT_ID = {"train": "E1", "hotel": "E0", "restaurant": "E2"}


def parser():
    ap = D.parser()
    ap.set_defaults(out=Path("results/loop1_v39/p2"))
    return ap


def _read_nodes(d):
    return pd.read_csv(d / "nodes.csv", keep_default_na=False, na_values=[""])


# ---- task 6

def keep_apart(set_name, run, chosen):
    """(Export, KA_COLS rows, notes) of one set. Notes = the checks against the existing select/ and schema/ (dev50 only)."""
    d = run / "spans"
    e = MN.load(d)
    g = GR.build_graphs(e)
    nodes = SB.status_from_chosen(_read_nodes(d), chosen)
    notes = []
    if (d / "select" / "nodes_status.csv").exists():
        old = pd.read_csv(d / "select" / "nodes_status.csv", keep_default_na=False, na_values=[""])
        same = (old["status"].values == nodes["status"].values).all() and (old["cluster_id"].values == nodes["cluster_id"].values).all()
        notes.append(f"status rebuilt from chosen.json = select/nodes_status.csv: {'yes' if same else 'NO'} "
                     f"({int((nodes['status'] == 'kept').sum())} kept of {len(nodes)})")
    else:
        notes.append(f"no select/: chosen.json of dev50 applied ({int((nodes['status'] == 'kept').sum())} kept of {len(nodes)})")
    kept = set(nodes.loc[nodes["status"] == "kept", "cluster_id"])
    sim_thr = SB.sim_threshold(g.sim, kept, GRUN.SIM_Q)
    schema = DS.build(e, g, nodes, sim_thr=sim_thr)
    rows = SB.keep_apart_rows(set_name, schema, e.clusters.set_index("cluster_id")["top_values"].to_dict())
    notes.append(f"sim_thr {sim_thr:.4f} (quantile {GRUN.SIM_Q} of kept-pair cosines)")
    if (d / "schema" / "eval.json").exists():
        ev = json.loads((d / "schema" / "eval.json").read_text(encoding="utf-8"))
        old = {(r["entity"], *sorted((r["cluster_a"], r["cluster_b"])), r["count"])
               for r in rows}
        existing = set()
        for f in sorted((d / "schema").glob("E[0-9].json")):
            for h in json.loads(f.read_text(encoding="utf-8"))["keep_apart"]:
                existing.add((f.stem, *sorted(h["nodes"]), h["count"]))
        notes.append(f"sim_thr in schema/eval.json {ev['sim_thr']:.4f}; keep-apart pairs: new {len(old)}, existing schema/ "
                     f"{len(existing)}, identical {'yes' if old == existing else 'NO: only new ' + str(sorted(old - existing)) + ' only old ' + str(sorted(existing - old))}")
    return e, rows, notes


# ---- task 7

def split_entity(set_name, ent, ed, orders, apart, cent, top, desc_of, role_labels):
    """(plan, SPLIT_COLS rows) for one entity of the prepared bundle: every group of A s012 with >= 2 clusters and a conflict."""
    vo = ed.variants[VOTE]
    names = {lab: M.decision_names(ed.variants[lab].dec) for lab in (*orders, VOTE)}
    size = ed.mentions.groupby("cluster_id").size().to_dict()
    own = {c: n for c, (n, _) in names[VOTE].items()}
    plan, rows = {}, []
    for _, r in vo.attrs.iterrows():
        clusters = [c for c in str(r["clusters"]).split(";") if c]
        if len(clusters) < 2 or r["source"] == "split":
            continue
        texts = {c: [names[lab][c][0] for lab in role_labels if c in names[lab] and names[lab][c][0]] for c in clusters}
        conf = SB.conflicts(clusters, apart, texts)
        if not conf:
            continue
        cols = SB.split_columns(clusters, conf, size, cent)
        nms = SB.column_names(r["name"], cols, own, top, size)
        plan[r["attr_id"]] = [{"clusters": col, "name": nm,
                               "description": next((desc_of[c] for c in sorted(col, key=lambda c: (-size.get(c, 0), c)) if desc_of.get(c)),
                                                   r["description"])}
                              for col, nm in zip(cols, nms)]
        rows.append({"set": set_name, "ent": ent, "attr_id": r["attr_id"], "name": r["name"], "n_clusters": len(clusters),
                     "conflicts": "; ".join(f"{'+'.join(sorted(k))} ({w})" for k, w in sorted(conf.items(), key=lambda kv: sorted(kv[0]))),
                     "columns": " | ".join(",".join(c) for c in cols), "column_names": " | ".join(nms)})
    return plan, rows


def run_set(set_name, pb, ka_rows, export, orders, rules, new, role_labels):
    """Adds variant `new` to `pb` (role test on the names of `role_labels`); returns (split rows, fate rows, wrong merges after, orphan mentions, wrong merges before ids)."""
    cent = GR.centroids(export)
    cl = export.clusters.set_index("cluster_id")
    top = {c: next((v for v in str(t).split("|") if v and v != "nan"), "") for c, t in cl["top_values"].items()}
    split_rows, fate, wrong_after, orphans, wrong_ids = [], [], 0, 0, set()
    for ent, ed in pb["lev"].items():
        vo = ed.variants[VOTE]
        desc_of = vo.dec.set_index("cluster_id")["description"].to_dict()
        plan, rows = split_entity(set_name, ent, ed, orders, SB.apart_pairs(ka_rows, ed.entity), cent, top, desc_of, role_labels)
        split_rows += rows
        mention_cluster = {int(i): c for i, c in zip(ed.mentions["mention_id"], ed.mentions["cluster_id"])}
        attrs, assign, n_orph = SB.apply_split(vo.attrs, vo.assign, mention_cluster, plan)
        orphans += n_orph
        add_variant(pb, ent, new, replace(vo, attrs=attrs, assign=assign))
        before, after = RG.merges(ed, VOTE, rules, {}), RG.merges(ed, new, rules, {})
        wrong_ids |= {(ent, a) for a in before.loc[before["judged"].astype(bool) & ~before["right"].astype(bool), "attr_id"]}
        wrong_after += int((after["judged"].astype(bool) & ~after["right"].astype(bool)).sum())
        fate += SB.merge_fate(set_name, ent, before, after, M.cluster_groups(attrs))
    return split_rows, fate, wrong_after, orphans, wrong_ids


# ---- report

def md_table(df, cols):
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
                     + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in df.iterrows()])


def report(ka, notes, splits, fate, counts, wrong_after, orphans, dash, decisions):
    rows = list(VARIANTS)
    L = ["# wf_v3.9 phase 2: keep-apart pairs and split back (A s012, Step 1a v2.2, L2, rules v1.1)", "",
         "Scripts: `scripts/splitback_v39.py`, `s1a/splitback_v39.py`. No LLM, no GPU. The split uses no gold: only keep-apart pairs "
         "(graph) and the method's own names. Gold is used only to score.", "",
         "## Task 6: keep-apart pairs", "",
         "Keep apart = two kept clusters of one entity with centroid cosine >= sim_thr (top 5% of kept-pair cosines) that co-occur in "
         "at least one instance. Per entity (E1 train, E0 hotel, E2 restaurant, E3 / E4 other entities):", ""]
    for s, g in ka.groupby("set", sort=False):
        L.append(f"- {s}: {len(g)} pairs; " + ", ".join(f"{e} {n}" for e, n in g.groupby("entity").size().items()))
    L += [""] + [f"- {s}: {n}" for s, ns in notes.items() for n in ns]
    L += ["", "Full lists with top values: `keep_apart.csv` (set, entity, cluster a, cluster b, cos, count, top values).", ""]
    for s, g in ka.groupby("set", sort=False):
        L += [f"### {s}", "", md_table(g, ["entity", "cluster_a", "cluster_b", "cos", "count", "values_a", "values_b"]), ""]
    L += ["## Task 7: split back", "",
          "Rule: a group of A s012 with >= 2 clusters is split when two of its clusters are a keep-apart pair or their names form a role pair "
          "(row \"all names\": the names in the 3 orders and the vote; row \"vote names\": the vote names only, as the v3.8 code check reads them) (departure / destination, leave at / arrive by, location / address). Every cluster in "
          "a conflict seeds a column (biggest first; a seed joins an existing column only when it conflicts with none of its seeds, "
          "choosing the column of its most similar seed); other members go to the column of the most similar seed (bge-m3 centroid "
          "cosine). Each column is a new group with the vote name of its biggest named cluster; a repeated name gets the top value "
          "of the cluster in brackets so that the columns stay distinct.", ""]
    L += [f"- mentions of a split group from a cluster the group did not list: {sum(orphans.values())}", ""]
    for row in rows:
        L += [f"### {row}", ""]
        sp = splits[splits["row"] == row]
        L += [f"- {s}: {len(g)} groups split, into {sum(len(c.split(' | ')) for c in g['columns'])} columns" for s, g in sp.groupby("set", sort=False)]
        L += ["", md_table(sp, SB.SPLIT_COLS), "",
              "Fate of the v3.8 judged merges (undone = judged members now in >= 2 columns; fixed = no wrong merge left among them):", ""]
        for s, c in counts[row].items():
            L.append(f"- {s}: wrong merges {c['wrong']}, undone {c['wrong_undone']}/{c['wrong']}, fixed {c['wrong_fixed']}/{c['wrong']}; "
                     f"right merges {c['right']}, undone by mistake {c['right_undone']}/{c['right']}; wrong merges after (whole variant) "
                     f"{wrong_after[row][s]}")
        f = fate[fate["row"] == row]
        show = f[(~f["was_right"]) | f["undone"]]
        L += ["", "Per merge (every wrong merge, and every right merge that was undone):", "",
              md_table(show, ["set", "ent", "column", "was_right", "reason", "members", "groups_after", "undone", "wrong_after", "fixed"]), ""]
    L += ["### Dashboard", "", md_table(dash, ["set", "row", "found_train", "found_hotel", "found_restaurant", "found_total", "columns",
                                               "columns_per_found", "dup_columns", "wrong_columns", "extras_no_gt", "merges_right",
                                               "merges_judged", "review_edits", "guard", "guard_detail"]), ""]
    L += ["## Decision", "", "Rule (diary): adopt if wrong merges go down, at most 1 right merge is undone per set, and the recall guard passes.", ""]
    for row in rows:
        for s, (ok, lines) in decisions[row].items():
            L.append(f"- {row}, {s}: {'adopt' if ok else 'do not adopt'}: " + "; ".join(lines))
        both = all(ok for ok, _ in decisions[row].values())
        L.append(f"- **{row}: {'ADOPT' if both else 'DO NOT ADOPT'}** (both sets must pass).")
    L.append("")
    return "\n".join(L)


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rules = CE.rules_v11(2)
    root = {s: paths.ROOT / D.SETS[s]["run"] for s in D.SETS}
    chosen = json.loads((root["dev50"] / "spans" / "select" / "chosen.json").read_text(encoding="utf-8"))
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in GT.items()}
    ka_rows, exports, notes = {}, {}, {}
    for s in D.SETS:
        exports[s], ka_rows[s], notes[s] = keep_apart(s, root[s], chosen)
    ka = pd.DataFrame([r for s in D.SETS for r in ka_rows[s]], columns=SB.KA_COLS)
    write_csv(ka, a.out / "keep_apart.csv")

    pbs, splits, fate, wrong_after, orphans, dash = {}, [], [], {r: {} for r in VARIANTS}, {}, []
    for s in D.SETS:
        pbs[s] = DB.prepare(s, D.load_v22(a, s), gts[s])
        orders = list(D.SETS[s]["orders"])
        role_labels = {"all": (*orders, VOTE), "vote": (VOTE,)}
        for row, kind in VARIANTS.items():
            sp, fa, wrong_after[row][s], orph, wrong_ids = run_set(s, pbs[s], ka_rows[s], exports[s], orders, rules, row, role_labels[kind])
            splits += [{**r, "row": row} for r in sp]
            fate += [{**r, "row": row} for r in fa]
            orphans[(row, s)] = orph
        old = pd.read_csv(V38_WRONG / f"merges_wrong_{s}.csv")
        old = {(r["ent"], r["attr_id"]) for _, r in old[old["variant"] == VOTE].iterrows()}
        notes[s].append(f"step 0: wrong merges of A s012 rebuilt {len(wrong_ids)}, v3.8 list {len(old)}, same ids: "
                        f"{'yes' if old == wrong_ids else 'NO'}")
        dash.append(D.rows_for(pbs[s], [VOTE, *VARIANTS], ["A s012", *VARIANTS]))
    dash = pd.concat(dash, ignore_index=True)
    bad = D.check_step0(dash)
    if bad:
        raise SystemExit("STEP 0 FAILED: " + "; ".join(bad))
    splits = pd.DataFrame(splits, columns=["row", *SB.SPLIT_COLS])
    fate = pd.DataFrame(fate, columns=["row", *SB.FATE_COLS])
    counts = {row: SB.fate_counts(fate[fate["row"] == row]) for row in VARIANTS}
    decisions = {row: {s: SB.decide(counts[row][s], wrong_after[row][s],
                                    dash[(dash["set"] == s) & (dash["row"] == row)].iloc[0]["guard"] == "pass") for s in D.SETS}
                 for row in VARIANTS}
    write_csv(splits, a.out / "splits.csv")
    write_csv(fate, a.out / "merge_fate.csv")
    write_csv(dash, a.out / "dashboard.csv")
    text = report(ka, notes, splits, fate, counts, wrong_after, orphans, dash, decisions)
    write(a.out / "p2.md", text)
    print(text)


if __name__ == "__main__":
    main()
