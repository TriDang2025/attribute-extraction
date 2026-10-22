"""Dev / test split of the 1,000 Conversation dialogues: dev = TEAR's pool (300), test = TEAR's
test (700). `chunking/data/conversation_ids.txt` lists the pool first, then the test ids, so
dev = ids[:300] and the n50 runs so far used the first 50 dev dialogues. Tune on dev only.
"""

from . import paths  # noqa: F401
from chk.data import load_dialogues

N_DEV = 300


def dialogues(split, limit=None):
    if split == "dev":
        out = load_dialogues(N_DEV)
    elif split == "test":
        out = load_dialogues()[N_DEV:]
    else:
        raise ValueError(split)
    return out[:limit] if limit else out
