"""wf_v3.3 noise sheet (PILOT_V33_CONTRACT.md, Part 0): one row per cluster that is gold noise or marked
not_attribute/unsure (also attribute_cue once it is in PV.MARKED) in any of the given decision tables, for hand
labelling.

python scripts/noise_sheet.py --run results/graph_v22_dev50 --decisions results/loop1_v31/decisions.csv
    results/loop1_v32/decisions.csv --out results/loop1_v33/noise_sheet.csv

Reads <run>/spans/{mentions.csv, vectors.npz, ...} (MN.load), <run>/spans/labels.csv and the docs of <run>.
Fill the `human` column with noise / real / mixed; the eval takes the sheet with --human-noise.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from pilot_eval_v31 import _read, _write  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--decisions", required=True, nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()

    e = MN.load(a.run / "spans")
    docs, _, _ = MN.load_shared(a.run)
    labels = _read(a.run / "spans" / "labels.csv")
    sheet = PS.noise_sheet(e.mentions, labels, [_read(p) for p in a.decisions], docs)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    _write(sheet, a.out)
    print(f"{len(sheet)} clusters -> {a.out}")


if __name__ == "__main__":
    main()
