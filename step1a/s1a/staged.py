"""wf_v2.2 part G: staged clustering (USSI, NAACL 2022). Stage 1 clusters the masked context (the
value hidden, only its role in the turn visible) inside each (stage-1 group, value type) partition;
stage 2 sub-clusters inside each context cluster by the span string (V21_TEXT shape text).
Every span is kept; label = "<partition>|c<ctx>|s<str>". Optional min context size m: context
clusters smaller than m merge into the nearest (centroid cosine) cluster of size >= m."""

from collections import defaultdict
from functools import partial

import numpy as np

from . import step2 as S2
from .combos import V21_FILTER, V21_TEXT
from .variants import Variant


def context_texts(spans, docs, context, k=2):
    """One masked context text per span: context "window" (k words each side, target marked) or
    "turn" (whole turn plus the previous one, other values masked, target marked)."""
    by_doc = defaultdict(list)
    for u in spans:
        by_doc[u.doc_id].append(u)
    if context == "window":
        return [S2.window_texts(docs[u.doc_id], u, by_doc[u.doc_id], k, side="sym") for u in spans]
    if context == "turn":
        return [S2.masked_context(docs[u.doc_id], u, by_doc[u.doc_id]) for u in spans]
    raise ValueError(context)


def merge_small(labels, vecs, min_size):
    """Merge each cluster smaller than min_size into the nearest (cosine of mean vectors) cluster
    of size >= min_size. With no such cluster, labels are returned unchanged."""
    labels = list(labels)
    members = defaultdict(list)
    for i, l in enumerate(labels):
        members[l].append(i)
    big = [l for l, m in members.items() if len(m) >= min_size]
    if not big:
        return labels
    cent = S2._unit(np.stack([np.asarray(vecs, float)[members[l]].mean(0) for l in big]))
    for l, m in members.items():
        if len(m) >= min_size:
            continue
        c = S2._unit(np.asarray(vecs, float)[m].mean(0, keepdims=True))
        target = big[int(np.argmax(cent @ c[0]))]
        for i in m:
            labels[i] = target
    return labels


def staged_labels(ctx_vecs, str_vecs, parts, t1, t2, min_size=0):
    """Two-stage labels "<partition>|c<ctx>|s<str>" from context and string vectors."""
    import relabel as RL  # scripts/ on sys.path (mentions.py puts it there)
    ctx = RL.stage2(ctx_vecs, parts, t1)
    if min_size > 1:
        ctx = merge_small(ctx, ctx_vecs, min_size)
    sub = RL.stage2(str_vecs, ctx, t2)  # "<ctx label>:<n>"
    return [f"{S2._name(p)}|c{c.rsplit(':', 1)[1]}|s{s.rsplit(':', 1)[1]}"
            for p, c, s in zip(parts, ctx, sub)]


def cluster_fn(spans, docs, enc, groups, books, context="window", k=2, t1=0.3, t2=0.4, min_size=0,
               text_fn=V21_TEXT):
    """Staged clustering; returns (string vectors, labels), one label per span."""
    parts = [(g, S2.value_type(u.text)) for g, u in zip(groups, spans)]
    ctx_vecs = enc.encode(context_texts(spans, docs, context, k))
    x = enc.encode([text_fn(u.text) for u in spans])
    return x, staged_labels(ctx_vecs, x, parts, t1, t2, min_size)


def _v(context, k, t1, min_size=0):
    tag = f"w{k}" if context == "window" else "turn"
    return Variant(span_filter=V21_FILTER, cluster_fn=partial(cluster_fn, context=context, k=k, t1=t1,
                                                              min_size=min_size),
                   note=f"staged: context {tag} t1 {t1}, strings t2 0.4" + (f", min ctx size {min_size}" if min_size else ""))


CONFIGS = {f"G_{'w' + str(k) if c == 'window' else 'turn'}_t1_{int(t1 * 10):02d}": _v(c, k, t1)
           for c, k in (("window", 2), ("window", 3), ("turn", 0)) for t1 in (0.2, 0.3, 0.4)}
CONFIGS |= {"G_w2_t1_03_m3": _v("window", 2, 0.3, 3), "G_turn_t1_03_m3": _v("turn", 0, 0.3, 3)}
