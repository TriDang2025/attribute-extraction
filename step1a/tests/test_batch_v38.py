import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import batch_v38 as B  # noqa: E402
from s1a import llm_cache as lc  # noqa: E402
from s1a import role_guard as RG  # noqa: E402


def table():
    attrs = pd.DataFrame({"attr_id": ["a", "b", "c/0", "d"], "description": ["the place", "", "", "x"]})
    assign = {1: "a", 2: "a", 3: "b", 4: "c/0", 5: "d", 6: "d"}
    men = pd.DataFrame({"mention_id": [1, 2, 3, 4, 5, 6], "cluster_id": ["E#0", "E#0", "E#1", "E#2", "E#3", "E#3"],
                        "dialogue_id": ["x", "y", "x", "z", "z", "w"], "norm_value": ["ely", "ely", "bath", "10", "9", "10"],
                        "text": ["Ely", "ely", "Bath", "10", "9", "10"]})
    gc = pd.DataFrame({"attr_id": ["a", "b", "c/0"], "column": ["place", "place", "other"]})   # d is not a column
    return attrs, assign, men, gc


def test_column_table_pools_groups_and_description():
    attrs, assign, men, gc = table()
    cols = B.column_table(attrs, assign, men, gc)
    assert [c["name"] for c in cols] == ["other", "place"] and [c["cid"] for c in cols] == [1, 2]
    place = cols[1]
    assert place["groups"] == ["a", "b"] and place["description"] == "the place"      # biggest group with a description
    assert place["members"] == [("E#0", "a"), ("E#1", "b")] and place["n_mentions"] == 3 and place["n_dialogues"] == 2
    assert place["top_values"] == ["ely", "bath"] and place["pools"][0][0] == "E#0@a"    # largest member first
    other = cols[0]
    assert other["description"] == "" and other["n_mentions"] == 1 and other["value_types"].startswith("number")


def test_column_table_keeps_column_without_mentions():
    attrs, _, men, gc = table()
    cols = B.column_table(attrs, {}, men, gc)
    assert len(cols) == 2 and all(c["n_mentions"] == 0 and c["pools"] == [] for c in cols)


def test_sample_examples_round_robin_seeded_and_spread():
    pools = [("big", [(i, f"d{i}", f"v{i % 2}") for i in range(10)]), ("small", [(100, "d100", "z"), (101, "d101", "z")])]
    got = B.sample_examples(pools, 4, 0, "s")
    assert [k for _, k in got] == ["big", "small", "big", "small"]
    assert got == B.sample_examples(pools, 4, 0, "s") and got != B.sample_examples(pools, 4, 1, "s")
    everything = B.sample_examples(pools, 50, 0, "s")
    assert len(everything) == 12 and len({m for m, _ in everything}) == 12
    assert B.sample_examples([], 5, 0, "s") == []


def test_sample_examples_prefers_new_dialogue_and_value():
    pools = [("m", [(1, "d1", "a"), (2, "d1", "b"), (3, "d2", "a"), (4, "d3", "c")])]
    first_two = {m for m, _ in B.sample_examples(pools, 2, 0, "s")}
    assert len({{1: "d1", 2: "d1", 3: "d2", 4: "d3"}[m] for m in first_two}) == 2     # never two mentions of one dialogue first
    assert sorted(m for m, _ in B.sample_examples(pools, 4, 0, "s")) == [1, 2, 3, 4]


def test_centroids_nearest_and_ties():
    cols = [{"cid": 1, "mention_ids": [10, 11]}, {"cid": 2, "mention_ids": [12]}, {"cid": 3, "mention_ids": [13]},
            {"cid": 4, "mention_ids": [14]}, {"cid": 5, "mention_ids": []}]
    x = np.array([[1, 0], [1, 0], [0.9, 0.1], [0, 1], [1, 0]], dtype=float)
    cent = B.centroids(cols, [10, 11, 12, 13, 14], x)
    assert set(cent) == {1, 2, 3, 4} and abs(np.linalg.norm(cent[1]) - 1) < 1e-9
    assert B.nearest(cent, 1) == [4, 2]            # cid 4 is identical to cid 1, then cid 2
    assert B.nearest(cent, 3, k=5) == [2, 1, 4]    # cid 1 and 4 are tied: the lower cid first
    assert B.nearest({1: cent[1]}, 1) == []


def test_neighbour_examples_five_each_shuffled_deterministic():
    def pool(base):
        return [("m", [(base + i, f"d{base + i}", f"v{i}") for i in range(8)])]
    cols = {2: {"pools": pool(0)}, 3: {"pools": pool(100)}}
    a = B.neighbour_examples(cols, 1, [2, 3], 5, 0)
    assert len(a) == 10 and sum(src == 2 for _, src in a) == 5 and a == B.neighbour_examples(cols, 1, [2, 3], 5, 0)
    assert {m for m, s in a if s == 3} <= set(range(100, 108))


