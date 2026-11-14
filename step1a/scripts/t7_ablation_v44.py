"""wf_v4.4 (diary Nov 14) T7: which Step 4 change helped. dev50, seed 0, input a_llama44 (a_llama43 works as a stand-in).

Runs (results/wf_v44/t7/<switch_off>/):
  all_on/        all five changes on, seeds 0, 1, 2 + the vote chain (or an existing T6 run: run(..., all_on_dir=<t6 dir>); the dir must hold the input's
                 dev50 chains and is scored in place, nothing is copied)
  entity_hint/, other_choice/, key_candidates/, code_links/   that change off, the others on, seed 0 only (one chain each)
  vote/          no new calls: the seed 0 single-seed schema of all_on, scored (the vote off = one seed)
Table t7/t7_table.md (table(out)): per change, score with it on and off. "On" = the all_on seed 0 schema (the voted schema for the vote); "off" = the
off run's seed 0 schema (the seed 0 single schema for the vote). Calls: on = the seed 0 chain of all_on (for the vote: all chains of all_on),
off = the off run's chain.

python scripts/t7_ablation_v44.py --fake [--out DIR] [--inp a_llama43] [--all-on-dir DIR]   fake model (default out results/wf_v44/t7/fake)
python scripts/t7_ablation_v44.py --table [--out DIR]                                         score every run dir and write the table
Colab: t7_ablation_v44.run(backend) with log_v44.VllmBackend44; step3_dirs={"a_llama44": Path(...)} points it at a_llama44 elsewhere.
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import step4_fake_v44 as F  # noqa: E402
from s1a import step4_v44 as S  # noqa: E402
from s1a.log_v44 import call_rows  # noqa: E402

OUT = ROOT / "results" / "wf_v44" / "t7"
OFF_RUNS = ("entity_hint", "other_choice", "key_candidates", "code_links")
COLUMNS = (("table_f1", "table F1", "f"), ("grouping_f1", "grouping F1", "f"), ("gt_columns_placed", "GT columns placed", "kn"),
           ("gt_in_rest", "GT in rest", "kn"), ("pk_right", "PK (a)", "kn"), ("rel_recall", "link recall", "kn"))


def run(backend, out=OUT, inp="a_llama44", set_name="dev50", cfg=None, step3_dirs=None, all_on_dir=None, log=print):
    """Run all_on and the four off runs (see the module doc), score every dir, write the table. Returns {"runs": {name: dir}, "table": text}."""
    out, cfg = Path(out), cfg or S.load_config()
    runs = {"all_on": Path(all_on_dir) if all_on_dir else out / "all_on"}
    if not all_on_dir:
        S.run(runs["all_on"], backend, (inp,), (set_name,), S.SEEDS, cfg, step3_dirs, ROOT, log)
    for sw in OFF_RUNS:
        runs[sw] = out / sw
        S.run(runs[sw], backend, (inp,), (set_name,), (0,), S.with_switches(cfg, off=(sw,)), step3_dirs, ROOT, log)
    runs["vote"] = out / "vote"
    for d in runs.values():
        if d.name != "vote" and not (d / "scores.csv").exists():
            S.score_chains(d, ROOT)
    return {"runs": {k: str(v) for k, v in runs.items()}, "table": table(out, inp, set_name, all_on_dir)}


def _rows(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if str(r["reachable_only"]) == "False"]


def _fmt(row, key, kind):
    if row is None:
        return "n/a"
    if kind == "f":
        return f"{float(row[key]):.3f}" if row.get(key) not in (None, "") else "n/a"
    return f"{row[key + '_k']}/{row[key + '_n']} ({float(row[key]):.3f})" if row.get(key + "_n") not in (None, "", "0", 0) else "n/a"


def _calls(d, prefix=None):
    return len([r for r in call_rows(d) if not r["file"].startswith("fake/") and (prefix is None or r["job"].startswith(prefix))])


def table(out=OUT, inp="a_llama44", set_name="dev50", all_on_dir=None):
    """Write <out>/t7_table.md (and score <out>/vote/scores.csv from the all_on seed 0 rows); returns the text."""
    import score_v4 as SCR
    out = Path(out)
    on_dir = Path(all_on_dir) if all_on_dir else out / "all_on"
    s0, vote = f"{inp}_{set_name}_s0", f"{inp}_{set_name}_vote"
    on_rows = _rows(on_dir / "scores.csv")
    pick = lambda rows, name: next((r for r in rows if r["schema"] == name), None)      # noqa: E731
    (out / "vote").mkdir(parents=True, exist_ok=True)
    allrows = []
    with open(on_dir / "scores.csv", encoding="utf-8") as f:
        allrows = [r for r in csv.DictReader(f) if r["schema"] == s0]
    SCR.write_rows(out / "vote" / "scores.csv", allrows)
    head = ["change"] + [f"{n} {w}" for _, n, _ in COLUMNS for w in ("on", "off")] + ["calls on", "calls off"]
    lines = [f"# wf_v4.4 T7: which Step 4 change helped ({inp}, {set_name}, seed 0)", "",
             "On = all changes on (seed 0 single schema; the voted schema for `vote`). Off = that change off, the others on (seed 0 single schema; the seed 0 "
             "single schema for `vote`). Calls: on = the seed 0 chain of all_on (all chains for `vote`), off = the off run's chain. Full GT.", "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for sw in S.SWITCHES:
        on = pick(on_rows, vote if sw == "vote" else s0)
        off = pick(_rows(out / sw / "scores.csv"), s0)
        cells = [x for key, _, kind in COLUMNS for x in (_fmt(on, key, kind), _fmt(off, key, kind))]
        c_on = _calls(on_dir) if sw == "vote" else _calls(on_dir, s0 + "_")
        c_off = _calls(on_dir, s0 + "_") if sw == "vote" else _calls(out / sw, s0 + "_")
        lines.append(f"| {sw} | " + " | ".join(cells) + f" | {c_on} | {c_off} |")
    text = "\n".join(lines) + "\n"
    B.write(out / "t7_table.md", text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--inp", default="a_llama44")
    ap.add_argument("--set", default="dev50")
    ap.add_argument("--all-on-dir", type=Path)
    ap.add_argument("--a-llama44-dir", type=Path)
    ap.add_argument("--a-llama43-dir", type=Path)
    a = ap.parse_args()
    if not (a.fake or a.table):
        ap.error("give --fake and/or --table (the real run is the Colab notebook calling t7_ablation_v44.run)")
    out = a.out or (OUT / "fake" if a.fake else OUT)
    if a.fake:
        dirs = {k: v for k, v in (("a_llama44", a.a_llama44_dir), ("a_llama43", a.a_llama43_dir)) if v}
        info = run(F.FakeV44(), out, a.inp, a.set, step3_dirs=dirs, all_on_dir=a.all_on_dir)
        print("runs:", ", ".join(info["runs"]))
    elif a.table:
        for d in [out / "all_on", *(out / s for s in OFF_RUNS)]:
            if (d / "final" / "status.json").exists():
                S.score_chains(d, ROOT)
        print(table(out, a.inp, a.set, a.all_on_dir))
    print("->", out / "t7_table.md")


if __name__ == "__main__":
    main()
