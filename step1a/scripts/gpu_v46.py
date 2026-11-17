"""wf_v4.6 (diary Nov 16) GPU jobs, called by the notebook colab/S1A_wf46_colab.ipynb (one session, model loaded once).

- y3:  loop 1 with LLM entity names (s1a/pipeline_v46, loops=1, Step 4 v4.3 seed 0 only) on raw dev50 and dev50b -> results/wf_v46/y3/<set>/
- y56: loop 2 (s1a/loop2_v46.run_loop2: Step 1b 3 orders + vote, evidence check, Step 3 naming) on the y3 folders -> results/wf_v46/y3/<set>/loop2/
- y8:  Step 4 v4.3 with pass 2 in batches of 20 (seed 0) on the y3 loop-1 input -> results/wf_v46/y3/<set>/step4_p2b20/
Step 1a-2 is not run here: results/graph_v22_c_n50 (wf_v4.5 W2) and results/graph_v22_c_n50b (wf_v4.6, laptop) come from git.
Scoring is on the laptop afterwards (block 3). The fake check of the whole driver: python scripts/gpu_v46.py --fake (no GPU).
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from s1a import batch_v4 as B  # noqa: E402
from s1a import loop2_v46 as L2  # noqa: E402
from s1a import pipeline_v45 as PL  # noqa: E402
from s1a import pipeline_v46 as PL46  # noqa: E402
from s1a import step4_v44 as S4  # noqa: E402

OUT = ROOT / "results" / "wf_v46" / "y3"
SETS = {"dev50": "c_n50", "dev50b": "c_n50b"}       # dev set -> run name of its raw-corpus Step 1a-2 folder results/graph_v22_<run>
STEP4 = "v43"                                       # frozen Step 4
P2_BATCH = 20


def out_dir(dev, root=OUT):
    return Path(root) / dev


def need(sets=SETS):
    """Files the GPU jobs read (from git); [] = all there."""
    return [str(p) for run in sets.values() for p in (PL.CO.run_dir(run) / "spans" / "mentions.csv", PL.CO.run_dir(run) / "spans" / "vectors.npz",
                                                      PL.CO.run_dir(run) / "docs.jsonl") if not p.exists()]


def y3(backend, enc3, enc_1a, sets=SETS, load_seconds=None, root=OUT, log=print, **kw):
    """Loop 1 with LLM entity names on each set (Step 1a-2 reused). Returns {dev: cost dict}."""
    res = {}
    for dev, run in sets.items():
        t0 = time.time()
        res[dev] = PL46.run_pipeline(None, out_dir(dev, root), run, backend, enc3, enc_1a, PL.step4_config(STEP4), load_seconds=load_seconds, log=log,
                                     skip_1a=True, step4_seeds=(0,), **kw)
        log(f"y3 {dev}: {res[dev]['total_llm']} | names {res[dev]['entity_names']['calls']} calls | {time.time() - t0:.0f} s wall")
    return res


def y56(backend, enc_1a, gliner_loader, sets=SETS, root=OUT, log=print, cfg=None):
    """Loop 2 on each y3 folder. Returns {dev: run_loop2 info}."""
    res = {}
    for dev, run in sets.items():
        res[dev] = L2.run_loop2(out_dir(dev, root), run, backend, enc_1a, gliner_loader, cfg, log=log)
        log(f"y5/y6 {dev}: {json.dumps({k: v for k, v in res[dev].items() if k != 'cost'})} | cost {res[dev]['cost']['total']}")
    return res


def y8(backend, sets=SETS, root=OUT, log=print):
    """Step 4 v4.3 with pass 2 in batches of P2_BATCH, seed 0, on the y3 Step 4 input. Returns {dev: chain status}."""
    res = {}
    for dev, run in sets.items():
        out = out_dir(dev, root)
        entmap = B.read_json(out / "entities.json")
        with PL.use_corpus(run, entmap, out / "a_prompts"):
            S4.run(out / f"step4_p2b{P2_BATCH}", backend, inputs=("a_llama44",), sets=(run,), seeds=(0,),
                   cfg=PL.step4_config(STEP4, P2_BATCH), step3_dirs={"a_llama44": out / "step3" / "a_llama44"})
        res[dev] = B.read_json(out / f"step4_p2b{P2_BATCH}" / "final" / "status.json")
        log(f"y8 {dev}: {[(r['run'], r['ok']) for r in res[dev]]}")
    return res


def fake_check(root):
    """The whole driver with the laptop fakes (fake LLMs, fake encoders, fake GLiNER) into `root`; raises on any failure."""
    import numpy as np
    from s1a import entity_names_v46 as EN
    from s1a import step3_v44 as S3
    from s1a import step4_fake_v44 as F4

    class Fakes:                                   # one backend for every job family, like the real VllmBackend44
        def __init__(self):
            self.s3, self.s4, self.names, self.l2 = S3.FakeStep44(), F4.FakeV44(), EN.FakeNames(), L2.FakeLoop2LLM()

        def run(self, folder, jobs):           # by folder: loop2/..., names/, step4*/, else Step 3
            parts = Path(folder).parts
            if "loop2" in parts:
                return self.l2.run(folder, jobs)
            if parts[-1] == "names":
                return self.names.run(folder, jobs)
            if any(p.startswith("step4") for p in parts):
                return self.s4.run(folder, jobs)
            return self.s3.run(folder, jobs)

    class Enc:                                     # .encode(list[str]) -> unit vectors (loop-2 evidence check)
        def encode(self, texts):
            v = np.array([[hash((t, i)) % 997 + 1.0 for i in range(8)] for t in texts], dtype="float32")
            return v / np.linalg.norm(v, axis=1, keepdims=True)

    class NoGliner:
        def predict_entities(self, text, labels, threshold=0.5):
            return []

        def inference(self, texts, labels, threshold=0.5, **kw):
            return [[] for _ in texts]

    fb = Fakes()
    sets = {k: v for k, v in SETS.items() if PL.CO.run_dir(v).exists()}
    y3(fb, S3.FakeEncoder(), Enc(), sets, root=root)
    y56(fb, Enc(), NoGliner, sets, root=root)
    y8(fb, sets, root=root)
    return sets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true", help="laptop check with fakes (no GPU)")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v46" / "fake_check")
    a = ap.parse_args()
    if not a.fake:
        ap.error("the real run is the notebook colab/S1A_wf46_colab.ipynb; give --fake for the laptop check")
    print("checked sets:", fake_check(a.out))


if __name__ == "__main__":
    main()
