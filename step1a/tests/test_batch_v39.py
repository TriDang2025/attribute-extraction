import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import batch_v38 as BT  # noqa: E402
from s1a import batch_v39 as B  # noqa: E402
from s1a import llm_cache as lc  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402


def col(cid, name, pools, description=""):
    rows = [x for _, items in pools for x in items]
    return {"cid": cid, "name": name, "description": description, "groups": [k.split("@")[1] for k, _ in pools],
            "members": [k for k, _ in pools], "mention_ids": [x[0] for x in rows], "n_mentions": len(rows),
            "n_dialogues": len({x[1] for x in rows}), "n_values": len({x[2] for x in rows}),
            "top_values": BT._top_values([x[2] for x in rows]), "pools": pools}


def columns():
    """1 start place (holds part E#0/0), 2 end place, 3 city, 4 time (holds part E#0/1 and a cluster E#3), 5 empty column."""
    return [col(1, "departure place", [("E#0@E#0/0", [(1, "d1", "ely"), (2, "d2", "bath")])]),
            col(2, "destination place", [("E#1@E#1", [(3, "d3", "york")])]),
            col(3, "city", [("E#2@E#2", [(4, "d4", "ely"), (5, "d5", "ely")])], "a city"),
            col(4, "time", [("E#0@E#0/1", [(6, "d1", "10:00")]), ("E#3@E#3", [(7, "d7", "9:00")])]),
            col(5, "unused", [])]


ATTRS = [{"attr_id": "E#0/0", "name": "departure_place", "clusters": "E#0", "source": "split"},
         {"attr_id": "E#0/1", "name": "time", "clusters": "E#0", "source": "split"},
         {"attr_id": "E#0/2", "name": "empty_part", "clusters": "E#0", "source": "split"},
         {"attr_id": "E#1", "name": "destination_place", "clusters": "E#1", "source": "keep"}]


def parts():
    return B.part_records(columns(), ATTRS, {("E#0", "time"): "when"})


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def test_part_records_skip_non_split_and_empty_parts():
    ps = parts()
    assert [p["pid"] for p in ps] == ["E#0/0", "E#0/1"]
    assert ps[0]["cid"] == 1 and ps[0]["mention_ids"] == [1, 2] and ps[0]["description"] == ""
    assert ps[1]["cid"] == 4 and ps[1]["description"] == "when" and ps[1]["key"] == "E#0@E#0/1"


def test_nearest_columns_excludes_own_column_and_is_capped():
    cent = {1: unit([1, 0]), 2: unit([0.9, 0.1]), 3: unit([0, 1]), 4: unit([0.5, 0.5])}
    part = unit([1, 0.01])      # closest to its own column 1, which must never come back
    assert B.nearest_columns(cent, part, 1, k=5) == [2, 4, 3]
    assert B.nearest_columns(cent, part, 1, k=2) == [2, 4]
    assert 1 not in B.nearest_columns(cent, part, 1)


def test_shuffled_order_is_deterministic_per_seed_and_a_permutation():
    items = list(range(8))
    a = B.shuffled_order(items, 0, "x")
    assert a == B.shuffled_order(items, 0, "x") and sorted(a) == items
    assert B.shuffled_order(items, 1, "x") != a
    assert items == list(range(8))    # the input is not changed


def test_reconcile_prompt_schema_and_parse():
    cands = [c for c in columns() if c["cid"] in (2, 3)]
    text = B.render_reconcile(parts()[0], cands, ["- 1 [user] turn: [[ely]]"])
    assert "Part E#0/0: name: departure place" in text and "name: city | description: a city | examples: ely" in text
    assert "Is this part the same attribute, with the same role, as one of these columns?" in text
    s = B.schema_reconcile("E#0/0", ["destination place", "city"])
    assert lc.schema_enum(s, "same_as") == ["destination place", "city", "none"] and lc.schema_enum(s, "unit_id") == ["E#0/0"]
    raw = json.dumps({"unit_id": "E#0/0", "reason": "same", "same_as": "city"})
    parsed, errs, n = lc.parse_job(raw, "reconcile", s)
    assert not errs and n == 1
    cands_json = [{"cid": 2, "name": "destination place"}, {"cid": 3, "name": "city"}]
    assert B.choice_from_response(parsed, errs, cands_json) == 3
    assert B.choice_from_response({"same_as": "none"}, [], cands_json) is None
    assert B.choice_from_response(parsed, ["bad"], cands_json) is None
    assert B.choice_from_response({"same_as": "elsewhere"}, [], cands_json) is None


