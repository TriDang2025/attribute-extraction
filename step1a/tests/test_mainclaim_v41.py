import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mainclaim_v41 as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GOLD = {"train": ["Train day", "Train leave at"], "hotel": ["Hotel name"], "restaurant": ["Restaurant food"]}
CFG = json.loads(M.NAME_MATCH.read_text(encoding="utf-8"))


def test_top_label_and_found_rule():
    assert M.top_label([["A"], ["A"], []]) == ("A", pytest.approx(2 / 3))
    assert M.top_label([[], [], ["A"]]) == ("", pytest.approx(2 / 3))   # an empty label counts
    assert M.top_label([["B", "A"]]) == ("A", 1.0)                      # tie: by name
    assert M.top_label([]) == ("", 0.0)
    total = M.totals([["Train day"]] * 10 + [["Train leave at"]] * 2)
    pure = [["Train day"]] * 3
    mixed = [["Train day"], [], []]
    tiny = [["Train leave at"]]                                          # pure, 1 of 2 mentions of the attribute
    assert M.found_in_groups([pure], total, set(GOLD["train"])) == {"Train day"}
    assert M.found_in_groups([mixed], total, set(GOLD["train"])) == set()     # purity 1/3
    assert M.found_in_groups([tiny], total, set(GOLD["train"])) == {"Train leave at"}
    assert M.found_in_groups([[["Train day"]]], total, set(GOLD["train"])) == {"Train day"}   # coverage 1/10 = 0.1 is enough
    assert M.found_in_groups([pure], total, {"Train leave at"}) == set()      # not in the gold list


def test_found_coverage_cut():
    total = M.totals([["Train day"]] * 20)
    assert M.found_in_groups([[["Train day"]]], total, {"Train day"}) == set()          # 1/20 < 0.10
    assert M.found_in_groups([[["Train day"]] * 2], total, {"Train day"}) == {"Train day"}


def test_rebuild_groups_merges_parts_of_one_cluster():
    col = {"mention_ids": [1, 2, 3, 4], "members": [{"cluster": "E1#1", "group": "E1#1/0"}, {"cluster": "E1#1", "group": "E1#1/1"},
                                                     {"cluster": "E1#2", "group": "E1#2"}]}
    assert M.rebuild_groups(col, {1: "E1#1", 2: "E1#1", 3: "E1#2", 4: "E1#2"}) == [[1, 2], [3, 4]]
    col = {"mention_ids": [1, 2, 3], "members": [{"cluster": "E1#1", "group": "g"}, {"cluster": "E1#2", "group": "g"}]}
    assert M.rebuild_groups(col, {1: "E1#1", 2: "E1#2", 3: "E1#2"}) == [[1, 2, 3]]


@pytest.mark.parametrize("set_name", ["dev50", "dev50b"])
def test_loop1_found_equals_step3(set_name):
    handover, mt, labels, gold = M.load_set(set_name)
    s = M.summarize_loop("loop1", M.loop1_items(handover, mt, labels), M.entity_totals(handover, mt, labels), gold)
    k, n = M.STEP3_FOUND[set_name]
    assert sum(len(s["found"][e] & set(gold[e])) for e in gold) == k
    assert sum(len(g) for g in gold.values()) == n


def fake_clusters(tmp_path, entity="train", keep=True, wrap=False, **extra):
    ms = [{"dialogue_id": "PMUL0001.json", "turn": 2, "text": "Friday"}, {"dialogue_id": "PMUL0002", "turn": 1, "text": "Monday", "norm_value": "monday"}]
    rec = {"id": "L2:train#0", "entity": entity, "label": "travel day", "keep": keep, "mentions": ms, **extra}
    p = tmp_path / "clusters.json"
    p.write_text(json.dumps({"clusters": [rec]} if wrap else [rec]), encoding="utf-8")
    return p


def test_read_loop2_adapter(tmp_path):
    for wrap in (False, True):
        c = M.read_loop2(fake_clusters(tmp_path, wrap=wrap))
        assert c[0]["name"] == "travel day" and c[0]["keep"] is True
        assert [m["dialogue_id"] for m in c[0]["mentions"]] == ["PMUL0001", "PMUL0002"]
        assert [m["norm_value"] for m in c[0]["mentions"]] == ["friday", "monday"]
    assert M.read_loop2(fake_clusters(tmp_path, entity="E1"), {"E1": "train"})[0]["entity"] == "train"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"id": "x", "entity": "train", "mentions": []}]), encoding="utf-8")
    with pytest.raises(ValueError, match="keep"):
        M.read_loop2(bad)


