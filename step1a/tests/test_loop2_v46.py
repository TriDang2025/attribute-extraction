"""wf_v4.6 Y4: s1a/loop2_v46.py (loop 2 for the 8B design). Pure tests first, then loop 2 end to end with the fake model (no GPU, no
model download) on the tracked n50 corpus run (results/graph_v22_c_n50 + results/wf_v45/w2/n50/step3)."""
import json
import re
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from s1a import batch_v4 as B
from s1a import loop2_v46 as L
from s1a import step1b_v41 as S1B

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SET, LOOP1 = "c_n50", ROOT / "results" / "wf_v45" / "w2" / "n50"
need_data = pytest.mark.skipif(not (ROOT / "results" / "graph_v22_c_n50" / "spans" / "vectors.npz").exists()
                               or not (LOOP1 / "step3" / "scores" / "final_columns.json").exists(),
                               reason="n50 corpus run not in this checkout")
CFG = L.load_config()


def col(i, name, ent="hotel", examples=(("north", "in the north part"),)):
    return {"id": f"{ent}:{i}", "name": name, "description": "", "role": "", "value_type": "text", "examples": [list(e) for e in examples],
            "n_mentions": 5, "n_dialogues": 3, "signal": "", "flag": ""}


COLS = [col(1, "area"), col(2, "price range"), col(3, "stars")]


def has_key(obj, key):
    if isinstance(obj, dict):
        return key in obj or any(has_key(v, key) for v in obj.values())
    return isinstance(obj, list) and any(has_key(v, key) for v in obj)


# ---------------------------------------------------------------- config
def test_evidence_defaults_equal_the_v41_config():
    assert CFG["evidence"] == json.loads((ROOT / "config" / "wf_v41_loop2.json").read_text(encoding="utf-8"))
    assert CFG["evidence"] == {"k": 40, "threshold": 0.3, "min_dialogues": 3, "min_support": 0.05, "max_overlap": 0.5}
    assert CFG["step1b"]["orders"] == [0, 1, 2] and CFG["step1b"]["min_votes"] == 2 and CFG["step1b"]["max_new"] == 10


def test_config_override_and_errors():
    c = L.load_config(evidence={"k": 5}, step1b={"min_votes": 3})
    assert c["evidence"]["k"] == 5 and c["evidence"]["threshold"] == 0.3 and c["step1b"]["min_votes"] == 3 and CFG["evidence"]["k"] == 40
    with pytest.raises(ValueError):
        L.load_config(evidence={"nope": 1})
    with pytest.raises(ValueError):
        L.load_config(nope={})


# ---------------------------------------------------------------- schemas and prompts
def test_verdicts_schema_is_keyed_exactly_once_without_pattern():
    ids = [c["id"] for c in COLS]
    s = L.verdicts_schema(ids)
    assert list(s["properties"]) == ids and s["required"] == ids and s["additionalProperties"] is False
    one = s["properties"][ids[0]]
    assert one["properties"]["verdict"] == {"enum": ["keep", "flag"]} and one["required"] == ["verdict", "reason"]
    assert not has_key(s, "pattern") and not has_key(s, "anyOf")


def test_missing_schema_has_max_items_10_without_pattern():
    s = L.missing_schema(CFG["step1b"]["max_new"])
    assert s["properties"]["missing"]["maxItems"] == 10 and s["required"] == ["missing"]
    assert not has_key(s, "pattern")


def test_prompts_ask_the_two_closed_questions_about_the_entity():
    p = L.question_prompts("hotel", COLS, CFG)
    v, m = p["verdicts"][0], p["missing"][0]
    assert "is each attribute a good attribute of a hotel" in v and "[hotel:1] area" in v and "exactly once" in v
    assert "which information is still missing for this hotel" in m and "At most 10" in m and "[hotel:3] stars" in m
    assert "== hotel ==" in v and v.rstrip().endswith("Return the JSON object now.")
    assert p["verdicts"][1]["required"] == [c["id"] for c in COLS]


def test_example_cap_is_the_step1b_cap():
    many = [col(1, "area", examples=[(f"v{i}", f"ctx v{i}") for i in range(9)])]
    text = L.question_prompts("hotel", many, CFG)["verdicts"][0]
    assert text.count("(in: ") == S1B.MAX_EXAMPLES == 3


