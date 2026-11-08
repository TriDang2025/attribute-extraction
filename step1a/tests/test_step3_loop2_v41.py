import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from s1a import llm_cache as LC  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import step3_loop2_v41 as S3  # noqa: E402
import step3_loop2_v41 as SC  # noqa: E402

TEXT = "User: I need a train for 5 people.\nSystem: Booked 4 tickets for you.\nUser: How many tickets?"
TURNS = [(0, 34), (35, 69), (70, 93)]


def doc():
    return MN.Doc("D1", TEXT, TURNS, [], [])


def mention(mid, needle, turn, cid_hint=""):
    s = TEXT.index(needle)
    return dict(mention_id=mid, dialogue_id="D1", turn=turn, instance_id="D1|0", char_start=s, char_end=s + len(needle),
                text=needle, norm_value=needle.lower(), left_word="for", context="x", score=0.5)


def cluster(num, needles, keep=True, entity="train", stage1="E1"):
    ms = [mention(100 + 10 * num + i, n, t) for i, (n, t) in enumerate(needles)]
    return dict(id=f"L2_{entity}#{num}", entity=entity, stage1_entity=stage1, label=f"lab{num}", name=f"n{num}", keep=keep,
                reason="ok" if keep else "overlap", n_mentions=len(ms), mentions=ms)


def base_table():
    return pd.DataFrame([dict(mention_id=0, input="spans", dialogue_id="D1", turn=0, char_start=2, char_end=3, text="I",
                              norm_value="i", left_word="", context="", cluster_id="E1#0", entity="E1", entity_gold="train",
                              instance_id="D1|0", gold_attr="a", gliner_score=0.9)])


def base_inp():
    return PIN.PilotInput("E1", [], [("current entity E1", "d"), ("separate table", "d")], {"E2": [("E2#0", ["x", "y"])]})


CLUSTERS = [cluster(0, [("5 people", 0), ("4 tickets", 1)]), cluster(1, [("tickets", 2)], keep=False),
            cluster(10, [("4 tickets", 1), ("5 people", 0)])]


def test_select_clusters_kept_or_all():
    empty = dict(CLUSTERS[0], id="L2_train#5", mentions=[])
    assert [c["id"] for c in S3.select_clusters(CLUSTERS + [empty])] == ["L2_train#0", "L2_train#10"]
    assert len(S3.select_clusters(CLUSTERS + [empty], include_dropped=True)) == 3


def test_merge_is_a_copy_with_loop2_ids_and_checks_collisions():
    base = base_table()
    merged = S3.merge_mentions(base, CLUSTERS)
    assert len(base) == 1 and len(merged) == 1 + 5
    row = merged[merged["mention_id"] == 100].iloc[0]
    assert row["cluster_id"] == "L2_train#0" and row["entity"] == "E1" and row["entity_gold"] == ""
    with pytest.raises(ValueError, match="not unique"):
        S3.merge_mentions(base.assign(mention_id=100), CLUSTERS)
    with pytest.raises(ValueError, match="stage1_entity"):
        S3.merge_mentions(base, [dict(CLUSTERS[0], stage1_entity=None)])


def test_l2_input_examples_values_and_order():
    merged = S3.merge_mentions(base_table(), CLUSTERS)
    inp = S3.l2_input(base_inp(), merged, CLUSTERS)
    assert inp.entity == "E1" and inp.options == base_inp().options and inp.others == base_inp().others
    assert [c.cluster_id for c in inp.clusters] == ["L2_train#0", "L2_train#1", "L2_train#10"]   # numeric, not text, order
    c0 = inp.clusters[0]
    assert (c0.n_mentions, c0.n_values, c0.low_conf) == (2, 2, False)
    assert [e for e, _ in c0.examples] == ["L2_train#0:0", "L2_train#0:1"]
    assert {m for _, m in c0.examples} == {100, 101}
    with pytest.raises(ValueError, match="belongs to"):
        S3.l2_input(base_inp(), merged, [dict(CLUSTERS[0], stage1_entity="E2")])


