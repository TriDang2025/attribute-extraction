import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_input as P  # noqa: E402
from s1a import step2 as S2  # noqa: E402
from chk.data import make_doc  # noqa: E402

N = 6
CITY = ["cambridge", "london", "ely", "bath", "leeds", "york"]
SECRET = ("ZZATTR", "ZZINST", "ZZDLG")  # strings of withheld columns; must never reach a prompt


def make_docs():
    docs = {}
    for i in range(N):
        t = [f"User: I want to go to {CITY[i]} at 1{i}:00 on monday and need {i + 1} seats and {i + 7} tickets.",
             f"System: it arrives at 2{i}:30 sharp.",
             "User: please add a stay for monday.",
             "System: done for the night."]
        docs[f"ZZDLG{i}"] = make_doc(f"ZZDLG{i}", [{"id": "x", "turns": t, "domains": ["a"] * 4}])
    return docs


def toy():
    """E0: 5 clusters (city, time, day, seats+tickets with 2 values per instance, a time fragment that
    never shares an instance with the time cluster); E1: 2 clusters, one sharing the value "monday"."""
    docs = make_docs()
    rows = []
    # (cluster, turn, text of dialogue i, instance suffix, vector, gliner score)
    spec = [("E0#0", 0, lambda i: CITY[i], "0", (1, 0, 0), 0.9),
            ("E0#1", 0, lambda i: f"1{i}:00", "0", (0, 1, 0), 0.8),
            ("E0#2", 0, lambda i: "monday", "0", (0, 0, 1), 0.7),
            ("E0#4", 0, lambda i: f"{i + 1} seats", "0", (1, 1, 0), 0.6),
            ("E0#4", 0, lambda i: f"{i + 7} tickets", "0", (1, 1, 0), 0.6),
            ("E0#3", 1, lambda i: f"2{i}:30", "9", (0.1, 1, 0), 0.95),
            ("E1#0", 2, lambda i: "monday", "1", (0, 0, 1), 0.9),
            ("E1#1", 3, lambda i: "night", "1", (1, 0, 1), 0.8)]
    for c, turn, f, inst, v, sc in spec:
        for i in range(N):
            d = docs[f"ZZDLG{i}"]
            s = d.text.index(f(i), d.spans[turn][0])
            ent = c.split("#")[0]
            rows.append(dict(mention_id=len(rows), input="spans", dialogue_id=d.doc_id, turn=turn, char_start=s,
                             char_end=s + len(f(i)), text=f(i), norm_value=S2.normalize(f(i)).lower(),
                             left_word="to", context="", cluster_id=c, entity=ent,
                             entity_gold="train" if ent == "E0" else "hotel", instance_id=f"{d.doc_id}|{inst}",
                             gold_attr="ZZATTR", gliner_score=sc, _v=v))
    m = pd.DataFrame(rows)
    x = np.array(list(m.pop("_v")), dtype=np.float32)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    inst = [(f"ZZDLG{i}|0", "E0", f"ZZDLG{i}", 0, 0) for i in range(N)]
    inst += [(f"ZZDLG{i}|9", "E0", f"ZZDLG{i}", 1, 1) for i in range(N)]
    inst += [(f"ZZDLG{i}|1", "E1", f"ZZDLG{i}", 2, 3) for i in range(N)]
    inst = pd.DataFrame(inst, columns=["instance_id", "entity", "dialogue_id", "start_turn", "end_turn"])
    export = SimpleNamespace(mentions=m, clusters=MN.cluster_table(m), instances=inst,
                             ids=m["mention_id"].to_numpy(), x=x)
    return export, docs


@pytest.fixture(scope="module")
def built():
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    return export, docs, inp, {c.cluster_id: c for c in inp.clusters}


def table(values, dialogues):
    return pd.DataFrame(dict(cluster_id="E0#0", norm_value=values, dialogue_id=dialogues,
                             mention_id=range(len(values))))


def test_pilot_entity_by_majority():
    export, _ = toy()
    assert P.find_pilot_entity(export.mentions, "train") == "E0"
    assert P.find_pilot_entity(export.mentions, "hotel") == "E1"
    with pytest.raises(ValueError):
        P.find_pilot_entity(export.mentions, "taxi")


