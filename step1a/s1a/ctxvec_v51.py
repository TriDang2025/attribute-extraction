"""wf_v5.1 R1 (S3): cluster the Step 1a mentions on value + context. "from Cambridge" and "to Cambridge" share the value, and so do "leave after 9"
and "arrive by 10"; the words around the value tell the roles apart. Per mention: v = unit((1 - alpha) * v_value + alpha * v_context), v_value =
the adopted value vector (shape text for codes, raw text otherwise), v_context = bge-m3 of the turn text from LEFT words before to RIGHT words after
the value (step2.window_texts: the value itself is masked as its type tag "<<[TIME]>>", other values of the dialogue by their type tags).
alpha 0 = the adopted Step 1a clustering F_m2_t06_bk exactly (fold.CONFIGS); the mix is used in the clustering and in the fold.
No gold, no word list. Switch: the cluster_fn / CONFIGS entry (off = alpha 0 = not used).

Replay helpers (pure, gold only to score): match the new clusters to the cached v5.0 clusters, carry the cached Step 3 column of an unchanged
cluster over to its new cluster, and count mixed-role clusters, fragmented attributes and attributes lost at the clusters checkpoint.
"""

from collections import Counter, defaultdict
from functools import partial

import numpy as np

from . import cue as C
from . import fold as F
from . import step2 as S2
from .combos import V21_FILTER, V21_TEXT
from .trace_v50 import best
from .variants import Variant

LEFT, RIGHT = 4, 2
ALPHAS = (0.0, 0.3, 0.5, 0.7)
JACCARD = 0.8        # a new cluster is "unchanged" when its Jaccard with an old cluster is at least this
LENIENT_SHARE = 0.5  # lenient replay: a new cluster inherits the old cluster that holds at least this share of its mentions
MIX_SHARE, MIX_MIN = 0.25, 3   # mixed-role cluster: two gold roles each with >= MIX_MIN mentions and >= MIX_SHARE of the cluster
FRAG_SHARE, FRAG_MIN = 0.5, 3  # fragmented attribute: >= 2 clusters where it is the majority with >= FRAG_MIN mentions


# ------------------------------------------------------------------ vectors
def context_text(doc, u, doc_units, left=LEFT, right=RIGHT):
    """`left` words before the value, its masked tag, `right` words after it (inside the mention's turn, speaker prefix stripped)."""
    lft, _ = S2.window_texts(doc, u, doc_units, left, side="lr")      # ends with the mark
    _, rgt = S2.window_texts(doc, u, doc_units, right, side="lr")     # starts with the mark
    tail = rgt.split(" ", 1)[1] if " " in rgt else ""
    return f"{lft} {tail}".strip()


def context_texts(spans, docs, left=LEFT, right=RIGHT):
    by_doc = defaultdict(list)
    for u in spans:
        by_doc[u.doc_id].append(u)
    return [context_text(docs[u.doc_id], u, by_doc[u.doc_id], left, right) for u in spans]


def context_vectors(spans, docs, enc, left=LEFT, right=RIGHT):
    """Unit bge-m3 vectors of the context texts (one encode call)."""
    return S2._unit(np.asarray(enc.encode(context_texts(spans, docs, left, right)), float))


def cluster_fn(alpha, t=0.4, left=LEFT, right=RIGHT):
    """Variant cluster_fn (spans, docs, enc, groups, books) -> (x, labels): the adopted F_m2_t06_bk with the context mixed in at weight alpha.
    t = distance threshold of the agglomerative step, the fold cosine is 1 - t (adopted: t 0.4, fold 0.6). Context vectors are similar to each
    other (bge-m3 cosines are high), so the mix needs a smaller t to keep the cluster count."""
    cue = lambda spans, docs, enc, _k: context_vectors(spans, docs, enc, left, right)  # noqa: E731
    base = partial(C.cluster_fn, beta=alpha, k=1, by_type=True, t=t, cannot_link=False, text_fn=V21_TEXT, cue_fn=cue)
    return partial(F.cluster_fn, min_size=2, tau=round(1 - t, 6), use_books=True, base=base)


CONFIGS = {f"R1_a{int(a * 10):02d}": Variant(span_filter=V21_FILTER, cluster_fn=cluster_fn(a),
                                             note=f"F_m2_t06_bk with value + context vectors, alpha {a}") for a in ALPHAS}


# ------------------------------------------------------------------ replay: clusters
def _jaccard(a, b):
    return len(a & b) / len(a | b)


