"""wf_v3.7 T9 / T13: recall@K at L1 and L2, the L2 ceiling and the J split of Step 1a v2.2 vs v2.3 on dev50 and dev50b.

python scripts/step1a_v23.py [--out results/loop1_v37]
Reads the exports results/graph_v22_<set>/ and results/graph_v23_<set>/ (scripts/export_mentions.py, then graph_run.py
--stage labels), the GT levels of each set, and s1a/ceiling_v37.py (W1). No encoder, no LLM.
Writes <out>/step1a_v22_v23.md and <out>/step1a_v22_v23.csv (one row per set x version), <out>/j_split_<set>.csv.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import recall as RC  # noqa: E402
from s1a import run_data_v37 as RD  # noqa: E402
from s1a import step1a_v37 as S  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

SETS = {"dev50": "results/loop1_v35/gt_levels.csv", "dev50b": "results/loop1_v37/dev50b/gt/gt_levels.csv"}
VERSIONS = {"v2.2": "results/graph_v22_{}", "v2.3": "results/graph_v23_{}"}


def count(k, n):
    return f"{k}/{n}"


def measure(run, gt):
    """One dict of a run: K, L1 and L2 recall, L2 ceiling counts per entity (and the ceiling table)."""
    e = MN.load(run / "spans")
    _, gv, attrs = MN.load_shared(run)
    t1 = RC.recall_table(e.mentions, gv, attrs)
    shared, data = RD.entity_data(run)
    ceil = CE.ceiling_for(data, gt, 2)
    t2, s2 = S.recall_l2(e.mentions, gt, list(ceil["attr"]))
    cnt = CE.ceiling_counts(ceil).set_index("ent")
    row = {"K": RC.summary(e.mentions, t1)["K"], "n_l1": len(attrs), **{f"L1_{k}": int(t1[k].sum()) for k in RC.MEASURES[1:]},
           "n_l2": len(ceil), **{f"L2_{k}": s2[k] for k in RC.MEASURES[1:]},
           "ceil_present": int(cnt.loc["total", "present"]), "ceil_recoverable": int(cnt.loc["total", "recoverable"])}
    for ent in ("train", "hotel", "restaurant"):
        row |= {f"ceil_{ent}_n": int(cnt.loc[ent, "n"]), f"ceil_{ent}_present": int(cnt.loc[ent, "present"]),
                f"ceil_{ent}_recoverable": int(cnt.loc[ent, "recoverable"])}
    return row, e, ceil


def wall_times(runs):
    """[(run dir name, export seconds, stages seconds)] from the "wall <n>s" / "export wall <n>s" / "stages wall <n>s"
    last lines of <run>/export.log and <run>/stages_1_4.log ("" when a log or line is missing)."""
    def last(path):
        m = re.findall(r"(?:wall|done in) (\d+)s", path.read_text(encoding="utf-8", errors="replace")) if path.exists() else []
        return m[-1] if m else ""
    return [(r.name, last(r / "export.log"), last(r / "stages_1_4.log")) for r in runs]


def md_table(df, cols):
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in df.iterrows()])


def report(rows, jsplits, times):
    t = pd.DataFrame(rows)
    show = pd.DataFrame({
        "set": t["set"], "version": t["version"], "K": t["K"],
        "L1 strict": [count(a, b) for a, b in zip(t["L1_strict"], t["n_l1"])],
        "L1 recoverable": [count(a, b) for a, b in zip(t["L1_recoverable"], t["n_l1"])],
        "L1 present": [count(a, b) for a, b in zip(t["L1_present"], t["n_l1"])],
        "L2 strict": [count(a, b) for a, b in zip(t["L2_strict"], t["n_l2"])],
        "L2 recoverable": [count(a, b) for a, b in zip(t["L2_recoverable"], t["n_l2"])],
        "L2 present": [count(a, b) for a, b in zip(t["L2_present"], t["n_l2"])],
        "L2 ceiling present": [count(a, b) for a, b in zip(t["ceil_present"], t["n_l2"])],
        "L2 ceiling recoverable": [count(a, b) for a, b in zip(t["ceil_recoverable"], t["n_l2"])]})
    ent = pd.DataFrame({"set": t["set"], "version": t["version"], **{
        f"{e}: present / recoverable (of n)": [f"{r[f'ceil_{e}_present']} / {r[f'ceil_{e}_recoverable']} (of {r[f'ceil_{e}_n']})"
                                               for _, r in t.iterrows()] for e in ("train", "hotel", "restaurant")}})
    parts = ["# Step 1a v2.2 vs v2.3 on dev50 and dev50b (wf_v3.7, T9 and T13)", "",
             "v2.2 = frozen recipe `F_m2_t06_bk`. v2.3 = `V23`: v2.2 with the T26 value-type fix in both type partitions "
             "(`value_type_v35`: 8.08GBP, 37.79 GPB, 66 GBP are price; 28-minute, 105 minutes are duration) and the J split "
             "of two-role clusters (`s1a/roles_v37.py`: a cluster is split when the cue words put >= 20% of its mentions on "
             "each side; mentions with no cue word form their own unknown-role cluster; no gold labels).", "",
             "Cue words of the J split: general words plus words learned per cluster (T12, `cue_words.md`). No learned word was "
             "mapped to a side on dev50 or dev50b (see the empty `learned` column below), so J here = the general cue words. "
             "dev50b was used for confirmation only: nothing was tuned on it. The `labels` stage wrote `label_sheet.csv` "
             "for the non-gold clusters of each run and it is left unfilled (only the select / schema stages and the old "
             "jury / pattern noise kinds need it; rules v1.1 noise does not).", "",
             "## Recall at K and L2 ceiling", "",
             "L1 = TEAR gold classes (recall.py with the gold values); L2 = GT level 2 labels on the clustered mentions "
             "(`s1a/step1a_v37.py`; strict: some cluster purity >= 0.6; recoverable: or >= 2 mentions inside and purity "
             ">= 0.25; present: >= 1 labelled mention inside a cluster). **L2 ceiling** = `ceiling_v37.ceiling_table` "
             "(found rule of rules v1.1: a single cluster with purity >= 0.6 and coverage >= 10% of the attribute's "
             "mentions; present: some labelled mention is in a cluster of the entity), over the L2 base attributes.", "",
             md_table(show, list(show.columns)), "", "L2 ceiling per entity:", "", md_table(ent, list(ent.columns)), "",
             "## Run times (wall seconds, CPU laptop)", "",
             "Export = `export_mentions.py` (GLiNER, bge-m3 encodes, clustering); stages = `graph_run.py` coverage, graph, "
             "stability, signals, labels. The v2.2 dev50b export needed fresh GLiNER and bge-m3 encodes; the others read the "
             "caches.", "", "| run | export | stages 1-4 |", "|---|---|---|"] + [f"| {n} | {e} | {s} |" for n, e, s in times] + [""]
    for name, df in jsplits.items():
        parts += [f"## J split on {name}", "",
                  f"{len(df)} clusters split; unknown-part sizes {sorted(df['unknown'].tolist())}; "
                  f"mentions in the unknown parts {int(df['unknown'].sum())} of {int(df['n'].sum())} in split clusters.", "",
                  "Clusters are listed as start part; end part; unknown part. l2_labels: the GT L2 labels of the mentions in "
                  "each part (not used by the split).", "",
                  md_table(df, list(df.columns)) if len(df) else "(no cluster was split)", ""]
    return "\n".join(parts), t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="results/loop1_v37")
    a = ap.parse_args()
    out = paths.ROOT / a.out
    rows, jsplits = [], {}
    for name, gt_path in SETS.items():
        gt = VD.read_gt_levels(paths.ROOT / gt_path)
        base = None
        for ver, pat in VERSIONS.items():
            run = paths.ROOT / pat.format(name)
            row, e, ceil = measure(run, gt)
            if base is None:
                base = e.mentions
            elif not S.same_spans(base, e.mentions):
                raise SystemExit(f"{run}: spans differ from the v2.2 run, so one gt_levels table does not fit both")
            rows.append({"set": name, "version": ver, **row})
            ceil.to_csv(out / f"ceiling_{ver}_{name}.csv", index=False, encoding="utf-8", lineterminator="\n")
            jf = run / "spans" / "j_split.json"
            if ver == "v2.3":
                stats = json.loads(jf.read_text(encoding="utf-8")) if jf.exists() else []
                jsplits[name] = S.j_split_summary(stats, e.mentions, gt)
                jsplits[name].to_csv(out / f"j_split_{name}.csv", index=False, encoding="utf-8", lineterminator="\n")
            print(name, ver, row, flush=True)
    md, t = report(rows, jsplits, wall_times([paths.ROOT / p.format(n) for n in SETS for p in VERSIONS.values()]))
    (out / "step1a_v22_v23.md").write_text(md, encoding="utf-8", newline="\n")
    t.to_csv(out / "step1a_v22_v23.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(md)


if __name__ == "__main__":
    main()
