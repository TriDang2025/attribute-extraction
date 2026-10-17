"""Reproduce BGE-M3 -> UMAP -> HDBSCAN on the Sri Lankan Hansard corpus.

Stage A: HDBSCAN + metrics on the repo's committed UMAP output (data/umap5.npy).
Stage B: our UMAP (seeds) + HDBSCAN on our bge-m3 embeddings (data/hansard_bge_m3.npy,
         made by colab/embed_hansard_bge_m3.ipynb).

Usage (from HDBSCAN_BGE_E5/):  python -I scripts/reproduce_hansard.py [A|B|all] [--seeds 42 0 1]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hbe import cluster, config, data, metrics  # noqa: E402

OUT = config.RESULTS / "hansard"


def evaluate(name, emb5, labels, corpus, ref_labels):
    row = {"run": name, **metrics.internal(emb5, labels, config.SILHOUETTE_SAMPLE)}
    lab = pd.DataFrame({"speech_id": corpus["speech_id"], "cluster": labels})
    g = data.gold_join(lab)
    row.update(metrics.external(g["label"], g["cluster"]))
    agr = metrics.agreement(ref_labels, labels)
    row["ari_vs_repo"], row["nmi_vs_repo"] = agr["ari"], agr["nmi"]
    return row, lab


def load_reference(corpus):
    ref = pd.read_csv(config.DATA / "v11_cluster_assignments.csv")
    assert len(ref) == len(corpus), f"corpus {len(corpus)} vs repo {len(ref)}"
    assert (ref["speech_id"].values == corpus["speech_id"].values).all(), "row order differs from repo"
    return ref


def stage_a(corpus, ref):
    emb5 = np.load(config.DATA / "umap5.npy")
    assert len(emb5) == len(corpus)
    t = time.time()
    labels = cluster.hdbscan_labels(emb5)
    print(f"[A] HDBSCAN on committed umap5: {cluster.summary(labels)} ({time.time() - t:.0f}s)")
    row, lab = evaluate("A: repo umap5 -> our HDBSCAN", emb5, labels, corpus, ref["hdbscan_cluster"].values)
    # repo's own labels scored with our metric code (checks the metric code alone)
    row_ref, _ = evaluate("repo labels, our metrics", emb5, ref["hdbscan_cluster"].values, corpus,
                          ref["hdbscan_cluster"].values)
    lab.to_csv(OUT / "stage_a_labels.csv", index=False)
    return [row_ref, row]


def stage_b(corpus, ref, seeds):
    emb_path = config.DATA / "hansard_bge_m3.npy"
    ids_path = config.DATA / "hansard_ids.csv"
    if not emb_path.exists():
        print(f"[B] skipped: {emb_path} not found (run the Colab notebook first)")
        return []
    emb = np.load(emb_path)
    ids = pd.read_csv(ids_path)["speech_id"].values
    assert (ids == corpus["speech_id"].values).all(), "embedding rows do not match corpus order"
    print(f"[B] embeddings {emb.shape}, norms {np.linalg.norm(emb, axis=1).min():.3f}"
          f"-{np.linalg.norm(emb, axis=1).max():.3f}")
    repo5 = np.load(config.DATA / "umap5.npy")
    rows = []
    for seed in seeds:
        cache = OUT / f"umap5_seed{seed}.npy"
        if cache.exists():
            emb5 = np.load(cache)
        else:
            t = time.time()
            emb5 = cluster.umap_reduce(emb, seed=seed)
            np.save(cache, emb5)
            print(f"[B] UMAP seed {seed}: {time.time() - t:.0f}s")
        labels = cluster.hdbscan_labels(emb5)
        print(f"[B] seed {seed}: {cluster.summary(labels)}")
        row, lab = evaluate(f"B: our bge-m3 -> UMAP(seed {seed}) -> HDBSCAN", emb5, labels, corpus,
                            ref["hdbscan_cluster"].values)
        row["knn15_overlap_vs_repo_umap5"] = metrics.knn_overlap(emb5, repo5)
        lab.to_csv(OUT / f"stage_b_labels_seed{seed}.csv", index=False)
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="all", choices=["A", "B", "all"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 0, 1])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    corpus = data.hansard_corpus()
    print(f"corpus: {len(corpus)} speeches, ids checksum {data.ids_checksum(corpus['speech_id'])}")
    ref = load_reference(corpus)

    rows = [{"run": "target: repo artifacts", **config.TARGET_REPO},
            {"run": "target: paper Table III (HDBSCAN row)", **config.TARGET_PAPER_TABLE3}]
    if args.stage in ("A", "all"):
        rows += stage_a(corpus, ref)
    if args.stage in ("B", "all"):
        rows += stage_b(corpus, ref, args.seeds)

    table = pd.DataFrame(rows)
    name = f"results_{args.stage}"
    table.to_csv(OUT / f"{name}.csv", index=False)
    cols = ["run", "K", "noise_pct", "silhouette", "calinski_harabasz", "davies_bouldin", "gold_n",
            "gold_k_pred", "purity", "bcubed_precision", "bcubed_recall", "bcubed_f1", "ari", "nmi",
            "ari_vs_repo", "nmi_vs_repo", "knn15_overlap_vs_repo_umap5"]
    cols = [c for c in cols if c in table]
    (OUT / f"{name}.md").write_text(table[cols].to_markdown(index=False, floatfmt=".4f"), encoding="utf-8")
    print(table[cols].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    (OUT / "env.json").write_text(json.dumps(versions(), indent=1))


def versions():
    import hdbscan, sklearn, umap, numba  # noqa: E401
    return {"python": sys.version.split()[0], "hdbscan": hdbscan.__version__ if hasattr(hdbscan, "__version__") else "?",
            "umap": umap.__version__, "numba": numba.__version__, "sklearn": sklearn.__version__,
            "numpy": np.__version__, "pandas": pd.__version__}


if __name__ == "__main__":
    main()
