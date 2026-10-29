"""wf_v3.2 Step-3 pilot evaluation (PILOT_V32_CONTRACT.md): variants A-D scored per entity with the unchanged scorer.

python scripts/pilot_eval_v32.py --run results/graph_v22_dev50 --dir results/loop1_v32 [--dir31 results/loop1_v31] [--no-gliner]
A = wf_v3.1 v2 r1 + its split pass (read from --dir31, no new run); B = nbhd, seed 0, + split pass; C = nbhd in seeds
0-2, majority vote, + split pass; D = C + noise probe + coherence gate + reconcile (s1a.pilot_combine.decisions_d).
Each variant is scored as is and again after name_merge ("+namemerge"). Reads <dir>/manifest.json, examples.csv,
responses/<job>.jsonl; <dir31> as in pilot_eval_v31.py. A variant whose responses are missing is skipped with a note.
Writes <dir>/{scores_<ent>.md, decisions.csv, verification.csv, name_rubric.csv, tokens.csv, summary.md}.
Recall per 100K tokens uses recall_after of the "+namemerge" row. GLiNER cache: <dir>/gliner_cache; --no-gliner skips it.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from pilot_eval_v31 import (GOLD_ENTS, _decisions, _examples, _read, _write,  # noqa: E402
                            score_entries, summary_rows, summary_table)

SEEDS = (0, 1, 2)
TAG = {"A": "r1", "B": "s0", "C": "s012", "D": "s012"}


def _jobs(dir):
    manifest = json.loads((dir / "manifest.json").read_text(encoding="utf-8"))
    return manifest["jobs"] if isinstance(manifest, dict) else manifest


def _have(dir, jobs):
    """True when there is at least one job and every job has a response file."""
    return bool(jobs) and all((dir / "responses" / f"{j['job']}.jsonl").exists() for j in jobs)


def _objs(dir, jobs, kind):
    """{cluster_id: parsed response} of the jobs of this kind (missing or failed responses left out)."""
    out = {}
    for j in jobs:
        if j["kind"] == kind:
            o = PC.load_obj(dir, j)
            if o is not None:
                out[j["cluster_id"]] = o
    return out


def _last_row(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    return rows[-1] if rows else None


def token_rows(ent, variant, jobs, dir, gate_failed=()):
    """PS.token_row of every job that `variant` pays for and whose response exists."""
    out = []
    for j in PS.variant_jobs(jobs, variant, gate_failed):
        path = dir / "responses" / f"{j['job']}.jsonl"
        if not path.exists():
            continue
        row = _last_row(path)
        counted = row and row.get("prompt_tokens") is not None and row.get("output_tokens") is not None
        text = "" if counted else (dir / j["prompt"]).read_text(encoding="utf-8")
        out.append(PS.token_row(ent, variant, j["job"], row, text))
    return out


def _fmt_stats(stats):
    return ", ".join(f"{k} {PS._fmt(v) if isinstance(v, float) else v}" for k, v in stats.items())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--dir31", type=Path, default=Path("results/loop1_v31"))
    ap.add_argument("--no-gliner", action="store_true")
    a = ap.parse_args()

    e = MN.load(a.run / "spans")
    docs, gv, gold_attrs = MN.load_shared(a.run)
    labels = _read(a.run / "spans" / "labels.csv")
    clusters = _read(a.run / "spans" / "clusters.csv")
    jobs32, jobs31 = _jobs(a.dir), _jobs(a.dir31)
    split31 = {}
    for (ent, tag), objs in PV.load_split_results(a.dir31 / "responses").items():
        split31.setdefault(ent, {})[tag] = objs
    old_rubric = _read(a.dir / "name_rubric.csv") if (a.dir / "name_rubric.csv").exists() else None
    extract = None if a.no_gliner else PV.gliner_extractor()

    all_dec, all_ver, all_rub, summary, tokens, recall, notes, stats = [], [], [], [], [], {}, [], []
    for ent in dict.fromkeys(j["ent"] for j in jobs32 if j["kind"] == "entity"):
        mine = [j for j in jobs32 if j["ent"] == ent]
        entity = next(j["entity"] for j in mine)
        cids = sorted(c for c in e.mentions.loc[e.mentions["entity"] == entity, "cluster_id"].unique() if c)
        gold_ents = GOLD_ENTS.get(ent, [ent])

        def ctx_of(path):
            return PS.Ctx(e.mentions, labels, gv, gold_attrs, e.ids, e.x, _examples(path, cids), entity, gold_ents)

        decs, vstats, dstats = {}, {}, {}  # variant letter -> decision table (as is)
        nbhd = {s: [j for j in mine if j["kind"] == "entity" and j["run_tag"] == f"s{s}"] for s in SEEDS}
        split = _objs(a.dir, mine, "split")

        jobA = next((j for j in jobs31 if j["ent"] == ent and j["kind"] == "entity" and j["variant"] == "v2"
                     and j["run_tag"] == "r1"), None)
        pathA = a.dir31 / "responses" / f"{jobA['job']}.jsonl" if jobA else None
        if pathA is not None and pathA.exists():
            decs["A"] = _decisions(jobA, pathA, cids, split31)
        else:
            notes.append(f"{ent}: A skipped, no v2 r1 response in {a.dir31}")
        if _have(a.dir, nbhd[0]):
            decs["B"] = PC.decisions_b(a.dir, ent, 0, split)
        else:
            notes.append(f"{ent}: B skipped, nbhd s0 responses missing")
        if all(_have(a.dir, nbhd[s]) for s in SEEDS):
            decs["C"], vstats = PC.vote([PC.decisions_b(a.dir, ent, s, split) for s in SEEDS])
            if any(j["kind"] in ("noise", "gate") and _have(a.dir, [j]) for j in mine):
                decs["D"], dstats = PC.decisions_d(a.dir, ent)
                if not _have(a.dir, [j for j in mine if j["kind"] == "reconcile"]):
                    notes.append(f"{ent}: D without reconcile responses (stage 2 not run or no reconcile jobs)")
            else:
                notes.append(f"{ent}: D skipped, no noise/gate responses")
        else:
            notes.append(f"{ent}: C and D skipped, nbhd responses of seeds 0-2 missing")
        if not decs:
            continue

        entries_a, entries_r = {}, {}
        for letter in list(decs):
            decs[letter] = decs[letter].assign(variant=letter, run_tag=TAG[letter])
            for d in (decs[letter], PS.name_merge(decs[letter], e.mentions, entity)):
                (entries_a if letter == "A" else entries_r)[(d["variant"].iloc[0], TAG[letter])] = (d, "v2")
        final, results, ver_name, ver_desc = {}, {}, {}, {}
        ctx = None
        for entries, path in ((entries_a, a.dir31 / "examples.csv"), (entries_r, a.dir / "examples.csv")):
            if entries:
                ctx = ctx_of(path)
                f, r, vn, vd = score_entries(entries, e, docs, ctx, entity, extract, a.dir / "gliner_cache", gold_ents)
                final.update(f), results.update(r), ver_name.update(vn), ver_desc.update(vd)
        results = {k: results[k] for k in sorted(results, key=lambda k: (k[0], "+namemerge" in k))}
        for letter in decs:
            recall[(ent, letter)] = results[f"{letter}+namemerge {TAG[letter]}"]["recall_after"]
        raw = {k: (v[1], v[2]) for k, v in final.items() if "+namemerge" not in k[0]}
        sheet = PS.rubric_sheet(raw, e.mentions, labels, clusters, old_rubric)

        gate = _objs(a.dir, mine, "gate")
        failed = sorted(c for c, o in gate.items() if o.get("coherent") is False)
        for letter in decs:
            src = ([j for j in jobs31 if j["ent"] == ent], a.dir31) if letter == "A" else (mine, a.dir)
            tokens += token_rows(ent, letter, *src, gate_failed=failed)
        stats.append(f"### {ent}")
        if "C" in decs:
            stats.append(f"- Order agreement (C and D share the 3 orders): {_fmt_stats(vstats)}")
        if "D" in decs:
            stats += [f"- D noise and vote stats: {_fmt_stats(dstats)}",
                      f"- D gate: candidates {len(gate)}, gate-failed {len(failed)}, "
                      f"split applied {int((decs['D']['action'] == 'split').sum())}"]

        note = f"{len(cids)} clusters, {len(ctx.train)} gold classes ({', '.join(gold_ents)})."
        (a.dir / f"scores_{ent}.md").write_text(
            PS.render_scores(results, None, entity, note, rubric=sheet, pair=None, stab_pair=None),
            encoding="utf-8", newline="\n")
        summary += summary_rows(ent, results, sheet)
        all_dec += [d.assign(ent=ent) for d in decs.values()]
        all_ver += [v.assign(ent=ent, label_kind="name") for v in ver_name.values() if len(v)]
        all_ver += [v.assign(ent=ent) for v in ver_desc.values() if len(v)]
        all_rub.append(sheet)

    if not summary:
        sys.exit(f"no responses for the manifest jobs in {a.dir / 'responses'}")
    tok = PS.token_table(tokens, recall)
    _write(pd.concat(all_dec), a.dir / "decisions.csv")
    _write(pd.concat(all_ver) if all_ver else pd.DataFrame(columns=PV.VERIFY_COLS), a.dir / "verification.csv")
    _write(pd.concat(all_rub), a.dir / "name_rubric.csv")
    _write(tok, a.dir / "tokens.csv")
    lines = ["# wf_v3.2 pilot summary", "",
             f"Run `{a.run}`. A = v3.1 v2 r1 + split pass (from `{a.dir31}`), B = nbhd seed 0, C = nbhd vote over 3 "
             "orders, D = C + noise + gate + reconcile; `+namemerge` = same response after merging same-name, "
             "same-placement clusters. Per-check blocks in scores_<ent>.md; real_acc / noise_rub / role_acc come from "
             "the filled name rubric.", ""]
    lines += summary_table(summary)
    lines += ["", "## Tokens", "",
              "Per entity and variant (\"all\" = sum). x A = total tokens over those of A; recall = strict recall_after "
              "of the +namemerge row; est = some counts estimated (est_tokens of the prompt, len(raw) / 3.5). "
              "B = seed-0 entity jobs + all split jobs; C = 3 orders + all splits; D = 3 orders + noise + gate + split "
              "jobs of failed gates + reconcile.", "", PS.render_tokens(tok), "", "## Stats", ""]
    lines += stats + [""] + [f"Note: {n}" for n in notes]
    (a.dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote scores_<ent>.md, decisions.csv, verification.csv, name_rubric.csv, tokens.csv, summary.md in {a.dir}")


if __name__ == "__main__":
    main()
