import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import gold as G  # noqa: E402
from chk.data import make_doc  # noqa: E402

LEVELS = {1: {"Hotel parking", "Hotel internet", "Taxi destination"}, 2: {"Train destination"}, 3: set()}
TABLE = {"headers": ["Hotel name", "Hotel confirmed name", "Train destination", "Hotel requested day",
                     "Train day", "Hotel parking", "Hotel internet", "Taxi destination", "Attraction name"],
         "rows": [[["acorn guest house"], ["Acorn Guest House"], ["cambridge"], ["monday"], ["monday"],
                   ["yes"], ["Yes"], ["guest house"], ["museum"]]]}


def doc():
    dlg = {"id": "D1",
           "turns": ["User: I want a hotel with parking in cambridge.",
                     "System: The Acorn Guest House is in cambridge, yes.",
                     "User: Book Acorn Guest House for monday.",
                     "User: Also a train to cambridge on monday."],
           "domains": ["hotel", "hotel", "hotel", "train"]}
    return make_doc("D1", [dlg])


def classes(merge=True):
    return {"Hotel confirmed name": "Hotel name"} if merge else {}


def ms(merge=True):
    return G.mentions(doc(), TABLE, LEVELS, classes(merge))


def test_multiple_hits_and_turn_label():
    verb = [m for m in ms() if m.verbatim]
    cam = [m for m in verb if m.value == "cambridge"]
    assert [m.turn for m in cam] == [0, 1, 3]
    mon = [m for m in verb if m.value == "monday"]
    assert [set(m.raw_labels) for m in mon] == [{"Hotel requested day"}, {"Train day"}]
    assert all(m.kind == "mention" and doc().text[m.start:m.end].lower() == m.value for m in verb)


def test_ambiguous_fallback():
    cam = [m for m in ms() if m.value == "cambridge"]
    assert [m.ambiguous for m in cam] == [True, True, False]
    assert all(m.labels == {"Train destination"} for m in cam)
    assert cam[0].hidden == {1: False, 2: True, 3: False}


def test_same_value_two_attributes_one_mention():
    raw = [m for m in ms(False) if m.value == "acorn guest house"]
    assert len(raw) == 2 and raw[0].labels == {"Hotel name", "Hotel confirmed name"}
    assert raw[0].label == "Hotel confirmed name|Hotel name"
    merged = [m for m in ms() if m.value == "acorn guest house"]
    assert merged[0].labels == {"Hotel name"} and merged[0].raw_labels == raw[0].raw_labels


def test_contained_hit_dropped_and_non_verbatim():
    out = ms()
    nv = {m.value: m for m in out if not m.verbatim}
    assert set(nv) == {"guest house", "yes", "museum"}
    assert nv["yes"].labels == {"Hotel parking", "Hotel internet"}
    assert nv["yes"].start == nv["yes"].end == nv["yes"].turn == -1
    assert nv["yes"].hidden[1] and not nv["museum"].hidden[1]
    assert len(out) == 3 + 2 + 2 + 3


def test_merge_classes_toy():
    tables = [
        {"headers": ["Hotel name", "Hotel confirmed name", "Restaurant requested time", "Taxi arrive by",
                     "Hotel parking", "Hotel internet"],
         "rows": [[["a"], ["A"], ["12:00"], ["12:00"], ["yes"], ["yes"]]]},
        {"headers": ["Hotel name", "Hotel confirmed name"], "rows": [[["b"], ["b"]]]},
        {"headers": ["Hotel name", "Hotel confirmed name"], "rows": [[["c"], ["d"]]]},
    ]
    c = G.merge_classes(tables)
    assert c["Hotel confirmed name"] == "Hotel name" and c["Hotel name"] == "Hotel name"
    assert c["Taxi arrive by"] == "Taxi arrive by" and c["Hotel parking"] == "Hotel parking"
    assert G.merge_classes(tables, threshold=0.7)["Hotel confirmed name"] == "Hotel confirmed name"


def test_merge_classes_real():
    tables = G.load_all_tables()
    assert len(tables) == 1000
    c = G.merge_classes(tables)
    assert len(c) == 35 and len(set(c.values())) == 33
    assert {a: b for a, b in c.items() if a != b} == {"Restaurant confirmed name": "Restaurant name",
                                                      "Hotel confirmed name": "Hotel name"}
    lv = G.load_levels()
    assert [len(lv[k]) for k in (1, 2, 3)] == [7, 12, 17]


def test_mentions_for():
    out = G.mentions_for({"D1": doc()}, {"D1": TABLE}, LEVELS, classes())
    assert len(out) == len(ms())