def test_build_step1b_writes_two_jobs_per_order_and_entity(tmp_path):
    jobs = L.build_step1b(tmp_path, "s", {"hotel": COLS, "train": [col(1, "leave", "train")]}, CFG)
    assert len(jobs) == 2 * 2 * 3 and {j["format"] for j in jobs} == {"s1b"} and len({j["job"] for j in jobs}) == 12
    j = next(j for j in jobs if j["ent"] == "hotel" and j["question"] == "verdicts" and j["order"] == 1)
    assert j["job"] == "l2s1b_s_hotel_verdicts_s1" and j["max_tokens"] == 60 * 3 + 100
    text = (tmp_path / j["prompt"]).read_text(encoding="utf-8")
    shuffled_1 = re.findall(r"^\[(hotel:\d)\]", text, re.M)
    other = (tmp_path / next(x for x in jobs if x["job"] == "l2s1b_s_hotel_verdicts_s2")["prompt"]).read_text(encoding="utf-8")
    assert sorted(shuffled_1) == ["hotel:1", "hotel:2", "hotel:3"]
    assert json.loads((tmp_path / j["schema"]).read_text(encoding="utf-8"))["required"] == shuffled_1      # keys in the order shown
    assert shuffled_1 != re.findall(r"^\[(hotel:\d)\]", other, re.M) or len(COLS) < 3


# ---------------------------------------------------------------- parse
def test_parse_verdicts_good_and_bad():
    ids = ["h:1", "h:2", "h:3"]
    good = {i: {"verdict": "keep", "reason": " fine "} for i in ids}
    got, errs = L.parse_verdicts(good, ids)
    assert errs == [] and got["h:1"] == {"verdict": "keep", "reason": "fine"}
    got, errs = L.parse_verdicts({"h:1": {"verdict": "drop", "reason": "x"}, "h:2": "keep", "h:9": {"verdict": "flag", "reason": ""},
                                  "h:3": {"verdict": "flag", "reason": "noise"}}, ids)
    assert list(got) == ["h:3"] and len(errs) == 3 and any("unknown key" in e for e in errs)
    assert L.parse_verdicts([], ids) == ({}, ["answer is not a JSON object"])


def test_parse_missing_good_and_bad():
    items, errs = L.parse_missing({"missing": [{"name": "Parking Facility", "description": "d"}, {"name": "parking_facility", "description": "x"},
                                               {"name": "", "description": "no name"}]}, 10)
    assert [i["name"] for i in items] == ["Parking Facility"] and len(errs) == 1
    assert L.parse_missing({"missing": []}, 10) == ([], [])
    assert L.parse_missing([{"name": "a b", "description": ""}], 10)[0] == [{"name": "a b", "description": ""}]   # bare list (unguided retry)
    assert L.parse_missing({"x": 1}, 10)[1] == ["answer has no missing list"]
    many = {"missing": [{"name": f"n{i}", "description": ""} for i in range(12)]}
    items, errs = L.parse_missing(many, 10)
    assert len(items) == 10 and "max 10" in errs[0]


# ---------------------------------------------------------------- vote
def v(verdict):
    return {"verdict": verdict, "reason": "r" if verdict == "flag" else ""}


def test_verdict_vote_is_a_strict_majority_and_never_drops():
    ids = ["h:1", "h:2", "h:3", "h:4"]
    per = {0: {"h:1": v("flag"), "h:2": v("flag"), "h:3": v("flag"), "h:4": v("keep")},
           1: {"h:1": v("flag"), "h:2": v("keep"), "h:3": v("flag")},          # h:4 not answered
           2: {"h:1": v("keep"), "h:2": v("keep"), "h:4": v("keep")}}          # h:3 not answered
    out = L.vote_verdicts(per, ids)
    assert [out[i]["verdict"] for i in ids] == ["flag", "keep", "flag", "keep"]       # h:3: 2 of 2 flag
    assert out["h:1"]["flags"] == 2 and out["h:1"]["votes"] == 3 and out["h:1"]["reasons"] == ["r", "r"]
    assert set(out) == set(ids)                                                       # every attribute stays
    tie = L.vote_verdicts({0: {"h:1": v("flag")}, 1: {"h:1": v("keep")}}, ["h:1"])
    assert tie["h:1"]["verdict"] == "keep"                                            # a tie keeps
    assert L.vote_verdicts({}, ["h:1"])["h:1"]["verdict"] == "keep"                   # no vote keeps


