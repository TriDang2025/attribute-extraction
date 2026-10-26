"""v2.1 part D: the context-aware Step 2 (step2.py) re-tuned on GLiNER spans (it was tuned on gold values)."""

import json

from . import step2 as S2
from .variants import Variant

BASE = {"normalize": True, "by_type": True, "linkage": "average", "prev_turns": 1}
WINDOW = {"window": 2, "beta": 0.5, "side": "lr", "alpha": 0.2}


def make_cluster_fn(cfg):
    def cluster_fn(spans, docs, enc, groups, books):
        x, ctx = S2.step2_vectors(spans, docs, enc, cfg)
        return x, S2.step2_cluster(spans, groups, books, x, ctx, cfg)
    return cluster_fn


def _variant(ctx, cl, t):
    cfg = dict(BASE, **ctx, cannot_link=cl, t=t)
    return Variant(cluster_fn=make_cluster_fn(cfg), note=json.dumps(cfg, sort_keys=True))


def _name(tag, cl, t):
    return f"D_{tag}_{'cl' if cl else 'nocl'}_t{round(t * 100):03d}"


_CONTEXTS = {"a02": {"alpha": 0.2}, "a05": {"alpha": 0.5}, "win": WINDOW}
CONFIGS = {_name(tag, cl, t): _variant(ctx, cl, t)
           for tag, ctx in _CONTEXTS.items() for cl in (False, True) for t in (0.35, 0.45, 0.55)}
# extras: alpha absent = strings + value type only (no context encoding), isolates what context adds
CONFIGS.update({_name("a0", False, t): _variant({}, False, t) for t in (0.3, 0.4, 0.5)})
CONFIGS[_name("a0", True, 0.4)] = _variant({}, True, 0.4)       # cannot-link effect without context
CONFIGS[_name("win", True, 0.65)] = _variant(WINDOW, True, 0.65)  # window vectors are tighter; looser t
