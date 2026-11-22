"""wf_v5.1 R3 + R4 offline build (CPU, no LLM, no bge-m3 encoding, no data/cache): from the cached v5.0 Step 3 run (results/wf_v46/y3/<dev>/,
the loop-1 Step 3 of v5.0; identical to results/wf_v47/z4/run1 final columns) build
- R4: the Step 3 names prompts with and without the naming_context switch, compare "off" with the cached prompts byte for byte, count
  the prompt tokens (project estimate pipeline: pilot_input.est_tokens = chars / 3.5, scaled to the real cached prompt tokens);
- R3: the name clash questions the name_clash switch would ask on the cached names (after rescue and merge), per set.
Writes results/wf_v51/r34/{r34.md, r34_summary.json, clash_<set>.csv, sample_prompts/, jobs/<set>/ (clash prompts, schemas, manifest)}.
Run from step1a/:  python scripts/r34_build_v51.py [--fake-smoke]
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from s1a import batch_v4 as B  # noqa: E402
from s1a import log_v44 as LOG  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import rolenames_v51 as RN  # noqa: E402
from s1a import step3_v44 as S3  # noqa: E402

SETS = {"dev50": "c_n50", "dev50b": "c_n50b"}
Y3 = ROOT / "results" / "wf_v46" / "y3"
OUT = ROOT / "results" / "wf_v51" / "r34"
CRLF = b"\r\n"        # the cached prompt files were written with CRLF
GRID = [(0, 4), (5, 4), (5, 6), (8, 4), (0, 99)]          # (min_mentions, max_per_name) variants of the question count


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def r4_set(dev, run, cfg_roles, sample=None):
    """R4 numbers of one set: names jobs off / on, byte check of "off" against the cached prompts, tokens."""
    step3, a_dir = Y3 / dev / "step3", Y3 / dev / "a_prompts"
    entmap = B.read_json(Y3 / dev / "entities.json")
    cfg = S3.load_config()
    variant = B.read_json(step3 / "config_used.json")["names_variant_used"]
    vecs, snips = S3.cluster_vectors(run), RN.set_snippets(run, cfg_roles)
    cached = {r["job"]: r for r in LOG.call_rows(step3) if "_names_" in r["job"]}
    rows = []
    with PL.use_corpus(run, entmap, a_dir):
        for j in [j for j in B.read_json(a_dir / "manifest.json")["jobs"] if j["family"] == "a"]:
            order, text = int(j["run_tag"][1:]), (a_dir / j["prompt"]).read_text(encoding="utf-8")
            r0, f0 = S3.names_jobs_for_v44(run, j["ent"], order, text, variant, cfg, vecs)
            r1, f1 = S3.names_jobs_for_v44(run, j["ent"], order, text, variant, cfg, vecs, snippets=snips)
            for a, b, p0, p1 in zip(r0, r1, f0, f1):
                old = step3 / "prompts" / f"{a['job']}.txt"
                real = cached.get(a["job"], {}).get("prompt_tokens")
                rows.append({"job": a["job"], "same_as_cached": old.exists() and old.read_bytes().replace(CRLF, b"\n") == p0[1].encode("utf-8"),
                             "est_off": a["est_prompt_tokens"], "est_on": b["est_prompt_tokens"], "real_off": real,
                             "same_schema": p0[2] == p1[2], "clusters": len(a["cluster_ids"])})
                if sample is not None and a["order"] == 0 and a["batch"] == 1:
                    sample.setdefault((dev, a["ent"]), (p0[1], p1[1], a["job"]))
    return pd.DataFrame(rows)


def r3_set(dev, run, cfg_roles, snips_run):
    """R3 numbers of one set: the questions on the cached names (after rescue and merge); writes jobs/<dev> and clash_<dev>.csv."""
    step3 = Y3 / dev / "step3"
    base = S3.read_base(step3)
    state, _ = S3.apply_rescue(step3, base)
    state, _ = S3.apply_merge(step3, state)
    jobs_dir = OUT / "jobs" / dev
    if jobs_dir.exists():
        shutil.rmtree(jobs_dir)
    jobs_dir.mkdir(parents=True)
    shutil.copy(step3 / "blocks.json", jobs_dir / "blocks.json")
    cfg = {**S3.load_config(), "name_clash": cfg_roles["name_clash"]}
    variant = B.read_json(step3 / "config_used.json")["names_variant_used"]
    entmap = B.read_json(Y3 / dev / "entities.json")
    with PL.use_corpus(run, entmap, Y3 / dev / "a_prompts"):
        jobs = RN.build_clash_q(jobs_dir, cfg, state, variant, {run: snips_run})
    doc = S3.blocks_doc(jobs_dir)
    rows = []
    for j in jobs:
        a, b = j["cluster_ids"]
        bl = doc[f"{run}/{j['ent']}"]["blocks"]
        rows.append({"set": dev, "entity": j["entity"], "ent": j["ent"], "name": j["name"], "cluster_a": a, "cluster_b": b,
                     "mentions_a": S3.block_mentions(bl[a]), "mentions_b": S3.block_mentions(bl[b]), "orders": ",".join(map(str, j["orders"])),
                     "job": j["job"], "est_prompt_tokens": PIN.est_tokens((jobs_dir / j["prompt"]).read_text(encoding="utf-8")),
                     "snippets_a": " | ".join(snips_run.get(a, [])), "snippets_b": " | ".join(snips_run.get(b, []))})
    df = pd.DataFrame(rows, columns=["set", "entity", "ent", "name", "cluster_a", "cluster_b", "mentions_a", "mentions_b", "orders", "job",
                                     "est_prompt_tokens", "snippets_a", "snippets_b"])
    df.to_csv(OUT / f"clash_{dev}.csv", index=False, encoding="utf-8", lineterminator="\n")
    grid = {}
    for mn, mx in GRID:
        keys = set()
        for (s, ent, o), st in state.items():
            for name, a, b in RN.clash_pairs(st, doc[f"{s}/{ent}"]["blocks"], mn, mx):
                keys.add((ent, name, RN.pair_key(a, b)))
        grid[f"min{mn}_max{mx}"] = len(keys)
    per_order = {o: sum(len(RN.clash_pairs(st, doc[f"{s}/{e}"]["blocks"], cfg_roles["name_clash"]["min_mentions"],
                                           cfg_roles["name_clash"]["max_per_name"])) for (s, e, oo), st in state.items() if oo == o)
                 for o in (0, 1, 2)}
    return df, jobs, state, grid, per_order


def fake_smoke(dev, run, jobs_dir, state, snips_run):
    """Run the clash stage on the fake backend in a temp copy; returns the backend info."""
    step3 = Y3 / dev / "step3"
    cfg = {**S3.load_config(), "switches": {**S3.load_config()["switches"], "name_clash": True}, **{k: v for k, v in RN.load_config().items()
                                                                                                  if k == "name_clash"}}
    variant = B.read_json(step3 / "config_used.json")["names_variant_used"]
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(step3 / "blocks.json", Path(tmp) / "blocks.json")
        with PL.use_corpus(run, B.read_json(Y3 / dev / "entities.json"), Y3 / dev / "a_prompts"):
            info, new = RN.run_clash(tmp, RN.FakeStep51(), cfg, state, variant, snips={run: snips_run})
        log = json.loads((Path(tmp) / "clash_log.json").read_text(encoding="utf-8"))
    return info, log["counts"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fake-smoke", action="store_true")
    args = ap.parse_args()
    cfg_roles = RN.load_config()
    OUT.mkdir(parents=True, exist_ok=True)
    summary, sample = {}, {}
    for dev, run in SETS.items():
        r4 = r4_set(dev, run, cfg_roles, sample)
        snips = RN.set_snippets(run, cfg_roles)
        df, jobs, state, grid, per_order = r3_set(dev, run, cfg_roles, snips)
        cached_calls = len([r for r in LOG.call_rows(Y3 / dev / "step3")])
        est_off, est_on = int(r4["est_off"].sum()), int(r4["est_on"].sum())
        real_off = int(r4["real_off"].dropna().sum())
        s = {"names_calls": len(r4), "names_calls_with_real_tokens": int(r4["real_off"].notna().sum()),
             "off_equals_cached": f"{int(r4['same_as_cached'].sum())}/{len(r4)}", "schema_unchanged": bool(r4["same_schema"].all()),
             "est_tokens_off": est_off, "est_tokens_on": est_on, "est_increase_per_call": round((est_on - est_off) / len(r4), 1),
             "est_increase_pct": round(100 * (est_on - est_off) / est_off, 1), "real_prompt_tokens_names_off": real_off,
             "step3_cached_calls": cached_calls, "clash_questions": len(jobs), "clash_per_order_pairs": per_order, "clash_grid": grid,
             "clash_blocked": sum(j["blocked"] for j in jobs), "clash_est_prompt_tokens": int(df["est_prompt_tokens"].sum()),
             "clash_est_tokens_per_call": round(float(df["est_prompt_tokens"].mean()), 1) if len(df) else 0,
             "step3_calls_with_r3_r4": cached_calls + len(jobs)}
        if args.fake_smoke:
            info, counts = fake_smoke(dev, run, OUT / "jobs" / dev, state, snips)
            s["fake_smoke"] = {"info": info, "log": counts}
        summary[dev] = s
        r4.to_csv(OUT / f"r4_prompts_{dev}.csv", index=False, encoding="utf-8", lineterminator="\n")
    sp = OUT / "sample_prompts"
    if sp.exists():
        shutil.rmtree(sp)
    for (dev, ent), (off, on, job) in sorted(sample.items()):
        if "train" in ent or ent in ("phone_number", "train_schedule"):       # sample only: the train / taxi entities of the two sets
            _write(sp / f"r4_{dev}_{job}_off.txt", off)
            _write(sp / f"r4_{dev}_{job}_on.txt", on)
    for dev in SETS:
        df = pd.read_csv(OUT / f"clash_{dev}.csv", dtype=str, keep_default_na=False)
        if len(df):
            df["m"] = df[["mentions_a", "mentions_b"]].astype(int).min(axis=1)
            for _, r in df.sort_values("m", ascending=False).head(2).iterrows():
                shutil.copy(OUT / "jobs" / dev / "prompts" / f"{r['job']}.txt", sp / f"r3_{dev}_{r['job']}.txt")
    B.write_json(OUT / "r34_summary.json", summary)
    _write(OUT / "r34.md", report(summary))
    print(json.dumps(summary, indent=1))


def report(sm):
    a, b = sm["dev50"], sm["dev50b"]
    lines = ["# wf_v5.1 R3 + R4: names with context, name clash question (offline build)", "",
             "Built by `scripts/r34_build_v51.py` from the cached v5.0 Step 3 (`results/wf_v46/y3/<set>/step3`). No LLM, no bge-m3, no cache writes.", "",
             "## R4 naming with context (switch `naming_context`)", "",
             "| | dev50 | dev50b |", "|---|---|---|"]
    for k, t in (("names_calls", "names calls (3 orders)"), ("off_equals_cached", "switch off = cached v5.0 prompt (cached files have CRLF; compared after CRLF to LF)"),
                 ("schema_unchanged", "schema unchanged"), ("est_tokens_off", "est. prompt tokens, off"), ("est_tokens_on", "est. prompt tokens, on"),
                 ("est_increase_per_call", "increase per call (est. tokens)"), ("est_increase_pct", "increase (%)"),
                 ("real_prompt_tokens_names_off", "real prompt tokens of the cached names calls")):
        lines.append(f"| {t} | {a[k]} | {b[k]} |")
    lines += ["", "Token counter: `pilot_input.est_tokens` (chars / 3.5, the project estimate in every job row); no tokenizer is on the laptop. "
              "Real tokens of the names calls on the GPU would grow by about the same percentage.", "",
              "## R3 name clash question (switch `name_clash`)", "",
              "Questions = distinct (entity, name, cluster pair) over the 3 orders, after names, rescue and merge. Defaults (config/wf_v51_roles.json): "
              "clusters with >= 5 mentions, the biggest 4 per name, each against the biggest.", "",
              "| | dev50 | dev50b |", "|---|---|---|",
              f"| questions asked | {a['clash_questions']} | {b['clash_questions']} |",
              f"| pairs per order 0 / 1 / 2 (before dedupe over orders) | {' / '.join(str(v) for v in a['clash_per_order_pairs'].values())} | "
              f"{' / '.join(str(v) for v in b['clash_per_order_pairs'].values())} |",
              f"| est. prompt tokens per question | {a['clash_est_tokens_per_call']} | {b['clash_est_tokens_per_call']} |",
              f"| est. prompt tokens, all questions | {a['clash_est_prompt_tokens']} | {b['clash_est_prompt_tokens']} |", "",
              "Questions for other settings (min mentions, max clusters per name):", "", "| setting | dev50 | dev50b |", "|---|---|---|"]
    lines += [f"| {k} | {v} | {b['clash_grid'][k]} |" for k, v in a["clash_grid"].items()]
    lines += ["", "The listed questions are in `clash_dev50.csv` and `clash_dev50b.csv` (names, cluster ids, mentions, orders, 3 snippets per cluster).", "",
              "## R5 Step 3 call estimate (with R3 + R4 on)", "",
              "| | dev50 | dev50b |", "|---|---|---|",
              f"| cached v5.0 Step 3 calls | {a['step3_cached_calls']} | {b['step3_cached_calls']} |",
              "| R4 extra calls | 0 | 0 |",
              f"| R3 extra calls | {a['clash_questions']} | {b['clash_questions']} |",
              f"| **Step 3 calls with R3 + R4** | {a['step3_calls_with_r3_r4']} | {b['step3_calls_with_r3_r4']} |", "",
              "The diary expects about 600 per set. Caveat: the cached count is the v5.0 run; role names change the later stages (merge questions depend on "
              "the name cosine, reconcile and duplicate check on the columns), so the real count can move by tens of calls either way.", ""]
    if "fake_smoke" in a:
        lines += ["## Fake-LLM smoke on the cached state", "", f"dev50: {a['fake_smoke']}", "", f"dev50b: {b['fake_smoke']}", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
