"""Value spans inside each entity piece with GLiNER and generic, schema-agnostic labels.

Pieces longer than the model's window are cut at line (turn) breaks; span offsets are mapped
back to the dialogue text. A span matches a gold value when their char spans overlap.
"""

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path

from . import paths
from .units import Unit, turn_of

MODEL = Path(os.environ.get("CHK_MODELS", Path.home() / "models")) / "gliner_medium-v2.1"
LABELS = ["place", "time", "date", "day", "number", "price", "name", "duration"]
THRESHOLD = 0.3          # low, for recall; higher thresholds are filtered from the scores
MAX_WORDS = 200          # below the model's 384-token window
SPEAKERS = {"User", "System"}  # turn prefixes, tagged as names otherwise
HAND_EXTRA = ["cuisine", "area", "hotel type", "price range", "star rating", "departure station",
              "destination station", "departure time", "arrival time", "number of guests",
              "length of stay"]
PROMPT_LIMIT = 512       # subtokens of "labels + text" the encoder is trusted with


def gold_slot_labels():
    """Slot names of the gold schema ("Train leave at" -> "leave at"), deduplicated, in order."""
    schema = json.loads((paths.TEAR_DATA / "levels.json").read_text(encoding="utf-8"))["full_schema"]
    out = []
    for attr in schema:
        slot = attr.split(" ", 1)[1].lower()
        if slot not in out:
            out.append(slot)
    return out


class _LabelSets(Mapping):
    """Label sets by name; the gold one is built on first access only."""

    def __getitem__(self, name):
        if name == "generic":
            return list(LABELS)
        if name == "hand":
            return LABELS + HAND_EXTRA
        if name == "gold":
            return LABELS + [s for s in gold_slot_labels() if s not in LABELS]
        raise KeyError(name)

    def __iter__(self):
        return iter(("generic", "hand", "gold"))

    def __len__(self):
        return 3


LABEL_SETS = _LabelSets()


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


def _run(model, doc, wins, labels, threshold):
    preds = model.inference([doc.text[a:b] for a, b in wins], labels, threshold=threshold,
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


def extract(model, doc, spans, threshold=THRESHOLD, labels=LABELS):
    """GLiNER spans of every piece of one document, as Units (label filled later)."""
    wins = [w for s, e in spans for w in windows(doc.text, s, e)]
    return _run(model, doc, wins, labels, threshold)


def turn_windows(doc, max_words=MAX_WORDS):
    """One (abs_start, abs_end) window per turn, without the speaker prefix; turns longer than
    max_words words are cut at word boundaries."""
    out = []
    for s, e in doc.spans:
        m = re.match(r"(User|System): ", doc.text[s:e])
        a = s + (m.end() if m else 0)
        words = [w.span() for w in re.finditer(r"\S+", doc.text[a:e])]
        for i in range(0, len(words), max_words):
            part = words[i:i + max_words]
            out.append((a + part[0][0], a + part[-1][1]))
    return out


def extract_windows(model, doc, windows, labels=LABELS, threshold=THRESHOLD):
    """GLiNER spans of explicit (start, end) windows, tag = GLiNER label."""
    return _run(model, doc, windows, labels, threshold)


def prompt_tokens(model, text, labels):
    """Subtokens GLiNER feeds the encoder: one entity token + label tokens per label, then the text."""
    tk = model.data_processor.transformer_tokenizer
    n = len(tk(text, add_special_tokens=False)["input_ids"])
    return n + sum(len(tk(lab, add_special_tokens=False)["input_ids"]) + 1 for lab in labels) + 3


def fit_max_words(model, docs, labels, start=MAX_WORDS, floor=25):
    """Largest window size (words, from start, shrinking by a quarter) at which no turn window
    of docs exceeds PROMPT_LIMIT subtokens with labels. Returns (max_words, n_overflowing at
    start, n_windows)."""
    first, mw = None, start
    while True:
        wins = [doc.text[a:b] for doc in docs for a, b in turn_windows(doc, mw)]
        bad = sum(prompt_tokens(model, w, labels) > PROMPT_LIMIT for w in wins)
        first = bad if first is None else first
        if bad == 0 or mw <= floor:
            return mw, first, len(wins)
        mw = max(floor, mw * 3 // 4)


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
