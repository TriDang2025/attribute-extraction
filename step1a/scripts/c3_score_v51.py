"""wf_v5.1 C3 (+ C4 clash list, + C1 count): score the REAL R5 Step 3 on the laptop. CPU only, no LLM, no GPU.

python scripts/c3_score_v51.py [--skip-build]  -> results/wf_v51/c3/{c3.md, summary.csv, role_table.csv, trace_<set>.csv, trace_table.csv,
    clash_<set>.csv, clash_summary.csv, r4_tokens.csv, step3_calls.csv, c1_replay_count.csv, figure_example.md, figure_example.png}
Input: results/wf_v51/r5/<set>/step3 (Llama-3.1-8B, guided, R3 + R4 on; written by Colab, read only here). Found L2 does not depend on the column
names (v5.0 report), so the real Step 3 is scored without the rename stage:
 1. context split big40 (gpu_v51.ctx_split, `out` = c3) on the Step 3 final columns; the parts keep their column names (NO LLM rename),
    then the loop-1 run folder, the frozen loop-2 CPU replay and the Step 4 input exactly as gpu_v51.loop2_stage, written to c3/ (not to r5/).
    Encoder: gpu_v50.CachedEnc on r5/<set>/vectors.npz, the laptop bge-m3 for a text without a vector (counted).
 2. found L2 (human check as v5.0, scripts/r0_taxi_v51.found_l2) with the taxi rule off and on, columns, wrong columns, loop-1-only found.
 3. role table, 4. G2 trace of the misses left (taxi rule on), 5. clash list + R4 tokens + call counts, 6. figure data, 7. C1 replay count.
Not done here: rename of the split parts, column clash question, Step 4 (these need the GPU).
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import g2_trace_v50 as G2  # noqa: E402
import g3_nojoin_v50 as G3  # noqa: E402
import gpu_v50 as G50  # noqa: E402
import gpu_v51 as G51  # noqa: E402
import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v49 as M49  # noqa: E402
import r0_taxi_v51 as R0  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import ctxvec_v51 as CV  # noqa: E402
from s1a import log_v43 as L43  # noqa: E402
from s1a import log_v44 as L44  # noqa: E402
from s1a import mainclaim_v41 as MC  # noqa: E402
from s1a import rolenames_v51 as RN  # noqa: E402

OUT = ROOT / "results" / "wf_v51" / "c3"
R5, SETS = G51.R5, G51.SETS            # {"dev50": run, "dev50b": run}
V50_STEP3 = ROOT / "results" / "wf_v46" / "y3"
R1_CLUSTERS = ROOT / "results" / "wf_v51" / "r1"
ROLE_PAIRS = (("Train leave at", "Train arrive by"), ("Train departure", "Train destination"), ("Taxi leave at", "Taxi arrive by"),
              ("Taxi departure", "Taxi destination"), ("Hotel address", "Restaurant address"))
EST_CALLS = {"dev50": 550, "dev50b": 475}      # the brief's estimate of the real Step 3 calls (r34.md: 599 | 516 incl. assembled rows)
R1_SELECTED = {0.3: 0.25, 0.5: 0.2, 0.7: 0.2}  # alpha -> t chosen on dev50 (r1.md)
FIG_PAIR = ("Train leave at", "Train arrive by")


def read_final(path, dev):
    return B.read_json(path)[SETS[dev]]


def variants(dev):
    """{name: final columns} scored in the summary: v4.9 cached, v5.0 (context split), the real R5 Step 3 before and after the context split."""
    return {"v4.9 cached": G3.load(dev)[3], "v5.0": R0.final_v50(dev),
            "v5.1 Step 3 (no split)": read_final(R5 / dev / "step3" / "scores" / "final_columns.json", dev),
            "v5.1 Step 3 + split": read_final(OUT / dev / "ctxsplit" / "final_columns.json", dev)}


# ---------------------------------------------------------------- 1. build (context split, run folder, loop-2 replay)
def build(enc_fallback=None):
    """Steps 1 of the module doc. Returns {"fallback_texts": n, "texts_total": n} of the encoder."""
    enc = G50.CachedEnc(R5, "vectors.npz", fallback=enc_fallback)
    for dev, run in SETS.items():
        G51.ctx_split(dev, run, enc, root=R5, out=OUT)
        G50.build_run_dir(dev, run, read_final(OUT / dev / "ctxsplit" / "final_columns.json", dev), OUT / "rename")
    G51.loop2_stage(enc, root=OUT)           # identity rename: the run folder holds the Step 3 names of the parts, nothing is asked
    return {"fallback_texts": enc.fallback_texts, "texts_with_vector": len(enc.vec) - enc.fallback_texts}


# ---------------------------------------------------------------- 2. scores
def score(final, dev, taxi, work):
    """{found (set), loop1 (set), kinds, cols, wrong} of one final columns, taxi rule on / off (found L2 as v5.0, found_l2 detail)."""
    found, f1, rows = R0.found_l2(final, dev, taxi, work, detail=True)
    k = Counter(r["kind"] for r in rows)
    return {"found": found, "loop1": f1, "cols": len(rows), "gold": k["gold"], "dup": k["dup"], "other": k["other"], "wrong": k["dup"] + k["other"]}


def summary_rows(work):
    """([summary rows], {(dev, variant, taxi): score}) over the variants, both sets, taxi rule off / on."""
    rows, res = [], {}
    for dev in SETS:
        n = {taxi: sum(len(v) for v in R0.gold_lists(dev, taxi).values()) for taxi in (False, True)}
        for name, final in variants(dev).items():
            for taxi in (False, True):
                res[(dev, name, taxi)] = score(final, dev, taxi, work)
        for (d, name, taxi), s in res.items():
            if d != dev:
                continue
            b = res[(dev, "v4.9 cached", taxi)]
            rows.append({"set": dev, "variant": name, "taxi_rule": "on" if taxi else "off", "gold_n": n[taxi], "found_L2": len(s["found"]),
                         "found_loop1_only": len(s["loop1"]), "cols": s["cols"], "cols_gold": s["gold"], "cols_dup": s["dup"], "cols_other": s["other"],
                         "wrong_cols": s["wrong"], "new_wrong_cols_vs_v49": s["wrong"] - b["wrong"],
                         "gained_vs_v50": "; ".join(sorted(s["found"] - res[(dev, "v5.0", taxi)]["found"])),
                         "lost_vs_v50": "; ".join(sorted(res[(dev, "v5.0", taxi)]["found"] - s["found"]))})
    return rows, res


def role_rows(res):
    """Role table rows: per set and role pair, found yes / no of each attribute v5.0 -> v5.1 (taxi rule on); an attribute that is not in the
    set's gold list is "n/a" and the pair is not counted."""
    rows = []
    for dev in SETS:
        gold = {a for v in R0.gold_lists(dev, True).values() for a in v}
        old, new = res[(dev, "v5.0", True)]["found"], res[(dev, "v5.1 Step 3 + split", True)]["found"]
        for a1, a2 in ROLE_PAIRS:
            r = {"set": dev, "pair": f"{a1} / {a2}"}
            for i, a in enumerate((a1, a2), 1):
                r[f"attribute {i} (v5.0 -> v5.1)"] = "n/a" if a not in gold else f"{a}: {'yes' if a in old else 'no'} -> {'yes' if a in new else 'no'}"
            ok = {a1, a2} <= gold
            r["both found v5.0"] = ("yes" if {a1, a2} <= old else "no") if ok else "n/a"
            r["both found v5.1"] = ("yes" if {a1, a2} <= new else "no") if ok else "n/a"
            rows.append(r)
    return rows


