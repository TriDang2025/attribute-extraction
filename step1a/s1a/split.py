"""Dev / test split of the 1,000 Conversation dialogues: dev = TEAR's pool (300), test = TEAR's
test (700). `chunking/data/conversation_ids.txt` lists the pool first, then the test ids, so
dev = ids[:300] and the n50 runs so far used the first 50 dev dialogues. Tune on dev only.
From wf_v3 the old test50 is a second dev set and "fresh" = test[350:450] is the sealed test split
(SPLITS.md); it loads only with unseal=True.
"""

from . import paths  # noqa: F401
from chk.data import load_dialogues

N_DEV = 300
FRESH = slice(N_DEV + 350, N_DEV + 450)


def dialogues(split, limit=None, unseal=False):
    if split == "dev":
        out = load_dialogues(N_DEV)
    elif split == "test":
        out = load_dialogues()[N_DEV:]
    elif split == "fresh":
        if not unseal:
            raise PermissionError("fresh test split is sealed until the final numbers (SPLITS.md)")
        out = load_dialogues()[FRESH]
    else:
        raise ValueError(split)
    return out[:limit] if limit else out
