import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import delex as D  # noqa: E402

M = pd.DataFrame(dict(norm_value=["cambridge", "stansted airport", "tr1234", "monday", "alexander bed and breakfast",
                                  "ab", "stansted"],
                      gold_attr=["Train departure", "Train destination", "Train confirmed reference", "Train day",
                                 "Hotel name", "Train departure", "Taxi departure;Taxi leave at"]))


def test_map_names_only_deterministic_unique():
    mp = D.build_map(M)
    assert set(mp) == {"cambridge", "stansted airport", "alexander bed and breakfast", "stansted"}  # "ab" too short
    assert mp == D.build_map(M.iloc[::-1])
    assert len(set(mp.values())) == len(mp) and not set(mp) & set(mp.values())
    assert all(len(k) == len(v) and k != v for k, v in mp.items())
    assert len(mp["stansted airport"].split()) == 2


def test_apply_whole_word_case_and_longest_first():
    mp = D.build_map(M)
    out = D.apply("Go to Stansted Airport or stansted, not Cambridge's. CAMBRIDGE; cambridgeshire.", mp)
    assert "Stansted" not in out and "cambridge" not in out.lower().replace("cambridgeshire", "")
    assert out.count(mp["stansted airport"].title()) == 1          # longest key first, case per word
    assert mp["stansted"] in out and "cambridgeshire" in out        # whole word only
    assert mp["cambridge"].upper() in out and mp["cambridge"].capitalize() + "'s" in out
    assert D.apply("nothing here", mp) == "nothing here" and D.apply("x", {}) == "x"


def test_reversible():
    mp = D.build_map(M)
    inv = {v: k for k, v in mp.items()}
    text = "from cambridge to stansted airport"
    assert D.apply(D.apply(text, mp), inv) == text


def test_tr_ids():
    mp = D.add_tr_ids({}, "The TR9999 and tr1234 and TR12345 and TRAIN")
    assert set(mp) == {"tr9999", "tr1234"}
    assert all(re.fullmatch(r"tx\d{4}", v) for v in mp.values()) and len(set(mp.values())) == 2
    assert D.add_tr_ids(mp, "TR9999") == mp
    out = D.apply("Take TR9999 now, TR12345 stays.", mp)
    assert re.search(r"TX\d{4} now", out) and "TR12345" in out
    assert D.build_map(M, texts=["see TR4321"])["tr4321"].startswith("tx")
