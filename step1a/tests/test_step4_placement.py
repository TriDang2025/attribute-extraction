"""wf_v4 batch additions: example contexts and data signals in the prompts, the placement prompt / validator / apply, placement_vs_gt."""
import copy
import json
import sqlite3

import pytest

from s1a import llm_cache as lc
from s1a import step4_gt as G
from s1a import step4_prompts as sp
from s1a import step4_score as S
from s1a import step4_sql as ss
from tests.test_step4_prompts import COLS, ROOT, col, jsonschema_ok
from tests.test_step4_score import toy

CANON = {"tables": [{"name": "hotel", "description": "A hotel.", "row": "one hotel",
                     "columns": [{"name": "hotel name", "type": "text", "source": "hotel:1", "new": False, "gt": None}],
                     "primary_key": ["hotel name"], "foreign_keys": []},
                    {"name": "booking", "description": "A booking.", "row": "one booking",
                     "columns": [{"name": "hotel name", "type": "text", "source": None, "new": True, "gt": None}],
                     "primary_key": [], "foreign_keys": [{"columns": ["hotel name"], "ref_table": "hotel", "ref_columns": ["hotel name"]}]}],
         "relationships": [{"from": "booking", "to": "hotel", "kind": "one_to_many", "reason": ""}], "unused": [], "duplicate_flags": []}
NEWCOL = {"id": "hotel:9", "name": "stars", "value_type": {"dominant": "number"}}


@pytest.fixture()
def gt():
    g = G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml")
    rows = [{"gt_table": tn, "gt_column": c["name"], "level": "", "found_by": "", "reachable": "yes"} for tn, t in g["tables"].items() for c in t["columns"]]
    G.attach_reachable(g, "dev50", rows)
    return g


# ---- prompts

def test_render_column_examples_with_context_and_no_examples():
    c = col("x:1", "day", ex=(["friday", "leave on Friday please"], ["monday", ""]), data_signal="5 mentions", signal="support 1/2")
    block = sp.render_column(c)
    assert '    "friday" (in: "leave on Friday please")\n    "monday"\n' in block + "\n"
    assert "checker evidence: support 1/2" in block and "data signals: 5 mentions" in block
    assert "no examples" in sp.render_column(col("x:2", "none", ex=()))


def test_41_data_signal_note_only_with_data_signals():
    plain, _ = sp.build_prompt_41(sp.render_columns(COLS), COLS)
    sig_cols = [{**c, "data_signal": "n"} for c in COLS]
    text, _ = sp.build_prompt_41(sp.render_columns(sig_cols), sig_cols)
    assert '"data signals" are automatic counts' not in plain and '"data signals" are automatic counts' in text
    assert '"checker evidence"' in plain and "signals:" not in plain.replace("checker evidence:", "")


def test_entity_field_sets_the_heading():
    cols = [{**col("gt:1", "a"), "entity": "train"}, {**col("gt:2", "b"), "entity": "hotel"}]
    block = sp.render_columns(cols)
    assert "== train ==" in block and "== hotel ==" in block and "== gt ==" not in block
    assert "under 2 headings" in sp.build_prompt_41(block, cols)[0]


def test_place_prompt_and_schema():
    column = col("hotel:9", "stars", "number", ("3", "4"), data_signal="card text")
    text, schema = sp.build_prompt_place(CANON, column)
    assert "Table hotel: A hotel. One row = one hotel." in text and "- hotel name (text) [primary key]" in text
    assert "[refers to hotel.hotel name]" in text and "booking -> hotel (one_to_many)" in text
    assert "[hotel:9] stars" in text and "data signals: card text" in text and "multiwoz" not in text.lower()
    assert schema["properties"]["option"]["enum"] == sp.OPTIONS and schema["properties"]["target_table"]["enum"] == ["hotel", "booking", "none"]
    assert "data signals" not in sp.build_prompt_place(CANON, {k: v for k, v in column.items() if k != "data_signal"})[0]
    js = jsonschema_ok(schema)
    ok = {"reason": "r", "option": "P3", "target_table": "none", "new_table": {"name": "n", "row": "one n"},
          "link": {"from": "n", "to": "hotel", "kind": "one_to_many"}}
    js.Draft202012Validator(schema).validate(ok)
    js.Draft202012Validator(schema).validate({**ok, "new_table": None, "link": None})
    assert lc.parse_job(json.dumps(ok), "s4_place", schema)[1] == []
    assert lc.parse_job(json.dumps({**ok, "new_table": None, "link": None}), "s4_place", schema)[1] == []
    assert lc.parse_job(json.dumps({**ok, "option": "P9"}), "s4_place", schema)[1] != []
    assert lc.parse_job(json.dumps({**ok, "link": {"from": "n"}}), "s4_place", schema)[1] != []


