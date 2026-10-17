"""bge-m3 embeddings for Hansard (19,553 speeches) and Conversation (1,000 dialogues), on GPU.

Writes data/hansard_bge_m3.npy, data/hansard_ids.csv, data/conversation_bge_m3.npy.
Resumable: partial files are saved every 500 texts (hbe/embed.py).
  python -I scripts/embed_all.py [--model PATH]   # PATH defaults to $HBE_MODELS/bge-m3
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hbe import config, data, embed  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    model = embed.load_model(args.model)
    print(f"model on {model.device}, max_seq_length {model.max_seq_length}", flush=True)

    corpus = data.hansard_corpus()
    assert len(corpus) == 19553, f"corpus size {len(corpus)} differs from the repo (19,553)"
    corpus[["speech_id"]].to_csv(config.DATA / "hansard_ids.csv", index=False)
    out = config.DATA / "hansard_bge_m3.npy"
    if out.exists():
        print("already done:", out)
    else:
        embed.encode(model, corpus["text"].tolist(), out)

    texts = config.ROOT / "colab" / "conversation_texts.jsonl"
    out = config.DATA / "conversation_bge_m3.npy"
    if out.exists():
        print("already done:", out)
    else:
        rows = [json.loads(line) for line in open(texts, encoding="utf-8")]
        embed.encode(model, [r["text"] for r in rows], out)
    print("EMBED_DONE", flush=True)


if __name__ == "__main__":
    main()