def test_loop2_labels_found_and_new(tmp_path):
    tear_map = {"Train day": "train-day"}
    span_idx = {"PMUL0001": {"friday": [("train", "day")]}, "PMUL0002": {"monday": [("hotel", "bookday"), ("train", "day")]}}
    clusters = M.read_loop2(fake_clusters(tmp_path))
    items, extra, unl = M.loop2_items(clusters, {}, span_idx, tear_map)
    assert unl == 0 and [it["groups"] for it in items] == [[[["Train day"], ["Train day"]]]]   # the entity's own domain wins
    assert extra == {"train": [["Train day"], ["Train day"]]}
    # a loop-1 mention with the same key gives its labels and is not added to the denominator
    items, extra, _ = M.loop2_items(clusters, {("PMUL0001", 2, "friday"): ["Train leave at"]}, span_idx, tear_map)
    assert items[0]["groups"][0][0] == ["Train leave at"] and len(extra["train"]) == 1
    # a dropped cluster gives no item but its mentions count in the denominator
    dropped = M.read_loop2(fake_clusters(tmp_path, keep=False))
    items, extra, _ = M.loop2_items(dropped, {}, span_idx, tear_map)
    assert items == [] and len(extra["train"]) == 2
    # no spans: unlabelled, and the item is new
    items, _, unl = M.loop2_items(clusters, {}, None, tear_map)
    assert unl == 2 and M.is_new(items[0], {"Train day"})[0]


def test_summaries_compare_and_blind_sheet():
    gold = {"train": ["Train day", "Train leave at"], "hotel": ["Hotel name"], "restaurant": []}
    gold_all = {"Train day", "Train leave at", "Hotel name"}
    a = M.item("loop1", "train", "travel day", "train:1", [[["Train day"]] * 4], ["friday"] * 4)
    b = M.item("loop1", "hotel", "mystery", "hotel:1", [[[], ["Hotel fax"], []]], ["x", "x", "y"])
    c = M.item("loop2", "hotel", "hotel name", "L2:hotel#0", [[["Hotel name"]] * 3], ["a b", "c d", "a b"])
    s1 = M.summarize_loop("loop1", [a, b], {"train": M.totals(M.item_labels(a)), "hotel": M.totals(M.item_labels(b))}, gold)
    assert s1["found"]["train"] == {"Train day"} and s1["found"]["hotel"] == set() and [i["id"] for i in s1["new"]] == ["hotel:1"]
    s2 = M.summarize_loop("loop2", [a, b, c], {"train": M.totals(M.item_labels(a)), "hotel": M.totals(M.item_labels(b) + M.item_labels(c))}, gold)
    assert s2["found"]["hotel"] == {"Hotel name"}
    rows = {(r["source"], r["entity"]): r for r in M.compare_rows("dev50", gold, [s1, s2])}
    assert (rows["loop1", "all"]["found_k"], rows["loop1", "all"]["gold_n"]) == (1, 3)
    assert (rows["loop2", "all"]["found_k"], rows["loop2", "all"]["new_items"], rows["loop2", "all"]["new_mentions"]) == (2, 1, 3)
    sheet, key = M.sheet_rows([s1, s2], gold, CFG)
    assert len(sheet) == 1 and list(sheet.columns) == M.SHEET_COLS   # the loop-1 item is listed once; no method, no GT label column
    assert sheet.iloc[0]["example_values"] == "x | y" and sheet.iloc[0]["real"] == ""
    assert key.iloc[0]["majority_gt_L2"] == "" and key.iloc[0]["item_id"] == "hotel:1" and key.iloc[0]["source"] == "loop1"
    md = M.compare_md("dev50", gold, [s1, s2], list(rows.values()), ["a note"])
    assert "1/3 (0.333)" in md and "- a note" in md


