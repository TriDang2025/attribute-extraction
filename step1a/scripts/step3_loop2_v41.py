"""wf_v4.1 Step 3 naming for loop 2: build the frozen Step 3 A prompts (orders s0, s1, s2) for loop-2 clusters (adapter: s1a/step3_loop2_v41.py).

python scripts/step3_loop2_v41.py --set dev50 [--include-dropped] [--seed 0]
  -> results/wf_v41/step3_loop2/<set>/{prompts/<job>.txt + .schema.json, manifest.json, examples.csv, check.md}
python scripts/step3_loop2_v41.py --set dev50 --check
  -> reads responses/<job>.jsonl (after scripts/dryrun_v41.py --dir <that folder>), applies the frozen decisions_from_v2 and the
     3-order vote, writes answers.md (cluster, name given, action, placement).
Input: results/wf_v41/loop2/<set>/clusters.json (scripts/loop2_v41.py) and the loop-1 run results/graph_v22_<set>/ (read only).
Only the kept loop-2 clusters go to Step 3; --include-dropped sends all clusters and marks the manifest (dry run only).
python scripts/step3_loop2_v41.py --set dev50 --dupcheck        (diary Nov 7 task 6; after the Step 3 responses)
  -> prompts/dupcheck_l2_<set>_<ent>_o{0,1}.txt + .schema.json, manifest_dupcheck.json, new_columns.json (s1a/dupcheck_l2_v41.py)
python scripts/step3_loop2_v41.py --set dev50 --dupcheck-apply  (after the duplicate-check responses)
  -> columns_l2.json (final new columns; duplicates of old handover columns marked), dupcheck.md
Jobs: <ent>_a_l2_<set>_s{0,1,2}, family "a", format "v2"; dupcheck_l2_<set>_<ent>_o{0,1}, family "dupcheck_l2", format "dupcheck".
Every job has a schema file for guided JSON (tests/test_step3_loop2_v41.py checks it); llm_cache.parse_job parses the answers.
No encoder, no LLM.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from s1a import llm_cache as LC  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import dupcheck_l2_v41 as DL  # noqa: E402
from s1a import step3_loop2_v41 as S3  # noqa: E402
from pilot_build_v31 import TOKEN_LIMIT, max_tokens  # noqa: E402
from pilot_build_v37 import ORDERS, RunInput, a_prompts  # noqa: E402

SEEDS = ORDERS
DUP_MAX_TOKENS = 1024   # STEP3.md, duplicate check


RUN_ROOT = None   # the Nov 16 run (scripts/nov16_v41.py) sets its run folder; default results/wf_v41


def run_root():
    return RUN_ROOT or paths.RESULTS / "wf_v41"


def out_dir(set_name):
    return run_root() / "step3_loop2" / set_name


def job_name(ent, set_name, s):
    return f"{ent}_a_l2_{set_name}_s{s}"


def job_row(ent, entity, set_name, s, k, include_dropped, n_tokens):
    """Manifest row of one A job: the keys of the frozen A rows (pilot_build_v37) plus the loop-2 marks."""
    name = job_name(ent, set_name, s)
    return {"job": name, "entity": entity, "ent": ent, "variant": "v2", "run_tag": f"s{s}", "kind": "entity", "stage": 1,
            "nbhd": None, "cluster_id": "", "format": "v2", "round": 0, "carry_from": [], "family": "a",
            "run": f"l2_{set_name}", "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
            "max_tokens": max_tokens(n_tokens), "loop2": True, "include_dropped": include_dropped}


def check_md(set_name, include_dropped, stat_rows, cluster_rows, notes):
    head = [f"# Step 3 naming for loop 2, {set_name}", ""]
    if include_dropped:
        head += ["**DRY RUN INPUT: --include-dropped. Dropped loop-2 clusters are in the prompts; the real input is the kept "
                 "clusters only.**", ""]
    return "\n".join(head + [
        "Frozen Step 3 A prompt (pilot_input.INSTRUCTION_V2 + render_v2 + schema_v2), orders s0 / s1 / s2, no frozen code changed. "
        "Tokens are chars / 3.5.", "",
        "| job | entity | k | clusters | chars | est. prompt tokens | status |", "|---|---|---|---|---|---|---|", *stat_rows, "",
        "| cluster | label | loop-2 keep | mentions | distinct values | reason |", "|---|---|---|---|---|---|", *cluster_rows, "",
        *notes, ""])


def build(a):
    set_name, odir = a.set, out_dir(a.set)
    clusters = json.loads((run_root() / "loop2" / set_name / "clusters.json").read_text(encoding="utf-8"))
    chosen = S3.select_clusters(clusters, a.include_dropped)
    notes = [f"Clusters in clusters.json: {len(clusters)}; sent to Step 3: {len(chosen)} "
             f"({'all with spans' if a.include_dropped else 'kept only'})."]
    if not chosen:
        sys.exit("no loop-2 cluster to send (none kept; use --include-dropped for a dry run)")
    base = RunInput(f"results/graph_v22_{set_name}", a.seed)       # loop 1, read only
    merged = S3.merge_mentions(base.export.mentions, chosen)       # a copy; mentions.csv on disk is not touched
    ri = S3.Loop2Run(base, merged, chosen, a.seed)
    (odir / "prompts").mkdir(parents=True, exist_ok=True)
    jobs, ex_rows, stat_rows = [], [], []
    for ent in dict.fromkeys(c["entity"] for c in chosen):
        mine = [c for c in chosen if c["entity"] == ent]
        entity, k, inp, texts = a_prompts(ri, ent)
        if entity != mine[0]["stage1_entity"]:
            raise ValueError(f"{ent}: find_pilot_entity gave {entity}, loop 2 says {mine[0]['stage1_entity']}")
        for s in SEEDS:
            name = job_name(ent, set_name, s)
            (odir / "prompts" / f"{name}.txt").write_text(texts[s], encoding="utf-8", newline="\n")
            (odir / "prompts" / f"{name}.schema.json").write_text(json.dumps(PIN.schema_v2(inp), indent=1), encoding="utf-8", newline="\n")
            n = PIN.est_tokens(texts[s])
            jobs.append(job_row(ent, entity, set_name, s, k, a.include_dropped, n))
            ex_rows.extend((ex, entity, ci.cluster_id, mid, name) for ci in inp.clusters for ex, mid in ci.examples)
            stat_rows.append(f"| {name} | {entity} ({ent}) | {k} | {len(inp.clusters)} | {len(texts[s])} | {n} | "
                             f"{'OVER LIMIT' if n >= TOKEN_LIMIT else 'ok'} |")
        print(f"{ent}: entity {entity}, {len(inp.clusters)} clusters, k {k}", flush=True)
    manifest = {"set": set_name, "include_dropped": a.include_dropped,
                "note": "DRY RUN INPUT: dropped clusters included" if a.include_dropped else "kept loop-2 clusters only",
                "jobs": jobs}
    (odir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    pd.DataFrame(ex_rows, columns=["ex_id", "entity", "cluster_id", "mention_id", "variant"]).to_csv(
        odir / "examples.csv", index=False, encoding="utf-8", lineterminator="\n")
    cl_rows = [f"| {c['id']} | {c['label']} | {'keep' if c['keep'] else 'drop'} | {c['n_mentions']} | "
               f"{merged[merged['cluster_id'] == c['id']]['norm_value'].nunique()} | {c['reason'].replace('|', '/')} |"
               for c in chosen]
    (odir / "check.md").write_text(check_md(set_name, a.include_dropped, stat_rows, cl_rows, notes), encoding="utf-8", newline="\n")
    print("\n".join(stat_rows))
    if any("OVER LIMIT" in r for r in stat_rows):
        print(f"WARNING: a prompt is over {TOKEN_LIMIT} estimated tokens", file=sys.stderr)


def check(a):
    """Frozen decisions_from_v2 per order + PC.vote over the answers of each entity; writes answers.md."""
    odir = out_dir(a.set)
    manifest = json.loads((odir / "manifest.json").read_text(encoding="utf-8"))
    clusters = read_clusters(a.set)
    lines = [f"# Step 3 naming for loop 2, {a.set}: answers", ""]
    if manifest["include_dropped"]:
        lines += ["**DRY RUN: dropped clusters were in the prompts; answers from a dry-run model are not a result.**", ""]
    lines += ["| cluster | label | loop-2 keep | name given | action | placement |", "|---|---|---|---|---|---|"]
    for ent in dict.fromkeys(j["ent"] for j in manifest["jobs"]):
        dec, stats, cids, missing = voted(odir, manifest, ent)
        lines += [f"| {ent} {j['run_tag']} | no response in responses/{j['job']}.jsonl | | | |" for j in missing]
        if dec is None:
            continue
        for r in S3.answer_rows(dec, [clusters[c] for c in cids]):
            lines.append(f"| {r['cluster']} | {r['label']} | {'keep' if r['keep'] else 'drop'} | {r['name']} | {r['action']} | "
                         f"{r['placement']} |")
        lines.append(f"| {ent}: {stats['n_orders']} orders | | | | agree_mean {stats['agree_mean']:.2f}, ties {stats['ties']} | |")
    (odir / "answers.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


def voted(odir, manifest, ent):
    """(voted decision table or None, vote stats + n_orders, cluster ids, [jobs without a response]) of one entity: the frozen
    decisions_from_v2 per order and PC.vote over the orders that have a response."""
    tables, cids, missing = [], None, []
    for j in sorted((j for j in manifest["jobs"] if j["ent"] == ent), key=lambda j: j["run_tag"]):
        obj = PC.load_obj(odir, j)
        ids = LC.schema_enum(PC._schema(odir, j), "cluster_id")
        if obj is None:
            missing.append(j)
            continue
        tables.append(S3.order_table(obj, ids, j["run_tag"]))
        cids = ids
    if not tables:
        return None, None, cids, missing
    dec, stats = S3.voted_table(tables)
    return dec, {**stats, "n_orders": len(tables)}, cids, missing


def read_clusters(set_name):
    return {c["id"]: c for c in json.loads((run_root() / "loop2" / set_name / "clusters.json").read_text(encoding="utf-8"))}


# ------------------------------------------------------------------ duplicate check after Step 3 (diary Nov 7 task 6)
def dup_job_name(ent, set_name, o):
    return f"dupcheck_l2_{set_name}_{ent}_o{o}"


def dupcheck_build(a):
    """Duplicate-check prompts (frozen v3.8 prompt, 2 orders) over the old handover columns + the new columns named by the voted Step 3
    answer; writes prompts/dupcheck_l2_*.txt + .schema.json, manifest_dupcheck.json and new_columns.json. An entity with no new column
    gets no job. Stops when a Step 3 response is missing."""
    from s1a import step4_inputs as I
    odir = out_dir(a.set)
    manifest = json.loads((odir / "manifest.json").read_text(encoding="utf-8"))
    clusters, handover = read_clusters(a.set), I.load_handover(a.set, paths.ROOT)
    jobs, cols = [], {}
    for ent in dict.fromkeys(j["ent"] for j in manifest["jobs"]):
        dec, _, _, missing = voted(odir, manifest, ent)
        if missing:
            sys.exit(f"STOP: Step 3 responses missing: {[j['job'] for j in missing]}")
        old = DL.old_columns(handover[ent])
        new = DL.new_columns(dec, clusters, max(c["cid"] for c in old) + 1)
        cols[ent] = {"old": old, "new": new}
        if not new:
            continue
        for o, (text, schema) in DL.prompts(old, new, f"{a.set}/{ent}").items():
            name = dup_job_name(ent, a.set, o)
            (odir / "prompts" / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
            (odir / "prompts" / f"{name}.schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8", newline="\n")
            jobs.append({"job": name, "ent": ent, "entity": handover[ent]["stage1_entity"], "family": "dupcheck_l2", "format": "dupcheck",
                         "order_seed": o, "run_tag": f"o{o}", "stage": 2, "round": 0, "carry_from": [], "prompt": f"prompts/{name}.txt",
                         "schema": f"prompts/{name}.schema.json", "max_tokens": DUP_MAX_TOKENS, "n_columns": len(old) + len(new),
                         "est_prompt_tokens": PIN.est_tokens(text)})
    (odir / "manifest_dupcheck.json").write_text(json.dumps({"set": a.set, "jobs": jobs}, indent=1), encoding="utf-8", newline="\n")
    (odir / "new_columns.json").write_text(json.dumps(cols, indent=1), encoding="utf-8", newline="\n")
    print(f"{len(jobs)} duplicate-check jobs; new columns: " + ", ".join(f"{e} {len(c['new'])}" for e, c in cols.items()))


def dupcheck_apply(a):
    """Reads the duplicate-check responses; writes columns_l2.json (final new columns per entity, duplicates marked) and dupcheck.md."""
    odir = out_dir(a.set)
    jobs = json.loads((odir / "manifest_dupcheck.json").read_text(encoding="utf-8"))["jobs"]
    cols = json.loads((odir / "new_columns.json").read_text(encoding="utf-8"))
    missing = [j["job"] for j in jobs if PC.load_obj(odir, j) is None]
    if missing:
        sys.exit(f"STOP: duplicate-check responses missing: {missing}")
    final = {ent: DL.resolve(c["old"], c["new"], [PC.load_obj(odir, j) for j in jobs if j["ent"] == ent]) for ent, c in cols.items()}
    (odir / "columns_l2.json").write_text(json.dumps(final, indent=1), encoding="utf-8", newline="\n")
    lines = [f"# Loop 2 duplicate check, {a.set}", "",
             "Frozen v3.8 prompt, 2 orders; a duplicate needs the same name as an old column or a join with it in both orders.", "",
             "| entity | new column | clusters | status | duplicate of | reason | joined |", "|---|---|---|---|---|---|---|"]
    for ent, rows in final.items():
        lines += [f"| {ent} | {r['name']} | {', '.join(r['clusters'])} | {r['status']} | {', '.join(r['duplicate_of'])} | {r['reason']} | "
                  f"{', '.join(r['joined'])} |" for r in rows]
    (odir / "dupcheck.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", default="dev50", choices=["dev50", "dev50b"])
    ap.add_argument("--include-dropped", action="store_true", help="dry run: send dropped clusters too")
    ap.add_argument("--seed", type=int, default=0, help="example-selection seed")
    ap.add_argument("--check", action="store_true", help="read the responses and write answers.md")
    ap.add_argument("--dupcheck", action="store_true", help="build the duplicate-check jobs from the Step 3 answers")
    ap.add_argument("--dupcheck-apply", action="store_true", help="read the duplicate-check responses, write columns_l2.json")
    a = ap.parse_args()
    if a.dupcheck_apply:
        dupcheck_apply(a)
    elif a.dupcheck:
        dupcheck_build(a)
    else:
        check(a) if a.check else build(a)


if __name__ == "__main__":
    main()
