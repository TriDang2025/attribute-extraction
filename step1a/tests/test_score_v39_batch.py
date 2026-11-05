import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import score_v39_batch as SB  # noqa: E402


def resp(same_as, errors=()):
    return {"parsed": {"unit_id": "p", "reason": "r", "same_as": same_as}, "errors": list(errors)}


def test_choices_agreement_and_intersection():
    cands = [{"cid": 2, "name": "city"}, {"cid": 3, "name": "time"}]
    jobs = [{"job": f"j{i}", "pid": f"P{i}", "candidates": cands} for i in range(4)]
    rows = {"j0": resp("city"), "j1": resp("none"), "j2": resp("time", ["bad"]), "j3": None}
    a = SB.choices_of(jobs, rows)
    assert a == {"P0": 2, "P1": None, "P2": None, "P3": None}      # errors and a missing response keep the part
    b = {"P0": 2, "P1": None, "P2": 3, "P3": None}
    assert SB.agreement(a, b) == (3, 4)
    assert SB.intersect(a, b) == {"P0": 2, "P1": None, "P2": None, "P3": None}
    assert SB.intersect({"P0": 2}, {"P0": 3}) == {"P0": None}


def test_clean_joins_drops_single_column_joins_and_repeated_ids():
    joins = [{"columns": [1, 4], "reason": "a"}, {"columns": [12], "reason": "no twin"}, {"columns": [5, 5], "reason": "x"},
             {"columns": [2, 3, 2], "reason": "y"}]
    kept, dropped = SB.clean_joins(joins)
    assert [j["columns"] for j in kept] == [[1, 4], [2, 3]] and [j["columns"] for j in dropped] == [[12], [5, 5]]


def test_final_names_renames_joined_groups_to_the_biggest_member():
    cols = [{"cid": 1, "name": "a", "groups": ["g1"], "n_mentions": 2}, {"cid": 2, "name": "b", "groups": ["g2", "g3"], "n_mentions": 5},
            {"cid": 3, "name": "c", "groups": ["g4"], "n_mentions": 1}]
    assert SB.final_names(cols) == {"g1": "a", "g2": "b", "g3": "b", "g4": "c"}
    assert SB.final_names(cols, [{"columns": [1, 2]}]) == {"g1": "b", "g2": "b", "g3": "b", "g4": "c"}


def clusters():
    q = ("unknown", ["request"] * 3 + ["noise"])                 # a question cluster (75% request)
    return {"C0": ("noise", ["noise"] * 4), "C1": q, "C2": ("real", ["wrong_entity"] * 4), "C3": ("real", ["departure"] * 4),
            "C4": q}


def test_cue_stats_question_cluster_is_right_only_when_marked_cue():
    acts = {"C0": "not_attribute", "C1": "attribute_cue", "C2": "not_attribute", "C3": "attribute_cue", "C4": "not_attribute"}
    r = SB.cue_stats(clusters(), acts)
    # C0 noise right; C1 question + cue right; C2 other domain dropped; C3 cue on a real cluster wrong; C4 question marked noise wrong
    assert (r["marks_right"], r["marks_n"], r["wrong_entity_dropped"]) == (2, 4, 1)
    assert (r["cue_marks"], r["cue_question"], r["questions"], r["questions_cue"], r["questions_noise"], r["questions_column"]) == (2, 1, 2, 1, 1, 0)
    r2 = SB.cue_stats(clusters(), {"C1": "keep", "C4": "unsure"})
    assert r2["questions_column"] == 1 and r2["questions_noise"] == 1 and r2["cue_marks"] == 0


def test_tokens_rows_total_and_estimates():
    jobs = [{"job": "a", "family": "f1", "est_prompt_tokens": 10}, {"job": "b", "family": "f2", "est_prompt_tokens": 20}]
    rows = SB.tokens_rows({"a": {"prompt_tokens": 12, "output_tokens": 3}, "b": {"prompt_tokens": 18, "output_tokens": 4}}, jobs, ("f1", "f2"))
    assert rows == [("f1", 1, 12, 3, 10), ("f2", 1, 18, 4, 20), ("total", 2, 30, 7, 30)]


def test_decisions():
    base = {"review_edits": 30, "columns": 60, "columns_per_found": 1.7, "found_total": 30}
    new = {"set": "s", "review_edits": 25, "columns": 55, "columns_per_found": 1.5, "found_total": 30, "guard": "pass", "guard_detail": "x"}
    assert SB.reconcile_decision(base, new)[1]
    assert not SB.reconcile_decision(base, {**new, "guard": "FAIL"})[1]
    assert not SB.reconcile_decision(base, {**new, "review_edits": 30})[1]
    cb, cn = {"marks13_right": 8, "marks13_n": 11}, {"set": "s", "marks13_right": 10, "marks13_n": 13, "guard": "pass"}
    assert SB.cue_decision(cb, cn)[1] and not SB.cue_decision(cb, {**cn, "marks13_right": 8})[1]
