"""Task 3: cluster stability under dialogue resampling and re-clustering seeds."""
import random
import time
from collections import Counter

import pandas as pd


def _members(mentions: pd.DataFrame) -> dict[str, set]:
    m = mentions[mentions["cluster_id"] != ""]
    keys = zip(m["dialogue_id"], m["char_start"], m["char_end"])
    out: dict[str, set] = {}
    for c, k in zip(m["cluster_id"], keys):
        out.setdefault(c, set()).add(k)
    return out


def _best_jaccard(base_members: set, new_of: dict, new_size: dict) -> float:
    hits = Counter(new_of[k] for k in base_members if k in new_of)
    if not hits:
        return 0.0
    return max(i / (len(base_members) + new_size[c] - i) for c, i in hits.items())


def stability_scores(input, docs, enc, base, seeds=(0, 1, 2), n_resamples=5, frac=0.8,
                     rng_seed=0, build_fn=None) -> pd.Series:
    """Mean over runs of the best Jaccard between each base cluster and any re-built cluster."""
    if build_fn is None:
        from s1a import mentions
        build_fn = mentions.build
    rng = random.Random(rng_seed)
    ids = sorted(docs)
    bm = base.mentions[base.mentions["cluster_id"] != ""]
    base_cl = {}
    for c, d, s, e in zip(bm["cluster_id"], bm["dialogue_id"], bm["char_start"], bm["char_end"]):
        base_cl.setdefault(c, []).append((d, (d, s, e)))
    scores: dict[str, list[float]] = {c: [] for c in base_cl}
    runs = [(s, r) for s in seeds for r in range(n_resamples)]
    for n, (seed, r) in enumerate(runs, 1):
        t0 = time.time()
        sample = set(rng.sample(ids, max(1, round(frac * len(ids)))))
        new = build_fn(input, {d: docs[d] for d in sorted(sample)}, enc, seed)
        new_m = _members(new.mentions)
        new_of = {k: c for c, ks in new_m.items() for k in ks}
        new_size = {c: len(ks) for c, ks in new_m.items()}
        for c, items in base_cl.items():
            mem = {k for d, k in items if d in sample}
            if mem:
                scores[c].append(_best_jaccard(mem, new_of, new_size))
        print(f"stability run {n}/{len(runs)} (seed {seed}, resample {r}): {time.time() - t0:.1f}s", flush=True)
    return pd.Series({c: (sum(v) / len(v) if v else float("nan")) for c, v in scores.items()},
                     name="stability", dtype=float).rename_axis("cluster_id")