def test_render_dupcheck_shows_only_non_empty_fields():
    cols = [{"cid": 1, "name": "a b", "description": "desc", "top_values": ["x", "y"]},
            {"cid": 2, "name": "c", "description": "", "top_values": []}]
    t = B.render_dupcheck(cols, {1: "start"})
    assert "1. name: a b | description: desc | role: start | examples: x; y" in t
    assert "2. name: c | examples: (none)" in t and "role" not in t.split("2. name")[1].split("\n")[0]
    assert "Columns (2):" in t and "MultiWOZ" not in t


def test_render_evidence_question_and_schemas():
    t = B.render_evidence("arrival location", "where it ends", ["- 1 [user] turn: to [[ely]]"])
    assert "Does the marked value fit the attribute arrival location (where it ends)?" in t
    assert "Does the marked value fit the attribute x?" in B.render_evidence("x", "", ["- 1 a"])
    assert B.schema_evidence([1, 2])["properties"]["answers"]["items"]["properties"]["id"]["enum"] == [1, 2]
    assert lc.schema_enum(B.schema_dupcheck([1, 2]), "columns") == [1, 2]
    assert lc.schema_enum(B.schema_evidence([3, 4]), "id") == [3, 4]


def test_est_output_tokens():
    assert B.est_output_tokens("dupcheck", 20) == 200 and B.est_output_tokens("example", 10) == 128


def test_check_joins_rejects_name_role_pairs_only():
    cols = {1: {"name": "departure location"}, 2: {"name": "arrival location"}, 3: {"name": "departure place"},
            4: {"name": "location"}, 5: {"name": "address"}, 6: {"name": "leave at time"}, 7: {"name": "arrive by time"},
            8: {"name": "earliest leave time"}}
    joins = [{"columns": [1, 2], "reason": ""}, {"columns": [1, 3], "reason": ""}, {"columns": [4, 5], "reason": ""},
             {"columns": [6, 7], "reason": ""}, {"columns": [6, 8, 1], "reason": ""}, {"columns": [1, 3, 2], "reason": ""}]
    kept, rejected = B.check_joins(joins, cols)
    assert [j["columns"] for j in rejected] == [[1, 2], [6, 7], [1, 3, 2]]
    assert [j["columns"] for j in kept] == [[1, 3], [4, 5], [6, 8, 1]]       # location vs address is not a name pair here
    assert RG.forbidden_merge("location", "address") and not RG.forbidden_merge("location", "address", B.NAME_PAIRS)
    k2, r2 = B.check_joins([{"columns": [4, 5]}], cols, roles={4: "where it starts", 5: "x"})
    assert len(k2) == 1 and r2 == []


# ---- parsers

def test_parse_dupcheck():
    schema = B.schema_dupcheck([1, 2, 3])
    ok = json.dumps({"joins": [{"columns": [1, 2], "reason": "same"}]})
    parsed, errs, n = lc.parse_job(ok, "dupcheck", schema)
    assert errs == [] and n == 1 and parsed["joins"][0]["columns"] == [1, 2]
    assert lc.parse_job('{"joins": []}', "dupcheck", schema)[1:] == ([], 0)
    bad = lc.parse_job('{"joins": [{"columns": [1], "reason": "x"}, {"columns": [1, 9], "reason": "y"}, {"columns": [2, 3]}]}',
                       "dupcheck", schema)
    assert len(bad[1]) == 3 and bad[2] == 3
    assert lc.parse_job('{"x": 1}', "dupcheck", schema)[1] == ["joins missing or not a list"]
    assert lc.parse_job("nothing", "dupcheck", schema)[1] == ["no JSON object found"]
    assert lc.parse_job('```json\n{"joins": []}\n```', "dupcheck", schema)[1] == []


def test_parse_evidence():
    schema = B.schema_evidence([1, 2, 3])
    ok = json.dumps({"answers": [{"id": 1, "fits": "yes"}, {"id": 2, "fits": "no"}, {"id": 3, "fits": "yes"}]})
    _, errs, n = lc.parse_job(ok, "evidence", schema)
    assert errs == [] and n == 3
    short = lc.parse_job('{"answers": [{"id": 1, "fits": "yes"}, {"id": 1, "fits": "no"}, {"id": 7, "fits": "yes"}, '
                         '{"id": 2, "fits": "maybe"}]}', "evidence", schema)
    assert short[1] == ["id 1 answered more than once", "answers[2] unknown id 7", "answers[3] needs an integer id and fits yes|no",
                        "id 2 not answered", "id 3 not answered"]
    assert lc.parse_job('{"answers": "no"}', "evidence", schema)[1] == ["answers missing or not a list"]
    assert lc.parse_evidence('{"answers": [{"id": 5, "fits": "no"}]}')[1] == []     # no id list: only the shape is checked


def test_parse_job_unchanged_for_old_formats():
    assert lc.parse_job('{"attributes": [{"name": "a", "description": "b"}]}', "baseline", {})[1:] == ([], 1)
    try:
        lc.parse_job("{}", "nope", {})
    except ValueError as e:
        assert "unknown job format" in str(e)
    else:
        raise AssertionError("no error")
