"""wf_v5.0 G5 freeze rule (diary Nov 23, final): rule 1 (step4_pick_v49.chain_problems) may fail in at most MAX_BAD of the 6 chains (3 seeds x
2 sets); among the variants that pass, the highest table F1 + grouping F1 (mean over seeds, summed over sets) is frozen; GT columns placed more
than TOL below the best variant is not a filter, only a limit to write down. No variants after this one.
"""
from . import step4_pick_v49 as PK

MAX_BAD = 1
TOL = PK.TOL


def freeze(df, seeds=(0, 1, 2), max_bad=MAX_BAD, tol=TOL):
    """(frozen variant or None, {variant: {"bad_chains", "rule1": (ok, reason), "limit": str, "score"}}). df as step4_pick_v49.pick."""
    _, res = PK.pick(df, seeds, tol)
    sets = sorted(df["set"].unique())
    out = {}
    for v, r in res.items():
        probs = {(dev, s): PK.chain_problems(df, v, dev, s) for dev in sets for s in seeds}
        bad = [w for w in probs.values() if w]
        out[v] = {"bad_chains": len(bad), "rule1": (len(bad) <= max_bad, "; ".join(x for w in bad for x in w) or "ok"),
                  "limit": "" if r["rule2"][0] else r["rule2"][1], "score": r["score"]}
    ok = {v: r["score"] for v, r in out.items() if r["rule1"][0] and r["score"] is not None}
    return (max(ok, key=ok.get) if ok else None), out
