"""wf_v3.6 W1: parse repair, AE instruction, F2 delex map, F2 carry, J general words, builder helpers."""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pilot_build_v36 as B  # noqa: E402
import pilot_eval_v31 as EV  # noqa: E402
import score_v35 as S35  # noqa: E402
from s1a import delex as D  # noqa: E402
from s1a import llm_cache as lc  # noqa: E402
from s1a import pilot_combine as PC  # noqa: E402
from s1a import pilot_input as P  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402
from s1a import roles_v35 as R  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from test_pilot_combine_v33 import folder_carry  # noqa: E402
from test_pilot_input import toy  # noqa: E402

DECLARED = [f"restaurant_{n}" for n in ("name", "address", "phone", "price", "area", "food", "ref", "postcode")]
UNDECLARED = ["restaurant_people", "restaurant_duration", "restaurant_date", "restaurant_time"]


def a_r2_shape():
    """8 declared names; 13 clusters, 6 of them use 4 undeclared names (some twice), one is noise, one a cue."""
    used = DECLARED[:5] + [UNDECLARED[0], UNDECLARED[0], UNDECLARED[1], UNDECLARED[2], UNDECLARED[2], UNDECLARED[3],
                           "not_attribute", "attribute_cue"]
    clusters = [{"cluster_id": f"E2#{i}", "attribute": a, "evidence": "e", "mixed": False, "placement": "current entity E2"}
                for i, a in enumerate(used)]
    attrs = [{"name": n, "description": "d", "role": "r"} for n in DECLARED]
    return {"attributes": attrs, "clusters": clusters}, [c["cluster_id"] for c in clusters]


def test_repair_undeclared_a_r2_shape():
    obj, ids = a_r2_shape()
    errs = [e for e in lc.parse_response_v2(json.dumps(obj), ids)[1] if "attribute list" in e]
    assert len(errs) == 7   # 6 uses of undeclared names + attribute_cue, which the v2 parser does not know
    fixed, names = lc.repair_undeclared(obj)
    assert names == UNDECLARED                                   # first-seen order, once each
    left = [e for e in lc.parse_response_v2(json.dumps(fixed), ids)[1] if "attribute list" in e]
    assert left == ["clusters[12] attribute 'attribute_cue' not in the attribute list"]
    assert len(fixed["attributes"]) == 12 and len(obj["attributes"]) == 8   # a copy, not changed in place
    assert fixed["attributes"][-1] == {"name": "restaurant_time", "description": "", "role": "", "repaired": True}
    assert fixed["clusters"] == obj["clusters"]


def test_repair_undeclared_noop_and_spelling():
    obj = {"attributes": [{"name": "Departure_Station", "description": "d", "role": "r"}],
           "clusters": [{"attribute": "departure station"}, {"attribute": "not_attribute"}, {"attribute": 3}]}
    fixed, names = lc.repair_undeclared(obj)
    assert names == [] and fixed["attributes"] == obj["attributes"]
    assert lc.repair_undeclared([1]) == ([1], []) and lc.repair_undeclared({})[1] == []


def test_repaired_names_become_decisions():
    obj, ids = a_r2_shape()
    plain = PV.decisions_from_v2(obj, ids, "v2", "r2", require_mixed=False).set_index("cluster_id")
    fixed = PV.decisions_from_v2(lc.repair_undeclared(obj)[0], ids, "v2", "r2", require_mixed=False).set_index("cluster_id")
    assert plain.loc["E2#5", "action"] == "unsure" and fixed.loc["E2#5", "action"] == "merge"   # people, twice
    assert fixed.loc["E2#5", "name"] == "restaurant_people" and fixed.loc["E2#7", "action"] == "keep"


