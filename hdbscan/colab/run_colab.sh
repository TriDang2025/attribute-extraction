#!/usr/bin/env bash
# BGE-M3 -> UMAP -> HDBSCAN on Colab: Hansard reproduction, then Conversation. Resumable.
#   bash colab/run_colab.sh          # starts in the background; progress in results/colab_logs/hbe.log
#   bash colab/run_colab.sh status
# Data comes from Hugging Face and the paper's public sources; embeddings go back to HF every
# 30 min (so a new VM resumes them); result tables are committed to GitHub at the end.
# Any Colab GPU works (the paper used a T4).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/results/colab_logs"; mkdir -p "$LOGS"   # not committed (.gitignore)
LOG="$LOGS/hbe.log"; PIDFILE="$LOGS/hbe.pid"
VENV=/content/hbe_venv
export HBE_MODELS=/content/hbe_models

running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

if [ "${1:-}" = status ]; then
  running && echo "running (pid $(cat "$PIDFILE"))" || echo "not running"
  tail -n 8 "$LOG" 2>/dev/null
  (cd "$ROOT/.." && git log -1 --format="last commit: %h %an %ar  %s" && git status -sb | head -1); exit 0
fi
if [ "${1:-}" != _worker ]; then
  running && { echo "already running; bash colab/run_colab.sh status"; exit 1; }
  setsid nohup bash "$0" _worker >> "$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  echo "started (pid $!). Progress: $LOG  (bash colab/run_colab.sh status)"; exit 0
fi

# ---- worker ----
step() { echo "$(date "+%F %T") == $*"; }
fail() {
  echo "$(date "+%F %T") HBE_FAILED (line $1)"
  [ -n "${SAVER:-}" ] && kill "$SAVER" 2>/dev/null
  bash colab/sync.sh push-data || true
  bash colab/sync.sh push-results "failed" || true
}
trap 'fail $LINENO' ERR
cd "$ROOT"

step "venv with the repo's pinned versions (uses Colab's CUDA torch)"
# --without-pip: Colab's Python lacks ensurepip; the system pip installs into the venv.
if [ ! -x "$VENV/bin/python" ]; then python -m venv --without-pip --system-site-packages "$VENV"; fi
"$VENV/bin/python" -m pip install -q -r requirements.txt
export PY="$VENV/bin/python"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

step "data (Hugging Face + public sources)"
(cd "$ROOT/.." && git pull -q --rebase --autostash)
bash colab/sync.sh pull-data

step "bge-m3 (pinned revision)"
"$PY" - <<'EOF'
import os
from huggingface_hub import snapshot_download
from hbe import config
snapshot_download(config.MODEL_NAME, revision=config.BGE_M3_REVISION,
                  local_dir=os.path.join(os.environ["HBE_MODELS"], "bge-m3"))
EOF

step "tests"
"$PY" -m pytest -q tests | tail -2

step "embeddings (Hansard then Conversation); saved to HF every 30 min"
"$PY" -I scripts/run_conversation.py export
( while sleep 1800; do bash colab/sync.sh push-data || true; done ) &
SAVER=$!
"$PY" -I scripts/embed_all.py --model "$HBE_MODELS/bge-m3"
kill "$SAVER" 2>/dev/null || true; SAVER=
bash colab/sync.sh push-data

step "Hansard: Stage A (repo UMAP) and Stage B (our embeddings, seeds 42 0 1)"
"$PY" -I scripts/reproduce_hansard.py all

step "Conversation: paper settings + min_cluster_size sweep"
"$PY" -I scripts/run_conversation.py run

step "commit results to GitHub"
bash colab/sync.sh push-results "Hansard A+B, Conversation sweep"
step "HBE_DONE"
