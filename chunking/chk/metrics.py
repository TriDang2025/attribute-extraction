"""Chunk alignment, segmentation scores (Pk, WindowDiff, boundary F1), chunk stats,
coherence without gold, and retrieval."""

import re

import numpy as np

WS = re.compile(r"\s+")


# ------------------------------------------------------------------ alignment
def _norm_map(text):
    """Whitespace-collapsed text and, for each of its chars, the index in the original."""
    out, idx, prev_ws = [], [], False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_ws:
                out.append(" ")
                idx.append(i)
            prev_ws = True
        else:
            out.append(ch)
            idx.append(i)
            prev_ws = False
    return "".join(out), idx


def align(text, chunks):
    """Char start of each chunk in text (chunks may have changed whitespace). Returns (spans, n_failed)."""
    norm, idx = _norm_map(text)
    starts, cur, failed = [], 0, 0
    for c in chunks:
        cn = WS.sub(" ", c).strip()
        pos = -1
        for n in (40, 20, 8):
            if cn[:n]:
                pos = norm.find(cn[:n], cur)
                if pos >= 0:
                    break
        if pos < 0:
            failed += 1
            continue
        starts.append(idx[pos])
        cur = pos + max(1, min(len(cn), 8))
    if not starts or starts[0] != 0:
        starts = [0] + [s for s in starts if s > 0]
    ends = starts[1:] + [len(text)]
    return list(zip(starts, ends)), failed


def cuts_to_gaps(doc, spans):
    """Map chunk starts (except the first) to turn gaps. Returns (gap set, number of cuts inside a turn)."""
    gaps, inside = set(), 0
    tspans = doc.spans
    for c, _ in spans[1:]:
        g = None
        for t, (s, e) in enumerate(tspans):
            if c <= s:            # at or before the start of turn t -> gap t-1
                g = t - 1
                break
            if s < c < e:          # inside turn t: snap to the nearer edge
                inside += 1
                g = t - 1 if (c - s) <= (e - c) else t
                break
        if g is None:
            g = len(tspans) - 1
        if 0 <= g < len(tspans) - 1:
            gaps.add(g)
    return gaps, inside


# ------------------------------------------------------------------ segmentation
def _k(n, ref):
    return max(1, round(n / (2 * (len(ref) + 1))))


def pk_wd(n, ref, hyp):
    """Pk and WindowDiff over turns for one document (k = half the mean gold segment length)."""
    k = _k(n, ref)
    if n - k <= 0:
        return None
    r = np.zeros(n - 1, int)
    h = np.zeros(n - 1, int)
    r[list(ref)] = 1
    h[list(hyp)] = 1
    pk = wd = 0
    for i in range(n - k):
        rr, hh = r[i:i + k].sum(), h[i:i + k].sum()
        pk += (rr == 0) != (hh == 0)
        wd += rr != hh
    return pk / (n - k), wd / (n - k)


def boundary_counts(ref, hyp, tol):
    ref_left, tp = set(ref), 0
    for g in sorted(hyp):
        m = next((r for r in sorted(ref_left, key=lambda r: abs(r - g)) if abs(r - g) <= tol), None)
        if m is not None:
            ref_left.discard(m)
            tp += 1
    return tp, len(hyp), len(ref)


def prf(tp, n_hyp, n_ref):
    p = tp / n_hyp if n_hyp else 0.0
    r = tp / n_ref if n_ref else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def segments(n, gaps):
    segs, cur = [], [0]
    for t in range(1, n):
        if t - 1 in gaps:
            segs.append(cur)
            cur = []
        cur.append(t)
    segs.append(cur)
    return segs


# ------------------------------------------------------------------ coherence
def coherence(turn_emb, segs, domains):
    """Mean pairwise turn cosine inside each segment, mean cross-pair turn cosine between
    adjacent segments (same scale), and domain purity (turns in their segment's majority domain)."""
    intra, adj, pure = [], [], 0
    for s in segs:
        e = turn_emb[s]
        if len(s) > 1:
            m = e @ e.T
            intra.append((m.sum() - np.trace(m)) / (len(s) * (len(s) - 1)))
        dom = [domains[t] for t in s]
        pure += max(dom.count(d) for d in set(dom))
    for a, b in zip(segs, segs[1:]):
        adj.append(float((turn_emb[a] @ turn_emb[b].T).mean()))
    return intra, adj, pure


# ------------------------------------------------------------------ retrieval
def retrieval(q_emb, queries, chunk_emb, chunk_meta, doc_spans, top_k=(1, 3, 5), mrr_at=10):
    """chunk_meta: list of (doc_id, start, end); doc_spans: doc_id -> turn spans.
    Hit = a retrieved chunk of the right document overlapping a gold turn."""
    sims = q_emb @ chunk_emb.T
    K = max(max(top_k), mrr_at)
    order = np.argsort(-sims, axis=1)[:, :K]
    rec = {k: 0 for k in top_k}
    mrr, cp, cr = 0.0, [], []
    for qi, q in enumerate(queries):
        gold = [doc_spans[q["doc_id"]][t] for t in q["turns"]]
        gold_len = sum(e - s for s, e in gold)
        first, ov5, len5, cov = None, 0, 0, np.zeros(len(gold), int)
        for rank, ci in enumerate(order[qi]):
            d, s, e = chunk_meta[ci]
            ov = 0
            if d == q["doc_id"]:
                for gi, (gs, ge) in enumerate(gold):
                    o = max(0, min(e, ge) - max(s, gs))
                    ov += o
                    if rank < 5:
                        cov[gi] += o
            if ov and first is None:
                first = rank
            if rank < 5:
                ov5 += ov
                len5 += e - s
        for k in top_k:
            rec[k] += first is not None and first < k
        mrr += 1 / (first + 1) if first is not None else 0
        cp.append(ov5 / len5 if len5 else 0)
        cr.append(min(gold_len, int(np.minimum(cov, [e - s for s, e in gold]).sum())) / gold_len)
    n = len(queries)
    out = {f"recall@{k}": rec[k] / n for k in top_k}
    out.update({f"mrr@{mrr_at}": mrr / n, "char_precision@5": float(np.mean(cp)),
                "char_recall@5": float(np.mean(cr))})
    return out
