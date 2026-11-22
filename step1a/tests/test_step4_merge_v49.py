"""wf_v4.9 B+M: join tables of one Step 1a entity (s1a/step4_merge_v49.py, chain key merge_same_entity of s1a/step4_v44.py), toy schemas."""
import copy

from s1a import step4_merge_v49 as M
from s1a import step4_sql as SQL
from s1a import step4_v44 as S

COLS = [{"id": f"{e}:{i}"} for e, i in (("hotel", 1), ("hotel", 2), ("hotel", 3), ("hotel", 4), ("pub", 1), ("pub", 2), ("taxi", 1))]


def col(name, source=None, type_="text"):
    return {"name": name, "type": type_, "source": source, "new": source is None, "gt": None}


def table(name, columns, pk, fks=()):
    return {"name": name, "description": f"d {name}", "row": f"one {name}", "columns": columns, "primary_key": pk, "foreign_keys": list(fks)}


def toy():
    hotel = table("hotel", [col("hotel", None, "id"), col("name", "hotel:1"), col("area", "hotel:2")], ["hotel"])
    hotel2 = table("hotel_2", [col("hotel", None, "id"), col("area", "hotel:3"), col("stars", "hotel:4"), col("name", "hotel:1"), col("hotel id", None, "id")],
                   ["hotel"], [{"columns": ["hotel id"], "ref_table": "hotel", "ref_columns": ["hotel"]}])
    pub = table("pub", [col("pub id", None, "id"), col("pub name", "pub:1"), col("hotel id", None, "id")], ["pub id"],
                [{"columns": ["hotel id"], "ref_table": "hotel_2", "ref_columns": ["hotel"]}])
    taxi = table("taxi", [col("taxi id", None, "id"), col("taxi type", "taxi:1")], ["taxi id"])
    return {"tables": [hotel, hotel2, pub, taxi],
            "relationships": [{"from": "hotel_2", "to": "hotel", "kind": "one_to_many", "reason": ""},
                              {"from": "pub", "to": "hotel_2", "kind": "one_to_many", "reason": "r"},
                              {"from": "pub", "to": "hotel", "kind": "one_to_many", "reason": "dup"}],
            "unused": [{"source": "pub:2", "reason": "x"}], "duplicate_flags": []}


def test_same_entity_tables_are_joined():
    src = toy()
    before = copy.deepcopy(src)
    c, merges = M.merge_same_entity(src, COLS)
    assert src == before                                                         # input untouched
    assert merges == [{"entity": "hotel", "kept": "hotel_2", "dropped": ["hotel"], "tables_before": 2}]
    assert [t["name"] for t in c["tables"]] == ["hotel_2", "pub", "taxi"]
    h = c["tables"][0]
    assert h["primary_key"] == ["hotel"] and h["description"] == "d hotel_2"
    srcs = [x["source"] for x in h["columns"] if x["source"]]
    assert sorted(srcs) == ["hotel:1", "hotel:2", "hotel:3", "hotel:4"] and len(set(srcs)) == 4        # union, no duplicate source
    names = [x["name"].lower() for x in h["columns"]]
    assert len(set(names)) == len(names) and names.count("hotel") == 1                # one key column, a taken name renamed
    assert not any(x["name"] == "hotel id" for x in h["columns"]) and h["foreign_keys"] == []   # the link between the two is gone, with its column


def test_other_links_are_repointed_and_unused_kept():
    c, _ = M.merge_same_entity(toy(), COLS)
    assert c["relationships"] == [{"from": "pub", "to": "hotel_2", "kind": "one_to_many", "reason": "r"}]   # intra link dropped, duplicate removed
    pub = c["tables"][1]
    assert pub["foreign_keys"] == [{"columns": ["hotel id"], "ref_table": "hotel_2", "ref_columns": ["hotel"]}]
    assert c["unused"] == toy()["unused"] and c["tables"][2] == toy()["tables"][3]


def test_repoint_to_a_dropped_table_and_its_key():
    src = toy()
    src["tables"][2]["foreign_keys"] = [{"columns": ["hotel id"], "ref_table": "hotel", "ref_columns": ["hotel"]}]
    src["tables"][1]["primary_key"] = ["hotel key"]                                    # dropped one has another key name
    src["tables"][1]["columns"][0]["name"] = "hotel key"
    src["tables"][0]["columns"] += [col("c5", "hotel:2"), col("c6", "x:1")]            # make the first one the larger: it is kept, hotel_2 dropped
    src["tables"][0]["columns"][-1]["source"] = None
    c, merges = M.merge_same_entity(src, COLS)
    kept = merges[0]["kept"]
    assert kept == "hotel"
    kp = next(t for t in c["tables"] if t["name"] == kept)["primary_key"][0]
    assert c["tables"][1]["foreign_keys"][0]["ref_table"] == kept and c["tables"][1]["foreign_keys"][0]["ref_columns"] == [kp]


def test_tie_prefers_name_without_suffix_and_link_tables_stay():
    a = table("hotel_2", [col("hotel", None, "id"), col("x", "hotel:1")], ["hotel"])
    b = table("hotel", [col("hotel", None, "id"), col("y", "hotel:2")], ["hotel"])
    link = table("hotel_pub", [col("hotel_pub id", None, "id")], ["hotel_pub id"])
    c, merges = M.merge_same_entity({"tables": [a, b, link], "relationships": [], "unused": [], "duplicate_flags": []}, COLS)
    assert merges[0]["kept"] == "hotel" and [t["name"] for t in c["tables"]] == ["hotel", "hotel_pub"]


def test_nothing_to_merge_returns_equal_schema_and_sql_works():
    src = toy()
    src["tables"] = [src["tables"][0]] + src["tables"][2:]
    src["relationships"], src["tables"][1]["foreign_keys"] = [], []
    c, merges = M.merge_same_entity(src, COLS)
    assert merges == [] and c == src
    merged, _ = M.merge_same_entity(toy(), COLS)
    assert "CREATE TABLE" in SQL.to_sql(merged) and any(o["op"] == "CREATE_REL" for o in SQL.to_operations(merged))


def test_switch_in_with_switches_and_chain():
    cfg = S.with_switches(S.load_config(), off=S.SWITCHES)
    assert "merge_same_entity" not in cfg and S.with_switches(cfg, merge_same_entity=True)["merge_same_entity"] is True
