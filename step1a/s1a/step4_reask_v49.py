"""wf_v4.9 A+R: re-ask a pass-2 batch of Step 4 once when it drops an entity (chain key `p2_reask` of s1a/step4_v44.py; needs p2_batch; off = v4.8 A).

Why: in variant A the batched pass 2 sometimes sends most columns of one entity to "unused" although pass 1 made a table for that entity (wf_v4.8:
A leaves 30-49 dev50b columns unused).
Rule: a batch is re-asked when, for some entity E with a table in the pass-1 list (tables = pass-1 names, slugs), at least half of the columns of E in
that batch got no table: the answer is "unused" (step4_v43.UNUSED), missing, or not one of the choices of the prompt (so None from a bad answer counts).
The re-ask is the job "<chain>_p2_b<k>_r1" with run_tag "<chain>_r1" (a different cache key) and the same prompt plus REASK_NOTE. The note is needed:
decoding is greedy (temperature 0, batch-invariant), so an identical prompt would return the identical answer. Set REASK_NOTE = "" for a pure re-ask.
The second answer replaces the first of that batch; when it is missing or does not parse, the first answer is kept. Counts: repair kinds
p2_reask (re-asked and second answer used), p2_reask_failed (second answer unusable, first kept), p2_reask_missing (no response, first kept).
"""
from . import step4_p2batch_v46 as P2B
from . import step4_prompts as SP
from . import step4_v43 as V

TAG = "r1"
REASK_NOTE = ("Note: columns that carry the same entity heading usually belong to the table of that entity. "
              f'Answer "{V.UNUSED}" only for a column that clearly fits no table.\n')
_TAIL = "\nReturn the JSON object now.\n"


def job_name(cid, b):
    return f"{P2B.job_name(cid, b)}_{TAG}"


def run_tag(cid):
    return f"{cid}_{TAG}"


def with_note(text):
    """The prompt of a re-ask: `text` with REASK_NOTE before its closing line."""
    if not REASK_NOTE:
        return text
    if not text.endswith(_TAIL):
        raise ValueError("pass-2 prompt does not end with the closing line; cannot add the re-ask note")
    return text[:-len(_TAIL)] + "\n" + REASK_NOTE + _TAIL


def drops_entity(batch_cols, parsed, tables, valid):
    """True when at least half of the columns of an entity with a table in `tables` are sent to no table in this batch. `valid` = table choices of
    the prompt; any other answer (unused, None, a bad name) counts as no table."""
    by = {}
    for c in batch_cols:
        by.setdefault(V._slug(SP._entity(c)), []).append(c["id"])
    return any(e in tables and 2 * sum(parsed.get(i) not in valid for i in ids) >= len(ids) for e, ids in by.items())


def to_reask(out, chain, cols, tables, valid):
    """Indexes of the batches of a chain to re-ask, from the first answers (a batch without a usable first answer is not re-asked)."""
    res = []
    for b, bc in enumerate(P2B.split(cols, chain["p2_batch"])):
        parsed, why = V._answer(out, P2B.job_name(chain["id"], b))
        if not why and isinstance(parsed, dict) and drops_entity(bc, parsed, tables, valid):
            res.append(b)
    return res


def answer(out, chain, cols, tables, valid, log=None, where=""):
    """(joined parsed answer of pass 2, None) or (None, why), like step4_p2batch_v46.answer, with the re-asked batches replaced by their second answer."""
    joined = {}
    for b, bc in enumerate(P2B.split(cols, chain["p2_batch"])):
        parsed, why = V._answer(out, P2B.job_name(chain["id"], b))
        if why:
            return None, f"batch b{b}: {why}"
        if not isinstance(parsed, dict):
            return None, f"batch b{b}: answer is not an object"
        if drops_entity(bc, parsed, tables, valid):
            second, why2 = V._answer(out, job_name(chain["id"], b))
            kind = "p2_reask" if not why2 and isinstance(second, dict) else ("p2_reask_missing" if why2 == "no response" else "p2_reask_failed")
            if log is not None:
                log.add(kind, where, f"b{b}")
            if kind == "p2_reask":
                parsed = second
        joined.update(parsed)
    return joined, None
