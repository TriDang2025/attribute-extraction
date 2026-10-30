import sys
import zlib
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pilot_build_v33 as B  # noqa: E402
from s1a import pilot_input as P  # noqa: E402
from test_pilot_input import toy  # noqa: E402


def test_old_instructions_unchanged():
    assert zlib.crc32(P.INSTRUCTION_V2.encode()) == 905036422
    assert zlib.crc32(P.INSTRUCTION_V3.encode()) == 686104669


def test_render_v3_default_is_v32():
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    grp = ["E0#0", "E0#1"]
    text = P.render_v3(inp, export, docs, grp, [("E1#0", ["monday"])], 2)
    assert text.startswith(P.INSTRUCTION_V3 + "\n\nEntity E0: 2 clusters.")
    assert "attribute_cue" not in text and P.CARRY_PLACEHOLDER not in text
    assert text == P.render_v3(inp, export, docs, grp, [("E1#0", ["monday"])], 2, None, None, False)


def test_cue_rule_text_and_example():
    assert P.INSTRUCTION_V33.startswith(P.INSTRUCTION_V3[:200])
    for part in (P.CUE_LINE, P.NOISE_RULE):
        assert part in P.INSTRUCTION_V33 and part not in P.INSTRUCTION_V3
    s = P.INSTRUCTION_V33
    assert s.index('Use "not_attribute" for noise.') < s.index(P.CUE_LINE) < s.index("Noise is common") \
        < s.index(P.NOISE_RULE) < s.index("If a cluster holds two")
    assert '"attribute": "attribute_cue"' in s
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    text = P.render_v3(inp, export, docs, ["E0#0"], [], 1, cue_rule=True)
    assert text.startswith(P.INSTRUCTION_V33)


def test_carry_placeholder_between_outside_and_clusters():
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    out = [("E1#0", ["monday"])]
    text = P.render_v3(inp, export, docs, ["E0#0"], out, 1, carry=P.CARRY_PLACEHOLDER)
    paras = text.split("\n\n")
    i = paras.index("{{CARRY_OVER}}")
    assert paras[i - 1].startswith("Elsewhere") and paras[i + 1].startswith("### E0#0")
    assert text.count("{{CARRY_OVER}}") == 1
    assert "{{CARRY_OVER}}" not in P.render_v3(inp, export, docs, ["E0#0"], out, 1)


def _cluster(words, values):
    return pd.DataFrame(dict(cluster_id="E0#0", norm_value=values, dialogue_id=[f"d{i}" for i in range(len(values))],
                             mention_id=range(len(values)))), dict(enumerate(words))


def test_roles_pick_one_start_one_end():
    # most frequent value overall is "x" (left word "the"); start values: a (x1), b (x2); end: c (x1), d (x3)
    values = ["x"] * 6 + ["a", "b", "b", "c", "d", "d", "d"]
    words = ["the"] * 6 + ["from", "from", "from", "to", "to", "to", "to"]
    g, roles = _cluster(words, values)
    picked = P.select_examples(g, 4, 0, roles)
    vals = [values[m] for m in picked]
    assert vals[0] == "b" and vals[1] == "d"
    assert len(set(picked)) == len(picked) == 4
    assert P.select_examples(g, 4, 0, roles) == picked


def test_roles_none_or_one_sided_unchanged():
    values = ["x"] * 6 + ["a", "b", "b", "c", "d", "d", "d"]
    words = ["the"] * 6 + ["from", "from", "from", "to", "to", "to", "to"]
    g, roles = _cluster(words, values)
    base = P.select_examples(g, 6, 0)
    assert P.select_examples(g, 6, 0, None) == base and P.select_examples(g, 6, 0, {}) == base
    only_start = {m: ("from" if w == "to" else w) for m, w in roles.items()}
    assert P.select_examples(g, 6, 0, only_start) == base


def test_job_plan_fields():
    plan = B.job_plan("train", 3)
    by = {p[0]: p for p in plan}
    assert len(plan) == 9 + 6 + 9 + 3
    assert by["train_e_nbhd0_s1"][4:] == (0, [])
    assert by["train_e_nbhd2_s1"][4:] == (2, ["train_e_nbhd0_s1", "train_e_nbhd1_s1"])
    assert "train_e1_nbhd0_s0" not in by and by["train_e1_nbhd2_s0"][4:] == (0, [])
    assert by["train_e2_nbhd1_s2"][4:] == (1, ["train_e2_nbhd0_s2"])
    assert not any(p[1] == "f" and p[3] != 0 for p in plan)
    assert by["train_f_nbhd2_s0"][4:] == (2, ["train_f_nbhd0_s0", "train_f_nbhd1_s0"])
    assert [p for p in B.job_plan("hotel", 1) if p[4]] == []
