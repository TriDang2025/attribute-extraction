"""wf_v4 task 1: data signals for every Step-3 handover column -> results/wf_v4/signals/<set>/.

python scripts/signals_v4.py [--set dev50 --set dev50b]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from s1a.step4_signals import write_set  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", dest="sets")
    ap.add_argument("--out", default=str(ROOT / "results" / "wf_v4" / "signals"))
    a = ap.parse_args()
    for s in a.sets or ["dev50", "dev50b"]:
        out = write_set(s, Path(a.out) / s)
        fd = out["fd"]
        print(s, "columns", len(out["columns"]), "pairs", len(out["pairs"]),
              "fd holds", int((fd["status"] == "holds").sum()), "of", len(fd))


if __name__ == "__main__":
    main()
