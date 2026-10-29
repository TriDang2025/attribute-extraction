import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_input as P  # noqa: E402
from test_pilot_input import SECRET, toy  # noqa: E402


def synth_export(sizes=(30, 15), dim=8, seed=0):
    """One entity E1 with sum(sizes) clusters of 2 mentions each; blob b has sizes[b] clusters."""
    rng = np.random.default_rng(seed)
    rows, vecs, n = [], [], 0
    for b, size in enumerate(sizes):
        base = np.zeros(dim)
        base[b] = 1.0
        for _ in range(size):
            for _ in range(2):
                rows.append(dict(mention_id=len(rows), cluster_id=f"E1#{n}", entity="E1", norm_value=f"v{n}"))
                vecs.append(base + 0.15 * rng.normal(size=dim))
            n += 1
    m = pd.DataFrame(rows)
    x = np.array(vecs, dtype=np.float32)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    return SimpleNamespace(mentions=m, ids=m["mention_id"].to_numpy(), x=x, clusters=MN.cluster_table(m))


def num(c):
    return int(c.rsplit("#", 1)[1])


def test_neighbourhoods_cover_once_and_cap():
    export = synth_export((30, 15))     # 45 clusters -> 3 groups; the 30-blob must be split and rebalanced
    groups = P.neighbourhoods(export, "E1")
    flat = [c for g in groups for c in g]
    assert len(groups) == 3 and sorted(flat, key=num) == [f"E1#{i}" for i in range(45)] and len(set(flat)) == 45
    assert all(1 <= len(g) <= 20 for g in groups)
    assert all(g == sorted(g, key=num) for g in groups)
    assert [g[0] for g in groups] == sorted((g[0] for g in groups), key=num)
    assert groups == P.neighbourhoods(export, "E1")


def test_neighbourhoods_rebalance_moves_to_room():
    export = synth_export((38, 2))      # 40 clusters, 2 groups, one blob of 38: rebalance to 20 + 20
    groups = P.neighbourhoods(export, "E1")
    assert sorted(len(g) for g in groups) == [20, 20]
    assert sorted(c for g in groups for c in g) == sorted(f"E1#{i}" for i in range(40))


def test_neighbourhoods_small_entity_one_group():
    export = synth_export((5,))
    assert P.neighbourhoods(export, "E1") == [[f"E1#{i}" for i in range(5)]]
    assert P.neighbourhoods(export, "E9") == []


def test_outside_context_other_groups_only():
    export = synth_export((6, 6))
    groups = [[f"E1#{i}" for i in range(6)], [f"E1#{i}" for i in range(6, 12)]]
    out = P.outside_context(export, groups, 0)
    assert len(out) == 3 and all(c in groups[1] for c, _ in out)
    assert out[0][1] == [f"v{num(out[0][0])}"]
    assert P.outside_context(export, [groups[0]], 0) == []


def test_nbhd_target():
    assert [P.nbhd_target(n) for n in (1, 2, 20, 19, 29)] == [1, 1, 7, 6, 10]


@pytest.fixture(scope="module")
def built():
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    return export, docs, inp


def test_render_v3_group_only_target_reason_outside(built):
    export, docs, inp = built
    grp = ["E0#4", "E0#0", "E0#1", "E0#3"]
    text = P.render_v3(inp, export, docs, grp, [("E1#0", ["monday", "night"])], 2)
    assert text.startswith(P.INSTRUCTION_V2) and P.REASON_LINE in text
    assert "Aim for about 2 attributes (between 1 and 3)." in text
    assert "Elsewhere in this entity (not yours to assign): E1#0: monday, night" in text
    assert all(f"### {c} " in text for c in grp) and "### E0#2 " not in text
    assert text.index("### E0#4 ") < text.index("### E0#0 ")      # given order kept
    assert not any(s in text for s in SECRET) and "Return the JSON object now." in text
    assert "Elsewhere" not in P.render_v3(inp, export, docs, grp, [], 2)


def test_render_v3_order_seed_reproducible(built):
    export, docs, inp = built
    grp = [c.cluster_id for c in inp.clusters]
    r = lambda s: P.render_v3(inp, export, docs, grp, [], 2, s)  # noqa: E731
    assert r(1) == r(1) and r(2) == r(2) and r(1) != r(None) and r(1) != r(2)
    order = lambda t: sorted(grp, key=lambda c: t.index(f"### {c} "))  # noqa: E731
    assert order(r(None)) == grp and sorted(order(r(1))) == sorted(grp)


def test_schema_v3_order_enum_and_required(built):
    _, _, inp = built
    grp = ["E0#1", "E0#0"]
    s = P.schema_v3(inp, grp)
    c = s["properties"]["clusters"]["items"]
    assert list(c["properties"]) == ["cluster_id", "reason", "attribute", "evidence", "mixed", "placement"]
    assert c["properties"]["cluster_id"]["enum"] == grp and c["required"] == list(c["properties"])
    assert c["properties"]["placement"]["enum"] == [t for t, _ in inp.options]
    assert s["required"] == ["attributes", "clusters"]
    v2 = P.schema_v2(inp)["properties"]["clusters"]["items"]    # v2 unchanged: no reason
    assert list(v2["properties"]) == ["cluster_id", "attribute", "evidence", "mixed", "placement"]


