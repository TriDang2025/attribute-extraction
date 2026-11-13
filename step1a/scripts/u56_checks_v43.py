"""wf_v4.3 CPU checks U5 (assembler repairs of the old Llama chains) and U6 (cost table option B vs v4.3).

python scripts/u56_checks_v43.py u5     -> results/wf_v43/u5/{repairs_old.csv, ablation_old.csv, summary.md}
python scripts/u56_checks_v43.py u6     -> results/wf_v43/u6/{cost.csv, cost.md}
Old chains: results/wf_v42/t2c_step4_keyed_ext (option B extended, Step 4; input c1 = all GT columns, input a = Qwen's Step 3 handover).
The v4.3 side of both reads results/wf_v43/u4/**/repairs.json and the response rows of results/wf_v43/u0, u2, u4 when they exist.
U5 scoring uses the scorer that wrote the old final/scores.csv (scripts/score_v4.py); the baseline row of each chain is checked against it.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import batch_v4 as B  # noqa: E402
from s1a import cost_v43 as C  # noqa: E402
from s1a import repairs_v43 as R  # noqa: E402
from s1a.log_v43 import RepairLog  # noqa: E402

OLD = ROOT / "results" / "wf_v42" / "t2c_step4_keyed_ext"
OLD_FIRST = ROOT / "results" / "wf_v42" / "t2b_step4_keyed"
OLD_STEP3 = ROOT / "results" / "wf_v42" / "t1b_step3_keyed"
V43 = ROOT / "results" / "wf_v43"
METRICS = ("table_recall", "table_precision", "table_f1", "placement", "gt_columns_placed", "grouping_f1", "pk_right", "rel_precision",
           "rel_recall")
ALT_DATA = Path.home() / "repos" / "attribute-extraction" / "chunking" / "data"   # gitignored data of the main checkout (read only)


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_text(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def md_table(rows, fields):
    return "\n".join(["| " + " | ".join(fields) + " |", "|" + "---|" * len(fields)]
                     + ["| " + " | ".join(str(r.get(k, "")) for k in fields) + " |" for r in rows]) + "\n"


# ---------------------------------------------------------------- U5
def repairs_table(out, root):
    """Wide rows (one per chain, then one total row per input): chain, input, ok, error, a count per R.ALL_TYPES, total_repairs."""
    rows = []
    for ch in B.read_json(Path(out) / "chains.json"):
        log, st = R.chain_repairs(out, ch, root)
        if not R.check_against_frozen(out, ch, root):
            raise ValueError(f"{ch['id']}: typed replay differs from batch_v4.replay")
        rows.append({"chain": ch["id"], "input": ch["input"], "set": ch["set"], "ok": st["error"] is None, "error": st["error"] or "",
                     **{t: log.counts.get(t, 0) for t in R.ALL_TYPES}, "total_repairs": sum(v for k, v in log.counts.items()
                                                                                              if R.TYPE_STEP[k] != "event")})
    for inp in dict.fromkeys(r["input"] for r in rows):
        mine = [r for r in rows if r["input"] == inp]
        rows.append({"chain": f"ALL_{inp}", "input": inp, "set": "", "ok": f"{sum(r['ok'] for r in mine)}/{len(mine)}", "error": "",
                     **{k: sum(r[k] for r in mine) for k in (*R.ALL_TYPES, "total_repairs")}})
    return rows


def variants(counts):
    """Ablation variants of a chain: each repaired type that can be switched off (the 4.4 kinds only together as all_44) and all of them."""
    kinds = sorted({("all_44" if k in R.TYPES_44 else k) for k in counts if R.TYPE_STEP[k] != "event" and counts[k]})
    return [{k} for k in kinds] + ([set(kinds)] if len(kinds) > 1 else [])


def make_scorer():
    import score_v4 as SC
    gt = SC.load(ROOT / "gt" / "schema_gt_v1.yaml", ROOT / "results" / "wf_v4" / "gt", B.SETS)
    return lambda canonical, ch: SC.score_rows(ch["id"], canonical, gt, ch["set"], ROOT / "handover")


def ablation_table(out, chains, root, score, old_scores):
    """Rows: chain, off, strict_ok / strict_error (validators on), lenient_ok / lenient_error (validators ignored), ignored, reachable_only,
    metrics and their change vs the old scores.csv row (lenient run; baseline row = nothing off)."""
    rows = []
    for ch in chains:
        counts = R.replay_typed(out, ch, root)["counts"]
        for off in [set()] + variants(counts):
            strict = R.ablate(out, ch, root, off, score, strict=True)
            lenient = R.ablate(out, ch, root, off, score, strict=False)
            base = {"chain": ch["id"], "off": lenient["off"] or "(baseline)", "strict_ok": strict["ok"], "strict_error": strict["error"] or "",
                    "lenient_ok": lenient["ok"], "lenient_error": lenient["error"] or "", "ignored": lenient["ignored"]}
            if not lenient["scores"]:
                rows.append(base)
            for s in lenient["scores"]:
                old = old_scores[(ch["id"], str(s["reachable_only"]))]
                rows.append({**base, "reachable_only": s["reachable_only"],
                             **{m: s[m] for m in METRICS},
                             **{f"d_{m}": "" if s[m] is None or old[m] in ("", None) else round(float(s[m]) - float(old[m]), 4) for m in METRICS}})
    return rows


def read_scores(path):
    with open(path, encoding="utf-8") as f:
        return {(r["schema"], r["reachable_only"]): r for r in csv.DictReader(f)}


def mean(xs):
    xs = [x for x in xs if x not in ("", None)]
    return round(sum(xs) / len(xs), 3) if xs else ""


def ablation_summary(rows):
    """Per (off): chains where it applies, how many pass the validators without it, how many assemble, mean change (full GT, lenient)."""
    out = []
    for off in dict.fromkeys(r["off"] for r in rows if r["off"] != "(baseline)"):
        mine = {r["chain"]: r for r in rows if r["off"] == off}
        full = [r for r in rows if r["off"] == off and r.get("reachable_only") in (False, "False")]
        out.append({"off": off, "chains": len(mine), "pass validators": sum(bool(r["strict_ok"]) for r in mine.values()),
                    "assemble anyway": sum(bool(r["lenient_ok"]) for r in mine.values()),
                    **{f"mean d_{m}": mean([r.get(f"d_{m}") for r in full]) for m in ("table_f1", "placement", "gt_columns_placed",
                                                                                         "grouping_f1", "pk_right")}})
    return out


def example_repairs(out, root):
    """Three example repairs with the raw answer text: a dropped 4.3 relationship, a column put back in 4.4, a renamed 4.2 table."""
    ex = []
    chains = {c["id"]: c for c in B.read_json(Path(out) / "chains.json")}

    def raw(ch, step):
        return B.last_row(Path(out) / "responses" / f"{ch}_4{step}.jsonl")["raw"]

    log = RepairLog(keep=1)
    R.replay_typed(out, chains["c1_dev50_s0"], root, log=log)
    d = log.examples.get("rel_unknown_table", [{}])[0].get("detail", "")
    if d:
        rel = json.loads(d)
        ex.append({"chain": "c1_dev50_s0", "step": "4.3", "type": "rel_unknown_table",
                   "raw": R.snippet(raw("c1_dev50_s0", 3), f'"{rel["from"]}"', 240),
                   "code": f"relationship {rel.get('from')!r} -> {rel.get('to')!r} names a table that no 4.2 group produced; repair_43 dropped it"})
    t = R.replay_typed(out, chains["c1_dev50_s0"], root, off={"col_missing", "all_44"}, strict=False)
    full = R.replay_typed(out, chains["c1_dev50_s0"], root)
    for tb_raw, tb in zip(t["ans"]["44"]["tables"], full["ans"]["44"]["tables"]):
        have = {c["column"] for c in tb_raw["columns"]}
        added = [c for c in tb["columns"] if c["column"] not in have and not str(c["column"]).startswith("new:")]
        if added:
            ex.append({"chain": "c1_dev50_s0", "step": "4.4", "type": "col_missing",
                       "raw": R.snippet(raw("c1_dev50_s0", 4), f'"{tb["name"]}"', 300),
                       "code": f"table {tb['name']!r} lacks columns of its 4.1 group in the answer; repair_44 added {[c['column'] for c in added]} "
                               f"(names from the input, types from the value type)"})
            break
    for ch in chains.values():
        tabs = R.raw_42_tables(raw(ch["id"], 2)) if B.last_row(Path(out) / "responses" / f"{ch['id']}_42.jsonl") else None
        names = [str(x.get("name", "")).strip().lower() for x in tabs or []]
        dup = next((n for n in names if n and names.count(n) > 1), None)
        if dup:
            t2 = R.replay_typed(out, ch, root, upto=2)
            new = [x["name"] for x in t2["ans"]["42"]["tables"] if x["name"].lower().startswith(dup + "_")]
            ex.append({"chain": ch["id"], "step": "4.2", "type": "name_renamed",
                       "raw": R.snippet(raw(ch["id"], 2), f'"name": "{dup}"', 240, nth=-1),
                       "code": f"two groups got the table name {dup!r}; keyed_v42._unique_names kept the first and renamed the second to {new}"})
            break
    return ex


def reading(summ):
    """The plain-English reading of the ablation summary, with its numbers taken from the table."""
    def g(off, key):
        return next((r[key] for r in summ if r["off"] == off), "n/a")
    return (f"Reading: with the validators on, 0 of the c1 chains pass without the 4.4 repairs ({g('all_44', 'pass validators')}/{g('all_44', 'chains')}) "
            f"or without the 4.3 repairs ({g('rel_unknown_table', 'pass validators')}/{g('rel_unknown_table', 'chains')} for rel_unknown_table): the "
            "frozen validators reject the raw answers (unknown tables in 4.3; columns missing or a key also listed as a column in 4.4), so the "
            "repairs decide whether a chain is scored at all. With the validators ignored: dropping 4.3 relationships (rel_*) changes no score; "
            f"keeping the invalid new tables (new_table_invalid) changes table F1 by {g('new_table_invalid', 'mean d_table_f1')} on average "
            "(one chain, c1_dev50b_s1); not repairing 4.4 (mostly col_missing: 150 columns put back) lowers table F1 by "
            f"{g('all_44', 'mean d_table_f1')} and the share of GT columns placed by {g('all_44', 'mean d_gt_columns_placed')}, because tables without "
            "their columns no longer match the GT tables. The placement score (right place among placed columns) goes up by "
            f"{g('all_44', 'mean d_placement')} only because fewer columns are placed, so it is not a gain. Conclusion: yes, the 4.4 repairs "
            "(col_missing above all) carry the old c1 scores; the 4.3 drops are harmless. Detail with both GT views and more metrics: "
            "`ablation_old.csv`.")


def run_u5(args):
    out_dir = ROOT / "results" / "wf_v43" / "u5"
    chains = B.read_json(OLD / "chains.json")
    table = repairs_table(OLD, ROOT)
    new_repairs = {k: v for k, v in R.load_repairs(V43 / "u4").items() if "fake" not in k.split("/")}   # fake-model dry runs are not results
    write_csv(out_dir / "repairs_old.csv", table)
    score = make_scorer()
    old = read_scores(OLD / "final" / "scores.csv")
    base_ok = []
    for ch in chains:
        if ch["input"] != "c1":
            continue
        r = R.ablate(OLD, ch, ROOT, set(), score)
        base_ok += [all(abs(float(s[m]) - float(old[(ch["id"], str(s["reachable_only"]))][m])) < 1e-9 for m in METRICS
                        if s[m] is not None) for s in r["scores"]]
    ab = ablation_table(OLD, [c for c in chains if c["input"] == "c1"], ROOT, score, old)
    write_csv(out_dir / "ablation_old.csv", ab)
    summ = ablation_summary(ab)
    side = R.side_by_side({r["chain"]: {k: r[k] for k in R.ALL_TYPES if r[k]} for r in table if not r["chain"].startswith("ALL")},
                          new_repairs)
    ex = example_repairs(OLD, ROOT)
    fields = ["chain", "ok", *[t for t in R.ALL_TYPES if any(r[t] for r in table)], "total_repairs"]
    md = ["# U5: assembler repairs in the old Llama chains (wf_v4.2 option B extended, results/wf_v42/t2c_step4_keyed_ext)\n",
          "Counts are replayed from the cached answers with `s1a/repairs_v43.py` (the typed replay gives the same answers and the same repair totals as "
          "`batch_v4.replay` for all 12 chains; the 4.2 renames are counted separately, `batch_v4` does not count them). Types: 4.1 col_*, "
          "4.2 name_renamed, 4.3 new_table_invalid / rel_*, 4.4 key_listed / dup_listed / col_missing / fk_col_added / fk_ref_to_pk; "
          "events (not text repairs): unguided_retry, unguided_job, cut_off. Chains of input c1 = all GT columns, input a = Qwen's Step 3 handover.\n",
          "## Repairs per chain\n", md_table(table, fields),
          "`ok` False = the chain stopped (a/dev50 s0 and s2: 4.4 still fails a validator after the repairs; a/dev50 s1: 4.4 cut off, parse error; "
          "a/dev50b: 4.3 cut off). For a stopped chain the counts cover the calls up to the one that stopped it.\n",
          "## Do the repairs change the scores? (input c1, 6 chains)\n",
          f"Baseline check: replaying with nothing switched off gives the scores of `final/scores.csv` for {sum(base_ok)}/{len(base_ok)} rows "
          "(both GT views x 6 chains), same scorer (`scripts/score_v4.py`).\n",
          "Two ways to leave a repair out: **validators on** (the unrepaired answer must pass the frozen validators, as in the real run) and "
          "**validators ignored** (the answer goes to the assembler and the scorer as it is; a failing assembly is `assemble anyway` = no). "
          "The 4.4 repair kinds cannot be switched off one by one (one function), so they are switched off together as `all_44`. "
          "Means are over the chains the repair applies to, full GT, change vs the old score:\n",
          md_table(summ, list(summ[0])) if summ else "no repairs\n",
          reading(summ),
          "## Three example repairs\n"]
    for e in ex:
        md.append(f"- **{e['chain']}, {e['type']} (step {e['step']})**\n  - raw answer: `{e['raw']}`\n  - code: {e['code']}\n")
    md += ["\n## v4.3 side by side (old = all 12 chains above, new = results/wf_v43/u4/**/repairs.json)\n",
           md_table(side, ["type", "step", "old", "new"]),
           "" if new_repairs else "v4.3 Step 4 not run yet: no repairs.json under results/wf_v43/u4; re-run this command after it. "
           "Note that the old column mixes input c1 and input a; compare by input only if the v4.3 chains say which input they used.\n"]
    write_text(out_dir / "summary.md", "\n".join(md))
    print("U5 written to", out_dir, "| baseline rows ok", sum(base_ok), "/", len(base_ok))


# ---------------------------------------------------------------- U6
def load_corpus(data_dir=None):
    """{set: (tokens, "tok" | "est.")} of the dev50 / dev50b dialogues (turns joined by newline), Llama-3.1 tokenizer if cached locally."""
    from s1a import paths  # noqa: F401 - puts chunking/ on sys.path
    from chk import config
    data = next((Path(d) for d in (data_dir, ROOT.parent / "chunking" / "data", ALT_DATA) if d and (Path(d) / "conversation_ids.txt").exists()), None)
    if data is None:
        raise FileNotFoundError("conversation_ids.txt and MULTIWOZ2.4.zip not found; pass --data-dir")
    config.IDS, config.MULTIWOZ_ZIP = data / "conversation_ids.txt", data / "MULTIWOZ2.4.zip"
    from s1a import split
    tok = None
    snaps = sorted((Path.home() / ".cache" / "huggingface" / "hub" / "models--meta-llama--Llama-3.1-8B-Instruct" / "snapshots").glob("*"))
    if snaps:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(str(snaps[0]), local_files_only=True)
    return {s: C.corpus_tokens(["\n".join(d["turns"]) for d in split.dialogues(*a)], tok)
            for s, a in (("dev50", ("dev", 50)), ("dev50b", ("dev50b",)))}


def run_u6(args):
    out_dir = ROOT / "results" / "wf_v43" / "u6"
    steps = {"option B": {"step3": C.run_stats(OLD_STEP3), "step4": C.run_stats(OLD), "post": None},
             "v4.3": {"step3": C.run_stats(V43 / "u2"), "step4": C.run_stats(V43 / "u4"), "post": C.run_stats(V43 / "u0")}}
    loading = {"option B": C.load_seconds(OLD_STEP3, OLD), "v4.3": C.load_seconds(V43 / "u2", V43 / "u4", V43 / "u0")}
    corpus = load_corpus(args.data_dir)
    rows = C.cost_rows(steps, corpus, loading)
    write_csv(out_dir / "cost.csv", rows)
    first, extra = C.run_stats(OLD_FIRST), C.run_stats(OLD_STEP3)
    md = ["# U6: cost, option B (wf_v4.2) vs v4.3, dev50 and dev50b\n",
          "Option B Step 3 = `results/wf_v42/t1b_step3_keyed` (A calls only, 18 jobs); Step 4 = `results/wf_v42/t2c_step4_keyed_ext` "
          "(12 chains: input c1 and input a, 4 calls each where they got that far). v4.3 reads `results/wf_v43/u2` (Step 3), `u4` (Step 4) and "
          "`u0` (post-step calls, own row); \"not run\" = no response rows there yet. Calls = jobs + unguided retries (a retried row holds both calls' tokens).\n",
          C.to_markdown(rows)]
    if first:
        md.append(f"\nFirst option B Step 4 run (`t2b_step4_keyed`, 4.3 not capped): {first['both']['calls']} calls, {first['both']['prompt_tokens']:,} tokens in, "
                  f"{first['both']['output_tokens']:,} out, {first['gpu_seconds'] / 60:.1f} GPU minutes.\n")
    md.append("\nCaveats: GPU time of a batch is shared by both sets, so it is given for both sets together; the seconds of an unguided retry are lost "
              "when the first (guided) row is kept, so GPU minutes can be slightly low. Model loading time is not logged in any committed run file "
              "(run_info.json holds job counts only; the notebooks print no timing).\n")
    write_text(out_dir / "cost.md", "\n".join(md))
    print("U6 written to", out_dir, "| step3 gpu s", extra and extra["gpu_seconds"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part", choices=("u5", "u6"))
    ap.add_argument("--data-dir", type=Path, help="folder with conversation_ids.txt and MULTIWOZ2.4.zip (u6; default: chunking/data, else the main checkout)")
    a = ap.parse_args()
    {"u5": run_u5, "u6": run_u6}[a.part](a)


if __name__ == "__main__":
    main()