def match_clusters(old, new, thr=JACCARD, lenient=False):
    """{new cluster: old cluster}. old / new = {cluster id: set of mention ids}. Strict: one-to-one, greedy by Jaccard, only >= thr.
    lenient (extra): every still unmatched new cluster takes the old cluster holding most of its mentions when that is >= LENIENT_SHARE of it."""
    pairs = sorted(((_jaccard(o, n), nc, oc) for nc, n in new.items() for oc, o in old.items() if o & n), key=lambda t: (-t[0], t[1], t[2]))
    out, used = {}, set()
    for j, nc, oc in pairs:
        if j < thr:
            break
        if nc not in out and oc not in used:
            out[nc] = oc
            used.add(oc)
    if lenient:
        for nc, n in new.items():
            if nc in out:
                continue
            cnt = {oc: len(o & n) for oc, o in old.items() if o & n}
            if cnt:
                oc = max(cnt, key=lambda c: (cnt[c], c))
                if cnt[oc] / len(n) >= LENIENT_SHARE:
                    out[nc] = oc
    return out


def carry_columns(columns, old_cl_of, new_cl_of, match):
    """Final columns of one entity for the new clustering. A new cluster in `match` takes the cached column of its old cluster: its members are
    the old members "old@group" renamed "new@group"; each of its mentions goes to the column that held the mention (when it sat in that old
    cluster) or else the column holding most of the new cluster. Unmatched new clusters get no column (their mentions are dropped)."""
    old_col = {}   # mention id -> (column index) in the old columns
    for ci, col in enumerate(columns):
        for i in col["mention_ids"]:
            old_col[int(i)] = ci
    by_new = defaultdict(list)
    for i, nc in new_cl_of.items():
        by_new[nc].append(i)
    ids = defaultdict(set)
    members = defaultdict(list)
    for nc, oc in match.items():
        mine = [i for i in by_new[nc] if old_cl_of.get(i) == oc and i in old_col]
        if not mine:
            continue
        major = Counter(old_col[i] for i in mine).most_common(1)[0][0]
        for i in by_new[nc]:
            ids[old_col[i] if old_cl_of.get(i) == oc and i in old_col else major].add(i)
        for ci in {old_col[i] for i in mine} | {major}:
            members[ci] += [f"{nc}@{m.split('@', 1)[1]}" for m in columns[ci]["members"] if m.split("@", 1)[0] == oc]
    out = []
    for ci, col in enumerate(columns):
        if not col["mention_ids"]:
            out.append(col)   # a column with no mention (a split part whose values sit in another part) stays as cached
        elif ids.get(ci):
            mem = list(dict.fromkeys(members[ci]))
            out.append({**col, "mention_ids": sorted(ids[ci]), "n_mentions": len(ids[ci]), "members": mem,
                        "groups": list(dict.fromkeys(m.split("@", 1)[1] for m in mem))})
    return out


# ------------------------------------------------------------------ replay: gold counts
def role_clusters(clusters, labels, attrs):
    """Clusters that hold two gold roles: {cluster id: (attr1, attr2)}. clusters = {id: [mention ids]}, attrs = the entity's gold attributes."""
    out = {}
    for cid, ids in clusters.items():
        cnt = Counter(a for i in ids for a in set(labels.get(i, [])) & attrs)
        top = [(a, k) for a, k in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])) if k >= MIX_MIN and k / len(ids) >= MIX_SHARE]
        if len(top) >= 2:
            out[cid] = (top[0][0], top[1][0])
    return out


def fragmented(clusters, labels, attrs):
    """Gold attributes that are the majority of >= 2 clusters (each with >= FRAG_MIN mentions of it): {attr: [cluster ids]}."""
    hold = defaultdict(list)
    for cid, ids in clusters.items():
        cnt = Counter(a for i in ids for a in set(labels.get(i, [])) & attrs)
        for a, k in cnt.items():
            if k >= FRAG_MIN and k / len(ids) >= FRAG_SHARE:
                hold[a].append(cid)
    return {a: cs for a, cs in hold.items() if len(cs) >= 2}


def s3_attrs(clusters, labels, attrs, total, share_ok):
    """Gold attributes lost at the clusters checkpoint (trace_v50 rule: no cluster passes the found rule), among those with mentions mostly in
    this entity. total = {attr: mentions of the entity}; share_ok(attr) = trace_v50 S1 test."""
    groups = {c: [labels.get(i, []) for i in ids] for c, ids in clusters.items()}
    keys = list(groups)
    return {a for a in attrs if total.get(a) and share_ok(a) and not best([groups[k] for k in keys], a, total[a])[0]}

