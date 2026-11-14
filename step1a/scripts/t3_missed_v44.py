"""wf_v4.4 T3: the L2 attributes that Qwen found and Llama v4.3 missed (diary Nov 14), with the reason for each miss. No GPU, no LLM.

python scripts/t3_missed_v44.py [--llama results/wf_v43/u2] [--out results/wf_v44/t3]  -> missed.csv, missed.md

- Qwen side = the frozen Step 3 v3.9 final (results/loop1_v39, the 31/40 and 29/41 of the v4.3 report). Llama side = results/wf_v43/u2
  (names v4.3 + split + reconcile + duplicate check, the 30/40 and 27/41). Both are scored the same way: the final columns are built with
  final_v39.entity_columns, read as the variant "Final v3.9", and `rules_groups.found` (L2, rules v1.1: the scorer behind both numbers)
  says which GT attributes are found. A miss = found for Qwen, not found for Llama.
- The clusters of a miss = the Step 1a clusters of the Qwen column that found it (its best_group, part suffixes dropped). The weight of a
  cluster = the number of mentions of the attribute in it (rules_groups._mentions golds).
- Classification (`classify`, deterministic, first rule that holds; weights = share of the attribute's mentions in the clusters):
  1. not_attribute: clusters holding >= 50% of the weight got the voted action not_attribute (or unsure / attribute_cue).
  2. bad batch: clusters holding >= 50% of the weight sit in a names batch whose answer failed in at least one order (parse errors, cut
     off, or the cluster has no name in it).
  3. merged: Llama has a column with the attribute's clusters but with purity < 0.6 (the clusters were folded with those of other attributes).
     The reason also says whether the clashing names came from the same batch, and whether the three orders disagree.
  4. other: anything else (the attribute is spread over several columns, or a split part is too small); the reason names the split-pass
     status of the clusters (parse error or ran).
"""
import argparse
import contextlib
import csv
import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SETS = ("dev50", "dev50b")
ENTS = ("train", "hotel", "restaurant")
TYPES = ("not_attribute", "bad batch", "merged", "other")
SHARE = 0.5          # weight share of the clusters that decides rules 1 and 2
PURE = 0.6           # rules_groups.PURE: purity needed for a found attribute
MARKED = ("not_attribute", "unsure", "attribute_cue")   # pilot_verify.MARKED
FIELDS = ["set", "entity", "attribute", "type", "reason", "qwen_clusters", "batches", "llama_names", "llama_vote", "llama_best_group",
          "llama_purity", "llama_coverage", "llama_case", "llama_column_holds", "gt_clusters"]


# ---------------------------------------------------------------- the classifier (pure)
def classify(facts):
    """(type, reason) of one miss. facts = {"clusters": [{"cid", "weight", "vote": voted action, "split": split-pass status or "",
    "orders": [{"order", "batch", "name", "failed": bool, "mates": [cluster ids of the batch with the same name]}]}],
    "case", "purity", "holds": {attr: mentions} of Llama's best column}. Weights of 0 are counted as 1 (a cluster with no counted mention)."""
    cl = facts["clusters"]
    w = {c["cid"]: c["weight"] or 1 for c in cl}
    total = sum(w.values())
    share = lambda pick: sum(w[c["cid"]] for c in cl if pick(c)) / total  # noqa: E731
    na = share(lambda c: c["vote"] in MARKED)
    if na >= SHARE:
        return "not_attribute", f"{na:.0%} of its mentions are in clusters Llama voted not_attribute (names: {_names(cl)})"
    failed = share(lambda c: any(o["failed"] for o in c["orders"]))
    if failed >= SHARE:
        return "bad batch", f"{failed:.0%} of its mentions are in a names batch whose answer failed in at least one order"
    if facts["case"] == "mixed_only" or (facts["purity"] and facts["purity"] < PURE and facts["case"] != "spread"):
        same = sorted({m for c in cl for o in c["orders"] for m in o["mates"]})
        unstable = [c["cid"] for c in cl if len({o["name"] for o in c["orders"]}) > 1]
        holds = ", ".join(f"{a} {n}" for a, n in sorted(facts["holds"].items(), key=lambda kv: -kv[1])[:3])
        return "merged", (f"its clusters sit in a column of purity {facts['purity']:.2f} that holds {holds}; "
                          + (f"same batch and same name as {', '.join(same)}" if same else "the clashing names came from different batches")
                          + ("; orders disagree on " + ", ".join(unstable) if unstable else "; all orders agree"))
    splits = sorted({f"{c['cid']}: {c['split']}" for c in cl if c["split"]})
    return "other", (f"the attribute is spread over several columns (best part purity {facts['purity']:.2f}, coverage "
                     f"{facts.get('coverage', 0):.2f})" + (f"; split pass {'; '.join(splits)}" if splits else ""))


