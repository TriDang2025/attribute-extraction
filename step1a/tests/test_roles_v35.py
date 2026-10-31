import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import roles_v35 as R  # noqa: E402

PAIRS = [("departure", "destination"), ("leave at", "arrive by")]


def mentions():
    rows = [  # cluster E1#0 holds both roles of a pair; E1#1 only one; E1#2 has none
        ("E1#0", "I want to leave from Cambridge please", "Cambridge", "from"),
        ("E1#0", "I want to go to London please", "London", "to"),
        ("E1#0", "Going to Cambridge", "Cambridge", "to"),
        ("E1#0", "Cambridge is the place", "Cambridge", ""),
        ("E1#1", "arrive at 10:30", "10:30", "at"),
        ("E1#1", "leave at 10:30", "10:30", "at"),
        ("E1#2", "TR1234 is the id", "TR1234", ""),
    ]
    return pd.DataFrame({"cluster_id": [r[0] for r in rows], "turn_text": [r[1] for r in rows],
                         "text": [r[2] for r in rows], "left_word": [r[3] for r in rows]})


L2 = pd.Series(["Train departure", "Train destination", "Train destination", "Train departure",
                "Train arriveby", "Train leave at", "Train trainid"])


def test_gold_role():
    s = pd.Series(["Train departure", "Taxi destination", "Train leaveat", "Hotel departure", "Train day", "",
                   "Train departure;Train day", "Train departure;Train destination", np.nan])
    assert list(R.gold_role(s, PAIRS)) == ["departure", "destination", "leave at", "", "", "", "departure", "", ""]


def test_two_role_clusters():
    m, g = mentions(), R.gold_role(L2, PAIRS)
    lab = L2 != ""
    assert R.two_role_clusters(m, g, lab, PAIRS) == {"E1#0": ("departure", "destination"),
                                                      "E1#1": ("leave at", "arrive by")}
    # a 20% share is needed: with 9 labelled mentions, 1 of 9 destination is below the threshold
    lab9 = lab.copy()
    extra = pd.DataFrame({"cluster_id": ["E1#0"] * 5, "turn_text": ["x"] * 5, "text": ["x"] * 5, "left_word": [""] * 5})
    m2 = pd.concat([m, extra], ignore_index=True)
    g2 = pd.concat([g, pd.Series([""] * 5)], ignore_index=True)
    l2 = pd.concat([lab9, pd.Series([True] * 5)], ignore_index=True)
    g2.loc[[1, 2]] = ["destination", ""]   # 1 destination of 8 labelled
    assert "E1#0" not in R.two_role_clusters(m2, g2, l2, PAIRS)


def test_j_side_looks_back_three_words():
    m = mentions()
    assert [R.j_side(r) for _, r in m.iterrows()] == [0, 1, 1, None, 1, 0, None]   # "arrive at": "at" is no cue, "arrive" two words back


def test_j_uses_local_start_for_repeated_value():
    r = pd.Series({"turn_text": "to Cambridge from Cambridge", "text": "Cambridge", "left_word": "from",
                   "local_start": 18})
    assert R.j_side(r) == 0
    r["local_start"] = 3
    assert R.j_side(r) == 1


def test_role_word_eval():
    m, g = mentions(), R.gold_role(L2, PAIRS)
    ev = R.role_word_eval(m, g, PAIRS).set_index("cluster_id")
    assert list(R.role_word_eval(m, g, PAIRS).columns) == R.EVAL_COLS
    a = ev.loc["E1#0"]   # gold roles on rows 0-3, J: 0 (ok), 1 (ok), 1 (ok), none
    assert (a["n"], a["n_gold_role"], a["covered"], a["correct"]) == (4, 4, 3, 3)
    assert a["accuracy"] == 1.0 and a["coverage"] == 0.75
    b = ev.loc["E1#1"]   # row 4 gold arrive by: J end; row 5 gold leave at: J start
    assert (b["covered"], b["correct"]) == (2, 2)
    assert "E1#2" not in ev.index


def test_masked_texts():
    t = R.masked_texts(mentions().iloc[:2])
    assert t == ["I want to leave from [V] please", "I want to go to [V] please"]


def toy_vectors(m):
    # E1#0: two well-separated context groups (departure vs destination); E1#1 stays as one blob
    v = np.zeros((len(m), 4), dtype=np.float32)
    v[0], v[3] = [1, 0, 0, 0], [0.98, 0.05, 0, 0]
    v[1], v[2] = [0, 1, 0, 0], [0.05, 0.98, 0, 0]
    v[4], v[5] = [0, 0, 1, 0], [0, 0, 0.99, 0.01]
    v[6] = [0, 0, 0, 1]
    return v