# ---------------------------------------------------------------- 4. trace
def trace_tables(res):
    """{set: G2 trace DataFrame} of the misses left on the new outputs (taxi rule on), + the stop-point table."""
    cfg = json.loads(MC.NAME_MATCH.read_text(encoding="utf-8"))
    tabs = {}
    for dev in SETS:
        data = G2.load(dev, step3=R5 / dev / "step3")
        data = (*data[:4], read_final(OUT / dev / "ctxsplit" / "final_columns.json", dev), data[5])
        with R0.rule(True):
            gold = M49.found_v49(dev)[1]
        tabs[dev] = G2.trace_set(dev, cfg, data, ({"loop2": res[(dev, "v5.1 Step 3 + split", True)]["found"]}, gold))
    return tabs, G2.stop_table(tabs)


# ---------------------------------------------------------------- 5. clash list, tokens, calls
def top_label(ids, labels):
    c = Counter(a for i in ids for a in labels.get(i, []))
    return (c.most_common(1)[0][0], round(c.most_common(1)[0][1] / len(ids), 2)) if c else ("", 0.0)


def clash_rows(dev):
    """[one row per R3 clash question of the real run]: names before / after, answer, orders, role pair touched (gold only to describe)."""
    step3 = R5 / dev / "step3"
    jobs = B.read_json(step3 / "manifest_clash.json")["jobs"]
    mt, labels = G3.load(dev)[:2]
    log = L43.RepairLog()
    answers = RN.read_answers(step3, jobs, log)
    pair_of = {a: p for p in ROLE_PAIRS for a in p}
    rows = []
    for j in jobs:
        a, b = j["cluster_ids"]
        la, lb = (top_label(list(mt.index[mt["cluster_id"] == c]), labels) for c in (a, b))
        ans = answers[j["job"]]
        touched = pair_of[la[0]] if la[0] in pair_of and pair_of.get(lb[0]) == pair_of[la[0]] and la[0] != lb[0] else None
        rows.append({"set": dev, "entity": j["ent"], "name_before": j["name"], "cluster_a": a, "cluster_b": b,
                     "mentions_a": int((mt["cluster_id"] == a).sum()), "mentions_b": int((mt["cluster_id"] == b).sum()),
                     "orders": ",".join(map(str, j["orders"])),
                     "answer": "fallback" if ans is None else ans["answer"],
                     "name_a_after": "" if ans is None else ans["names"][a], "name_b_after": "" if ans is None else ans["names"][b],
                     "gold_a": f"{la[0]} ({la[1]})", "gold_b": f"{lb[0]} ({lb[1]})",
                     "role_pair_touched": " / ".join(touched) if touched else ""})
    return rows


