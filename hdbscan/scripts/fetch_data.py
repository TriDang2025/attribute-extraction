"""Download the inputs into data/ with resumable curl (python -I scripts/fetch_data.py)."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hbe import config  # noqa: E402

REPO_FILES = {
    "data/evaluation/ground_truth_300.csv": "ground_truth_300.csv",
    "artifacts/final_v14/umap5.npy": "umap5.npy",
    "artifacts/final_v14/v11_cluster_assignments.csv": "v11_cluster_assignments.csv",
    "artifacts/final_v14/v11_metrics.csv": "v11_metrics.csv",
    "artifacts/evaluation/table_iii_metrics.csv": "table_iii_metrics.csv",
    # source code, for reference only
    "src/modeling/generate_bge_m3_embeddings.ipynb": "repo_src/generate_bge_m3_embeddings.ipynb",
    "src/modeling/run_macro_topic_modeling.ipynb": "repo_src/run_macro_topic_modeling.ipynb",
    "src/ingestion/build_speech_corpus.py": "repo_src/build_speech_corpus.py",
    "src/evaluation/classification_metrics.py": "repo_src/classification_metrics.py",
    "src/evaluation/run_evaluation.py": "repo_src/run_evaluation.py",
}
HF = f"https://huggingface.co/datasets/{config.HF_DATASET}/resolve/{config.HF_REVISION}/data"


def get(url, dest):
    dest = config.DATA / dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sS", "-L", "-C", "-", "--retry", "10", "-o", str(dest), url], check=True)
    print(f"{dest.relative_to(config.ROOT)}  {dest.stat().st_size:,} bytes")


def main():
    for src, dest in REPO_FILES.items():
        get(f"{config.REPO_RAW}/{src}", dest)
    for split in ("train", "test"):
        get(f"{HF}/{split}-00000-of-00001.parquet", f"hf/{split}.parquet")


if __name__ == "__main__":
    main()
