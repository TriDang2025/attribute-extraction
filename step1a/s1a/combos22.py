"""wf_v2.2 part J: the parts that helped alone (H role word, G staged context) followed by F fold.
All on top of wf_v2.1 (stop list + code shapes + value-type split)."""

from functools import partial

from . import fold as F
from . import roleword as H
from . import staged as G
from .combos import V21_FILTER
from .variants import Variant


def _v(note, base, m="mean", tau=0.6, bk=False):
    return Variant(span_filter=V21_FILTER, note=note,
                   cluster_fn=partial(F.cluster_fn, min_size=m, tau=tau, use_books=bk, base=base))


_H = {k: partial(H.cluster_fn, left=l, right=r, t=t) for k, (l, r, t) in
      {"l1r0_t035": (1, 0, 0.35), "l1r0_t04": (1, 0, 0.4), "l0r1_t04": (0, 1, 0.4),
       "l1r1_t04": (1, 1, 0.4)}.items()}
_G = {"w2_t1_03": partial(G.cluster_fn, context="window", k=2, t1=0.3)}

CONFIGS = {}
for k, base in (_H | _G).items():
    tag = "H" if k in _H else "G"
    CONFIGS[f"J_{tag}{k}_fmean06"] = _v(f"{tag} {k} + fold mean, tau 0.6", base)
    CONFIGS[f"J_{tag}{k}_fm2_06bk"] = _v(f"{tag} {k} + fold 2, tau 0.6, booking", base, m=2, bk=True)
    CONFIGS[f"J_{tag}{k}_fmean05"] = _v(f"{tag} {k} + fold mean, tau 0.5", base, tau=0.5)