def test_validate_place():
    base = {"reason": "", "option": "P1", "target_table": "hotel", "new_table": None, "link": None}
    assert sp.validate_place(base, CANON) == []
    assert sp.validate_place({**base, "target_table": "none"}, CANON)
    assert sp.validate_place({**base, "option": "P3", "target_table": "none"}, CANON)             # needs new_table
    assert sp.validate_place({**base, "option": "P4", "link": None}, CANON)                         # needs link
    assert sp.validate_place({**base, "new_table": {"name": "hotel", "row": ""}}, CANON)           # name used
    p3 = {**base, "option": "P3", "target_table": "none", "new_table": {"name": "n", "row": "r"},
          "link": {"from": "n", "to": "hotel", "kind": "one_to_many"}}
    assert sp.validate_place(p3, CANON) == []
    assert sp.validate_place({**p3, "link": {"from": "n", "to": "zzz", "kind": "one_to_many"}}, CANON)


def test_canon_type():
    assert sp.canon_type({"dominant": "number"}) == "integer" and sp.canon_type({"dominant": "time"}) == "time"
    assert sp.canon_type({"dominant": ""}) == "text" and sp.canon_type(None) == "text" and sp.canon_type("price") == "price"


# ---- apply_placement

def place(opt, **kw):
    return {"reason": "", "option": opt, "target_table": kw.get("target_table", "none"), "new_table": kw.get("new_table"), "link": kw.get("link")}


def test_apply_p1_adds_column_and_leaves_input():
    before = copy.deepcopy(CANON)
    c = ss.apply_placement(CANON, place("P1", target_table="hotel"), NEWCOL)
    assert CANON == before
    assert c["tables"][0]["columns"][-1] == {"name": "stars", "type": "integer", "source": "hotel:9", "new": False, "gt": None}


def test_apply_p2_existing_and_new_linking_table():
    c = ss.apply_placement(CANON, place("P2", target_table="booking"), NEWCOL)
    assert [x["name"] for x in c["tables"][1]["columns"]] == ["booking id", "hotel name", "stars"]   # a table without a key gets one
    nt = {"name": "stay", "row": "one stay"}
    c = ss.apply_placement(CANON, place("P2", new_table=nt, link={"from": "stay", "to": "hotel", "kind": "many_to_many"}), NEWCOL)
    stay = c["tables"][-1]
    assert stay["name"] == "stay" and stay["primary_key"] == ["stay id"] and [x["name"] for x in stay["columns"]] == ["stay id", "stars", "hotel id"]
    assert stay["foreign_keys"] == [{"columns": ["hotel id"], "ref_table": "hotel", "ref_columns": ["hotel name"]}]
    assert c["relationships"][-1] == {"from": "stay", "to": "hotel", "kind": "many_to_many", "reason": "placement"}


def test_apply_p3_new_table_and_p5():
    nt = {"name": "review", "row": "one review"}
    link = {"from": "review", "to": "hotel", "kind": "one_to_many"}
    for opt in ("P3", "P5"):
        c = ss.apply_placement(CANON, place(opt, new_table=nt, link=link), NEWCOL)
        t = c["tables"][-1]
        assert t["primary_key"] == ["review id"] and "stars" in [x["name"] for x in t["columns"]]
        assert t["foreign_keys"][0]["ref_table"] == "hotel" and len(c["relationships"]) == 2
    c = ss.apply_placement(CANON, place("P3", new_table=nt), NEWCOL)
    assert len(c["relationships"]) == 1 and c["tables"][-1]["foreign_keys"] == []
    sqlite3.connect(":memory:").executescript(ss.to_sql(ss.apply_placement(CANON, place("P3", new_table=nt, link=link), NEWCOL)))


