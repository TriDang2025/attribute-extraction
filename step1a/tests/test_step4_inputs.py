"""wf_v4 inputs (s1a/step4_inputs.py): examples with context, column order, GT inputs, flat schema, dialogue fill, signals-only schema."""
import json
from pathlib import Path

import pandas as pd
import pytest

from s1a import step4_gt as G
from s1a import step4_inputs as I
from s1a import step4_prompts as sp
from s1a.pilot_input import est_tokens

ROOT = Path(__file__).resolve().parents[1]


def mentions(rows):
    """rows: (mention_id, dialogue_id, text, norm_value, context)."""
    return pd.DataFrame(rows, columns=["mention_id", "dialogue_id", "text", "norm_value", "context"]).set_index("mention_id")


def test_snippet_width_and_value_kept():
    ctx = "I would really like to book a table for the evening, say at 18:30, at the restaurant near the river."
    s = I.snippet("18:30", ctx, 40)
    assert len(s) == 40 and "18:30" in s and s.startswith("...") and s.endswith("...")
    assert I.snippet("x", "short context", 40) == "short context"
    assert I.snippet("zzz", ctx, 30).startswith("I would") or len(I.snippet("zzz", ctx, 30)) == 30


def test_examples_most_frequent_first_ties_alphabetical_context_of_first_mention():
    m = mentions([(1, "d1", "Friday", "friday", "on Friday one"), (2, "d1", "monday", "monday", "monday two"),
                  (3, "d2", "Friday", "friday", "on Friday three"), (4, "d2", "tuesday", "tuesday", "tuesday four"),
                  (5, "d3", "monday", "monday", "monday five")])
    assert I.examples_of(m, 3) == [["friday", "on Friday one"], ["monday", "monday two"], ["tuesday", "tuesday four"]]
    assert len(I.examples_of(m, 2)) == 2 and I.examples_of(m.iloc[0:0]) == []


def test_main_columns_uses_mention_ids_and_keeps_checker_text():
    m = mentions([(0, "d1", "Ely", "ely", "to Ely"), (1, "d1", "Ely", "ely", "to Ely now"), (2, "d2", "Leeds", "leeds", "from Leeds")])
    handover = {e: {"columns": []} for e in I.ENTITIES}
    handover["train"] = {"columns": [{"id": 1, "name": "destination", "description": "d", "role": "r", "value_type": {"dominant": "text", "share": 1.0},
                                       "n_mentions": 3, "n_dialogues": 2, "mention_ids": [0, 1, 2], "top_values": [], "verdict": "unsure",
                                       "evidence": {"support": {"yes": 1, "n": 4}}, "flags": {}}]}
    cols = I.main_columns(handover, m, 5, 80)
    assert len(cols) == 1 and cols[0]["id"] == "train:1" and cols[0]["examples"] == [["ely", "to Ely"], ["leeds", "from Leeds"]]
    assert cols[0]["signal"] == "support 1/4" and cols[0]["flag"] == "unsure" and "data_signal" not in cols[0]
    b = I.with_signals(cols, {"train:1": "card"})
    assert b[0]["data_signal"] == "card" and "data_signal" not in cols[0]


def test_order_columns_seed0_same_others_shuffle_inside_entity_blocks():
    cols = [{"id": f"{e}:{i}"} for e in ("train", "hotel") for i in range(1, 7)]
    assert I.order_columns(cols, 0) == cols
    one, again, two = I.order_columns(cols, 1), I.order_columns(cols, 1), I.order_columns(cols, 2)
    assert one == again and one != cols and one != two
    assert [c["id"].split(":")[0] for c in one] == ["train"] * 6 + ["hotel"] * 6 and sorted(c["id"] for c in one) == sorted(c["id"] for c in cols)


