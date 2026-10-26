import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import roleword as R  # noqa: E402
from chk.data import make_doc  # noqa: E402


@dataclass
class Sp:
    doc_id: str
    text: str
    start: int
    end: int
    turn: int = -1


def _doc(*turns):
    return make_doc("D1", [{"id": "D1", "turns": list(turns), "domains": ["train"] * len(turns)}])


def _sp(doc, value, nth=0):
    s = -1
    for _ in range(nth + 1):
        s = doc.text.index(value, s + 1)
    return Sp("D1", value, s, s + len(value))


def test_from_to_with_other_value_masked():
    doc = _doc("User: I leave from Cambridge to London.")
    sps = [_sp(doc, "Cambridge"), _sp(doc, "London")]
    assert R.role_text(doc, sps[0], mentions_in_doc=sps) == "from cambridge"
    assert R.role_text(doc, sps[1], mentions_in_doc=sps) == "to london"
    assert R.role_text(doc, sps[1], left=2, mentions_in_doc=sps) == "to london"  # wall at Cambridge
    assert R.role_text(doc, sps[1], left=2) == "cambridge to london"  # no other spans known


def test_right_word_and_filler():
    doc = _doc("User: Please book for 3 people, thanks.")
    sp = _sp(doc, "3")
    assert R.role_text(doc, sp, left=1, right=1) == "for 3 people"
    assert R.role_text(doc, sp, left=0, right=1) == "3 people"
    assert R.role_text(doc, sp, left=0, right=0) == "3"


def test_filler_skipped_prepositions_kept():
    doc = _doc("User: I want to leave at the 20:30 please")
    sp = _sp(doc, "20:30")
    assert R.role_text(doc, sp, left=1) == "at 20:30"
    assert R.role_text(doc, sp, left=2) == "leave at 20:30"
    assert R.role_text(doc, sp, left=1, right=1) == "at 20:30"  # "please" skipped, nothing left


def test_speaker_prefix_excluded_and_turn_bound():
    doc = _doc("System: Which day?", "User: Cambridge please.")
    sp = _sp(doc, "Cambridge")
    assert R.role_text(doc, sp, left=3) == "cambridge"  # no "user" / previous turn
    doc2 = _doc("User: Cambridge to London.")
    assert R.role_text(doc2, _sp(doc2, "Cambridge"), left=2) == "cambridge"


def test_codes_are_shaped():
    doc = _doc("User: my train is TR1234 now")
    assert R.role_text(doc, _sp(doc, "TR1234"), left=0) == "train id tr####"
    doc = _doc("User: the reference is 8A2BC3D1")
    assert R.role_text(doc, _sp(doc, "8A2BC3D1"), left=1) == "is reference code xxxxxxxx"


def test_configs():
    assert len(R.CONFIGS) == 12
    assert "H_l1r0_t04" in R.CONFIGS and "H_l1r0_t035" in R.CONFIGS and "H_l0r1_t045" in R.CONFIGS
