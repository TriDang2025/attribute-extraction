"""Entity segmentation: Chroma ClusterSemanticChunker (bge-m3) with smaller sizes, then a merge
of adjacent pieces that are very similar and bring no new entity word.

Goal: one piece per entity. Smaller min/max sizes raise boundary recall at the cost of
precision; the merge undoes wrong cuts.
"""

import re

from . import paths  # noqa: F401
from chk.embed import chroma_embedding_function
from chk.metrics import align
from chk.methods import chroma

# (min_chunk_size, max_chunk_size) in cl100k tokens; (50, 400) is the published setting
SIZES = ((50, 400), (25, 200), (25, 100), (15, 75))
# adjacent-piece cosines under bge-m3 lie in about 0.3-0.75 (median ~0.45, 90th pct ~0.55-0.6
# on a 5-dialogue check), so "very high" is set on that scale
TAUS = (None, 0.45, 0.50, 0.55, 0.60)

# cheap keyword check: which entity types a piece mentions
ENTITY_WORDS = {
    "hotel": r"hotels?|guest ?houses?|lodging|accommodation|place to stay|nights?|rooms?",
    "restaurant": r"restaurants?|food|cuisine|eat|dine|dinner|lunch|table",
    "train": r"trains?|railway|rail|station",
    "taxi": r"taxis?|cabs?",
    "attraction": r"attractions?|museums?|college|park|theatre|theater|cinema|church|"
                  r"architecture|nightclub|swimming pool|entertainment|gallery|boat",
}
_ENTITY_RE = {e: re.compile(rf"\b(?:{p})\b", re.I) for e, p in ENTITY_WORDS.items()}


def entity_words(text):
    return {e for e, rx in _ENTITY_RE.items() if rx.search(text)}


def chroma_pieces(text, enc, min_size, max_size):
    return chroma(text, chroma_embedding_function(enc),
                  dict(max_chunk_size=max_size, min_chunk_size=min_size))


def merge_adjacent(text, spans, enc, tau, use_keywords=True):
    """Merge span i+1 into the current piece when cos >= tau and span i+1 adds no entity type
    the current piece lacks (use_keywords=False: cosine only). Works on char spans so pieces
    stay slices of text."""
    if tau is None or len(spans) < 2:
        return list(spans)
    vec = enc.encode([text[s:e] for s, e in spans])
    out = [spans[0]]
    cur_v, cur_ents = vec[0], entity_words(text[spans[0][0]:spans[0][1]])
    for (s, e), v in zip(spans[1:], vec[1:]):
        ents = entity_words(text[s:e])
        if float(cur_v @ v) >= tau and (not use_keywords or ents <= cur_ents):
            out[-1] = (out[-1][0], e)
            cur_v = enc.encode([text[out[-1][0]:e]])[0]
        else:
            out.append((s, e))
            cur_v, cur_ents = v, ents
        cur_ents = cur_ents | ents
    return out


def piece_spans(doc, chunks):
    """Char spans covering doc.text from the chunker's strings (each ends where the next starts)."""
    starts = [s for s, _ in align(doc.text, chunks)[0]]
    ends = starts[1:] + [len(doc.text)]
    return [(s, e) for s, e in zip(starts, ends) if doc.text[s:e].strip()]


def snap_to_turns(doc, spans):
    """Move every internal cut of contiguous char spans to the nearest turn start (ties: earlier),
    then rebuild contiguous spans without empty or whitespace-only pieces."""
    starts = [s for s, _ in doc.spans]
    first, end = spans[0][0], len(doc.text)
    cuts = sorted({min(starts, key=lambda t: (abs(t - c), t)) for c, _ in spans[1:]})
    out, cur = [], first
    for c in cuts + [end]:
        if c <= cur or c > end:
            continue
        if not doc.text[cur:c].strip():
            if c == end and out:  # trailing blank piece joins the previous one
                out[-1] = (out[-1][0], end)
            continue
        out.append((cur, c))
        cur = c
    if cur < end and out:
        out[-1] = (out[-1][0], end)
    return out or [(first, end)]


def turn_pieces(doc):
    """One contiguous char piece per turn: starts at each turn start (first at 0), last ends at len(text)."""
    starts = [0] + [s for s, _ in doc.spans[1:]]
    return list(zip(starts, starts[1:] + [len(doc.text)]))


def as_chunks(doc, spans):
    return [doc.text[s:e] for s, e in spans]