def clash_summary(rows_by_set):
    out = []
    for dev, rows in rows_by_set.items():
        jobs = B.read_json(R5 / dev / "step3" / "manifest_clash.json")["jobs"]
        log = B.read_json(R5 / dev / "step3" / "clash_log.json")
        per_order = Counter(o for j in jobs for o in j["orders"])
        ans = Counter(r["answer"] for r in rows)
        out.append({"set": dev, "questions": len(rows), "same": ans["same"], "different": ans["different"], "fallback": ans["fallback"],
                    "name_taken": log["counts"].get("clash_name_taken", 0), "blocked_same": log["counts"].get("clash_blocked_same", 0),
                    "pairs_order0": per_order[0], "pairs_order1": per_order[1], "pairs_order2": per_order[2],
                    "role_pair_questions": sum(bool(r["role_pair_touched"]) for r in rows),
                    "role_pair_different": sum(bool(r["role_pair_touched"]) and r["answer"] == "different" for r in rows)})
    return out


def names_tokens(folder):
    rows = [r for r in L44.call_rows(folder) if "_names_" in r["job"]]
    return len(rows), sum(r["prompt_tokens"] for r in rows), sum(r["output_tokens"] for r in rows)


def r4_rows():
    out = []
    for dev in SETS:
        (n0, p0, o0), (n1, p1, o1) = names_tokens(V50_STEP3 / dev / "step3"), names_tokens(R5 / dev / "step3")
        out.append({"set": dev, "names_calls_v50": n0, "names_calls_v51": n1, "prompt_tokens_v50": p0, "prompt_tokens_v51": p1,
                    "per_call_v50": round(p0 / n0, 1), "per_call_v51": round(p1 / n1, 1), "increase_pct": round(100 * (p1 / n1) / (p0 / n0) - 100, 1),
                    "r34_estimate_increase_pct": {"dev50": 12.1, "dev50b": 11.9}[dev]})
    return out


