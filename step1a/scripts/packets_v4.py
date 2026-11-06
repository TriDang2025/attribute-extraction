"""wf_v4 task 9: blind grading packets -> results/wf_v4/grading/{packets/<set>_<code>.md, key.json, README.md}.

python scripts/packets_v4.py [--seed 0]
Candidates per set: a (main, seed 0), b (main + signals), c2, e (v0), f, d, gt (GT main design), gt_planted (GT with 3 planted errors).
Candidate SQL = step4_sql.to_sql of the canonical schema (no comments, nothing renamed); reference SQL = results/wf_v4/gt/schema_gt_v1.sql.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step4_grading as P  # noqa: E402
from s1a import step4_gt as G  # noqa: E402
from s1a import step4_sql as Q  # noqa: E402

RES = ROOT / "results" / "wf_v4"
FINAL = RES / "colab" / "final"
SOURCE = {"a": lambda s: FINAL / f"a_{s}_s0" / "canonical.json", "b": lambda s: FINAL / f"b_{s}_s0" / "canonical.json",
          "c2": lambda s: FINAL / f"c2_{s}_s0" / "canonical.json", "e": lambda s: FINAL / f"e_{s}_v0" / "canonical.json",
          "f": lambda s: RES / "inputs" / s / "f.canonical.json", "d": lambda s: RES / "inputs" / s / "d.canonical.json"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=RES / "grading")
    a = ap.parse_args()
    gt = G.load_gt(ROOT / "gt" / "schema_gt_v1.yaml")
    gt_canon = G.to_canonical(gt)
    gt_sql = P.strip_sql((RES / "gt" / "schema_gt_v1.sql").read_text(encoding="utf-8"))
    template = (ROOT / "config" / "wf_v4_grading_prompt.txt").read_text(encoding="utf-8")
    codes = P.assign([(s, k) for s in P.SETS for k in P.KINDS], a.seed)
    repeats = P.pick_repeats(codes, a.seed)
    key = {"seed": a.seed, "packets": {}, "planted": {}, "repeats": {j: [codes[x] for x in v] for j, v in repeats.items()}}
    (a.out / "packets").mkdir(parents=True, exist_ok=True)
    for s in P.SETS:
        planted, errors = P.plant_errors(gt_canon, a.seed, s)
        key["planted"][s] = errors
        canon = {k: read(SOURCE[k](s)) for k in SOURCE} | {"gt": gt_canon, "gt_planted": planted}
        for k in P.KINDS:
            code = codes[(s, k)]
            text = P.fill_prompt(template, code, gt_sql, P.strip_sql(Q.to_sql(canon[k])))
            (a.out / "packets" / f"{s}_{code}.md").write_text(text, encoding="utf-8", newline="\n")
            key["packets"][code] = {"set": s, "candidate": k}
    (a.out / "key.json").write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (a.out / "README.md").write_text(P.readme(P.checklist(codes, repeats)), encoding="utf-8", newline="\n")
    print(len(key["packets"]), "packets ->", a.out)


if __name__ == "__main__":
    main()
