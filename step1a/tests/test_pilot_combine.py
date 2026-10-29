import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402

CIDS = ["E1#0", "E1#1", "E1#2", "E1#3", "E1#4"]


def v3(assign, cids=CIDS):
    """v3 object: assign {cid: attribute name or 'not_attribute'}; attribute list from the names used."""
    names = sorted({a for a in assign.values() if a != "not_attribute"})
    return {"attributes": [{"name": n, "description": f"d {n}", "role": "r"} for n in names],
            "clusters": [{"cluster_id": c, "reason": "x", "attribute": assign[c], "evidence": "e", "mixed": False,
                          "placement": "current entity E1"} for c in cids if c in assign]}


def schema(cids=None, key="cluster_id"):
    return {"type": "object", "properties": {"clusters": {"type": "array", "items": {
        "type": "object", "properties": {key: {"enum": list(cids)}}}}}}


def write_job(d, job, obj, sch=None):
    (d / "prompts").mkdir(exist_ok=True)
    (d / "responses").mkdir(exist_ok=True)
    (d / job["schema"]).write_text(json.dumps(sch or {}), encoding="utf-8")
    if obj is not None:
        (d / "responses" / f"{job['job']}.jsonl").write_text(json.dumps({"key": "k", "parsed": obj}) + "\n", encoding="utf-8")


def mk_job(kind, tag, cid="", nbhd=None, variant=None, fmt=None, stage=1):
    name = f"train_{kind}{nbhd if nbhd is not None else ''}_{cid.replace('#', '-')}_{tag}"
    return {"job": name, "entity": "E1", "ent": "train", "variant": variant or kind, "run_tag": tag, "kind": kind,
            "stage": stage, "nbhd": nbhd, "cluster_id": cid, "prompt": f"prompts/{name}.txt",
            "schema": f"prompts/{name}.schema.json", "max_tokens": 100, "format": fmt or kind}


def folder(tmp_path, orders):
    """3 orders; each order has 2 groups: E1#0-2 and E1#3-4. orders = list of {cid: name}."""
    jobs = []
    for s, assign in enumerate(orders):
        for g, ids in enumerate([CIDS[:3], CIDS[3:]]):
            j = mk_job("entity", f"s{s}", nbhd=g, variant="nbhd", fmt="v3")
            write_job(tmp_path, j, v3({c: assign[c] for c in ids}, ids), schema(ids))
            jobs.append(j)
    (tmp_path / "manifest.json").write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
    return jobs


def add_jobs(tmp_path, new):
    m = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    for j, obj in new:
        write_job(tmp_path, j, obj)
        m["jobs"].append(j)
    (tmp_path / "manifest.json").write_text(json.dumps(m), encoding="utf-8")


def test_decisions_b_joins_groups(tmp_path):
    folder(tmp_path, [{"E1#0": "leave", "E1#1": "leave", "E1#2": "day", "E1#3": "leave", "E1#4": "not_attribute"}] * 3)
    d = PC.decisions_b(tmp_path, "train", 0)
    assert list(d["cluster_id"]) == CIDS
    assert list(d["action"]) == ["merge", "merge", "keep", "keep", "not_attribute"]  # E1#3 not merged yet
    assert PC.load_obj(tmp_path, PC.load_jobs(tmp_path)[0])["clusters"][0]["reason"] == "x"
    assert PC.load_obj(tmp_path, {"job": "nope", "format": "v3", "schema": "s"}) is None


def test_vote_majority_and_tie(tmp_path):
    a = {"E1#0": "leave", "E1#1": "leave", "E1#2": "day", "E1#3": "price", "E1#4": "area"}
    b = {**a, "E1#2": "day", "E1#3": "price", "E1#4": "not_attribute"}
    c = {**a, "E1#0": "arrive", "E1#1": "leave", "E1#3": "stars", "E1#4": "other"}
    folder(tmp_path, [a, b, c])
    tabs = [PC.decisions_b(tmp_path, "train", s) for s in range(3)]
    out, st = PC.vote(tabs)
    row = out.set_index("cluster_id")
    assert row.loc["E1#0", "name"] == "leave"  # 2 of 3
    assert row.loc["E1#4", "name"] == "area"  # 3-way tie (area, not attribute, other) -> seed 0
    assert row.loc["E1#3", "name"] == "price"  # 2 of 3
    assert st["ties"] == 1
    assert st["agree_full_share"] == 0.4  # E1#1 and E1#2 agree 3/3
    assert abs(st["agree_mean"] - np.mean([2 / 3, 1, 1, 2 / 3, 1 / 3])) < 1e-9
    assert row.loc["E1#0", "action"] == "merge" and json.loads(row.loc["E1#0", "merge_with"]) == ["E1#1"]


