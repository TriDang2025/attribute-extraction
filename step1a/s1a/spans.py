"""Value spans inside each entity piece with GLiNER and generic, schema-agnostic labels.

Pieces longer than the model's window are cut at line (turn) breaks; span offsets are mapped
back to the dialogue text. A span matches a gold value when their char spans overlap.
"""

import os
from pathlib import Path

from .units import Unit, turn_of

MODEL = Path(os.environ.get("CHK_MODELS", Path.home() / "models")) / "gliner_medium-v2.1"
LABELS = ["place", "time", "date", "day", "number", "price", "name", "duration"]
THRESHOLD = 0.3          # low, for recall; higher thresholds are filtered from the scores
MAX_WORDS = 200          # below the model's 384-token window
SPEAKERS = {"User", "System"}  # turn prefixes, tagged as names otherwise


def load():
    from gliner import GLiNER
    return GLiNER.from_pretrained(str(MODEL), local_files_only=True)


def windows(text, start, end, max_words=MAX_WORDS):
    """(abs_start, abs_end) pieces of text[start:end], cut at line breaks."""
    out, s, pos, words = [], start, start, 0
    for line in text[start:end].split("\n"):
        n = len(line.split())
        if words and words + n > max_words:
            out.append((s, pos - 1))
            s, words = pos, 0
        words += n
        pos += len(line) + 1
    out.append((s, end))
    return [(a, b) for a, b in out if text[a:b].strip()]


def extract(model, doc, spans, threshold=THRESHOLD):
    """GLiNER spans of every piece of one document, as Units (label filled later)."""
    wins = [w for s, e in spans for w in windows(doc.text, s, e)]
    preds = model.inference([doc.text[a:b] for a, b in wins], LABELS, threshold=threshold,
                            batch_size=8)
    out = []
    for (a, _), ents in zip(wins, preds):
        for ent in ents:
            if ent["text"] in SPEAKERS:
                continue
            s, e = a + ent["start"], a + ent["end"]
            u = Unit("span", doc.doc_id, "", doc.text[s:e], s, e, turn_of(doc, s))
            u.tag, u.score = ent["label"], float(ent["score"])
            out.append(u)
    return out


def match(spans, values):
    """Give each span the attribute of an overlapping gold value (each value used once,
    the best-overlapping span wins). Returns the number of gold values matched."""
    used = 0
    for v in values:
        best, ov = None, 0
        for u in spans:
            if u.doc_id != v.doc_id or u.label:
                continue
            o = min(u.end, v.end) - max(u.start, v.start)
            if o > ov:
                best, ov = u, o
        if best is not None:
            best.label = v.label
            used += 1
    return used