def family(job):
    return next((k.strip("_") for k in ("_clashq_", "_mergeq_", "_names_", "_rescuen_", "_rescueq_", "_splitk_", "_split_", "_a_") if k in job), "reconcile/dupcheck")


def call_rows(root, tag):
    """Calls and tokens per family from the cached rows (rows without tokens = assembled by code, not calls: left out of `calls`)."""
    out = []
    for dev in SETS:
        df = pd.DataFrame(L44.call_rows(Path(root) / dev / "step3"))
        df["family"] = df["job"].map(family)
        for fam, g in df.groupby("family"):
            real = g[g["prompt_tokens"].notna()]
            out.append({"run": tag, "set": dev, "family": fam, "rows": len(g), "calls": len(real), "prompt_tokens": int(real["prompt_tokens"].sum()),
                        "output_tokens": int(real["output_tokens"].sum()), "unguided_rows": int((real["guided"] != True).sum())})  # noqa: E712
    return out


# ---------------------------------------------------------------- 6. figure data
def figure_data(dev, source):
    """The most mixed column of the two roles FIG_PAIR in the v5.0 Step 3 (cached v4.9 columns, before the context split) and the columns of the
    same entity in v5.1 (Step 3 + split) that hold these roles, 2 snippets each; "also" = the columns of the same entity in v5.0 final and in
    v5.1 Step 3 before the split. None when v5.0 Step 3 has no mixed column for the pair in this set."""
    mt, labels, emap, cached, _s3 = G3.load(dev)
    a1, a2 = FIG_PAIR
    vs = variants(dev)

    def cols(final, entity=None):
        out = []
        for key, cs in final.items():
            for c in cs:
                ids = [int(i) for i in c["mention_ids"]]
                n1, n2 = (sum(a in labels.get(i, []) for i in ids) for a in FIG_PAIR)
                if n1 + n2 and entity in (None, key):
                    out.append({"entity": key, "cid": c["cid"], "name": c["name"], "n": len(ids), "n1": n1, "n2": n2, "ids": ids})
        return out

    old = [c for c in cols(cached) if min(c["n1"], c["n2"]) >= 0.25 * c["n"] and min(c["n1"], c["n2"]) >= 5]
    if not old:
        return None
    old = max(old, key=lambda c: c["n"])
    top = lambda cs: sorted((c for c in cs if c["n1"] + c["n2"] >= 5), key=lambda c: -(c["n1"] + c["n2"]))   # noqa: E731

    def snip(ids, k):
        return RN.column_snippets(dev, {"x": ids}, None, source=source)["x"][:k]

    mix = [i for i in old["ids"] if a1 in labels.get(i, [])], [i for i in old["ids"] if a2 in labels.get(i, [])]
    also = {v: [f"{c['name']} #{c['cid']} ({c['n']}: {c['n1']} {a1} / {c['n2']} {a2})" for c in top(cols(vs[v], old["entity"]))]
            for v in ("v5.0", "v5.1 Step 3 (no split)", "v5.1 Step 3 + split")}
    return {"set": dev, "old": {**old, "snippets": [(a, snip(m, 1)[0]) for a, m in zip(FIG_PAIR, mix) if m]}, "also": also,
            "new": [{**c, "snippets": snip(c["ids"], 2)} for c in top(cols(vs["v5.1 Step 3 + split"], old["entity"]))[:2]]}