def test_decisions_repairs_flag(tmp_path):
    obj, ids = a_r2_shape()
    p = tmp_path / "r.jsonl"
    p.write_text(json.dumps({"parsed": obj, "errors": [], "finish_reason": "stop"}) + "\n", encoding="utf-8")
    job = {"job": "restaurant_v2_r2", "variant": "v2", "run_tag": "r2", "format": "v2", "ent": "restaurant"}
    assert EV._decisions(job, p, ids, {}).set_index("cluster_id").loc["E2#5", "action"] == "unsure"   # default: off
    rows = []
    assert EV._decisions(job, p, ids, {}, rows).set_index("cluster_id").loc["E2#5", "action"] == "merge"
    assert rows == [{"job": "restaurant_v2_r2", "repaired_names": UNDECLARED}]
    p.write_text(json.dumps({"parsed": lc.repair_undeclared(obj)[0], "errors": []}) + "\n", encoding="utf-8")
    again = []
    EV._decisions(job, p, ids, {}, again)
    assert again == []   # nothing left to repair: no row


def test_repairs_frame_and_invalid_file():
    df = S35.repairs_frame([{"variant": "A r2", "ent": "restaurant", "job": "j", "repaired_names": ["a", "b"]}])
    assert list(df.columns) == ["variant", "ent", "job", "repaired_names", "n_repaired"]
    assert df.iloc[0]["n_repaired"] == 2 and json.loads(df.iloc[0]["repaired_names"]) == ["a", "b"]
    assert S35.repairs_frame([]).empty
    root = Path(__file__).resolve().parents[1] / "config"
    assert RN.invalid_runs(root / "invalid_runs_v36.json") == []
    assert RN.invalid_runs(root / "invalid_runs.json")[0]["variant"] == "A r2"   # the default file is unchanged


# ---- AE
def test_ae_instruction_is_a_plus_noise_rule():
    export, docs = toy()
    inp = P.build_input(export, docs, "E0", k=8, seed=0)
    a = P.render_v2(inp, export, docs, "v2", order_seed=1)
    assert a == P.render_v2(inp, export, docs, "v2", order_seed=1, noise_rule=False)   # default unchanged
    ae = P.render_v2(inp, export, docs, "v2", order_seed=1, noise_rule=True)
    assert ae.replace(" " + P.NOISE_RULE_AE, "", 1) == a and len(ae) == len(a) + 1 + len(P.NOISE_RULE_AE)
    assert P.INSTRUCTION_V2_AE.replace(" " + P.NOISE_RULE_AE, "") == P.INSTRUCTION_V2
    assert P.CUE_LINE not in ae and ae.count(P.NOISE_RULE_AE) == 1 and "attribute_cue" not in P.NOISE_RULE_AE


# ---- F2
def make_db(tmp_path):
    z = tmp_path / "db.zip"
    rows = {"hotel": [{"name": "the acorn guest house"}, {"name": "hotel"}],
            "restaurant": [{"name": "Pizza Hut  City Centre"}, {"name": "ab"}],
            "attraction": [{"name": "Whale of a Time"}],
            "train": [{"departure": "cambridge", "destination": "London Kings Cross"},
                      {"departure": "travel time", "destination": "ely"}]}
    with zipfile.ZipFile(z, "w") as f:
        for k, v in rows.items():
            f.writestr(f"MULTIWOZ2.4/{k}_db.json", json.dumps(v))
    return z


def test_build_map_v2_names_only(tmp_path):
    names = D.db_names(make_db(tmp_path))
    assert "pizza hut city centre" in names and "london kings cross" in names and "travel time" in names
    mp = D.build_map_v2(names, ["Take TR1234 to Ely", "or tr9999"])
    for generic in ("hotel", "restaurant", "travel time", "cambridge", "the", "guest house", "centre"):
        assert generic not in mp
    for real in ("the acorn guest house", "acorn guest house", "pizza hut city centre", "whale of a time",
                 "london kings cross", "ely", "tr1234", "tr9999"):
        assert real in mp
    assert "ab" not in mp                                              # shorter than 3
    assert mp == D.build_map_v2(names[::-1], ["or tr9999", "Take TR1234 to Ely"])
    assert len(set(mp.values())) == len(mp) and not set(mp) & set(mp.values())
    out = D.apply("The hotel near Acorn Guest House, train TR1234, travel time 20 minutes", mp)
    assert "Acorn" not in out and "TR1234" not in out and "hotel" in out and "travel time" in out and "train" in out


