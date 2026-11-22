"""wf_v5.1 R0: score taxi as its own entity (switch, default off = the v5.0 scorer exactly).

Today (rules v1.3) the gold list of "restaurant" holds the taxi attributes too (pilot_eval_v31.GOLD_ENTS["restaurant"] = restaurant + taxi,
mainclaim_v41.DOMAIN_ENTITY["taxi"] = "restaurant") and a predicted entity that holds most of the taxi mentions is not scored at all
(mainclaim_v46.GOLD_ENTITIES has no taxi). Taxi rule (on): taxi is a fourth scored entity with its own gold list (the gold attributes whose
mentions belong to GT entity "taxi"); a predicted entity is matched to it by the usual rule (the GT entity most of the predicted entity's
mentions belong to, mainclaim_v46.entity_map), so a taxi gold attribute is found only on the predicted entity matched to taxi, with the same
purity 0.6 / coverage 0.10 found rule over that entity's clustered mentions. TEAR: a column whose header domain is taxi counts for taxi.
The gold count does not change (the taxi attributes only move from the restaurant list to the taxi list). Nothing else is edited:
`taxi_scoring` patches the existing scorers for the duration of a `with` block.
"""
from contextlib import contextmanager
from unittest.mock import patch

from . import mainclaim_v41 as MC
from . import v34_data as VD

TAXI = "taxi"


@contextmanager
def taxi_scoring(on=True):
    """Within the block: mainclaim_v41 scores `taxi` as a fourth entity (gold_lists, TEAR domain map). on=False changes nothing.
    mainclaim_v46.GOLD_ENTITIES (scripts/, which predicted entities are scored) is patched by scripts/r0_taxi_v51.rule."""
    if not on:
        yield
        return
    with patch.object(MC, "ENTITIES", (*MC.ENTITIES, TAXI)), patch.dict(MC.DOMAIN_ENTITY, {TAXI: TAXI}), \
            patch.dict(VD.GOLD_ENTS, {"restaurant": ["restaurant"], TAXI: [TAXI]}):
        yield


def moved_attrs(gold_off, gold_on):
    """The gold attributes whose entity differs between two gold lists ({entity: [attr]}): {attr: (entity off, entity on)}. Fails fast when the
    two lists do not hold the same attributes (the gold count must not change)."""
    off = {a: e for e, attrs in gold_off.items() for a in attrs}
    on = {a: e for e, attrs in gold_on.items() for a in attrs}
    if set(off) != set(on):
        raise ValueError(f"gold attributes differ: only off {sorted(set(off) - set(on))}, only on {sorted(set(on) - set(off))}")
    return {a: (off[a], on[a]) for a in off if off[a] != on[a]}


def adjust(base, f_ref, f_new):
    """found L2 of a changed final columns: the base set minus the loop-1 span finds that the change loses, plus the new ones (a lost find is
    counted lost even if loop 2 might credit it again: conservative, as scripts/g3_nojoin_v50.py)."""
    return (set(base) - (set(f_ref) - set(f_new))) | (set(f_new) - set(f_ref))
