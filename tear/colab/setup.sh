#!/usr/bin/env bash
# Per-session setup on a Colab GPU runtime. Safe to rerun.
#   bash colab/setup.sh
# 1. checks the GPU  2. installs Python packages  3. data + surrogate from Hugging Face
# 4. llama-server with CUDA (cached on HF per GPU type; built once otherwise)  5. GGUFs  6. unit tests
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$TEAR_PROJECT"
mkdir -p "$TEAR_MODELS/gguf"

echo "== GPU"
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader || { echo "No GPU: Runtime > Change runtime type > L4 or A100"; exit 1; }
MEM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
ARCH=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d .)
if [ "$MEM_MB" -lt 20000 ]; then
  echo "WARNING: ${MEM_MB} MB GPU memory. The coherence step runs 3 llama servers (~15 GB); use L4 or A100, not T4."
fi

echo "== Python packages (keeps Colab's CUDA torch)"
pip install -q "transformers>=4.56" accelerate "bert-score==0.3.13" gguf safetensors tokenizers "huggingface_hub>=0.34"

echo "== data and surrogate (Hugging Face)"
bash colab/sync.sh pull-data

echo "== llama-server ($TEAR_LLAMA_TAG, CUDA sm_$ARCH)"
BIN="llama-server-$TEAR_LLAMA_TAG-sm$ARCH"
if hf download "$HF_DATA_REPO" "cache/$BIN" --repo-type dataset --local-dir /content/hf_cache --quiet >/dev/null 2>&1; then
  cp "/content/hf_cache/cache/$BIN" "$TEAR_LLAMA_SERVER"
  echo "from HF cache"
else
  echo "building once for this GPU type (about 10-20 min)"
  rm -rf /content/llama.cpp
  git clone -q --depth 1 --branch "$TEAR_LLAMA_TAG" https://github.com/ggml-org/llama.cpp /content/llama.cpp
  cmake -S /content/llama.cpp -B /content/llama.cpp/build -DGGML_CUDA=ON -DBUILD_SHARED_LIBS=OFF \
    -DLLAMA_CURL=OFF -DCMAKE_CUDA_ARCHITECTURES="$ARCH" -DCMAKE_BUILD_TYPE=Release > "$TEAR_LOGS/llama_build.log" 2>&1
  cmake --build /content/llama.cpp/build --target llama-server -j"$(nproc)" >> "$TEAR_LOGS/llama_build.log" 2>&1 \
    || { echo "build failed, see $TEAR_LOGS/llama_build.log"; exit 1; }
  cp /content/llama.cpp/build/bin/llama-server "$TEAR_LLAMA_SERVER"
  hf upload "$HF_DATA_REPO" "$TEAR_LLAMA_SERVER" "cache/$BIN" --repo-type dataset \
    --commit-message "cache $BIN" --quiet >/dev/null && echo "cached on HF" || echo "could not cache on HF (read-only token?)"
fi
chmod +x "$TEAR_LLAMA_SERVER"

echo "== GGUF models (public Hugging Face repos)"
fetch() {  # name url bytes
  local path="$TEAR_MODELS/gguf/$1"
  if [ "$(stat -c %s "$path" 2>/dev/null || echo 0)" = "$3" ]; then echo "$1 ok"; return; fi
  echo "$1: downloading"; curl -L -C - -s -S -o "$path" "$2"
  [ "$(stat -c %s "$path")" = "$3" ] || { echo "$1: wrong size"; exit 1; }
}
fetch Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \
  https://huggingface.co/lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf 4920733888
fetch ggml-sfr-embedding-mistral-q4_k_m.gguf \
  https://huggingface.co/dranger003/SFR-Embedding-Mistral-GGUF/resolve/main/ggml-sfr-embedding-mistral-q4_k_m.gguf 4368439008

echo "== unit tests"
python -m unittest tests.test_metrics tests.test_retrieval tests.test_pipeline tests.test_surrogate \
  tests.test_reproduce tests.test_client 2>&1 | tail -3
echo "SETUP_DONE"
