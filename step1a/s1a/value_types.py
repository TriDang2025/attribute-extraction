"""Value types of span strings: the frozen step2.value_type plus the wf_v3.5 T26 fixes (light module: step2 only).
Used by checks_v35 (re-exported there) and by Step 1a v2.3 (combos23)."""

import re

from . import step2 as S2

_PRICE = re.compile(r"\d\s*-?\s*(?:gbp|gpb|pounds?|quid)\b")
_DURATION = re.compile(r"\d\s*-?\s*(?:minutes?|mins?|hours?|hrs?)\b")


def value_type_v35(text):
    """step2.value_type plus two fixes: a number glued to or hyphenated with a currency (8.08GBP, 37.79 GPB) is a
    price; a number with a duration unit (28-minute, 105 minutes) is a duration (the frozen function gives text /
    number). Everything else is the frozen result."""
    raw = str(text).strip()
    low = S2.normalize(raw)
    if "£" in raw or _PRICE.search(low):
        return "price"
    if _DURATION.search(low):
        return "duration"
    return S2.value_type(raw)
