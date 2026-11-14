"""wf_v4.4 (diary Nov 14) T4: Step 3 v4.4 -> a_llama44 (s1a/step3_v44.py; config/wf_v44_step3.json).

python scripts/t4_step3_v44.py --build [--out DIR] [--variant v1]  -> DIR (default results/wf_v44/t4): names jobs (switches of the config),
                                                                      keyed split jobs, A rows, blocks.json
python scripts/t4_step3_v44.py --fake  [--out DIR] [--ablate SWITCH]-> every stage with the fake model and the fake encoder (plumbing only)
python scripts/t4_step3_v44.py --score [--out DIR]                 -> DIR/scores/*, DIR/a_llama44/<set>/a.columns.json
Notebook (GPU): `full_run(out, backend, cfg, encoder, name_vecs, save_vecs=True)` = build + run + score + a_llama44, e.g.
    full_run(OUT, VllmBackend44(...), load_config(), step3_v44.bge_m3_encoder(), name_vecs=OUT / "name_vecs.npz", save_vecs=True)
The 3 ablations (one call each, dev50 + dev50b order 0, same layout under results/wf_v44/t4_ablate/<switch>/):
    ablation("similar_batches" | "rescue" | "merge", backend, cfg, encoder)       # name vectors are read from t4/name_vecs.npz, never written
Step 4 input: step3_v44.a_llama44_files() -> {set: path relative to the step1a root} (the `a2_files` argument of nov16_v41.step4_chains, or
the `columns_file` of a chain with input "a_llama44"); step3_v44.a_llama44_file(set) -> absolute path; step3_v44.write_a_llama44(out) writes them.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step3_v44 as S  # noqa: E402

OUT = S.OUT_T4
load_config, build, run, score_v44, write_a_llama44 = S.load_config, S.build, S.run, S.score_v44, S.write_a_llama44
full_run, ablation, a_llama44_files, a_llama44_file = S.full_run, S.ablation, S.a_llama44_files, S.a_llama44_file


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for k in ("build", "fake", "score"):
        g.add_argument(f"--{k}", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--variant", default="v1", help="names schema variant (default v1; the notebook uses the T1 choice)")
    ap.add_argument("--ablate", choices=S.SWITCHES, help="with --fake: the ablation run of this switch (written under --out/<switch>)")
    a = ap.parse_args()
    cfg = load_config()
    if a.build:
        names, jobs = build(a.out, cfg, a.variant)
        print(f"{len(names)} names jobs, {len(jobs)} manifest jobs in {a.out}")
    elif a.fake and a.ablate:
        print(ablation(a.ablate, S.FakeStep44(), cfg, S.FakeEncoder(), root=a.out, name_vecs=a.out / "name_vecs.npz", variant=a.variant))
    elif a.fake:
        print(full_run(a.out, S.FakeStep44(), cfg, S.FakeEncoder(), name_vecs=a.out / "name_vecs.npz", save_vecs=True, variant=a.variant))
    else:
        score_v44(a.out)
        print((a.out / "scores" / "summary.md").read_text(encoding="utf-8"))
        print("a_llama44 columns:", write_a_llama44(a.out))


if __name__ == "__main__":
    main()