def _names(cl):
    return "; ".join(f"{c['cid']}: " + "/".join(o["name"] or "not_attribute" for o in c["orders"]) for c in cl)


def counts_by_type(rows, key=None):
    """{type: n} over rows, with every type present (key = a row field to group on first: {value: {type: n}})."""
    if key is None:
        c = Counter(r["type"] for r in rows)
        return {t: c.get(t, 0) for t in TYPES}
    return {v: counts_by_type([r for r in rows if r[key] == v]) for v in dict.fromkeys(r[key] for r in rows)}


# ---------------------------------------------------------------- scoring both sides
def final_found(set_name, bundle, tables, responses, rc_jobs, dup_jobs):
    """(prepared bundle with the variant "Final v3.9", {entity: rules_groups.found frame}) of one set (the scorer of the 31/40, 30/40 ...)."""
    import final_v39 as FV
    import score_t14_v37 as T
    from s1a import ceiling_v37 as CE
    from s1a import dashboard_v38 as DB
    from s1a import rules_groups as RG
    from s1a import score_v39_batch as SB
    from s1a import v34_data as VD
    rules = CE.rules_v11(2)
    pb = DB.prepare(set_name, bundle, VD.read_gt_levels(ROOT / T.GT[set_name] / "gt_levels.csv"))
    found = {}
    for ent in ENTS:
        b = FV.entity_columns(set_name, ent, tables[set_name][ent], responses, rc_jobs, dup_jobs)
        FV.add_variant(pb, ent, FV.FINAL, SB.final_names(b["acols"], b["kept_final"]))
        found[ent] = RG.found(pb["lev"][ent], FV.FINAL, rules, {})
    return pb, found


