"""wf_v3.5 W4 (GT_V35_CONTRACT.md): role-word (J) and context-split role evidence for two-role clusters, and the train
instability list.

python scripts/roles_v35.py --run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 \
    --out results/loop1_v35 [--wait-min 40]
Reads <out>/gt_levels.csv (gt_L2, mention_id; waits up to --wait-min for it). Context vectors (bge-m3 of the turn with the
value replaced by "[V]", CPU) are cached in <out>/context_vectors.npz (ids, x); delete it to re-embed.
Writes <out>/{roles_j.csv, roles_context.csv, roles_summary.md, train_instability.csv}.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import roles_v35 as R  # noqa: E402
from s1a import rules_labels as RL  # noqa: E402
from s1a import v34_data as D  # noqa: E402

ENTS = ("train", "hotel", "restaurant")


def wait_for(path, minutes):
    deadline = time.time() + minutes * 60
    while not path.exists():
        if time.time() > deadline:
            raise SystemExit(f"{path} is still missing after {minutes} min")
        time.sleep(60)
    time.sleep(5)   # let the writer finish


def clustered_mentions(shared, data):
    """All clustered mentions of the 3 entities (unique index) with `local_start` = offset of the value in turn_text."""
    m = pd.concat([data[e].mentions.assign(ent=e) for e in ENTS], ignore_index=True)
    lo = [MN.turn_bounds(shared.docs[d], int(t))[0] for d, t in zip(m["dialogue_id"], m["turn"])]
    return m.assign(local_start=m["char_start"].astype(int) - np.asarray(lo))


def context_vectors(m, cache):
    """bge-m3 vectors of R.masked_texts(m), one row per m row, cached by mention_id in `cache` (npz: ids, x)."""
    ids = m["mention_id"].astype(int).to_numpy()
    if cache.exists():
        z = np.load(cache)
        if np.array_equal(z["ids"], ids):
            return z["x"]
    from run import encoder
    enc = encoder()
    x = np.asarray(enc.encode(R.masked_texts(m)), dtype=np.float32)   # the shared pkl is not saved: single writer
    np.savez(cache, ids=ids, x=x)
    return x


def table_md(df, cols):
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |"
                      for _, r in df.iterrows()])


def count(k, n):
    return f"{k}/{n} ({k / n:.3f})" if n else "0/0 (n/a)"


def summary(ent_of, j, ctx, two):
    parts = ["# Role evidence (wf_v3.5 T15, T16)", "",
             "Gold role = L2 slot of a role pair (train/taxi). Two-role cluster = both slots of one pair, each >= 20% of the "
             "cluster's labelled mentions. J = cue word (from/leave... start, to/arrive/by... end) among the 3 words before "
             "the value. Context split = KMeans k=2 on bge-m3 of the turn with the value as [V], split when silhouette >= "
             f"{R.SPLIT_THR}; each part takes its own majority gold role (upper bound: it uses the gold labels). "
             "accuracy = correct / covered, coverage = covered / gold-role mentions.", ""]
    for title, ids in (("Two-role clusters, all entities", set(two)),
                       ("Two-role clusters, train", {c for c in two if ent_of[c] == "train"}),
                       ("All clusters with a gold role", None)):
        pj, pc = R.pooled(j, ids), R.pooled(ctx, ids)
        parts += [f"## {title} ({pj['clusters']} clusters, {pj['n_gold_role']} gold-role mentions)", "",
                  f"- J: accuracy {count(pj['correct'], pj['covered'])}, coverage {count(pj['covered'], pj['n_gold_role'])}",
                  f"- context split: accuracy {count(pc['correct'], pc['covered'])}, "
                  f"coverage {count(pc['covered'], pc['n_gold_role'])}; clusters split "
                  f"{int((ctx[ctx['cluster_id'].isin(ids)] if ids is not None else ctx)['split'].sum())}", ""]
    both = j.merge(ctx, on="cluster_id", suffixes=("_j", "_ctx"))
    both = both[both["cluster_id"].isin(set(two))]
    both["pair"] = both["cluster_id"].map(lambda c: "/".join(two[c]))
    cols = ["cluster_id", "pair", "n_gold_role_j", "accuracy_j", "coverage_j", "split", "silhouette", "accuracy_ctx",
            "acc_nosplit"]
    parts += ["## Per two-role cluster", "", table_md(both, cols), ""]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--dir32", default="results/loop1_v32")
    ap.add_argument("--dir31", default="results/loop1_v31")
    ap.add_argument("--out", default="results/loop1_v35")
    ap.add_argument("--wait-min", type=float, default=40)
    a = ap.parse_args()
    out = paths.ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    shared, data = D.load_all(a.run, a.dir32, a.dir31)
    m = clustered_mentions(shared, data)
    x = context_vectors(m, out / "context_vectors.npz")
    gt_path = out / "gt_levels.csv"
    wait_for(gt_path, a.wait_min)
    gt = pd.read_csv(gt_path).drop_duplicates("mention_id").set_index("mention_id")["gt_L2"]
    l2 = m["mention_id"].astype(int).map(gt).fillna("").astype(str)
    pairs = RL.role_pairs()
    role = R.gold_role(l2, pairs)
    two = R.two_role_clusters(m, role, l2 != "", pairs)
    ent_of = dict(zip(m["cluster_id"], m["ent"]))
    flag = lambda df: df.assign(ent=df["cluster_id"].map(ent_of), two_role=df["cluster_id"].isin(set(two)),  # noqa: E731
                                pair=df["cluster_id"].map(lambda c: "/".join(two.get(c, ()))))
    j = R.role_word_eval(m, role, pairs)
    ctx = R.context_split(m, x, role, pairs=pairs)
    for name, df in (("roles_j", j), ("roles_context", ctx)):
        flag(df).to_csv(out / f"{name}.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "roles_summary.md").write_text(summary(ent_of, j, ctx, two), encoding="utf-8")
    inst = pd.concat([R.train_instability(data[e], l2[m["ent"] == e].set_axis(data[e].mentions.index), pairs)
                      for e in ENTS], ignore_index=True)
    inst.to_csv(out / "train_instability.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(f"two-role clusters {len(two)}; instability rows {len(inst)}; wrote {out}")


if __name__ == "__main__":
    main()
