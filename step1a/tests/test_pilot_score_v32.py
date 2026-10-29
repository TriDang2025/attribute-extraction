import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import pilot_score as PS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a.pilot_input import est_tokens  # noqa: E402


def job(name, kind, variant, tag, cid=""):
    return {"job": name, "ent": "train", "entity": "E1", "kind": kind, "variant": variant, "run_tag": tag,
            "cluster_id": cid, "prompt": f"prompts/{name}.txt"}


JOBS32 = [job("n_s0", "entity", "nbhd", "s0"), job("n_s1", "entity", "nbhd", "s1"), job("n_s2", "entity", "nbhd", "s2"),
          job("sp_1", "split", "split", "r1", "E1#1"), job("sp_2", "split", "split", "r1", "E1#2"),
          job("no_1", "noise", "noise", "r1", "E1#1"), job("ga_1", "gate", "gate", "r1", "E1#1"),
          job("ga_2", "gate", "gate", "r1", "E1#2"), job("rc_a0", "reconcile", "reconcile", "r1")]
JOBS31 = [job("v_r1", "entity", "v2", "r1"), job("v_r2", "entity", "v2", "r2"), job("nh_r1", "entity", "nohints", "r1"),
          job("s31_1", "split", "split", "r1", "E1#1"), job("s31_2", "split", "split", "r2", "E1#1")]


def names(jobs):
    return sorted(j["job"] for j in jobs)


def test_variant_jobs_follow_the_contract():
    assert names(PS.variant_jobs(JOBS31, "A")) == ["s31_1", "v_r1"]
    assert names(PS.variant_jobs(JOBS32, "B")) == ["n_s0", "sp_1", "sp_2"]
    assert names(PS.variant_jobs(JOBS32, "C")) == ["n_s0", "n_s1", "n_s2", "sp_1", "sp_2"]
    # D: 3 orders + noise + gate + the split jobs of failed gates + reconcile
    assert names(PS.variant_jobs(JOBS32, "D", gate_failed=["E1#2"])) == [
        "ga_1", "ga_2", "n_s0", "n_s1", "n_s2", "no_1", "rc_a0", "sp_2"]
    assert not [j for j in PS.variant_jobs(JOBS32, "D") if j["kind"] == "split"]
    with pytest.raises(ValueError):
        PS.variant_jobs(JOBS32, "E")


def test_token_row_measured_and_estimated():
    r = PS.token_row("train", "B", "j", {"prompt_tokens": 100, "output_tokens": 20, "raw": "x" * 700}, "p" * 3500)
    assert (r["prompt_tokens"], r["output_tokens"], r["estimated"]) == (100, 20, False)
    r = PS.token_row("train", "B", "j", {"raw": "x" * 700}, "p" * 3500)
    assert (r["prompt_tokens"], r["output_tokens"], r["estimated"]) == (est_tokens("p" * 3500), 200, True)
    r = PS.token_row("train", "B", "j", {"prompt_tokens": 100, "raw": "x" * 70}, "p" * 3500)  # output count missing
    assert (r["prompt_tokens"], r["output_tokens"], r["estimated"]) == (100, 20, True)
    r = PS.token_row("train", "B", "j", None, "p" * 35)
    assert (r["prompt_tokens"], r["output_tokens"], r["estimated"]) == (10, 0, True)


