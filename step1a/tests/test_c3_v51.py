"""wf_v5.1 C3: scripts/c3_score_v51.py (real R5 Step 3 scored on CPU) on the committed result files; no LLM, no encoder."""
import sys
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / "scripts")]

import c3_score_v51 as C  # noqa: E402
import gpu_v51 as G  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402

pytestmark = pytest.mark.skipif(not (C.R5 / "dev50" / "step3" / "manifest_clash.json").exists(), reason="R5 Step 3 not pulled")


def test_family_names_every_job_kind():
    assert [C.family(j) for j in ("accommodation_names_c_n50_s0", "x_clashq_c_n50_p0", "x_a_c_n50_s0", "x_splitk_E0-1_r1", "x_split_E0-1_r1",
                                  "x_reconcile_c_n50_p3")] == ["names", "clashq", "a", "splitk", "split", "reconcile/dupcheck"]


def test_call_rows_leave_assembled_rows_out_of_the_calls():
    rows = C.call_rows(C.R5, "v5.1")
    for dev in C.SETS:
        r = [x for x in rows if x["set"] == dev]
        assert sum(x["rows"] for x in r) > sum(x["calls"] for x in r) > 0
        assert {x["family"]: x["rows"] - x["calls"] for x in r if x["rows"] != x["calls"]} == {"a": 15, "split": 34 if dev == "dev50" else 27}
        assert sum(x["unguided_rows"] for x in r) == 0


def test_clash_rows_match_the_manifest_and_the_clash_log():
    rows = {d: C.clash_rows(d) for d in C.SETS}
    for s in C.clash_summary(rows):
        log = B.read_json(C.R5 / s["set"] / "step3" / "clash_log.json")["counts"]
        assert s["questions"] == len(rows[s["set"]]) == log.get("clash_same", 0) + log.get("clash_different", 0) + s["fallback"]
        assert s["same"] == log.get("clash_same", 0) and s["different"] == log.get("clash_different", 0)
        assert s["pairs_order0"] + s["pairs_order1"] + s["pairs_order2"] >= s["questions"]


def test_role_rows_count_only_pairs_in_the_gold_and_keep_the_order():
    f = lambda *a: {"found": set(a)}   # noqa: E731
    res = {(d, v, True): f("Train leave at", "Train arrive by") if v == "v5.0" else f("Train leave at", "Train arrive by", "Hotel address", "Restaurant address")
           for d in C.SETS for v in ("v5.0", "v5.1 Step 3 + split")}
    rows = C.role_rows(res)
    assert len(rows) == 10 and rows[0]["both found v5.0"] == "yes"
    hotel = [r for r in rows if r["pair"].startswith("Hotel")]
    assert [r["both found v5.0"] for r in hotel] == ["no", "no"] and [r["both found v5.1"] for r in hotel] == ["yes", "yes"]


def test_c1_count_alpha0_takes_nothing_and_lenient_adds_to_strict():
    rows = C.c1_count()
    for r in rows:
        assert r["strict_match"] + r["took_cached_decision"] + r["no_cached_cluster_holds_half"] == r["new_clusters"]
        if r["alpha"] == 0.0 and r["t"] == 0.4:
            assert r["took_cached_decision"] == 0 and r["strict_match"] == r["new_clusters"]
    assert any(r["took_cached_decision"] > 0 for r in rows)


def test_ctx_split_writes_to_out_and_not_to_the_run_folder(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(G.CS, "context_vectors", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(G.CS, "mention_table", lambda dev: None)
    monkeypatch.setattr(G.CS, "reassign", lambda parts, vec, *ctx: seen.setdefault("ctx", ctx) and {})
    monkeypatch.setattr(G.CS, "apply", lambda cols, parts, new: cols)
    run = G.SETS["dev50"]
    p = G.ctx_split("dev50", run, None, root=C.R5, out=tmp_path)
    assert p == tmp_path / "dev50" / "ctxsplit" / "final_columns.json" and p.exists() and seen["ctx"] == G.CTX
    assert B.read_json(p)[run] == B.read_json(C.R5 / "dev50" / "step3" / "scores" / "final_columns.json")[run]
