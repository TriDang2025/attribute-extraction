"""wf_v4 4.4 repairs v2 (batch_v4.repair_44) and the narrowed 4.4 check (new columns per table, relationships without a foreign key
only in strict mode)."""
import copy

from s1a import batch_v4 as B
from s1a import step4_prompts as sp
from s1a import step4_sql as ss
from tests.test_step4_prompts import A41, A42, A43, A44, COLS


def test_valid_answer_needs_no_repair():
    fixed, kinds = B.repair_44(copy.deepcopy(A44), A41, A42, A43, COLS)
    assert sum(kinds.values()) == 0 and fixed["tables"] == A44["tables"]


def test_new_key_also_listed_is_dropped_and_refs_renamed():
    a = copy.deepcopy(A44)
    a["tables"][0]["columns"].insert(0, {"column": "new:tid", "name": "train id", "type": "id"})
    a["tables"][2]["foreign_keys"][0]["ref_column"] = "new:tid"
    assert any("also a column name" in e for e in sp.validate_44(a, A41, A42, A43, COLS))
    fixed, kinds = B.repair_44(a, A41, A42, A43, COLS)
    assert kinds["key_listed"] == 1
    assert fixed["tables"][2]["foreign_keys"][0]["ref_column"] == "new:train id"
    assert sp.validate_44(fixed, A41, A42, A43, COLS) == []


def test_same_new_name_in_two_tables_is_not_an_error():
    a = copy.deepcopy(A44)
    a["tables"][1]["columns"].append({"column": "new:train id", "name": "train id", "type": "id"})
    assert not any("in two tables" in e for e in sp.validate_44(a, A41, A42, A43, COLS))


def test_missing_column_put_back_and_fk_fixed():
    a = copy.deepcopy(A44)
    del a["tables"][1]["columns"][1]                                  # hotel:2 left out
    a["tables"][2]["foreign_keys"][1]["ref_column"] = "new:ghost"      # unknown column of hotel -> its primary key
    a["tables"][2]["foreign_keys"].append({"column": "new:extra", "ref_table": "train", "ref_column": "new:train id"})
    fixed, kinds = B.repair_44(a, A41, A42, A43, COLS)
    assert kinds["col_missing"] == 1 and kinds["fk_ref_to_pk"] == 1 and kinds["fk_col_added"] == 1
    hotel = next(t for t in fixed["tables"] if t["name"] == "hotel")
    assert {"column": "hotel:2", "name": "stars", "type": "integer"} in hotel["columns"]
    assert fixed["tables"][2]["foreign_keys"][1]["ref_column"] == "hotel:1"
    assert sp.validate_44(fixed, A41, A42, A43, COLS) == []
    assert ss.to_sql(ss.assemble(A41, A42, A43, fixed))


def test_relationship_without_fk_only_strict():
    a = copy.deepcopy(A44)
    a["tables"][2]["foreign_keys"] = a["tables"][2]["foreign_keys"][:1]
    assert any("has no foreign key" in e for e in sp.validate_44(a, A41, A42, A43, COLS))
    assert sp.validate_44(a, A41, A42, A43, COLS, strict=False) == []
    assert sp.unimplemented_43(a, A43) == [("trip", "hotel")]
