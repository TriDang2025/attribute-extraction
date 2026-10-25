"""Tasks 1-8 on one run directory written by export_mentions.py (GRAPH_CONTRACT.md).

python scripts/graph_run.py --run results/graph_dev50 --input spans|gold|both --stage STAGE [...]
Stages (each reads the files of the earlier ones):
  coverage   T1 -> coverage.csv
  graph      T2 -> graphs.pkl, graph_<entity>.png (smallest entity with >= 4 clusters)
  stability  T3 part -> stability.csv (re-clusters: seeds x resamples; encodes nothing new)
  signals    T3 -> nodes.csv (with stability.csv when present)
  labels     T4 -> labels.csv, label_sheet.csv (scripts/label_sheet.py --merge folds filled sheets in)
  select     T5-T6 -> select/{auc.csv, corr.csv, sweep.csv, curve.png, chosen.json, nodes_status.csv}
             with --chosen FILE: no choice, apply the chosen.json of another run (test split)
  schema     T7-T8 -> schema/<entity>.json, relationships.json, schema.md, eval.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import coverage as CV  # noqa: E402
from s1a import draft_schema as DS  # noqa: E402
from s1a import graph as GR  # noqa: E402
from s1a import labels as LB  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import node_filter as NF  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import schema_eval as SE  # noqa: E402
from s1a import signals as SG  # noqa: E402
from s1a import stability as ST  # noqa: E402

SIGNALS = ["n_mentions", "n_values", "n_docs", "support", "wilson_lo", "degree", "wdegree_npmi", "pagerank",
           "cohesion", "separation", "stability", "repetition", "cue_consistency", "cardinality", "proximity",
           "confidence"]
THETAS = (0.05, 0.10, 0.20)
SIM_Q = 0.95  # merge / keep-apart pairs: top 5% of within-entity centroid cosines among kept nodes


def _csv(df, path, index=False):
    df.to_csv(path, index=index, encoding="utf-8", lineterminator="\n")


def _docs(run):
    """docs.jsonl as {id: {"text", "turns"}} (the shape coverage.py reads)."""
    out = {}
    for line in open(run / "docs.jsonl", encoding="utf-8"):
        r = json.loads(line)
        out[r["dialogue_id"]] = {"text": r["text"], "turns": r["turns"]}
    return out


def _nodes(d):
    return pd.read_csv(d / "nodes.csv", keep_default_na=False, na_values=[""])


def _labels(d):
    return pd.read_csv(d / "labels.csv", keep_default_na=False, dtype={"gold_attr": str})


def coverage(run, d, e, gv):
    t = CV.coverage_table(e, _docs(run), gv)
    _csv(t, d / "coverage.csv", index=True)
    print(t[["word_cov", "value_cov", "turn_cov", "instance_cov"]].round(3).to_string())


def graph(d, e):
    g = GR.build_graphs(e)
    GR.save(g, d / "graphs.pkl")
    sizes = {ent: h.number_of_nodes() for ent, h in g.co.items()}
    small = min((n, ent) for ent, n in sizes.items() if n >= 4)[1] if any(n >= 4 for n in sizes.values()) \
        else min(sizes, key=sizes.get)
    GR.draw_entity(g, small, d / f"graph_{small}.png")
    for ent, h in sorted(g.co.items()):
        print(f"{ent}: {h.number_of_nodes()} nodes, {h.number_of_edges()} co edges, "
              f"{g.sim[ent].number_of_edges()} sim edges")
    print(f"cross: {g.cross.number_of_edges()} edges; picture of {small}")


def stability(run, name, d, e, args):
    import export_mentions as EX
    docs, inp, enc = EX.prepare(args.split, args.limit, run, name == "spans")
    seeds = (0, 1, 2) if name == "spans" else (0,)  # gold input: stage 1 is the gold entity, no seed
    s = ST.stability_scores(name, docs, enc, e, seeds=seeds, n_resamples=args.resamples,
                            build_fn=lambda i, dd, en, sd: MN.build(i, dd, en, sd, inp=inp))
    _csv(s.reset_index(), d / "stability.csv")
    print(s.describe().round(3).to_string())


def signals(d, e):
    g = GR.load(d / "graphs.pkl")
    stab = None
    if (d / "stability.csv").exists():
        stab = pd.read_csv(d / "stability.csv", keep_default_na=False).set_index("cluster_id")["stability"]
    t = SG.node_table(e, g, stab).reset_index()
    _csv(t, d / "nodes.csv")
    print(f"{len(t)} nodes; stability {'in' if stab is not None else 'missing'}")
    print(t[[c for c in SIGNALS if c in t]].describe().T[["mean", "50%", "min", "max"]].round(3).to_string())


def labels(d, e):
    lab = LB.gold_labels(e.mentions)
    _csv(lab, d / "labels.csv")
    _csv(LB.sheet(e.mentions, lab, n=len(lab)), d / "label_sheet.csv")  # every non-gold node
    print(lab["label"].value_counts().to_string())


def select(d, e, gv, attrs, args):
    nodes, lab = _nodes(d), _labels(d)
    out = d / "select"
    out.mkdir(exist_ok=True)
    sigs = [s for s in SIGNALS if s in nodes]
    if args.chosen:
        ch = json.loads(Path(args.chosen).read_text(encoding="utf-8"))
    else:
        auc = NF.auc_table(nodes, lab, sigs)
        corr = NF.correlations(nodes, sigs)
        _csv(auc, out / "auc.csv")
        _csv(corr, out / "corr.csv", index=True)
        chosen = NF.choose(auc.dropna(subset=["auc"]), corr)
        dirs = dict(zip(auc["signal"], auc["direction"]))
        ch = {"signals": [c for c, _ in chosen], "reasons": [r for _, r in chosen],
              "directions": {c: int(dirs[c]) for c, _ in chosen}}
        print(auc.round(3).to_string(index=False))
    vc = lambda ids: CV.value_coverage(e.mentions, gv, ids)  # noqa: E731
    gold_lab = lab[lab["label"] == "gold"]
    before = gold_lab.loc[gold_lab["gold_attr"].isin(attrs), "gold_attr"].nunique()
    min_attrs = min(30, before - 3)  # "at least 30 of 33" = lose at most 3 of the attributes found unfiltered
    best = None
    for method in ("rank", "weak2"):
        score = NF.combine(nodes, ch["signals"], ch["directions"], method)
        sw = NF.sweep(nodes, lab, score, attrs, THETAS,
                      thresholds=[ch["threshold"]] if args.chosen and ch.get("method") == method else None,
                      value_cov_fn=vc)
        sw.insert(0, "method", method)
        _csv(sw, out / f"sweep_{method}.csv")
        if args.chosen:
            if method == ch["method"]:
                sw = sw[sw["theta"] == ch["theta"]]
                best = (sw.iloc[0], score, method, sw)
            continue
        p = NF.pick(sw.drop(columns="method"), 0.8, min_attrs)
        key = (bool(p["target_met"]), p["attr_covered"], -p["kept"], p["node_precision"])  # same order as NF.pick
        if best is None or key > best[0]:
            best = (key, p, score, method, sw)
    if args.chosen:
        p, score, method, sw = best
        p = pd.concat([p, pd.Series({"target_met": None})])
    else:
        _, p, score, method, sw = best
        NF.plot_curve(sw.drop(columns="method"), out / "curve.png", picked=p, min_attrs=min_attrs)
        ch |= {"attrs_before": int(before), "min_attrs": int(min_attrs), "method": method, "theta": float(p["theta"]), "threshold": float(p["threshold"]),
               "target_met": bool(p["target_met"])}
        (out / "chosen.json").write_text(json.dumps(ch, indent=1), encoding="utf-8", newline="\n")
    st = NF.apply(nodes, score, ch["theta"], ch["threshold"])
    _csv(st, out / "nodes_status.csv")
    print(f"method {method}, theta {ch['theta']}, threshold {ch['threshold']:.3f}: kept {int(p['kept'])}, "
          f"precision {p['node_precision']:.3f} (n {int(p['n_labelled_kept'])}), attrs {int(p['attr_covered'])}"
          f"/{len(attrs)}, value cov {p['value_coverage']:.3f}, saved {int(p['llm_saved'])}, "
          f"target met {p['target_met']}")


def schema(d, e, attrs):
    nodes = pd.read_csv(d / "select" / "nodes_status.csv", keep_default_na=False, na_values=[""])
    g = GR.load(d / "graphs.pkl")
    kept = set(nodes.loc[nodes["status"] == "kept", "cluster_id"])
    cos = [c for h in g.sim.values() for a, b, c in h.edges(data="cos") if a in kept and b in kept]
    sim_thr = float(np.quantile(cos, SIM_Q))  # relative: the cosine scale differs by input (raw vs window mix)
    s = DS.build(e, g, nodes, sim_thr=sim_thr)
    out = d / "schema"
    DS.write(s, out)
    (out / "schema.md").write_text(DS.to_markdown(s), encoding="utf-8", newline="\n")
    ev = SE.evaluate(s, nodes, _labels(d), e.mentions, attrs) | {"sim_thr": sim_thr, "sim_q": SIM_Q}
    (out / "eval.json").write_text(json.dumps(ev, indent=1, default=float), encoding="utf-8", newline="\n")
    print(json.dumps(ev, indent=1, default=float))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--input", choices=("spans", "gold", "both"), default="both")
    ap.add_argument("--stage", required=True, action="append",
                    choices=("coverage", "graph", "stability", "signals", "labels", "select", "schema"))
    ap.add_argument("--split", choices=("dev", "test"), default="dev", help="for the stability stage")
    ap.add_argument("--limit", type=int, default=50, help="for the stability stage")
    ap.add_argument("--resamples", type=int, default=5)
    ap.add_argument("--chosen", help="chosen.json of another run: apply instead of choosing (select stage)")
    args = ap.parse_args()
    run = Path(args.run)
    run = run if run.is_absolute() else paths.ROOT / run
    _, gv, attrs = MN.load_shared(run)
    for name in (("spans", "gold") if args.input == "both" else (args.input,)):
        d = run / name
        e = MN.load(d)
        for stage in args.stage:
            t0 = time.time()
            print(f"== {name} / {stage}", flush=True)
            if stage == "coverage":
                coverage(run, d, e, gv)
            elif stage == "graph":
                graph(d, e)
            elif stage == "stability":
                stability(run, name, d, e, args)
            elif stage == "signals":
                signals(d, e)
            elif stage == "labels":
                labels(d, e)
            elif stage == "select":
                select(d, e, gv, attrs, args)
            else:
                schema(d, e, attrs)
            print(f"   {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