def test_context_split():
    m, g = mentions(), R.gold_role(L2, PAIRS)
    out = R.context_split(m, toy_vectors(m), g, thr=0.25, pairs=PAIRS).set_index("cluster_id")
    a = out.loc["E1#0"]
    assert bool(a["split"]) and a["silhouette"] > 0.9
    assert a["accuracy"] == 1.0 and a["coverage"] == 1.0 and a["acc_nosplit"] == 0.5   # 2 of 4 match the majority role
    b = out.loc["E1#1"]   # only 2 rows: never split, majority tie
    assert not bool(b["split"]) and np.isnan(b["silhouette"])
    # threshold above the silhouette keeps the cluster whole
    hi = R.context_split(m, toy_vectors(m), g, thr=0.999, pairs=PAIRS).set_index("cluster_id")
    assert not bool(hi.loc["E1#0", "split"]) and hi.loc["E1#0", "accuracy"] == 0.5


def test_context_split_nosplit_compares_sides():
    # departure x2 + leave at x1 are all start-side: never split, both accuracies are side based and equal
    m = pd.DataFrame({"cluster_id": ["c"] * 3, "turn_text": ["a"] * 3, "text": ["a"] * 3, "left_word": [""] * 3})
    g = pd.Series(["departure", "departure", "leave at"], index=m.index)
    out = R.context_split(m, np.zeros((3, 4)), g, pairs=PAIRS).iloc[0]
    assert out["acc_nosplit"] == 1.0 and out["accuracy"] == 1.0


def test_context_split_checks_vector_rows():
    m, g = mentions(), R.gold_role(L2, PAIRS)
    try:
        R.context_split(m, np.zeros((2, 4)), g, pairs=PAIRS)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_pooled():
    ev = pd.DataFrame({"cluster_id": ["a", "b"], "n_gold_role": [4, 2], "covered": [3, 1], "correct": [3, 0]})
    p = R.pooled(ev)
    assert p["accuracy"] == 0.75 and p["coverage"] == 4 / 6 and p["clusters"] == 2
    assert R.pooled(ev, ["a"])["correct"] == 3


# ---- T27

def dec(*rows):
    return pd.DataFrame([{"cluster_id": c, "name": n, "action": a, "merge_with": json.dumps(w), "split": ""}
                         for c, n, a, w in rows],
                        columns=["cluster_id", "name", "action", "merge_with", "split"])


def toy_ed():
    men = pd.DataFrame({
        "cluster_id": ["E1#0", "E1#1", "E1#2", "E1#2", "E1#3", "E1#4", "E1#5"],
        "mention_id": [0, 1, 2, 3, 4, 5, 6],
        "gold_attr": ["Train departure", "Train destination", "Train day", "Train arrive by", "", "Train day", "Train day"]})
    # E1#0 / E1#1: grouped together in s1 (role pair); E1#2: mixed; E1#3: noise in s0 only; E1#5 name wording only
    s0 = dec(("E1#0", "departure", "keep", []), ("E1#1", "destination", "keep", []), ("E1#2", "x", "keep", []),
             ("E1#3", "yes", "not_attribute", []), ("E1#4", "day", "keep", []), ("E1#5", "day", "keep", []))
    s1 = dec(("E1#0", "place", "merge", ["E1#1"]), ("E1#1", "place", "merge", ["E1#0"]), ("E1#2", "x", "merge", ["E1#4"]),
             ("E1#3", "yes", "keep", []), ("E1#4", "day", "merge", ["E1#2"]), ("E1#5", "travel day", "keep", []))
    s2 = s0.copy()
    return SimpleNamespace(ent="train", gold_ents=["train"], mentions=men,
                           seed_decs={"C s0": s0, "C s1": s1, "C s2": s2})


def test_train_instability_reasons():
    out = R.train_instability(toy_ed(), pairs=PAIRS).set_index("cluster_id")
    assert out.loc["E1#0", "reason"] == "role_pair" and out.loc["E1#1", "reason"] == "role_pair"
    assert out.loc["E1#3", "reason"] == "noise_flip"
    assert out.loc["E1#2", "reason"] == "mixed_cluster"
    assert out.loc["E1#4", "reason"] == "other"
    assert out.loc["E1#5", "reason"] == "name_wording"
    assert len(out) == 6
