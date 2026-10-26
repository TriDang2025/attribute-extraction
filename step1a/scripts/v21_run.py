"""v2.1 experiment: score Step-3 (spans clustering) variants on the dev spans, the same way for every part.

python scripts/v21_run.py --part A|B|C|D|E [--only NAME,...] [--limit 50]
  -> results/v21_<part>/scores.csv, scores.md (one row per variant, baseline first)
Parts: A span_filter, B shapes, C cue, D spans_step2 (modules in s1a/, each with CONFIGS);
E = combos registered in s1a/combos.py.
Per variant:
- F1/P/R/K: lenient B-cubed of the spans vs gold classes, mean over the 3 stage-1 seeds (as plug_in.py);
- vrec: value recall of the (filtered) spans; e2e = vrec * F1;
- attrs: gold classes with a gold-labelled node (purity >= 0.6), seed 42; clusters at seed 42;
- valcov: gold values inside a clustered span (coverage.value_coverage), seed 42.
Encodes with bge-m3: run one part at a time.
"""

import argparse
import importlib
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

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

PARTS = {"A": "s1a.span_filter", "B": "s1a.shapes", "C": "s1a.cue", "D": "s1a.spans_step2", "E": "s1a.combos"}
RUNS = {"dev": paths.RESULTS / "graph_dev50", "test": paths.RESULTS / "graph_test50"}  # v2 exports (caches)


def score(name, v, docs, inp, enc, gv):
    spans = v.span_filter(list(inp.spans)) if v.span_filter else list(inp.spans)
    run_inp = MN.Inputs(mentions=inp.mentions, tables=inp.tables, spans=spans, segs=inp.segs,
                        cluster_fn=v.cluster_fn)
    vrec = M.span_recall(spans, inp.mentions)["value"]
    blocks, e42 = [], None
    for s in RL.SEEDS:
        e = MN.build("spans", docs, enc, s, inp=run_inp)
        units = [u for u in spans if u.doc_id in docs]  # build matched labels onto these
        pred = [c or f"none{i}" for i, c in enumerate(e.mentions.cluster_id)]
        blocks.append(M.report_block(units, pred, levels=()))
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
        valcov=CV.value_coverage(e42.mentions, gv))


def write(out, rows, part):
    df = pd.DataFrame(rows)
    df.to_csv(out / "scores.csv", index=False, lineterminator="\n")
    cols = ["variant", "n_spans", "vrec", "P", "R", "F1", "e2e", "K", "singleton_share", "attrs", "valcov", "note"]
    L = [f"# v2.1 part {part}: spans clustering variants", "",
         "F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; "
         "attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.", "",
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
    out = paths.RESULTS / (f"v21_{args.part}" + ("_test" if args.split == "test" else ""))
    out.mkdir(parents=True, exist_ok=True)
    configs = importlib.import_module(PARTS[args.part]).CONFIGS
    if args.only:
        configs = {k: configs[k] for k in args.only.split(",")}
    run = RUNS[args.split]
    docs, inp, enc = EX.prepare(args.split, args.limit, run, True)
    _, gv, _ = MN.load_shared(run)
    todo = ({} if args.no_baseline else {"baseline": BASELINE}) | configs
    rows = []
    for name, v in todo.items():
        t0 = time.time()
        rows.append(score(name, v, docs, inp, enc, gv))
        enc.save()
        r = rows[-1]
        print(f"{name}: F1 {r['F1']:.3f} e2e {r['e2e']:.3f} K {r['K']:.0f} attrs {r['attrs']} "
              f"valcov {r['valcov']:.3f} ({time.time() - t0:.0f}s)", flush=True)
        write(out, rows, args.part)


if __name__ == "__main__":
    main()
