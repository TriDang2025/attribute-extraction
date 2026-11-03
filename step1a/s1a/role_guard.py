"""wf_v3.5 T20: deterministic check that rejects a merge across a role pair.

Forbidden pairs: departure / destination, leave at / arrive by, location / address. An attribute is on a side of a pair
when its name or role contains a word of that side (words split on non-letters, lower case) and no word of the other
side. A merge of two attributes on opposite sides of one pair is rejected. Descriptions are not read (they often
mention both ends). Names that contain both sides of a pair, or neither, are never rejected.
"""

import re

from .pilot_verify import norm_name

# (side A words, side B words); "departure" / "arrival" also count for leave at / arrive by (departure_time)
PAIRS = (({"departure", "depart", "departs", "origin"}, {"destination", "arrival", "arrive", "arrives"}),
         ({"leave", "leaves", "leaving", "leaveat", "departure", "depart", "departs"},
          {"arrive", "arrives", "arriving", "arriveby", "arrival"}),
         ({"location"}, {"address"}))


def _words(text):
    return set(re.split(r"[^a-z0-9]+", str(text).lower())) - {""}


def forbidden_merge(a, b, pairs=PAIRS):
    """True when attribute texts a and b (name + " " + role) sit on opposite sides of a forbidden pair of `pairs`."""
    wa, wb = _words(a), _words(b)
    for left, right in pairs:
        a_l, a_r, b_l, b_r = bool(wa & left), bool(wa & right), bool(wb & left), bool(wb & right)
        if (a_l and not a_r and b_r and not b_l) or (a_r and not a_l and b_l and not b_r):
            return True
    return False


def filter_reconcile_answers(units, answers, roles=None):
    """(answers, rejected): reconcile answers {unit_id: obj with same_as} with every merge across a forbidden pair
    set to same_as "none" (marked `role_pair_rejected`). `units` as pilot_combine.units_from_dec; `roles`
    {norm name: role} from the entity answers. rejected = [(unit_id, unit name, same_as)]."""
    roles = roles or {}

    def text(name):
        return f"{name} {roles.get(norm_name(name), '')}"

    out, rejected = {}, []
    names = {u["uid"]: u["name"] for u in units}
    for uid, obj in answers.items():
        target = (obj or {}).get("same_as", "none")
        if norm_name(target) not in ("none", "") and forbidden_merge(text(names.get(uid, "")), text(target)):
            out[uid] = {**obj, "same_as": "none", "role_pair_rejected": target}
            rejected.append((uid, names.get(uid, ""), target))
        else:
            out[uid] = obj
    return out, rejected
