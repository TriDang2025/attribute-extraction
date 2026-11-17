"""wf_v4.6 Y8: pass 2 of Step 4 in batches of columns (switch `p2_batch` of s1a/step4_v44.py; off = the single pass-2 prompt of v4.3, untouched).

Why: pass 2 lists every column in one prompt, so it fails from about 300 dialogues (prompt over the token limit, answer over the output limit).
With p2_batch = N the columns (frozen order) are cut into consecutive batches of N. Each batch is one job "<chain>_p2_b<k>": the same prompt builder
as the single pass 2 (same instruction, same table list from pass 1, "Columns (<batch size>)"), and the same keyed schema over the ids of the batch
(every id exactly once, value = one of the pass-1 names plus the third option; no regex pattern). The answers of all batches are joined into one
object, which is what the single pass-2 answer is, so p2_assign and everything after it are unchanged.

max_tokens of a batch = min(cap of the format, TOKENS_BASE + TOKENS_PER_COLUMN * batch size) = 100 + 30 * size (20 columns: 700; cap 1500).
A chain stops at pass 2 when any batch answer is missing or unparsable (as it does today for the single answer).
"""
from . import step4_v43 as V

TOKENS_BASE, TOKENS_PER_COLUMN = 100, 30


def split(cols, n):
    """Consecutive batches of at most n columns (order kept)."""
    return [cols[i:i + n] for i in range(0, len(cols), n)]


def job_name(cid, b):
    return f"{cid}_p2_b{b}"


def max_tokens(n_cols, cap):
    return min(cap, TOKENS_BASE + TOKENS_PER_COLUMN * n_cols)


def check(n):
    """n as given by a CLI or config: None or 0 = off, else a whole number >= 1."""
    if n is None or n == 0:
        return None
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"p2_batch must be a whole number >= 1 (0 or none = off), got {n!r}")
    return n


def prompts(build, cols, cid, n):
    """[(job name, text, schema, format, batch columns)] of the batches. build(batch columns) -> (text, schema, format) is the pass-2 builder of
    the chain, so every batch sees the same table list."""
    out = []
    for b, bc in enumerate(split(cols, n)):
        text, schema, fmt = build(bc)
        out.append((job_name(cid, b), text, schema, fmt, bc))
    return out


def answer(out, chain, cols):
    """(joined parsed answer, None) of pass 2 of a chain, or (None, why). Without p2_batch it is the single answer of the job "<chain>_p2"."""
    n = chain.get("p2_batch")
    if not n:
        return V._answer(out, f"{chain['id']}_p2")
    joined = {}
    for b in range(len(split(cols, n))):
        parsed, why = V._answer(out, job_name(chain["id"], b))
        if why:
            return None, f"batch b{b}: {why}"
        if not isinstance(parsed, dict):
            return None, f"batch b{b}: answer is not an object"
        joined.update(parsed)
    return joined, None
