import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import score_t14_v37 as S  # noqa: E402
from s1a import exit_v37 as EX  # noqa: E402
from s1a import stability_v37 as ST  # noqa: E402
from s1a import t14_v37 as T  # noqa: E402
from test_w1_v37 import toy, variant, with_variants  # noqa: E402

ENTS = ("train", "hotel", "restaurant")


def frames(label, found, role, agree=None, noise=(9, 13)):
    """score / noise / dup / ceiling toy inputs of one label; found = (train, hotel, restaurant)."""
    sc = pd.DataFrame({"ent": ENTS, "variant": label, "found_n": found, "gold_n": [10, 14, 16], "role_right": [role, 0, 0],
                       "role_base": [8, 0, 0], "name_right": [5, 5, 5], "name_base": [10, 14, 16], "names_unrated": [0, 1, 0]})
    nz = pd.DataFrame({"variant": label, "ent": ENTS, "noise_n": [4, 6, 3], "noise_marked": [3, 4, noise[0] - 7],
                       "marked_n": [4, 5, 3], "marked_noise": [3, 4, 2], "marked_real": [0, 1, 0], "marked_mixed": 0})
    dup = pd.DataFrame({"variant": label, "ent": "train", "attr": ["a", "b"], "n_columns": [1, 2], "n_groups": [1, 2], "columns": "x"})
    ceil = pd.DataFrame({"recoverable": [True, True, False], "present": True})
    return sc, nz, dup, ceil


def rows_for(set_name, version, orders, found_by_order, vote_found, vote_role, agree):
    out = []
    for lab, f in zip(orders, found_by_order):
        sc, nz, dup, ceil = frames(lab, f, 3)
        out.append(T.run_rows(set_name, version, [lab], "none", sc, nz, {lab: 60}, dup, ceil))
    sc, nz, dup, ceil = frames("A s012", vote_found, vote_role)
    out.append(T.run_rows(set_name, version, [], "A s012", sc, nz, {"A s012": 61}, dup, ceil, {"agree_groups": agree}))
    return pd.concat(out, ignore_index=True)


def test_run_rows_and_decision_keep():
    old = rows_for("dev50", "v2.2", ("A r1", "A r2", "A s2"), [(8, 12, 11), (7, 12, 11), (8, 12, 11)], (8, 12, 11), 3, 0.6)
    new = rows_for("dev50", "v2.3", ("A s0", "A s1", "A s2"), [(8, 12, 11), (7, 13, 11), (8, 12, 12)], (8, 12, 11), 4, 0.5)
    r = old[old["variant"] == "A s012"].iloc[0]
    assert r["found_n"] == 31 and r["columns"] == 61 and r["dup_mean"] == 1.5 and r["dup_attrs"] == 1 and r["noise_n"] == 13
    assert r["role_right"] == 3 and r["role_base"] == 8 and r["recoverable"] == 2 and r["agree_groups"] == 0.6
    other = rows_for("dev50b", "v2.2", ("A r1", "A r2", "A s2"), [(8, 12, 11)] * 3, (8, 12, 11), 3, 0.6)
    other3 = rows_for("dev50b", "v2.3", ("A s0", "A s1", "A s2"), [(8, 12, 11)] * 3, (8, 12, 11), 3, 0.7)
    keep, lines, text = T.decide(pd.concat([old, new, other, other3], ignore_index=True))
    assert keep is True and "KEEP v2.3" in text and len(lines) == 2   # dev50: role better; dev50b: agreement better
    md = T.t14_md(pd.concat([old, new], ignore_index=True), (keep, lines, text), {("dev50", "v2.2"): frames("x", (1, 1, 1), 1)[3].assign(ent="train")})
    assert "A, 3 orders (range)" in md and "31-32/40" in md and "7-8" in md and "Ceiling per run" in md


