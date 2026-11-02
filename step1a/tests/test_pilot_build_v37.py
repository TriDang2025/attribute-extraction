import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pilot_build_v37 as B  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402


def test_names_carry_the_run():
    assert B.a_name("train", "v23d50", 2) == "train_a_v23d50_s2"
    assert B.split_name("hotel", "v22d50b", "E1#12") == "hotel_v22d50b_split_E1-12"


def test_split_job_file_is_read_by_the_v31_loader(tmp_path):
    p = tmp_path / f"{B.split_name('train', 'v23d50', 'E1#3')}_r1.jsonl"
    p.write_text(json.dumps({"parsed": {"is_mixed": False, "parts": []}}) + "\n", encoding="utf-8")
    assert list(PV.load_split_results(tmp_path)) == [("train_v23d50", "r1")]
    assert list(PV.load_split_results(tmp_path)[("train_v23d50", "r1")]) == ["E1#3"]


def test_merge_manifest_keeps_other_families_and_replaces_ours():
    old = {"run": "x", "jobs": [{"job": "b0", "family": "baseline"}, {"job": "a_old", "family": "a"},
                                {"job": "s_old", "family": "split"}, {"job": "b1", "family": "baseline"}]}
    m = B.merge_manifest(old, [{"job": "a_new", "family": "a"}], {"r": "dir"})
    assert [j["job"] for j in m["jobs"]] == ["b0", "b1", "a_new"] and m["run"] == "x" and m["runs"] == {"r": "dir"}
    assert B.merge_manifest(None, [{"job": "n", "family": "a"}], {})["jobs"] == [{"job": "n", "family": "a"}]
    assert B.merge_manifest([{"job": "b", "family": "baseline"}], [], {})["jobs"] == [{"job": "b", "family": "baseline"}]


def test_family_rows_totals():
    rows, tot = B.family_rows([("a", 100, 10), ("a", 50, 5), ("split", 20, 2), ("baseline", 1, 1)])
    assert tot == [4, 171, 18] and rows[0] == "| a | 2 | 150 | 15 |" and rows[-1] == "| total | 4 | 171 | 18 |"


def test_notebook_points_at_v37():
    nb = json.loads((Path(__file__).resolve().parents[1] / "colab" / "S1A_llm_v37_colab.ipynb").read_text(encoding="utf-8"))
    text = "\n".join("".join(c["source"]) for c in nb["cells"])
    assert 'BRANCH = "wf-v3.7"' in text and 'results/loop1_v37/colab' in text and "loop1_v36" not in text
    assert 'FAMILY_ORDER = ["a", "split", "baseline"]' in text
    assert 'sync.sh push-results "v3.7 batch responses" loop1_v37/colab' in text
