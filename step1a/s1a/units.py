"""Step 1a units on Conversation: segments (Chroma chunks, oracle domain runs) and gold values.

Gold values come from TEAR's Conversation tables (one row per dialogue, header "Entity attr").
A value is located in the dialogue text (case-insensitive, word boundaries); the occurrence
in a turn whose gold domain is the attribute's entity is preferred, else the first one.
"""

import json
import re
from collections import Counter
from dataclasses import dataclass

from . import paths  # noqa: F401  (puts chunking/ and hdbscan/ on sys.path)
from chk.metrics import align

WINDOW = 10  # words each side for the "window" variant


@dataclass
class Unit:
    kind: str        # "chroma", "oracle_seg", "value"
    doc_id: str
    label: str       # gold domain (segments) or gold attribute (values)
    text: str        # the segment text, or the value string
    start: int = 0   # char span in the dialogue text
    end: int = 0
    turn: int = -1   # values: index of the turn holding the occurrence


def load_tables(tear_data, ids):
    want, out = set(ids), {}
    for name in ("input", "pool", "test"):
        p = tear_data / f"{name}.jsonl"
        if not p.exists():
            continue
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if r["id"] in want and r["id"] not in out and "table" in r:  # input.jsonl rows hold no table
                out[r["id"]] = r["table"]
    return out


def turn_of(doc, pos):
    for i, (s, e) in enumerate(doc.spans):
        if s <= pos <= e:
            return i
    return len(doc.spans) - 1


def majority(labels):
    return Counter(labels).most_common(1)[0][0] if labels else "general"


def turns_overlapping(doc, start, end):
    return [i for i, (s, e) in enumerate(doc.spans) if s < end and e > start]


def chroma_units(doc, chunks):
    spans, _ = align(doc.text, chunks)
    out = []
    for s, e in spans:
        ts = turns_overlapping(doc, s, e)
        out.append(Unit("chroma", doc.doc_id, majority([doc.domains[t] for t in ts]),
                        doc.text[s:e].strip(), s, e))
    return out


def oracle_segments(doc):
    out, start = [], 0
    for t in range(1, doc.n_turns + 1):
        if t == doc.n_turns or doc.domains[t] != doc.domains[start]:
            s, e = doc.spans[start][0], doc.spans[t - 1][1]
            out.append(Unit("oracle_seg", doc.doc_id, doc.domains[start], doc.text[s:e], s, e))
            start = t
    return out


def locate(doc, value, entity):
    """Char span of the best occurrence of value, or None."""
    pat = re.compile(r"(?<!\w)" + re.escape(value.strip()) + r"(?!\w)", re.I)
    hits = [(m.start(), m.end()) for m in pat.finditer(doc.text)]
    if not hits:
        return None
    for s, e in hits:
        if doc.domains[turn_of(doc, s)] == entity:
            return s, e
    return hits[0]


def value_units(doc, table):
    """Returns (units, n_missing)."""
    out, missing = [], 0
    for row in table["rows"]:
        for header, vals in zip(table["headers"], row):
            entity = header.split()[0].lower()
            for v in vals:
                if not str(v).strip():
                    continue
                span = locate(doc, str(v), entity)
                if span is None:
                    missing += 1
                    continue
                s, e = span
                out.append(Unit("value", doc.doc_id, header, doc.text[s:e], s, e, turn_of(doc, s)))
    return out, missing


def value_text(doc, u, variant):
    if variant == "value":
        return u.text
    if variant == "turn":
        ts, te = doc.spans[u.turn]
        return f"{u.text} | {doc.text[ts:te]}"
    if variant == "window":
        left = doc.text[:u.start].split()[-WINDOW:]
        right = doc.text[u.end:].split()[:WINDOW]
        return " ".join(left + [f"[{u.text}]"] + right)
    raise ValueError(variant)
