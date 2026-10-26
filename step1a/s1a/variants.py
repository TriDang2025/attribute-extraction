"""v2.1 experiment: one Step-3 (spans clustering) variant = an optional span filter plus an optional
cluster function, plugged into mentions.build (Inputs.spans / Inputs.cluster_fn).

Part modules (span_filter, shapes, cue, spans_step2) each export CONFIGS: {name: Variant}.
cluster_fn(spans, docs, enc, groups, books) -> (x, labels): x = vectors clustered on (rows per span),
labels = one hashable cluster label per span; groups = stage-1 entity per span (-1 = none),
books = (dialogue, segment) per span (for cannot-link).
"""

from dataclasses import dataclass
from typing import Callable

from . import step2 as S2


@dataclass
class Variant:
    span_filter: Callable = None   # list[span Unit] -> list[span Unit]
    cluster_fn: Callable = None    # see module docstring; None = original Step 2
    note: str = ""


def original(spans, docs, enc, groups, books, t=0.4):
    """The v1 / v2 Step 2 for spans: raw strings, cosine, average linkage, distance threshold t."""
    import relabel as RL  # scripts/ on sys.path (mentions.py puts it there)
    x = enc.encode([u.text for u in spans])
    return x, RL.stage2(x, groups, t)


def cluster_texts(spans, texts, groups, enc, t=0.4, books=None, by_type=False):
    """Shared helper: encode `texts` (one per span) and cluster inside each group, optionally also
    inside each value type of the span text, with cannot-link inside each booking when `books`."""
    import relabel as RL
    x = enc.encode(texts)
    parts = [(g, S2.value_type(u.text)) for g, u in zip(groups, spans)] if by_type else list(groups)
    if books is None:
        return x, RL.stage2(x, parts, t)
    return x, S2.cluster_constrained(x, parts, S2.cannot_links(spans, books), t)


BASELINE = Variant(note="v1/v2: original Step 2, no filter")