def test_noise_and_gate_prompts_and_schemas(built):
    export, docs, _ = built
    t, exs = P.render_noise(export, docs, "E0", "E0#4")
    assert len(exs) == 6 and exs[0][0] == "E0#4:n0" and "If unsure, answer unsure." in t
    assert "### E0#4 " in t and "- E0#4:n0 " in t and "- E0#4:n6 " not in t
    t, exs = P.render_gate(export, docs, "E0", "E0#4")
    assert len(exs) == 12 and exs[0][0] == "E0#4:g0" and "If unsure, answer coherent true." in t
    assert "summarise" in t and not any(s in t for s in SECRET)
    n = P.schema_noise("E0#4")
    assert n["properties"]["verdict"]["enum"] == ["attribute", "noise", "unsure"]
    assert n["properties"]["cluster_id"]["enum"] == ["E0#4"] and "name" in n["required"]
    g = P.schema_gate("E0#4")
    assert g["properties"]["coherent"] == {"type": "boolean"} and g["required"] == ["cluster_id", "summary", "coherent"]
    with pytest.raises(ValueError):
        P.render_noise(export, docs, "E0", "E1#0")


def test_split_prompt_text_unchanged_by_refactor(built):
    export, docs, _ = built
    text, exs = P.render_split(export, docs, "E0", "E0#4", k=16, seed=0)
    assert text.startswith(P.INSTRUCTION_SPLIT + "\n\nCluster E0#4 of entity E0 (mentions 12, distinct values 12).\nExamples:\n- E0#4:s0 ")
    assert text.endswith("\n\nReturn the JSON object now.\n") and len(exs) == 12


def test_reconcile_prompt_and_schema():
    unit = {"unit_id": "a3", "name": "leave_time", "description": "earliest departure",
            "lines": ["- E0#1:n0 [user] turn: leave at [[10:00]]"]}
    t = P.render_reconcile(unit, [("arrive_by_time", "latest arrival"), ("day", "day of travel")])
    assert "Attribute a3: leave_time: earliest departure" in t and "- E0#1:n0 [user]" in t
    assert "- arrive_by_time: latest arrival\n- day: day of travel" in t and "If unsure, answer none." in t
    s = P.schema_reconcile("a3", ["arrive_by_time", "day"])
    assert s["properties"]["same_as"]["enum"] == ["arrive_by_time", "day", "none"]
    assert s["properties"]["unit_id"]["enum"] == ["a3"] and s["required"] == ["unit_id", "reason", "same_as"]
    assert P.schema_reconcile("a0", [])["properties"]["same_as"]["enum"] == ["none"]


def test_build_v32_files(tmp_path, monkeypatch):
    export, docs = toy()
    spec = importlib.util.spec_from_file_location(
        "pilot_build_v32", Path(__file__).resolve().parents[1] / "scripts" / "pilot_build_v32.py")
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
    assert {"train_nbhd0_s0", "train_nbhd0_s1", "train_nbhd0_s2", "train_noise_E0-4", "train_gate_E0-4",
            "train_split_E0-4", "hotel_nbhd0_s2", "hotel_noise_E1-1"} <= set(names)
    assert not any("reconcile" in n for n in names)
    keys = {"job", "entity", "ent", "variant", "run_tag", "kind", "stage", "nbhd", "cluster_id", "prompt", "schema",
            "max_tokens", "format"}
    for j in jobs:
        assert set(j) == keys and j["stage"] == 1 and (out / j["prompt"]).exists() and (out / j["schema"]).exists()
        assert j["variant"] == j["kind"] or (j["variant"], j["kind"]) == ("nbhd", "entity")
        assert 1000 <= j["max_tokens"] <= 12000 and j["format"] in ("v3", "noise", "gate", "split")
    assert [j["nbhd"] for j in jobs if j["job"].startswith("train_nbhd")] == [0, 0, 0]
    assert (out / "prompts" / "train_nbhd0_s1.txt").read_text(encoding="utf-8") != (
        out / "prompts" / "train_nbhd0_s0.txt").read_text(encoding="utf-8")
    nb = pd.read_csv(out / "neighbourhoods.csv")
    assert list(nb.columns) == ["ent", "entity", "nbhd", "cluster_id"] and len(nb[nb.ent == "train"]) == 5
    ex = pd.read_csv(out / "examples.csv")
    assert list(ex.columns) == ["ex_id", "entity", "cluster_id", "mention_id", "variant"]
    s2 = json.loads((out / "stage2_inputs.json").read_text(encoding="utf-8"))
    tr = s2["train"]
    assert tr["entity"] == "E0" and set(tr["clusters"]) == {f"E0#{i}" for i in range(5)}
    c = tr["clusters"]["E0#4"]
    assert c["head"].startswith("### E0#4 ") and len(c["lines"]) == 6 and c["lines"][0].startswith("- E0#4:n0 ")
    assert list(tr["split_examples"]) == ["E0#4"] and len(tr["split_examples"]["E0#4"]) == 12
    assert tr["options"][0] == "current entity E0" and tr["nbhd"]["E0#4"] == 0
    z = np.load(out / "stage2_vectors.npz")
    assert z["cluster_ids"].shape == (7,) and z["cluster_x"].shape == (7, 3) and z["cluster_x"].dtype == np.float32
    assert z["ex_ids"].shape == (12,) and z["ex_x"].shape == (12, 3)
    gen = json.loads((out / "generic.json").read_text(encoding="utf-8"))
    assert set(gen) == {"train", "hotel"} and all(c.startswith("E0#") for c in gen["train"])
    stats = (out / "prompt_stats.md").read_text(encoding="utf-8")
    assert "| train | B |" in stats and "| train | D |" in stats
