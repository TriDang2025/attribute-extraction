import json
import sys
import zlib
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pilot_build_v35 as B  # noqa: E402
from s1a import oracle_v35 as OR  # noqa: E402
from s1a import pilot_input as P  # noqa: E402
from s1a import role_guard as RG  # noqa: E402
from s1a.pilot_verify import norm_name  # noqa: E402
from test_pilot_input import toy  # noqa: E402

GRP = ["E0#0", "E0#1"]


def role_toy():
    """toy export where cluster E0#1 holds two roles (3 departure, 2 destination, 1 unlabelled mention)."""
    export, docs = toy()
    mm = export.mentions
    lab = pd.Series("", index=mm.index)
    ids = list(mm.index[mm["cluster_id"] == "E0#1"])
    for i, label in zip(ids, ["Train departure"] * 3 + ["Train destination"] * 2):
        lab.loc[i] = label
    lab.loc[mm.index[mm["cluster_id"] == "E0#0"]] = "Train day"
    return export, docs, lab


# ---- T18: old prompts byte-identical, new flag
def test_old_instructions_and_prompts_unchanged():
    assert zlib.crc32(P.INSTRUCTION_V3.encode()) == 686104669
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    out = [("E1#0", ["monday"])]
    base = P.render_v3(inp, export, docs, GRP, out, 2)
    assert base == P.render_v3(inp, export, docs, GRP, out, 2, None, None, False, False)
    assert base.startswith(P.INSTRUCTION_V3) and "role_examples" not in base
    sch = P.schema_v3(inp, GRP)
    assert "role_examples" not in json.dumps(sch)
    assert sch == P.schema_v3(inp, GRP, False)


def test_mixed_instruction_replaced_only_in_g():
    assert P.INSTRUCTION_V35G.count("role_examples") == 2 and P.ROLE_EXAMPLES_LINE in P.INSTRUCTION_V35G
    assert P._MIXED_SENT not in P.INSTRUCTION_V35G and "assign its most frequent attribute, set" in P.INSTRUCTION_V35G
    rest = P.INSTRUCTION_V3.replace(P._MIXED_SENT, "")
    assert P.INSTRUCTION_V35G.replace(P.ROLE_EXAMPLES_LINE, "") == rest
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    text = P.render_v3(inp, export, docs, GRP, [], 2, role_examples=True)
    assert text.startswith(P.INSTRUCTION_V35G)
    try:
        P.render_v3(inp, export, docs, GRP, [], 2, cue_rule=True, role_examples=True)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_role_examples_schema_optional_with_group_example_ids():
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    sch = P.schema_v3(inp, GRP, role_examples=True)
    item = sch["properties"]["clusters"]["items"]
    assert list(item["properties"])[-1] == "role_examples" and "role_examples" not in item["required"]
    assert item["required"] == list(P.schema_v3(inp, GRP)["properties"]["clusters"]["items"]["properties"])
    enum = item["properties"]["role_examples"]["items"]["properties"]["examples"]["items"]["enum"]
    shown = [ex for c in inp.clusters if c.cluster_id in GRP for ex, _ in c.examples]
    assert enum == shown and not any(e.startswith("E0#2") for e in enum)


def test_cluster_number_sorts_oracle_parts():
    ids = ["E1#2", "E1#10", "E1#1.b", "E1#1.a", "E1#1"]
    assert sorted(ids, key=P._cluster_number) == ["E1#1", "E1#1.a", "E1#1.b", "E1#2", "E1#10"]