def test_examples_are_diverse_and_deterministic():
    g = table(["a"] * 25 + list("bcdef"), [f"d{i}" for i in range(30)])
    pick = P.select_examples(g, 8, seed=1)
    vals = g.set_index("mention_id").loc[pick, "norm_value"]
    assert len(pick) == 8 and vals.nunique() == 6 and (vals == "a").sum() == 3  # never 8 copies of one value
    assert pick == P.select_examples(g, 8, seed=1)
    assert pick != P.select_examples(g, 8, seed=2)


def test_examples_spread_over_dialogues_and_small_cluster():
    g = table(["a"] * 4, ["d0", "d0", "d1", "d2"])
    pick = P.select_examples(g, 3, seed=0)
    assert len(set(g.set_index("mention_id").loc[pick, "dialogue_id"])) == 3
    small = table(["a", "b", "a"], ["d0", "d1", "d2"])
    assert sorted(P.select_examples(small, 8)) == [0, 1, 2]  # fewer than 8


def test_examples_in_inputs_are_distinct_mentions(built):
    _, _, _, by = built
    c = by["E0#0"]
    assert len(c.examples) == 6 and len({m for _, m in c.examples}) == 6
    assert [e for e, _ in c.examples] == [f"E0#0:{j}" for j in range(6)]


def test_exclusive_flag(built):
    _, _, _, by = built
    mg = {h["other"]: h for h in by["E0#1"].merge}
    assert mg["E0#3"]["exclusive"] is True        # never in the same instance
    assert mg["E0#0"]["exclusive"] is False
    assert [h["other"] for h in by["E0#1"].merge][0] == "E0#3"  # nearest centroid first
    assert len(by["E0#1"].merge) == 3


def test_cosine_percentile_range(built):
    _, _, inp, by = built
    for c in inp.clusters:
        for h in c.merge:
            assert 0 <= h["pct"] <= 100
    assert {h["other"]: h["pct"] for h in by["E0#1"].merge}["E0#3"] == 100.0  # the closest pair of the entity


def test_low_conf_bottom_third(built):
    export, _, inp, _ = built
    assert P.low_conf_clusters(export.mentions, "E0") == {"E0#4"}  # 5 clusters -> 1; lowest mean score
    assert [c.cluster_id for c in inp.clusters if c.low_conf] == ["E0#4"]


def test_cardinality_favours_separate_table(built):
    _, _, _, by = built
    sep = {p["option"]: p for p in by["E0#4"].placement}[P.SEPARATE]
    assert sep["raw_card"] == 2.0 and sep["signals"]["cardinality"] > 0.5
    one = {p["option"]: p for p in by["E0#0"].placement}[P.SEPARATE]
    assert one["raw_card"] == 1.0 and one["signals"]["cardinality"] == 0.0


def test_shared_values(built):
    _, _, _, by = built
    rel = {p["option"]: p for p in by["E0#2"].placement}["relationship(E0, E1)"]
    assert rel["signals"]["shared values"] == 1.0  # "monday" is also an E1 value in each dialogue
    rel0 = {p["option"]: p for p in by["E0#0"].placement}["relationship(E0, E1)"]
    assert rel0["signals"]["shared values"] == 0.0


def test_placement_signals_and_rank(built):
    _, _, _, by = built
    pl = by["E0#0"].placement
    opt = {p["option"]: p for p in pl}
    assert opt["current entity E0"]["signals"]["entity share"] == 1.0
    assert 0 <= opt["other entity E1"]["signals"]["entity share"] <= 1
    assert opt["sub-entity of E0"]["signals"] == {}
    scores = [p["score"] for p in pl if p["signals"]]
    assert scores == sorted(scores, reverse=True) and all(0 <= s <= 1 for s in scores)
    assert not pl[-1]["signals"]  # no-signal options last


def test_withheld_fields_absent(built):
    export, docs, inp, _ = built
    for v in P.VARIANTS:
        text = P.render(inp, export, docs, v)
        assert not any(s in text for s in SECRET)
        assert "train" not in text.lower() and "hotel" not in text.lower()
        assert "E0#0" in text and "[[" in text


