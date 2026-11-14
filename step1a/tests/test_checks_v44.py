"""wf_v4.4 T3 / T8 / T9 checks on tiny made-up rows: the missed-attribute classifier, per-job GPU minutes, the table-count trace, the sampler."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import t3_missed_v44 as T3  # noqa: E402
import t8_checks_v44 as T8  # noqa: E402
import t9_cost_v44 as T9  # noqa: E402
from s1a import log_v44 as L  # noqa: E402


# ---------------------------------------------------------------- T3
def order(o, name="x", failed=False, mates=()):
    return {"order": o, "batch": o + 1, "name": name, "failed": failed, "mates": list(mates)}


def cluster(cid, weight, vote="keep", names=("x", "x", "x"), failed=(), mates=(), split=""):
    return {"cid": cid, "weight": weight, "vote": vote, "split": split,
            "orders": [order(i, n, i in failed, mates if i == 0 else ()) for i, n in enumerate(names)]}


def facts(clusters, case="", purity=0.0, coverage=0.0, holds=None):
    return {"clusters": clusters, "case": case, "purity": purity, "coverage": coverage, "holds": holds or {}}


def test_not_attribute_when_half_of_the_weight_was_dropped():
    c = [cluster("E1#1", 3, vote="not_attribute", names=("not_attribute",) * 3), cluster("E1#2", 3, vote="keep")]
    assert T3.classify(facts(c, "mixed_only", 0.2))[0] == "not_attribute"      # 3 of 6 = 50%
    c[0]["weight"] = 2                                                          # 2 of 5 = 40%: no longer rule 1
    assert T3.classify(facts(c, "mixed_only", 0.2))[0] == "merged"


def test_unsure_and_cue_count_as_not_attribute():
    for vote in ("unsure", "attribute_cue"):
        assert T3.classify(facts([cluster("E1#1", 4, vote=vote)]))[0] == "not_attribute"


def test_bad_batch_beats_merged_but_not_not_attribute():
    failed = cluster("E1#1", 5, failed=(1,))
    assert T3.classify(facts([failed], "mixed_only", 0.3))[0] == "bad batch"
    dropped = cluster("E1#1", 5, vote="not_attribute", failed=(1,))
    assert T3.classify(facts([dropped], "mixed_only", 0.3))[0] == "not_attribute"


def test_bad_batch_needs_half_of_the_weight():
    c = [cluster("E1#1", 1, failed=(0,)), cluster("E1#2", 9)]
    assert T3.classify(facts(c, "mixed_only", 0.3))[0] == "merged"


def test_merged_reason_names_batch_mates_and_disagreement():
    c = [cluster("E0#1", 4, names=("destination", "departure", "departure"), mates=("E0#9",))]
    typ, why = T3.classify(facts(c, "mixed_only", 0.55, holds={"Train destination": 24, "Train departure": 17}))
    assert typ == "merged"
    assert "E0#9" in why and "Train destination 24" in why and "orders disagree on E0#1" in why
    typ, why = T3.classify(facts([cluster("E0#1", 4)], "mixed_only", 0.4, holds={"Hotel area": 6}))
    assert typ == "merged" and "different batches" in why and "all orders agree" in why


def test_low_purity_with_a_candidate_is_merged_but_spread_is_other():
    assert T3.classify(facts([cluster("E1#1", 4)], "", 0.4))[0] == "merged"
    typ, why = T3.classify(facts([cluster("E1#1", 4, vote="split", split="ran (2 parts)")], "spread", 0.67, 0.08))
    assert typ == "other" and "ran (2 parts)" in why and "0.08" in why


def test_no_candidate_at_all_is_other():
    assert T3.classify(facts([cluster("E1#1", 4)], "", 0.0, 0.0))[0] == "other"


def test_zero_weight_clusters_count_as_one():
    c = [cluster("E1#1", 0, vote="not_attribute"), cluster("E1#2", 0, vote="keep")]
    assert T3.classify(facts(c, "mixed_only", 0.2))[0] == "not_attribute"       # 1 of 2


def test_cluster_ids_drop_part_suffixes():
    assert T3._cluster_ids("E1#0|E1#11/1|E1#0/2") == ["E1#0", "E1#11"]
    assert T3._cluster_ids("") == []


def test_counts_by_type_keeps_every_type_and_groups():
    rows = [{"set": "a", "type": "merged"}, {"set": "a", "type": "other"}, {"set": "b", "type": "merged"}]
    assert T3.counts_by_type(rows) == {"not_attribute": 0, "bad batch": 0, "merged": 2, "other": 1}
    assert T3.counts_by_type(rows, "set")["b"]["merged"] == 1


# ---------------------------------------------------------------- T8
def row(job, batch_seconds, batch_size, retried=False, **extra):
    r = {"job": job, "batch_seconds": batch_seconds, "batch_size": batch_size, "retried": retried, "guided_finish_reason": None, "file": f"responses/{job}.jsonl"}
    return r | extra | {"job_seconds": L.job_seconds(r)}


def test_job_seconds_is_the_batch_share():
    assert L.job_seconds({"batch_seconds": 6.0, "batch_size": 3}) == 2.0
    assert L.job_seconds({"batch_seconds": 4.0, "batch_size": None}) == 4.0
    assert L.job_seconds({"batch_seconds": None, "batch_size": 3}) is None


def test_stage_and_set_of_job_names():
    assert T8.stage_of("hotel_names_v22d50_s0_b3") == "step3 names"
    assert T8.stage_of("train_v22d50b_split_E0-3_r1") == "step3 split"
    assert T8.stage_of("reconcile_dev50_hotel_E0-1p2_o0") == "step3 reconcile"
    assert T8.stage_of("dupcheck_dev50_rc0_hotel") == "step3 dupcheck"
    assert T8.stage_of("hotel_a_v22d50b_s1") == "step3 A answers"
    assert [T8.stage_of(f"a_llama43_dev50_s0_{k}") for k in ("p1", "p2", "r0_3", "k2")] == [
        "step4 pass 1 (tables)", "step4 pass 2 (assign)", "step4 pairs (links)", "step4 keys"]
    assert T8.set_of("hotel_names_v22d50b_s0_b1") == "dev50b" and T8.set_of("c1_dev50_s0_p1") == "dev50"


def test_per_job_minutes_sum_the_shares_of_one_batch():
    rows = [row(f"c1_dev50_s{i}_k0", 6.0, 3) for i in range(3)]               # one batch of 3 jobs, 6 s in all
    t = T8.per_job_table(rows)
    assert len(t) == 1 and t[0]["stage"] == "step4 keys" and t[0]["jobs"] == 3
    assert t[0]["seconds"] == 6.0 and t[0]["minutes"] == 0.1 and t[0]["mean_job_seconds"] == 2.0 and t[0]["lost"] == 0


def test_retried_v43_rows_are_flagged_lost_and_estimated_from_the_clean_rows():
    clean = [row("hotel_v22d50_split_E0-0_r1", 10.0, 5), row("hotel_v22d50_split_E0-1_r1", 10.0, 5)]       # 2 s each
    retried = [row("hotel_v22d50_split_E0-2_r1", 1.0, 1, retried=True)]                                      # only the retry: 1 s
    t = T8.per_job_table(clean + retried)[0]
    assert t["retried"] == 1 and t["lost"] == 1 and t["seconds"] == 5.0
    assert t["est_lost_seconds"] == 2.0 and t["minutes"] == round(7.0 / 60, 2)


def test_stage_with_only_retried_rows_has_an_unknown_estimate():
    t = T8.per_job_table([row("hotel_names_v22d50_s0_b1", 0.8, 1, retried=True)])[0]
    assert t["lost"] == 1 and t["est_lost_seconds"] is None and t["minutes"] == round(0.8 / 60, 2)


def test_v44_retried_rows_keep_both_calls_and_are_not_lost():
    r = row("hotel_names_v22d50_s0_b1", 5.0, 1, retried=True, guided_finish_reason="length")
    t = T8.per_job_table([r])[0]
    assert t["retried"] == 1 and t["lost"] == 0 and t["est_lost_seconds"] == 0.0


def test_rows_without_seconds_are_counted_apart():
    t = T8.per_job_table([row("hotel_a_v22d50_s0", None, None), row("hotel_a_v22d50_s1", None, None)])[0]
    assert t["jobs"] == 0 and t["no_seconds"] == 2 and t["seconds"] == 0 and t["mean_job_seconds"] is None


def test_per_set_split():
    rows = [row("c1_dev50_s0_k0", 2.0, 1), row("c1_dev50b_s0_k0", 4.0, 1)]
    t = {x["set"]: x["seconds"] for x in T8.per_job_table(rows, by_set=True)}
    assert t == {"dev50": 2.0, "dev50b": 4.0}


def test_table_origin_counts_link_tables_on_top_of_the_cap():
    tables = [{"name": n, "description": f"The {n} table."} for n in "abcdefg"]
    tables += [{"name": "a_b", "description": "Links a and b."}, {"name": "c_d", "description": "Links c and d."}]
    o = T8.table_origin({"tables": tables}, {"counts": {"p2_empty_table": 1}}, list("abcdefgh"), 8)
    assert o["tables"] == 9 and o["over_cap"] and o["links"] == ["a_b", "c_d"] and o["kept_pass1"] == 7
    assert o["pass1"] == 8 and o["cap_kept"] == 8 and o["dropped_empty"] == 1


def test_load_report_says_not_logged_then_reads_the_file(tmp_path):
    p = tmp_path / "model_load.json"
    assert T8.load_report(p) == "not logged"
    L.save_load_time(p, 93.4, "m", "r1")
    assert T8.load_report(p).startswith("93.4 s (1.6 min)")


# ---------------------------------------------------------------- T9
def test_sample_is_seeded_nested_and_capped_by_the_pool():
    ids = [f"D{i}" for i in range(20)]
    a, b = T9.sample_ids(ids, 5, 0), T9.sample_ids(ids, 12, 0)
    assert a == T9.sample_ids(ids, 5, 0) and b[:5] == a and len(set(b)) == 12 and a != T9.sample_ids(ids, 5, 1)
    with pytest.raises(ValueError, match="pool has 20"):
        T9.sample_ids(ids, 21, 0)


def test_pool_loader_refuses_other_splits(tmp_path):
    p = tmp_path / "pool.jsonl"
    p.write_text(json.dumps({"id": "A", "split": "test"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outside the pool splits"):
        T9.load_pool(p)
    p.write_text("\n".join(json.dumps({"id": i, "split": s}) for i, s in (("A", "train"), ("B", "val"))) + "\n", encoding="utf-8")
    assert [r["id"] for r in T9.load_pool(p)] == ["A", "B"]


def test_time_estimate_is_linear_in_dialogues():
    assert T9.time_estimate(300)["Step 1a + 2 (CPU, Colab)"] == tuple(round(x * 6, 1) for x in T9.STEP1A_MIN)
    assert T9.time_estimate(300)["model loading (GPU, once)"] == T9.LOAD_MIN


def test_count_run_reads_logs_clusters_and_columns(tmp_path):
    (tmp_path / "step3" / "responses").mkdir(parents=True)
    rows = [{"job": "j1", "prompt_tokens": 100, "output_tokens": 10, "retried": True}, {"job": "j2", "prompt_tokens": 50, "output_tokens": 5}]
    (tmp_path / "step3" / "responses" / "x.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (tmp_path / "run" / "spans").mkdir(parents=True)
    (tmp_path / "run" / "spans" / "clusters.csv").write_text("cluster_id,entity\nE0#0,E0\nE0#1,E0\nE1#0,E1\n", encoding="utf-8")
    (tmp_path / "cols.json").write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    c = T9.count_run([tmp_path / "step3"], tmp_path / "run", tmp_path / "cols.json", 999)
    assert c == {"corpus_tokens": 999, "calls": 3, "jobs": 2, "retries": 1, "tokens_in": 150, "tokens_out": 15, "clusters": 3, "entities": 2,
                 "final_columns": 2}
    assert T9.growth({"calls": 2, "tokens_in": 100}, {"calls": 6, "tokens_in": 300}) == {"calls": 3.0, "tokens_in": 3.0}
