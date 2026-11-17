"""wf_v4.6 Y3: LLM entity names (s1a/entity_names_v46.py) and the merge of equal names at the Step 4 input (s1a/pipeline_v46.py). Fake LLM only."""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import batch_v4 as B  # noqa: E402
from s1a import entity_names_v46 as EN  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import pipeline_v46 as PL46  # noqa: E402
from s1a import step4_v44 as S4  # noqa: E402

SET = "tiny"


def mentions(n_per=8, entities=("E0", "E1", "E2")):
    rows, i = [], 0
    for e in entities:
        for j in range(n_per):
            rows.append({"mention_id": i, "text": f"{e} text {j}", "norm_value": f"{e} value {j % 6}", "context": f"context of {e} mention {j} " + "x" * 200,
                         "entity": e})
            i += 1
    return pd.DataFrame(rows)


def write_run(root, ents=("E0", "E1", "E2")):
    """results/graph_v22_<SET>/ with entities.json and spans/mentions.csv (the files names_for_run reads)."""
    rd = Path(root) / "results" / f"graph_v22_{SET}"
    (rd / "spans").mkdir(parents=True)
    (rd / "entities.json").write_text(json.dumps({e: f"kw{e}" for e in ents}), encoding="utf-8")
    m = mentions(entities=ents)
    m.assign(**{c: "" for c in ("input", "dialogue_id")}).to_csv(rd / "spans" / "mentions.csv", index=False)
    pd.DataFrame({"cluster_id": [f"{e}#0" for e in ents], "entity": list(ents)}).to_csv(rd / "spans" / "clusters.csv", index=False)
    return m


def test_prompt_has_five_examples_and_top_values():
    m = mentions()
    df = m[m["entity"] == "E1"]
    text = EN.render(df, "E1")
    assert [line[:2] for line in text.splitlines() if line[:2] in {f"{i}." for i in range(1, 7)}] == ["1.", "2.", "3.", "4.", "5."]
    assert "Most frequent values: " in text and "E1 value 0" in text.split("Most frequent values: ")[1].splitlines()[0]
    assert len(text.split("Most frequent values: ")[1].splitlines()[0].split(" | ")) == 6          # 6 distinct values < N_VALUES
    assert "x" * 200 not in text                                                                    # context cut
    assert EN.render(df, "E1") == text                                                              # seeded: deterministic
    assert EN.render(df, "E1", seed=1) != text
    assert len(text) < 2000                                                                         # about 500 tokens


def test_examples_prefer_distinct_values():
    df = mentions(n_per=8)
    df = df[df["entity"] == "E0"]
    picked = EN.pick_examples(df, "E0")
    assert len(picked) == 5 and len({r.norm_value for r in picked}) == 5


def test_schema_has_no_pattern():
    s = EN.schema()
    assert "pattern" not in json.dumps(s)
    assert s["required"] == ["name"] and s["properties"]["name"] == {"type": "string"}


@pytest.mark.parametrize("answer,name", [({"name": "Hotel"}, "hotel"), ({"name": " Train  Ticket "}, "train_ticket"), ({"name": "car-rental!"}, "car_rental"),
                                         ({"name": "a very long entity name"}, None), ({"name": ""}, None), ({"name": 3}, None), ({"nom": "x"}, None),
                                         ([], None), (None, None)])
def test_parse_name(answer, name):
    assert EN.parse_name(answer) == name


def test_keys_and_merge_map():
    names = {"E0": "hotel", "E1": "train", "E2": "hotel", "E10": "hotel", "E3": "hotel_2"}
    keys = EN.unique_keys(names)
    assert keys == {"E0": "hotel", "E1": "train", "E2": "hotel_2", "E3": "hotel_2_2", "E10": "hotel_3"}
    assert len(set(keys.values())) == 5
    groups = EN.merge_map(names)
    assert groups == {"hotel": ["E0", "E2", "E10"], "train": ["E1"], "hotel_2": ["E3"]}
    rec = {"keys": keys, "groups": groups}
    assert EN.key_groups(rec) == {"hotel": ["hotel", "hotel_2", "hotel_3"]}
    assert EN.key_groups(rec, present={"hotel", "hotel_3", "train"}) == {"hotel": ["hotel", "hotel_3"]}
    assert EN.key_groups(rec, present={"hotel", "train"}) == {}


def test_names_for_run_with_fake_llm(tmp_path):
    write_run(tmp_path)
    out = tmp_path / "out"
    rec = EN.names_for_run(SET, out, EN.FakeNames(n_names=2), root=tmp_path, log=lambda *_: None)
    assert rec["names"] == {"E0": "fake_entity_0", "E1": "fake_entity_1", "E2": "fake_entity_0"}
    assert rec["keys"] == {"E0": "fake_entity_0", "E1": "fake_entity_1", "E2": "fake_entity_0_2"}
    assert rec["groups"] == {"fake_entity_0": ["E0", "E2"], "fake_entity_1": ["E1"]} and rec["fallback"] == []
    assert json.loads((out / "entity_names.json").read_text(encoding="utf-8"))["groups"] == rec["groups"]
    assert json.loads((tmp_path / "results" / f"graph_v22_{SET}" / "entities.json").read_text(encoding="utf-8")) == rec["keys"]
    rows = B.read_json(out / "names" / "prompts" / "ename_tiny_E0.schema.json")
    assert "pattern" not in json.dumps(rows)
    assert len(list((out / "names" / "responses").glob("*.jsonl"))) == 3
    # rerun: cached answers, same record
    assert EN.names_for_run(SET, out, EN.FakeNames(n_names=2), root=tmp_path, log=lambda *_: None)["keys"] == rec["keys"]


