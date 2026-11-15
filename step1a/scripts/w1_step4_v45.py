"""wf_v4.5 (diary Nov 15) W1: Step 4 v4.4 confirm run with the "other" choice off (all other switches as config/wf_v44_step4.json), then the
freeze check against v4.3 (corrected scorer).

python scripts/w1_step4_v45.py --fake [--out DIR]   all stages with the fake model (laptop plumbing test; default out results/wf_v45/w1/fake)
python scripts/w1_step4_v45.py --score [--out DIR]  score the finished chains (t6_step4_v44.score), then DIR/freeze.md (default out results/wf_v45/w1)
The real run is on Colab: w1_step4_v45.run(backend) (inputs a_llama44 then c1, dev50 + dev50b, seeds 0-2 + vote; finished jobs are cached).
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import t6_step4_v44 as T6  # noqa: E402
from s1a import step4_fake_v44 as F  # noqa: E402
from s1a import step4_v44 as S  # noqa: E402

OUT = ROOT / "results" / "wf_v45" / "w1"
INPUTS = ("a_llama44", "c1")
# v4.3 Step 4 with the corrected scorer, single seed chains (wf_v4.4 report, T6 table)
V43 = {"a_llama44": {"table_f1": 0.672, "grouping_f1": 0.770, "placed": (164, 306)},
       "c1": {"table_f1": 0.753, "grouping_f1": 0.890, "placed": (199, 306)}}
C1_TOL = 0.005  # "about 0.75 or higher": 0.753 - C1_TOL, set before the run


def config():
    """config/wf_v44_step4.json with other_choice off."""
    return S.with_switches(S.load_config(), off=("other_choice",))


def run(backend, out=OUT, inputs=INPUTS, log=print):
    """Each input in turn (cache-safe rerun). Returns {input: t6 run info}."""
    return {inp: T6.run(backend, out, inputs=(inp,), cfg=config(), log=log) for inp in inputs}


def single_means(out):
    """{input: {"table_f1", "grouping_f1", "placed": (k, n)}} over the finished single-seed chains, full GT."""
    with open(Path(out) / "scores.csv", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["reachable_only"] == "False" and r["kind"] == "main"]
    res = {}
    for inp in INPUTS:
        rs = [r for r in rows if r["input"] == inp]
        if rs:
            res[inp] = {"table_f1": sum(float(r["table_f1"]) for r in rs) / len(rs),
                        "grouping_f1": sum(float(r["grouping_f1"]) for r in rs) / len(rs),
                        "placed": (sum(int(r["gt_columns_placed_k"]) for r in rs), sum(int(r["gt_columns_placed_n"]) for r in rs)),
                        "chains": len(rs)}
    return res


def freeze_check(m):
    """[(check, v4.3, v4.4 other off, pass)] and the decision ('v4.4 other off' or 'v4.3')."""
    a, c = m.get("a_llama44"), m.get("c1")
    pa = a and a["placed"][0] / a["placed"][1]
    rows = [("GT columns placed, a_llama44", 0.536, pa, a is not None and pa >= 0.536),
            ("table F1, c1", V43["c1"]["table_f1"], c and c["table_f1"], c is not None and c["table_f1"] >= V43["c1"]["table_f1"] - C1_TOL),
            ("table F1, a_llama44", V43["a_llama44"]["table_f1"], a and a["table_f1"], a is not None and a["table_f1"] >= V43["a_llama44"]["table_f1"])]
    return rows, "v4.4 other off" if all(r[3] for r in rows) else "v4.3"


def write_freeze(out=OUT):
    m = single_means(out)
    rows, decision = freeze_check(m)
    f = lambda x: "missing" if x is None else f"{x:.3f}"  # noqa: E731
    lines = ["# wf_v4.5 W1: Step 4 freeze check", "",
             "Single seed chains, means of F1, counts summed; full GT; corrected scorer. v4.3 values from the wf_v4.4 report (T6 table).", "",
             "| check | v4.3 (corrected) | v4.4 other off | pass |", "|---|---|---|---|"]
    lines += [f"| {n} | {b:.3f} | {f(v)} | {'yes' if ok else 'no'} |" for n, b, v, ok in rows]
    lines += ["", f"**Freeze: {decision}.**", ""]
    for inp, x in m.items():
        lines.append(f"- {inp}: {x['chains']} chains, table F1 {x['table_f1']:.3f}, grouping F1 {x['grouping_f1']:.3f}, "
                     f"GT placed {x['placed'][0]}/{x['placed'][1]} ({x['placed'][0] / x['placed'][1]:.3f})")
    text = "\n".join(lines) + "\n"
    (Path(out) / "freeze.md").write_text(text, encoding="utf-8", newline="\n")
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if not (a.fake or a.score):
        ap.error("give --fake and/or --score (the real run is the Colab notebook calling w1_step4_v45.run)")
    out = a.out or (OUT / "fake" if a.fake else OUT)
    if a.fake:
        print({k: v["finished"] for k, v in run(F.FakeV44(), out).items()})
    if a.score:
        T6.score(out)
        print(write_freeze(out))


if __name__ == "__main__":
    main()
