#!/usr/bin/env bash
# Moves data between this Colab VM, Hugging Face and GitHub.
#   bash colab/sync.sh pull-data          HF dataset chunking/ -> data/ (keeps local files)
#   bash colab/sync.sh push-results MSG   commit chunking/results/ and push to GitHub (rebases on others' commits)
# Auth: HF from `huggingface_hub.login` (notebook cell 1); GitHub from the GH_TOKEN env var + credential helper set by notebook cell 1.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HF_DATA_REPO="${HF_DATA_REPO:-database-lab/attribute-extraction-data}"   # dataset: chunking/ <-> chunking/data/
cd "$ROOT"

pull_data() {
  hf download "$HF_DATA_REPO" --repo-type dataset --include "chunking/*" --local-dir /content/hf_data --quiet >/dev/null
  mkdir -p data
  cp -rn /content/hf_data/chunking/. data/   # -n: never overwrite files this session already updated
  echo "data ready: $(ls data | tr '\n' ' ')"
}

push_results() {
  local msg="chunking results: ${1:-update} $(date -u '+%F %H:%M') UTC"
  cd "$(dirname "$ROOT")"
  git add chunking/results
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
  push-results) push_results "${2:-}" ;;
  *) echo "usage: bash colab/sync.sh pull-data|push-results [MSG]"; exit 1 ;;
esac
