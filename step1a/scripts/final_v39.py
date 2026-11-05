"""wf_v3.9 tasks 9 and 11: score the final Step 1a -> Step 3 setting once per set, and write the handover files. No GPU, no LLM.

python scripts/final_v39.py --dir33 ../../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--colab39 results/loop1_v39/colab] [--out results/loop1_v39/final] [--handover handover]
Final setting = A s012 (3-order vote) + split pass + reconcile joins both candidate orders agree on + duplicate-check joins that both
reconcile orders unite (same set of A s012 groups; applied on the agreed columns; role-pair block still applies) + the v3.8 checker as a
flag only (evidence cards, verdict rule v0). Writes <out>/{final.md, final_rows.csv, exit_bar.csv, exit_bar_<set>.md, dup_survival.csv,
final_columns.csv} and <handover>/<set>/<entity>.json (+ HANDOVER_FORMAT.md by hand).
"""

import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import batch_build_v38 as BB  # noqa: E402
import batch_build_v39 as BB9  # noqa: E402
import dashboard_v38 as D  # noqa: E402
import score_t14_v37 as T  # noqa: E402
import score_v38 as SV  # noqa: E402
import score_v39_batch as SBT  # noqa: E402
import score_v39_p1 as P1  # noqa: E402
from score_v35 import score_levels  # noqa: E402
from score_v36 import write, write_csv  # noqa: E402
from s1a import a_s012_v37 as AS  # noqa: E402
from s1a import batch_v38 as BT  # noqa: E402
from s1a import batch_v39 as B9  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import columns_v37 as CV  # noqa: E402
from s1a import dashboard_v38 as DB  # noqa: E402
from s1a import exit_v37 as EX  # noqa: E402
from s1a import handover_v39 as HV  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a import score_v38 as S  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import score_v39_batch as SB  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

BASE = D.VOTE
AGREED = "A s012 + reconcile (both orders)"
FINAL = "Final v3.9"
ENT_NAME = {"train": "train", "hotel": "hotel", "restaurant": "restaurant"}
ROLE_FILES = {"dev50": [("results/loop1_v31/responses", "{ent}_v2_r1"), ("results/loop1_v31/responses", "{ent}_v2_r2"),
                        ("results/loop1_v36/colab/responses", "{ent}_v2_s2")],
              "dev50b": [("results/loop1_v37/colab/responses", "{ent}_a_v22d50b_s%d" % i) for i in range(3)]}
ROW_EXTRA = ["role_columns", "role_pure", "role_share", "marks13_right", "marks13_n", "wrong_entity_dropped"]


def parser():
    ap = P1.parser()
    ap.set_defaults(out=Path("results/loop1_v39/final"))
    ap.add_argument("--colab39", type=Path, default=Path("results/loop1_v39/colab"))
    ap.add_argument("--handover", type=Path, default=Path("handover"))
    ap.add_argument("--keep-apart", type=Path, default=Path("results/loop1_v39/p2/keep_apart.csv"))
    return ap


# ---- small readers

def attribute_roles(set_name, ent):
    """{norm name: role} of the attributes the A orders declared (the first non-empty role, order 0 first)."""
    out = {}
    for root, stem in ROLE_FILES[set_name]:
        path = paths.ROOT / root / f"{stem.format(ent=ent)}.jsonl"
        for obj in (PV.load_objects(path) if path.exists() else [])[:1]:
            for a in obj.get("attributes") or []:
                if isinstance(a, dict) and a.get("role"):
                    out.setdefault(PV.norm_name(a.get("name")), a["role"])
    return out


def add_variant(pb, ent, label, rename):
    """Variant `label` = A s012 whose groups in `rename` {attr id: column name} get that name; a group whose name already is the
    column name (same norm name) keeps its own spelling, so its name rating still applies."""
    vo = pb["lev"][ent].variants[BASE]
    have = dict(zip(vo.attrs["attr_id"], vo.attrs["name"]))
    rename = {g: n for g, n in rename.items() if PV.norm_name(have.get(g)) != PV.norm_name(n)}
    SV.add_variant(pb, ent, label, replace(vo, attrs=S.renamed_attrs(vo.attrs, rename)))


# ---- the final columns of one entity