@contextlib.contextmanager
def _quiet():
    """The loaders print one line per response file; hide it."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def score_llama(out):
    """{set: (pb, found)} of a Llama run folder (step3_post_v43 layout)."""
    import score_v38 as SV
    from s1a import batch_v4 as B
    from s1a import step3_post_v43 as PP
    jobs = PP.manifest_all(out)
    rc = [j for j in jobs if j["family"] == "reconcile"]
    dup = {(j["set"], j["ent"], j["order_seed"]): j for j in jobs if j["family"] == "dupcheck_rc"}
    tables, res = B.read_json(Path(out) / "columns.json"), {}
    for s in SETS:
        with _quiet():
            _, bundle, _ = PP.load_bundle(out, s)
            res[s] = final_found(s, bundle, tables, SV.read_responses(Path(out)), rc, dup)
    return res


def score_qwen():
    """{set: (pb, found)} of the frozen Step 3 v3.9 run (results/loop1_v39/colab + the Qwen A answers of the v3.x folders)."""
    import final_v39 as FV
    import score_t14_v37 as T
    import score_v38 as SV
    from s1a import batch_v4 as B
    a = FV.parser().parse_args(["--dir33", "unused", "--mwoz", "unused"])    # --dir33 / --mwoz are required but not read on this path
    m1 = B.read_json(a.colab39 / "manifest.json")["jobs"]
    m2 = B.read_json(a.colab39 / "manifest_stage2.json")["jobs"]
    rc = [j for j in m1 if j["family"] == "reconcile"]
    dup = {(j["set"], j["ent"], j["order_seed"]): j for j in m2}
    tables, res = B.read_json(a.colab39 / "columns.json"), {}
    for s in SETS:
        run_dir, key = T.RUNS[(s, "v2.2")]
        with _quiet():
            _, bundle, _ = T.load_old(a, []) if key is None else T.load_new(a, Path(run_dir), key, [])
            res[s] = final_found(s, bundle, tables, SV.read_responses(a.colab39), rc, dup)
    return res


# ---------------------------------------------------------------- facts of one miss
def _cluster_ids(group):
    """Cluster ids of a group id: 'E1#0|E1#11/1' -> ['E1#0', 'E1#11'] (split part suffixes dropped)."""
    return sorted({g.split("/")[0] for g in group.split("|") if g})


def split_status(out, set_name, ent, cid):
    """Status of the split pass for a cluster: "" (no split job), "parse error", "ran (n parts)" / "ran (not mixed)"."""
    from s1a import batch_v4 as B
    from s1a import step3_post_v43 as PP
    p = Path(out) / "responses" / f"{ent}_{PP.RUN_KEY[set_name]}_split_{cid.replace('#', '-')}_r1.jsonl"
    last = B.last_row(p) if p.exists() else None
    if not last:
        return ""
    if last.get("errors"):
        return "parse error"
    parsed = last.get("parsed") or {}
    return f"ran ({len(parsed.get('parts') or [])} parts)" if parsed.get("is_mixed") else "ran (not mixed)"


def cluster_facts(out, set_name, ent, ed, cid, weight):
    """The facts of `classify` for one cluster of the Llama run folder `out`."""
    from s1a import batch_v4 as B
    from s1a import step3_v43 as S3
    names = [j for j in S3.names_jobs(out) if (j["set"], j["ent"]) == (set_name, ent)]
    orders = []
    for o in (0, 1, 2):
        dec = ed.variants[f"A s{o}"].dec.set_index("cluster_id")
        job = next(j for j in names if j["order"] == o and cid in j["cluster_ids"])
        last = B.last_row(Path(out) / "responses" / f"{job['job']}.jsonl")
        errs = S3.validate_names(last["raw"], job["cluster_ids"])[1] if last else ["no response"]
        row = dec.loc[cid]
        name = "" if row["action"] in MARKED else row["name"]
        orders.append({"order": o, "batch": job["batch"], "name": name or "not_attribute",
                       "failed": bool(errs) or bool(last and last["finish_reason"] == "length") or cid not in dec.index,
                       "mates": [x for x in job["cluster_ids"] if x != cid and name and dec.loc[x, "name"] == name]})
    vote = ed.variants["A s012"].dec.set_index("cluster_id").loc[cid]
    return {"cid": cid, "weight": weight, "vote": vote["action"], "orders": orders, "split": split_status(out, set_name, ent, cid) if vote["action"] == "split" else ""}


def miss_row(out, set_name, ent, attr, pb_l, found_l, found_q):
    """One output row for the miss (set, ent, attr): facts from both runs, then classify."""
    from s1a import ceiling_v37 as CE
    from s1a import rules_groups as RG
    import final_v39 as FV
    ed = pb_l["lev"][ent]
    q, lf = found_q.set_index("attr").loc[attr], found_l.set_index("attr").loc[attr]
    m = RG._mentions(ed, FV.FINAL, CE.rules_v11(2), {})
    mine = m[[attr in g for g in m["golds"]]]
    gt_clusters = Counter(mine["cluster_id"])
    q_clusters = _cluster_ids(q["best_group"])
    clusters = [cluster_facts(out, set_name, ent, ed, c, gt_clusters.get(c, 0)) for c in q_clusters]
    held = Counter(a for g in m[m["group"] == lf["best_group"]]["golds"] for a in set(g)) if lf["best_group"] else Counter()
    facts = {"clusters": clusters, "case": lf["case"], "purity": lf["purity"], "coverage": lf["coverage"], "holds": dict(held)}
    typ, reason = classify(facts)
    col_names = ed.variants[FV.FINAL].attrs.set_index("attr_id")["name"].to_dict()
    return {"set": set_name, "entity": ent, "attribute": attr, "type": typ, "reason": reason,
            "qwen_clusters": " ".join(f"{c['cid']}({c['weight']})" for c in clusters),
            "batches": "; ".join(c["cid"] + ": " + ", ".join(f"s{o['order']}b{o['batch']}" for o in c["orders"]) for c in clusters),
            "llama_names": "; ".join(c["cid"] + ": " + " / ".join(o["name"] for o in c["orders"]) for c in clusters),
            "llama_vote": "; ".join(f"{c['cid']}: {c['vote']}" for c in clusters),
            "llama_best_group": f"{lf['best_group']} ({col_names.get(lf['best_group'], '')})" if lf["best_group"] else "(none)",
            "llama_purity": round(float(lf["purity"]), 2), "llama_coverage": round(float(lf["coverage"]), 2), "llama_case": lf["case"],
            "llama_column_holds": ", ".join(f"{a} {n}" for a, n in sorted(held.items(), key=lambda kv: -kv[1])[:4]),
            "gt_clusters": " ".join(f"{c}({n})" for c, n in gt_clusters.most_common())}


def diff(scored_q, scored_l):
    """([(set, ent, attr)] found by Qwen, not by Llama), ([...] found by Llama, not by Qwen)."""
    miss, extra = [], []
    for s in SETS:
        for ent in ENTS:
            q, l = scored_q[s][1][ent].set_index("attr")["found"], scored_l[s][1][ent].set_index("attr")["found"]
            miss += [(s, ent, a) for a in q.index if q[a] and not l[a]]
            extra += [(s, ent, a) for a in q.index if l[a] and not q[a]]
    return miss, extra


# ---------------------------------------------------------------- output
def to_markdown(rows, extra, totals):
    """missed.md: counts per type (all sets, then per set), the table, and the attributes only Llama found."""
    def line(label, c):
        return f"| {label} | " + " | ".join(str(c[t]) for t in TYPES) + f" | {sum(c.values())} |"
    head = "| | " + " | ".join(TYPES) + " | all |\n|---|" + "---|" * (len(TYPES) + 1)
    per = counts_by_type(rows, "set")
    md = ["# T3: L2 attributes Qwen found and Llama v4.3 missed\n",
          f"Qwen = frozen Step 3 v3.9 (found {totals['qwen']}), Llama = v4.3 (`results/wf_v43/u2`, found {totals['llama']}); same scorer "
          "(`rules_groups.found`, L2, rules v1.1) on the final columns of both. Types come from `classify` in `scripts/t3_missed_v44.py` "
          "(deterministic; rules in its docstring). The clusters of a miss are those of the Qwen column that found it; "
          "(n) = mentions of the attribute in the cluster.\n",
          "## Counts per type\n", head, line("all", counts_by_type(rows)), *[line(s, c) for s, c in per.items()], "",
          "## Misses\n", "| set | entity | attribute | type | clusters | batches (order, batch) | Llama names (s0 / s1 / s2) | vote | Llama column | why |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['set']} | {r['entity']} | {r['attribute']} | **{r['type']}** | {r['qwen_clusters']} | {r['batches']} | {r['llama_names']} | "
                  f"{r['llama_vote']} | {r['llama_best_group']}, purity {r['llama_purity']}, coverage {r['llama_coverage']} | {r['reason']} |")
    md += ["", f"## Found by Llama but not by Qwen ({len(extra)})\n"] + [f"- {s} {e}: {a}" for s, e, a in extra]
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--llama", type=Path, default=ROOT / "results" / "wf_v43" / "u2")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v44" / "t3")
    a = ap.parse_args()
    sq, sl = score_qwen(), score_llama(a.llama)
    miss, extra = diff(sq, sl)
    rows = [miss_row(a.llama, s, e, attr, sl[s][0], sl[s][1][e], sq[s][1][e]) for s, e, attr in miss]
    totals = {k: " | ".join(f"{sum(int(sc[s][1][e]['found'].sum()) for e in ENTS)}/{sum(len(sc[s][1][e]) for e in ENTS)}" for s in SETS)
              for k, sc in (("qwen", sq), ("llama", sl))}
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "missed.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (a.out / "missed.md").write_text(to_markdown(rows, extra, totals), encoding="utf-8", newline="\n")
    print("T3:", len(rows), "misses", counts_by_type(rows), "| found", totals, "| Llama only", len(extra))


if __name__ == "__main__":
    main()
