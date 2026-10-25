import json
from types import SimpleNamespace

import networkx as nx
import pandas as pd
import pytest

from s1a import draft_schema as ds
from s1a import schema_eval as se

GOLD_ATTRS = ["Train departure", "Train destination", "Train id", "Hotel name", "Hotel area"]


def _nodes():
    rows = [  # cluster_id, entity, n_values, pagerank, cardinality, status
        ("train#0", "train", 5, 0.4, 1.0, "kept"),
        ("train#1", "train", 5, 0.3, 1.5, "kept"),
        ("train#2", "train", 10, 0.5, 1.0, "kept"),
        ("train#3", "train", 3, 0.1, 1.0, "kept"),
        ("train#4", "train", 9, 0.9, 1.0, "dropped"),
        ("hotel#0", "hotel", 8, 0.6, 1.0, "kept"),
        ("hotel#1", "hotel", 3, 0.2, 1.0, "kept"),
    ]
    return pd.DataFrame(rows, columns=["cluster_id", "entity", "n_values", "pagerank", "cardinality", "status"])


def _export():
    vals = {"train#0": ["london", "london", "paris"], "train#1": ["rome"], "train#2": ["tr1"],
            "train#3": ["oslo"], "train#4": ["x"], "hotel#0": ["ritz"], "hotel#1": ["3"]}
    rows = []
    for cid, vs in vals.items():
        for i, v in enumerate(vs):
            rows.append(dict(cluster_id=cid, norm_value=v, text=v.upper(), context=f"ctx {v}",
                             dialogue_id="d1", turn=i, entity_gold=cid.split("#")[0]))
    clusters = pd.DataFrame({"cluster_id": list(vals), "top_values": ["|".join(dict.fromkeys(v)) for v in vals.values()]})
    return SimpleNamespace(mentions=pd.DataFrame(rows), clusters=clusters)


def _graphs():
    co = nx.Graph()
    co.add_nodes_from(["train#0", "train#1", "train#2", "train#3"])
    co.add_edge("train#0", "train#1", count=2, npmi=0.5)
    sim = nx.Graph()
    sim.add_edge("train#0", "train#1", cos=0.9)   # both in one instance -> keep apart
    sim.add_edge("train#0", "train#3", cos=0.8)   # never together -> merge
    sim.add_edge("train#1", "train#3", cos=0.5)   # below threshold
    cross = nx.Graph()
    cross.add_edge("train#2", "hotel#0", count=4, npmi=0.5)
    cross.add_edge("train#0", "hotel#1", count=9, npmi=0.1)   # npmi too low
    cross.add_edge("train#4", "hotel#0", count=9, npmi=0.9)   # dropped node
    cross.add_edge("train#0", "train#1", count=9, npmi=0.9)   # same entity
    return {"co": {"train": co, "hotel": nx.Graph()}, "sim": {"train": sim, "hotel": nx.Graph()}, "cross": cross}


@pytest.fixture
def schema():
    return ds.build(_export(), _graphs(), _nodes(), n_examples=2)


def test_identifier_and_forms(schema):
    t = schema["train"]
    assert t["identifier"]["cluster_id"] == "train#2"      # median 5; cands #0 #1 #2; top pagerank
    assert "median 5" in t["identifier"]["why"]
    assert set(t["attributes"]) == {"#train#0", "#train#1", "#train#3"}   # dropped #4 excluded
    assert t["attributes"]["#train#0"]["form"] == "column"
    assert t["attributes"]["#train#1"]["form"] == "table"
    assert t["attributes"]["#train#0"]["scores"]["pagerank"] == 0.4
    assert schema["hotel"]["identifier"]["cluster_id"] == "hotel#0"


def test_merge_keep_apart_sub_entities(schema):
    t = schema["train"]
    assert [h["nodes"] for h in t["merge_hints"]] == [["train#0", "train#3"]]
    assert [h["nodes"] for h in t["keep_apart"]] == [["train#0", "train#1"]]
    assert t["keep_apart"][0]["count"] == 2
    assert t["sub_entities"] == [{"nodes": ["train#0", "train#1"]}]


def test_relationships(schema):
    pairs = schema["relationships"]["pairs"]
    assert len(pairs) == 1
    p = pairs[0]
    assert p["entities"] == ["hotel", "train"] and p["n_node_pairs"] == 1 and p["max_npmi"] == 0.5
    assert sorted(p["example"]["nodes"]) == ["hotel#0", "train#2"]


def test_examples_distinct_first(schema):
    ex = schema["train"]["attributes"]["#train#0"]["examples"]
    assert sorted(e["text"] for e in ex) == ["LONDON", "PARIS"]
    assert ds.build(_export(), _graphs(), _nodes(), n_examples=2) == schema   # seeded


def test_write_and_markdown(schema, tmp_path):
    ds.write(schema, tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["hotel.json", "relationships.json", "train.json"]
    raw = (tmp_path / "train.json").read_bytes()
    assert raw.endswith(b"}\n") and b"\r" not in raw
    assert json.loads(raw)["identifier"]["cluster_id"] == "train#2"
    md = ds.to_markdown(schema)
    assert "## train" in md and "keep apart" in md and "hotel - train" in md


def test_evaluate(schema):
    labels = pd.DataFrame({
        "cluster_id": ["train#0", "train#1", "train#2", "train#3", "train#4", "hotel#0", "hotel#1"],
        "label": ["gold", "gold", "gold", "gold", "noise", "gold", "valid_new"],
        "gold_attr": ["Train departure", "Train destination", "Train id", "Hotel name", "", "Hotel name", ""],
    })
    r = se.evaluate(schema, _nodes(), labels, _export().mentions, GOLD_ATTRS)
    assert r["attr_coverage_n"] == 4 and r["attr_coverage"] == 0.8
    assert r["precision"] == 1.0 and r["precision_n"] == 6     # dropped noise node not counted
    assert r["K"] == 6 and r["K_gold"] == 5
    assert r["right_entity"] == 0.8 and r["right_entity_n"] == 5   # train#3 labelled Hotel name
    assert r["merge_precision"] == 0.0 and r["merge_precision_n"] == 1
    assert r["role_pairs_correct"] == 1.0 and r["role_pairs_correct_n"] == 1
    t = se.as_table({"gold": r, "spans": r})
    assert list(t.index) == ["gold", "spans"] and t.loc["gold", "K"] == 6