def test_vote_merge_with_restricted():
    a = PV.decisions_from_v2(v3({c: "x" for c in CIDS[:3]}), CIDS[:3], "nbhd", "s0")
    b = PV.decisions_from_v2(v3({"E1#0": "x", "E1#1": "y", "E1#2": "x"}), CIDS[:3], "nbhd", "s1")
    out, _ = PC.vote([a, b, b])
    rows = out.set_index("cluster_id")
    assert rows.loc["E1#1", "action"] == "keep"
    assert json.loads(rows.loc["E1#0", "merge_with"]) == ["E1#2"]


def test_generic_flags():
    rows = [("E1#0", "E1", "monday"), ("E1#0", "E1", "tuesday"), ("E2#0", "E2", "monday"), ("E3#0", "E3", "monday"),
            ("E3#0", "E3", "tuesday"), ("E4#0", "E4", "x1"), ("E4#0", "E4", "x2")]
    m = pd.DataFrame(rows, columns=["cluster_id", "entity", "norm_value"])
    # monday is in E1, E2, E3: every cluster with >= 50% such values is generic; E4 is not
    assert PC.generic_flags(m, ["E1", "E2", "E3", "E4"]) == {"E1#0", "E2#0", "E3#0"}
    assert PC.generic_flags(m, ["E1", "E2"]) == set()


def dec_of(assign):
    return PV.decisions_from_v2(v3(assign), CIDS, "nbhd", "s0")


def test_apply_noise_rules():
    dec = dec_of({"E1#0": "a", "E1#1": "b", "E1#2": "c", "E1#3": "not_attribute", "E1#4": "not_attribute"})
    probe = {"E1#0": {"verdict": "noise"}, "E1#1": {"verdict": "unsure"}, "E1#2": {"verdict": "attribute", "name": "c"},
             "E1#3": {"verdict": "attribute", "name": "rescued_name"}, "E1#4": {"verdict": "unsure"}}
    out, st = PC.apply_noise(dec, probe, generic={"E1#1", "E1#2"})
    r = out.set_index("cluster_id")
    assert r.loc["E1#0", "action"] == "not_attribute"  # probe noise
    assert r.loc["E1#1", "action"] == "not_attribute"  # generic, probe not attribute
    assert r.loc["E1#2", "action"] == "keep"  # generic but probe attribute
    assert r.loc["E1#3", "action"] == "keep" and r.loc["E1#3", "name"] == "rescued_name"
    assert r.loc["E1#4", "action"] == "not_attribute"  # voted, probe unsure
    assert st == {"marked_by_probe": 1, "by_vote": 1, "by_generic": 1, "rescued": 1}


def test_apply_noise_removes_from_group():
    dec = dec_of({"E1#0": "a", "E1#1": "a", "E1#2": "b"})
    out, _ = PC.apply_noise(dec, {"E1#0": {"verdict": "noise"}}, set())
    assert out.set_index("cluster_id").loc["E1#1", "action"] == "keep"


