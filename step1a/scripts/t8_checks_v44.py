"""wf_v4.4 T8 small checks (diary Nov 14): where the 9th table came from, GPU minutes per job, model loading time. No GPU, no LLM.

python scripts/t8_checks_v44.py [--v43 results/wf_v43] [--load results/wf_v44/model_load.json] [--out results/wf_v44/t8]  -> checks.md

1. Table count trace: for every final chain of <v43>/u4 the tables in canonical.json are split into pass-1 tables that kept columns and
   link tables (step4_v43.build_answers makes one for every pair answered "many_to_many"; description "Links X and Y."). MAX_TABLES caps
   only the pass-1 names (step4_v43.p1_names), so link tables come on top of the cap.
2. GPU minutes per job: log_v44.job_seconds = batch_seconds / batch_size of the cached rows (log_v44.call_rows), summed per stage.
   v4.3 rows have a trap: when the guided answer failed and the unguided retry was kept, the row holds the seconds of the single retry call,
   so the guided share of that job is missing. Those jobs are counted (`lost`) and, where the stage has other rows, estimated with the mean
   job seconds of the stage's rows that were not retried (est.); a stage with no such row is "unknown". Rows of v4.4 runs carry both calls.
3. Model loading time: <load> (written by the v4.4 notebook, log_v44.save_load_time), else "not logged".
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

STAGES = (("step3 A answers", r"_a_v22d50b?_s\d$"), ("step3 names", r"_names_"), ("step3 split", r"_split_"), ("step3 reconcile", r"^reconcile_"),
          ("step3 dupcheck", r"^dupcheck_"), ("step4 pass 1 (tables)", r"_p1$"), ("step4 pass 2 (assign)", r"_p2$"),
          ("step4 pairs (links)", r"_r\d+_\d+$"), ("step4 keys", r"_k\d+$"))
LINK_DESC = "Links "          # description of a table made from a many_to_many answer (step4_v43.build_answers)


def stage_of(job):
    """Stage name of a job name (first pattern of STAGES that matches), else "other"."""
    return next((name for name, pat in STAGES if re.search(pat, str(job))), "other")


def set_of(job):
    """dev50 / dev50b / other of a job name (cost_v43.set_of)."""
    from s1a import cost_v43 as C
    return C.set_of(job)


# ---------------------------------------------------------------- 2. GPU minutes per job
def per_job_table(rows, by_set=False):
    """Rows of call rows (log_v44.call_rows) grouped by stage (and set): jobs, retried, lost, seconds (sum of job_seconds), est_lost_seconds
    (None = unknown), minutes (seconds + estimate), mean_job_seconds. Rows with no seconds (assembled, no call) are left out and counted in
    `no_seconds`. A retried row without guided_finish_reason lost the guided share of its job (v4.3 rows)."""
    groups = defaultdict(list)
    for r in rows:
        groups[(stage_of(r["job"]), set_of(r["job"]) if by_set else "both")].append(r)
    out = []
    for (stage, s), rs in groups.items():
        timed = [r for r in rs if r["job_seconds"] is not None]
        lost = [r for r in timed if r["retried"] and r.get("guided_finish_reason") is None]
        clean = [r["job_seconds"] for r in timed if not (r["retried"] and r.get("guided_finish_reason") is None)]
        secs = sum(r["job_seconds"] for r in timed)
        est = round(len(lost) * sum(clean) / len(clean), 1) if lost and clean else (0.0 if not lost else None)
        out.append({"stage": stage, "set": s, "jobs": len(timed), "no_seconds": len(rs) - len(timed), "retried": sum(bool(r["retried"]) for r in timed),
                    "lost": len(lost), "seconds": round(secs, 1), "est_lost_seconds": est,
                    "minutes": round((secs + (est or 0)) / 60, 2), "mean_job_seconds": round(secs / len(timed), 2) if timed else None})
    return sorted(out, key=lambda x: ([n for n, _ in STAGES].index(x["stage"]) if x["stage"] != "other" else 99, x["set"]))


def batch_once_seconds(rows):
    """The old estimate (cost_v43.gpu_seconds): each batch counted once, for comparison."""
    from s1a import cost_v43 as C
    return C.gpu_seconds([r for r in rows if "fake" not in r["file"].split("/")])


# ---------------------------------------------------------------- 1. the 9th table
def table_origin(canonical, repairs, p1_tables, cap):
    """dict for one chain: tables (in the final canonical), pass1 (names asked), cap_kept (names after the cap), dropped_empty (pass-1 tables with
    no column after pass 2: repair p2_empty_table), kept_pass1 (pass-1 tables in the result), links (tables made from many_to_many answers), over_cap."""
    tables = canonical["tables"]
    links = [t["name"] for t in tables if str(t.get("description", "")).startswith(LINK_DESC)]
    dropped = repairs.get("counts", {}).get("p2_empty_table", 0)
    return {"tables": len(tables), "pass1": len(p1_tables), "cap_kept": min(len(p1_tables), cap), "dropped_empty": dropped,
            "kept_pass1": len(tables) - len(links), "links": links, "over_cap": len(tables) > cap}


def lineno(path, text):
    """Line numbers (1-based) of the lines of a file that contain `text`."""
    return [i for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1) if text in line]


def chain_origins(u4, cap):
    """{chain: table_origin} of every final chain under u4/final (needs responses/<chain>_p1.jsonl for the pass-1 names)."""
    out = {}
    for d in sorted((Path(u4) / "final").glob("*")):
        if not (d / "canonical.json").exists():          # status.json and other files of the final folder
            continue
        p1 = Path(u4) / "responses" / f"{d.name}_p1.jsonl"
        rows = [json.loads(x) for x in p1.read_text(encoding="utf-8").splitlines() if x.strip()] if p1.exists() else []
        names = (json.loads(rows[-1]["raw"]).get("tables") or []) if rows and not rows[-1].get("errors") else []
        out[d.name] = table_origin(json.loads((d / "canonical.json").read_text(encoding="utf-8")),
                                   json.loads((d / "repairs.json").read_text(encoding="utf-8")), names, cap)
    return out


def md_table(rows, fields):
    return "\n".join(["| " + " | ".join(fields) + " |", "|" + "---|" * len(fields)]
                     + ["| " + " | ".join("" if r.get(k) is None else str(r.get(k)) for k in fields) + " |" for r in rows]) + "\n"


def load_report(path):
    """One line: the model loading time of a v4.4 run, or "not logged"."""
    from s1a import log_v44 as L
    d = L.load_time(path)
    return "not logged" if d is None else f"{d['load_seconds']} s ({d['load_seconds'] / 60:.1f} min), {d.get('model', '')} {d.get('revision', '')}, logged {d.get('logged_at', '')}"


def main():
    from s1a import log_v44 as L
    from s1a import step4_v43 as S4
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--v43", type=Path, default=ROOT / "results" / "wf_v43")
    ap.add_argument("--load", type=Path, default=ROOT / "results" / "wf_v44" / "model_load.json")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v44" / "t8")
    a = ap.parse_args()
    origins = chain_origins(a.v43 / "u4", S4.MAX_TABLES)
    src = ROOT / "s1a" / "step4_v43.py"
    over = {k: v for k, v in origins.items() if v["over_cap"]}
    md = ["# T8: small checks (v4.3 results, wf_v4.4 diary)\n", "## 1. The 9th table\n",
          f"`MAX_TABLES = {S4.MAX_TABLES}` caps the pass-1 table names only (`step4_v43.p1_names`, line {lineno(src, 'names = names[:MAX_TABLES]')[0]}). "
          "The final schema adds one link table for every pair that Llama answers `many_to_many` "
          f"(`step4_v43.build_answers`, `new_tables.append(...)`, line {lineno(src, 'new_tables.append')[0]}, after the cap). "
          "A link table is not a repair and not a key table. Tables per chain (`links` = tables with description \"Links X and Y.\"):\n",
          md_table([{"chain": k, **{f: (", ".join(v[f]) if f == "links" else v[f]) for f in
                                    ("tables", "pass1", "cap_kept", "dropped_empty", "kept_pass1", "links", "over_cap")}} for k, v in origins.items()],
                   ["chain", "tables", "pass1", "cap_kept", "dropped_empty", "kept_pass1", "links", "over_cap"])]
    for k, v in over.items():
        md.append(f"**{k}**: pass 1 gave {v['pass1']} names (cap {S4.MAX_TABLES}), {v['dropped_empty']} table(s) got no column in pass 2 and were dropped "
                  f"(p2_empty_table), leaving {v['kept_pass1']}; the pair questions answered many_to_many twice and added the link tables "
                  f"{', '.join(v['links'])}: {v['kept_pass1']} + {len(v['links'])} = {v['tables']}.\n")
    md.append("## 2. GPU minutes per job (batch_seconds / batch_size)\n")
    for name in ("u0", "u2", "u4"):
        rows = L.call_rows(a.v43 / name) if (a.v43 / name).exists() else []
        rows = [r for r in rows if "fake" not in r["file"].split("/")]
        if not rows:
            md.append(f"### {name}: no rows\n")
            continue
        tab = per_job_table(rows)
        tot = sum(t["minutes"] for t in tab)
        md += [f"### {name}\n", md_table(tab, ["stage", "jobs", "no_seconds", "retried", "lost", "seconds", "est_lost_seconds", "minutes", "mean_job_seconds"]),
               f"Total {tot:.2f} min over {sum(t['jobs'] for t in tab)} timed jobs (unknown estimates count 0); batch-once estimate of cost_v43: "
               f"{batch_once_seconds(rows) / 60:.2f} min.\n", f"Per set: " + "; ".join(
                   f"{t['stage']} {t['set']} {t['minutes']} min" for t in per_job_table(rows, by_set=True) if t["set"] != "other") + "\n"]
    md += ["`lost` = retried jobs whose guided share is missing in the v4.3 rows (the kept row is the single unguided retry); `est_lost_seconds` = "
           "lost x mean seconds of the stage's other rows, empty = unknown (every job of the stage was retried, so its guided batch time is not "
           "in any row). The minutes are therefore a lower bound for the names stage. The v4.4 backend (`log_v44.VllmBackend44`) keeps both calls.\n",
           "## 3. Model loading time\n", f"{load_report(a.load)} (file `{a.load.relative_to(ROOT).as_posix() if a.load.is_relative_to(ROOT) else a.load}`)\n"]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "checks.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("T8 written to", a.out / "checks.md", "| chains over cap:", list(over))


if __name__ == "__main__":
    main()