def test_name_vote_needs_two_orders_after_normalisation():
    per = {0: [{"name": "Check_in Time", "description": "a"}, {"name": "pool", "description": ""}],
           1: [{"name": "check in time", "description": "b"}, {"name": "check in  time", "description": "c"}],
           2: [{"name": "Pool", "description": "p"}, {"name": "spa", "description": ""}]}
    rows = {r["key"]: r for r in L.vote_names(per, 2)}
    assert rows["check in time"]["votes"] == 2 and rows["check in time"]["orders"] == [0, 1] and rows["check in time"]["voted"]   # once per order
    assert rows["check in time"]["description"] == "a"
    assert rows["pool"]["voted"] and rows["pool"]["description"] == "p"            # description from the first order that has one
    assert rows["spa"]["votes"] == 1 and not rows["spa"]["voted"]
    assert [r["key"] for r in L.vote_names(per, 2)][-1] == "spa"
    assert not L.vote_names(per, 3)[0]["voted"]


def test_screen_reasons():
    existing, values = {"area"}, S1B.example_values([col(1, "area", examples=[("Ashley Hotel", "stay at the Ashley Hotel")])])

    def sg(key, votes=2):
        return {"key": key, "voted": votes >= 2, "votes": votes}
    assert L.screen(sg("spa", 1), 3, existing, values, CFG) == ("vote", "suggested in 1 of 3 orders (needs 2)")
    assert L.screen(sg("area"), 3, existing, values, CFG)[1] == "repeats an existing attribute name"
    assert "longer than 4 words" in L.screen(sg("a b c d e"), 3, existing, values, CFG)[1]
    assert "example value" in L.screen(sg("ashley hotel"), 3, existing, values, CFG)[1]
    assert "corpus word" in L.screen(sg("dialogue length"), 3, existing, values, CFG)[1]
    assert L.screen(sg("parking facility"), 3, existing, values, CFG) == ("", "")


# ---------------------------------------------------------------- evidence thresholds
class FakeEnc:
    def encode(self, texts):
        out = np.zeros((len(texts), 3))
        for i, t in enumerate(texts):
            out[i, 0 if "price" in t or "pound" in t else 1 if "phone" in t else 2] = 1.0
        return out


class FakeGliner:
    def inference(self, texts, labels, threshold=0.3, batch_size=8):
        pat = r"\d+ pounds" if labels[0] == "price" else r"\d{4}"
        return [[dict(start=m.start(), end=m.end(), score=0.9, text=m.group()) for m in re.finditer(pat, t)] for t in texts]


def tiny_ri():
    def doc(did, turns):
        text, spans, pos = "", [], 0
        for i, t in enumerate(turns):
            line = ("User" if i % 2 == 0 else "System") + ": " + t
            spans.append((pos, pos + len(line)))
            text += line + "\n"
            pos += len(line) + 1
        return SimpleNamespace(doc_id=did, text=text.rstrip("\n"), spans=spans)
    docs = {"D1": doc("D1", ["I need a train", "The price is 12 pounds", "ok", "phone 0123"]), "D2": doc("D2", ["hello", "ticket price 9 pounds"]),
            "D3": doc("D3", ["hello there", "nothing here"])}
    inst = pd.DataFrame([("D1|0", "E1", "D1", 0, 3), ("D2|0", "E1", "D2", 0, 1), ("D3|0", "E2", "D3", 0, 1)],
                        columns=["instance_id", "entity", "dialogue_id", "start_turn", "end_turn"])
    mt = pd.DataFrame([dict(mention_id=1, dialogue_id="D1", instance_id="D1|0", char_start=0, char_end=3),
                       dict(mention_id=2, dialogue_id="D2", instance_id="D2|0", char_start=0, char_end=1)])
    return SimpleNamespace(docs=docs, export=SimpleNamespace(mentions=mt, instances=inst))


def test_evidence_thresholds_come_from_the_config():
    labels = [{"entity": "train", "name": "price", "label": "price", "description": "d", "value_type": "text"}]
    finals = {"train": [dict(name="leaving", mention_ids=[1, 2])]}
    cfg = L.load_config(evidence={"k": 3, "min_dialogues": 2})
    c = L.run_evidence(tiny_ri(), labels, finals, {"train": "E1"}, FakeEnc(), FakeGliner, cfg, log=lambda *_: None)[0]
    assert c["id"] == "L2_train#0" and c["n_dialogues"] == 2 and c["keep"] and c["mentions"][0]["mention_id"] == 3
    strict = L.load_config(evidence={"k": 3, "min_dialogues": 3})
    assert not L.run_evidence(tiny_ri(), labels, finals, {"train": "E1"}, FakeEnc(), FakeGliner, strict, log=lambda *_: None)[0]["keep"]
    assert c["reason"] == "all checks passed"
    assert L.run_evidence(tiny_ri(), [], finals, {}, FakeEnc(), FakeGliner, cfg) == []


def test_gliner_loader_is_called_only_when_a_name_reaches_the_check():
    def boom():
        raise AssertionError("loaded")
    assert L.run_evidence(tiny_ri(), [], {}, {}, FakeEnc(), boom, CFG) == []


