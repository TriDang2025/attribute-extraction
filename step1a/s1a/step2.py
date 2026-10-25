"""Step 2: cluster attribute values inside each entity group.

Pieces: value normalization and typing, masked turn context, string + context vectors,
agglomerative clustering with a threshold (optionally with cannot-link constraints), and a
post-hoc merge of clusters that never share a booking. Generic over objects with
doc_id / text / start / end / turn, so predicted spans can be plugged in later.
"""

import re
from collections import Counter, defaultdict

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from . import paths  # noqa: F401  (chunking/ and hdbscan/ on sys.path)

TAGS = {"time": "[TIME]", "day": "[DAY]", "number": "[NUMBER]", "price": "[PRICE]",
        "id": "[ID]", "text": "[TEXT]"}
type_tags = TAGS
NUM_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "weekend", "today", "tomorrow"}
_EDGE = re.compile(r"^[^\w£]+|[^\w]+$")
_AMPM = r"(a\.?m\.?|p\.?m\.?)"


def _hhmm(h, m, ap=None):
    h, m = int(h), int(m)
    if ap:
        ap = ap.replace(".", "")
        if h > 12:
            return None
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
    return f"{h:02d}:{m:02d}" if h < 24 and m < 60 else None


def _time(s):
    """24h "HH:MM" when the whole string is clearly a time, else None."""
    m = re.fullmatch(r"(\d{1,2})[:.](\d{2})\s*" + _AMPM + "?", s)
    if m:
        return _hhmm(*m.groups())
    m = re.fullmatch(r"(\d{1,2})\s*" + _AMPM, s)
    if m:
        return _hhmm(m.group(1), 0, m.group(2))
    m = re.fullmatch(r"([01]\d|2[0-3])([0-5]\d)", s)  # "1715"; 4 digits, hh <= 23, mm <= 59
    return _hhmm(*m.groups()) if m else None


