from s1a import nojoin_v50 as NJ


def test_unjoin_splits_multi_cluster_column_and_keeps_parts():
    cols = [{"cid": 1, "name": "location", "groups": ["g"], "members": ["A@g", "B@g", "A@A/1"], "mention_ids": [1, 2, 3, 4]},
            {"cid": 2, "name": "price", "groups": ["C"], "members": ["C@C"], "mention_ids": [5]}]
    cluster_of = {1: "A", 2: "A", 3: "B", 4: "A", 5: "C"}
    out = NJ.unjoin(cols, cluster_of, {"B": "pickup location"})
    assert [(c["cid"], c["name"], c["mention_ids"]) for c in out] == [
        (1, "location", [1, 2, 4]), (3, "pickup location", [3]), (2, "price", [5])]
    assert out[0]["members"] == ["A@g", "A@A/1"] and out[1]["unjoined_from"] == 1


def test_unjoin_fallback_name():
    cols = [{"cid": 4, "name": "time", "groups": ["g"], "members": ["A@g", "B@g"], "mention_ids": [1, 2]}]
    out = NJ.unjoin(cols, {1: "A", 2: "B"}, {})
    assert out[1]["name"] == "time B"
