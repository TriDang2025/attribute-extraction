#!/usr/bin/env bash
# Moves data between this Colab VM, Hugging Face and GitHub.
#   bash colab/sync.sh pull-data          HF dataset hdbscan/ -> data/ (keeps local files) + public Hansard sources
#   bash colab/sync.sh push-data          bge-m3 embeddings (also partial ones, so embedding resumes) -> HF
#   bash colab/sync.sh push-results MSG   commit hdbscan/results/ and push to GitHub (rebases on others' commits)
# Auth: HF from `huggingface_hub.login` (notebook cell 1); GitHub from git's credential cache.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HF_DATA_REPO="${HF_DATA_REPO:-database-lab/attribute-extraction-data}"   # dataset: hdbscan/ <-> hdbscan/data/
case "$HF_DATA_REPO" in *HF_USER*) echo "Set HF_DATA_REPO in hdbscan/colab/sync.sh (placeholder)"; exit 1;; esac
PY="${PY:-python}"
cd "$ROOT"

pull_data() {
  hf download "$HF_DATA_REPO" --repo-type dataset --include "hdbscan/*" --local-dir /content/hf_data --quiet >/dev/null
  mkdir -p data
  cp -rn /content/hf_data/hdbscan/. data/   # -n: never overwrite files this session already updated
  "$PY" -I scripts/fetch_data.py > /dev/null  # Hansard parquet, gold labels, repo UMAP/labels (public, resumable)
  echo "data ready: $(ls data | tr '\n' ' ')"
}

push_data() {
  "$PY" - <<'EOF'
import os
from pathlib import Path
from huggingface_hub import HfApi
data, repo = Path("data"), os.environ["HF_DATA_REPO"]
files = sorted(p.name for p in data.glob("*_bge_m3*.npy")) + ["hansard_ids.csv"] * (data / "hansard_ids.csv").exists()
finals = {n for n in files if not n.endswith((".partial.npy", ".done.npy"))}
api = HfApi()
remote = {f.split("/", 1)[1] for f in api.list_repo_files(repo, repo_type="dataset") if f.startswith("hdbscan/")}
# finished embeddings replace their partial files on HF
stale = [f"hdbscan/{n}" for n in remote if n.endswith((".partial.npy", ".done.npy"))
         and n.replace(".partial.npy", ".npy").replace(".done.npy", ".npy") in finals]
if files:
    api.upload_folder(repo_id=repo, repo_type="dataset", folder_path=str(data), path_in_repo="hdbscan",
                      allow_patterns=files, delete_patterns=[s.split("/", 1)[1] for s in stale] or None,
                      commit_message="hdbscan embeddings")
print("data pushed:", files)
EOF
}

push_results() {
  local msg="hdbscan results: ${1:-update} $(date -u '+%F %H:%M') UTC"
  cd "$(dirname "$ROOT")"
  git add hdbscan/results
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
