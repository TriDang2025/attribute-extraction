"""v2.1 part E: combinations of the part A-D variants that helped alone.

A = drop stop words + slot names; B = code shapes (train id, reference, phone, postcode);
type = cluster inside value type; cue = left-word mix (beta, k = 1); cl = cannot-link per booking.
"""

from functools import partial

from . import cue as C
from . import shapes as SH
from . import span_filter as SF
from .variants import Variant

_A = SF.compose(SF.drop_stop, SF.drop_slot_names)
_B = partial(SH.shape, kinds=SH.CODES)


def _v(note, beta=0.0, by_type=True, t=0.4, cannot_link=False):
    return Variant(span_filter=_A, note=note,
                   cluster_fn=partial(C.cluster_fn, beta=beta, k=1, by_type=by_type, t=t,
                                      cannot_link=cannot_link, text_fn=_B))


CONFIGS = {
    "E_AB": _v("A + B, no type split", by_type=False),
    "E_AB_type": _v("A + B + type"),
    "E_AB_type_t045": _v("A + B + type, t 0.45", t=0.45),
    "E_AB_type_t035": _v("A + B + type, t 0.35", t=0.35),
    "E_AB_type_cue01": _v("A + B + type + cue 0.1", beta=0.1),
    "E_AB_type_cue02": _v("A + B + type + cue 0.2", beta=0.2),
    "E_AB_type_cue03": _v("A + B + type + cue 0.3", beta=0.3),
    "E_AB_type_cl": _v("A + B + type + cannot-link", cannot_link=True),
    "E_AB_type_cl_t05": _v("A + B + type + cannot-link, t 0.5", t=0.5, cannot_link=True),
    "E_AB_type_cue02_cl": _v("A + B + type + cue 0.2 + cannot-link", beta=0.2, cannot_link=True),
}

# public handles for building on wf_v2.1 (used by the v2.2 parts)
V21_FILTER = _A  # span filter: stop words + slot names
V21_TEXT = _B    # text_fn: code shapes
V21 = CONFIGS["E_AB_type"]  # the adopted wf_v2.1 variant (type split, t 0.4)
