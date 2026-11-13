"""wf_v4.3 (diary Nov 13, U0 / U2): the rest of frozen Step 3 on A answers of Llama-3.1-8B, shared by U0 (A = wf_v4.2 option B answers)
and U2 (A = Step 3 v4.3 names, s1a/step3_v43.py). Frozen code is only imported (nothing is edited).

Run folder `out` = the v3.9 Colab folder layout (so final_v39.entity_columns and batch_stage2_v39 read it unchanged):
- manifest.json: A jobs (family a, run key v22d50 / v22d50b; U0: the real option B jobs, U2: assembled jobs with "assembled": true and
  no prompt) + the 54 frozen split jobs (family split, STEP3.md step 3) + the reconcile jobs once built. run_data_v37.load_a reads it.
- examples.csv (variant = job name), prompts/, responses/ (U0: the 18 option B answers are copied in, marked "reused": true).
- columns.json + manifest_stage2.json: written by the reconcile / duplicate-check builders (batch_build_v39 / batch_stage2_v39 code).
Stages after A (each stage's jobs are built from the answers before it, so a notebook drives them one at a time):
  split (frozen prompts, independent of A) -> reconcile (batch_build_v39.build_reconcile on the Llama columns) -> dupcheck
  (batch_stage2_v39 on the reconciled columns). `stage_jobs(out, stage)` returns a stage's jobs; `run_post(out, llm)` runs them all.
Scoring: `score(out)` reads everything through final_v39 / dashboard_v38 (the scorer of the Qwen 31/40 and 29/41, STEP3.md).
Data the builders and the scorer read: results/graph_v22_<set>/ (spans incl. the gitignored vectors.npz, docs.jsonl) and
results/loop1_v35/gt_levels.csv, results/loop1_v37/dev50b/gt/gt_levels.csv (scoring only; the stage builders do not read the GT).
"""
import contextlib
import importlib
import io
import json
import re
import shutil
import sys
import zlib
from collections import Counter
from pathlib import Path

import pandas as pd

from . import batch_v4 as B
from . import batch_v38 as BT
from . import batch_v39 as B9
from . import llm_cache as LC
from . import log_v43 as LOG
from . import nov16_v41 as NV
from . import pilot_input as PIN
from . import pilot_verify as PV
from . import run_data_v37 as RD
from . import score_v39_batch as SB
from . import v34_data as VD

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SETS = ("dev50", "dev50b")
ENTS = ("train", "hotel", "restaurant")
RUN_KEY = {"dev50": "v22d50", "dev50b": "v22d50b"}
BASE = "A s012"
POST_STAGES = ("split", "reconcile", "dupcheck")
T1B = ROOT / "results" / "wf_v42" / "t1b_step3_keyed"          # option B answers (U0 input) and the frozen A prompts (U2 batches)
SPLIT_SRC = {"dev50": (ROOT / "results" / "loop1_v31", None), "dev50b": (ROOT / "results" / "loop1_v37" / "colab", "v22d50b")}
A_EX_SRC = {"dev50": ((ROOT / "results" / "loop1_v31" / "examples.csv", "{ent}_v2"),
                      (ROOT / "results" / "loop1_v31" / "examples.csv", "{ent}_v2"),
                      (ROOT / "results" / "loop1_v36" / "colab" / "examples.csv", "{ent}_v2_s2")),
            "dev50b": tuple((ROOT / "results" / "loop1_v37" / "colab" / "examples.csv", "{ent}_a_v22d50b_s%d" % s) for s in range(3))}
SPLIT_MAX_TOKENS = 3000                                        # STEP3.md
END_NAME = re.compile(r"[ _-]end$")                            # an invented "_end"-style name (norm_name turns "_" into " ")
FREE_NAMES = {PV.norm_name("not_attribute"), PV.norm_name("attribute_cue")}


def is_end_name(name):
    return bool(END_NAME.search(str(name)))


