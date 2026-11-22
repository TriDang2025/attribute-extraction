"""Dev / test split of the 1,000 Conversation dialogues: dev = TEAR's pool (300), test = TEAR's
test (700). `chunking/data/conversation_ids.txt` lists the pool first, then the test ids, so
dev = ids[:300] and the n50 runs so far used the first 50 dev dialogues. Tune on dev only.
From wf_v3 the old test50 is a second dev set and "fresh" = test[350:450] is the sealed test split
(SPLITS.md); it loads only with unseal=True. wf_v5.0 G0: dev50c = 50 dialogues drawn with seed 0 from pool[100:300]
(neither dev50 nor dev50b), sealed the same way: used once, for the final check.
"""

import random

from . import paths  # noqa: F401
from chk.data import load_dialogues

N_DEV = 300
FRESH = slice(N_DEV + 350, N_DEV + 450)
DEV50B = slice(50, 100)  # wf_v3.7: pool[50:100], confirm decisions only, never tune
DEV50C_POOL, DEV50C_N, DEV50C_SEED = slice(100, N_DEV), 50, 0
RUNNABLE = ("dev", "dev50b", "test")  # --split choices of the scripts ("fresh" is never a flag)


def dialogues(split, limit=None, unseal=False):
    if split == "dev":
        out = load_dialogues(N_DEV)
    elif split == "dev50b":
        out = load_dialogues(N_DEV)[DEV50B]
    elif split == "test":
        out = load_dialogues()[N_DEV:]
    elif split in ("fresh", "dev50c"):
        if not unseal:
            raise PermissionError(f"{split} split is sealed until the final numbers (SPLITS.md)")
        out = load_dialogues()[FRESH] if split == "fresh" else dev50c(load_dialogues(N_DEV))
    else:
        raise ValueError(split)
    return out[:limit] if limit else out


def dev50c(pool):
    """dev50c: DEV50C_N dialogues of pool[100:300] drawn with DEV50C_SEED, kept in pool order."""
    idx = sorted(random.Random(DEV50C_SEED).sample(range(len(pool))[DEV50C_POOL], DEV50C_N))
    return [pool[i] for i in idx]