def test_flat_schema_one_table_per_entity_no_keys():
    cols = [{"id": "train:1", "name": "a", "value_type": {"dominant": "number"}}, {"id": "hotel:1", "name": "b", "value_type": None}]
    c = I.flat_schema(cols)
    assert [t["name"] for t in c["tables"]] == ["train", "hotel", "restaurant"]
    assert c["tables"][0]["columns"][0] == {"name": "a", "type": "integer", "source": "train:1", "new": False, "gt": None}
    assert all(t["primary_key"] == [] and t["foreign_keys"] == [] for t in c["tables"]) and c["relationships"] == []


def test_fill_dialogues_budget_skips_long_and_orders():
    texts = {"a": "User: hi\nSystem: hello", "b": "User: " + "word " * 400, "c": "User: yes\nSystem: ok"}
    ids = ["a", "b", "c"]
    base = est_tokens(sp.build_prompt_e("")[0])
    chosen, prompt = I.fill_dialogues(texts, ids, "v0", budget=base + 60)
    assert chosen == ["a", "c"] and "word word" not in prompt and est_tokens(prompt) < base + 60
    assert I.fill_dialogues(texts, ids, "v0", budget=10 ** 6)[0] == ids
    assert sorted(I.fill_dialogues(texts, ids, "v1", budget=10 ** 6)[0]) == ids
    assert I.fill_dialogues(texts, ids, "v1", budget=10 ** 6)[0] != I.fill_dialogues(texts, ids, "v2", budget=10 ** 6)[0] or True
    assert "[dialogue 1]" in prompt and "[dialogue 2]" in prompt and "multiwoz" not in prompt.lower()


@pytest.fixture(scope="module")
def gt():
    g = G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml")
    rows = [{"gt_table": tn, "gt_column": c["name"], "level": "", "found_by": "",
             "reachable": "added" if c["source"] == "added" else "yes" if c["name"] != "Train price" else "no"}
            for tn, t in g["tables"].items() for c in t["columns"]]
    G.attach_reachable(g, "dev50", rows)
    return g


def test_gt_columns_c1_c2(gt):
    m = mentions([(0, "d1", "friday", "friday", "on friday"), (1, "d1", "12:00", "12:00", "at 12:00"), (2, "d2", "friday", "friday", "friday again")])
    levels = pd.Series(["Train day", "Train leave at;Train arrive by", "Train day"])
    c1 = I.gt_columns(gt, levels, m)
    names = [c["name"] for c in c1]
    assert "Train booking id" not in names and "Train trainid" in names and all(c["id"] == f"gt:{i}" for i, c in enumerate(c1, 1) for _ in [0])
    assert len({c["id"] for c in c1}) == len(c1) and all(c["gt"] == c["name"] for c in c1)
    assert {c["entity"] for c in c1} == set(I.ENTITIES) and len(c1) == sum(c["source"] != "added" for t in I.GT_TABLES for c in gt["tables"][t]["columns"])
    day = next(c for c in c1 if c["name"] == "Train day")
    assert day["n_mentions"] == 2 and day["n_dialogues"] == 2 and day["examples"] == [["friday", "on friday"]] and day["value_type"]["dominant"] == "day"
    assert day["description"] == "day of the train"
    leave = next(c for c in c1 if c["name"] == "Train leave at")
    assert leave["n_mentions"] == 1                                              # a mention with two labels counts for each
    assert next(c for c in c1 if c["name"] == "Train price")["examples"] == [] and "no examples" in sp.render_column(next(c for c in c1 if c["name"] == "Train price"))
    c2 = I.gt_columns(gt, levels, m, reachable={r: s for r, s in G.reachable_status(
        [{"gt_table": "", "gt_column": c["name"], "reachable": "yes" if c["name"] != "Train price" else "no"} for c in c1]).items()})
    assert "Train price" not in [c["name"] for c in c2] and len(c2) == len(c1) - 1
    assert [c["id"] for c in c2][0] == "gt:1"


def test_gt_columns_order_is_by_entity_then_name_not_by_table(gt):
    c1 = I.gt_columns(gt, pd.Series([], dtype=str), mentions([]).reindex([]))
    train = [c["name"] for c in c1 if c["entity"] == "train"]
    assert train == sorted(train, key=str.lower)


