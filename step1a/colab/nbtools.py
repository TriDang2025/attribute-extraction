"""Helpers of the notebook generators from make_nb49.py on (colab/make_nb42 .. make_nb48 each define their own copy of text / cell / swap)."""
import json
from pathlib import Path


def read_cells(path):
    """Cells of a notebook file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["cells"]


def text(c):
    return "".join(c["source"])


def cell(kind, s):
    c = {"cell_type": kind, "metadata": {}, "source": s.splitlines(keepends=True)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


def swap(s, pairs, what):
    """s with every (a, b) pair replaced; exits when an `a` is missing (the source notebook changed)."""
    for a, b in pairs:
        if a not in s:
            raise SystemExit(f"{what}: '{a}' not found; the source notebook changed, update the generator")
        s = s.replace(a, b)
    return s


def write_notebook(src, cells, out):
    """Write `cells` with the metadata of notebook `src` to `out` (LF, UTF-8)."""
    nb = json.loads(Path(src).read_text(encoding="utf-8"))
    nb["cells"] = cells
    Path(out).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
