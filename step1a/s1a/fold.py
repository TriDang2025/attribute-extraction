"""v2.2 part F: fold small clusters into big ones (DeepAligned / USNID idea). After the V21 clustering,
keep clusters with >= min_size members and move every member of a smaller cluster to the nearest
kept centroid of the same partition (same stage-1 group and value type)."""

from collections import defaultdict
from functools import partial

import numpy as np

from . import step2 as S2
from .combos import V21, V21_FILTER
from .variants import Variant


def fold(x, labels, parts, min_size, tau=None, books=None, texts=None):
    """New labels. Per partition: kept = clusters with size >= min_size (number, or "mean" = mean
    cluster size in that partition). A member of a small cluster moves to the kept cluster with the
    highest cosine to its centroid, if that cosine >= tau (None = always move). With books (one per
    member, with texts = span strings), a member never moves into a kept cluster that already holds
    the same booking with a different normalized string. No kept cluster in a partition = unchanged."""
    x = S2._unit(np.asarray(x, float))
    out = list(labels)
    norm = [S2.normalize(t) for t in texts] if books is not None else None
    by_part = defaultdict(lambda: defaultdict(list))
    for i, (p, l) in enumerate(zip(parts, labels)):
        by_part[p][l].append(i)
    for clusters in by_part.values():
        thr = np.mean([len(m) for m in clusters.values()]) if min_size == "mean" else min_size
        kept = [l for l, m in clusters.items() if len(m) >= thr]
        if not kept:
            continue
        cent = S2._unit(np.stack([x[clusters[l]].mean(0) for l in kept]))
        held = {}  # kept label -> {booking: normalized strings already in it}
        if books is not None:
            for l in kept:
                d = defaultdict(set)
                for i in clusters[l]:
                    d[books[i]].add(norm[i])
                held[l] = d
        for l, members in clusters.items():
            if l in kept:
                continue
            for i in members:
                sims = cent @ x[i]
                for k in np.argsort(-sims):
                    if tau is not None and sims[k] < tau:
                        break  # sorted: nothing further qualifies
                    tgt = kept[k]
                    if books is not None and held[tgt][books[i]] - {norm[i]}:
                        continue
                    out[i] = tgt
                    if books is not None:
                        held[tgt][books[i]].add(norm[i])
                    break
    return out


def cluster_fn(spans, docs, enc, groups, books, min_size=3, tau=None, use_books=False, base=None):
    """`base` clustering (default: V21), then fold. Returns (x, new labels)."""
    x, labels = (base or V21.cluster_fn)(spans, docs, enc, groups, books)
    parts = [(g, S2.value_type(u.text)) for g, u in zip(groups, spans)]
    texts = [u.text for u in spans]
    return x, fold(x, labels, parts, min_size, tau, books if use_books else None, texts)


def _name(m, tau, bk):
    return f"F_{'mean' if m == 'mean' else f'm{m}'}" + ("" if tau is None else f"_t{int(tau * 10):02d}") + ("_bk" if bk else "")


def _v(m, tau=None, bk=False):
    return _name(m, tau, bk), Variant(
        span_filter=V21_FILTER, cluster_fn=partial(cluster_fn, min_size=m, tau=tau, use_books=bk),
        note=f"V21 + fold small clusters (< {m}) to nearest kept centroid, tau {tau}" + (", booking constraint" if bk else ""))


CONFIGS = dict(_v(m, tau) for m in (2, 3, "mean") for tau in (None, 0.5, 0.6))
CONFIGS |= dict(_v(m, 0.6, True) for m in (2, 3, "mean"))