# ---- T14 oracle split
def test_oracle_split_and_prompts():
    export, docs, lab = role_toy()
    mm = export.mentions
    roles, two = OR.two_roles(mm, lab)
    assert two == {"E0#1": ("departure", "destination")}
    new = OR.split_ids(mm, roles, two)
    mine = mm.index[mm["cluster_id"] == "E0#1"]
    # 3 departure -> .a, 2 destination -> .b, the unlabelled mention joins the larger part (.a)
    assert sorted(new.loc[mine]) == ["E0#1.a"] * 4 + ["E0#1.b"] * 2
    assert (new.drop(mine) == mm["cluster_id"].drop(mine)).all()
    oe = OR.oracle_export(export, new)
    assert (export.mentions["cluster_id"] == mm["cluster_id"]).all()   # the original is untouched
    cl = oe.clusters.set_index("cluster_id")
    assert "E0#1" not in cl.index and cl.at["E0#1.a", "n_mentions"] == 4 and cl.at["E0#1.b", "n_mentions"] == 2
    assert cl.at["E0#0", "n_mentions"] == len(mm[mm["cluster_id"] == "E0#0"])
    rows = OR.oracle_rows(mm, roles, new)
    assert set(rows.columns) == {"mention_id", "entity", "orig_cluster_id", "oracle_cluster_id", "gold_role"}
    assert set(rows.loc[rows["orig_cluster_id"] == "E0#1", "oracle_cluster_id"]) == {"E0#1.a", "E0#1.b"}
    specs, nb = B.entity_specs(oe, docs, None, "train", "E0", "oracle")
    assert len(specs) == 3 and {s["seed"] for s in specs} == {0, 1, 2}
    assert "### E0#1.a" in specs[0]["text"] and "### E0#1.b" in specs[0]["text"] and "### E0#1 " not in specs[0]["text"]
    assert {c for *_, c in nb} >= {"E0#1.a", "E0#1.b"}


def test_oracle_without_two_role_clusters_changes_nothing():
    export, docs, lab = role_toy()
    mm = export.mentions
    roles, two = OR.two_roles(mm, pd.Series("", index=mm.index))
    assert two == {}
    new = OR.split_ids(mm, roles, two)
    assert (new == mm["cluster_id"]).all()
    assert OR.oracle_export(export, new).clusters is export.clusters


# ---- T19 example per role
def test_example_role_counts():
    export, _, lab = role_toy()
    mm = export.mentions
    roles, two = OR.two_roles(mm, lab)
    ids = [int(mm.at[i, "mention_id"]) for i in mm.index[mm["cluster_id"] == "E0#1"]]
    rows = OR.example_role_counts(mm, {"E0#1": ids[:2]}, roles, two)   # shown: 2 departure mentions
    got = {r.slot: (r.shown, r.total) for r in rows.itertuples()}
    assert got == {"departure": (2, 3), "destination": (0, 2)}


def test_g_specs_use_role_picker_and_role_schema():
    export, docs, _ = role_toy()
    left = {int(i): w for i, w in zip(export.mentions["mention_id"], export.mentions["left_word"])}
    specs, _ = B.entity_specs(export, docs, None, "train", "E0", "g", 0, left, True)
    assert [s["name"] for s in specs] == [f"train_g_nbhd0_s{s}" for s in (0, 1, 2)]
    assert specs[0]["text"].startswith(P.INSTRUCTION_V35G)
    item = specs[0]["schema"]["properties"]["clusters"]["items"]
    assert "role_examples" in item["properties"] and "role_examples" not in item["required"]
    plain, _ = B.entity_specs(export, docs, None, "train", "E0", "c")
    assert plain[0]["text"].startswith(P.INSTRUCTION_V3) and "role_examples" not in json.dumps(plain[0]["schema"])


# ---- T20 role-pair guard and reconcile prompt
def test_forbidden_merge_pairs():
    assert RG.forbidden_merge("departure_station from", "destination_station to")
    assert RG.forbidden_merge("leave_at time", "arrival_time")
    assert RG.forbidden_merge("hotel_location", "hotel_address")
    assert RG.forbidden_merge("train_destination", "train_departure")
    assert not RG.forbidden_merge("departure_station", "departure_place")
    assert not RG.forbidden_merge("restaurant_name", "hotel_name")
    assert not RG.forbidden_merge("route_departure_destination", "destination_station")   # both sides in one name


