#!/usr/bin/env bash
# Commit step1a/results/loop1_check and loop1_v31/responses and push to the current branch (wf-v3). Same retry loop as chunking/colab/sync.sh,
# which is fixed to chunking/results (the HF data pull is not needed here: prompts come from git).
#   bash colab/sync.sh push-results MSG
# Auth: GitHub from the GH_TOKEN env var + credential helper set by notebook cell 1.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$(dirname "$ROOT")"
[ "${1:-}" = push-results ] || { echo "usage: bash colab/sync.sh push-results [MSG]"; exit 1; }
msg="step1a loop1_check: ${2:-update} $(date -u '+%F %H:%M') UTC"
git add step1a/results/loop1_check
[ -d step1a/results/loop1_v31/responses ] && git add step1a/results/loop1_v31/responses
if git diff --cached --quiet; then echo "results unchanged"; exit 0; fi
git commit -q -m "$msg"
for attempt in 1 2 3; do
  if git pull -q --rebase --autostash && git push -q; then echo "pushed: $msg"; exit 0; fi
  git rebase --abort 2>/dev/null || true
  echo "push attempt $attempt failed; retrying"; sleep 20
done
echo "PUSH_FAILED: results are committed locally; run this again or ask the user"; exit 1