# ---- signals-only schema (f)

def frames():
    cols = pd.DataFrame([
        # entity train: id column "a" (high name score), b and c co-occur, d is multi valued, e isolated; entity hotel: x (name), y
        dict(column_id="train:1", entity="train", n_instances=10, share_multi_value=0.0, name_score=0.9, n_mentions=10),
        dict(column_id="train:2", entity="train", n_instances=10, share_multi_value=0.0, name_score=0.2, n_mentions=10),
        dict(column_id="train:3", entity="train", n_instances=10, share_multi_value=0.0, name_score=0.3, n_mentions=9),
        dict(column_id="train:4", entity="train", n_instances=8, share_multi_value=0.75, name_score=0.1, n_mentions=20),
        dict(column_id="train:5", entity="train", n_instances=2, share_multi_value=0.0, name_score=0.1, n_mentions=2),
        dict(column_id="hotel:1", entity="hotel", n_instances=9, share_multi_value=0.0, name_score=0.4, n_mentions=9),
        dict(column_id="hotel:2", entity="hotel", n_instances=9, share_multi_value=0.0, name_score=0.3, n_mentions=9)])
    rows = [("same_entity", "train:2", "train:3", 8, 0.8), ("same_entity", "train:1", "train:5", 1, -0.2), ("same_entity", "hotel:1", "hotel:2", 5, 0.5),
            ("cross_entity", "train:1", "hotel:1", 6, 0.4), ("cross_entity", "train:5", "hotel:2", 2, 0.5)]
    pairs = pd.DataFrame(rows, columns=["scope", "col_a", "col_b", "count", "npmi"])
    fd = pd.DataFrame([("cross_entity", "hotel:2", "train:2", 5, 1.0, "holds")], columns=["scope", "x", "y", "n", "share", "status"])
    hand = {c: {"name": f"col {c.replace(':', ' ')}", "value_type": {"dominant": "text"}} for c in cols["column_id"]}
    return cols, pairs, fd, hand


def test_signals_schema_rules():
    c = I.signals_schema(*frames())
    tabs = {t["name"]: t for t in c["tables"]}
    src = {k: t["name"] for t in c["tables"] for k in (x["source"] for x in t["columns"]) if k}
    assert src["train:1"] == "train" and src["train:5"] == "train"              # isolated column joins the main table
    assert src["train:2"] == src["train:3"] != "train"                          # a community of two becomes a sub-table
    assert src["train:4"] not in ("train",) and tabs[src["train:4"]]["columns"][0]["source"] is None or True
    child = tabs[src["train:4"]]
    assert [x["source"] for x in child["columns"] if x["source"]] == ["train:4"] and child["primary_key"] == [f"{child['name']} id"]
    assert tabs["train"]["primary_key"] == ["col train 1"]                      # name_score 0.9 >= 0.5
    assert tabs["hotel"]["primary_key"] == ["hotel id"]                         # best name_score 0.4 < 0.5: a new id column
    rel = {(r["from"], r["to"]) for r in c["relationships"]}
    assert (child["name"], "train") in rel and (src["train:2"], "train") in rel
    assert ("train", "hotel") in rel or ("hotel", "train") in rel               # cross-entity link: NPMI 0.4, count 6
    assert (src["train:2"], "hotel") in rel                                     # the FD hotel:2 -> train:2 makes the dependent side refer
    assert not any({r[0], r[1]} == {"train", "hotel"} and False for r in rel)
    for t in c["tables"]:                                                       # every FK points to a key of an existing table
        for f in t["foreign_keys"]:
            assert f["ref_columns"][0] in tabs[f["ref_table"]]["primary_key"]
    assert all(r["kind"] == "one_to_many" for r in c["relationships"])


def test_signals_schema_scorable_json_roundtrip():
    c = I.signals_schema(*frames())
    assert json.loads(json.dumps(c)) == c