def write_figure(fig):
    a1, a2 = FIG_PAIR
    o = fig["old"]
    lines = ["# wf_v5.1 C3 figure: one train time cluster, v5.0 vs v5.1 (real Step 3 + context split, no rename)", "",
             f"Set {fig['set']}, entity {o['entity']}. Roles from the gold, used only to describe. Snippets: the value is in [ ].", "",
             f"## v5.0 Step 3 (before the context split): column \"{o['name']}\" (#{o['cid']}, {o['n']} mentions): {o['n1']} {a1} + {o['n2']} {a2} (two roles mixed)", ""]
    lines += [f"- as {a}: `{s}`" for a, s in o["snippets"]]
    lines += ["", "## v5.1 (Step 3 + context split): the columns of this entity that hold these roles", ""]
    for c in fig["new"]:
        lines += [f"- column \"{c['name']}\" (#{c['cid']}, {c['n']} mentions): {c['n1']} {a1}, {c['n2']} {a2}"] + [f"  - `{s}`" for s in c["snippets"]]
    lines += ["", "(v5.1 names are the Step 3 names of the parts: no rename ran. The separation comes from the context split, as in v5.0.)", "",
              "Columns of this entity that hold the two roles, by variant:", ""]
    lines += [f"- {v}: " + "; ".join(cs) for v, cs in fig["also"].items()]
    lines.append("")
    (OUT / "figure_example.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import textwrap
    except ImportError:
        return False
    boxes = [(f"v5.0: \"{o['name']}\" ({o['n']})\n{o['n1']} {a1} + {o['n2']} {a2}", [f"{a}: {s}" for a, s in o["snippets"]])]
    boxes += [(f"v5.1: \"{c['name']}\" ({c['n']})\n{c['n1']} {a1}, {c['n2']} {a2}", c["snippets"]) for c in fig["new"][:2]]
    fig_, axs = plt.subplots(1, len(boxes), figsize=(4.2 * len(boxes), 3.6))
    for ax, (title, snips) in zip(axs if len(boxes) > 1 else [axs], boxes):
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, lw=1.2, transform=ax.transAxes))
        ax.text(0.04, 0.93, title, va="top", fontsize=9, fontweight="bold", transform=ax.transAxes)
        ax.text(0.04, 0.68, "\n\n".join(textwrap.fill(s, 38) for s in snips), va="top", fontsize=8, transform=ax.transAxes)
    fig_.tight_layout()
    fig_.savefig(OUT / "figure_example.png", dpi=130)
    return True


# ---------------------------------------------------------------- 7. C1 replay count
def c1_count(work=None):
    """Per R1 setting (alpha, t): how many new clusters (of the entities with cached columns) took the cached decision of the cached cluster
    they overlap most (lenient replay = the diary rule), strict one-to-one matches (Jaccard >= 0.8) and clusters nobody takes."""
    import r1_ctxvec_v51 as R1
    rows = []
    for dev in SETS:
        df = pd.read_csv(R1_CLUSTERS / f"clusters_{dev}.csv", dtype=str, keep_default_na=False)
        df["mention_id"] = df["mention_id"].astype(int)
        df = df.set_index("mention_id")
        emap, final = G3.load(dev)[2], G3.load(dev)[3]
        stage1 = {emap[k][0] for k in final}
        old = R1.by_entity(df, "cluster_a0.0_t0.4")
        for col in [c for c in df.columns if c.startswith("cluster_a")]:
            a, t = (float(x[1:]) for x in col[len("cluster_"):].split("_"))
            new = R1.by_entity(df, col)
            k = strict = lenient = mentions_len = 0
            for s in stage1:
                o = {c: set(v) for c, v in old.get(s, {}).items()}
                n = {c: set(v) for c, v in new.get(s, {}).items()}
                ms, ml = CV.match_clusters(o, n, CV.JACCARD, False), CV.match_clusters(o, n, CV.JACCARD, True)
                k += len(n)
                strict += len(ms)
                lenient += len(ml) - len(ms)
                mentions_len += sum(len(n[c]) for c in ml if c not in ms)
            rows.append({"set": dev, "alpha": a, "t": t, "new_clusters": k, "strict_match": strict, "took_cached_decision": lenient,
                         "mentions_in_those": mentions_len, "no_cached_cluster_holds_half": k - strict - lenient,
                         "selected": R1_SELECTED.get(a) == t if a else (t == 0.4), "adopted_t": t == 0.4})
    return rows


