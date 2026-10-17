"""Paper hyperparameters (HimathX/lk-hansard-topic-modeling, final v14) and paths."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
MODELS = Path(os.environ.get("HBE_MODELS", Path.home() / "hbe_models"))

# Pinned sources
REPO_RAW = "https://raw.githubusercontent.com/HimathX/lk-hansard-topic-modeling/main"
HF_DATASET = "sl-parliamentary-nlp/sl-parliamentary-hansard-17-26"
HF_REVISION = "48ace46ccab77cc3187d94ffb50d50bb75f83430"
BGE_M3_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"

# Embedding (generate_bge_m3_embeddings.ipynb)
MODEL_NAME = "BAAI/bge-m3"
MAX_SEQ_LEN = 8192
BATCH_SIZE = 1
NORMALIZE = True

# UMAP (run_macro_topic_modeling.ipynb, cell 8)
UMAP_PARAMS = dict(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine")
RANDOM_STATE = 42

# HDBSCAN (cell 2 / cell 10)
HDBSCAN_PARAMS = dict(min_cluster_size=10, min_samples=5, metric="euclidean",
                      cluster_selection_method="eom")

# Metrics (cell 16)
SILHOUETTE_SAMPLE = 5000

# Targets from the repo artifacts and the paper
TARGET_REPO = {
    "K": 336, "noise_pct": 35.4, "n_clustered": 12632,
    "silhouette": 0.5741, "calinski_harabasz": 15052.01, "davies_bouldin": 0.5148,
    "gold_n": 269, "gold_k_pred": 92, "purity": 0.6394, "bcubed_precision": 0.5567,
    "bcubed_recall": 0.2954, "bcubed_f1": 0.3859, "ari": 0.0625, "nmi": 0.4688,
}
TARGET_PAPER_TABLE3 = {  # arXiv 2608.20365 Table III, HDBSCAN row (288 speeches, 13 topics)
    "gold_n": 288, "gold_k_pred": 11, "noise_pct_gold": 41.7, "bcubed_precision": 0.673,
    "bcubed_f1": 0.313, "ari": 0.104, "nmi": 0.340, "silhouette": 0.532,
}
TARGET_PAPER_CORPUS = {"K": 336, "noise_pct": 35.4, "n_clustered": 12632}