def test_token_table_sums_x_a_and_recall_per_100k():
    def row(ent, v, p, o, est=False):
        return {"ent": ent, "variant": v, "job": "j", "prompt_tokens": p, "output_tokens": o, "estimated": est}
    rows = [row("train", "A", 1000, 100), row("train", "A", 800, 100, True), row("train", "B", 3000, 200),
            row("train", "B", 2000, 100), row("hotel", "A", 500, 0), row("hotel", "B", 1000, 0)]
    t = PS.token_table(rows, {("train", "A"): 0.5, ("train", "B"): 0.6, ("hotel", "A"): 0.4})
    g = t.set_index(["ent", "variant"])
    assert g.loc[("train", "A"), ["calls", "prompt_tokens", "output_tokens", "total"]].tolist() == [2, 1800, 200, 2000]
    assert bool(g.loc[("train", "A"), "estimated"]) and not bool(g.loc[("train", "B"), "estimated"])
    assert g.loc[("train", "B"), "total"] == 5300
    assert g.loc[("train", "A"), "x_A"] == 1.0
    assert g.loc[("train", "B"), "x_A"] == pytest.approx(5300 / 2000)
    assert g.loc[("train", "A"), "recall_per_100k"] == pytest.approx(0.5 / 2000 * 1e5)
    assert math.isnan(g.loc[("hotel", "B"), "recall_per_100k"])  # no recall given
    assert g.loc[("all", "B"), "total"] == 6300 and g.loc[("all", "A"), "total"] == 2500
    assert g.loc[("all", "B"), "x_A"] == pytest.approx(6300 / 2500)
    assert math.isnan(g.loc[("all", "A"), "recall"])
    md = PS.render_tokens(t)
    assert "| train | B | 2 | 5000 | 300 | 5300 | 2.650 |" in md and "| train | A |" in md and "yes" in md


def test_token_table_without_variant_a_gives_nan_x_a():
    t = PS.token_table([{"ent": "train", "variant": "B", "prompt_tokens": 10, "output_tokens": 5, "estimated": False}])
    assert math.isnan(t["x_A"].iloc[0])


def test_render_scores_blocks_are_optional():
    res = {"A r1": {"recall_before": 0.1}}
    old = PS.render_scores(res, None, "E1", "n")
    assert "## Context" in old and "## Stability" in old
    new = PS.render_scores(res, None, "E1", "n", pair=None, stab_pair=None)
    assert "## Context" not in new and "## Stability" not in new and "## Comparison" in new


def test_token_rows_and_variant_a_decisions_match_v31(tmp_path):
    pc = pytest.importorskip("s1a.pilot_combine")  # written in parallel by W2
    assert pc
    import pilot_eval_v31 as v31
    import pilot_eval_v32 as v32
    assert v32._decisions is v31._decisions  # variant A goes through the v3.1 path unchanged

    d = tmp_path
    (d / "responses").mkdir()
    (d / "prompts").mkdir()
    obj = {"attributes": [{"name": "day", "description": "d", "role": "r"}],
           "clusters": [{"cluster_id": "E1#0", "attribute": "day", "evidence": "e", "mixed": False, "placement": "p"},
                        {"cluster_id": "E1#1", "attribute": "day", "evidence": "e", "mixed": False, "placement": "p"}]}
    j = dict(JOBS31[0], format="v2")
    (d / "responses" / "v_r1.jsonl").write_text(json.dumps({"parsed": obj, "prompt_tokens": 7, "output_tokens": 3}) + "\n")
    dec = v32._decisions(j, d / "responses" / "v_r1.jsonl", ["E1#0", "E1#1"], {})
    assert dec["action"].tolist() == ["merge", "merge"]
    assert dec.equals(PV.decisions_from_v2(obj, ["E1#0", "E1#1"], "v2", "r1", None, require_mixed=False))

    # token rows: one measured response, one estimated (prompt file read), one missing response skipped
    (d / "responses" / "n_s0.jsonl").write_text(json.dumps({"raw": "x" * 70}) + "\n")
    (d / "prompts" / "n_s0.txt").write_text("p" * 350)
    rows = v32.token_rows("train", "B", JOBS32, d)
    assert [(r["job"], r["prompt_tokens"], r["output_tokens"], r["estimated"]) for r in rows] == [("n_s0", 100, 20, True)]
    rows = v32.token_rows("train", "A", JOBS31, d)
    assert [(r["job"], r["prompt_tokens"], r["output_tokens"], r["estimated"]) for r in rows] == [("v_r1", 7, 3, False)]