# ---------------------------------------------------------------- merge and outcomes
def test_merged_columns_keep_every_loop1_column_even_when_flagged():
    finals = {"hotel": [{"cid": 1, "name": "area", "description": "", "n_mentions": 4}, {"cid": 2, "name": "stars", "description": "", "n_mentions": 3}]}
    review = {"hotel": {"verdicts": {"hotel:1": {"verdict": "flag", "reasons": ["noise"]}, "hotel:2": {"verdict": "keep", "reasons": []}}}}
    final = {"hotel": [{"name": "pool", "description": "d", "clusters": ["L2_hotel#0"], "top_values": ["x"], "n_mentions": 2, "status": "new",
                        "joined": []}, {"name": "dup", "description": "", "clusters": ["L2_hotel#1"], "status": "duplicate", "duplicate_of": ["area"],
                                        "reason": "same name", "joined": []}]}
    cl = {"L2_hotel#0": {"mentions": [{"mention_id": 9}, {"mention_id": 7}]}}
    rows = L.merged_columns(finals, review, final, cl)["hotel"]
    assert [r["name"] for r in rows] == ["area", "stars", "pool"] and rows[0]["flag"] == "flag" and rows[0]["source"] == "loop1"
    assert rows[2]["source"] == "loop2" and rows[2]["cid"] == 3 and rows[2]["mention_ids"] == [7, 9]


def test_outcomes_name_the_failing_stage():
    rows = [{"entity": "h", "name": n, "stage": s, "reason": r} for n, s, r in
            [("a", "vote", "v"), ("b", "", ""), ("c", "", ""), ("d", "", ""), ("e", "", ""), ("f", "", "")]]
    cl = [{"id": f"L2_h#{i}", "entity": "h", "label": n, "keep": n != "b", "reason": "no spans"} for i, n in enumerate("bcdef")]
    final = {"h": [{"name": "c", "clusters": ["L2_h#1"], "status": "new", "joined": []},
                   {"name": "d", "clusters": ["L2_h#2"], "status": "duplicate", "duplicate_of": ["x"], "reason": "same name", "joined": []}]}
    L.outcomes(rows, final, {"h": {"L2_h#3": "not_attribute", "L2_h#4": ""}}, cl)
    got = {r["name"]: (r["passed"], r["stage"]) for r in rows}
    assert got["a"] == (False, "vote") and got["b"] == (False, "evidence") and got["c"] == (True, "added")
    assert got["d"] == (False, "dupcheck") and got["e"] == (False, "step3")
    assert "not_attribute" in next(r for r in rows if r["name"] == "e")["reason"]


# ---------------------------------------------------------------- end to end (fake LLM, real n50 data)
class HotelGliner:
    """Spans for the label "parking facility" only (the words free / parking / internet / wifi); no span for any other label."""

    def inference(self, texts, labels, threshold=0.3, batch_size=8):
        pat = r"\b(free|parking|internet|wifi)\b" if labels[0] == "parking facility" else r"\bzzzzqq\b"
        return [[dict(start=m.start(), end=m.end(), score=0.9, text=m.group()) for m in re.finditer(pat, t, re.I)] for t in texts]


class HashEnc:
    """Hashed character trigrams, unit vectors (same idea as step3_v44.FakeEncoder, with .encode)."""

    def encode(self, texts):
        from s1a import step3_v44 as S3_44
        return S3_44.FakeEncoder()(texts)


