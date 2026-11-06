"""wf_v4 task 16: Step-4 handover -> step1a/handover_step4/<set>/{schema.json, schema.sql, operations.json} (+ FORMAT.md by hand).

python scripts/handover_v4.py [--run main] [--sets dev50,dev50b]
The chosen setting is main (input a), column order seed 0: results/wf_v4/colab/final/a_<set>_s0/canonical.json. schema.sql and operations.json are
regenerated from the canonical schema by step4_sql (same code that wrote final/<run>/).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a import step4_handover as H  # noqa: E402
from s1a import step4_sql as Q  # noqa: E402

FINAL = ROOT / "results" / "wf_v4" / "colab" / "final"
ENTITIES = ("train", "hotel", "restaurant")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default="dev50,dev50b")
    ap.add_argument("--out", type=Path, default=ROOT / "handover_step4")
    a = ap.parse_args()
    for s in a.sets.split(","):
        run = f"a_{s}_s0"
        canon = json.loads((FINAL / run / "canonical.json").read_text(encoding="utf-8"))
        hand = {e: json.loads((ROOT / "handover" / s / f"{e}.json").read_text(encoding="utf-8")) for e in ENTITIES}
        schema = H.build(canon, hand, s, run)
        problems = H.check(schema, hand)
        if problems:
            sys.exit(f"{run}: " + "; ".join(problems))
        out = a.out / s
        out.mkdir(parents=True, exist_ok=True)
        (out / "schema.json").write_text(json.dumps(schema, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (out / "schema.sql").write_text(Q.to_sql(canon), encoding="utf-8", newline="\n")
        (out / "operations.json").write_text(json.dumps(Q.to_operations(canon), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        n = sum(1 for t in schema["tables"] for c in t["columns"] if c["source"])
        print(f"{s}: {len(schema['tables'])} tables, {n} linked columns, {len(schema['unused'])} unused -> {out}")


if __name__ == "__main__":
    main()