def test_apply_gate_only_where_gate_fails():
    dec = dec_of({"E1#0": "a", "E1#1": "a", "E1#2": "b"})
    parts = {"is_mixed": True, "parts": [{"name": "p", "role": "r", "examples": ["E1#0:s0"]},
                                         {"name": "q", "role": "r2", "examples": ["E1#0:s1"]}]}
    split = {"E1#0": parts, "E1#2": {**parts, "parts": [{"name": "p", "examples": ["E1#2:s0"]},
                                                         {"name": "q", "examples": ["E1#2:s1"]}]}}
    gate = {"E1#0": {"coherent": False}, "E1#2": {"coherent": True}}
    out = PC.apply_gate(dec, gate, split).set_index("cluster_id")
    assert out.loc["E1#0", "action"] == "split"
    assert [p["name"] for p in json.loads(out.loc["E1#0", "split"])] == ["p", "q"]
    assert out.loc["E1#1", "action"] == "keep"  # its partner was split off
    assert out.loc["E1#2", "action"] == "keep"  # gate coherent: not split
    # not mixed in the split result -> no split even if the gate fails
    out2 = PC.apply_gate(dec, {"E1#0": {"coherent": False}}, {"E1#0": {**parts, "is_mixed": False}})
    assert (out2["action"] != "split").all()


def test_apply_reconcile_union_and_none():
    dec = dec_of({"E1#0": "a", "E1#1": "b", "E1#2": "c", "E1#3": "d", "E1#4": "a"})
    parts = {"is_mixed": True, "parts": [{"name": "p", "role": "r", "examples": ["E1#3:s0"]},
                                         {"name": "q", "role": "r", "examples": ["E1#3:s1"]}]}
    dec = PC.apply_gate(dec, {"E1#3": {"coherent": False}}, {"E1#3": parts})
    units = PC.units_from_dec(dec)
    assert [u["uid"] for u in units] == ["a0", "a1", "a2", "E1#3-p0", "E1#3-p1"]
    assert units[0]["clusters"] == ["E1#0", "E1#4"] and units[0]["name"] == "a"
    answers = {"a1": {"same_as": "c"}, "a2": {"same_as": "none"}, "E1#3-p0": {"same_as": "a"},
               "E1#3-p1": {"same_as": "none"}}
    out = PC.apply_reconcile(dec, units, answers).set_index("cluster_id")
    assert out.loc["E1#1", "action"] == "merge" and json.loads(out.loc["E1#1", "merge_with"]) == ["E1#2"]
    assert out.loc["E1#2", "action"] == "merge"
    assert out.loc["E1#0", "action"] == "merge"  # a (E1#0, E1#4) unchanged group
    sp = json.loads(out.loc["E1#3", "split"])
    assert sp[0]["name"] == "a" and sp[0]["merge_into"] == ["E1#0", "E1#4"]
    assert sp[1]["name"] == "q"  # "none": stays its own new attribute
    # chain: a1 -> c and a2 -> a0 joins all three
    out2 = PC.apply_reconcile(dec, units, {"a1": {"same_as": "c"}, "a2": {"same_as": "a"}}).set_index("cluster_id")
    assert set(json.loads(out2.loc["E1#1", "merge_with"])) == {"E1#2", "E1#0", "E1#4"}


def fake_render(unit, cands):
    return f"{unit['unit_id']}|{unit['name']}|" + ";".join(c[0] for c in cands) + "|" + "/".join(unit["lines"])


def fake_schema(uid, names):
    return {"unit_id": uid, "enum": names + ["none"]}


def stage2_folder(tmp_path):
    folder(tmp_path, [{"E1#0": "leave", "E1#1": "day", "E1#2": "day", "E1#3": "price", "E1#4": "not_attribute"}] * 3)
    parts = {"is_mixed": True, "parts": [{"name": "p", "role": "r", "examples": ["E1#3:s0"]},
                                         {"name": "q", "role": "r", "examples": ["E1#3:s1"]}]}
    add_jobs(tmp_path, [(mk_job("gate", "r1", "E1#3"), {"cluster_id": "E1#3", "summary": "s", "coherent": False}),
                        (mk_job("split", "r1", "E1#3", fmt="split"), {"cluster_id": "E1#3", **parts})])
    inputs = {"train": {"entity": "E1", "clusters": {c: {"head": c, "lines": [f"{c} l{k}" for k in range(6)]} for c in CIDS},
                        "split_examples": {"E1#3": {"E1#3:s0": "ex0", "E1#3:s1": "ex1"}}, "options": []}}
    (tmp_path / "stage2_inputs.json").write_text(json.dumps(inputs), encoding="utf-8")
    x = np.array([[1, 0, 0], [0, 1, 0], [0, 1, 0.1], [1, 1, 0], [0, 0, 1]], dtype=np.float32)
    np.savez(tmp_path / "stage2_vectors.npz", cluster_ids=np.array(CIDS), cluster_x=x,
             ex_ids=np.array(["E1#3:s0", "E1#3:s1"]), ex_x=np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32))


