#!/usr/bin/env bash
# Starts the chat model (port 1234) and the SFR embedder (port 8082) on the GPU, in the background.
# run_all.py starts the third server (coherence scorer, port 8081) itself. Safe to rerun.
#   bash colab/start_servers.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"

up() { curl -s "http://localhost:$1/health" 2>/dev/null | grep -q ok; }

start() {  # port log args...
  local port=$1 log=$2; shift 2
  if up "$port"; then echo "port $port already up"; return; fi
  setsid nohup "$TEAR_LLAMA_SERVER" --port "$port" --no-webui -ngl 99 "$@" > "$TEAR_LOGS/$log" 2>&1 &
  echo "port $port starting (log: $TEAR_LOGS/$log)"
}

# Same settings as the laptop run (README 2.5): 8K context, one slot.
start 1234 server_chat.log -m "$TEAR_LLAMA_GGUF" -c 8192 -np 1
start 8082 server_embed.log -m "$TEAR_EMBED_GGUF" -c 4096 -np 1 --embedding --pooling last

for port in 1234 8082; do
  for _ in $(seq 120); do up "$port" && break; sleep 3; done
  up "$port" && echo "port $port ok" || { echo "port $port failed; see $TEAR_LOGS"; exit 1; }
done
echo "SERVERS_UP"
