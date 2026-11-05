"""wf_v3.9 scoring of the Colab batch (T4 reconcile, T5 reconcile + duplicate check, T8 A-cue; contract WF_V39_BATCH.md, rules
RULES_V1_3.md): pure functions, no I/O, no models. Loading and writing are in scripts/score_v39_batch.py.

- choices_of / agreement / intersect: the reconcile answers of one entity and order, and how two orders compare.
- clean_joins / final_names: a duplicate check answer after cleaning, and the group renames of reconciled columns plus joins.
- mark_outcome_cue / cue_stats: rules 2a / 2b for a variant that has the attribute_cue label (a question cluster is right only
  when marked attribute_cue).
- tokens_rows: exact token table per family.
- reconcile_decision / cue_decision: the decision lines.
"""

from collections import Counter

from . import batch_v39 as B9
from . import score_v38 as S
from . import score_v39 as S39

CUE = "attribute_cue"


# ---- reconcile answers

def choices_of(jobs, rows):
    """{part id: chosen column cid or None} from the reconcile jobs of one set, entity and order (manifest rows) and the response
    rows {job: row or None}; a missing response or one with errors keeps the part (None)."""
    out = {}
    for j in jobs:
        r = rows.get(j["job"])
        out[j["pid"]] = B9.choice_from_response(r["parsed"], r["errors"], j["candidates"]) if r else None
    return out


def agreement(a, b):
    """(k, n): parts that got the same answer in both orders (the same column, or none in both); n = parts of `a`."""
    return sum(a[p] == b.get(p) for p in a), len(a)


def intersect(a, b):
    """Choices both orders agree on: {part id: cid} where the two orders chose the same column, else None."""
    return {p: (c if c is not None and c == b.get(p) else None) for p, c in a.items()}


# ---- duplicate check answers and renames

def clean_joins(joins):
    """(kept, dropped): a join keeps its distinct column ids in order; a join with fewer than 2 distinct ids is dropped (the
    parse error of the v3.9 batch). Everything else is as given."""
    kept, dropped = [], []
    for j in joins:
        ids = list(dict.fromkeys(j["columns"]))
        (kept if len(ids) >= 2 else dropped).append({**j, "columns": ids} if len(ids) >= 2 else j)
    return kept, dropped


def final_names(cols, joins=()):
    """{attr id: column name} of every group of the column dicts `cols`; a join (list of {"columns": [cids]}, after the code check)
    gives all groups of its columns the name of the biggest member (S.union_joins, S.join_base). Used to rename the groups of
    the A s012 variant so that the dashboard reads the reconciled / joined columns."""
    by_id = {c["cid"]: c for c in cols}
    name = {c["cid"]: c["name"] for c in cols}
    for comp in S.union_joins(list(joins)):
        base = S.join_base(by_id, comp)
        for c in comp:
            name[c] = by_id[base]["name"]
    return {g: name[c["cid"]] for c in cols for g in c["groups"]}


# ---- noise marks of a variant with the cue label

def mark_outcome_cue(label, classes, action):
    """Outcome of one marked cluster of a variant that has attribute_cue: wrong_entity_dropped (2b), right (label noise, or a
    question cluster (2a) marked attribute_cue), else wrong."""
    if S39.is_other_domain_cluster(classes):
        return "wrong_entity_dropped"
    if label == "noise" or (S39.is_question_cluster(classes) and action == CUE):
        return "right"
    return "wrong"


def cue_stats(clusters, actions):
    """dict for one entity of a variant with the cue label. clusters {cid: (label, [classes])}, actions {cid: decision action}
    (a cluster missing from `actions` has none). marks_n / marks_right / wrong_entity_dropped: as score_v39.marks_v13 with
    mark_outcome_cue; cue_marks: clusters marked attribute_cue; cue_question: of them question clusters; cue_other_domain: of
    them other-domain; questions: question clusters (all); questions_cue / questions_noise (marked not_attribute / unsure) /
    questions_column (not marked)."""
    marked = {c for c, a in actions.items() if a in ("not_attribute", "unsure", CUE) and c in clusters}
    out = Counter(mark_outcome_cue(*clusters[c], actions[c]) for c in marked)
    q = {c for c, (_, cl) in clusters.items() if S39.is_question_cluster(cl) and not S39.is_other_domain_cluster(cl)}
    cue = {c for c in marked if actions[c] == CUE}
    return {"marks_n": out["right"] + out["wrong"], "marks_right": out["right"], "wrong_entity_dropped": out["wrong_entity_dropped"],
            "cue_marks": len(cue), "cue_question": len(cue & q), "cue_other_domain": sum(S39.is_other_domain_cluster(clusters[c][1]) for c in cue),
            "questions": len(q), "questions_cue": len(q & cue), "questions_noise": len((q & marked) - cue),
            "questions_column": len(q - marked)}


# ---- tokens

def tokens_rows(responses, jobs, families):
    """[(family, calls, prompt tokens, output tokens, est. prompt tokens)] from the response rows {job: row} and manifest jobs
    (family, est_prompt_tokens), plus a total row ("total")."""
    fam = {j["job"]: j["family"] for j in jobs}
    est = Counter()
    for j in jobs:
        est[j["family"]] += j["est_prompt_tokens"]
    rows, tot = [], [0, 0, 0, 0]
    for f in families:
        rs = [r for k, r in responses.items() if fam.get(k) == f]
        v = [len(rs), sum(r["prompt_tokens"] for r in rs), sum(r["output_tokens"] for r in rs), est[f]]
        tot = [a + b for a, b in zip(tot, v)]
        rows.append((f, *v))
    rows.append(("total", *tot))
    return rows


# ---- decisions

def reconcile_decision(base, new):
    """(line, adopt?) for one set. base / new = dashboard rows (dicts) of A s012 and of the reconcile row: adopt on this set when
    the recall guard passes and review edits go down."""
    ok = new["guard"] == "pass" and int(new["review_edits"]) < int(base["review_edits"])
    return (f"{new['set']}: review edits {base['review_edits']} -> {new['review_edits']}, columns {base['columns']} -> {new['columns']} "
            f"(columns per found {base['columns_per_found']:.3f} -> {new['columns_per_found']:.3f}), found {base['found_total']} -> "
            f"{new['found_total']}, recall guard {new['guard']} ({new['guard_detail']}): {'pass' if ok else 'not met'}."), ok


def cue_decision(base, new):
    """(line, adopt?) for one set: adopt when the noise marks right (rules 1.3, counts) go up and the recall guard passes. base /
    new = dicts with marks13_right, marks13_n, guard."""
    ok = int(new["marks13_right"]) > int(base["marks13_right"]) and new["guard"] == "pass"
    return (f"{new['set']}: marks right {base['marks13_right']}/{base['marks13_n']} -> {new['marks13_right']}/{new['marks13_n']}, "
            f"recall guard {new['guard']}: {'pass' if ok else 'not met'}."), ok