def test_tear_items():
    gold = {"train": ["Train day"], "hotel": ["Hotel name"], "restaurant": ["Taxi phone"]}
    cols = pd.DataFrame([
        {"column": "Train day", "ent": "train", "n_cells": 3, "final_label": "Train day"},
        {"column": "Taxi phone", "ent": "taxi", "n_cells": 2, "final_label": "Taxi phone"},
        {"column": "Hotel pets", "ent": "hotel", "n_cells": 4, "final_label": ""},
        {"column": "Hotel fax", "ent": "hotel", "n_cells": 1, "final_label": "Hotel fax"},
        {"column": "Attraction type", "ent": "attraction", "n_cells": 5, "final_label": "Attraction type"}])
    found, new, skipped = M.tear_items(cols, {"Hotel pets": ["yes", "no"]}, gold)
    assert found == {"train": {"Train day"}, "hotel": set(), "restaurant": {"Taxi phone"}} and skipped == 1
    assert [(i["name"], len(M.item_labels(i)), i["values"]) for i in new] == [("Hotel pets", 4, ["yes", "no"]), ("Hotel fax", 1, [])]


def test_cli_loop1_and_fake_loop2(tmp_path):
    handover, mt, labels, gold = M.load_set("dev50")
    s = M.summarize_loop("loop1", M.loop1_items(handover, mt, labels), M.entity_totals(handover, mt, labels), gold)
    missing = sorted(set(gold["train"]) - s["found"]["train"])[0]          # a train attribute that loop 1 does not find
    ids = [i for i, ls in labels.items() if ls == [missing]]
    ments = [{"dialogue_id": mt.loc[i, "dialogue_id"], "turn": int(mt.loc[i, "turn"]), "text": mt.loc[i, "norm_value"]} for i in ids]
    p = tmp_path / "clusters.json"
    p.write_text(json.dumps([{"id": "L2:train#0", "entity": "train", "keep": True, "name": "x", "mentions": ments}]), encoding="utf-8")
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "mainclaim_v41.py"), "--set", "dev50", "--loop2", str(p), "--tear", str(tmp_path / "none.jsonl"),
                        "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    cmp = pd.read_csv(out / "dev50" / "compare.csv")
    allrow = cmp[cmp["entity"] == "all"].set_index("source")
    assert allrow.loc["loop1", "found_k"] == 31 and allrow.loc["loop2", "found_k"] == 32
    md = (out / "dev50" / "compare.md").read_text(encoding="utf-8")
    assert "TEAR: skipped" in md and "Loop 2: 1 clusters, 1 kept" in md
    for f in ("human_check_sheet.csv", "human_check_key.csv"):
        assert (out / "dev50" / f).exists()
    assert "gt" not in " ".join(pd.read_csv(out / "dev50" / "human_check_sheet.csv").columns).lower()


def test_name_match():
    gold = {"hotel": ["Hotel internet", "Hotel parking", "Hotel type", "Hotel price range"],
            "restaurant": ["Restaurant phone", "Taxi phone", "Taxi type", "Restaurant food"]}
    nm = lambda n, e="hotel": M.name_match(n, e, gold, CFG)   # noqa: E731
    assert [nm(n) for n in ("internet access", "has wifi", "free wi-fi", "Hotel internet", "parking available", "hotel_parking")] ==         ["Hotel internet"] * 4 + ["Hotel parking"] * 2
    assert nm("room type") == "" and nm("price") == "" and nm("price range") == "Hotel price range" and nm("internet") == "Hotel internet"
    assert nm("internet", "restaurant") == ""                                  # same entity only
    assert nm("restaurant type", "restaurant") == ""                           # a prefix word must be the gold's own
    assert nm("phone", "restaurant") == "Restaurant phone" and nm("taxi phone", "restaurant") == "Taxi phone"
    assert M.blind_name("Hotel pets", "hotel", gold) == "pets" and M.blind_name("hotel", "hotel", gold) == "hotel"


def test_parse_real_and_merge_answers():
    assert [M.parse_real(v) for v in ("yes", " Y ", "no", "0", "", None, float("nan"))] == [True, True, False, False, None, None, None]
    with pytest.raises(ValueError):
        M.parse_real("maybe")
    new = pd.DataFrame({"id": [1, 2], "entity": ["hotel"] * 2, "attribute": ["a", "b"], "example_values": ["x", ""], "real": ["", ""]})
    assert M.merge_answers(new, None) is new and M.merge_answers(new, new.copy()) is new          # nothing filled: the new sheet
    old = new.assign(real=["yes", ""])
    assert list(M.merge_answers(new, old)["real"]) == ["yes", ""]
    with pytest.raises(ValueError, match="does not match"):
        M.merge_answers(new.assign(attribute=["a", "c"]), old)