def test_bad_answer_falls_back_to_the_entity_id(tmp_path):
    write_run(tmp_path, ents=("E0", "E1"))

    class Bad(EN.FakeNames):
        def respond(self, job, prompt, schema):
            return json.dumps({"name": "way too many words in here"}) if job["entity"] == "E1" else super().respond(job, prompt, schema)

    rec = EN.names_for_run(SET, tmp_path / "out", Bad(), root=tmp_path, log=lambda *_: None)
    assert rec["names"]["E1"] == "e1" and rec["fallback"] == ["E1"]


# ---------------------------------------------------------------- merge at the Step 4 input
def step3_dir(root):
    """A Step 3 output folder of three entities: two with the name "hotel" (keys hotel, hotel_2) and one "train"."""
    out = Path(root) / "step3"
    cols, final, mid = [], {}, 0
    for key, n_cols in (("hotel", 2), ("train", 1), ("hotel_2", 2)):
        final[key] = []
        for n in range(1, n_cols + 1):
            ids = [mid, mid + 1]
            mid += 2
            final[key].append({"cid": n, "name": f"{key} col {n}", "description": "", "mention_ids": ids})
            cols.append({"id": f"{key}:{n}", "name": f"{key} col {n}", "description": "", "role": "", "value_type": "text",
                         "examples": [f"{key} example {n}"], "n_mentions": 2, "n_dialogues": 1, "signal": "", "flag": ""})
    B.write_json(out / "scores" / "final_columns.json", {SET: final})
    B.write_json(out / "a_llama44" / SET / "a.columns.json", cols)
    return out, cols


def mention_table(root, n=10):
    rd = Path(root) / "results" / f"graph_v22_{SET}" / "spans"
    rd.mkdir(parents=True)
    pd.DataFrame({"mention_id": range(n), "dialogue_id": "d0", "text": [f"v{i}" for i in range(n)], "norm_value": [f"v{i}" for i in range(n)],
                  "context": "ctx"}).to_csv(rd / "mentions.csv", index=False)


def test_merge_step4_input_joins_columns_of_equal_names(tmp_path):
    out, cols = step3_dir(tmp_path)
    groups = {"hotel": ["hotel", "hotel_2"]}
    ids = {f"{e}:{c['cid']}": c["mention_ids"] for e, cs in B.read_json(out / "scores" / "final_columns.json")[SET].items() for c in cs}
    merged = EN.merge_step4_input(cols, ids, groups)
    assert [c["id"] for c in merged] == ["hotel:1", "hotel:2", "hotel:3", "hotel:4", "train:1"]
    assert [c["name"] for c in merged] == ["hotel col 1", "hotel col 2", "hotel_2 col 1", "hotel_2 col 2", "train col 1"]
    assert [c["mention_ids"] for c in merged] == [[0, 1], [2, 3], [6, 7], [8, 9], [4, 5]]
    assert S4.entity_tables(merged) == ["hotel", "train"]


def test_merge_a_columns_reaches_step4(tmp_path):
    out, cols = step3_dir(tmp_path)
    mention_table(tmp_path)
    assert EN.merge_a_columns(out, SET, {}, log=lambda *_: None) is None                           # nothing to merge: file untouched
    assert B.read_json(out / "a_llama44" / SET / "a.columns.json") == cols
    assert EN.merge_a_columns(out, SET, {"hotel": ["hotel", "hotel_2"]}, log=lambda *_: None) == 5
    assert B.read_json(out / "a_llama44" / SET / "a.premerge.columns.json") == cols
    s4out = tmp_path / "s4"
    chains = S4.make_chains(s4out, ("a_llama44",), (SET,), (0,), PL.step4_config("v43"), {"a_llama44": out / "a_llama44"}, tmp_path, lambda *_: None)
    assert len(chains) == 1                                                                         # all switches off: no vote, no values file
    jobs = S4.build_stage(s4out, 1, chains, tmp_path)
    prompt = (s4out / jobs[0]["prompt"]).read_text(encoding="utf-8")
    assert jobs[0]["n_columns"] == 5
    assert "[hotel_2:" not in prompt and "[hotel:4] hotel_2 col 2" in prompt and "[train:1]" in prompt   # one hotel block, the columns stay
    score_map = {p.stem: B.read_json(p) for p in (s4out / "score_map" / "a_llama44" / SET).glob("*.json")}
    assert sorted(score_map) == ["hotel", "train"] and len(score_map["hotel"]["columns"]) == 4
    assert score_map["hotel"]["columns"][2] == {"id": "3", "mention_ids": [6, 7]}
    cfg = S4.with_switches(PL.step4_config("v43"), off=(), key_candidates=True)
    vals = S4.column_values("a_llama44", SET, out / "a_llama44" / SET / "a.columns.json", B.read_json(out / "a_llama44" / SET / "a.columns.json"), tmp_path)
    assert vals["hotel:3"] == {"n": 2, "values": ["v6", "v7"]} and cfg["switches"]["key_candidates"]


