"""Put the gitignored Conversation files the tests need into tear/data/conversation/.

  python -I step1a/scripts/get_conversation_data.py                 # from the HF dataset (needs `hf auth login`)
  python -I step1a/scripts/get_conversation_data.py --src DIR       # copy from another checkout's tear/data/conversation

Files already present are kept.
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s1a import paths  # noqa: E402

FILES = ("pool.jsonl", "test.jsonl", "levels.json")
HF_REPO = "database-lab/attribute-extraction-data"
HF_DIR = "tear/conversation"


def fetch(name, dest, src):
    if src:
        shutil.copy2(Path(src) / name, dest / name)
        return
    from huggingface_hub import hf_hub_download
    got = hf_hub_download(HF_REPO, f"{HF_DIR}/{name}", repo_type="dataset")
    shutil.copy2(got, dest / name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="folder holding pool.jsonl, test.jsonl and levels.json")
    args = ap.parse_args()
    dest = paths.TEAR_DATA
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if not (dest / name).exists():
            fetch(name, dest, args.src)
        print(name, (dest / name).stat().st_size, "bytes")


if __name__ == "__main__":
    main()