@pytest.fixture(scope="module")
def loop1_copy(tmp_path_factory):
    out = tmp_path_factory.mktemp("loop1")
    for rel in ("scores/final_columns.json", f"a_llama44/{SET}/a.columns.json"):
        (out / "step3" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(LOOP1 / "step3" / rel, out / "step3" / rel)
    return out


@need_data
def test_run_loop2_end_to_end_with_the_fake_model(loop1_copy):
    fake = L.FakeLoop2LLM()
    info = L.run_loop2(loop1_copy, SET, fake, HashEnc(), HotelGliner, CFG, log=lambda *_: None)
    l2 = loop1_copy / "loop2"
    for f in ("step1b/review.json", "step1b/labels.json", "step1b/manifest.json", "evidence/clusters.json", "evidence/evidence.csv",
              "evidence/summary.md", "evidence/run_info.json", "step3/manifest_names.json", "step3/manifest_dupcheck.json", "step3/naming.json",
              "columns_l2.json", "merged_columns.json", "attributes.json", "a2.columns.json", "suggestions.csv", "report.md", "calls.csv",
              "cost.json", "run_info.json"):
        assert (l2 / f).exists(), f
    finals = B.read_json(loop1_copy / "step3" / "scores" / "final_columns.json")[SET]
    n_attr = sum(len(c) for c in finals.values())
    assert info["attributes"] == n_attr and info["entities"] == len(finals) and info["flagged"] == len(finals)   # first attribute per entity flagged
    merged = B.read_json(l2 / "merged_columns.json")
    for ent, cols in finals.items():                                    # nothing dropped, the flagged one stays
        assert [c["name"] for c in cols] == [r["name"] for r in merged[ent] if r["source"] == "loop1"]
    assert sum(r["flag"] == "flag" for rs in merged.values() for r in rs) == len(finals)
    sug = pd.read_csv(l2 / "suggestions.csv", keep_default_na=False)
    by = {(r.entity, r.name): r for r in sug.itertuples()}
    hotel = {n: r for (e, n), r in by.items() if e == "hotel"}
    assert hotel["parking facility"].passed and hotel["parking facility"].stage == "added"           # 3 votes, spans, new column
    assert hotel["contact number"].stage == "vote" and "1 of 3" in hotel["contact number"].reason     # one order only
    assert hotel["area"].stage == "check" and "existing" in hotel["area"].reason                      # repeats a loop-1 name
    assert hotel["star rating"].stage == "evidence" and hotel["star rating"].reason == "no spans"     # 2 votes, GLiNER finds nothing
    assert hotel["parking facility"].reason.startswith("new column fake_new_")                                # named by the fake Step 3
    new = [r["name"] for r in merged["hotel"] if r["source"] == "loop2"]
    assert len(new) == 1 and new[0] in B.read_json(l2 / "attributes.json")["hotel"] and len(merged["hotel"]) == len(finals["hotel"]) + 1
    assert info["new_columns"] == sum(r["source"] == "loop2" for rs in merged.values() for r in rs) >= 1
    assert (l2 / "report.md").read_text(encoding="utf-8").count("| pass |") == info["new_columns"]
    a2 = B.read_json(l2 / "a2.columns.json")
    assert len(a2) == n_attr + info["new_columns"] and any(c["name"] == new[0] for c in a2)
    calls = pd.read_csv(l2 / "calls.csv")
    assert info["cost"]["step1b"]["calls"] == 2 * 3 * len(finals) == (calls["file"].str.startswith("step1b/")).sum()
    assert info["cost"]["step3"]["calls"] >= 3 and info["cost"]["total"]["prompt_tokens"] > 0
    # all schemas of the run: no regex pattern
    for p in list(l2.glob("step1b/prompts/*.schema.json")) + list(l2.glob("step3/prompts/*.schema.json")):
        assert not has_key(json.loads(p.read_text(encoding="utf-8")), "pattern"), p.name


@need_data
def test_run_loop2_without_a_passing_name_still_writes_the_outputs(loop1_copy, tmp_path):
    out = tmp_path / "o"
    shutil.copytree(loop1_copy / "step3", out / "step3", ignore=shutil.ignore_patterns("loop2"))
    cfg = L.load_config(evidence={"min_dialogues": 10 ** 6})
    info = L.run_loop2(out, SET, L.FakeLoop2LLM(), HashEnc(), HotelGliner, cfg, log=lambda *_: None)
    assert info["evidence_kept"] == 0 and info["new_columns"] == 0 and info["cost"]["step3"]["calls"] == 0
    assert (out / "loop2" / "attributes.json").exists()
    rows = pd.read_csv(out / "loop2" / "suggestions.csv", keep_default_na=False)
    assert "n_dialogues" in rows[rows.name == "parking facility"].iloc[0].reason


@need_data
def test_run_loop2_reads_the_premerge_columns_after_a_merge(loop1_copy, tmp_path):
    out = tmp_path / "m"
    shutil.copytree(loop1_copy / "step3", out / "step3", ignore=shutil.ignore_patterns("loop2"))
    a = out / "step3" / "a_llama44" / SET / "a.columns.json"
    shutil.copy(a, a.with_name("a.premerge.columns.json"))
    B.write_json(a, [])                                                  # a merged file loop 2 must not read
    cfg = L.load_config(evidence={"min_dialogues": 10 ** 6})
    info = L.run_loop2(out, SET, L.FakeLoop2LLM(), HashEnc(), HotelGliner, cfg, log=lambda *_: None)
    finals = B.read_json(out / "step3" / "scores" / "final_columns.json")[SET]
    assert info["attributes"] == sum(len(c) for c in finals.values())
