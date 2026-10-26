"""v2.1 part B: replace code-like span values (train id, booking reference, phone, postcode, price) by a
canonical SHAPE text before bge-m3 encoding, so all values of one kind land in one cluster.
Everything else keeps its raw text. Exports CONFIGS (see variants.py)."""

import re

from .variants import Variant, cluster_texts

_I = re.I
_TRAIN = re.compile(r"(?:train\s+)?tr\s?\d{4}", _I)
_POSTCODE = re.compile(r"cb\s?\d{1,2}\s?\d[a-z]{2}", _I)
_PHONE = re.compile(r"(?:\+44\s?)?0[\d ]{9,12}")
_REF = re.compile(r"[a-z0-9]{8}", _I)
_PRICE = re.compile(r"(?:£\s?\d+(?:\.\d+)?|\d+(?:\.\d+)?\s?(?:pounds?|gbp|gpb|quid|£))(?:\s+fee)?", _I)

SHAPES = {
    "train": "train id TR####",
    "ref": "reference code XXXXXXXX",
    "phone": "phone number 01223 ######",
    "postcode": "postcode CB# #XX",
    "price": "price ## pounds",
}
CODES = ("train", "ref", "phone", "postcode")


def kind(text):
    """train / ref / phone / postcode / price, or None for any other text."""
    s = str(text).strip()
    if _TRAIN.fullmatch(s):
        return "train"
    if _POSTCODE.fullmatch(s):
        return "postcode"
    if _PHONE.fullmatch(s) and 10 <= len(re.sub(r"\D", "", s)) <= 13:
        return "phone"
    # 8 letters+digits with at least one digit, or 8 capital letters; a plain 8-letter word is not a code
    if _REF.fullmatch(s) and (re.search(r"\d", s) and re.search(r"[a-z]", s, _I) or re.fullmatch(r"[A-Z]{8}", s)):
        return "ref"
    if _PRICE.fullmatch(s):
        return "price"
    return None


def shape(text, kinds=CODES + ("price",)):
    k = kind(text)
    return SHAPES[k] if k in kinds else text


def _make(kinds, t=0.4):
    def fn(spans, docs, enc, groups, books):
        return cluster_texts(spans, [shape(u.text, kinds) for u in spans], groups, enc, t)
    return fn


CONFIGS = {
    "B_codes": Variant(cluster_fn=_make(CODES), note="codes -> shape text (train id, reference, phone, postcode)"),
    "B_codes_prices": Variant(cluster_fn=_make(CODES + ("price",)), note="codes and prices -> shape text"),
    "B_codes_prices_t05": Variant(cluster_fn=_make(CODES + ("price",), 0.5), note="codes and prices -> shape text, t=0.5"),
}
