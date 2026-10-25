"""Node selection: signal AUCs, signal choice, combined score, support/score sweep, pick, apply."""

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

REAL = ("gold", "valid_new")


def _real_noise(nodes: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    """nodes with a 0/1 `y` (1 = real, 0 = noise); unlabelled rows dropped."""
    lab = labels.set_index("cluster_id")["label"]
    d = nodes.assign(label=nodes["cluster_id"].map(lab))
    d = d[d["label"].isin(REAL + ("noise",))]
    return d.assign(y=d["label"].isin(REAL).astype(int))


def auc_table(nodes, labels, signals, n_boot=1000, seed=0) -> pd.DataFrame:
    """Per signal: auc, direction, auc_oriented, bootstrap 95% range (lo, hi) of the oriented auc, class sizes."""
    d = _real_noise(nodes, labels)
    rng = np.random.default_rng(seed)
    rows = []
    for s in signals:
        x = d[[s, "y"]].dropna()
        v, y = x[s].to_numpy(float), x["y"].to_numpy()
        row = {"signal": s, "auc": np.nan, "direction": 0, "auc_oriented": np.nan, "lo": np.nan, "hi": np.nan,
               "n_real": int(y.sum()), "n_noise": int(len(y) - y.sum())}
        if 0 < y.sum() < len(y):
            auc = roc_auc_score(y, v)
            sign = 1 if auc >= 0.5 else -1
            boots = []
            for _ in range(n_boot):
                i = rng.integers(0, len(y), len(y))
                if 0 < y[i].sum() < len(i):
                    a = roc_auc_score(y[i], v[i])
                    boots.append(a if sign > 0 else 1 - a)
            row.update(auc=auc, direction=sign, auc_oriented=max(auc, 1 - auc))
            if boots:
                row["lo"], row["hi"] = np.percentile(boots, [2.5, 97.5])
        rows.append(row)
    return pd.DataFrame(rows)


def correlations(nodes, signals) -> pd.DataFrame:
    return nodes[list(signals)].corr(method="spearman")


def choose(auc, corr, k_min=3, k_max=5, corr_max=0.8) -> list[tuple[str, str]]:
    """Greedy by auc_oriented; skip a signal with |rho| > corr_max against one already chosen.
    Returns [(signal, reason)], at most k_max. Fewer than k_min come back only if candidates ran out."""
    chosen: list[tuple[str, str]] = []
    for _, r in auc.dropna(subset=["auc_oriented"]).sort_values("auc_oriented", ascending=False).iterrows():
        if len(chosen) >= k_max:
            break
        s = r["signal"]
        rho = [abs(corr.loc[s, c]) for c, _ in chosen]
        if any(x > corr_max for x in rho):
            continue
        chosen.append((s, f"auc {r['auc_oriented']:.3f} (direction {int(r['direction']):+d}), "
                          f"max |rho| with chosen {max(rho, default=0):.2f}"))
    return chosen


def combine(nodes, chosen, directions, method="rank") -> pd.Series:
    """rank: mean oriented percentile rank in [0,1], high = keep. weak2: -(number of chosen signals in the
    bottom oriented tercile). Missing values are skipped in the mean and never count as weak."""
    names = [c[0] if isinstance(c, tuple) else c for c in chosen]
    ranks = pd.DataFrame({s: (nodes[s] * directions[s]).rank(pct=True) for s in names}, index=nodes.index)
    if method == "rank":
        return ranks.mean(axis=1)
    if method == "weak2":
        return -(ranks <= 1 / 3).sum(axis=1).astype(float)
    raise ValueError(method)


def sweep(nodes, labels, score, gold_attrs, thetas=(0.05, 0.10, 0.20), thresholds=None,
          value_cov_fn=None) -> pd.DataFrame:
    """One row per (theta, threshold). Kept = wilson_hi >= theta and score >= threshold."""
    score = np.asarray(score, float)
    if thresholds is None:
        thresholds = np.unique(np.nanquantile(score, np.linspace(0, 1, 21)))
    lab = labels.set_index("cluster_id")
    label = nodes["cluster_id"].map(lab["label"]).fillna("unlabelled").to_numpy()
    attr = nodes["cluster_id"].map(lab["gold_attr"]).fillna("").to_numpy()
    real = np.isin(label, REAL)
    labelled = real | (label == "noise")
    in_gold = np.isin(attr, list(gold_attrs)) & (label == "gold")
    cids = nodes["cluster_id"].to_numpy()
    wilson_hi = nodes["wilson_hi"].to_numpy(float)
    rows = []
    for theta in thetas:
        sup = wilson_hi >= theta
        for t in thresholds:
            kept = sup & (score >= t)
            nl = int((kept & labelled).sum())
            covered = len(set(attr[kept & in_gold]))
            rows.append({
                "theta": theta, "threshold": t, "kept": int(kept.sum()),
                "node_precision": (kept & real).sum() / nl if nl else np.nan, "n_labelled_kept": nl,
                "attr_covered": covered, "attr_coverage": covered / len(gold_attrs),
                "value_coverage": value_cov_fn(list(cids[kept])) if value_cov_fn else np.nan,
                "llm_saved": int(len(nodes) - kept.sum()),
            })
    return pd.DataFrame(rows)


def pick(sweep_df, target_prec=0.8, min_attrs=30) -> pd.Series:
    """Among rows with precision >= target and >= min_attrs gold classes: the most gold classes kept, then
    the fewest kept nodes (attributes lost cannot be recovered later; extra nodes only cost LLM calls).
    Else the highest-precision row among those with >= min_attrs (all rows if none reach it).
    `target_met` flags which case."""
    okc = sweep_df[sweep_df["attr_covered"] >= min_attrs]
    hit = okc[okc["node_precision"] >= target_prec]
    if len(hit):
        row = hit.sort_values(["attr_covered", "kept", "node_precision"], ascending=[False, True, False]).iloc[0]
        return pd.concat([row, pd.Series({"target_met": True})])
    pool = (okc if len(okc) else sweep_df).dropna(subset=["node_precision"])
    row = pool.sort_values(["node_precision", "kept"], ascending=[False, True]).iloc[0]
    return pd.concat([row, pd.Series({"target_met": False})])


def apply(nodes, score, theta, threshold) -> pd.DataFrame:
    """nodes + score + status (kept|dropped) + reason (support|score|""); dropped rows stay."""
    out = nodes.copy()
    out["score"] = np.asarray(score, float)
    no_support = ~(out["wilson_hi"] >= theta)
    low = ~(out["score"] >= threshold)
    out["status"] = np.where(no_support | low, "dropped", "kept")
    out["reason"] = np.where(no_support, "support", np.where(low, "score", ""))
    return out


def plot_curve(sweep_df, path, picked=None, target_prec=0.8, min_attrs=30) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    picked = pick(sweep_df, target_prec, min_attrs) if picked is None else picked
    fig, ax = plt.subplots(figsize=(6, 4))
    for theta, g in sweep_df.groupby("theta"):
        g = g.sort_values("attr_covered")
        ax.plot(g["attr_covered"], g["node_precision"], marker=".", label=f"theta {theta:g}")
    ax.plot([picked["attr_covered"]], [picked["node_precision"]], "k*", ms=14, label="picked")
    ax.axhline(target_prec, ls=":", c="grey")
    ax.set_xlabel("gold attributes kept")
    ax.set_ylabel("node precision")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
