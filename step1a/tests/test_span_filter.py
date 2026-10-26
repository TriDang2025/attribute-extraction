from s1a import span_filter as F
from s1a.units import Unit
from s1a.variants import Variant


def sp(text, score=0.9):
    u = Unit("span", "d", "", text, 0, len(text), 0)
    u.score = score
    return u


def texts(us):
    return [u.text for u in us]


def test_normalize():
    assert F.normalize("The Postcode.") == "postcode"
    assert F.normalize("  an  Entrance   Fee! ") == "entrance fee"


def test_drop_stop_whole_text_only():
    spans = [sp("I"), sp("Bye!"), sp("the cambridge belfry"), sp("5 star hotel"), sp("that")]
    assert texts(F.drop_stop(spans)) == ["the cambridge belfry", "5 star hotel"]


def test_drop_slot_names_whole_text_only():
    spans = [sp("the postcode"), sp("Reference Number"), sp("phone number 01223"), sp("area"), sp("north")]
    assert texts(F.drop_slot_names(spans)) == ["phone number 01223", "north"]


def test_custom_lists():
    assert texts(F.drop_stop([sp("foo"), sp("i")], words={"foo"})) == ["i"]


def test_min_score_and_missing_score():
    a, b = sp("x", 0.5), sp("y", 0.6)
    c = Unit("span", "d", "", "z")
    assert F.min_score([a, b, c], 0.6) == [b, c]


def test_compose():
    spans = [sp("you"), sp("price"), sp("cheap", 0.4), sp("cheap", 0.8)]
    out = F.CONFIGS["A_stop_slots_s06"].span_filter(spans)
    assert [(u.text, u.score) for u in out] == [("cheap", 0.8)]


def test_configs():
    assert set(F.CONFIGS) == {"A_stop", "A_slots", "A_stop_slots", "A_stop_slots_s06", "A_s06"}
    for v in F.CONFIGS.values():
        assert isinstance(v, Variant) and callable(v.span_filter) and v.cluster_fn is None


def test_list_sizes():
    assert len(F.STOP) <= 60 and len(F.SLOT_NAMES) <= 60
