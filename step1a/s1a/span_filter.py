"""v2.1 part A: drop junk GLiNER spans (pronouns, fillers, slot names) before clustering.

A span is dropped only if its WHOLE normalized text is in the list (lowercase, punctuation stripped,
leading the/a/an removed); never a substring match. The lists are generic English / booking-slot
vocabulary, not derived from gold labels.
"""

import re
from functools import partial

from .variants import Variant

STOP = frozenset({
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "she", "it", "they", "them",
    "this", "that", "these", "those", "there", "here", "one", "ones", "something", "anything",
    "hi", "hello", "hey", "bye", "goodbye", "thanks", "thank you", "please", "sorry", "ok", "okay",
    "yes", "no", "sure", "sir", "madam", "today", "tomorrow", "now", "time", "day", "thing",
})

SLOT_NAMES = frozenset({
    "address", "postcode", "post code", "zip code", "phone", "phone number", "telephone number",
    "reference number", "reference", "confirmation number", "booking reference", "booking number",
    "entrance fee", "fee", "price", "price range", "cost", "area", "location", "name", "type",
    "food", "cuisine", "day", "time", "departure time", "arrival time", "leave time", "arrive time",
    "departure", "destination", "stars", "star rating", "rating", "number of people", "people",
    "train id", "car type", "contact number", "number", "date", "length of stay", "stay",
    "parking", "internet", "wifi",
})

_PUNCT = re.compile(r"[^\w\s]")
_ART = re.compile(r"^(the|a|an)\s+")


def normalize(text):
    t = _PUNCT.sub(" ", text.lower())
    return _ART.sub("", " ".join(t.split()))


def _drop(spans, words):
    return [u for u in spans if normalize(u.text) not in words]


def drop_stop(spans, words=STOP):
    return _drop(spans, words)


def drop_slot_names(spans, names=SLOT_NAMES):
    return _drop(spans, names)


def min_score(spans, thr):
    """Keep spans with GLiNER score >= thr (spans without a score are kept)."""
    return [u for u in spans if getattr(u, "score", None) is None or u.score >= thr]


def compose(*fns):
    def run(spans):
        for f in fns:
            spans = f(spans)
        return spans
    return run


_s06 = partial(min_score, thr=0.6)

CONFIGS = {
    "A_stop": Variant(span_filter=drop_stop, note="drop pronouns / fillers"),
    "A_slots": Variant(span_filter=drop_slot_names, note="drop slot names"),
    "A_stop_slots": Variant(span_filter=compose(drop_stop, drop_slot_names), note="stop + slot names"),
    "A_stop_slots_s06": Variant(span_filter=compose(drop_stop, drop_slot_names, _s06),
                                note="stop + slot names + score >= 0.6"),
    "A_s06": Variant(span_filter=_s06, note="GLiNER score >= 0.6 only"),
}
