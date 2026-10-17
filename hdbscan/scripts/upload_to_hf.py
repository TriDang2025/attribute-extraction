"""One-off: put the Conversation dialogues used by the HDBSCAN run on Hugging Face (private repo).

  python -I scripts/upload_to_hf.py --data-repo USER/attribute-extraction-data [--public]

data/conversation/{pool,test}.jsonl go to hdbscan/conversation/ in the dataset repo. The Hansard data
is not rehosted (scripts/fetch_data.py gets it from the paper's public sources); the bge-m3 embeddings
are added from Colab by colab/sync.sh push-data. Needs `hf auth login` with a write token first.
"""

import argparse
import sys
from pathlib import Path

from huggingface_hub import HfApi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hbe import data  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-repo", required=True)
    ap.add_argument("--public", action="store_true")
    args = ap.parse_args()
    conv = Path(data.CONVERSATION_DIR)
    assert len(data.conversation(conv)) == 1000, f"expected 1,000 dialogues in {conv}"

    api = HfApi()
    print("logged in as", api.whoami()["name"])
    api.create_repo(args.data_repo, repo_type="dataset", private=not args.public, exist_ok=True)
    api.upload_folder(repo_id=args.data_repo, repo_type="dataset", folder_path=str(conv),
                      path_in_repo="hdbscan/conversation", allow_patterns=["pool.jsonl", "test.jsonl"],
                      commit_message="HDBSCAN: Conversation dialogues")
    print("uploaded to", args.data_repo)


if __name__ == "__main__":
    main()
