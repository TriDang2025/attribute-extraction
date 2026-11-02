import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import run_data_v37 as RD  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

CIDS = ["E1#0", "E1#1"]


def job(name, family, run, tag, **kw):
    return {"job": name, "ent": "train", "entity": "E1", "variant": "v2", "run_tag": tag, "kind": "entity",
            "format": "v2", "family": family, "run": run, **kw}


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"parsed": obj}) + "\n", encoding="utf-8")


def answer(name0, name1):
    return {"attributes": [{"name": name0, "description": "d"}, {"name": name1, "description": "d"}],
            "clusters": [{"cluster_id": "E1#0", "attribute": name0, "reason": "r"},
                         {"cluster_id": "E1#1", "attribute": name1, "reason": "r"}]}


def setup(tmp_path, orders=(0, 1, 2)):
    d = tmp_path / "colab"
    jobs = [job(f"train_a_r1_s{s}", "a", "r1", f"s{s}") for s in range(3)]
    jobs += [job(f"train_a_r2_s{s}", "a", "r2", f"s{s}") for s in range(3)]
    jobs.append(job("train_r1_split_E1-0_r1", "split", "r1", "r1", kind="split", cluster_id="E1#0", format="split"))
    jobs.append({"job": "baseline_train_dev50_v0", "ent": "train", "family": "baseline", "format": "baseline"})
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(json.dumps({"runs": {}, "jobs": jobs}), encoding="utf-8")
    pd.DataFrame([("e0", "E1", "E1#0", "5", "train_a_r1_s0"), ("e0", "E1", "E1#0", "5", "train_a_r1_s1"),
                  ("x0", "E1", "E1#0", "6", "train_a_r2_s0")],
                 columns=["ex_id", "entity", "cluster_id", "mention_id", "variant"]).to_csv(d / "examples.csv", index=False)
    for s in orders:
        write(d / "responses" / f"train_a_r1_s{s}.jsonl", answer("Train id" if s < 2 else "Other", "Train day"))
    write(d / "responses" / "train_a_r2_s0.jsonl", answer("A", "B"))
    return d


def entity_data():
    ctx = SimpleNamespace(examples=None)
    return {"train": VD.EntityData("train", "E1", ["train"], CIDS, None, None, ctx, ctx, {}, {}, {})}


def test_batch_jobs_by_run(tmp_path):
    d = setup(tmp_path)
    a, sp = RD.batch_jobs(d, "r1", "train")
    assert [j["job"] for j in a] == [f"train_a_r1_s{s}" for s in range(3)] and len(sp) == 1
    assert RD.batch_jobs(d, "r2", "train")[1] == []
    ex = RD.batch_examples(d, a, CIDS)
    assert list(ex["ex_id"]) == ["e0"]          # only this run's jobs, one row per ex_id


def test_load_a_variants_and_vote(tmp_path, monkeypatch):
    d, seen = setup(tmp_path), {}
    monkeypatch.setattr(RD.V36, "_add", lambda variants, label, dec, e, ctx, entity: seen.update({label: (dec, ctx)}))
    out, notes = RD.load_a(SimpleNamespace(e=None), entity_data(), d, "r1", repairs=[])
    assert sorted(seen) == ["A s0", "A s012", "A s1", "A s2"] and notes == []
    dec = seen["A s012"][0].set_index("cluster_id")
    assert dec.loc["E1#0", "name"] == "Train id" and dec.loc["E1#1", "name"] == "Train day"   # 2 of 3 orders
    assert list(seen["A s0"][1].examples["ex_id"]) == ["e0"] and out["train"].ctx_a is seen["A s0"][1]


def test_load_a_missing_order_skips_vote(tmp_path, monkeypatch):
    d, seen = setup(tmp_path, orders=(0, 1)), {}
    monkeypatch.setattr(RD.V36, "_add", lambda variants, label, dec, e, ctx, entity: seen.update({label: dec}))
    _, notes = RD.load_a(SimpleNamespace(e=None), entity_data(), d, "r1")
    assert sorted(seen) == ["A s0", "A s1"] and any("s2" in n for n in notes) and any("s012" in n for n in notes)
