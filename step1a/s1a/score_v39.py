"""wf_v3.9 Phase 1 (RULES_V1_3.md): pure scoring functions. No models, no LLM, no files.

- role-pure columns (rules 1): `role_counts`, `is_role_pure`;
- noise marks (rules 2a / 2b): `is_question_cluster`, `is_other_domain_cluster`, `mark_outcome`, `marks_v13`.
Loading and writing are in scripts/score_v39_p1.py.
"""

from collections import Counter

from . import pilot_score as PS
from .labels import _classes

PURE_SHARE = 0.80      # rules 1: share of a column's role mentions that must hold one role
CLUSTER_SHARE = 0.60   # rules 2a / 2b (the Q2 cluster rule)
REQUEST_CLASSES = ("cue", "request")


def role_counts(gold_attrs, gold_ents):
    """Counter {role slot: role mentions} over mention gold labels (a multi-class "A;B" mention counts once per class); only the
    slots of PS.ROLE_SLOTS are counted."""
    cnt = Counter()
    for g in gold_attrs:
        for c in _classes(g):
            slot = PS._slot(c, gold_ents)
            if slot in PS.ROLE_SLOTS:
                cnt[slot] += 1
    return cnt


def is_role_pure(counts, share=PURE_SHARE):
    """None for a column with no role mention (not a role column), else True when the biggest slot holds >= `share` of them."""
    total = sum(counts.values())
    if not total:
        return None
    return max(counts.values()) / total >= share


def _share(classes, pred):
    classes = list(classes)
    return sum(pred(c) for c in classes) / len(classes) if classes else 0.0


def is_question_cluster(classes, share=CLUSTER_SHARE):
    """True when >= `share` of the counted mention classes are request mentions (class cue / request)."""
    return _share(classes, lambda c: c in REQUEST_CLASSES) >= share


def is_other_domain_cluster(classes, share=CLUSTER_SHARE):
    """True when >= `share` of the counted mention classes are other-entity (wrong_entity / other_entity:<E>)."""
    return _share(classes, lambda c: c == "wrong_entity" or c.startswith("other_entity")) >= share


def mark_outcome(label, classes, has_cue):
    """Outcome of one marked cluster: "wrong_entity_dropped" (2b), "right" (label noise, or 2a: a question cluster when the
    variant has no attribute_cue label), else "wrong". `has_cue`: the variant's output has an attribute_cue label."""
    if is_other_domain_cluster(classes):
        return "wrong_entity_dropped"
    if label == "noise" or (not has_cue and is_question_cluster(classes)):
        return "right"
    return "wrong"


def marks_v13(clusters, marked, has_cue):
    """dict(marks_n, marks_right, wrong_entity_dropped) over the marked clusters. clusters {cluster_id: (label, [classes])};
    marked = set of marked cluster ids (ids missing from `clusters` are ignored, as in noise_v36.noise_l2_rows)."""
    out = Counter(mark_outcome(*clusters[c], has_cue) for c in marked if c in clusters)
    return {"marks_n": out["right"] + out["wrong"], "marks_right": out["right"],
            "wrong_entity_dropped": out["wrong_entity_dropped"]}
