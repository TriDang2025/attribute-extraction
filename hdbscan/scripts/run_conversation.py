"""BGE-M3 -> UMAP -> HDBSCAN on the 1,000 Conversation (MultiWOZ) dialogues.

  python -I scripts/run_conversation.py export   # write colab/conversation_texts.jsonl
  python -I scripts/run_conversation.py run      # needs data/conversation_bge_m3.npy

Same settings as the paper, then a min_cluster_size sweep. External labels: the domain
set of each gold table (e.g. "Attraction+Train") and the main domain.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hbe import cluster, config, data, metrics  # noqa: E402

OUT = config.RESULTS / "conversation"
TEXTS = config.ROOT / "colab" / "conversation_texts.jsonl"
SWEEP = [5, 10, 20, 40]


def export():
    df = data.conversation()
    with open(TEXTS, "w", encoding="utf-8") as f:
        for r in df.itertuples():
            f.write(json.dumps({"id": r.id, "text": r.text}, ensure_ascii=False) + "\n")
    print(f"wrote {len(df)} dialogues to {TEXTS}")


def run(seeds=(42, 0, 1)):
    OUT.mkdir(parents=True, exist_ok=True)
    df = data.conversation()
    ids = [json.loads(l)["id"] for l in open(TEXTS, encoding="utf-8")]
    assert ids == df["id"].tolist(), "conversation_texts.jsonl does not match the dataset order"
    emb = np.load(config.DATA / "conversation_bge_m3.npy")
    assert emb.shape[0] == len(df)
    print(f"{len(df)} dialogues; domain sets: {df.domain_set.nunique()}, main domains: {df.main_domain.nunique()}")

    rows = []
    for seed in seeds:
        emb5 = cluster.umap_reduce(emb, seed=seed)
        for mcs in SWEEP:
            ms = min(config.HDBSCAN_PARAMS["min_samples"], mcs)
            labels = cluster.hdbscan_labels(emb5, min_cluster_size=mcs, min_samples=ms)
            row = {"seed": seed, "min_cluster_size": mcs, "min_samples": ms,
                   **metrics.internal(emb5, labels, config.SILHOUETTE_SAMPLE)}
            for target in ("domain_set", "main_domain"):
                ext = metrics.external(df[target], labels)
                row.update({f"{target}:{k}": v for k, v in ext.items()
                            if k in ("purity", "bcubed_precision", "bcubed_recall", "bcubed_f1", "ari", "nmi")})
            # same metrics on clustered points only (noise removed)
            m = labels != -1
            ext = metrics.external(df["domain_set"][m], labels[m])
            row["domain_set:nmi_clustered_only"] = ext["nmi"]
            rows.append(row)
            if seed == 42 and mcs == config.HDBSCAN_PARAMS["min_cluster_size"]:
                save_clusters(df, labels)
            print(f"seed {seed} mcs {mcs}: {cluster.summary(labels)}")
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "sweep.csv", index=False)
    mean = table.drop(columns="seed").groupby(["min_cluster_size", "min_samples"]).agg(["mean", "std"])
    mean.columns = [f"{a} ({b})" for a, b in mean.columns]
    mean.to_csv(OUT / "sweep_mean.csv")
    print(mean.filter(like="(mean)").round(3).to_string())


def save_clusters(df, labels):
    """Paper config (seed 42): cluster sizes and their domain make-up."""
    d = df.assign(cluster=labels)
    d[["id", "domain_set", "main_domain", "cluster"]].to_csv(OUT / "labels_paper_config.csv", index=False)
    comp = (d.groupby("cluster")["domain_set"]
            .agg(size="size", top=lambda s: s.value_counts().index[0],
                 top_share=lambda s: s.value_counts(normalize=True).iloc[0]))
    comp.to_csv(OUT / "clusters_paper_config.csv")


if __name__ == "__main__":
    {"export": export, "run": run}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
