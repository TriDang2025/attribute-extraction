"""Node labels: rule labels from gold purity, a sheet for manual labelling, and merging it back."""

from collections import Counter

import numpy as np
import pandas as pd

VALID_NEW = ("valid_new", "noise")


def _classes(v) -> list[str]:
    return [c for c in (v if isinstance(v, str) else "").split(";") if c]


def gold_labels(mentions: pd.DataFrame, min_purity: float = 0.6) -> pd.DataFrame:
    """Per cluster: purity = top gold class count / all members (multi-class members count for each)."""
    m = mentions[mentions["cluster_id"].fillna("") != ""]
    rows = []
    for cid, g in m.groupby("cluster_id", sort=True):
        cnt = Counter(c for v in g["gold_attr"] for c in set(_classes(v)))
        attr, top = cnt.most_common(1)[0] if cnt else ("", 0)
        purity = top / len(g)
        is_gold = purity >= min_purity
        rows.append({"cluster_id": cid, "label": "gold" if is_gold else "unlabelled",
                     "gold_attr": attr if is_gold else "", "purity": purity, "label_by": "rule"})
    return pd.DataFrame(rows, columns=["cluster_id", "label", "gold_attr", "purity", "label_by"])


def sheet(mentions: pd.DataFrame, labels: pd.DataFrame, n: int = 50, seed: int = 0) -> pd.DataFrame:
    """Up to n non-gold nodes; one random pick per size-sorted slice so big and small clusters both appear."""
    cols = ["cluster_id", "entity", "n_mentions", "top_values", "examples", "label", "label_by"]
    ids = set(labels.loc[labels["label"] != "gold", "cluster_id"])
    m = mentions[mentions["cluster_id"].isin(ids)]
    info = []
    for cid, g in m.groupby("cluster_id", sort=True):
        vals = "|".join(v for v, _ in Counter(g["norm_value"]).most_common(5))
        ctx = [c for c in g["context"].fillna("") if c][:3]
        info.append({"cluster_id": cid, "entity": g["entity"].iloc[0], "n_mentions": len(g),
                     "top_values": vals, "examples": " || ".join(ctx), "label": "", "label_by": ""})
    df = pd.DataFrame(info, columns=cols)
    if len(df) > n:
        df = df.sort_values(["n_mentions", "cluster_id"]).reset_index(drop=True)
        rng = np.random.default_rng(seed)
        picks = [int(rng.choice(s)) for s in np.array_split(np.arange(len(df)), n)]
        df = df.iloc[picks]
    return df.reset_index(drop=True)


def merge_sheet(labels: pd.DataFrame, filled: pd.DataFrame) -> pd.DataFrame:
    """Copy label/label_by from the filled rows (label valid_new|noise); blank rows are ignored."""
    given = filled["label"].fillna("")
    bad = set(given) - set(VALID_NEW) - {""}
    if bad:
        raise ValueError(f"invalid labels in sheet: {sorted(bad)}")
    out = labels.copy()
    for _, r in filled[given.isin(VALID_NEW)].iterrows():
        hit = out["cluster_id"] == r["cluster_id"]
        if not hit.any():
            raise KeyError(f"cluster not in labels: {r['cluster_id']}")
        by = r.get("label_by")
        out.loc[hit, "label"] = r["label"]
        out.loc[hit, "label_by"] = by if isinstance(by, str) and by else "human"
    return out
