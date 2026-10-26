"""v2.1 / v2.2 experiments: score Step-3 (spans clustering) variants the same way for every part.

python scripts/v21_run.py --part A..J [--only NAME,...] [--limit 50] [--split test]
  -> results/v21_<part>/ (A-E) or results/v22_<part>/ (F-J): scores.csv, scores.md
Parts (modules in s1a/, each with CONFIGS): v2.1 A span_filter, B shapes, C cue, D spans_step2, E combos;
v2.2 F fold, G staged, H roleword, I multiview, J combos22. Reference rows: baseline (v1/v2) and,
for F-J, v2.1 (combos E_AB_type).
Per variant:
- F1/P/R/K: lenient B-cubed of the spans vs gold classes, mean over the 3 stage-1 seeds (as plug_in.py);
- vrec: value recall of the (filtered) spans; e2e = vrec * F1;
- attrs: gold classes with a gold-labelled node (purity >= 0.6), seed 42; clusters at seed 42;
- valcov: gold values inside a clustered span (coverage.value_coverage), seed 42;
- F1_1to1 (P1/R1): one-to-one mapping of clusters to gold classes (Hungarian on mention counts), mean of
  3 seeds: P1 = matched mentions / labelled mentions in matched clusters, R1 = matched / all labelled
  mentions, so splitting one class over many clusters lowers R1.
Encodes with bge-m3: run one part at a time.
"""

import argparse
import importlib
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_mentions as EX  # noqa: E402
import relabel as RL  # noqa: E402
from s1a import coverage as CV  # noqa: E402
from s1a import labels as LB  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import metrics as M  # noqa: E402
from s1a import paths  # noqa: E402
from s1a.variants import BASELINE  # noqa: E402

PARTS = {"A": "s1a.span_filter", "B": "s1a.shapes", "C": "s1a.cue", "D": "s1a.spans_step2", "E": "s1a.combos",
         "F": "s1a.fold", "G": "s1a.staged", "H": "s1a.roleword", "I": "s1a.multiview", "J": "s1a.combos22"}
RUNS = {"dev": paths.RESULTS / "graph_dev50", "test": paths.RESULTS / "graph_test50"}  # v2 exports (caches)


def one_to_one(units, pred):
    """(P1, R1, F1) of a one-to-one cluster -> gold class mapping maximising matched mentions."""
    lab = [(p, u.labels) for u, p in zip(units, pred) if u.labels]
    cl, gs = sorted({p for p, _ in lab}), sorted({g for _, ls in lab for g in ls})
    ci, gi = {c: i for i, c in enumerate(cl)}, {g: i for i, g in enumerate(gs)}
    n = np.zeros((len(cl), len(gs)))
    size = np.zeros(len(cl))
    for p, ls in lab:
        size[ci[p]] += 1
        for g in ls:
            n[ci[p], gi[g]] += 1
    r, c = linear_sum_assignment(-n)
    hit = n[r, c].sum()
    p1, r1 = hit / max(1, size[r].sum()), hit / max(1, len(lab))
    return p1, r1, 2 * p1 * r1 / max(1e-9, p1 + r1)


def score(name, v, docs, inp, enc, gv):
    spans = v.span_filter(list(inp.spans)) if v.span_filter else list(inp.spans)
    run_inp = MN.Inputs(mentions=inp.mentions, tables=inp.tables, spans=spans, segs=inp.segs,
                        cluster_fn=v.cluster_fn)
    vrec = M.span_recall(spans, inp.mentions)["value"]
    blocks, oto, e42 = [], [], None
    for s in RL.SEEDS:
        e = MN.build("spans", docs, enc, s, inp=run_inp)
        units = [u for u in spans if u.doc_id in docs]  # build matched labels onto these
        pred = [c or f"none{i}" for i, c in enumerate(e.mentions.cluster_id)]
        blocks.append(M.report_block(units, pred, levels=()))
        oto.append(one_to_one(units, pred))
        if s == 42:
            e42 = e
    lab = LB.gold_labels(e42.mentions)
    f1 = float(np.mean([b["all"]["f"] for b in blocks]))
    return dict(
        variant=name, note=v.note, n_spans=len(spans), vrec=vrec,
        P=float(np.mean([b["all"]["p"] for b in blocks])), R=float(np.mean([b["all"]["r"] for b in blocks])),
        F1=f1, e2e=vrec * f1, K=float(np.mean([b["K"] for b in blocks])), clusters=len(e42.clusters),
        singleton_share=float((e42.clusters["n_values"] == 1).mean()),
        attrs=int(lab.loc[lab["label"] == "gold", "gold_attr"].nunique()),
        valcov=CV.value_coverage(e42.mentions, gv),
        P1=float(np.mean([o[0] for o in oto])), R1=float(np.mean([o[1] for o in oto])),
        F1_1to1=float(np.mean([o[2] for o in oto])))


def write(out, rows, part):
    df = pd.DataFrame(rows)
    df.to_csv(out / "scores.csv", index=False, lineterminator="\n")
    cols = ["variant", "n_spans", "vrec", "P", "R", "F1", "e2e", "K", "singleton_share", "attrs", "valcov",
            "P1", "R1", "F1_1to1", "note"]
    L = [f"# Part {part}: spans clustering variants", "",
         "F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; "
         "attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; "
         "P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.", "",
         "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.to_dict("records"):
        L.append("| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
    (out / "scores.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=sorted(PARTS))
    ap.add_argument("--only", default="", help="comma-separated variant names")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--split", choices=("dev", "test"), default="dev", help="test: scoring check only, no tuning")
    args = ap.parse_args()
    v22 = args.part in "FGHIJ"
    out = paths.RESULTS / (("v22_" if v22 else "v21_") + args.part + ("_test" if args.split == "test" else ""))
    out.mkdir(parents=True, exist_ok=True)
    configs = importlib.import_module(PARTS[args.part]).CONFIGS
    if args.only:
        configs = {k: configs[k] for k in args.only.split(",")}
    run = RUNS[args.split]
    docs, inp, enc = EX.prepare(args.split, args.limit, run, True)
    _, gv, _ = MN.load_shared(run)
    refs = {"baseline": BASELINE}
    if v22:
        from s1a.combos import CONFIGS as V21
        refs["v2.1"] = V21["E_AB_type"]
    todo = ({} if args.no_baseline else refs) | configs
    rows = []
    for name, v in todo.items():
        t0 = time.time()
        rows.append(score(name, v, docs, inp, enc, gv))
        enc.save()
        r = rows[-1]
        print(f"{name}: F1 {r['F1']:.3f} e2e {r['e2e']:.3f} K {r['K']:.0f} attrs {r['attrs']} "
              f"valcov {r['valcov']:.3f} 1to1 {r['F1_1to1']:.3f} ({time.time() - t0:.0f}s)", flush=True)
        write(out, rows, args.part)


if __name__ == "__main__":
    main()
