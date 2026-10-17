# Shared settings for the Colab scripts. Source it: `source colab/env.sh`.
# Code comes from GitHub (this repo, cloned to /content/attribute-extraction); data and the
# surrogate come from Hugging Face; results are committed back to GitHub (colab/sync.sh).
export TEAR_PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT="$(dirname "$TEAR_PROJECT")"
export HF_DATA_REPO="${HF_DATA_REPO:-database-lab/attribute-extraction-data}"   # dataset: tear/ <-> tear/data/
export HF_MODEL_REPO="${HF_MODEL_REPO:-database-lab/tear-surrogate}"            # surrogate_conversation_cont2
export TEAR_MODELS="${TEAR_MODELS_LOCAL:-/content/models}"
export TEAR_LLAMA_TAG="${TEAR_LLAMA_TAG:-b11139}"
export TEAR_LLAMA_SERVER="/content/llama-server"
export TEAR_LLAMA_GGUF="$TEAR_MODELS/gguf/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
export TEAR_EMBED_GGUF="$TEAR_MODELS/gguf/ggml-sfr-embedding-mistral-q4_k_m.gguf"
export TEAR_LLAMA_ARGS="${TEAR_LLAMA_ARGS:--ngl 99}"
export TEAR_LOGS="$TEAR_PROJECT/results/colab_logs"   # not committed (.gitignore)
mkdir -p "$TEAR_LOGS"
case "$HF_DATA_REPO$HF_MODEL_REPO" in *HF_USER*) echo "Set the HF repo ids in tear/colab/env.sh (placeholder)"; return 1 2>/dev/null || exit 1;; esac
