"""wf_v4.3 report figure: Step 4 v4.3 schema (Llama, input a, dev50, seed 0) next to the GT schema, as boxes and arrows.

python scripts/fig_schema_v43.py OUT.png   (reads results/wf_v43/u4/fig_schema_a_dev50_s0.json)
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results" / "wf_v43" / "u4" / "fig_schema_a_dev50_s0.json"
MAX_COLS = 9


def links(schema):
    """(from table, to table) for each foreign key, plus the relationships list if present."""
    out = []
    for t in schema["tables"]:
        for fk in t.get("foreign_keys") or []:
            ref = fk.get("ref_table") or fk.get("references") or fk.get("to") or fk.get("table")
            if isinstance(ref, dict):
                ref = ref.get("table")
            if ref:
                out.append((t["name"], ref))
    for r in schema.get("relationships") or []:
        out.append((r.get("from"), r.get("to")))
    return out


def draw(ax, schema, title):
    tables = schema["tables"]
    n = len(tables)
    cols_per_row = 3
    pos = {}
    for i, t in enumerate(tables):
        x, y = (i % cols_per_row) * 3.4, -(i // cols_per_row) * 4.2
        pos[t["name"]] = (x + 1.5, y)
        cols = [c["name"] + (" (PK)" if c.get("pk") else "") + (" (FK)" if c.get("fk") else "") for c in t["columns"]]
        shown = cols[:MAX_COLS] + ([f"... +{len(cols) - MAX_COLS} more"] if len(cols) > MAX_COLS else [])
        h = 0.35 * (len(shown) + 1) + 0.2
        ax.add_patch(FancyBboxPatch((x, y - h), 3.0, h, boxstyle="round,pad=0.05", fc="#eef3fb", ec="#33557a"))
        ax.text(x + 1.5, y - 0.3, f"{t['name']}  ({len(cols)} cols)", ha="center", va="center", fontsize=8, weight="bold")
        for k, s in enumerate(shown):
            ax.text(x + 0.12, y - 0.65 - 0.35 * k, s, fontsize=6.5, va="center")
    for a, b in links(schema):
        if a in pos and b in pos and a != b:
            ax.annotate("", xy=pos[b], xytext=pos[a], arrowprops=dict(arrowstyle="->", color="#b0413e", lw=1.4))
    nl = len(links(schema))
    ax.set_title(f"{title}\n{n} tables, {nl} links", fontsize=10)
    rows = (n + cols_per_row - 1) // cols_per_row
    ax.set_xlim(-0.3, cols_per_row * 3.4)
    ax.set_ylim(-rows * 4.2 - 0.5, 0.4)
    ax.axis("off")


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    draw(axes[0], d["model"], f"Llama-3.1-8B, Step 4 v4.3 (input a, {d['set']}, seed 0)")
    draw(axes[1], d["gt"], "Ground truth (schema GT v1)")
    fig.tight_layout()
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    main()
