"""wf_v4 task 11: read results/wf_v4/grading/answers/<judge>_<code>[_r2].json -> grades.csv and task11.md (agreement, controls, Spearman).

python scripts/read_grades_v4.py [--dir results/wf_v4/grading] [--no-auto]
Needs key.json (written by packets_v4.py). The automatic scores come from results/wf_v4/colab/final/scores.csv (a, b, c2),
results/wf_v4/scores/baselines_df.csv (d, f; full GT), results/wf_v4/scores/e_scores.csv (e, rated columns) and the scorer for the GT and the planted GT (--no-auto skips them).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s1a import step4_grades as R  # noqa: E402

RES = ROOT / "results" / "wf_v4"
NAMES = {"a": "a_{s}_s0", "b": "b_{s}_s0", "c2": "c2_{s}_s0", "e": "e_{s}_v0", "d": "d_{s}", "f": "f_{s}"}


def read_answers(folder):
    """(rows, problems): one row per readable answer file; problems = [file: message]."""
    rows, bad = [], []
    for p in sorted(Path(folder).glob("*.json")):
        m = R.FILE.match(p.name)
        if not m:
            bad.append(f"{p.name}: file name is not <judge>_<CODE>[_r2].json")
            continue
        try:
            d = R.parse_answer(p.read_text(encoding="utf-8"), m.group(2))
        except (ValueError, json.JSONDecodeError) as e:
            bad.append(f"{p.name}: {e}")
            continue
        rows.append(R.answer_row(m.group(1), m.group(2), 2 if m.group(3) else 1, d))
    return rows, bad


def auto_scores(key):
    """{(set, candidate): {metric: value}} (full GT, not reachable-only)."""
    import score_v4 as SC
    from s1a import step4_grading as P
    from s1a import step4_gt as G
    from s1a import step4_score as S
    gt = SC.load(ROOT / "gt" / "schema_gt_v1.yaml", RES / "gt", P.SETS)
    final = {}
    # e_scores.csv last: its rated e rows replace the unrated e rows of final/scores.csv (wf_v4.1 fix; before, e scored 0)
    for f in (RES / "colab" / "final" / "scores.csv", RES / "scores" / "baselines_df.csv", RES / "scores" / "e_scores.csv"):
        with open(f, encoding="utf-8") as fh:
            final.update({(r["schema"], r["set"]): r for r in csv.DictReader(fh) if r["reachable_only"] == "False"})
    out = {}
    for s in P.SETS:
        for k, n in NAMES.items():
            row = final.get((n.format(s=s), s))
            out[(s, k)] = {m: (float(row[m]) if row and row[m] != "" else None) for m in R.AUTO}
        planted, _ = P.plant_errors(G.to_canonical(gt), key["seed"], s)
        for k, canon in (("gt", G.to_canonical(gt)), ("gt_planted", planted)):
            met = S.score(canon, gt, s)["metrics"]
            out[(s, k)] = {"grouping_f1": met["grouping_f1"], "table_f1": met["table_f1"], "rel_recall": met["rel_recall"]["share"],
                           "pk_right": met["pk_right"]["share"]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=RES / "grading")
    ap.add_argument("--no-auto", action="store_true")
    a = ap.parse_args(argv)
    key = json.loads((a.dir / "key.json").read_text(encoding="utf-8"))
    rows, bad = read_answers(a.dir / "answers")
    for b in bad:
        print("PROBLEM", b)
    if not rows:
        sys.exit("no answers found")
    for r in rows:
        p = key["packets"].get(r["code"])
        r["set"], r["candidate"] = (p["set"], p["candidate"]) if p else ("", "")
    with open(a.dir / "grades.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    res = R.analyse(rows, key, None if a.no_auto else auto_scores(key))
    (a.dir / "task11.md").write_text(R.to_markdown(res), encoding="utf-8", newline="\n")
    print(f"{len(rows)} answers, {len(bad)} problems -> {a.dir / 'grades.csv'}, {a.dir / 'task11.md'}")


if __name__ == "__main__":
    main()