def test_build_stage2_idempotent(tmp_path):
    stage2_folder(tmp_path)
    new = PC.build_stage2(tmp_path, render=fake_render, schema=fake_schema)
    # units: a0 leave, a1 day (E1#1+E1#2 joined by name), a2 price? E1#3 is split -> parts; E1#4 marked? (no probe: kept as not_attribute)
    assert sorted(j["unit_id"] for j in new) == ["E1#3-p0", "E1#3-p1", "a0", "a1"]
    assert all(j["stage"] == 2 and j["kind"] == "reconcile" and j["format"] == "reconcile" for j in new)
    p = (tmp_path / "prompts" / "train_reconcile_a0.txt").read_text(encoding="utf-8")
    assert p == "a0|leave|day|E1#0 l0/E1#0 l1/E1#0 l2/E1#0 l3/E1#0 l4/E1#0 l5"
    assert (tmp_path / "prompts" / "train_reconcile_E1-3-p0.txt").read_text(encoding="utf-8").startswith("E1#3-p0|p|")
    assert (tmp_path / "prompts" / "train_reconcile_E1-3-p0.txt").read_text(encoding="utf-8").endswith("|ex0")
    first = (tmp_path / "manifest.json").read_text(encoding="utf-8")
    again = PC.build_stage2(tmp_path, render=fake_render, schema=fake_schema)
    assert again == new
    assert (tmp_path / "manifest.json").read_text(encoding="utf-8") == first
    assert sum(j["kind"] == "reconcile" for j in PC.load_jobs(tmp_path)) == 4


def test_decisions_d_chain(tmp_path):
    stage2_folder(tmp_path)
    new = PC.build_stage2(tmp_path, render=fake_render, schema=fake_schema)
    by = {j["unit_id"]: j for j in new}
    add_jobs(tmp_path, [(by["a0"], {"unit_id": "a0", "reason": "r", "same_as": "day"}),
                        (by["E1#3-p0"], {"unit_id": "E1#3-p0", "reason": "r", "same_as": "none"})])
    (tmp_path / "generic.json").write_text(json.dumps({"train": []}), encoding="utf-8")
    # E1#4 got no probe answer: voted not_attribute + unsure -> stays marked
    dec, st = PC.decisions_d(tmp_path, "train")
    r = dec.set_index("cluster_id")
    assert r.loc["E1#3", "action"] == "split"
    assert r.loc["E1#4", "action"] == "not_attribute"
    assert set(json.loads(r.loc["E1#0", "merge_with"])) == {"E1#1", "E1#2"}  # leave -> day
    assert st["reconcile_merged"] == 1 and st["split"] == 1
    assert set(dec["variant"]) == {"full"}


def _rows(*rows):
    base = {"variant": "nbhd", "run_tag": "s0", "description": "", "evidence": "", "merge_with": "[]", "split": "[]",
            "placement": "current entity E1"}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_name_join_needs_same_placement_and_no_shared_instance():
    dec = _rows({"cluster_id": "E1#0", "name": "station", "action": "keep"},
                {"cluster_id": "E1#1", "name": "station", "action": "keep"},
                {"cluster_id": "E1#2", "name": "station", "action": "keep", "placement": "entity E2"},
                {"cluster_id": "E1#3", "name": "day", "action": "keep"},
                {"cluster_id": "E1#4", "name": "day", "action": "keep"})
    out = PC._name_join(dec, cooccur=[["E1#3", "E1#4"]]).set_index("cluster_id")
    assert json.loads(out.loc["E1#0", "merge_with"]) == ["E1#1"]  # same name + placement
    assert out.loc["E1#2", "action"] == "keep"                    # other placement
    assert out.loc["E1#3", "action"] == out.loc["E1#4", "action"] == "keep"  # share an instance
