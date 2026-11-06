import copy
import sqlite3

from s1a import step4_sql as ss
from tests.test_step4_prompts import A41, A42, A43, A44, COLS


def canon():
    return ss.assemble(A41, A42, A43, A44, COLS)


def test_assemble_contract():
    c = canon()
    assert [t["name"] for t in c["tables"]] == ["train", "hotel", "trip"]
    train, hotel, trip = c["tables"]
    assert train["columns"][0] == {"name": "train id", "type": "id", "source": None, "new": True, "gt": None}
    assert train["columns"][1] == {"name": "leave at", "type": "time", "source": "train:1", "new": False, "gt": None}
    assert train["primary_key"] == ["train id"] and hotel["primary_key"] == ["hotel name"]
    assert trip["description"] == "A trip." and trip["row"] == "one trip"
    assert trip["foreign_keys"] == [{"columns": ["train id"], "ref_table": "train", "ref_columns": ["train id"]},
                                    {"columns": ["hotel name"], "ref_table": "hotel", "ref_columns": ["hotel name"]}]
    assert c["relationships"][0] == {"from": "trip", "to": "train", "kind": "one_to_many", "reason": "r"}
    assert c["unused"] == [{"source": "train:4", "reason": "noise"}]
    assert c["duplicate_flags"] == [{"source": "hotel:3", "duplicate_of": "hotel:1"}]


def test_to_sql_runs_in_sqlite_and_quotes():
    sql = ss.to_sql(canon())
    assert '"train id" INTEGER' in sql and 'PRIMARY KEY ("hotel name")' in sql
    assert 'FOREIGN KEY ("train id") REFERENCES "train" ("train id")' in sql
    assert sql.index('CREATE TABLE "train"') < sql.index('CREATE TABLE "trip"')
    con = sqlite3.connect(":memory:")
    con.executescript(sql)
    assert {r[0] for r in con.execute("select name from sqlite_master where type='table'")} == {"train", "hotel", "trip"}


def test_quote_escapes():
    assert ss.quote('a"b') == '"a""b"'


def test_to_operations_order_and_fields():
    ops = ss.to_operations(canon())
    kinds = [o["op"] for o in ops]
    assert kinds == sorted(kinds, key=["CREATE_ENTITY", "ADD_ATTR", "CREATE_REL"].index)
    assert ops[0] == {"op": "CREATE_ENTITY", "name": "train", "description": "A train.", "row": "one train"}
    attr = [o for o in ops if o["op"] == "ADD_ATTR"]
    assert len(attr) == 4 + 3 + 3
    assert {"op": "ADD_ATTR", "entity": "train", "name": "leave at", "type": "time", "source": "train:1", "is_key": False} in attr
    assert {"op": "ADD_ATTR", "entity": "train", "name": "train id", "type": "id", "source": None, "is_key": True} in attr
    rels = [o for o in ops if o["op"] == "CREATE_REL"]
    assert rels[1] == {"op": "CREATE_REL", "from": "trip", "to": "hotel", "kind": "one_to_many", "fk_columns": ["hotel name"]}


def test_from_e_roundtrip():
    e = {"tables": [{"name": "a", "description": "d", "row": "one a", "primary_key": ["id"],
                     "columns": [{"name": "id", "type": "id"}, {"name": "b id", "type": "id"}],
                     "foreign_keys": [{"column": "b id", "ref_table": "b", "ref_column": "id"}]},
                    {"name": "b", "description": "d", "row": "one b", "primary_key": ["id"],
                     "columns": [{"name": "id", "type": "id"}], "foreign_keys": []}],
         "relationships": [{"from": "a", "to": "b", "kind": "one_to_many", "reason": "r"}]}
    c = ss.from_e(e)
    assert all(col["source"] is None for t in c["tables"] for col in t["columns"])
    assert c["unused"] == [] and c["duplicate_flags"] == []
    sql = ss.to_sql(c)
    assert sql.index('CREATE TABLE "b"') < sql.index('CREATE TABLE "a"')     # referenced table first
    sqlite3.connect(":memory:").executescript(sql)
    assert ss.to_operations(c)[-1] == {"op": "CREATE_REL", "from": "a", "to": "b", "kind": "one_to_many", "fk_columns": ["b id"]}


def test_to_sql_cycle_keeps_order():
    c = canon()
    c = copy.deepcopy(c)
    c["tables"][0]["foreign_keys"].append({"columns": ["train id"], "ref_table": "trip", "ref_columns": ["trip id"]})
    sql = ss.to_sql(c)
    assert sql.count("CREATE TABLE") == 3
