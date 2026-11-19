"""wf_v4.7 Z6: the v4.6 loop-2 tables and worked-example figure (scripts/loop2_report_v46.py, unchanged) on the Z4 run 1.

python scripts/loop2_report_v47.py  -> results/wf_v47/z6/report/{loop2.md, new_columns.csv, fig_worked_example.png}
Reads results/wf_v47/z4/run1/<set>/loop2/ and the entity map of results/wf_v47/z6/run1/<set>/ (run scripts/mainclaim_v47.py first).
The three Z4 runs gave the same answers (results/wf_v47/z4/settings.json), so run 1 stands for all.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import loop2_report_v46 as R  # noqa: E402

R.Y3 = ROOT / "results" / "wf_v47" / "z4" / "run1"
R.MC = ROOT / "results" / "wf_v47" / "z6" / "run1"
R.OUT = ROOT / "results" / "wf_v47" / "z6" / "report"
R.EXAMPLE = ("dev50b", "internet")   # 3 of 3 orders, as the figure text says

if __name__ == "__main__":
    R.main()
    md = R.OUT / "loop2.md"
    t = md.read_text(encoding="utf-8").replace("(wf_v4.6 Y5-Y7)", "(wf_v4.7 Z6, Z4 run 1)")
    md.write_text(t.replace("Voted = suggested in >= 2 of 3 orders.", "Voted = suggested in >= 1 of 3 orders (v4.7 r4)."), encoding="utf-8", newline=chr(10))
