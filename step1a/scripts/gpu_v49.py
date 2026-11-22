"""wf_v4.9 V3 GPU job, called by the notebook colab/S1A_wf49_colab.ipynb (one session, model loaded once).

Variant AR = v4.8 variant A (pass 2 in batches of 20) + p2_reask (s1a/step4_reask_v49.py): Step 4 v4.3 on the same W3 input as wf_v4.8 (built by
`prepare`, which reuses gpu_v48.prepare: results/wf_v48/w2 + wf_v47 loop 1), dev50 and dev50b, seeds 0-2 -> results/wf_v49/v3/<set>/step4_AR/.
Everything else is gpu_v48 (imported): the run function, the config, the sets and seeds. Variant AR is registered in gpu_v48.VARIANTS on import.
Scoring is on the laptop afterwards. Laptop: python scripts/gpu_v49.py --prepare | --fake [--out DIR] (no GPU).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import gpu_v46 as G46  # noqa: E402
import gpu_v48 as G48  # noqa: E402

OUT = ROOT / "results" / "wf_v49" / "v3"
SETS, SEEDS, Y3, config = G48.SETS, G48.SEEDS, G48.Y3, G48.config
G48.VARIANTS["AR"] = {**G48.VARIANTS["A"], "p2_reask": True}


def input_dir(dev, root=OUT):
    return G48.input_dir(dev, root)


def prepare(dev, run, root=OUT):
    return G48.prepare(dev, run, root)


def w3(backend, variants=("AR",), root=OUT, **kw):
    """Step 4 of variant AR on each set (gpu_v48.w3 into results/wf_v49/v3). Returns {(variant, dev): final/status.json rows}."""
    return G48.w3(backend, variants=variants, root=root, **kw)


def fake_check(root):
    """prepare + w3 with the laptop fake Step 4 model into `root`; raises on any failure. Returns {(variant, dev): [tables per seed]}."""
    for dev, run in SETS.items():
        prepare(dev, run, root)
    res = w3(G46.Fakes(), root=root, log=lambda *_: None)
    assert all(len(rows) == len(SEEDS) and all(r["ok"] for r in rows) for rows in res.values()), res
    return {k: [(r["tables"], r["repair_kinds"].get("p2_reask", 0)) for r in rows] for k, rows in res.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true", help="write the inputs (laptop, before the GPU session)")
    ap.add_argument("--fake", action="store_true", help="laptop check with fakes (no GPU)")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wf_v49_fake_check")
    a = ap.parse_args()
    if a.prepare:
        for dev, run in SETS.items():
            print("wrote", prepare(dev, run))
    elif a.fake:
        print(fake_check(a.out))
    else:
        ap.error("the real run is the notebook colab/S1A_wf49_colab.ipynb; give --prepare or --fake")


if __name__ == "__main__":
    main()