def test_nocontext_has_no_context(built):
    export, docs, inp, _ = built
    full, nc = P.render(inp, export, docs, "full"), P.render(inp, export, docs, "nocontext")
    assert "I want to go to" in full and "previous turn" in full and "[user]" in full
    assert "I want to go to" not in nc and "it arrives at" not in nc and "previous turn" not in nc
    assert "[[cambridge]]" in nc and "Merge suggestions" in nc


def test_nohints_has_no_hints(built):
    export, docs, inp, _ = built
    nh = P.render(inp, export, docs, "nohints")
    assert "Merge suggestions" not in nh and "Placement suggestions" not in nh and "percentile" not in nh
    assert "Placement options" in nh and "I want to go to" in nh
    assert "Merge suggestions" in P.render(inp, export, docs, "full")


def test_other_entities_listed_by_id_and_top_values(built):
    export, docs, inp, _ = built
    assert list(inp.others) == ["E1"] and [c for c, _ in inp.others["E1"]] == ["E1#0", "E1#1"]
    assert "- E1: monday; night" in P.render(inp, export, docs, "full")


def test_example_text_marks_mention_and_previous_turn(built):
    export, docs, _, _ = built
    mm = export.mentions
    r = mm[(mm.cluster_id == "E0#3") & (mm.dialogue_id == "ZZDLG0")].iloc[0]
    spk, prev, turn = P.example_text(docs["ZZDLG0"], r)
    assert spk == "system" and turn == "it arrives at [[20:30]] sharp."
    assert prev.startswith("user: I want to go to cambridge")


# ------------------------------------------------------------------ wf_v3.1
def ids_in_order(text, ids):
    return [c for c in sorted(ids, key=text.index)]


def test_v2_render_every_cluster_once_and_shuffle(built):
    export, docs, inp, _ = built
    ids = [c.cluster_id for c in inp.clusters]
    for v in P.VARIANTS_V2:
        text = P.render_v2(inp, export, docs, v)
        assert all(text.count(f"### {c} ") == 1 for c in ids)
        assert "graduation_year" in text and "Return the JSON object" in text
        assert not any(s in text for s in SECRET)
        assert "train" not in text.lower() and "hotel" not in text.lower()
    sh = P.render_v2(inp, export, docs, "v2", order_seed=1)
    assert sh == P.render_v2(inp, export, docs, "v2", order_seed=1)
    assert all(sh.count(f"### {c} ") == 1 for c in ids)
    order = lambda t: [c for c in sorted(ids, key=lambda c: t.index(f"### {c} "))]  # noqa: E731
    assert order(P.render_v2(inp, export, docs, "v2")) == ids and order(sh) != ids


def test_v2_variants_context_and_hints(built):
    export, docs, inp, _ = built
    nc = P.render_v2(inp, export, docs, "v2_nocontext")
    assert "I want to go to" not in nc and "[[cambridge]]" in nc
    hints = {"E0#1": [dict(other="E0#3"), dict(other="E0#0")], "E0#0": []}
    h = P.render_v2(inp, export, docs, "v2_hints", hints)
    assert h.count("Possibly the same attribute as:") == 1
    assert "Possibly the same attribute as: E0#3, E0#0 (automatic suggestion, may be wrong)" in h
    assert "Possibly" not in P.render_v2(inp, export, docs, "v2", hints)
    assert "Possibly" not in P.render_v2(inp, export, docs, "v2_hints")


def test_v1_prompt_unchanged_by_v2_code(built):
    export, docs, inp, _ = built
    text = P.render(inp, export, docs, "nohints")
    assert text.startswith(P.INSTRUCTION) and "graduation_year" in text and "Possibly" not in text
    assert "Return the JSON array now." in text


