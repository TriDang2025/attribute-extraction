"""Helpers for label-free span extraction with spaCy. Stdlib only at import time, so the spaCy
venv can load this file directly; spans are lists [start, end, source, label] (dialogue offsets).
"""

import json

PREFIXES = ("User: ", "System: ")
DETERMINERS = {"the", "a", "an"}
PRONOUNS = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
            "that", "this", "these", "those", "one", "ones", "something", "anything",
            "everything", "nothing", "someone", "anyone", "what", "which", "who",
            "my", "your", "mine", "yours", "myself", "yourself", "there", "here"}


def prefix_len(turn_text):
    """Length of the speaker prefix of a turn line ("User: " / "System: "), 0 if none."""
    return next((len(p) for p in PREFIXES if turn_text.startswith(p)), 0)


def turn_bodies(text, turns):
    """[(offset, body)] per turn: the text after the speaker prefix and its dialogue offset."""
    out = []
    for s, e in turns:
        n = prefix_len(text[s:e])
        out.append((s + n, text[s + n:e]))
    return out


def to_dialogue(offset, s, e):
    """Map a span (s, e) local to a turn body back to dialogue offsets."""
    return offset + s, offset + e


def strip_determiner(text, s, e):
    """Drop leading the/a/an of the span text[s:e]; None when nothing is left or the rest is a
    pronoun. Offsets stay in the same coordinate system as text."""
    while True:
        word = text[s:e].split(None, 1)
        if not word:
            return None
        if word[0].lower() in DETERMINERS and len(word) > 1:
            s += text[s:e].index(word[1])
        else:
            break
    if text[s:e].strip().lower().strip(".,!?") in PRONOUNS:
        return None
    return s, e


def union(spans_a, spans_b):
    """Merge two span lists, dropping overlapping spans: the longest wins, ties go to the span
    seen first (list a before b). Returns spans sorted by start."""
    allspans = [list(x) for x in spans_a] + [list(x) for x in spans_b]
    order = sorted(range(len(allspans)), key=lambda i: (-(allspans[i][1] - allspans[i][0]), i))
    kept = []
    for i in order:
        s, e = allspans[i][:2]
        if all(e <= k[0] or s >= k[1] for k in kept):
            kept.append(allspans[i])
    return sorted(kept, key=lambda x: (x[0], x[1]))


def load_raw(path):
    """{doc_id: [[start, end, source, label], ...]} from the extractor's jsonl."""
    out = {}
    try:
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            out[r["doc_id"]] = r["spans"]
    except FileNotFoundError:
        pass
    return out


def load_spacy_cache(path, docs, dedup=True, sources=None):
    """Units (kind "span", tag = source, score 1.0) of every doc in docs, as in
    entity_seg.gliner_spans. dedup keeps the longest of overlapping spans; sources filters."""
    from .units import Unit, turn_of
    raw = load_raw(path)
    out = []
    for did, doc in docs.items():
        spans = [x for x in raw.get(did, []) if sources is None or x[2] in sources]
        if dedup:
            spans = union(spans, [])
        for s, e, src, _label in spans:
            u = Unit("span", did, "", doc.text[s:e], s, e, turn_of(doc, s))
            u.tag, u.score = src, 1.0
            out.append(u)
    return out