# ---------------------------------------------------------------- report
def md_table(rows, cols=None):
    return pd.DataFrame(rows)[cols].to_markdown(index=False) if cols else pd.DataFrame(rows).to_markdown(index=False)


def fmt(k, n):
    return f"{k}/{n}"


def report(build_info, summary, roles, tabs, table, clash, clash_sum, r4, calls, c1, fig, png):
    s = pd.DataFrame(summary)
    head = ["# wf_v5.1 C3: the real R5 Step 3 scored on the laptop (CPU)", "",
            "**What this is:** the real Step 3 of the R5 run (Llama-3.1-8B, guided, R3 + R4 on) + the v5.0 context split (big40) + the frozen loop-2 replay. "
            "**No rename** (the split parts keep the Step 3 names, no LLM), **no Step 4**, no column clash question. Found L2 does not depend on column names, "
            "so the found numbers are real for Step 3; names, loop-2 columns and Step 4 stay unknown until the rename / Step 4 run.", "",
            f"Encoder for the split and the loop-2 replay: laptop vectors (r5/<set>/vectors.npz); {build_info['fallback_texts']} texts needed the "
            f"laptop bge-m3 fallback ({build_info['texts_with_vector']} had a vector).", "",
            "## Summary: found L2, columns, wrong columns", ""]
    for taxi in ("off", "on"):
        t = s[s["taxi_rule"] == taxi]
        head += [f"### Taxi rule {taxi}", "",
                 t[["set", "variant", "gold_n", "found_L2", "found_loop1_only", "cols", "cols_gold", "cols_dup", "cols_other", "wrong_cols",
                    "new_wrong_cols_vs_v49", "gained_vs_v50", "lost_vs_v50"]].to_markdown(index=False), ""]
    head += ["found_loop1_only = gold attributes found by the loop-1 span rule on these columns alone (before loop 2 and the human check); "
             "found_L2 = v4.9 set (loop 1 + 2 + human check) minus loop-1 finds lost plus new ones (as v5.0 G3). Columns kinds as g3s3.md: gold / dup / other.",
             "Headline row = `v5.1 Step 3 + split`; v5.0 reference 34/40 | 30/41 (rule off), 33/40 | 34/41 (rule on).", "",
             "## Role table (taxi rule on; found yes/no, v5.0 -> v5.1)", "", md_table(roles), ""]
    done = [r for r in roles if r["both found v5.1"] != "n/a"]
    head += [f"Role pairs found (both found): v5.0 {sum(r['both found v5.0'] == 'yes' for r in done)}/{len(done)}, "
             f"v5.1 {sum(r['both found v5.1'] == 'yes' for r in done)}/{len(done)} "
             f"({'; '.join(f'{d} {sum(r['both found v5.1'] == 'yes' for r in done if r['set'] == d)}/{sum(r['set'] == d for r in done)}' for d in SETS)} in v5.1).", "",
             "## G2 trace of the misses left (taxi rule on; first stop point, loop 2 counted separately as S7 / S8; v5.0 g2.md was taxi off on the v4.9 columns)", "",
             table.to_markdown(index=False), ""]
    for d, df in tabs.items():
        cols = ["attr", "n_pipe", "share_in_scored", "stop", "stop_last", "if_majority_scored", "clusters_best", "split_best", "final_best", "loop2", "examples"]
        head += [f"### {d}: {len(df)} misses", "", df[[c for c in cols if c in df.columns]].to_markdown(index=False), ""]
    head += ["## C4: R3 clash questions of the real run", "", md_table(clash_sum), "",
             "Questions = distinct (entity, name, cluster pair) over the 3 orders; per-order counts are before the dedupe. same / unusable answer (fallback) = join as before. "
             "Full lists: `clash_<set>.csv` (names before / after, gold roles of the two clusters = description only).", ""]
    for d, rows in clash.items():
        df = pd.DataFrame(rows)
        ex = pd.concat([df[df["role_pair_touched"] != ""], df[df["role_pair_touched"] == ""].head(4)]).head(10)
        head += [f"### {d} examples (role-pair clashes first)", "", ex[["entity", "name_before", "cluster_a", "cluster_b", "answer", "name_a_after", "name_b_after",
                                                                     "gold_a", "gold_b", "role_pair_touched"]].to_markdown(index=False), ""]
    head += ["## R4: real prompt tokens per naming call", "", md_table(r4), "",
             "## Step 3 calls and tokens (cached rows; rows without tokens = assembled by code, not calls)", ""]
    c = pd.DataFrame(calls)
    tot = c.groupby(["run", "set"])[["rows", "calls", "prompt_tokens", "output_tokens"]].sum().reset_index()
    tot["estimate"] = tot["set"].map(EST_CALLS).where(tot["run"] == "v5.1")
    head += [tot.to_markdown(index=False), "", "Estimate = the brief's ~550 | ~475 (r34.md: 599 | 516 counted assembled rows too). Per family: `step3_calls.csv`.", "",
             "## C1: new clusters that took a cached decision (replay rule)", "",
             "Lenient replay of R1 = a new cluster takes the Step 3 decision of the cached cluster holding at least half of its mentions (the diary rule); "
             "strict = Jaccard >= 0.8 one-to-one; the rest got nothing (their mentions are dropped).", "",
             pd.DataFrame(c1)[lambda d: d["selected"] | d["adopted_t"]].to_markdown(index=False), "", "All settings: `c1_replay_count.csv`.", "",
             "## Figure", "", "See `figure_example.md`" + (" and `figure_example.png`." if png else ".") if fig else "No train time column with two mixed roles in v5.0 for this pair.", ""]
    (OUT / "c3.md").write_text("\n".join(head), encoding="utf-8", newline="\n")


