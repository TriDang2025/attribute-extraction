"""wf_v5.0 G5 A+R+M: a second re-ask round on top of wf_v4.9 A+R (chain key `p2_reask2` of s1a/step4_v44.py; needs p2_reask; off = v4.9 A+R).

Rule: a pass-2 batch whose r1 answer (step4_reask_v49) is usable but still drops an entity (step4_reask_v49.drops_entity) is asked a third time: job
"<chain>_p2_b<k>_r2", run_tag "<chain>_r2", the r1 prompt with NOTE_R2 added (decoding is greedy, so the prompt must differ from r1). The r2 answer
replaces r1 when it parses; else r1 is kept. Repair kinds: p2_reask2, p2_reask2_failed, p2_reask2_missing.
"""
from . import step4_p2batch_v46 as P2B
from . import step4_reask_v49 as RA
from . import step4_v43 as V

TAG = "r2"
NOTE_R2 = ("Second check: in the last answer at least half of the columns of one entity heading went to no table, although that entity has a table. "
           "Give each such column the table of its entity heading unless its values clearly belong to another table.\n")


def job_name(cid, b):
    return f"{P2B.job_name(cid, b)}_{TAG}"


def run_tag(cid):
    return f"{cid}_{TAG}"


def with_note(text):
    """The r2 prompt: the r1 prompt (step4_reask_v49.with_note) with NOTE_R2 after the r1 note."""
    r1 = RA.with_note(text)
    return r1[:-len(RA._TAIL)] + NOTE_R2 + RA._TAIL


def to_reask(out, chain, cols, tables, valid):
    """Indexes of the batches to ask in round 2: the first answer dropped an entity, the r1 answer is usable and still drops one."""
    res = []
    for b in RA.to_reask(out, chain, cols, tables, valid):
        bc = P2B.split(cols, chain["p2_batch"])[b]
        second, why = V._answer(out, RA.job_name(chain["id"], b))
        if not why and isinstance(second, dict) and RA.drops_entity(bc, second, tables, valid):
            res.append(b)
    return res


def batch_answer(out, chain, b, bc, tables, valid, log=None, where=""):
    """step4_reask_v49.batch_answer, then the r2 answer when the used r1 answer still drops an entity and r2 parses."""
    parsed, why = RA.batch_answer(out, chain, b, bc, tables, valid, log, where)
    if why or not RA.drops_entity(bc, parsed, tables, valid):
        return parsed, why
    r1, why1 = V._answer(out, RA.job_name(chain["id"], b))
    if why1 or parsed != r1:          # r1 was not used (missing or bad): no second round
        return parsed, None
    third, why3 = V._answer(out, job_name(chain["id"], b))
    kind = "p2_reask2" if not why3 and isinstance(third, dict) else ("p2_reask2_missing" if why3 == "no response" else "p2_reask2_failed")
    if log is not None:
        log.add(kind, where, f"b{b}")
    return (third if kind == "p2_reask2" else parsed), None


def answer(out, chain, cols, tables, valid, log=None, where=""):
    """step4_reask_v49.answer with the second round."""
    return RA.answer(out, chain, cols, tables, valid, log, where, batch_fn=batch_answer)
