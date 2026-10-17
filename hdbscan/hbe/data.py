"""Datasets.

Hansard: the published HF dataset holds the repo's all_speakers.csv rows (speech_id
SP_00000.. in CSV order) plus topic labels. The repo's modeling notebook then
  1. sets year = pd.to_datetime(date, errors="coerce").dt.year (so dates such as
     "2022-08-09-2" become NaT and drop out), and
  2. stacks per-year embeddings in sorted year order, each year in CSV order.
`hansard_corpus()` rebuilds exactly that row order.

Conversation: the 1,000 MultiWOZ dialogues of the TEAR reproduction (read-only copy in
data/conversation, downloaded from the HF dataset's hdbscan/conversation on Colab).
"""

import hashlib
import json
import os
from pathlib import Path

import pandas as pd

from . import config

HF_FILES = ("train", "test")
CONVERSATION_DIR = Path(os.environ.get("HBE_CONVERSATION_DIR", config.DATA / "conversation"))


def hansard_raw(data_dir=config.DATA):
    parts = [pd.read_parquet(Path(data_dir) / "hf" / f"{s}.parquet") for s in HF_FILES]
    df = pd.concat(parts, ignore_index=True)
    df["_n"] = df["speech_id"].str[3:].astype(int)
    return df.sort_values("_n").drop(columns="_n").reset_index(drop=True)


def hansard_corpus(data_dir=config.DATA):
    """Rows in the order the repo's embeddings/UMAP use (19,553 speeches)."""
    df = hansard_raw(data_dir)
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)
    # stable sort = concat of per-year blocks, each in CSV order
    df = df.sort_values("year", kind="stable").reset_index(drop=True)
    df["text"] = df["text"].fillna("")
    return df


def ids_checksum(ids):
    return hashlib.sha256("\n".join(ids).encode()).hexdigest()[:16]


def gold(data_dir=config.DATA):
    gt = pd.read_csv(Path(data_dir) / "ground_truth_300.csv")
    return gt[gt["is_evaluable"].astype(str).str.lower() == "true"].copy()


def gold_join(labels_df, data_dir=config.DATA, col="cluster"):
    """Inner join on speech_id, as run_evaluation.py does."""
    df = gold(data_dir).merge(labels_df[["speech_id", col]], on="speech_id", how="inner")
    return df.dropna(subset=["label", col])


def conversation(conv_dir=CONVERSATION_DIR):
    """1,000 dialogues with domain labels taken from the gold table headers."""
    rows = []
    for name in ("pool.jsonl", "test.jsonl"):
        with open(Path(conv_dir) / name, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                domains = sorted({h.split()[0] for h in r["table"]["headers"]})
                # main domain = the one with the most filled columns
                counts = {}
                for h in r["table"]["headers"]:
                    counts[h.split()[0]] = counts.get(h.split()[0], 0) + 1
                main = max(sorted(counts), key=counts.get)
                rows.append({"id": r["id"], "source": name.split(".")[0], "text": r["text"],
                             "domain_set": "+".join(domains), "main_domain": main,
                             "n_domains": len(domains)})
    return pd.DataFrame(rows)
