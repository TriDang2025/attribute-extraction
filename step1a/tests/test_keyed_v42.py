"""wf_v4.2 option B: keyed "exactly once" schemas (s1a/keyed_v42.py) on real schemas of the T1 / T2 job folders."""
import json
from pathlib import Path

import pytest

from s1a import batch_v4_fake as F
from s1a import keyed_v42 as K
from s1a import nov16_v41 as NV

ROOT = Path(__file__).resolve().parents[1]
T1 = ROOT / "results" / "wf_v42" / "t1_step3" / "prompts"
T2 = ROOT / "results" / "wf_v42" / "t2_step4" / "prompts"
T2B = ROOT / "results" / "wf_v42" / "t2b_step4_keyed" / "prompts"
CASES = [("v2", T1 / "train_a_v22d50b_s0.schema.json"), ("s4_41", T2 / "c1_dev50_s0_41.schema.json"),
         ("s4_42", T2 / "c1_dev50_s0_42.schema.json"), ("s4_43", T2B / "c1_dev50_s0_43.schema.json"), ("s4_44", ROOT / "results" / "wf_v41" / "step4_dryrun" / "prompts" / "c1_dev50_s0_44.schema.json")]


def frozen_answer(fmt, schema, path):
    job = {"job": path.stem, "format": fmt, "family": "a" if fmt == "v2" else fmt, "prompt": "", "schema": ""}
    return NV.fake_a(schema) if fmt == "v2" else F.respond(job, "", schema)


@pytest.mark.parametrize("fmt,path", CASES)
def test_round_trip_parses_like_frozen(fmt, path):
    if not path.exists():
        pytest.skip(f"{path} not in this checkout")
    frozen = json.loads(path.read_text(encoding="utf-8"))
    keyed = K.key_schema(fmt, frozen)
    raw = frozen_answer(fmt, frozen, path)
    job = {"format": fmt}
    want = NV.parse_answer(raw, job, frozen)
    got = NV.parse_answer(K.key_answer(fmt, raw), {**job, "keyed": True}, keyed)
    assert got == want
    assert NV.parse_answer(raw, {**job, "keyed": True}, keyed) == want      # list form (unguided retry) passes unchanged


@pytest.mark.parametrize("fmt,path", [c for c in CASES if c[0] != "s4_43"])
def test_keyed_lists_every_id_once(fmt, path):
    if not path.exists():
        pytest.skip(f"{path} not in this checkout")
    keyed = K.key_schema(fmt, json.loads(path.read_text(encoding="utf-8")))
    per_id = keyed["properties"]["columns" if fmt == "s4_41" else "clusters" if fmt == "v2" else "tables"]
    assert per_id["additionalProperties"] is False and per_id["required"] == list(per_id["properties"])
    assert keyed["title"] == K.MARK


def test_cut_off_answer_stays_an_error():
    parsed, errors = NV.parse_answer('{"attributes": [], "clusters": {"E0#0": {"attr', {"format": "v2", "keyed": True},
                                     {"properties": {"clusters": {"properties": {"E0#0": {}}}}})
    assert errors


def test_key_job_is_idempotent(tmp_path):
    src = CASES[2][1]
    if not src.exists():
        pytest.skip("no T2 schema")
    (tmp_path / "prompts").mkdir()
    p = tmp_path / "prompts" / src.name
    p.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    job = {"format": "s4_42", "schema": f"prompts/{src.name}"}
    K.key_job(tmp_path, job)
    once = p.read_text(encoding="utf-8")
    assert K.key_job(tmp_path, job)["keyed"] and p.read_text(encoding="utf-8") == once
    assert json.loads(K.frozen_path(p).read_text(encoding="utf-8")) == json.loads(src.read_text(encoding="utf-8"))


def test_43_lists_are_capped():
    path = CASES[3][1]
    if not path.exists():
        pytest.skip("no T2b 4.3 schema")
    keyed = K.key_schema("s4_43", json.loads(path.read_text(encoding="utf-8")))       # 4 tables -> 6 pairs
    assert keyed["properties"]["relationships"]["maxItems"] == 12 and keyed["properties"]["new_tables"]["maxItems"] == 6
    assert keyed["properties"]["relationships"]["items"]["properties"]["reason"]["maxLength"] == K.CAP["reason"]


def test_42_repeated_names_renamed():
    raw = json.dumps({"tables": {"G1": {"name": "Ref", "description": "d", "row": "r"},
                                 "G2": {"name": "ref ", "description": "d", "row": "r"},
                                 "G3": {"name": "ref_g2", "description": "d", "row": "r"}}})
    assert K.renamed_42(raw) == 1
    names = [t["name"] for t in json.loads(K.unkey("s4_42", raw))["tables"]]
    assert names == ["Ref", "ref_g2", "ref_g2_g3"]
