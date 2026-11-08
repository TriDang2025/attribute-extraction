import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import contamination_v41 as C  # noqa: E402
from s1a import step4_gt as G  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def gt():
    return G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml")


def as_answer(canon):
    """A canonical schema rendered as a dialogues-only (e) answer (the shape the probe asks for)."""
    return {"tables": [{"name": t["name"], "description": t["description"], "row": t["row"], "primary_key": t["primary_key"],
                        "columns": [{"name": c["name"], "type": c["type"]} for c in t["columns"]],
                        "foreign_keys": [{"column": f["columns"][0], "ref_table": f["ref_table"], "ref_column": f["ref_columns"][0]}
                                         for f in t["foreign_keys"]]} for t in canon["tables"]],
            "relationships": [{"from": r["from"], "to": r["to"], "kind": r["kind"], "reason": r["reason"]} for r in canon["relationships"]]}


def test_prompt_names_dataset_and_schema_matches_e():
    text, schema = C.build()
    assert "MultiWOZ" in text and "{" in text and "{types}" not in text
    assert schema == C.schema_from_prompt_e()


def test_gt_as_answer_scores_one(gt):
    ans = as_answer(G.to_canonical(gt))
    assert C.validate_e(ans) == []
    sc = C.score_answer(ans, gt)
    m = sc["result"]["metrics"]
    assert sc["unmatched"] == []
    assert sc["tables_named"]["share"] == 1.0 and sc["columns_named"]["share"] == 1.0
    assert m["grouping_f1"] == pytest.approx(1.0) and m["pk_right"]["share"] == 1.0 and m["rel_recall"]["share"] == 1.0


def test_empty_answer_scores_zero(gt):
    sc = C.score_answer({"tables": [], "relationships": []}, gt)
    assert sc["tables_named"]["k"] == 0 and sc["columns_named"]["k"] == 0
    assert not sc["result"]["metrics"]["grouping_f1"]  # None: no GT column placed
    assert "0/" in C.report_md(sc)


def test_real_multiwoz_spellings_map(gt):
    ans = {"tables": [
        {"name": "hotel", "description": "", "row": "", "primary_key": ["name"],
         "columns": [{"name": "name", "type": "text"}, {"name": "pricerange", "type": "text"}, {"name": "Stars", "type": "integer"},
                     {"name": "internet", "type": "boolean"}, {"name": "fax", "type": "text"}], "foreign_keys": []},
        {"name": "train", "description": "", "row": "", "primary_key": ["trainID"],
         "columns": [{"name": "trainID", "type": "id"}, {"name": "leaveAt", "type": "time"}, {"name": "arrive_by", "type": "time"}],
         "foreign_keys": []},
        {"name": "restaurant_booking", "description": "", "row": "", "primary_key": [],
         "columns": [{"name": "people", "type": "integer"}, {"name": "ref", "type": "id"}], "foreign_keys": []}],
        "relationships": []}
    canon, unmatched = C.map_to_gt(C.from_e(ans), gt)
    got = {t["name"]: {c["name"]: c["gt"] for c in t["columns"]} for t in canon["tables"]}
    assert got["hotel"] == {"name": "Hotel name", "pricerange": "Hotel price range", "Stars": "Hotel stars",
                            "internet": "Hotel internet", "fax": None}
    assert got["train"] == {"trainID": "Train trainid", "leaveAt": "Train leave at", "arrive_by": "Train arrive by"}
    assert got["restaurant_booking"] == {"people": "Restaurant requested people", "ref": "Restaurant confirmed reference"}
    assert unmatched == [("hotel", "fax")]
    assert all(c["gt"] is None for t in C.from_e(ans)["tables"] for c in t["columns"])  # the input is not changed


def test_cli_build_and_score(tmp_path, gt):
    import subprocess
    ans = tmp_path / "a.json"
    ans.write_text(json.dumps(as_answer(G.to_canonical(gt))), encoding="utf-8")
    out = tmp_path / "out"
    cmd = [sys.executable, "-I", str(ROOT / "scripts" / "contamination_v41.py"), "--out", str(out)]
    subprocess.run(cmd + ["--build", "--score", str(ans)], check=True, capture_output=True)
    assert (out / "prompts" / "contamination.txt").exists() and (out / "prompts" / "contamination.schema.json").exists()
    assert "columns_named_k" in (out / "scores.csv").read_text(encoding="utf-8")
    assert (out / "scores.md").exists()