def test_schema_enums(built):
    _, _, inp, _ = built
    ids = [c.cluster_id for c in inp.clusters]
    opts = [t for t, _ in inp.options]
    s1 = P.schema_v1(inp)["items"]["properties"]
    assert s1["cluster_id"]["enum"] == ids and s1["merge_with"]["items"]["enum"] == ids
    assert s1["placement"]["enum"] == opts
    s2 = P.schema_v2(inp)
    c = s2["properties"]["clusters"]["items"]
    assert c["properties"]["cluster_id"]["enum"] == ids and c["properties"]["placement"]["enum"] == opts
    assert set(c["required"]) == {"cluster_id", "attribute", "evidence", "mixed", "placement"}
    assert s2["required"] == ["attributes", "clusters"]
    sp = P.schema_split("E0#4", ["E0#4:s0", "E0#4:s1"])
    assert sp["properties"]["parts"]["items"]["properties"]["examples"]["items"]["enum"] == ["E0#4:s0", "E0#4:s1"]
    assert sp["properties"]["cluster_id"]["enum"] == ["E0#4"]


def test_split_candidates_and_prompt():
    export, docs = toy()
    assert P.split_candidates(export, "E0") == ["E0#4"]   # 2 values per instance; others have < 8 mentions
    assert P.split_candidates(export, "E0", min_mentions=6) == ["E0#4"]  # one value per instance elsewhere
    assert P.split_candidates(export, "E1") == []
    text, exs = P.render_split(export, docs, "E0", "E0#4", k=16, seed=0)
    ids = [e for e, _ in exs]
    assert len(ids) == len(set(ids)) == 12 and ids[0] == "E0#4:s0"
    assert all(f"- {e} " in text for e in ids)
    assert "mixes" in text and not any(s in text for s in SECRET)
    assert P.render_split(export, docs, "E0", "E0#4", k=5)[1] == exs[:0] + P.render_split(export, docs, "E0", "E0#4", k=5)[1]
    with pytest.raises(ValueError):
        P.render_split(export, docs, "E0", "E1#0")


def test_manifest_jobs(tmp_path, monkeypatch):
    import importlib.util
    import json
    export, docs = toy()
    export = MN.Export(**vars(export))  # hints.py uses dataclasses.replace
    spec = importlib.util.spec_from_file_location("pilot_build_v31", Path(__file__).resolve().parents[1] / "scripts" / "pilot_build_v31.py")
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    monkeypatch.setattr(B.paths, "ROOT", tmp_path)
    monkeypatch.setattr(B.MN, "load_shared", lambda run: (docs, None, []))
    monkeypatch.setattr(B.MN, "load", lambda d: export)
    monkeypatch.setattr(sys, "argv", ["x", "--ents", "train,hotel", "--out", "out", "--run", "run"])
    B.main()
    out = tmp_path / "out"
    jobs = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    names = [j["job"] for j in jobs]
    assert len(names) == len(set(names))
    assert {"train_nohints_r1", "train_nohints_long_r1", "train_v2_r1", "train_v2_r2", "train_v2_nocontext_r1",
            "hotel_nohints_r1", "hotel_v2_r2", "train_split_E0-4_r1"} <= set(names)
    assert "hotel_nohints_long_r1" not in names and "hotel_v2_hints_r1" not in names  # no window cache
    keys = {"job", "entity", "ent", "variant", "run_tag", "kind", "cluster_id", "prompt", "schema", "max_tokens", "format"}
    for j in jobs:
        assert set(j) == keys and (out / j["prompt"]).exists() and (out / j["schema"]).exists()
        assert 2000 <= j["max_tokens"] <= 12000 and j["format"] in ("v1", "v2", "split")
    sp = [j for j in jobs if j["kind"] == "split"][0]
    assert sp["max_tokens"] == 3000 and sp["cluster_id"] == "E0#4" and sp["format"] == "split"
    assert (out / "prompts" / "train_v2_r2.txt").read_text(encoding="utf-8") != (out / "prompts" / "train_v2.txt").read_text(encoding="utf-8")
    ex = pd.read_csv(out / "examples.csv")
    assert list(ex.columns) == ["ex_id", "entity", "cluster_id", "mention_id", "variant"]
    assert (out / "prompt_stats.md").exists()
    assert B.max_tokens(10000) == 12000 - 0 and B.max_tokens(27000) == 2000
