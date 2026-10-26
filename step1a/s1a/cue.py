"""v2.1 part C: mix the words just before a span ("to Cambridge", "by 20:30", "for 3 people") into
its string vector, so slots that share strings (departure vs destination, leave-at vs arrive-by)
separate. Left cue = left k-word masked window of step2.window_texts (target marked)."""

from collections import defaultdict
from functools import partial

from . import step2 as S2
from .variants import Variant


def cue_vectors(spans, docs, enc, k):
    """Encoded left k-word masked window of every span (one encode call)."""
    by_doc = defaultdict(list)
    for u in spans:
        by_doc[u.doc_id].append(u)
    left = [S2.window_texts(docs[u.doc_id], u, by_doc[u.doc_id], k, side="lr")[0] for u in spans]
    return enc.encode(left)


def cluster_fn(spans, docs, enc, groups, books, beta=0.5, k=1, by_type=False, t=0.4, cannot_link=False,
               text_fn=None):
    """x = unit(beta * cue + (1 - beta) * string), clustered inside each group (and value type).
    text_fn(text) -> the string to encode (e.g. shapes.shape); default the raw span text."""
    x = enc.encode([text_fn(u.text) if text_fn else u.text for u in spans])
    if beta:
        x = S2.combine(cue_vectors(spans, docs, enc, k), x, beta)
    parts = [(g, S2.value_type(u.text)) for g, u in zip(groups, spans)] if by_type else list(groups)
    if cannot_link:
        return x, S2.cluster_constrained(x, parts, S2.cannot_links(spans, books), t)
    import relabel as RL  # scripts/ on sys.path (mentions.py puts it there)
    return x, RL.stage2(x, parts, t)


def _v(beta, k, by_type, t=0.4, cannot_link=False):
    return Variant(cluster_fn=partial(cluster_fn, beta=beta, k=k, by_type=by_type, t=t, cannot_link=cannot_link),
                   note=f"left cue beta {beta} k {k} type {'on' if by_type else 'off'} t {t}"
                        + (" cannot-link" if cannot_link else ""))


CONFIGS = {f"C_b{int(b * 10):02d}_k{k}_{'type' if ty else 'flat'}": _v(b, k, ty)
           for b in (0.3, 0.5) for k in (1, 2) for ty in (False, True)}
CONFIGS |= {
    "C_b05_k1_type_t03": _v(0.5, 1, True, t=0.3),
    "C_b05_k1_type_t05": _v(0.5, 1, True, t=0.5),
    "C_b05_k1_type_cl": _v(0.5, 1, True, cannot_link=True),
}
