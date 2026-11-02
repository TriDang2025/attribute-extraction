import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import roles_v35 as R  # noqa: E402
from s1a import roles_v37 as R37  # noqa: E402

LT = R.left_tokens


def lefts(*texts):
    return [LT(t) for t in texts]


def test_left_tokens_and_side_word():
    assert LT("a b c d e") == ["c", "d", "e"]
    assert LT("I want to leave, from") == ["to", "leave", "from"]
    assert R.side_word(LT("a train from the")) == (0, "from")
    assert R.side_word(LT("going to")) == (1, "to")
    assert R.side_word(LT("nothing here")) == (None, None)
    assert R.side_word(["leave"], {"start": {"leave"}, "end": set()}) == (0, "leave")


def test_j_word_unchanged_by_refactor():
    row = {"turn_text": "I want to leave from Cambridge please", "text": "Cambridge", "left_word": "from"}
    assert R.j_word(row) == (0, "from")
    assert R.j_word({**row, "turn_text": "no value here"}) == (0, "from")   # falls back to left_word
    assert R.j_word({**row, "turn_text": "see you at Cambridge", "left_word": "at"}) == (None, None)


def test_learn_words_maps_by_general_evidence():
    # "via" (just before 3 of 10 mentions) follows the start word "from" -> start; "at" has no evidence -> not mapped;
    # "the" is under 20% of the cluster, so it is not a candidate
    ls = lefts("from london via", "from leeds via", "from york via", "to cambridge", "to ely", "to bath",
               "go to the", "go at", "at", "okay at")
    words, rows = R37.learn_words(ls)
    by = {r["word"]: r for r in rows}
    assert "via" in words["start"] and by["via"]["side"] == 0 and by["via"]["ev_start"] == 3
    assert "at" not in words["start"] | words["end"] and by["at"]["side"] is None
    assert "the" not in by
    assert not (words["start"] | words["end"]) & {"from", "to"}   # general words are not learned


def test_learn_words_needs_both_parts():
    words, rows = R37.learn_words(lefts("x via", "y via", "z via"))      # the word covers 100%
    assert rows == [] and words == {"start": set(), "end": set()}


def test_split_parts_and_unknown_part():
    assert R37.split_parts([0, 0, 1, 1, None]) == [0, 0, 1, 1, R37.UNKNOWN]
    assert R37.split_parts([0, 0, 0, 0, 1]) == [0, 0, 0, 0, 1]   # 1/5 = 20%: enough
    assert R37.split_parts([0, 0, 0, 0, 0, 1]) is None           # 1/6: not
    assert R37.split_parts([0, 1]) == [0, 1]
    assert R37.split_parts([]) is None


def test_split_labels_only_two_role_clusters():
    ls = lefts("from a", "from b", "to c", "to d", "at 5", "okay", "at 7", "at 9")
    labels = ["x", "x", "x", "x", "y", "y", "y", "y"]
    out, stats = R37.split_labels(labels, [0] * 8, ls)
    assert out[:4] == [("x", 0), ("x", 0), ("x", 1), ("x", 1)] and out[4:] == ["y"] * 4
    assert len(stats) == 1 and stats[0]["start"] == 2 and stats[0]["end"] == 2 and stats[0]["unknown"] == 0
    # a mention with no cue word gets its own part, never a side
    out2, st2 = R37.split_labels(["x"] * 5, [0] * 5, lefts("from a", "from b", "to c", "to d", "on e"))
    assert out2[4] == ("x", R37.UNKNOWN) and st2[0]["unknown"] == 1
    # the same label in two stage-1 groups is two clusters
    out3, _ = R37.split_labels(["x", "x"], [0, 1], lefts("from a", "to b"))
    assert out3 == ["x", "x"]


def test_split_with_learned_word():
    # "via" follows "from" often enough to be learned as a start word; without that evidence it is not used
    ls2 = lefts("a via", "b via", "to c", "to d", "to e")
    assert R37.split_labels(["x"] * 5, [0] * 5, ls2)[0] == ["x"] * 5
    ls3 = lefts("from a", "from b via", "from c via", "to d", "to e")
    out, st = R37.split_labels(["x"] * 5, [0] * 5, ls3)
    assert st[0]["learned"] == ["via"] and out[0] == ("x", 0) and out[3] == ("x", 1)


def test_learned_eval_scores_with_gold_only_for_scoring():
    rows = [("c", "go from a via", "a", "via", "departure"), ("c", "from b via", "b", "via", "departure"),
            ("c", "to c", "c", "to", "destination"), ("c", "to d", "d", "to", "destination"),
            ("c", "see e", "e", "see", "destination")]
    m = pd.DataFrame({"cluster_id": [r[0] for r in rows], "turn_text": [r[1] for r in rows],
                      "text": [r[2] for r in rows], "left_word": [r[3] for r in rows]})
    gold = pd.Series([r[4] for r in rows])
    pairs = [("departure", "destination")]
    ev_a, w_a = R37.learned_eval(m, gold, pairs, learn=False)
    ev_b, w_b = R37.learned_eval(m, gold, pairs, learn=True)
    assert w_a.empty
    assert int(ev_a["covered"].sum()) == int(ev_b["covered"].sum()) == 4
    assert list(ev_a["correct"]) == [4]
    assert set(w_b.columns) == set(R37.WORD_COLS)