def script(name):
    """Import a module of scripts/ (the frozen builders and scorers live there)."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


# ---------------------------------------------------------------- manifest
def read_manifest(out):
    return B.read_json(Path(out) / "manifest.json")["jobs"]


def write_manifest(out, jobs):
    B.write_json(Path(out) / "manifest.json", {"stage": 1, "jobs": jobs})


def manifest_all(out):
    """Every job of the run folder: manifest.json, manifest_names.json (U2) and manifest_stage2.json (duplicate checks)."""
    jobs = []
    for name in ("manifest.json", "manifest_names.json", "manifest_stage2.json"):
        p = Path(out) / name
        if p.exists():
            jobs += B.read_json(p)["jobs"]
    return jobs


# ---------------------------------------------------------------- build: frozen split jobs, examples
def _manifest_jobs(d):
    m = B.read_json(Path(d) / "manifest.json")
    return m["jobs"] if isinstance(m, dict) else m


def _csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def copy_split_jobs(out, set_name):
    """Copy the frozen split prompts + schemas of the set to out (job `<ent>_<run>_split_<cid>_r1`); returns (manifest rows, example rows)."""
    src, run = SPLIT_SRC[set_name]
    ex, rows, ex_rows = _csv(src / "examples.csv"), [], []
    for j in _manifest_jobs(src):
        if j.get("kind") != "split" or (run is not None and j.get("run") != run):
            continue
        name = f"{j['ent']}_{RUN_KEY[set_name]}_split_{j['cluster_id'].replace('#', '-')}_r1"
        row = {"job": name, "entity": j["entity"], "ent": j["ent"], "variant": j["variant"], "run_tag": "r1", "kind": "split",
               "cluster_id": j["cluster_id"], "format": "split", "family": "split", "run": RUN_KEY[set_name], "set": set_name,
               "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": SPLIT_MAX_TOKENS}
        for k, ext in (("prompt", ".txt"), ("schema", ".schema.json")):
            (Path(out) / row[k]).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / j[k], Path(out) / row[k])
        row["est_prompt_tokens"] = PIN.est_tokens((Path(out) / row["prompt"]).read_text(encoding="utf-8"))
        stem = j["job"] if j["job"] in set(ex["variant"]) else Path(j["prompt"]).stem
        mine = ex[ex["variant"] == stem]
        if mine.empty:
            raise ValueError(f"{set_name}: no example rows for split job {j['job']} in {src}")
        ex_rows.append(mine.assign(variant=name))
        rows.append(row)
    return rows, ex_rows


def a_example_rows(set_name, jobs):
    """Example rows of the A jobs (variant = job name), best effort: the frozen sources of STEP3.md; a job without rows is skipped."""
    out = []
    for j in jobs:
        path, stem = A_EX_SRC[set_name][int(j["run_tag"][1:])]
        if not path.exists():
            continue
        ex = _csv(path)
        mine = ex[ex["variant"] == stem.format(ent=j["ent"])]
        if len(mine):
            out.append(mine.assign(variant=j["job"]))
    return out


def build_common(out, a_rows, a_examples):
    """Split jobs + examples.csv + manifest.json (A rows first) of a run folder; returns the jobs."""
    out = Path(out)
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    (out / "responses").mkdir(parents=True, exist_ok=True)
    split, ex_rows = [], list(a_examples)
    for s in SETS:
        rows, ex = copy_split_jobs(out, s)
        split += rows
        ex_rows += ex
    pd.concat(ex_rows, ignore_index=True).to_csv(out / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    jobs = list(a_rows) + split
    write_manifest(out, jobs)
    return jobs


def t1b_a_jobs():
    """The 18 option B A jobs (wf_v4.2, results/wf_v42/t1b_step3_keyed) as manifest rows with the set added."""
    jobs = []
    for j in _manifest_jobs(T1B):
        s = "dev50b" if j["run"] == "v22d50b" else "dev50"
        jobs.append({**j, "set": s})
    if len(jobs) != 18:
        raise ValueError(f"expected 18 option B jobs in {T1B}, got {len(jobs)}")
    return jobs


# ---------------------------------------------------------------- bundle (A + split pass) of a run folder
def load_bundle(out, set_name, repairs=None):
    """(shared, {ent: EntityData with variants A s0 / s1 / s2 / A s012}, notes) of the set: run_data_v37.load_a on the run folder (the
    parse repair is on, as in every frozen Step 3 scoring: a list)."""
    run = ROOT / "results" / f"graph_v22_{set_name}"
    shared, data = RD.entity_data(run)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        bundle, notes = RD.load_a(shared, data, Path(out), RUN_KEY[set_name], [] if repairs is None else repairs)
    return shared, bundle, notes


# ---------------------------------------------------------------- stage: reconcile
def split_roles(out, set_name, ent):
    """{(cluster id, raw part name): role} from the split answers of the run folder (the part description, batch_build_v39.split_roles)."""
    res = PV.load_split_results(Path(out) / "responses").get((f"{ent}_{RUN_KEY[set_name]}", "r1"), {})
    return {(cid, p["name"]): p.get("role", "") for cid, obj in res.items() for p in obj.get("parts") or []
            if isinstance(p, dict) and p.get("name")}


def build_reconcile(out, seed=0):
    """Reconcile jobs (2 candidate orders per split part, STEP3.md step 4) on the Llama columns; writes columns.json and the jobs into
    manifest.json (replacing earlier reconcile jobs); returns the new jobs. Reads no GT."""
    out = Path(out)
    BB, BB9 = script("batch_build_v38"), script("batch_build_v39")
    st, tables = BB9.Stage1(out), {}
    for set_name in SETS:
        _, bundle, _ = load_bundle(out, set_name)
        si = BB.SetInput(set_name)
        for ent, (entity, cols) in BB.columns_of({"set": set_name, "lev": bundle}).items():
            attrs = bundle[ent].variants[BB.LABEL].attrs.to_dict("records")
            parts = B9.part_records(cols, attrs, split_roles(out, set_name, ent))
            cent = BT.centroids(cols, si.export.ids, si.export.x)
            tables.setdefault(set_name, {})[ent] = {"entity": entity, "columns": BB9.ser_columns(cols), "parts": parts}
            BB9.build_reconcile(st, si, set_name, ent, entity, cols, parts, cent, seed)
    B.write_json(out / "columns.json", tables)
    write_manifest(out, [j for j in read_manifest(out) if j["family"] != "reconcile"] + st.jobs)
    return st.jobs


# ---------------------------------------------------------------- stage: duplicate check
def build_dupcheck(out, allow_missing=False):
    """Duplicate-check jobs (2 reconcile orders x 3 entities x 2 sets) via batch_stage2_v39.main; writes manifest_stage2.json."""
    mod = script("batch_stage2_v39")
    argv = sys.argv
    sys.argv = ["batch_stage2_v39.py", "--dir", str(out)] + (["--allow-missing"] if allow_missing else [])
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            mod.main()
    finally:
        sys.argv = argv
    return B.read_json(Path(out) / "manifest_stage2.json")["jobs"]


def stage_jobs(out, stage):
    """Jobs of one post stage (reconcile and dupcheck are built from the answers of the stages before them)."""
    if stage == "split":
        return [j for j in read_manifest(out) if j["family"] == "split"]
    if stage == "reconcile":
        return build_reconcile(out)
    if stage == "dupcheck":
        return build_dupcheck(out)
    raise ValueError(f"unknown stage {stage!r}; choose one of {POST_STAGES}")


def run_post(out, llm, stages=POST_STAGES):
    """The post stages in order on backend `llm` (llm.run(out, jobs) -> {"jobs", "run", "parse_errors"}); returns {stage: llm info}."""
    info = {}
    for stage in stages:
        info[stage] = llm.run(out, stage_jobs(out, stage))
        NV.mark_done(out, stage, info[stage])
    return info


# ---------------------------------------------------------------- fake backend (laptop plumbing; no model)
class FakeStep3(NV.FakeLLM):
    """nov16_v41.FakeLLM with valid answers for the Step 3 families: split (every other cluster split in two halves), reconcile (the
    smallest candidate name for half of the parts, the same in both orders), dupcheck (the first two columns), names (U2)."""

    def respond(self, job, prompt, schema):
        self.n_made += 1
        fam, props = job["family"], schema.get("properties", {})
        if fam == "split":
            ex = props["parts"]["items"]["properties"]["examples"]["items"]["enum"]
            mixed = len(ex) >= 4 and zlib.crc32(job["cluster_id"].encode()) % 2 == 0
            h = len(ex) // 2
            parts = [{"name": "fake_part_a", "role": "first", "examples": ex[:h]},
                     {"name": "fake_part_b", "role": "second", "examples": ex[h:]}] if mixed else []
            return json.dumps({"cluster_id": job["cluster_id"], "is_mixed": mixed, "parts": parts})
        if fam in ("reconcile", "dupcheck_rc"):
            if fam == "dupcheck_rc":
                ids = props["joins"]["items"]["properties"]["columns"]["items"]["enum"]
                return json.dumps({"joins": [{"columns": ids[:2], "reason": "fake"}] if len(ids) >= 2 else []})
            names = sorted(props["same_as"]["enum"][:-1])
            pick = names[0] if names and zlib.crc32(job["pid"].encode()) % 2 == 0 else B9.NONE
            return json.dumps({"unit_id": job["pid"], "reason": "fake", "same_as": pick})
        if fam == "names":
            out = {}
            for cid in props:
                n = int(cid.rsplit("#", 1)[1])
                out[cid] = "not_attribute" if n % 7 == 6 else f"fake_attr_{n % 4}"
            return json.dumps(out)
        raise ValueError(f"FakeStep3: no fake answer for family {fam!r}")


# ---------------------------------------------------------------- scoring
def _reused(jobs):
    return {j["job"] for j in jobs if j.get("reused")}


def call_stats(out):
    """{families: {family: {calls, prompt_tokens, output_tokens, max_prompt_tokens, errors, length}}, total over the new calls, reused: n,
    max_prompt_tokens}. Rows of assembled jobs (U2 A, no call) are skipped; reused rows (U0 option B A answers) are counted apart."""
    jobs = {j["job"]: j for j in manifest_all(out)}
    reused = _reused(jobs.values())
    rows = [r for r in LOG.call_rows(out) if r["job"] in jobs and not jobs[r["job"]].get("assembled")]
    fam = {}
    for r in rows:
        if r["job"] in reused:
            continue
        f = jobs[r["job"]]["family"]
        resp = B.last_row(Path(out) / "responses" / f"{r['job']}.jsonl")
        d = fam.setdefault(f, {"calls": 0, "prompt_tokens": 0, "output_tokens": 0, "max_prompt_tokens": 0, "errors": 0, "length": 0})
        d["calls"] += 1
        d["prompt_tokens"] += r["prompt_tokens"] or 0
        d["output_tokens"] += r["output_tokens"] or 0
        d["max_prompt_tokens"] = max(d["max_prompt_tokens"], r["prompt_tokens"] or 0)
        d["errors"] += bool(resp.get("errors"))
        d["length"] += r["finish_reason"] == "length"
    tot = {k: sum(d[k] for d in fam.values()) for k in ("calls", "prompt_tokens", "output_tokens", "errors", "length")}
    tot["max_prompt_tokens"] = max((d["max_prompt_tokens"] for d in fam.values()), default=0)
    reused_rows = [r for r in rows if r["job"] in reused]
    return {"families": fam, "total": tot,
            "reused": {"calls": len(reused_rows), "errors": sum(bool(B.last_row(Path(out) / "responses" / f"{r['job']}.jsonl").get("errors"))
                                                                for r in reused_rows),
                       "length": sum(r["finish_reason"] == "length" for r in reused_rows)}}


def a_name_stats(parsed):
    """Name facts of one A answer (frozen v2 object): declared names no cluster uses, names a cluster uses but never declared, and
    invented "_end"-style names (a name ending in `_end`)."""
    if not isinstance(parsed, dict):
        return {"clusters": 0, "declared": 0, "unused": [], "undeclared": [], "end_names": []}
    declared = [PV.norm_name(a.get("name")) for a in parsed.get("attributes") or [] if isinstance(a, dict) and a.get("name")]
    used = [PV.norm_name(c.get("attribute")) for c in parsed.get("clusters") or [] if isinstance(c, dict) and c.get("attribute")]
    names = set(declared) | set(used)
    return {"clusters": len(used), "declared": len(declared),
            "unused": sorted(set(declared) - set(used)), "undeclared": sorted(set(used) - set(declared) - FREE_NAMES),
            "end_names": sorted(n for n in names if is_end_name(n))}


def a_answer_stats(out):
    """Rows (set, ent, order, ok, n clusters, name facts) of every A job of the run folder (the answers the vote reads)."""
    rows = []
    for j in read_manifest(out):
        if j["family"] != "a":
            continue
        path = Path(out) / "responses" / f"{j['job']}.jsonl"
        objs = PV.load_objects(path) if path.exists() else []
        last = B.last_row(path) or {}
        s = a_name_stats(objs[0] if objs else {})
        rows.append({"set": j["set"], "ent": j["ent"], "order": j["run_tag"], "errors": len(last.get("errors") or []),
                     "finish": last.get("finish_reason", ""), "clusters": s["clusters"], "declared": s["declared"],
                     "unused_names": len(s["unused"]), "undeclared_names": len(s["undeclared"]), "end_names": len(s["end_names"]),
                     "end_name_list": " | ".join(s["end_names"])})
    return pd.DataFrame(rows)


def score(out, sets=SETS):
    """Score the run folder: dashboard rows (found / columns / duplicates ...) of A s012 after the split pass, after reconcile and
    after the duplicate check, plus the stage facts. Writes out/scores/{rows.csv, orders.csv, stats.json, a_answers.csv, calls.json,
    final_columns.json}; returns {"rows", "stats", "calls", "a_answers", "final_columns"}."""
    out = Path(out)
    FV, D, BB, T = script("final_v39"), script("dashboard_v38"), script("batch_build_v38"), script("score_t14_v37")
    from . import dashboard_v38 as DB
    jobs = manifest_all(out)
    rc_jobs = [j for j in jobs if j["family"] == "reconcile"]
    dup_jobs = {(j["set"], j["ent"], j["order_seed"]): j for j in jobs if j["family"] == "dupcheck_rc"}
    tables = B.read_json(out / "columns.json")
    responses = script("score_v38").read_responses(out)
    rows, orders, stats, final_cols = [], [], {}, {}
    for s in sets:
        _, bundle, notes = load_bundle(out, s)
        gt = VD.read_gt_levels(ROOT / T.GT[s] / "gt_levels.csv")
        pb = DB.prepare(s, bundle, gt)
        per_ent, built = BB.columns_of(pb), {}
        st = stats.setdefault(s, {"notes": notes, "entities": {}})
        for ent in ENTS:
            t = tables[s][ent]
            if [(c["cid"], c["name"], c["n_mentions"]) for c in per_ent[ent][1]] != [(c["cid"], c["name"], c["n_mentions"]) for c in t["columns"]]:
                raise ValueError(f"{s} {ent}: columns rebuilt from the answers differ from columns.json (answers changed after the build?)")
            b = built[ent] = FV.entity_columns(s, ent, t, responses, rc_jobs, dup_jobs)
            FV.add_variant(pb, ent, FV.AGREED, SB.final_names(b["acols"]))
            FV.add_variant(pb, ent, FV.FINAL, SB.final_names(b["acols"], b["kept_final"]))
            vo = pb["lev"][ent].variants[BASE]
            marked = vo.dec[vo.dec["action"].isin(PV.MARKED)]
            ments = pb["lev"][ent].mentions
            agree = SB.agreement(b["choice"][0], b["choice"][1])
            moved = Counter(r["status"] for r in b["areport"])
            st["entities"][ent] = {
                "columns_split_pass": len(t["columns"]), "parts": len(t["parts"]),
                "reconcile_agree": list(agree), "reconcile_joined_agreed": moved.get("joined", 0),
                "parts_moved_mentions": sum(len(p["mention_ids"]) for p in t["parts"]
                                            if any(r["pid"] == p["pid"] and r["status"] == "joined" for r in b["areport"])),
                "dup_joins_order0": list(b["n_joins"][0]), "dup_joins_order1": list(b["n_joins"][1]),
                "dup_same_groups_both": len(b["both"]), "dup_on_agreed_columns": len(b["joins_final"]),
                "dup_role_pair_blocked": len(b["rejected_final"]), "dup_joins_kept": len(b["kept_final"]),
                "columns_final": len(b["final"]), "mentions_in_columns": sum(c["n_mentions"] for c in b["final"]),
                "dropped_clusters": len(marked), "dropped_mentions": int(ments["cluster_id"].isin(set(marked["cluster_id"])).sum())}
            final_cols.setdefault(s, {})[ent] = [{k: v for k, v in c.items() if k not in ("pools", "value_types")} | {"entity": t["entity"]}
                                                 for c in b["final"]]
        names = ["A s012 + split pass", FV.AGREED, FV.FINAL]
        df = D.rows_for(pb, [BASE, FV.AGREED, FV.FINAL], names)
        rows.append(df)
        orders.append(D.rows_for(pb, [o for o in ("A s0", "A s1", "A s2") if o in pb["lev"]["train"].variants],
                                 [o for o in ("A s0", "A s1", "A s2") if o in pb["lev"]["train"].variants]))
        st["found_final"] = f"{int(df.iloc[2]['found_total'])}/{int(df.iloc[2]['gold_total'])}"
    res = {"rows": pd.concat(rows, ignore_index=True), "orders": pd.concat(orders, ignore_index=True), "stats": stats,
           "calls": call_stats(out), "a_answers": a_answer_stats(out), "final_columns": final_cols}
    d = out / "scores"
    d.mkdir(exist_ok=True)
    res["rows"].to_csv(d / "rows.csv", index=False, encoding="utf-8", lineterminator="\n")
    res["orders"].to_csv(d / "orders.csv", index=False, encoding="utf-8", lineterminator="\n")
    res["a_answers"].to_csv(d / "a_answers.csv", index=False, encoding="utf-8", lineterminator="\n")
    B.write_json(d / "stats.json", stats)
    B.write_json(d / "calls.json", res["calls"])
    B.write_json(d / "final_columns.json", final_cols)
    return res


def summary_md(res, title):
    """Markdown summary of a score() result."""
    r = res["rows"]
    lines = [f"# {title}", "", "| set | row | found | columns | columns per found | dup columns | wrong columns | review edits | guard |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, x in r.iterrows():
        lines.append(f"| {x['set']} | {x['row']} | {x['found_total']}/{x['gold_total']} ({x['found_train']}+{x['found_hotel']}+"
                     f"{x['found_restaurant']}) | {x['columns']} | {x['columns_per_found']} | {x['dup_columns']} | {x['wrong_columns']} | "
                     f"{x['review_edits']} | {x['guard']} |")
    lines += ["", "## Stage facts", ""]
    for s, st in res["stats"].items():
        for ent, e in st["entities"].items():
            lines.append(f"- {s} {ent}: " + ", ".join(f"{k} {v}" for k, v in e.items()))
    c = res["calls"]
    lines += ["", "## Calls", "", f"New calls {c['total']['calls']}, prompt tokens {c['total']['prompt_tokens']:,}, output tokens "
              f"{c['total']['output_tokens']:,}, largest prompt {c['total']['max_prompt_tokens']:,}; parse errors {c['total']['errors']}, "
              f"cut off (finish length) {c['total']['length']}. Reused A answers (not rerun): {c['reused']}.", ""]
    lines += [f"- {f}: " + ", ".join(f"{k} {v}" for k, v in d.items()) for f, d in c["families"].items()]
    a = res["a_answers"]
    if len(a):
        lines += ["", "## A answers (the vote's input)", "",
                  f"{len(a)} answers; with parse errors {int((a['errors'] > 0).sum())}; cut off {int((a['finish'] == 'length').sum())}; "
                  f"declared names no cluster uses {int(a['unused_names'].sum())}; names used but never declared "
                  f"{int(a['undeclared_names'].sum())}; `_end`-style names {int(a['end_names'].sum())}."]
    return "\n".join(lines) + "\n"
