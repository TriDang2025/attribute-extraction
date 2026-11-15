"""wf_v4.5 (diary Nov 15) W4, part 3: cost table and chart from the W4 runs (results/wf_v45/w4/n<size>/cost.json), plus the TEAR estimate.

python scripts/w4_cost_v45.py   -> results/wf_v45/w4/{cost_table.md, cost.csv, tear_estimate.json, fig_llm_tokens.png}

TEAR is not run. Its estimate uses the wf_v4.4 T9 method (scripts/t9_cost_v44.tear_estimate: TEAR's own prompt builders on each dialogue,
times the measured attempts and outputs of the 200-text TEAR run). The method needs each dialogue's TEAR table, which only the 300 pool
dialogues have, so sizes 50-300 (pool prefixes, as the corpora) are computed and 500 / 1000 extend the 300 value linearly per dialogue
(TEAR makes the same calls for every dialogue; marked "linear" in the table).
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import t9_cost_v44 as T9  # noqa: E402

OUT = ROOT / "results" / "wf_v45" / "w4"
SIZES = (50, 100, 200, 300, 500, 1000)
POOL_SIZES = (50, 100, 200, 300)
OURS, TEAR = "#2a78d6", "#eb6834"           # dataviz reference palette slots 1-2 (validated light; orange needs labels: every point is labelled)
INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"


def tear_estimates(seed=0):
    pool, tok = T9.load_pool(), T9.tokenizer()
    measured = T9.measured_tear(tok)
    est = {n: {**T9.tear_estimate(pool[:n], pool, seed, tok, measured), "how": "TEAR prompts"} for n in POOL_SIZES}
    per = {k: est[300][k] / 300 for k in ("calls", "tokens_in", "tokens_out")}
    for n in SIZES:
        if n not in est:
            est[n] = {"n": n, **{k: round(v * n) for k, v in per.items()}, "how": "linear from 300"}
    return est, "Llama tokenizer" if tok else "4 chars / token"


def rows(est):
    out = []
    for n in SIZES:
        c = json.loads((OUT / f"n{n}" / "cost.json").read_text(encoding="utf-8"))
        sp = OUT / f"n{n}" / "step4" / "final" / "status.json"
        st = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else []
        s4 = f"{sum(r['ok'] for r in st)}/{len(st)}"
        if c.get("step4_aborted"):
            s4 = "aborted (prompt over 30K)"
        out.append({"dialogues": n, "corpus_tokens": c["corpus_tokens"], "clusters": None, "columns": c.get("step3_columns"),
                    "calls": c["total_llm"]["calls"], "tokens_in": c["total_llm"]["prompt_tokens"], "tokens_out": c["total_llm"]["output_tokens"],
                    "step3_in": c["step3"]["prompt_tokens"], "step4_in": c["step4"]["prompt_tokens"], "step4": s4,
                    "step1a_s": c["step1a_2"]["seconds"]["total"] if c.get("step1a_2") else None,
                    "tear_calls": est[n]["calls"], "tear_in": est[n]["tokens_in"], "tear_out": est[n]["tokens_out"], "tear_how": est[n]["how"]})
    times = json.loads((OUT / "step1a_times.json").read_text(encoding="utf-8"))
    for r in out:
        r["clusters"] = times[str(r["dialogues"])]["clusters"]
    return out


def columns_when_missing(rs):
    """Step 3 column count of the runs written before cost.json carried it (from step3/scores/final_columns.json)."""
    for r in rs:
        if r["columns"] is None:
            f = json.loads((OUT / f"n{r['dialogues']}" / "step3" / "scores" / "final_columns.json").read_text(encoding="utf-8"))
            r["columns"] = sum(len(c) for ents in f.values() for c in ents.values())
    return rs


def chart(rs, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = [r["dialogues"] for r in rs]
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    other = {"tear_in": "tokens_in", "tokens_in": "tear_in"}
    for key, color, name in (("tear_in", TEAR, "TEAR (estimate, not run; 500 and 1000 linear)"), ("tokens_in", OURS, "Ours (Llama-3.1-8B, measured)")):
        y = [r[key] / 1e6 for r in rs]
        done = [i for i, r in enumerate(rs) if key == "tear_in" or not r["step4"].startswith(("0/", "aborted"))]
        cut = done[-1]
        ax.plot(x[:cut + 1], y[:cut + 1], color=color, lw=2, marker="o", ms=6, mec="#fcfcfb", mew=2, label=name, zorder=3)
        if cut < len(x) - 1:   # ours where Step 4 did not finish: dashed line, hollow markers
            ax.plot(x[cut:], y[cut:], color=color, lw=2, ls="--", zorder=2)
            ax.plot(x[cut + 1:], y[cut + 1:], ls="none", marker="o", ms=7, mfc="#fcfcfb", mec=color, mew=2, zorder=3,
                    label="Ours, Step 4 did not finish (Steps 1a-3 only)")
        for i, (xi, yi) in enumerate(zip(x, y)):
            up = rs[i][key] >= rs[i][other[key]]
            ax.annotate(f"{yi:.2f}M", (xi, yi), textcoords="offset points", xytext=(0, 8 if up else -15), ha="center", fontsize=8, color=INK)
    ax.set_xlabel("dialogues in the corpus", color=MUTED)
    ax.set_ylabel("LLM input tokens (millions)", color=MUTED)
    ax.set_xticks(x)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="y", color=GRID, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.set_ylim(0, None)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("LLM input tokens vs corpus size", fontsize=9, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def table_md(rs, tok_note):
    lines = ["| dialogues | corpus tokens | clusters | Step 3 columns | our calls | our tokens in / out | Step 3 / Step 4 in | Step 4 chains | "
             "Step 1a-2 s (GPU) | TEAR calls (est.) | TEAR tokens in / out (est.) |", "|" + "---|" * 11]
    for r in rs:
        tear_mark = "" if r["tear_how"] == "TEAR prompts" else " (linear)"
        lines.append(f"| {r['dialogues']} | {r['corpus_tokens']:,} | {r['clusters']} | {r['columns']} | {r['calls']:,} | {r['tokens_in']:,} / "
                     f"{r['tokens_out']:,} | {r['step3_in']:,} / {r['step4_in']:,} | {r['step4']} | {r['step1a_s']} | {r['tear_calls']:,.0f}{tear_mark} | "
                     f"{r['tear_in']:,.0f} / {r['tear_out']:,.0f}{tear_mark} |")
    lines += ["", f"TEAR tokens: {tok_note}. Our corpus tokens: Llama-3.1 tokenizer on Colab."]
    return "\n".join(lines) + "\n"


def main():
    est, tok_note = tear_estimates()
    (OUT / "tear_estimate.json").write_text(json.dumps({str(k): v for k, v in est.items()}, indent=1) + "\n", encoding="utf-8", newline="\n")
    rs = columns_when_missing(rows(est))
    with open(OUT / "cost.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rs)
    md = table_md(rs, tok_note)
    (OUT / "cost_table.md").write_text("# wf_v4.5 W4 cost test\n\n" + md, encoding="utf-8", newline="\n")
    chart(rs, OUT / "fig_llm_tokens.png")
    print(md)


if __name__ == "__main__":
    main()
