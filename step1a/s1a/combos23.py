"""wf_v3.7 Step 1a v2.3 = v2.2 (V21 + fold min 2, tau 0.6, booking) with the T26 value-type fix in both type partitions,
then the J split of two-role clusters (roles_v37: general + learned cue words, unknown-role part). No gold labels.
V23_NOJ = the value-type fix alone (to tell the two changes apart). v2.2 stays reachable as fold.CONFIGS["F_m2_t06_bk"]."""

from functools import partial

from . import combos
from . import fold as F
from . import roles_v37 as R37
from .combos import V21_FILTER
from .mentions import turn_bounds
from .roles_v35 import left_tokens
from .value_types import value_type_v35
from .variants import Variant

V21_T26 = combos._v("A + B + type (T26 value types), t 0.4", type_fn=value_type_v35)
_FOLD = partial(F.cluster_fn, min_size=2, tau=0.6, use_books=True, base=V21_T26.cluster_fn, type_fn=value_type_v35)
LAST_SPLIT = []  # stats of the last J split (roles_v37.split_labels), for the report scripts


def span_lefts(spans, docs):
    """Left-token lists (3 words before the value inside its turn, nearest last) of each span."""
    out = []
    for u in spans:
        lo, _ = turn_bounds(docs[u.doc_id], u.turn)
        out.append(left_tokens(docs[u.doc_id].text[lo:max(lo, u.start)]))
    return out


def cluster_fn(spans, docs, enc, groups, books):
    x, labels = _FOLD(spans, docs, enc, groups, books)
    new, stats = R37.split_labels(labels, groups, span_lefts(spans, docs))
    LAST_SPLIT[:] = stats
    return x, new


CONFIGS = {
    "V23_NOJ": Variant(span_filter=V21_FILTER, cluster_fn=_FOLD,
                       note="v2.2 + T26 value types (no J split)"),
    "V23": Variant(span_filter=V21_FILTER, cluster_fn=cluster_fn,
                   note="v2.2 + T26 value types + J split (general + learned cue words, unknown-role part)"),
}
