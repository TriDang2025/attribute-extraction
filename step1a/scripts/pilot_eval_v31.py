"""wf_v3.1 Step-3 pilot evaluation (PILOT_V31_CONTRACT.md): responses -> decisions, verification, scores.

python scripts/pilot_eval_v31.py --run results/graph_v22_dev50 --dir results/loop1_v31 [--no-gliner]
Reads <dir>/manifest.json, <dir>/examples.csv, <dir>/responses/<job>.jsonl (entity jobs) and
<dir>/responses/<ent>_split_<cid>_<tag>.jsonl (split pass). For every entity job it scores the response as is and
again after name_merge ("+namemerge"). v1 responses go through decisions_table, v2 through decisions_from_v2 (with
the split results of the same run tag, else the first tag found for that entity).
Writes <dir>/{scores_<ent>.md, decisions.csv, verification.csv, name_rubric.csv, summary.md}. name_rubric.csv keeps
the hand-filled columns on re-runs; its names are the responses as is (no "+namemerge" rows).
GLiNER outputs are cached per entity and label in <dir>/gliner_cache/<ent>/; --no-gliner skips verification (no GLiNER load).
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402

GOLD_ENTS = {"train": ["train"], "hotel": ["hotel"], "restaurant": ["restaurant", "taxi"]}
VARIANT_ORDER = ["nohints", "nohints_long", "v2", "v2_hints", "v2_nocontext"]
SUMMARY_COLS = ["merge_pure", "merge_frag", "split_done", "split_side", "noise_marked", "noise_kept", "place_right",
                "recall_after", "p1_after", "j_right", "j_wrong", "j_right_desc", "j_wrong_desc", "real_acc",
                "noise_rub", "role_acc"]


def _read(path, **kw):
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8", **kw)


def _write(df, path):
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def _order(label):
    variant, tag = label.rsplit(" ", 1)
    base = variant.replace("+namemerge", "")
    return (VARIANT_ORDER.index(base) if base in VARIANT_ORDER else len(VARIANT_ORDER), base, "+namemerge" in variant, tag)


def _examples(path, cids):
    """examples.csv rows of these clusters, one per ex_id; warns when one ex_id points at different mentions."""
    ex = _read(path)
    ex = ex[ex["cluster_id"].isin(cids)]
    bad = ex.groupby("ex_id")["mention_id"].nunique()
    if (bad > 1).any():
        print(f"WARNING: ex_ids with different mentions across variants: {sorted(bad[bad > 1].index)[:5]}", file=sys.stderr)
    return ex.drop_duplicates("ex_id")


def _check_row(path):
    """Warn when the last response row has parse errors or was cut off; print its model."""
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    if not rows:
        return
    r = rows[-1]
    print(f"{path.name}: model {r.get('model')} rev {str(r.get('revision', ''))[:8]} guided {r.get('guided', '')} "
          f"finish {r.get('finish_reason', '')}")
    if r.get("errors") or r.get("finish_reason") == "length":
        print(f"WARNING: {path.name}: {len(r.get('errors') or [])} parse errors, finish {r.get('finish_reason')}: "
              f"{(r.get('errors') or [])[:3]}", file=sys.stderr)


def _decisions(job, path, cids, split_all):
    _check_row(path)
    variant, tag = job["variant"], job["run_tag"]
    if job["format"] == "v2":
        objs = PV.load_objects(path)
        by_tag = split_all.get(job["ent"], {})
        split = by_tag.get(tag) or (by_tag[sorted(by_tag)[0]] if by_tag else None)
        return PV.decisions_from_v2(objs[0] if objs else {}, cids, variant, tag, split, require_mixed=False)
    return PV.decisions_table(PV.load_objects(path), cids, variant, tag)


def score_entries(entries, e, docs, ctx, entity, extract, cache_dir, gold_ents):
    """Score {(variant, run_tag): (decision table, format)} of one entity with the unchanged scorer.
    Returns ({(variant, run_tag): (dec, attrs, assign, parts)}, {"<variant> <run_tag>": score_file output + *_desc})."""
    final, ver_name, ver_desc = {}, {}, {}
    for (variant, tag), (d, fmt) in entries.items():
        assign, attrs, parts = PV.final_attributes(d, e.mentions, e.ids, e.x, ctx.examples, entity)
        final[(variant, tag)] = (d, attrs, assign, parts)
        empty = pd.DataFrame(columns=PV.VERIFY_COLS)
        ver_name[(variant, tag)] = empty if extract is None else PV.verify(
            attrs, assign, e.mentions, docs, e.instances, entity, extract, cache_dir, variant, tag)
        ver_desc[(variant, tag)] = empty.assign(label_kind="description") if extract is None or fmt != "v2" else PV.verify(
            attrs, assign, e.mentions, docs, e.instances, entity, extract, cache_dir, variant, tag, use_description=True)
    names = PS.apply_manual(PS.name_check_table({k: (v[1], v[2]) for k, v in final.items()}, e.mentions, gold_ents))
    results = {}
    for (variant, tag), (d, attrs, assign, parts) in final.items():
        r = PS.score_file(d, attrs, assign, parts, ctx, ver_name[(variant, tag)], names)
        for k, v in PS._verification_checks(ver_desc[(variant, tag)], names).items():  # description label
            r[k + "_desc"], r[k + "_desc_n"] = v
        results[f"{variant} {tag}"] = r
    return final, results, ver_name, ver_desc


def summary_rows(ent, results, sheet):
    """One summary dict per scored response label of one entity (SUMMARY_COLS + the rubric accuracies)."""
    acc = PS.rubric_accuracy(sheet)
    rows = []
    for label, r in results.items():
        variant, tag = label.rsplit(" ", 1)
        ra = acc.get((variant, tag), {})
        rows.append({"ent": ent, "variant": variant, "run_tag": tag, **{k: r.get(k) for k in SUMMARY_COLS},
                     "real_acc": ra.get("real_acc"), "noise_rub": ra.get("noise_marked"), "role_acc": ra.get("role_acc")})
    return rows


def summary_table(summary):
    """Markdown lines of the summary table (rows from summary_rows)."""
    lines = ["| ent | variant | run | " + " | ".join(SUMMARY_COLS) + " |", "|---|---|---|" + "---|" * len(SUMMARY_COLS)]
    for r in summary:
        lines.append(f"| {r['ent']} | {r['variant']} | {r['run_tag']} | "
                     + " | ".join(PS._fmt(r[c], c == "noise_kept") for c in SUMMARY_COLS) + " |")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--no-gliner", action="store_true")
    a = ap.parse_args()

    e = MN.load(a.run / "spans")
    docs, gv, gold_attrs = MN.load_shared(a.run)
    labels = _read(a.run / "spans" / "labels.csv")
    clusters = _read(a.run / "spans" / "clusters.csv")
    manifest = json.loads((a.dir / "manifest.json").read_text(encoding="utf-8"))
    jobs = [j for j in (manifest["jobs"] if isinstance(manifest, dict) else manifest) if j.get("kind") == "entity"]
    split_all = {}
    for (ent, tag), objs in PV.load_split_results(a.dir / "responses").items():
        split_all.setdefault(ent, {})[tag] = objs
    old_rubric = _read(a.dir / "name_rubric.csv") if (a.dir / "name_rubric.csv").exists() else None
    extract = None if a.no_gliner else PV.gliner_extractor()

    all_dec, all_ver, all_rub, summary = [], [], [], []
    for ent in dict.fromkeys(j["ent"] for j in jobs):
        entity = next(j["entity"] for j in jobs if j["ent"] == ent)
        cids = sorted(c for c in e.mentions.loc[e.mentions["entity"] == entity, "cluster_id"].unique() if c)
        examples = _examples(a.dir / "examples.csv", cids)
        gold_ents = GOLD_ENTS.get(ent, [ent])
        ctx = PS.Ctx(e.mentions, labels, gv, gold_attrs, e.ids, e.x, examples, entity, gold_ents)
        decs, entries = {}, {}
        for job in (j for j in jobs if j["ent"] == ent):
            path = a.dir / "responses" / f"{job['job']}.jsonl"
            if not path.exists():
                print(f"missing response {path.name}", file=sys.stderr)
                continue
            dec = _decisions(job, path, cids, split_all)
            for d in (dec, PS.name_merge(dec, e.mentions, entity)):
                decs[f"{d['variant'].iloc[0]} {job['run_tag']}"] = d
                entries[(d["variant"].iloc[0], job["run_tag"])] = (d, job["format"])
        if not entries:
            continue
        final, results, ver_name, ver_desc = score_entries(entries, e, docs, ctx, entity, extract, a.dir / "gliner_cache" / ent, gold_ents)
        results = {k: results[k] for k in sorted(results, key=_order)}
        raw = {k: (v[1], v[2]) for k, v in final.items() if "+namemerge" not in k[0]}
        sheet = PS.rubric_sheet(raw, e.mentions, labels, clusters, old_rubric)
        stab = PS.stability(decs["v2 r1"], decs["v2 r2"]) if "v2 r1" in decs and "v2 r2" in decs else None
        note = f"{len(cids)} clusters, {len(ctx.train)} gold classes ({', '.join(gold_ents)})."
        (a.dir / f"scores_{ent}.md").write_text(
            PS.render_scores(results, stab, entity, note, rubric=sheet, pair=("v2", "v2_nocontext"),
                             stab_pair=("v2 r1", "r2")), encoding="utf-8", newline="\n")
        summary += summary_rows(ent, results, sheet)
        all_dec += [d.assign(ent=ent) for d in decs.values()]
        all_ver += [v.assign(ent=ent, label_kind="name") for v in ver_name.values() if len(v)]
        all_ver += [v.assign(ent=ent) for v in ver_desc.values() if len(v)]
        all_rub.append(sheet)

    if not summary:
        sys.exit(f"no responses for the manifest jobs in {a.dir / 'responses'}")
    _write(pd.concat(all_dec), a.dir / "decisions.csv")
    _write(pd.concat(all_ver) if all_ver else pd.DataFrame(columns=PV.VERIFY_COLS), a.dir / "verification.csv")
    _write(pd.concat(all_rub), a.dir / "name_rubric.csv")
    lines = ["# wf_v3.1 pilot summary", "", f"Run `{a.run}`. Targets and per-check blocks in scores_<ent>.md; "
             "`+namemerge` = same response after merging same-name, same-placement clusters; j_*_desc = GLiNER with the "
             "description as label (v2 only); real_acc / noise_rub / role_acc come from the filled name rubric.", ""]
    lines += summary_table(summary)
    (a.dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote scores_<ent>.md, decisions.csv, verification.csv, name_rubric.csv, summary.md in {a.dir}")


if __name__ == "__main__":
    main()