def to_csv(rows, name):
    pd.DataFrame(rows).to_csv(OUT / name, index=False, encoding="utf-8", lineterminator="\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-build", action="store_true", help="reuse c3/<set>/ctxsplit and c3/rename (already built)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    info = B.read_json(OUT / "build_info.json") if a.skip_build else None
    if info is None:
        from run import encoder
        enc = encoder()
        info = build(enc)
        enc.save()
        B.write_json(OUT / "build_info.json", info)
    work = OUT / "work"
    summary, res = summary_rows(work)
    roles = role_rows(res)
    tabs, table = trace_tables(res)
    for d, df in tabs.items():
        df.to_csv(OUT / f"trace_{d}.csv", index=False, encoding="utf-8", lineterminator="\n")
    clash = {d: clash_rows(d) for d in SETS}
    for d, rows in clash.items():
        to_csv(rows, f"clash_{d}.csv")
    clash_sum, r4 = clash_summary(clash), r4_rows()
    calls = call_rows(R5, "v5.1") + call_rows(V50_STEP3, "v5.0")
    c1 = c1_count()
    fig = None
    for dev in SETS:
        fig = figure_data(dev, RN.text_source(dev))
        if fig:
            break
    png = write_figure(fig) if fig else False
    to_csv(summary, "summary.csv")
    to_csv(roles, "role_table.csv")
    table.to_csv(OUT / "trace_table.csv", index=False, encoding="utf-8", lineterminator="\n")
    to_csv(clash_sum, "clash_summary.csv")
    to_csv(r4, "r4_tokens.csv")
    to_csv(calls, "step3_calls.csv")
    to_csv(c1, "c1_replay_count.csv")
    report(info, summary, roles, tabs, table, clash, clash_sum, r4, calls, c1, fig, png)
    print((OUT / "c3.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
