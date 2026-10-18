#!/usr/bin/env bash
# Moves data between this Colab VM, Hugging Face and GitHub.
#   bash colab/sync.sh pull-data          HF dataset tear/ -> tear/data/ (keeps local files), surrogate -> $TEAR_MODELS
#   bash colab/sync.sh push-data          tear/data/conversation caches that runs grow -> HF (only if changed)
#   bash colab/sync.sh push-results MSG   commit tear/results/ and push to GitHub (rebases on others' commits)
# Auth: HF from `huggingface_hub.login` / HF_TOKEN; GitHub from the GH_TOKEN env var + credential helper set by notebook cell 1.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$TEAR_PROJECT"
GROWN=(conversation/embeddings_sfr-embedding-mistral-q4_k_m.json conversation/previews.jsonl)

pull_data() {
  hf download "$HF_DATA_REPO" --repo-type dataset --include "tear/*" --local-dir /content/hf_data --quiet >/dev/null
  mkdir -p data
  cp -rn /content/hf_data/tear/. data/   # -n: never overwrite files this session already updated
  if [ ! -f "$TEAR_MODELS/surrogate_conversation_cont2/model.safetensors" ]; then
    hf download "$HF_MODEL_REPO" --local-dir "$TEAR_MODELS/surrogate_conversation_cont2" --quiet >/dev/null
  fi
  echo "data and surrogate ready"
}

push_data() {
  local stamp=/content/.tear_data_md5 now
  now=$(cd data && md5sum "${GROWN[@]}" 2>/dev/null || true)
  if [ -f "$stamp" ] && [ "$now" = "$(cat "$stamp")" ]; then echo "data unchanged"; return; fi
  for f in "${GROWN[@]}"; do
    [ -f "data/$f" ] && hf upload "$HF_DATA_REPO" "data/$f" "tear/$f" --repo-type dataset \
      --commit-message "tear data: $f" --quiet >/dev/null
  done
  echo "$now" > "$stamp"
  echo "data pushed to $HF_DATA_REPO"
}

push_results() {
  local msg="results: ${1:-update} $(date -u '+%F %H:%M') UTC"
  cd "$REPO_ROOT"
  git add tear/results
  if git diff --cached --quiet; then echo "results unchanged"; return; fi
  git commit -q -m "$msg"
  for attempt in 1 2 3; do
    if git pull -q --rebase --autostash && git push -q; then echo "pushed: $msg"; return; fi
    git rebase --abort 2>/dev/null || true
    echo "push attempt $attempt failed; retrying"; sleep 20
  done
  echo "PUSH_FAILED: results are committed locally; run this again or ask the user"; return 1
}

case "${1:-}" in
  pull-data) pull_data ;;
  push-data) push_data ;;
  push-results) push_results "${2:-}" ;;
  *) echo "usage: bash colab/sync.sh pull-data|push-data|push-results [MSG]"; exit 1 ;;
esac
