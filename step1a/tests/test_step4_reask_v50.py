from s1a import step4_reask_v49 as RA
from s1a import step4_reask_v50 as RA2
from s1a import step4_v43 as V

COLS = [{"id": "hotel:1"}, {"id": "hotel:2"}]
CHAIN = {"id": "c", "p2_batch": 20}
TABLES, VALID = ["hotel"], {"hotel", "train"}


def _answers(monkeypatch, answers):
    monkeypatch.setattr(V, "_answer", lambda out, job: (answers[job], None) if job in answers else (None, "no response"))


def test_r2_used_when_r1_still_drops(monkeypatch):
    drop = {"hotel:1": V.UNUSED, "hotel:2": V.UNUSED}
    good = {"hotel:1": "hotel", "hotel:2": "hotel"}
    _answers(monkeypatch, {"c_p2_b0": drop, "c_p2_b0_r1": dict(drop), "c_p2_b0_r2": good})
    assert RA2.answer("out", CHAIN, COLS, TABLES, VALID) == (good, None)
    assert RA2.to_reask("out", CHAIN, COLS, TABLES, VALID) == [0]
    assert RA.answer("out", CHAIN, COLS, TABLES, VALID) == (drop, None)        # v4.9 behaviour unchanged


def test_no_r2_when_r1_fixes_or_is_missing(monkeypatch):
    drop = {"hotel:1": V.UNUSED, "hotel:2": V.UNUSED}
    good = {"hotel:1": "hotel", "hotel:2": "hotel"}
    _answers(monkeypatch, {"c_p2_b0": drop, "c_p2_b0_r1": good, "c_p2_b0_r2": drop})
    assert RA2.answer("out", CHAIN, COLS, TABLES, VALID) == (good, None)
    assert RA2.to_reask("out", CHAIN, COLS, TABLES, VALID) == []
    _answers(monkeypatch, {"c_p2_b0": drop, "c_p2_b0_r2": good})             # r1 missing: first kept, no round 2
    assert RA2.answer("out", CHAIN, COLS, TABLES, VALID) == (drop, None)


def test_r2_prompt_differs_from_r1():
    text = "prompt body\n" + RA._TAIL
    assert RA2.with_note(text) != RA.with_note(text) and RA2.with_note(text).endswith(RA._TAIL)