def test_apply_reconcile_moves_mentions_and_keeps_other_members():
    cols = columns()
    new, rep = B.apply_reconcile(cols, parts(), {"E#0/1": 3})
    names = [c["name"] for c in new]
    assert names == sorted(names) and [c["cid"] for c in new] == list(range(1, len(new) + 1))
    by = {c["name"]: c for c in new}
    assert set(by["city"]["mention_ids"]) == {4, 5, 6} and by["city"]["n_mentions"] == 3 and by["city"]["old_cids"] == [3]
    assert by["time"]["mention_ids"] == [7] and by["time"]["groups"] == ["E#3"]    # "time" keeps its other member
    assert by["city"]["groups"] == ["E#0/1", "E#2"]
    assert [r["status"] for r in rep] == ["none", "joined"] and rep[1]["from"] == 4 and rep[1]["to"] == 3
    assert len(new) == 5 and "unused" in names      # an empty column that lost nothing stays
    assert cols[3]["n_mentions"] == 2 and cols[2]["n_mentions"] == 2    # the input is not changed


def test_apply_reconcile_drops_a_column_emptied_by_the_join():
    new, _ = B.apply_reconcile(columns(), parts(), {"E#0/0": 3})
    names = [c["name"] for c in new]
    assert "departure place" not in names and len(new) == 4
    assert {c["name"]: c for c in new}["city"]["top_values"] == ["ely", "bath"]


def test_apply_reconcile_blocks_role_pairs_and_invalid_choices():
    cols = columns()
    new, rep = B.apply_reconcile(cols, parts(), {"E#0/0": 2, "E#0/1": 4})   # start into end place; a part into its own column
    assert [r["status"] for r in rep] == ["blocked", "invalid"]
    assert sum(c["n_mentions"] for c in new) == 7 and len(new) == 5
    _, rep = B.apply_reconcile(cols, parts(), {"E#0/0": 99})
    assert rep[0]["status"] == "invalid"


def test_apply_reconcile_without_choices_changes_nothing():
    cols = columns()
    new, rep = B.apply_reconcile(cols, parts(), {})
    assert [(c["name"], c["mention_ids"]) for c in new] == sorted((c["name"], c["mention_ids"]) for c in cols)
    assert {r["status"] for r in rep} == {"none"}


def test_apply_reconcile_accepts_json_pools():
    cols = json.loads(json.dumps(columns()))      # tuples become lists, as columns.json stores them
    new, rep = B.apply_reconcile(cols, json.loads(json.dumps(parts())), {"E#0/1": 3})
    assert rep[1]["status"] == "joined" and {c["name"]: c for c in new}["city"]["n_mentions"] == 3
    assert BT.render_dupcheck(new).count("\n") > 3    # the reconciled columns render as a duplicate check


def test_a_cue_prompt_adds_one_sentence_and_schema_names_the_label():
    text = PIN.INSTRUCTION_V2 + "\n\nEntity E1: 2 clusters.\n"
    out = B.render_a_cue(text)
    assert out.endswith(text[len(PIN.INSTRUCTION_V2):]) and PIN.CUE_LINE in out
    assert len(out.splitlines()) == len(text.splitlines())     # the cue joins an existing line
    assert out.replace(" " + PIN.CUE_LINE, "") == text
    with pytest.raises(ValueError):
        B.render_a_cue("not an A prompt")
    base = {"type": "object", "properties": {"clusters": {"type": "array", "items": {"type": "object", "properties": {
        "attribute": {"type": "string"}}}}}}
    s = B.schema_a_cue(base)
    assert "attribute_cue" in s["properties"]["clusters"]["items"]["properties"]["attribute"]["description"]
    assert "description" not in base["properties"]["clusters"]["items"]["properties"]["attribute"]
    raw = json.dumps({"attributes": [{"name": "day", "description": "d", "role": "r"}],
                      "clusters": [{"cluster_id": "E1#0", "attribute": "attribute_cue", "evidence": "what day", "mixed": False,
                                    "placement": "current entity E1"}]})
    sch = {"properties": {"cluster_id": {"enum": ["E1#0"]}}}
    parsed, errs, _ = B.parse_job(raw, "v2", sch, "a_cue")
    assert not errs and parsed["clusters"][0]["attribute"] == "attribute_cue"
    assert lc.parse_job(raw, "v2", sch)[1]       # the plain v2 parser rejects it, so the a_cue family needs its own
    bad = raw.replace("attribute_cue", "made_up")
    assert B.parse_job(bad, "v2", sch, "a_cue")[1] and B.parse_job(bad, "v2", sch)[1]
    assert not B.parse_job(raw.replace("attribute_cue", "day"), "v2", sch, "a_cue")[1]
