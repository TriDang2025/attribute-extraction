import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import pilot_combine as PC  # noqa: E402
from test_pilot_combine import CIDS, mk_job, schema, v3, write_job  # noqa: E402


def mk(var, seed, g, ids, rnd=0, carry=()):
    j = mk_job("entity", f"s{seed}", nbhd=g, variant=var, fmt="v3")
    j.update(job=f"train_{var}_nbhd{g}_s{seed}", round=rnd, carry_from=list(carry),
             prompt=f"prompts/train_{var}_nbhd{g}_s{seed}.txt", schema=f"prompts/train_{var}_nbhd{g}_s{seed}.schema.json")
    return j, ids


def put(d, j, ids, assign):
    write_job(d, j, v3({c: assign[c] for c in ids}, ids), schema(ids))


def test_render_carry_dedup_and_exclusions():
    out = PC.render_carry([("Departure_Station", "from"), ("departure station", "dup"), ("not_attribute", ""),
                           ("attribute_cue", "q"), ("day", ""), ("", "x")])
    lines = out.splitlines()
    assert lines[0].startswith("Attributes already found") and lines[1].endswith("make a new one):")
    assert lines[2:] == ["- Departure_Station: from", "- day"]
    assert PC.render_carry([("not_attribute", ""), ("attribute_cue", "")]) == ""


def folder_carry(tmp_path, variant="e", parent_resp=True):
    g0, ids0 = mk(variant, 0, 0, CIDS[:3])
    g1, ids1 = mk(variant, 0, 1, CIDS[3:], rnd=1, carry=[g0["job"]])
    (tmp_path / "prompts").mkdir(exist_ok=True)
    (tmp_path / g1["prompt"].replace(".txt", ".tmpl.txt")).write_text("head\n{{CARRY_OVER}}\nTrain station TR1234 tail\n", encoding="utf-8")
    assign = {"E1#0": "leave", "E1#1": "day", "E1#2": "not_attribute", "E1#3": "x", "E1#4": "y"}
    if parent_resp:
        put(tmp_path, g0, ids0, assign)
    write_job(tmp_path, g1, None)
    (tmp_path / "manifest.json").write_text(json.dumps({"jobs": [g0, g1]}), encoding="utf-8")
    return g1


def test_fill_carry_writes_text(tmp_path):
    g1 = folder_carry(tmp_path)
    done = PC.fill_carry(tmp_path, 1)
    assert [j["job"] for j in done] == [g1["job"]]
    text = (tmp_path / g1["prompt"]).read_text(encoding="utf-8")
    assert text.startswith("head\nAttributes already found") and "- day: d day" in text and "- leave: d leave" in text
    assert "not_attribute" not in text and text.endswith("tail\n") and "{{CARRY_OVER}}" not in text
    assert PC.fill_carry(tmp_path, 1) and (tmp_path / g1["prompt"]).read_text(encoding="utf-8") == text  # deterministic
    assert PC.fill_carry(tmp_path, 0) == []  # round 0 has no carry jobs


def test_fill_carry_raises_on_missing_parent(tmp_path):
    g1 = folder_carry(tmp_path, parent_resp=False)
    with pytest.raises(ValueError, match="without a parsed response"):
        PC.fill_carry(tmp_path, 1)
    assert not (tmp_path / g1["prompt"]).exists()  # nothing written: a round is never half filled


def test_fill_carry_variant_f_applies_delex(tmp_path):
    from s1a import delex
    if not hasattr(delex, "apply"):
        pytest.skip("s1a.delex.apply not written yet")
    g1 = folder_carry(tmp_path, variant="f")
    (tmp_path / "delex_map.json").write_text(json.dumps({"day": "zorp"}), encoding="utf-8")
    PC.fill_carry(tmp_path, 1)
    text = (tmp_path / g1["prompt"]).read_text(encoding="utf-8")
    assert "zorp" in text and "- day" not in text


def test_decisions_e_e1_composition_and_cue(tmp_path):
    names = {"e": {"E1#0": "a", "E1#1": "attribute_cue", "E1#2": "c"},
             "e1": {"E1#3": "d", "E1#4": "attribute_cue"}}
    jobs = []
    for var, g, ids in (("e", 0, CIDS[:3]), ("e", 1, CIDS[3:]), ("e1", 1, CIDS[3:])):
        for s in range(3):
            j, _ = mk(var, s, g, ids)
            src = names["e1" if var == "e1" else "e"]
            assign = {c: src.get(c, "wrong") for c in ids}
            if var == "e" and g == 1:
                assign = {c: "from_e" for c in ids}  # E1 must ignore this group-1 `e` response
            put(tmp_path, j, ids, assign)
            jobs.append(j)
    gate_job = mk_job("gate", "r1", "E1#0")
    write_job(tmp_path, gate_job, {"cluster_id": "E1#0", "coherent": False})
    parts = {"is_mixed": True, "parts": [{"name": "p", "examples": ["E1#0:s0"]}, {"name": "q", "examples": ["E1#0:s1"]}]}
    split_job = mk_job("split", "r1", "E1#0", fmt="split")
    write_job(tmp_path, split_job, {"cluster_id": "E1#0", **parts})
    (tmp_path / "manifest.json").write_text(json.dumps({"jobs": jobs + [gate_job, split_job]}), encoding="utf-8")

    d, st = PC.decisions_e(tmp_path, "train", "e1", tmp_path)
    r = d.set_index("cluster_id")
    assert r.loc["E1#3", "name"] == "d" and r.loc["E1#4", "action"] == "attribute_cue"  # groups >= 1 from e1
    assert r.loc["E1#1", "action"] == "attribute_cue" and r.loc["E1#0", "action"] == "split"  # group 0 from e + gate
    assert st["cue"] == 2 and st["gate_failed"] == 1 and st["split"] == 1 and st["agree_mean"] == 1.0
    de, ste = PC.decisions_e(tmp_path, "train", "e", tmp_path)
    assert de.set_index("cluster_id").loc["E1#3", "name"] == "from_e" and ste["cue"] == 1
    assert set(d["variant"]) == {"e1"}
