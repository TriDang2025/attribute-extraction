#!/usr/bin/env bash
# Size-constrained semantic chunking on Colab: setting S, then T with seeds 42 0 1. Resumable.
#   bash colab/run_colab.sh          # starts in the background; progress in results/colab_logs/chk.log
#   bash colab/run_colab.sh status
# Data (MultiWOZ zip, dialogue ids) comes from Hugging Face; chunks and metrics are committed to
# GitHub every 30 min and after each run, so a new VM skips documents already chunked.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/results/colab_logs"; mkdir -p "$LOGS"   # not committed (.gitignore)
LOG="$LOGS/chk.log"; PIDFILE="$LOGS/chk.pid"
VENV=/content/chk_venv
export CHK_MODELS=/content/chk_models CHK_BATCH=64

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
  echo "$(date "+%F %T") CHK_FAILED (line $1)"
  [ -n "${SAVER:-}" ] && kill "$SAVER" 2>/dev/null
  bash colab/sync.sh push-results "failed" || true
}
trap 'fail $LINENO' ERR
cd "$ROOT"

step "hf CLI (colab/sync.sh uses it)"
pip install -q "huggingface_hub>=0.34"

step "venv with the pinned versions (uses Colab's CUDA torch)"
# --without-pip: Colab's Python lacks ensurepip; the system pip installs into the venv.
if [ ! -x "$VENV/bin/python" ]; then python -m venv --without-pip --system-site-packages "$VENV"; fi
"$VENV/bin/python" -m pip install -q -r requirements.txt
export PY="$VENV/bin/python"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

step "data (Hugging Face)"
(cd "$ROOT/.." && git pull -q --rebase --autostash)
bash colab/sync.sh pull-data

step "models (pinned revisions) and NLTK stopwords"
"$PY" - <<'EOF'
import os
import nltk
from huggingface_hub import snapshot_download
from chk import config
m = os.environ["CHK_MODELS"]
snapshot_download("BAAI/bge-m3", revision=config.BGE_M3_REVISION, local_dir=f"{m}/bge-m3",
                  allow_patterns=["*.json", "*.model", "pytorch_model.bin", "1_Pooling/*"])
snapshot_download("minishlab/potion-base-32M", revision=config.POTION_REVISION,
                  local_dir=f"{m}/potion-base-32M", allow_patterns=["*.json", "*.txt", "model.safetensors"])
nltk.download("stopwords", quiet=True)
print("models ready")
EOF

step "tests"
"$PY" -m pytest -q tests | tail -2

( while sleep 1800; do bash colab/sync.sh push-results "progress" || true; done ) &
SAVER=$!
step "setting S (1,000 single dialogues)"
"$PY" -W ignore scripts/run.py --setting S
bash colab/sync.sh push-results "S done" || true
for seed in 42 0 1; do
  step "setting T seed $seed (50 stitched documents)"
  "$PY" -W ignore scripts/run.py --setting T --seed "$seed"
  bash colab/sync.sh push-results "T seed $seed done" || true
done
kill "$SAVER" 2>/dev/null || true; SAVER=

step "commit results to GitHub"
bash colab/sync.sh push-results "all runs"
step "CHK_DONE"
