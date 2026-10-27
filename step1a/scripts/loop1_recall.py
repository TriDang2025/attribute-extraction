"""Loop-1 T2: recall at K for v2.2 (sweep), setting J and setting G (LOOP1_CONTRACT.md).

python scripts/loop1_recall.py [--run results/graph_v22_dev50] [--split dev] [--limit 50] [--out results/loop1_check]
  -> <out>/{recall.csv, recall_by_attr.csv, fig/loop1_recall_at_k.png}
Encodes with bge-m3 through the shared single-writer cache: run alone.
v2.2 = fold.CONFIGS["F_m2_t06_bk"] on combos.V21 (Step-2 t 0.4). The sweep varies that t and the fold tau / min_size.
"""

import argparse
import sys
import time
from dataclasses import replace
from functools import partial
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_mentions as EX  # noqa: E402
from s1a import combos, combos22, fold, paths, recall, staged  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a.variants import Variant  # noqa: E402

SEED = 42
MAIN = "t0.4 m2 tau0.6 bk"  # params of the adopted v2.2 point (bootstrap + per-attribute table)
J_KEY, G_KEY = "J_Hl0r1_t04_fm2_06bk", "G_w2_t1_02"  # role word 1 right, t 0.4, + fold; staged window 2, t1 0.2


def v22(t=0.4, m=2, tau=0.6, bk=True):
    """v2.2 with another base Step-2 threshold t and fold min_size m / tau (bk = booking check)."""
    return Variant(span_filter=combos.V21_FILTER,
                   cluster_fn=partial(fold.cluster_fn, min_size=m, tau=tau, use_books=bk,
                                      base=partial(combos.V21.cluster_fn, t=t)))


def settings():
    """[(setting, params, Variant)]; the v2.2 sweep first (K spread by t and the fold), then J and G."""
    sweep = [(0.30, 2, 0.6, True), (0.35, 2, 0.6, True), (0.40, 2, 0.6, True), (0.45, 2, 0.6, True),
             (0.50, 2, 0.6, True), (0.40, "mean", 0.5, False)]
    out = [("v2.2", f"t{t} m{m} tau{tau}" + (" bk" if bk else ""), v22(t, m, tau, bk)) for t, m, tau, bk in sweep]
    return out + [("J", J_KEY, combos22.CONFIGS[J_KEY]), ("G", G_KEY, staged.CONFIGS[G_KEY])]


def build(inp, v, docs, enc):
    """Spans mentions of variant v (seed 42), on a copy of the shared inputs."""
    spans = v.span_filter(list(inp.spans)) if v.span_filter else list(inp.spans)
    return MN.build("spans", docs, enc, SEED, inp=replace(inp, spans=spans, cluster_fn=v.cluster_fn)).mentions


def plot(df, n_attrs, path):
    """K on x, classes recovered on y; v2.2 as lines, J and G as single points; strict solid, recoverable hollow."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"v2.2": "#1f77b4", "J": "#d55e00", "G": "#009e73"}
    fig, ax = plt.subplots(figsize=(8, 5))
    for s, g in df.groupby("setting", sort=False):
        g = g.sort_values("K")
        for col, ls, fill in (("strict", "-", colors[s]), ("recoverable", "--", "white")):
            ax.plot(g["K"], g[col], ls, marker="o", color=colors[s], markerfacecolor=fill, markersize=7,
                    label=f"{s} {col}")
            for k, y in zip(g["K"], g[col]):
                ax.annotate(str(y), (k, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_xlabel("K (clusters)")
    ax.set_ylabel(f"gold classes recovered (of {n_attrs})")
    ax.set_ylim(0, n_attrs)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Loop 1: recall at K (strict: purity >= 0.6; recoverable: or >= 2 mentions inside, purity >= 0.25)")
    ax.title.set_fontsize(9)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/graph_v22_dev50", help="run dir: cache, docs, gold values")
    ap.add_argument("--split", choices=("dev", "test"), default="dev")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", default="results/loop1_check")
    ap.add_argument("--boot", type=int, default=1000, help="bootstrap resamples for the v2.2 point")
    args = ap.parse_args()
    run, out = (p if p.is_absolute() else paths.ROOT / p for p in (Path(args.run), Path(args.out)))
    docs, inp, enc = EX.prepare(args.split, args.limit, run, True)
    _, gv, attrs = MN.load_shared(run)
    frozen = MN.load(run / "spans").mentions
    rows, by_attr = [], None
    for setting, params, v in settings():
        t0 = time.time()
        m = build(inp, v, docs, enc)
        enc.save()
        if setting == "v2.2" and params == MAIN:  # the frozen T1 export: score it, after checking the rebuild matches
            key = ["dialogue_id", "char_start", "char_end", "cluster_id"]
            if not m[key].reset_index(drop=True).equals(frozen[key].reset_index(drop=True)):
                raise RuntimeError(f"rebuilt v2.2 differs from the frozen {run / 'spans'}")
            m = frozen
        tab = recall.recall_table(m, gv, attrs)
        r = dict(setting=setting, params=params, **recall.summary(m, tab))
        if setting == "v2.2" and params == MAIN:
            for k, (lo, hi) in recall.bootstrap(m, gv, attrs, n=args.boot).items():
                r[f"{k}_lo"], r[f"{k}_hi"] = lo, hi
            by_attr = tab
        rows.append(r)
        print(f"{setting} {params}: K {r['K']} strict {r['strict']} recoverable {r['recoverable']} "
              f"present {r['present']} ({time.time() - t0:.0f}s)", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "recall.csv", index=False, lineterminator="\n")
    by_attr.to_csv(out / "recall_by_attr.csv", index=False, lineterminator="\n")
    plot(df, len(attrs), out / "fig" / "loop1_recall_at_k.png")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
