"""wf_v3.4 evidence table (SCORER_V34_CONTRACT.md, W1).

python scripts/evidence_v34.py --run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 --out results/loop1_v34
Writes <out>/evidence.csv (one row per clustered mention of the 3 pilot entities, with each variant's name, action,
group and placement) and <out>/attrs.csv (the attributes of every variant label).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import v34_data as V  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--dir32", required=True, type=Path)
    ap.add_argument("--dir31", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    _, data = V.load_all(a.run, a.dir32, a.dir31)
    a.out.mkdir(parents=True, exist_ok=True)
    ev = V.evidence_table(data)
    ev.to_csv(a.out / "evidence.csv", index=False, encoding="utf-8", lineterminator="\n")
    V.attrs_table(data).to_csv(a.out / "attrs.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(f"evidence.csv {len(ev)} rows; clusters per entity: "
          + ", ".join(f"{k} {len(d.cids)}" for k, d in data.items()) + f"; wrote {a.out}")


if __name__ == "__main__":
    main()