def test_filter_reconcile_answers():
    units = [{"uid": "a0", "name": "train_departure"}, {"uid": "a1", "name": "train_destination"},
             {"uid": "a2", "name": "pickup_place"}, {"uid": "a3", "name": "origin_station"}]
    answers = {"a0": {"same_as": "train_destination"}, "a1": {"same_as": "none"},
               "a2": {"same_as": "train_departure"}, "a3": {"same_as": "train_departure"}}
    roles = {norm_name("pickup_place"): "where the trip starts departure"}
    out, rej = RG.filter_reconcile_answers(units, answers, roles)
    assert out["a0"]["same_as"] == "none" and out["a0"]["role_pair_rejected"] == "train_destination"
    assert out["a1"] == answers["a1"] and out["a3"] == answers["a3"]
    assert out["a2"]["same_as"] == "train_departure"   # same side: allowed
    assert rej == [("a0", "train_departure", "train_destination")]
    out2, rej2 = RG.filter_reconcile_answers([{"uid": "a2", "name": "pickup_place"}],
                                             {"a2": {"same_as": "train_destination"}},
                                             {norm_name("pickup_place"): "departure place"})
    assert rej2 and out2["a2"]["same_as"] == "none"   # the role text counts


def test_reconcile_v35_prompt_has_roles_and_rule():
    unit = {"unit_id": "a0", "name": "train_departure", "description": "start station", "lines": ["- ex"]}
    cands = [("train_destination", "end station"), ("train_day", "day")]
    roles = {norm_name("train_departure"): "origin", norm_name("train_destination"): "end"}
    text = P.render_reconcile_v35(unit, cands, roles)
    assert "departure with destination, leave at with arrive by, location with address" in text
    assert "Attribute a0: train_departure (role: origin): start station" in text
    assert "- train_destination (role: end): end station" in text and "- train_day: day" in text
    old = P.render_reconcile(unit, cands)
    assert "role pair" not in old and "(role:" not in old


# ---- batch plumbing
def test_t8_job_copies_prompt_lf(tmp_path):
    src, out = tmp_path / "v31", tmp_path / "out"
    (src / "prompts").mkdir(parents=True)
    (src / "responses").mkdir()
    (out / "prompts").mkdir(parents=True)
    (src / "prompts" / "restaurant_v2_r2.txt").write_bytes(b"line one\r\nline two\r\n")
    (src / "prompts" / "restaurant_v2_r2.schema.json").write_bytes(b'{"type": "object"}')
    old = {"job": "restaurant_v2_r2", "entity": "E2", "ent": "restaurant", "variant": "v2", "run_tag": "r2",
           "kind": "entity", "cluster_id": "", "prompt": "prompts/restaurant_v2_r2.txt",
           "schema": "prompts/restaurant_v2_r2.schema.json", "max_tokens": 12000, "format": "v2"}
    (src / "manifest.json").write_text(json.dumps([old, {**old, "job": "other"}]), encoding="utf-8")
    (src / "responses" / "restaurant_v2_r2.jsonl").write_text(json.dumps({"raw": "x" * 70}) + "\n", encoding="utf-8")
    job, text, o = B.t8_job(src, out)
    assert text == "line one\nline two\n" and o == 20
    assert (out / "prompts" / "restaurant_v2_r2_rerun.txt").read_bytes() == b"line one\nline two\n"
    assert job["job"] == "restaurant_v2_r2_rerun" and job["run_tag"] == "r2" and job["format"] == "v2"
    assert job["max_tokens"] == 12000 and job["prompt"] == "prompts/restaurant_v2_r2_rerun.txt"
    assert job["round"] == 0 and job["carry_from"] == []


def test_manifest_job_and_token_tables():
    s = dict(name="train_g_nbhd1_s2", ent="train", entity="E1", tag="g", gi=1, seed=2, text="x" * 700)
    j = B.manifest_job(s, "g")
    assert j["run_tag"] == "s2" and j["nbhd"] == 1 and j["format"] == "v3" and j["family"] == "g" and j["round"] == 0
    assert j["prompt"] == "prompts/train_g_nbhd1_s2.txt" and j["schema"].endswith(".schema.json")
    rows = B.family_rows([("t8", 100, 10.4), ("g", 50, 5), ("g", 70, 7.9), ("oracle", 1, 1)])
    assert rows == ["| t8 | 1 | 100 | 10 |", "| oracle | 1 | 1 | 1 |", "| g | 2 | 120 | 12 |", "| total | 4 | 221 | 23 |"]
    assert B.out_rate([(10, 100), (30, 500)]) == 15 and B.out_rate([]) == 0.0