def test_frozen_render_and_schema_accept_loop2_clusters():
    merged = S3.merge_mentions(base_table(), CLUSTERS)
    inp = S3.l2_input(base_inp(), merged, CLUSTERS)
    export = MN.Export(merged, pd.DataFrame(), pd.DataFrame(), None, None)
    text = PIN.render_v2(inp, export, {"D1": doc()}, "v2")
    assert "### L2_train#0  (mentions 2, distinct values 2)" in text and "[[5 people]]" in text
    assert "- L2_train#10:0 [" in text and "Entity E1: 3 clusters." in text
    ids = LC.schema_enum(PIN.schema_v2(inp), "cluster_id")
    assert ids == ["L2_train#0", "L2_train#1", "L2_train#10"]
    assert PIN.render_v2(inp, export, {"D1": doc()}, "v2", order_seed=1).count("### L2_train#") == 3


def answer(cids, names, actions=None):
    attrs = [{"name": n, "description": "d", "role": "r"} for n in dict.fromkeys(n for n in names if n != "not_attribute")]
    return {"attributes": attrs, "clusters": [dict(cluster_id=c, attribute=n, evidence="e", mixed=False, placement="current entity E1")
                                              for c, n in zip(cids, names)]}


def test_l2_ids_survive_the_frozen_parser_decisions_and_vote():
    cids = ["L2_train#0", "L2_train#1", "L2_train#10"]
    raw = json.dumps(answer(cids, ["num_people", "not_attribute", "num_people"]))
    parsed, errs, n = LC.parse_job(raw, "v2", {"properties": {"cluster_id": {"enum": cids}}})
    assert errs == [] and n == 3
    t = S3.order_table(parsed, cids, "s0")
    assert list(t["action"]) == ["merge", "not_attribute", "merge"] and t.iloc[0]["merge_with"] == '["L2_train#10"]'
    dec, stats = S3.voted_table([t, S3.order_table(parsed, cids, "s1")])
    rows = S3.answer_rows(dec, CLUSTERS)
    assert [r["name"] for r in rows] == ["num_people", "", "num_people"] and rows[1]["keep"] is False
    assert stats["agree_mean"] == 1.0


def test_check_reads_responses_and_writes_the_table(tmp_path, monkeypatch):
    monkeypatch.setattr(SC.paths, "RESULTS", tmp_path)
    odir = tmp_path / "wf_v41" / "step3_loop2" / "dev50"
    (tmp_path / "wf_v41" / "loop2" / "dev50").mkdir(parents=True)
    (tmp_path / "wf_v41" / "loop2" / "dev50" / "clusters.json").write_text(json.dumps(CLUSTERS), encoding="utf-8")
    cids = ["L2_train#0", "L2_train#1", "L2_train#10"]
    (odir / "prompts").mkdir(parents=True)
    (odir / "responses").mkdir()
    jobs = [SC.job_row("train", "E1", "dev50", s, 8, True, 1000) for s in SC.SEEDS]
    (odir / "manifest.json").write_text(json.dumps({"include_dropped": True, "jobs": jobs}), encoding="utf-8")
    schema = json.dumps({"properties": {"cluster_id": {"enum": cids}}})
    for j in jobs[:2]:                      # the third order has no response yet
        (odir / j["schema"]).write_text(schema, encoding="utf-8")
        (odir / "responses" / f"{j['job']}.jsonl").write_text(
            json.dumps({"key": "k", "parsed": answer(cids, ["num_people", "num_people", "not_attribute"])}) + "\n", encoding="utf-8")
    (odir / jobs[2]["schema"]).write_text(schema, encoding="utf-8")
    SC.check(type("A", (), {"set": "dev50"})())
    text = (odir / "answers.md").read_text(encoding="utf-8")
    assert "DRY RUN" in text and "| L2_train#0 | lab0 | keep | num_people | merge | current entity E1 |" in text
    assert "no response in responses/train_a_l2_dev50_s2.jsonl" in text and "2 orders" in text


def test_job_rows_have_the_frozen_a_shape():
    row = SC.job_row("train", "E1", "dev50", 2, 8, False, 3000)
    assert row["job"] == "train_a_l2_dev50_s2" and row["family"] == "a" and row["format"] == "v2" and row["run_tag"] == "s2"
    assert row["max_tokens"] == SC.max_tokens(3000)
    assert row["include_dropped"] is False and row["run"] == "l2_dev50"