def test_decision_fails_and_undecided():
    old = rows_for("dev50", "v2.2", ("A r1", "A r2", "A s2"), [(8, 12, 11), (7, 12, 11), (8, 12, 11)], (8, 12, 11), 3, 0.6)
    worse = rows_for("dev50", "v2.3", ("A s0", "A s1", "A s2"), [(8, 12, 11), (6, 12, 11), (8, 12, 11)], (8, 12, 11), 5, 0.9)
    keep, lines, text = T.decide(pd.concat([old, worse], ignore_index=True))
    assert keep is False and "DROP v2.3" in text and "below v2.2: train" in lines[0]    # worst train order 6 < 7
    same = rows_for("dev50", "v2.3", ("A s0", "A s1", "A s2"), [(8, 12, 11), (7, 12, 11), (8, 12, 11)], (8, 12, 11), 3, 0.6)
    assert T.decide(pd.concat([old, same], ignore_index=True))[0] is False   # nothing improves
    none = T.decide(old)
    assert none[0] is None and "missing" in none[1][0]
    assert T.decide(pd.DataFrame(columns=T.ROW_COLS))[0] is None


def test_exit_e_and_md():
    assert EX.exit_e(30, 25) is True and EX.exit_e(25, 25) is False and EX.exit_e(None, 25) is None
    runs = {"A s012": {"found": 31, "recoverable": 29, "found_recoverable": 27, "found_not_recoverable": 4, "noise_n": 13,
                       "noise_marked": 10, "marked_n": 13, "marked_noise": 10, "columns_per_found": 1.1}}
    t = EX.bar_rows(runs, {"A s012 (vote)": ["A s012"]})
    assert "pending the baseline" in EX.exit_md(t, runs)
    assert "pass: A right 30" in EX.exit_md(t, runs, e={"A s012 (vote)": "pass: A right 30"})


def test_seed_labels_and_baseline_right(tmp_path):
    ed = toy({"c1": ["Train price"] * 4})
    v = variant(ed, {"c1": "g"})
    ed = with_variants(ed, A_r1=v, A_r2=v, A_s2=v)
    assert list(ST.with_seed_labels(ed, ("A r1", "A r2", "A s2")).seed_decs) == ["C s0", "C s1", "C s2"]
    assert S.baseline_right(tmp_path, "dev50") is None
    pd.DataFrame({"set": ["dev50", "dev50", "dev50b"], "ent": ["train", "hotel", "train"], "version": ["union"] * 3,
                  "right": [4, 5, 7]}).to_csv(tmp_path / "baseline_v37.csv", index=False)
    assert S.baseline_right(tmp_path, "dev50") == 9 and S.baseline_right(tmp_path, "dev50b") == 7
    assert S.baseline_right(tmp_path, "nope") is None


def test_missing_jobs_with_fake_responses(tmp_path):
    jobs = [{"job": f"{e}_a_r_s{k}", "ent": e, "family": "a", "run": "r"} for e in ("train", "hotel", "restaurant") for k in range(3)]
    jobs += [{"job": "train_split_r_0", "ent": "train", "family": "split", "run": "r"}]
    (tmp_path / "manifest.json").write_text(json.dumps({"run": "x", "runs": {}, "jobs": jobs}), encoding="utf-8")
    (tmp_path / "responses").mkdir()
    assert len(S.missing_jobs(tmp_path, "r")) == 10
    for j in jobs[:4]:
        (tmp_path / "responses" / f"{j['job']}.jsonl").write_text("{}\n", encoding="utf-8")
    assert set(S.missing_jobs(tmp_path, "r")) == {j["job"] for j in jobs[4:]}
    assert S.missing_jobs(tmp_path, "other") == []


def test_check_ids_and_only():
    ed = toy({"c1": ["Train price"] * 2})
    gt = pd.DataFrame({"mention_id": ["0"]})
    assert "1 mentions" in S.check_ids({"train": ed}, gt)[0] and S.check_ids({"train": ed}, pd.DataFrame({"mention_id": ["0", "1"]})) == []
    ed = with_variants(ed, A_r1=variant(ed, {"c1": "g"}), B_s0=variant(ed, {"c1": "g"}))
    assert set(S.only({"train": ed}, ("A r1",))["train"].variants) == {"A r1"}