def test_blind_shuffled_sheet_and_human_found():
    gold = {"train": [], "hotel": ["Hotel internet", "Hotel parking"], "restaurant": []}
    l1 = [M.item("loop1", "hotel", f"col {i}", f"hotel:{i}", [[[]]], ["v"]) for i in range(6)]
    l2 = [M.item("loop2", "hotel", "internet access", "L2:hotel#0", [[[], []]], ["free wifi", "wifi"]),
          M.item("loop2", "hotel", "parking available", "L2:hotel#1", [[[]]], ["parking"])]
    s1 = {"source": "loop1", "found": {}, "new": l1, "n_items": {}}
    s2 = {"source": "loop2", "found": {"hotel": set()}, "new": l1 + l2, "n_items": {}}
    tear = {"source": "tear", "found": {}, "new": [M.item("tear", "hotel", "Hotel internet", "Hotel internet", [[[]]], ["yes"])], "n_items": {}}
    sheet, key = M.sheet_rows([s1, s2, tear], gold, CFG)
    assert len(sheet) == 9 and list(sheet["id"]) == list(range(1, 10))
    assert list(key["source"]) != sorted(key["source"], key=M.SOURCES.index)                # shuffled, not grouped by method
    assert M.sheet_rows([s1, s2, tear], gold, CFG)[1].equals(key)                           # fixed seed
    assert "tear" not in sheet.to_csv() and "loop" not in sheet.to_csv()
    by_item = dict(zip(key["item_id"], key["id"]))
    answers = {i: None for i in key["id"]} | {by_item["L2:hotel#0"]: True, by_item["L2:hotel#1"]: False, by_item["Hotel internet"]: True}
    fh = M.human_found([s1, s2, tear], key, answers)
    assert fh == {"loop1": {}, "loop2": {"hotel": {"Hotel internet"}}, "tear": {"hotel": {"Hotel internet"}}}
    rows = {(r["source"], r["entity"]): r for r in M.compare_rows("dev50", gold, [s1, s2, tear], fh)}
    assert (rows["loop2", "all"]["found_k"], rows["loop2", "all"]["found_human_k"], rows["tear", "all"]["found_human_k"]) == (0, 1, 1)
    md = M.compare_md("dev50", gold, [s1, s2, tear], list(rows.values()), [], fh, (3, 9))
    assert "1/2 (0.500)" in md and "3/9 rows checked" in md and "| hotel | Hotel internet | no | check | check |" in md


def test_cli_keeps_filled_answers(tmp_path):
    p = tmp_path / "clusters.json"
    p.write_text(json.dumps([{"id": "L2_hotel#0", "entity": "hotel", "keep": True, "name": "internet access",
                              "mentions": [{"dialogue_id": "XX0001", "turn": 1, "text": "free wifi"}]}]), encoding="utf-8")
    args = [sys.executable, "-I", str(ROOT / "scripts" / "mainclaim_v41.py"), "--set", "dev50", "--loop2", str(p), "--spans", "--out", str(tmp_path / "out")]
    assert subprocess.run(args, capture_output=True, text=True).returncode == 0
    d = tmp_path / "out" / "dev50"
    key = pd.read_csv(d / "human_check_key.csv", keep_default_na=False)
    sheet = pd.read_csv(d / "human_check_sheet.csv", keep_default_na=False)
    sheet.loc[sheet["id"] == key.loc[key["item_id"] == "L2_hotel#0", "id"].iloc[0], "real"] = "yes"
    sheet.to_csv(d / "human_check_sheet.csv", index=False)
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    allrow = pd.read_csv(d / "compare.csv").query("entity == 'all'").set_index("source")
    assert allrow.loc["loop2", "found_k"] == 31 and allrow.loc["loop2", "found_human_k"] == 32 and allrow.loc["loop1", "found_human_k"] == 31
    assert "yes" in pd.read_csv(d / "human_check_sheet.csv", keep_default_na=False)["real"].tolist()   # the answer survived the rerun