# ---------------------------------------------------------------- pipeline_v46 order (the heavy steps are stubbed)
def test_run_pipeline_loops(tmp_path):
    with pytest.raises(ValueError, match="gliner_loader"):
        PL46.run_pipeline("c.jsonl", tmp_path, SET, None, None, None, None, loops=2)
    with pytest.raises(ValueError):
        PL46.run_pipeline("c.jsonl", tmp_path, SET, None, None, None, None, loops=3)


def test_run_pipeline_order(tmp_path, monkeypatch):
    """Steps 1a-2 -> names -> Step 3 -> merge -> Step 4: Step 3 gets the unique keys, Step 4 gets the merged input."""
    write_run(tmp_path / "root")
    calls = []
    monkeypatch.setattr(PL46.CO, "step1a", lambda *a, **k: calls.append("1a") or {"entities": {}})
    monkeypatch.setattr(PL46.CO, "run_dir", lambda s, root=None: tmp_path / "root" / "results" / f"graph_v22_{s}")
    monkeypatch.setattr(EN.CO, "run_dir", PL46.CO.run_dir)
    monkeypatch.setattr(PL46.PL, "use_corpus", lambda *a: __import__("contextlib").nullcontext())
    monkeypatch.setattr(PL46.PL, "build_prompts", lambda s, entmap, a_dir: calls.append(("prompts", dict(entmap))))

    def step3(s, out, backend, enc):
        calls.append("step3")
        step3_dir(Path(out).parent)
        assert Path(out) == tmp_path / "out" / "step3"
        return {}, {}

    def step4(s, out, backend, step3_out, cfg):
        calls.append("step4")
        assert len(B.read_json(Path(step3_out) / "a_llama44" / s / "a.columns.json")) == 5
    monkeypatch.setattr(PL46.PL, "step3", step3)
    monkeypatch.setattr(PL46.PL, "step4", step4)

    def loop2(out, s, backend, enc, gl, cfg, log=print):
        calls.append("loop2")       # before the merge: loop 2 reads the unmerged Step 3 columns
        assert len(B.read_json(Path(out) / "step3" / "a_llama44" / s / "a.columns.json")) == 5
        assert not (Path(out) / "step3" / "a_llama44" / s / "a.premerge.columns.json").exists()
        return {"cost": {"total": {"calls": 7}}}
    monkeypatch.setattr(PL46.L2, "run_loop2", loop2)
    monkeypatch.setattr(PL46.PL, "outputs", lambda out, s, info, load: (B.write_json(Path(out) / "attributes.json", {"hotel": ["a"], "train": ["b"], "hotel_2": ["c"]})
                                                                          or {"total_llm": {"calls": 1, "prompt_tokens": 10, "output_tokens": 2}}))
    # the Step 3 stub writes columns for the keys hotel / train / hotel_2: the names backend answers "hotel" / "train" / "hotel"
    class Names(EN.FakeNames):
        def respond(self, job, prompt, schema):
            return json.dumps({"name": {"E0": "hotel", "E1": "train", "E2": "hotel"}[job["entity"]]})

    out = tmp_path / "out"
    c = PL46.run_pipeline("c.jsonl", out, SET, None, None, None, None, backend4=None, names_backend=Names(), log=lambda *_: None)
    assert calls == ["1a", ("prompts", {"hotel": "E0", "train": "E1", "hotel_2": "E2"}), "step3", "step4"]
    assert c["entity_names"]["calls"] == 3 and c["total_llm"]["calls"] == 4
    assert B.read_json(out / "entity_names.json")["groups"] == {"hotel": ["E0", "E2"], "train": ["E1"]}
    assert B.read_json(out / "entities.json") == {"hotel": "E0", "train": "E1", "hotel_2": "E2"}
    shutil.rmtree(out)
    calls.clear()
    c = PL46.run_pipeline("c.jsonl", out, SET, None, None, None, None, names_backend=Names(), log=lambda *_: None, loops=2, gliner_loader=object)
    assert calls == ["1a", ("prompts", {"hotel": "E0", "train": "E1", "hotel_2": "E2"}), "step3", "loop2", "step4"]
    assert c["loop2"] == {"total": {"calls": 7}} and c["total_llm"]["calls"] == 4
    shutil.rmtree(out)
    calls.clear()
    seen = {}
    monkeypatch.setattr(PL46.S4, "run", lambda o, b, **kw: seen.update(kw) or calls.append("s4run"))
    PL46.run_pipeline("c.jsonl", out, SET, None, None, None, None, names_backend=Names(), log=lambda *_: None, step4_seeds=(0,))
    assert calls[-1] == "s4run" and "step4" not in calls and seen["seeds"] == (0,) and seen["sets"] == (SET,)
