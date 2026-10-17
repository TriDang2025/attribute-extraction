#!/usr/bin/env bash
# llama.cpp server for the Schema Coherence Score (tear_reproduction/coherence.py).
# Same Llama-3-8B-Instruct Q4_K_M GGUF as the chat endpoint; --poll 0 stops idle busy-waiting.
# Uses the same TEAR_* variables as tools/run_all.py; add "-ngl 99" to TEAR_LLAMA_ARGS on a GPU.
cd "$(dirname "$0")/.."
MODELS="${TEAR_MODELS:-models}"
SERVER="${TEAR_LLAMA_SERVER:-tools/llama.cpp/bin/llama-server}"
[ -x "$SERVER" ] || SERVER="$SERVER.exe"
exec "$SERVER" -m "${TEAR_LLAMA_GGUF:-$MODELS/gguf/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf}" \
  --port 8081 -c 8192 -np 4 --poll 0 --no-webui ${TEAR_LLAMA_ARGS:--t 10}
