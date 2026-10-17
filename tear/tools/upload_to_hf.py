"""One-off: put the TEAR data and the trained surrogate on Hugging Face (private repos).

  python tools/upload_to_hf.py --data-repo USER/attribute-extraction-data --model-repo USER/tear-surrogate \
      [--surrogate PATH] [--public]

data/ goes to the dataset repo under tear/ (Colab's colab/sync.sh pull-data reads it back into data/).
The surrogate folder goes to the model repo root. Needs `hf auth login` with a write token first.
"""

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-repo", required=True)
    ap.add_argument("--model-repo", required=True)
    ap.add_argument("--surrogate", default=str(Path(os.environ.get("TEAR_MODELS", ROOT / "models"))
                                               / "surrogate_conversation_cont2"))
    ap.add_argument("--public", action="store_true")
    args = ap.parse_args()
    surrogate = Path(args.surrogate)
    assert (surrogate / "model.safetensors").exists(), f"no model.safetensors in {surrogate}"
    assert (ROOT / "data/conversation/test.jsonl").exists(), "tear/data is missing"

    api = HfApi()
    print("logged in as", api.whoami()["name"])
    api.create_repo(args.data_repo, repo_type="dataset", private=not args.public, exist_ok=True)
    api.upload_folder(repo_id=args.data_repo, repo_type="dataset", folder_path=str(ROOT / "data"),
                      path_in_repo="tear", commit_message="TEAR data (Conversation, small sets, caches)")
    print("data uploaded to", args.data_repo)
    api.create_repo(args.model_repo, repo_type="model", private=not args.public, exist_ok=True)
    api.upload_folder(repo_id=args.model_repo, folder_path=str(surrogate),
                      commit_message="BART-Large surrogate, Conversation, full schema (cont2)")
    print("surrogate uploaded to", args.model_repo)


if __name__ == "__main__":
    main()
