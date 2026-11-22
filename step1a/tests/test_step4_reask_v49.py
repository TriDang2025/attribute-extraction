"""wf_v4.9 A+R: re-ask a pass-2 batch that drops an entity (s1a/step4_reask_v49.py, chain key p2_reask of s1a/step4_v44.py), fake model only."""
import json

import pytest

from s1a import batch_v4 as B
from s1a import step4_reask_v49 as RA
from s1a import step4_v44 as S

from test_step4_p2batch_v46 import ALL_OFF, ByIdFake, jobs_of, make_root, run

UNUSED = "unused"
VALID = ["boat", "shop", "port"]


def cols_of(*ents):
    return [{"id": f"{e}:{i}"} for i, e in enumerate(ents)]


def test_rule_half_of_an_entity_unused_with_table_present():
    cols = cols_of("boat", "boat", "shop", "shop")
    ask = lambda ans, tables=("boat", "shop"): RA.drops_entity(cols, dict(zip([c["id"] for c in cols], ans)), set(tables), VALID)
    assert ask([UNUSED, "boat", "shop", "shop"])                 # 1 of 2 = half -> re-ask
    assert ask(["boat", None, "shop", "shop"])                   # None counts
    assert ask(["boat", "bad name", "shop", "shop"])             # not a choice counts
    assert not ask(["boat", "boat", "shop", "shop"])             # nothing unused
    assert not ask([UNUSED, UNUSED, "shop", "shop"], tables=("shop",))     # entity without a pass-1 table is not re-asked
    cols3 = cols_of("boat", "boat", "boat")
    assert not RA.drops_entity(cols3, {"boat:0": UNUSED, "boat:1": "boat", "boat:2": "boat"}, {"boat"}, VALID)   # 1 of 3 < half


class DropFake(ByIdFake):
    """Pass 2 first ask: entity "boat" columns of batch b0 go to "unused"; the re-ask puts them in the boat table."""
    def respond(self, job, prompt, schema):
        if job["format"] != "s43_p2":
            return super().respond(job, prompt, schema)
        enum = next(iter(schema["properties"].values()))["enum"]
        again = job["job"].endswith("_r1")
        return json.dumps({cid: (UNUSED if cid.startswith("boat:") and job["job"].endswith("_b0") and not again else
                                 ("boat" if cid.startswith("boat:") else enum[0])) for cid in schema["properties"]})


def test_chain_reasks_once_and_keeps_second_answer(tmp_path):
    root, _ = make_root(tmp_path, 45)
    cfg = S.with_switches(ALL_OFF, p2_batch=20, p2_reask=True)
    assert cfg["p2_reask"] is True
    out = tmp_path / "on"
    info = run(out, root, cfg, backend=DropFake())
    assert info["finished"] == "1/1" and info["p2_reask"] is True
    rj = B.read_json(out / "manifests" / "a_stage2_reask.json")["jobs"]
    assert [j["job"] for j in rj] == ["a_dev50_s0_p2_b0_r1"] and rj[0]["run_tag"] == "a_dev50_s0_r1" and rj[0]["n_columns"] == 20
    first = (out / jobs_of(out, 2)[0]["prompt"]).read_text(encoding="utf-8")
    assert (out / rj[0]["prompt"]).read_text(encoding="utf-8").replace(RA.REASK_NOTE, "") .replace("\n\nReturn", "\nReturn") == first or RA.REASK_NOTE in (out / rj[0]["prompt"]).read_text(encoding="utf-8")
    ch = B.read_json(out / "chains.json")[0]
    st, err, log = S.replay(out, ch, 2, root)
    assert err is None and log.to_dict()["counts"]["p2_reask"] == 1
    boats = [c["id"] for c in st["cols"] if c["id"].startswith("boat:")]
    assert all(st["assign"][i] == "boat" for i in boats)                         # the second answer replaced the first
    assert json.loads((out / "final" / "status.json").read_text(encoding="utf-8"))[0]["repair_kinds"]["p2_reask"] == 1


def test_switch_off_is_identical_to_a(tmp_path):
    root, _ = make_root(tmp_path, 45)
    off, base = tmp_path / "off", tmp_path / "base"
    run(base, root, S.with_switches(ALL_OFF, p2_batch=20), backend=DropFake())
    run(off, root, S.with_switches(ALL_OFF, p2_batch=20, p2_reask=False), backend=DropFake())
    assert not (off / "manifests" / "a_stage2_reask.json").exists() and all("p2_reask" not in c for c in B.read_json(off / "chains.json"))
    for f in ("final/a_dev50_s0/canonical.json", "final/status.json", "chains.json"):
        assert (off / f).read_text(encoding="utf-8") == (base / f).read_text(encoding="utf-8")
    ch = B.read_json(off / "chains.json")[0]
    assert S.replay(off, ch, 2, root)[2].to_dict()["counts"].get("p2_reask") is None


def test_missing_second_answer_keeps_first_and_is_counted(tmp_path):
    root, _ = make_root(tmp_path, 45)
    out = tmp_path / "x"
    run(out, root, S.with_switches(ALL_OFF, p2_batch=20, p2_reask=True), backend=DropFake())
    (out / "responses" / "a_dev50_s0_p2_b0_r1.jsonl").unlink()
    st, err, log = S.replay(out, B.read_json(out / "chains.json")[0], 2, root)
    assert err is None and log.to_dict()["counts"]["p2_reask_missing"] == 1
    assert all(st["assign"][c["id"]] is None for c in st["cols"][:20] if c["id"].startswith("boat:"))


def test_reask_needs_p2_batch():
    with pytest.raises(ValueError, match="p2_batch"):
        S.with_switches(ALL_OFF, p2_reask=True)
