import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import read_grades_v4 as RG  # noqa: E402
from s1a import step4_grades as R  # noqa: E402
from s1a import step4_grading as P  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_sql as Q  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def canon():
    return G.to_canonical(G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml"))


def test_codes_distinct_and_seeded():
    c = P.make_codes(16, 0)
    assert len(set(c)) == 16 and all(len(x) == 4 and x.isalpha() and x.isupper() for x in c) and c == P.make_codes(16, 0) != P.make_codes(16, 1)


def test_strip_sql():
    assert P.strip_sql('-- hi\nCREATE TABLE "a" ( -- x\n  "b" TEXT /* c */\n);\n') == 'CREATE TABLE "a" (\n  "b" TEXT\n);\n'


def test_fill_prompt_uses_template_exactly():
    tpl = (ROOT / "config" / "wf_v4_grading_prompt.txt").read_text(encoding="utf-8")
    out = P.fill_prompt(tpl, "ABCD", "REF SQL", "CAND SQL")
    for ph in ("[ALTERNATIVES", "[Q1..Q8]", "[GT SQL]", "[CANDIDATE SQL]", "[CODE]"):
        assert ph not in out
    assert out.count("ABCD") == 2 and "REF SQL" in out and "CAND SQL" in out and "8. What is the address" in out
    with pytest.raises(ValueError):
        P.fill_prompt("no placeholders", "ABCD", "a", "b")


def test_plant_errors_deterministic_and_three(canon):
    c1, e1 = P.plant_errors(canon, 0, "dev50")
    c2, e2 = P.plant_errors(canon, 0, "dev50")
    assert c1 == c2 and e1 == e2 and [e["kind"] for e in e1] == ["merge", "fk_removed", "column_moved"]
    assert len(c1["tables"]) == len(canon["tables"]) - 1
    n_fk = sum(len(t["foreign_keys"]) for t in canon["tables"])
    assert sum(len(t["foreign_keys"]) for t in c1["tables"]) == n_fk - 1
    assert sum(len(t["columns"]) for t in c1["tables"]) == sum(len(t["columns"]) for t in canon["tables"])
    names = {t["name"] for t in c1["tables"]}
    assert all(f["ref_table"] in names for t in c1["tables"] for f in t["foreign_keys"])
    assert "CREATE TABLE" in Q.to_sql(c1) and canon["tables"][0]["columns"]  # original untouched


def test_assign_repeats_and_checklist():
    codes = P.assign([(s, k) for s in P.SETS for k in P.KINDS], 0)
    assert len(set(codes.values())) == 16
    rep = P.pick_repeats(codes, 0)
    assert all(len(v) == 3 for v in rep.values()) and not set(rep["claude"]) & set(rep["chatgpt"])
    rows = P.checklist(codes, rep)
    assert len(rows) == 38 and sum(r["repeat"] for r in rows) == 6 and len({r["file"] for r in rows}) == 38
    assert "candidate" not in P.readme(rows)


def ans(code, scores, reason="ok", q="yes"):
    d = {"code": code, "model": "fake-1", "answerability": [{"q": i, "answer": q, "reason": ""} for i in range(1, 9)]}
    d.update({k: {"score": s, "reason": reason} for k, s in zip(R.ITEMS, scores)})
    return d


def test_parse_answer():
    d = ans("ABCD", [5] * 6)
    assert R.parse_answer("```json\n" + json.dumps(d) + "\n```", "ABCD")["code"] == "ABCD"
    assert R.parse_answer("Here: " + json.dumps(d) + " thanks")["model"] == "fake-1"
    for bad in (dict(d, code="WXYZ"), dict(d, grouping={"score": 6, "reason": ""}), dict(d, answerability=d["answerability"][:7])):
        with pytest.raises(ValueError):
            R.parse_answer(json.dumps(bad), "ABCD")


def test_spearman():
    assert R.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert R.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert R.spearman([1, 2, 3, None], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert R.spearman([1, 1, 1], [1, 2, 3]) is None and R.spearman([1, 2], [1, 2]) is None


def test_planted_named():
    errs = [{"kind": "merge", "keywords": ["hotel", "restaurant"]}, {"kind": "fk_removed", "keywords": ["hotel confirmed name", "hotel_booking", "hotel"]},
            {"kind": "column_moved", "keywords": ["hotel type"]}]
    assert R.planted_named("Hotel and restaurant are merged; hotel_booking lacks its FK to hotel", errs) == [True, True, False]


def test_two_fake_answers_end_to_end(tmp_path):
    key = {"seed": 0, "packets": {"AAAA": {"set": "dev50", "candidate": "gt"}, "BBBB": {"set": "dev50", "candidate": "d"},
                                  "CCCC": {"set": "dev50", "candidate": "gt_planted"}},
           "planted": {"dev50": [{"kind": "merge", "keywords": ["hotel", "restaurant"]}, {"kind": "fk_removed", "keywords": ["fkcol", "tbl", "refx"]},
                                 {"kind": "column_moved", "keywords": ["hotel type"]}]}}
    (tmp_path / "answers").mkdir()
    (tmp_path / "key.json").write_text(json.dumps(key), encoding="utf-8")
    files = {"claude_AAAA": ans("AAAA", [5] * 6), "claude_AAAA_r2": ans("AAAA", [4, 5, 5, 5, 5, 5]), "chatgpt_AAAA": ans("AAAA", [5, 5, 4, 5, 3, 5]),
             "chatgpt_BBBB": ans("BBBB", [1] * 6, q="no"), "claude_BBBB": ans("BBBB", [2] * 6, q="no"),
             "claude_CCCC": ans("CCCC", [3] * 6, reason="hotel and restaurant merged, hotel type misplaced"), "chatgpt_CCCC": ans("CCCC", [3] * 6)}
    for n, d in files.items():
        (tmp_path / "answers" / f"{n}.json").write_text(json.dumps(d), encoding="utf-8")
    (tmp_path / "answers" / "notes.json").write_text("{}", encoding="utf-8")
    RG.main(["--dir", str(tmp_path), "--no-auto"])
    md = (tmp_path / "task11.md").read_text(encoding="utf-8")
    csv_text = (tmp_path / "grades.csv").read_text(encoding="utf-8")
    assert len(csv_text.strip().splitlines()) == 1 + 7 and "gt_planted" in csv_text
    rows, bad = RG.read_answers(tmp_path / "answers")
    assert len(rows) == 7 and len(bad) == 1
    res = R.analyse(rows, key)
    ag = res["agreement"]["chatgpt vs claude"]
    assert ag["grouping"]["n"] == 3 and ag["grouping"]["exact"] == pytest.approx(2 / 3) and ag["design_quality"]["within1"] == pytest.approx(2 / 3)
    assert ag["relationships"]["exact"] == pytest.approx(1 / 3) and ag["answerability"]["exact"] == 1.0
    assert res["self"]["claude"]["grouping"] == {"n": 1, "exact": 0.0, "within1": 1.0} and res["self"]["chatgpt"]["grouping"]["n"] == 0
    c = res["controls"]["claude"]["dev50"]
    assert c["gt_rank"] == 1 and c["d_rank"] == 3 and c["planted_rank"] == 2 and c["planted_between"] is True and c["planted_middle"] is False
    assert res["planted"]["claude"]["dev50"] == [True, False, True] and res["planted"]["chatgpt"]["dev50"] == [False, False, False]
    assert "Judge agreement" in md and "Controls" in md
