"""wf_v2.2 part H (Hudecek et al., ACL 2021: attach the head verb / preposition to the filler): embed ONE
text that joins the role words with the value ("from cambridge", "leave at 20:30", "3 people") instead of
the bare value, so bge-m3 sees the role inside the same string. No separate window vector is mixed in
(cue.py did, and merged clusters too much)."""

import re
from collections import defaultdict
from functools import partial

from . import step2 as S2
from .combos import V21_FILTER, V21_TEXT
from .variants import Variant, cluster_texts

# filler only; prepositions and verbs stay (they are the role words)
STOP = frozenset({"the", "a", "an", "please", "some", "my", "your", "our", "just", "also", "and",
                  "um", "uh", "so", "then", "like"})
_PUNCT = re.compile(r"^\W+|\W+$")
_TAG = re.compile(r"\[[A-Z]+\]")
_EXTRA = 6  # extra words requested before filler removal


def _words(text, skip):
    """Lowercased, punctuation-stripped words of `text` (window_texts output, target mark removed);
    filler dropped. A type tag (another value) is a wall: left keeps words after it, right before it,
    so a role word never belongs to two values. Returns (words after last tag, words before first tag)."""
    toks = [t for t in text.split() if not t.startswith("<<")]
    out = [[]]
    for t in toks:
        if _TAG.fullmatch(t):
            out.append([])
            continue
        w = _PUNCT.sub("", t).lower()
        if w and w not in skip:
            out[-1].append(w)
    return out[-1], out[0]


def role_text(doc, span, left=1, right=0, skip=STOP, mentions_in_doc=None, text_fn=V21_TEXT):
    """"<left words> <value> <right words>" inside the span's turn: speaker prefix excluded, other
    values (mentions_in_doc, default only the span itself) masked so they are not crossed, filler `skip`
    removed. The value part is text_fn(span.text) lowercased."""
    mentions = mentions_in_doc if mentions_in_doc is not None else [span]
    k = max(left, right) + _EXTRA
    lt, rt = S2.window_texts(doc, span, mentions, k, side="lr")
    lw = _words(lt, skip)[0][-left:] if left > 0 else []
    rw = _words(rt, skip)[1][:right] if right > 0 else []
    return " ".join(lw + [text_fn(span.text).lower()] + rw)


def role_texts(spans, docs, **kw):
    by_doc = defaultdict(list)
    for u in spans:
        by_doc[u.doc_id].append(u)
    return [role_text(docs[u.doc_id], u, mentions_in_doc=by_doc[u.doc_id], **kw) for u in spans]


def cluster_fn(spans, docs, enc, groups, books, left=1, right=0, t=0.4, skip=STOP):
    """Encode the role texts and cluster inside (group, value type of the span text) at threshold t."""
    texts = role_texts(spans, docs, left=left, right=right, skip=skip)
    return cluster_texts(spans, texts, groups, enc, t, by_type=True)


CONFIGS = {
    f"H_l{l}r{r}_t{str(t).replace('.', '')}": Variant(
        span_filter=V21_FILTER, cluster_fn=partial(cluster_fn, left=l, right=r, t=t),
        note=f"role words left {l} right {r}, code shapes, type split, t {t}")
    for l, r in ((1, 0), (2, 0), (1, 1), (0, 1)) for t in (0.35, 0.4, 0.45)
}