def entity_columns(set_name, ent, t, responses, rc_jobs, dup_jobs):
    """dict with everything the final setting builds for one entity: choices per order, agreed columns, the dupcheck joins per
    order (cleaned, after the code check) and the surviving ones, final columns."""
    cols, parts = t["columns"], t["parts"]
    choice, new, kept, n_joins = {}, {}, {}, {}
    for o in (0, 1):
        jobs = [j for j in rc_jobs if (j["set"], j["ent"], j["order_seed"]) == (set_name, ent, o)]
        choice[o] = SB.choices_of(jobs, {j["job"]: responses.get(j["job"]) for j in jobs})
        new[o], _ = B9.apply_reconcile(cols, parts, choice[o])
        joins, _ = SB.clean_joins(responses[dup_jobs[(set_name, ent, o)]["job"]]["parsed"].get("joins", []))
        kept[o], _ = BT.check_joins(joins, {c["cid"]: c for c in new[o]})
        n_joins[o] = (len(joins), len(kept[o]))
    agreed = SB.intersect(choice[0], choice[1])
    acols, areport = B9.apply_reconcile(cols, parts, agreed)
    sets = [HV.group_sets(new[o], kept[o]) for o in (0, 1)]
    both = HV.both_orders(*sets)
    joins_final = HV.joins_on_columns(acols, both)
    kept_final, rejected_final = BT.check_joins(joins_final, {c["cid"]: c for c in acols})
    return {"choice": choice, "agreed": agreed, "acols": acols, "areport": areport, "n_joins": n_joins, "sets": sets, "both": both,
            "joins_final": joins_final, "kept_final": kept_final, "rejected_final": rejected_final,
            "final": HV.merge_joined_columns(acols, kept_final)}


# ---- exit bar

def exit_tables(a, set_name, pb, shared, bundle_labels, gt, rated, extra):
    """(table DataFrame, runs dict, md text, right names {label: n}) of the exit bar (a)-(e) for A's orders, A s012 and the final."""
    lev, raw = pb["lev"], pb["raw"]
    rules = CE.rules_v11(2)
    ceil = CE.ceiling_table(lev, 2, rules)
    labels = bundle_labels
    noise = NV.noise_l2_rows(raw, {"gt_levels": gt}, labels)
    dup = pd.concat([CV.dup_rows(ed, l, rules, {}) for l in labels for ed in lev.values()], ignore_index=True)
    runs = {}
    for v in labels:
        found = set().union(*(EX.found_set(ed, v, rules, {}) for ed in lev.values()))
        nz = noise[noise["variant"] == v][["noise_n", "noise_marked", "marked_n", "marked_noise"]].sum()
        runs[v] = EX.run_metrics(found, ceil, nz, CV.dup_summary(dup[dup["variant"] == v])["mean"])
    orders = [v for v in labels if v not in (BASE, FINAL)]
    groups = {f"A, {len(orders)} orders ({' / '.join(orders)})": orders, "A s012 (vote)": [BASE], FINAL: [FINAL]}
    table = EX.bar_rows(runs, groups)
    sc = score_levels(T.SETTING, (2,), T.only(raw, [BASE, FINAL]), shared, extra)
    right = {v: int(sc.loc[sc["variant"] == v, "name_right"].sum()) for v in (BASE, FINAL)}
    bl = T.baseline_right(paths.ROOT / "results/loop1_v37", set_name)
    e = {}
    for name, v in (("A s012 (vote)", BASE), (FINAL, FINAL)):
        verdict = EX.exit_e(right[v], bl)
        e[name] = "pending the baseline" if verdict is None else f"{'pass' if verdict else 'FAIL'}: right names {right[v]} vs baseline union {bl}"
    e[next(k for k in groups if k.startswith("A, "))] = "n/a (orders not scored here)"
    md = EX.exit_md(table, runs, [
        "(e): right names = names L2 rated, summed over the entities (score_levels, as scripts/score_t14_v37.py). Final v3.9: a group "
        "renamed by a join has a name+description that was never rated and counts as not right (unrated = not right), so its right-names "
        "count is a lower bound (only groups whose name changed lose their rating); the right names of A s012 are the exact ones.",
        "(d) uses the v1.1 / v1.2 marks (noise_v36.noise_l2_rows, as every earlier exit bar); the v1.3 marks are in final.md.",
        "(b): A's three orders range over the orders; the vote and the final are one result each, so (b) is n/a for them."],
        e=e, title=f"wf_v3.9 exit bar, final setting on {set_name} (L2, rules v1.1; guard RULES_V1_2.md)")
    return table, runs, md, right, bl


