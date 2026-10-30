"""wf_v3.3 Step-3 pilot evaluation (PILOT_V33_CONTRACT.md): variants C, E, E1, E2, F scored per entity with the
unchanged scorer.

python scripts/pilot_eval_v33.py --run results/graph_v22_dev50 --dir results/loop1_v33 --dir32 results/loop1_v32
        [--no-gliner] [--human-noise <noise_sheet.csv>] [--no-cue-spread]
C = v3.2 C (nbhd, 3-order vote + split pass) read from --dir32, no rerun; E / E1 / E2 = v3.3 entity jobs, 3-order vote,
then the v3.2 gate and split responses of --dir32 (PC.decisions_e); F = de-lexicalised `f` jobs, seed 0, no gate/split,
no GLiNER. Each is scored as is and after name_merge ("+namemerge"). P4 cue spread is on for every variant (C too);
--no-cue-spread gives the old centroid-only spread. --human-noise: filled noise sheet applied to the gold labels.
Writes <dir>/{scores_<ent>.md, decisions.csv, verification.csv, name_rubric.csv, tokens.csv, summary.md, role_mix.csv}.
GLiNER cache: <dir>/gliner_cache/<ent>; --no-gliner skips it. A variant whose responses are missing is skipped with a note.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from pilot_eval_v31 import (GOLD_ENTS, SUMMARY_COLS, _examples, _read, _write,  # noqa: E402
                            score_entries, summary_rows)
from pilot_eval_v32 import _fmt_stats, _jobs, _last_row, _objs  # noqa: E402

SEEDS = (0, 1, 2)
TAG = {"C": "s012", "E": "s012", "E1": "s012", "E2": "s012", "F": "s0"}
VAR = {"E": "e", "E1": "e1", "E2": "e2", "F": "f"}
EXTRA_COLS = ["place_base", "place_current", "cue"]


def needed(jobs, letter):
    """Entity jobs whose responses variant `letter` reads: C = v3.2 nbhd of seeds 0-2; E1 = `e` group 0 + `e1`;
    F = seed 0 only."""
    var = VAR.get(letter, "nbhd")
    tags = ("s0",) if letter == "F" else tuple(f"s{s}" for s in SEEDS)
    pick = [var] + (["e"] if letter == "E1" else [])
    return [j for j in jobs if j["kind"] == "entity" and j["variant"] in pick and j["run_tag"] in tags
            and (letter != "E1" or (j["variant"] == "e") == ((j["nbhd"] or 0) == 0))]


def _have(dir, jobs):
    """True when there is at least one job and every job has a response file."""
    return bool(jobs) and all((dir / "responses" / f"{j['job']}.jsonl").exists() for j in jobs)


def token_rows(ent, letter, jobs, gate_failed=()):
    """PS.token_row of every job that `letter` pays for and whose response exists. Each job carries `_dir`, the
    folder that holds its prompt and response (v3.3 jobs: --dir, v3.2 gate/split/nbhd jobs: --dir32)."""
    out = []
    for j in PS.variant_jobs(jobs, letter, gate_failed):
        path = j["_dir"] / "responses" / f"{j['job']}.jsonl"
        if not path.exists():
            continue
        row = _last_row(path)
        counted = row and row.get("prompt_tokens") is not None and row.get("output_tokens") is not None
        text = "" if counted else (j["_dir"] / j["prompt"]).read_text(encoding="utf-8")
        out.append(PS.token_row(ent, letter, j["job"], row, text))
    return out


def summary_table33(rows):
    cols = SUMMARY_COLS + EXTRA_COLS
    lines = ["| ent | variant | run | " + " | ".join(cols) + " |", "|---|---|---|" + "---|" * len(cols)]
    for r in rows:
        lines.append(f"| {r['ent']} | {r['variant']} | {r['run_tag']} | "
                     + " | ".join(PS._fmt(r.get(c), c in ("noise_kept", "cue")) for c in cols) + " |")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--dir32", type=Path, default=Path("results/loop1_v32"))
    ap.add_argument("--no-gliner", action="store_true")
    ap.add_argument("--human-noise", type=Path, default=None)
    ap.add_argument("--no-cue-spread", action="store_true")
    a = ap.parse_args()

    e = MN.load(a.run / "spans")
    docs, gv, gold_attrs = MN.load_shared(a.run)
    labels = _read(a.run / "spans" / "labels.csv")
    if a.human_noise is not None:
        sheet_in = _read(a.human_noise)
        if (sheet_in["human"].str.strip() != "").any():
            labels = PS.apply_human_labels(labels, sheet_in)
    clusters = _read(a.run / "spans" / "clusters.csv")
    jobs33, jobs32 = _jobs(a.dir), _jobs(a.dir32)
    old_rubric = _read(a.dir / "name_rubric.csv") if (a.dir / "name_rubric.csv").exists() else None
    extract = None if a.no_gliner else PV.gliner_extractor()
    left_words = None if a.no_cue_spread else PV.left_word_map(e.mentions, docs)

    all_dec, all_ver, all_rub, summary, tokens, recall, notes, stats, roles = [], [], [], [], [], {}, [], [], []
    for ent in dict.fromkeys(j["ent"] for j in jobs33 if j["kind"] == "entity"):
        mine33, mine32 = [j for j in jobs33 if j["ent"] == ent], [j for j in jobs32 if j["ent"] == ent]
        entity = next(j["entity"] for j in mine33)
        cids = sorted(c for c in e.mentions.loc[e.mentions["entity"] == entity, "cluster_id"].unique() if c)
        gold_ents = GOLD_ENTS.get(ent, [ent])
        split32 = _objs(a.dir32, mine32, "split")
        gate = _objs(a.dir32, mine32, "gate")
        failed = sorted(c for c, o in gate.items() if o.get("coherent") is False)
        if not _have(a.dir32, [j for j in mine32 if j["kind"] == "gate"]):
            notes.append(f"{ent}: v3.2 gate responses incomplete in {a.dir32}; clusters without a gate answer stay unsplit")

        decs, vstats = {}, {}  # variant letter -> decision table (as is)
        if _have(a.dir32, needed(mine32, "C")):
            decs["C"], vstats["C"] = PC.vote([PC.decisions_b(a.dir32, ent, s, split32) for s in SEEDS])
        else:
            notes.append(f"{ent}: C skipped, v3.2 nbhd responses of seeds 0-2 missing in {a.dir32}")
        for letter, var in VAR.items():
            if _have(a.dir, needed(mine33, letter)):
                decs[letter], vstats[letter] = PC.decisions_e(a.dir, ent, var, a.dir32)
            else:
                notes.append(f"{ent}: {letter} skipped, `{var}` responses missing in {a.dir}")
        if not decs:
            continue

        # one Ctx: v3.3 examples plus the v3.2 ones (the gate/split examples of C and the split parts of E)
        ex = pd.concat([_examples(a.dir / "examples.csv", cids), _examples(a.dir32 / "examples.csv", cids)]
                       ).drop_duplicates("ex_id")
        ctx = PS.Ctx(e.mentions, labels, gv, gold_attrs, e.ids, e.x, ex, entity, gold_ents)

        final, results, ver_name, ver_desc = {}, {}, {}, {}
        for group, ext in (([k for k in decs if k != "F"], extract), (["F"] if "F" in decs else [], None)):
            entries = {}
            for letter in group:
                decs[letter] = decs[letter].assign(variant=letter, run_tag=TAG[letter])
                for d in (decs[letter], PS.name_merge(decs[letter], e.mentions, entity)):
                    entries[(d["variant"].iloc[0], TAG[letter])] = (d, "v2")
            if entries:
                f, r, vn, vd = score_entries(entries, e, docs, ctx, entity, ext, a.dir / "gliner_cache" / ent, gold_ents,
                                             left_words)
                final.update(f), results.update(r), ver_name.update(vn), ver_desc.update(vd)
        results = {k: results[k] for k in sorted(results, key=lambda k: (k[0], "+namemerge" in k))}
        for letter in decs:
            recall[(ent, letter)] = results[f"{letter}+namemerge {TAG[letter]}"]["recall_after"]
        raw = {k: (v[1], v[2]) for k, v in final.items() if "+namemerge" not in k[0]}
        sheet = PS.rubric_sheet(raw, e.mentions, labels, clusters, old_rubric)
        roles.append(PS.role_table(e.mentions, entity))

        jobs = [{**j, "_dir": a.dir} for j in mine33] + [{**j, "_dir": a.dir32} for j in mine32
                                                         if j["kind"] in ("entity", "gate", "split")]
        for letter in decs:
            tokens += token_rows(ent, letter, jobs, failed)

        stats.append(f"### {ent}")
        for letter, st in vstats.items():
            stats.append(f"- {letter}: {_fmt_stats(st)}")
        stats.append(f"- v3.2 gate: candidates {len(gate)}, gate-failed {len(failed)}")

        note = f"{len(cids)} clusters, {len(ctx.train)} gold classes ({', '.join(gold_ents)})."
        (a.dir / f"scores_{ent}.md").write_text(
            PS.render_scores(results, None, entity, note, rubric=sheet, pair=None, stab_pair=None),
            encoding="utf-8", newline="\n")
        rows = summary_rows(ent, results, sheet)
        for r in rows:
            letter = r["variant"].replace("+namemerge", "")
            r["cue"] = float((decs[letter]["action"] == "attribute_cue").sum())
            r["place_base"], r["place_current"] = (results[f"{r['variant']} {r['run_tag']}"][k] for k in EXTRA_COLS[:2])
        summary += rows
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
    _write(pd.concat(roles), a.dir / "role_mix.csv")
    _write(tok, a.dir / "tokens.csv")
    lines = ["# wf_v3.3 pilot summary", "",
             f"Run `{a.run}`. C = v3.2 C re-scored from `{a.dir32}`; E = C prompts + attribute_cue + noise rule + role-aware "
             "examples + carry-over, 3-order vote, v3.2 gate and split; E1 = E without carry-over; E2 = E without the cue "
             "and noise text; F = E on de-lexicalised text, seed 0, no gate/split, no GLiNER. `+namemerge` = same response "
             "after merging same-name, same-placement clusters. "
             + ("P4 cue spread is OFF (--no-cue-spread)." if a.no_cue_spread else
                "P4 cue spread is ON for every variant, C included.")
             + (f" Gold labels use the human noise sheet `{a.human_noise}`." if a.human_noise else "")
             + " place_base = placement score if every placement were `current entity`; place_current = share of rows "
             "placed on the current entity; cue = attribute_cue clusters.", ""]
    lines += summary_table33(summary)
    lines += ["", "## Tokens", "",
              "Per entity and variant (\"all\" = sum). x_A is n/a (no A in this run). recall = strict recall_after of the "
              "+namemerge row; est = some counts estimated. C = 3 orders + all splits (v3.2); E, E1, E2 = entity jobs + all "
              "gate jobs + split jobs of failed gates (E1 = `e` group-0 jobs + `e1` jobs); F = `f` jobs.", "",
              PS.render_tokens(tok), "", "## Stats", ""]
    lines += stats + [""] + [f"Note: {n}" for n in notes]
    (a.dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote scores_<ent>.md, decisions.csv, verification.csv, name_rubric.csv, role_mix.csv, tokens.csv, "
          f"summary.md in {a.dir}")


if __name__ == "__main__":
    main()
