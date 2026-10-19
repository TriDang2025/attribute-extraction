"""Paths and the published settings of each chunker."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
CACHE = DATA / "cache"
MODELS = Path(os.environ.get("CHK_MODELS", Path.home() / "models"))

MULTIWOZ_ZIP = DATA / "MULTIWOZ2.4.zip"
IDS = DATA / "conversation_ids.txt"
TEXTS = DATA / "conversation_texts.jsonl"  # the HDBSCAN copy, used only as a check


def model_path(local, hub):
    p = MODELS / local
    return str(p) if (p / "config.json").exists() else hub


BGE_M3 = model_path("bge-m3", "BAAI/bge-m3")
POTION = model_path("potion-base-32M", "minishlab/potion-base-32M")
# revisions of the laptop copies; colab/run_colab.sh downloads exactly these
BGE_M3_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
POTION_REVISION = "1e5a03f8eeb2c98b928fbbd846f22f816360919f"
BGE_BATCH = int(os.environ.get("CHK_BATCH", 16))
BGE_MAX_LEN = 8192

# 1. Recursive Semantic Chunking (Latif et al., ICNLSP 2025, Algorithm 1), lengths in characters
RSC = dict(t_max=15_000, t_chunk=1_500, t_final=2_500, t_merge=350, delta=3,
           start_percentile=95,   # LangChain SemanticChunker default (paper: "initial semantic chunking")
           floor_percentile=50)   # ours: the paper gives no stopping point for the recursion

# 2. Chroma ClusterSemanticChunker (chunking_evaluation @ e708410), lengths in cl100k tokens
CHROMA = dict(max_chunk_size=400, min_chunk_size=50)

# 3. Chonkie SemanticChunker 1.7.0 defaults, chunk_size in the embedding model's tokens
CHONKIE = dict(threshold=0.8, chunk_size=2048, similarity_window=3, min_sentences_per_chunk=1,
               min_characters_per_sentence=24, skip_window=0, filter_window=5,
               filter_polyorder=3, filter_tolerance=0.2)

# Baselines
FIXED = dict(chunk_size=400, chunk_overlap=0)  # cl100k tokens
TEXTTILING = dict(w=20, k=10)                  # NLTK defaults

# Stitched setting
STITCH_SIZE = 20
STITCH_SEEDS = (42, 0, 1)
TOP_K = (1, 3, 5)