def _lemma(w):
    if len(w) <= 3 or not w.isalpha():
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("sses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def normalize(value):
    """Lowercase, trim punctuation, 24h times, number words -> digits, plural strip."""
    s = re.sub(r"\s+", " ", str(value).lower()).strip()
    s = _EDGE.sub("", s)
    t = {"noon": "12:00", "midnight": "00:00"}.get(s) or _time(s)
    if t:
        return t
    toks = []
    for w in s.split():
        w = NUM_WORDS.get(w, w)
        toks.append(_lemma(w))
    s = " ".join(toks)
    # times inside a longer string, e.g. "after 5:30 pm"
    s = re.sub(r"(?<![£\d.:])\b(\d{1,2}):(\d{2})\s*" + _AMPM + r"?(?!\w)",
               lambda m: _hhmm(*m.groups()) or m.group(0), s)
    return s


def value_type(value):
    """time, day, number, price, id or text."""
    raw = str(value).strip()
    s = normalize(raw)
    if "£" in raw or re.search(r"\b(pound|gbp|quid)\b", s):
        return "price"
    if re.search(r"\b\d{2}:\d{2}\b", s):
        return "time"
    toks = s.split()
    if toks and len(toks) <= 2 and any(w in DAYS or w.rstrip("s") in DAYS for w in toks):
        return "day"
    if re.fullmatch(r"[A-Za-z0-9]{6,10}", raw) and re.search(r"\d", raw) and re.search(r"[A-Za-z]", raw):
        return "id"
    if re.fullmatch(r"[A-Z]{8}", raw):  # all-letter reference codes, e.g. "OAEJMYOI"
        return "id"
    if re.fullmatch(r"\d+( [a-z]+)?", s):
        return "number"
    return "text"


def turn_index(doc, m):
    if getattr(m, "turn", -1) is not None and getattr(m, "turn", -1) >= 0:
        return m.turn
    for i, (s, e) in enumerate(doc.spans):
        if s <= m.start <= e:
            return i
    return len(doc.spans) - 1


def _value_spans(doc, lo, hi, mentions_in_doc, mask_strings=True):
    """(start, end, text) of mention spans inside [lo, hi], plus (mask_strings) every other
    occurrence of a mention string there; sorted by start, longer first."""
    spans = [(m.start, m.end, m.text) for m in mentions_in_doc
             if m.start is not None and m.start >= 0 and m.start >= lo and m.end <= hi]
    if mask_strings:
        win = doc.text[lo:hi]
        for v in {m.text for m in mentions_in_doc if m.text and m.text.strip()}:
            pat = re.compile(r"(?<!\w)" + re.escape(v.strip()) + r"(?!\w)", re.I)
            spans += [(lo + a.start(), lo + a.end(), v) for a in pat.finditer(win)]
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    return spans


def masked_context(doc, mention, mentions_in_doc, prev_turns=1, mask_strings=True, mark_target=True):
    """Text of the mention's turn and `prev_turns` previous turns, with every mention span in
    that window replaced by its type tag. mask_strings also tags other occurrences of the
    mention strings (a value said twice but located once), so no value string leaks. mark_target
    writes the mention's own tag as <<[TAG]>>, so mentions in the same turns get different contexts."""
    t = turn_index(doc, mention)
    lo, hi = doc.spans[max(0, t - prev_turns)][0], doc.spans[t][1]
    spans = _value_spans(doc, lo, hi, mentions_in_doc, mask_strings)
    out, pos = [], lo
    for s, e, v in spans:
        if s < pos:
            continue  # overlaps a span already replaced
        tag = TAGS[value_type(v)]
        if mark_target and (s, e) == (mention.start, mention.end):
            tag = f"<<{tag}>>"
        out += [doc.text[pos:s], tag]
        pos = e
    out.append(doc.text[pos:hi])
    return "".join(out)


_SPEAKER = re.compile(r"\s*(User|System)\s*:\s*")


def _masked(doc, a, b, spans):
    """doc.text[a:b] with the spans inside it (already non-overlapping) replaced by type tags."""
    out, pos = [], a
    for s, e, v in spans:
        if s < pos or s < a or e > b:
            continue
        pad_l = " " if s > 0 and doc.text[s - 1].isalnum() else ""
        pad_r = " " if e < len(doc.text) and doc.text[e].isalnum() else ""
        out += [doc.text[pos:s], pad_l + TAGS[value_type(v)] + pad_r]
        pos = e
    out.append(doc.text[pos:b])
    return "".join(out)


def window_texts(doc, mention, mentions_in_doc, k, side="lr", mask_strings=True):
    """k words before and after the mention inside its own turn (speaker prefix stripped), other
    values masked by type tag, target written as <<[TAG]>>. side "lr" -> (left, right) with left
    ending and right starting at the mark; side "sym" -> one string left + mark + right."""
    lo, hi = doc.spans[turn_index(doc, mention)]
    m = _SPEAKER.match(doc.text, lo, hi)
    if m:
        lo = m.end()
    ts, te = mention.start, mention.end
    spans = [x for x in _value_spans(doc, lo, hi, mentions_in_doc, mask_strings)
             if x[1] <= ts or x[0] >= te]  # the target wins over anything overlapping it
    left = _masked(doc, lo, ts, spans).split()[-k:] if k > 0 else []
    right = _masked(doc, te, hi, spans).split()[:k] if k > 0 else []
    mark = f"<<{TAGS[value_type(mention.text)]}>>"
    if side == "sym":
        return " ".join(left + [mark] + right)
    return " ".join(left + [mark]), " ".join([mark] + right)


def _unit(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.where(n == 0, 1, n)


def combine(ctx_vecs, str_vecs, alpha):
    """alpha * context + (1 - alpha) * string, re-normalized rows."""
    return _unit(alpha * np.asarray(ctx_vecs, float) + (1 - alpha) * np.asarray(str_vecs, float)).astype(np.float32)



def combine_window(ctx_vecs, left_vecs, right_vecs, str_vecs, alpha, beta):
    """alpha * context + beta * window + (1 - alpha - beta) * string, re-normalized rows. Window =
    (left + right) / 2, or left_vecs alone when right_vecs is None (the "sym" window).
    beta = 0 gives exactly combine(ctx, string, alpha)."""
    if not beta:
        return combine(ctx_vecs, str_vecs, alpha)
    w = np.asarray(left_vecs, float)
    if right_vecs is not None:
        w = (w + np.asarray(right_vecs, float)) / 2
    s = np.asarray(str_vecs, float)
    c = np.asarray(ctx_vecs, float) if alpha else np.zeros_like(s)
    return _unit(alpha * c + beta * w + (1 - alpha - beta) * s).astype(np.float32)


def labels_of(u):
    return frozenset(u.labels) if hasattr(u, "labels") else frozenset({u.label})


def gold_entity(u, doc=None):
    """Entity (first word) of the mention's label; several -> the turn's domain, else first sorted."""
    ents = sorted({l.split()[0] for l in labels_of(u)})
    if len(ents) > 1 and doc is not None:
        dom = doc.domains[turn_index(doc, u)].lower()
        for e in ents:
            if e.lower() == dom:
                return e
    return ents[0]


def _by_group(groups):
    idx = defaultdict(list)
    for i, g in enumerate(groups):
        idx[g].append(i)
    return idx


def _name(g):
    return "|".join(map(str, g)) if isinstance(g, tuple) else str(g)


def string_ceiling(units, groups):
    """Best string-only clustering: each normalized string (per group) -> its most frequent gold label."""
    cnt = defaultdict(Counter)
    for u, g in zip(units, groups):
        cnt[(g, normalize(u.text))].update(labels_of(u))
    best = {k: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k, c in cnt.items()}
    return [f"{_name(g)}:{best[(g, normalize(u.text))]}" for u, g in zip(units, groups)]


def oracle_k(vecs, units, groups, linkage="average"):
    """Agglomerative (cosine) with n_clusters = number of gold classes present in each group."""
    lab = [None] * len(units)
    for g, idx in _by_group(groups).items():
        k = len(set().union(*[labels_of(units[i]) for i in idx]))
        if k >= len(idx):
            sub = range(len(idx))
        else:
            sub = AgglomerativeClustering(n_clusters=k, metric="cosine",
                                          linkage=linkage).fit_predict(vecs[idx])
        for i, c in zip(idx, sub):
            lab[i] = f"{_name(g)}:{c}"
    return lab


def cluster_threshold(vecs, groups, t, linkage="average"):
    """relabel.stage2 with a linkage choice: cosine agglomerative, distance threshold t, per group."""
    lab = [None] * len(groups)
    for g, idx in _by_group(groups).items():
        if len(idx) == 1:
            sub = [0]
        else:
            sub = AgglomerativeClustering(n_clusters=None, distance_threshold=t, metric="cosine",
                                          linkage=linkage).fit_predict(vecs[idx])
        for i, c in zip(idx, sub):
            lab[i] = f"{_name(g)}:{c}"
    return lab


def constrained_agglomerative(dist, cannot_link=None, t=0.4, linkage="average"):
    """Agglomerative on a precomputed distance matrix (Lance-Williams), never merging two
    clusters with a cannot-link pair across them; stops when the smallest allowed linkage
    distance is >= t (as sklearn's distance_threshold). cannot_link: (n, n) bool matrix or
    iterable of index pairs. Returns labels 0..K-1 in order of first appearance."""
    D = np.array(dist, dtype=float)
    n = len(D)
    if n <= 1:
        return np.zeros(n, dtype=int)
    if cannot_link is None:
        C = np.zeros((n, n), bool)
    elif isinstance(cannot_link, np.ndarray):
        C = cannot_link.astype(bool).copy()
    else:
        C = np.zeros((n, n), bool)
        for i, j in cannot_link:
            C[i, j] = C[j, i] = True
    size = np.ones(n)
    active = np.ones(n, bool)
    parent = np.arange(n)
    np.fill_diagonal(C, True)  # never "merge" a cluster with itself

    def row(i):
        r = np.where(C[i] | ~active, np.inf, D[i])
        k = int(np.argmin(r))
        return r[k], k

    rmin = np.empty(n)
    rarg = np.empty(n, int)
    for i in range(n):
        rmin[i], rarg[i] = row(i)
    while True:
        m = np.where(active, rmin, np.inf)
        i = int(np.argmin(m))
        if not np.isfinite(m[i]) or m[i] >= t:
            break
        j = int(rarg[i])
        if linkage == "average":
            new = (size[i] * D[i] + size[j] * D[j]) / (size[i] + size[j])
        elif linkage == "complete":
            new = np.maximum(D[i], D[j])
        elif linkage == "single":
            new = np.minimum(D[i], D[j])
        else:
            raise ValueError(linkage)
        D[i], D[:, i] = new, new
        C[i] |= C[j]
        C[:, i] = C[i]
        size[i] += size[j]
        active[j] = False
        parent[parent == j] = i
        # refresh row minima that pointed at i or j, or that i now beats
        cand = np.where(C[i] | ~active, np.inf, D[i])
        others = active.copy()
        others[i] = False
        stale = others & ((rarg == i) | (rarg == j))
        better = others & ~stale & (cand < rmin)
        rmin[better], rarg[better] = cand[better], i
        for k in np.where(stale)[0]:
            rmin[k], rarg[k] = row(k)
        rmin[i], rarg[i] = row(i)
    _, lab = np.unique(parent, return_inverse=True)
    order = {}
    return np.array([order.setdefault(x, len(order)) for x in lab])


def cannot_links(units, booking_ids):
    """Index pairs (i < j) in the same booking with different normalized strings."""
    by = _by_group(booking_ids)
    out = set()
    for idx in by.values():
        norm = [normalize(units[i].text) for i in idx]
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                if norm[a] != norm[b]:
                    out.add((idx[a], idx[b]))
    return out


def cluster_constrained(vecs, groups, pairs, t, linkage="average"):
    """constrained_agglomerative (cosine distance) inside each group; pairs are global indices."""
    lab = [None] * len(groups)
    for g, idx in _by_group(groups).items():
        pos = {i: k for k, i in enumerate(idx)}
        local = [(pos[a], pos[b]) for a, b in pairs if a in pos and b in pos]
        x = vecs[idx]
        sub = constrained_agglomerative(np.clip(1 - x @ x.T, 0, 2), local, t, linkage)
        for i, c in zip(idx, sub):
            lab[i] = f"{_name(g)}:{c}"
    return lab


def merge_split_clusters(labels, ctx_vecs, booking_ids, theta, groups=None):
    """Repeatedly merge the most similar pair of clusters (cosine of mean context vectors >= theta)
    whose members never share a booking; with groups, only clusters of the same group merge.
    Returns (new labels, merge log [(cos, members_a, members_b)])."""
    names = sorted(set(labels), key=str)
    members = {c: [i for i, l in enumerate(labels) if l == c] for c in names}
    books = {c: {booking_ids[i] for i in members[c]} for c in names}
    grp = {c: (groups[members[c][0]] if groups is not None else 0) for c in names}
    x = np.asarray(ctx_vecs, float)
    live = list(names)
    log = []
    while len(live) > 1:
        M = _unit(np.stack([x[members[c]].mean(0) for c in live]))
        S = M @ M.T
        np.fill_diagonal(S, -np.inf)
        for a in range(len(live)):
            for b in range(a + 1, len(live)):
                if S[a, b] < theta:
                    continue
                ca, cb = live[a], live[b]
                if grp[ca] != grp[cb] or books[ca] & books[cb]:
                    S[a, b] = S[b, a] = -np.inf
        a, b = np.unravel_index(int(np.argmax(S)), S.shape)
        if not S[a, b] >= theta:
            break
        ca, cb = live[a], live[b]
        log.append((float(S[a, b]), list(members[ca]), list(members[cb])))
        members[ca] += members.pop(cb)
        books[ca] |= books.pop(cb)
        live.remove(cb)
    out = list(labels)
    for c in live:
        for i in members[c]:
            out[i] = c
    return out, log


def _with_window(units, docs, enc, cfg, ctx, x):
    """String vectors x mixed with context (alpha) and the k-word window (beta, side)."""
    by_doc = defaultdict(list)
    for u in units:
        by_doc[u.doc_id].append(u)
    side = cfg.get("side", "lr")
    w = [window_texts(docs[u.doc_id], u, by_doc[u.doc_id], cfg["window"], side) for u in units]
    if side == "sym":
        lv, rv = enc.encode(w), None
    else:
        lv, rv = enc.encode([a for a, _ in w]), enc.encode([b for _, b in w])
    return combine_window(ctx, lv, rv, x, cfg.get("alpha") or 0.0, cfg["beta"])


def step2_vectors(units, docs, enc, cfg):
    """Vectors a Step-2 config clusters on: (x, ctx) with x the string / context / window mix and
    ctx the masked-context vectors (None when the config has no alpha or theta)."""
    texts = [normalize(u.text) if cfg.get("normalize") else u.text for u in units]
    x = enc.encode(texts)
    ctx = None
    if cfg.get("alpha") is not None or cfg.get("theta") is not None:
        by_doc = defaultdict(list)
        for u in units:
            by_doc[u.doc_id].append(u)
        ctx = enc.encode([masked_context(docs[u.doc_id], u, by_doc[u.doc_id],
                                         cfg.get("prev_turns", 1)) for u in units])
    if cfg.get("window") and cfg.get("beta"):
        x = _with_window(units, docs, enc, cfg, ctx, x)
    elif cfg.get("alpha") is not None:
        x = combine(ctx, x, cfg["alpha"])
    return x, ctx


def step2_cluster(units, groups, booking_ids, x, ctx, cfg):
    """Cluster the vectors of step2_vectors inside each group: returns labels."""
    parts = [(g, value_type(u.text)) for g, u in zip(groups, units)] if cfg.get("by_type") else list(groups)
    t, link = cfg["t"], cfg.get("linkage", "average")
    if cfg.get("cannot_link"):
        lab = cluster_constrained(x, parts, cannot_links(units, booking_ids), t, link)
    else:
        lab = cluster_threshold(x, parts, t, link)
    if cfg.get("theta") is not None:
        lab, _ = merge_split_clusters(lab, ctx, booking_ids, cfg["theta"], groups)
    return lab


def run_best(units, docs, groups, booking_ids, enc, cfg):
    """Apply a chosen Step-2 config (chosen_step2.json) to any units: returns labels.
    Optional window keys: window (k words), beta (window weight), side ("lr" | "sym")."""
    x, ctx = step2_vectors(units, docs, enc, cfg)
    return step2_cluster(units, groups, booking_ids, x, ctx, cfg)
