"""wf_v3.9 Phase 1: role-pure columns and the noise rules 2a / 2b on tiny fake data (RULES_V1_3.md)."""

from collections import Counter

from s1a import score_v39 as S

ENTS = ["train"]


def test_role_counts_only_role_slots():
    c = S.role_counts(["train departure", "train destination;train day", "train day", ""], ENTS)
    assert c == Counter({"departure": 1, "destination": 1})


def test_role_pure_threshold_80():
    assert S.is_role_pure(Counter({"departure": 4, "destination": 1})) is True      # exactly 0.8
    assert S.is_role_pure(Counter({"departure": 7, "destination": 3})) is False     # 0.7
    assert S.is_role_pure(Counter({"departure": 3, "leave at": 1})) is False        # 0.75, place and time are two roles


def test_column_without_role_mentions_left_out():
    assert S.is_role_pure(Counter()) is None


def test_question_and_other_domain_cluster_60():
    assert S.is_question_cluster(["request"] * 3 + ["x"] * 2)
    assert S.is_question_cluster(["cue", "request", "a", "b", "c"]) is False
    assert S.is_other_domain_cluster(["wrong_entity"] * 3 + ["other_entity:Hotel"] * 0 + ["a"] * 2)
    assert S.is_other_domain_cluster(["other_entity:Hotel", "wrong_entity", "a"])
    assert S.is_other_domain_cluster(["other_entity:Hotel", "a", "b"]) is False


def test_rule_2a_question_marked_noise():
    q = ["request"] * 4 + ["a"]
    assert S.mark_outcome("mixed", q, has_cue=False) == "right"
    assert S.mark_outcome("mixed", q, has_cue=True) == "wrong"      # scored as before
    assert S.mark_outcome("noise", q, has_cue=True) == "right"      # label noise stays right


def test_rule_2b_other_domain_dropped():
    od = ["wrong_entity"] * 4 + ["a"]
    assert S.mark_outcome("real", od, has_cue=False) == "wrong_entity_dropped"
    assert S.mark_outcome("noise", od, has_cue=False) == "wrong_entity_dropped"


def test_marks_v13_counts():
    clusters = {"c1": ("noise", ["noise"] * 3), "c2": ("mixed", ["request"] * 3), "c3": ("real", ["wrong_entity"] * 3),
                "c4": ("mixed", ["a", "b", "noise"]), "c5": ("real", ["a"])}
    got = S.marks_v13(clusters, {"c1", "c2", "c3", "c4", "zz"}, has_cue=False)
    assert got == {"marks_n": 3, "marks_right": 2, "wrong_entity_dropped": 1}