# ---- handover

def handover_doc(set_name, ent, ed, pb, si, t, built, evid, pairs, roles, split_role, entity_id):
    """The handover document of one entity (HANDOVER_FORMAT.md)."""
    cols, final = t["columns"], built["final"]
    sup, src, neigh = evid
    owner = {key: c["cid"] for c in cols for key, _ in c["pools"]}
    by_pre = {c["cid"]: c for c in cols}
    names = {c["cid"]: c["name"] for c in cols}
    vo = ed.variants[BASE]
    attrs = vo.attrs.set_index("attr_id")
    dec = vo.dec.set_index("cluster_id")
    m = ed.mentions.set_index("mention_id")
    contrib = {}
    for f in final:
        cnt = Counter()
        for key, items in f["pools"]:
            cnt[owner[key]] += len(items)
        contrib[f["cid"]] = [c for c, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))]
    cent = BT.centroids(final, si.export.ids, si.export.x)
    near = {f["cid"]: BT.nearest(cent, f["cid"]) for f in final if f["cid"] in cent}
    moved = {r["pid"] for r in built["areport"] if r["status"] == "joined"}
    aname = {c["cid"]: c["name"] for c in built["acols"]}
    records = []
    for f in final:
        members_pre = contrib[f["cid"]]
        exact = (len(members_pre) == 1 and {k for k, _ in by_pre[members_pre[0]]["pools"]} == {k for k, _ in f["pools"]})
        if exact:
            nb = [[n] for n in neigh.get((set_name, ent, members_pre[0]), [])]
        else:
            nb = [contrib[n] for n in near.get(f["cid"], [])]
        card = HV.evidence_card(members_pre, names,
                                {c: v for (s, e, c), v in sup.items() if (s, e) == (set_name, ent)},
                                {c: v for (s, e, c), v in src.items() if (s, e) == (set_name, ent)}, nb)
        members = []
        for key, items in f["pools"]:
            cl, g = key.split("@")
            members.append({"cluster": cl, "group": g, "part": g if "/" in g else None, "mentions": len(items)})
        clusters = sorted({x["cluster"] for x in members})
        texts = [m.loc[i, "text"] for i in f["mention_ids"]]
        vt = HV.value_type_counts(texts)
        top = max(vt.items(), key=lambda kv: (kv[1], kv[0]))[0] if vt else ""
        part_roles = [split_role.get((x["cluster"], str(attrs.loc[x["group"], "name"])), "") for x in members if x["part"]]
        desc = f["description"] or next((r for r in part_roles if r), "")
        role = roles.get(PV.norm_name(f["name"])) or next((r for r in part_roles if r), "")
        placements = Counter(str(dec.loc[x["cluster"], "placement"]) for x in members if x["cluster"] in dec.index)
        origin = {"groups": f["groups"], "from_columns": [names[c] for c in members_pre],
                  "reconcile_parts_moved_in": sorted(g for g in f["groups"] if "/" in g and g in moved),
                  "duplicate_check_joined": [aname[c] for c in f["old_cids"]] if len(f["old_cids"]) > 1 else []}
        records.append(HV.column_record(
            f["cid"], f["name"], desc, role, {"dominant": top, "share": round(vt[top] / sum(vt.values()), 3) if vt else 0.0,
                                               "counts": dict(vt)},
            members, [int(i) for i in f["mention_ids"]], f["n_dialogues"], f["top_values"],
            placements.most_common(1)[0][0] if placements else "", card, not exact, [names[c] for c in members_pre],
            HV.keep_apart_flags(clusters, pairs), origin))
    marked = vo.dec[vo.dec["action"].isin(PV.MARKED)]
    pm = ed.mentions
    dropped = [HV.dropped_record(r["cluster_id"], r["action"], r["name"], r["evidence"], str(r["placement"]),
                                 [int(i) for i in pm.loc[pm["cluster_id"] == r["cluster_id"], "mention_id"]])
               for _, r in marked.iterrows()]
    return {"set": set_name, "entity": ent, "stage1_entity": entity_id, "setting": "A s012 + split pass + reconcile (both orders) + "
            "duplicate check (both orders) + checker flag", "clusters": list(ed.cids), "columns": records, "dropped": dropped,
            "counts": {"columns": len(records), "mentions_in_columns": sum(r["n_mentions"] for r in records),
                       "dropped_clusters": len(dropped), "dropped_mentions": sum(d["n_mentions"] for d in dropped)}}


