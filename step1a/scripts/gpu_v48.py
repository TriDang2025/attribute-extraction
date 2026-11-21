"""wf_v4.8 W3 (diary Nov 19) GPU job, called by the notebook colab/S1A_wf48_colab.ipynb (one session, model loaded once).

w3: Step 4 v4.3 (all v4.4 switches off) on the final loop 1 + 2 attributes after W2, dev50 and dev50b, seeds 0-2, two variants:
    A = pass 2 in batches of 20 (p2_batch 20); B = A + neutral table ids in pass 2 (s1a/step4_neutral_v48.py). 12 chains.
    -> results/wf_v48/w3/<set>/step4_<A|B>/   (s1a/step4_v44.run layout: final/<chain>/canonical.json, final/status.json, responses/, ...)
Input: results/wf_v48/w3/<set>/input/a_llama44/<run>/a.columns.json = results/wf_v48/w2/<set>/a2.columns.json plus `mention_ids` per column
(loop-1 columns: the v4.7 run-1 final_columns.json; loop-2 columns: [] because their mention ids are not ids of the Step 1a-2 mention table,
so the score map gives them no GT label). Built by `prepare` on the laptop and committed; the notebook only checks it is there.
Scoring is on the laptop afterwards (scripts/step4_score_v48.py). Laptop check of the driver: python scripts/gpu_v48.py --fake (no GPU).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import gpu_v46 as G46  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import step4_v44 as S4  # noqa: E402

OUT = ROOT / "results" / "wf_v48" / "w3"
W2 = ROOT / "results" / "wf_v48" / "w2"
LOOP1 = ROOT / "results" / "wf_v47" / "z4" / "run1"
Y3 = ROOT / "results" / "wf_v46" / "y3"           # entities.json and a_prompts/ of the loop-1 run (PL.use_corpus)
SETS = G46.SETS
SEEDS = (0, 1, 2)
P2_BATCH = 20
VARIANTS = {"A": dict(p2_batch=P2_BATCH, neutral_ids=False), "B": dict(p2_batch=P2_BATCH, neutral_ids=True)}


def input_dir(dev, root=OUT):
    return Path(root) / dev / "input" / "a_llama44"


def prepare(dev, run, root=OUT):
    """Write the W3 input of one set (see the module doc). Returns its path."""
    cols = B.read_json(W2 / dev / "a2.columns.json")
    final = B.read_json(LOOP1 / dev / "step3" / "scores" / "final_columns.json")[run]
    ids = {f"{e}:{c['cid']}": c["mention_ids"] for e, cs in final.items() for c in cs}
    p = input_dir(dev, root) / run / "a.columns.json"
    B.write_json(p, [{**c, "mention_ids": ids.get(c["id"], [])} for c in cols])
    return p


def config(variant):
    return S4.with_switches(S4.load_config(), off=S4.SWITCHES, **VARIANTS[variant])


def w3(backend, variants=tuple(VARIANTS), sets=SETS, seeds=SEEDS, root=OUT, log=print):
    """Step 4 of every variant on each set. Returns {(variant, dev): final/status.json rows}."""
    res = {}
    for v in variants:
        for dev, run in sets.items():
            if not (input_dir(dev, root) / run / "a.columns.json").exists():
                raise FileNotFoundError(f"no W3 input for {dev}: run scripts/gpu_v48.py --prepare on the laptop")
            out = Path(root) / dev / f"step4_{v}"
            with PL.use_corpus(run, B.read_json(Y3 / dev / "entities.json"), Y3 / dev / "a_prompts"):
                S4.run(out, backend, inputs=("a_llama44",), sets=(run,), seeds=seeds, cfg=config(v), step3_dirs={"a_llama44": input_dir(dev, root)})
            res[(v, dev)] = B.read_json(out / "final" / "status.json")
            log(f"w3 {v} {dev}: {[(r['run'], r['ok'], r['tables']) for r in res[(v, dev)]]}")
    return res


def fake_check(root):
    """prepare + w3 with the laptop fake Step 4 model into `root`; raises on any failure."""
    for dev, run in SETS.items():
        prepare(dev, run, root)
    res = w3(G46.Fakes(), root=root, log=lambda *_: None)
    assert all(len(rows) == len(SEEDS) and all(r["ok"] for r in rows) for rows in res.values()), res
    return {k: [r["tables"] for r in rows] for k, rows in res.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true", help="write the W3 inputs (laptop, before the GPU session)")
    ap.add_argument("--fake", action="store_true", help="laptop check with fakes (no GPU)")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v48" / "fake_check")
    a = ap.parse_args()
    if a.prepare:
        for dev, run in SETS.items():
            print("wrote", prepare(dev, run))
    elif a.fake:
        print(fake_check(a.out))
    else:
        ap.error("the real run is the notebook colab/S1A_wf48_colab.ipynb; give --prepare or --fake")


if __name__ == "__main__":
    main()