def test_f2_plan_mirrors_f_carry():
    plan = B.f2_plan("train", 3)
    assert [p[0] for p in plan] == ["train_f2_nbhd0_s0", "train_f2_nbhd1_s0", "train_f2_nbhd2_s0"]
    assert [p[2] for p in plan] == [0, 1, 2] and plan[0][3] == [] and plan[2][3] == [plan[0][0], plan[1][0]]


def test_fill_carry_variant_f2_applies_delex(tmp_path):
    g1 = folder_carry(tmp_path, variant="f2")
    (tmp_path / "delex_map.json").write_text(json.dumps({"day": "zorp"}), encoding="utf-8")
    PC.fill_carry(tmp_path, 1)
    text = (tmp_path / g1["prompt"]).read_text(encoding="utf-8")
    assert "zorp" in text and "- day" not in text


# ---- J general words
def test_cue_sets_partition_cue_roles():
    for side in ("start", "end"):
        assert R.CUE_GENERAL[side] | R.CUE_DOMAIN[side] == P.CUE_ROLES[side] and not R.CUE_GENERAL[side] & R.CUE_DOMAIN[side]
    assert R.CUE_DOMAIN["start"] >= {"leave", "leaving", "depart"} and R.CUE_DOMAIN["end"] >= {"arrive", "arriving"}
    assert R.CUE_GENERAL == {"start": {"from", "after"}, "end": {"to", "into", "by", "before"}}


def test_j_side_word_sets():
    def row(turn, text):
        return {"turn_text": turn, "text": text, "left_word": ""}
    leave, to = row("I want to leave Cambridge now", "Cambridge"), row("go to London", "London")
    assert R.j_side(leave) == 0 and R.j_word(leave) == (0, "leave")
    assert R.j_word(leave, words=R.CUE_GENERAL) == (1, "to")   # without the domain word, the farther "to" decides
    assert R.j_side(row("depart Ely", "Ely"), words=R.CUE_GENERAL) is None and R.j_word(row("Ely", "Ely")) == (None, None)
    assert R.j_side(to, words=R.CUE_GENERAL) == 1 == R.j_side(to)


# ---- builder helpers
def test_family_rows_and_old_stats(tmp_path):
    rows, tot = B.family_rows([("a_s2", 10, 3.0), ("g", 5, 2), ("ae", 1, 1)])
    assert rows == ["| a_s2 | 1 | 10 | 3 |", "| ae | 1 | 1 | 1 |", "| g | 1 | 5 | 2 |", "| total | 3 | 16 | 6 |"]
    assert tot == [3, 16, 6]
    f = tmp_path / "s.md"
    f.write_text("| job1 | E1 | 8 | 100 | 40 | 7 | ok |\n| other | E1 | 8 | 1 | 2 | 3 | ok |\n| a | b |\n", encoding="utf-8")
    assert B.old_stats(f, {"job1"}) == {"job1": (40, 7)}


def test_v31_check_and_earlier_output(tmp_path):
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "t.txt").write_bytes(b"a\r\nb\r\n")
    assert B.v31_check("a\nb\n", tmp_path, "t.txt") == "identical" and B.v31_check("a\n", tmp_path, "t.txt") == "DIFFERENT"
    assert B.v31_check("a", tmp_path, "no.txt") == "missing"
    r = tmp_path / "r.jsonl"
    r.write_text(json.dumps({"raw": "x" * 70}) + "\n" + json.dumps({"output_tokens": 9, "raw": "y"}) + "\n", encoding="utf-8")
    assert B.earlier_output(r) == 9 and B.earlier_output(tmp_path / "none.jsonl") == 0
    r.write_text(json.dumps({"raw": "x" * 70}) + "\n", encoding="utf-8")
    assert B.earlier_output(r) == 20


def test_v36_notebook_compiles():
    nb = json.loads((Path(__file__).resolve().parents[1] / "colab" / "S1A_llm_v36_colab.ipynb").read_text(encoding="utf-8"))
    code = "\n".join("\n".join(ln for ln in "".join(c["source"]).split("\n") if not ln.lstrip().startswith(("%", "!")))
                     for c in nb["cells"] if c["cell_type"] == "code")
    compile(code, "v36", "exec")
    assert "loop1_v36/colab" in code and "wf-v3.6" in code and "fill_carry" in code and "loop1_v35" not in code