def md_table(df, cols):
    f = lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else (f"{v:.3f}" if isinstance(v, float) else str(v))  # noqa: E731
    return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f(r[c]) for c in cols) + " |" for _, r in df.iterrows()]


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    m1 = json.loads((a.colab39 / "manifest.json").read_text(encoding="utf-8"))["jobs"]
    m2 = json.loads((a.colab39 / "manifest_stage2.json").read_text(encoding="utf-8"))["jobs"]
    tables = json.loads((a.colab39 / "columns.json").read_text(encoding="utf-8"))
    responses = SV.read_responses(a.colab39)
    rc_jobs = [j for j in m1 if j["family"] == "reconcile"]
    dup_jobs = {(j["set"], j["ent"], j["order_seed"]): j for j in m2}
    manifest38 = json.loads((a.colab38 / "manifest.json").read_text(encoding="utf-8"))
    examples38 = pd.read_csv(a.colab38 / "examples.csv")
    responses38 = SV.read_responses(a.colab38)
    evid = SV.evidence_tables(manifest38, examples38, responses38)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in T.GT.items()}
    rated = AS.read_l2_rated(a.names36, a.ratings)
    pairs_all = pd.read_csv(a.keep_apart)
    rows, surv, exit_tabs, exit_md_all, colrows, notes = [], [], [], [], [], []
    for set_name in D.SETS:
        run_dir, key = T.RUNS[(set_name, "v2.2")]
        shared, bundle, _ = T.load_old(a, []) if key is None else T.load_new(a, Path(run_dir), key, [])
        pb = DB.prepare(set_name, bundle, gts[set_name])
        si = BB.SetInput(set_name)
        per_ent = BB.columns_of(pb)
        built = {}
        for ent in DB.ENTS:
            t = tables[set_name][ent]
            if [(c["cid"], c["name"], c["n_mentions"]) for c in per_ent[ent][1]] != [(c["cid"], c["name"], c["n_mentions"]) for c in t["columns"]]:
                raise SystemExit(f"STOP: {set_name} {ent}: rebuilt columns differ from columns.json")
            built[ent] = entity_columns(set_name, ent, t, responses, rc_jobs, dup_jobs)
            ac, fin = built[ent]["acols"], built[ent]["final"]
            add_variant(pb, ent, AGREED, SB.final_names(ac))
            add_variant(pb, ent, FINAL, SB.final_names(ac, built[ent]["kept_final"]))
            if CV.n_columns(pb["lev"][ent], FINAL) != len(fin):
                raise SystemExit(f"STOP: {set_name} {ent}: final variant has {CV.n_columns(pb['lev'][ent], FINAL)} columns, table {len(fin)}")
        labels_agreed = SV.gt_info(pb, AGREED)
        for ent in DB.ENTS:
            b = built[ent]
            jrows, _ = SV.score_joins(set_name, "final", ent, pb["lev"][ent], b["acols"], b["joins_final"], labels_agreed[ent])
            jc = Counter((r["code check"], r["GT status"]) for r in jrows)
            surv.append({"set": set_name, "ent": ent, "rc0 joins": b["n_joins"][0][0], "rc0 after code check": b["n_joins"][0][1],
                         "rc1 joins": b["n_joins"][1][0], "rc1 after code check": b["n_joins"][1][1],
                         "same groups in both": len(b["both"]), "on agreed columns": len(b["joins_final"]), "role-pair blocked": len(b["rejected_final"]),
                         "kept": len(b["kept_final"]), **{f"kept {k}": jc[("accepted", k)] for k in S.JOIN_STATUS}})
        # rows
        labels = [BASE, FINAL]
        dash = D.rows_for(pb, labels, labels)
        base_inputs = P1.noise_inputs(pb["raw"], pb["gt"], BASE)
        for _, r in dash.iterrows():
            rc = P1.role_column_rows(pb, r["row"], r["row"], set_name)
            summ = P1.summary_row(set_name, r["row"], rc, "n/a")
            mk = SBT.marks_of(base_inputs, pb["raw"], BASE)
            rows.append({**r.to_dict(), "role_columns": summ["role_columns"], "role_pure": summ["role_pure"], "role_share": summ["share"],
                         "marks13_right": mk["marks_right"], "marks13_n": mk["marks_n"], "wrong_entity_dropped": mk["wrong_entity_dropped"]})
        # exit bar
        extra = SR.load_extra(a.gt, a.dir32)
        extra["gt_levels"], extra["names_l2"] = gts[set_name], rated
        orders = list(D.SETS[set_name]["orders"])
        table, runs, md, right, bl = exit_tables(a, set_name, pb, shared, [*orders, BASE, FINAL], gts[set_name], rated, extra)
        table.insert(0, "set", set_name)
        exit_tabs.append(table)
        exit_md_all.append((set_name, md, right, bl))
        write(a.out / f"exit_bar_{set_name}.md", md)
        # handover
        for ent in DB.ENTS:
            ed = pb["lev"][ent]
            entity_id = tables[set_name][ent]["entity"]
            pairs = pairs_all[(pairs_all["set"] == set_name) & (pairs_all["entity"] == entity_id)].to_dict("records")
            doc = handover_doc(set_name, ent, ed, pb, si, tables[set_name][ent], built[ent], evid, pairs, attribute_roles(set_name, ent),
                               BB9.split_roles(set_name, ent), entity_id)
            bad = HV.check_handover(doc)
            if bad:
                raise SystemExit(f"STOP: {set_name} {ent} handover: {bad[:5]}")
            out = a.handover / set_name
            out.mkdir(parents=True, exist_ok=True)
            write(out / f"{ent}.json", json.dumps(doc, indent=1, ensure_ascii=False))
            colrows += [{"set": set_name, "ent": ent, "id": c["id"], "name": c["name"], "mentions": c["n_mentions"], "verdict": c["verdict"],
                         "pooled": c["evidence"]["pooled"], "support": c["evidence"]["support"] and c["evidence"]["support"]["share"],
                         "keep_apart_pairs": len(c["flags"]["keep_apart"]), "from_columns": " | ".join(c["evidence"]["from_columns"])}
                        for c in doc["columns"]]
    df = pd.DataFrame(rows)
    sv = pd.DataFrame(surv)
    et = pd.concat(exit_tabs, ignore_index=True)
    write_csv(df, a.out / "final_rows.csv")
    write_csv(sv, a.out / "dup_survival.csv")
    write_csv(et, a.out / "exit_bar.csv")
    write_csv(pd.DataFrame(colrows), a.out / "final_columns.csv")
    tot = sv.groupby("set")[[c for c in sv.columns if c not in ("set", "ent")]].sum().reset_index()
    show = ["set", "row", "found_total", "gold_total", "columns", "columns_per_found", "dup_columns", "wrong_columns", "extras_no_gt",
            "review_edits", "guard", "guard_detail", "role_pure", "role_columns", "marks13_right", "marks13_n", "wrong_entity_dropped"]
    L = ["# wf_v3.9 final setting scored once per set (L2, rules v1.3 over v1.2, Step 1a v2.2)", "",
         "Final setting = A s012 (3-order vote) + split pass + reconcile joins both candidate orders agree on + duplicate-check joins "
         "both reconcile orders unite (same set of A s012 groups; applied on the agreed columns; role-pair block applies) + the v3.8 "
         "checker as a flag only (no column is removed). Decisions, found and noise marks are those of A s012; only the columns change.", "",
         "## Rows", ""] + md_table(df, show) + ["", "## Duplicate-check joins that survive the both-orders rule", "",
         "A join is kept when both reconcile orders' duplicate checks (after cleaning and the code check on their own columns) unite exactly "
         "the same set of A s012 groups. It is then applied on the agreed-reconcile columns (every column holding one of its groups is "
         "joined), checked for role pairs, and judged by the GT as in v3.8 (right = same L2 attribute and role).", ""]
    L += md_table(tot, ["set", "rc0 joins", "rc0 after code check", "rc1 joins", "rc1 after code check", "same groups in both",
                        "on agreed columns", "role-pair blocked", "kept", "kept right", "kept wrong", "kept no_gt"]) + ["", "Per entity: `dup_survival.csv`.", "",
         "## Exit bar (RULES_V1_1.md, a)-(e)", ""]
    for set_name, md, right, bl in exit_md_all:
        L += [f"### {set_name}", "", *md.split("\n")[2:], ""]
    write(a.out / "final.md", "\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