def test_apply_p4_column_becomes_foreign_key_and_existing_relationship_not_doubled():
    c = ss.apply_placement(CANON, place("P4", target_table="booking", link={"from": "booking", "to": "hotel", "kind": "one_to_many"}), NEWCOL)
    b = c["tables"][1]
    assert b["columns"][-1]["name"] == "stars" and {"columns": ["stars"], "ref_table": "hotel", "ref_columns": ["hotel name"]} in b["foreign_keys"]
    assert len(c["relationships"]) == 1


def test_apply_placement_errors():
    for bad in (place("P1", target_table="zzz"), place("P3"), place("P4", target_table="hotel")):
        with pytest.raises(ValueError):
            ss.apply_placement(CANON, bad, NEWCOL)
    with pytest.raises(ValueError):
        ss.apply_placement(CANON, place("P3", new_table={"name": "hotel", "row": ""}), NEWCOL)


# ---- placement_vs_gt

def stars_schema(gt, table):
    c = G.to_canonical(gt)
    for t in c["tables"]:
        t["columns"] = [x for x in t["columns"] if x["gt"] != "Hotel stars"]
    next(t for t in c["tables"] if t["name"] == table)["columns"].append(
        {"name": "stars", "type": "integer", "source": "hotel:18", "new": False, "gt": "Hotel stars"})
    return c


def test_placement_vs_gt_option_and_table(tmp_path, gt):
    ho, lev = toy(tmp_path, gt)
    attr = {"gt": "Hotel stars", "kind": "P1", "columns": ["hotel:18"]}
    ok = S.placement_vs_gt([stars_schema(gt, "hotel")], [{"option": "P1"}], [attr], gt, "dev50", ho, lev)[0]
    assert ok == {"gt": "Hotel stars", "expected_option": "P1", "option": "P1", "option_ok": True, "expected_table": "hotel", "table": "hotel",
                  "table_ok": True}
    wrong = S.placement_vs_gt([stars_schema(gt, "train")], [{"option": "P2"}], [attr], gt, "dev50", ho, lev)[0]
    assert (wrong["option_ok"], wrong["table_ok"], wrong["table"]) == (False, False, "train")
    failed = S.placement_vs_gt([stars_schema(gt, "hotel")], [None], [attr], gt, "dev50", ho, lev)[0]
    assert failed["option"] is None and failed["option_ok"] is False


def test_placement_vs_gt_booking_column_in_place_table_counts(tmp_path, gt):
    ho, lev = toy(tmp_path, gt)
    c = G.to_canonical(gt)
    for t in c["tables"]:
        t["columns"] = [x for x in t["columns"] if x["gt"] != "Restaurant requested time"]
    next(t for t in c["tables"] if t["name"] == "restaurant")["columns"].append(
        {"name": "time", "type": "time", "source": "restaurant:10", "new": False, "gt": "Restaurant requested time"})
    r = S.placement_vs_gt([c], [{"option": "P2"}], [{"gt": "Restaurant requested time", "kind": "P2", "columns": ["restaurant:10"]}],
                          gt, "dev50", ho, lev)[0]
    assert r["expected_table"] == "restaurant_booking" and r["table"] == "restaurant" and r["table_ok"]   # the merged design accepts it


def test_validate_44_new_key_name_must_not_be_a_column_name():
    from tests.test_step4_prompts import A41, A42, A43, A44
    bad = copy.deepcopy(A44)
    bad["tables"][0]["new_id_name"] = "Leave At"
    assert any("also a column name" in e for e in sp.validate_44(bad, A41, A42, A43, COLS))
    assert not any("also a column name" in e for e in sp.validate_44(A44, A41, A42, A43, COLS))
