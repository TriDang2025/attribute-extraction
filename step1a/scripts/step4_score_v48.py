"""wf_v4.8 W3: score the Step 4 chains of results/wf_v48/w3/<set>/step4_<A|B>/ (seeds 0-2) with the v4.6 scorer (scripts/step4_score_v46.score_chain).

python scripts/step4_score_v48.py  -> results/wf_v48/w3/{scores.csv, w3.md}
Main view: the Y1 rule (step4_gt.reachable_by_annotations); keys: rule b (pk_right_b) is the main number, rule a (pk_right) next to it.
Per variant and set: chains finished, then mean (min-max) over the finished chains of tables, table F1, grouping F1, GT columns placed,
columns in "unused", PK right, calls and tokens. The v4.3 one-pass row is the v4.6 seed-0 chain (results/wf_v46/step4/scores.csv, loop-1 input).
Pick rule (diary): higher table F1 and grouping F1 on both sets, no collapse (1 table) in any chain; if close, fewer unused columns.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import gpu_v48 as G  # noqa: E402
import step4_score_v46 as S46  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402

OUT = G.OUT
V46 = ROOT / "results" / "wf_v46" / "step4" / "scores.csv"
VIEW = "Y1 rule"
SHARES = ("table_f1", "grouping_f1", "gt_columns_placed", "pk_right_b", "pk_right")


def rows(gt, root=OUT, opts=None, variants=None):
    """opts: callable(variant, set) -> kwargs of S46.chain_mapping (score map, gt levels, tweak); None = the W3 scoring.
    variants: {variant: root} (folder <root>/<set>/step4_<variant>, a folder without final/ = "not run"); None = every gpu_v48 variant under root."""
    out = []
    for v, vroot in (variants or {v: root for v in G.VARIANTS}).items():
        for dev, run in G.SETS.items():
            folder = Path(vroot) / dev / f"step4_{v}"
            status = {r["run"]: r for r in json.loads((folder / "final" / "status.json").read_text(encoding="utf-8"))} if (folder / "final").exists() else {}
            for s in G.SEEDS:
                cid = f"a_llama44_{run}_s{s}"
                if not status.get(cid, {}).get("ok"):
                    out.append({"variant": v, "set": dev, "seed": s, "finished": False, "error": status.get(cid, {}).get("error", "not run")})
                    continue
                c = json.loads((folder / "final" / cid / "canonical.json").read_text(encoding="utf-8"))
                for r in S46.score_chain(gt, v, dev, run, folder, s, **(opts(v, dev) if opts else {})):
                    out.append({"variant": v, "seed": s, "finished": True, "unused": len(c.get("unused", [])), **r})
    return pd.DataFrame(out)


def share(r, k):
    n = r.get(f"{k}_n")
    return r[f"{k}_k"] / n if n else r.get(k)


def cell(vals, fmt="{:.3f}"):
    vals = [x for x in vals if pd.notna(x)]
    if not vals:
        return "n/a"
    m = sum(vals) / len(vals)
    return fmt.format(m) + (f" ({fmt.format(min(vals))}-{fmt.format(max(vals))})" if len(vals) > 1 else "")


def table_md(df):
    v46 = pd.read_csv(V46)
    v46 = v46[(v46["label"] == "v4.6 LLM names") & (v46["gt_view"] == VIEW)].set_index("set") if V46.exists() else None
    groups = [("v4.3 one pass (v4.6 s0, loop 1)", None)] + [(f"{v}: {'batched' if v == 'A' else 'batched + neutral ids'}", v) for v in G.VARIANTS]
    metrics = [("chains finished", None), ("tables per chain", "tables"), ("table F1", "table_f1"), ("grouping F1", "grouping_f1"),
               ("GT columns placed", "gt_columns_placed"), ('columns in "unused"', "unused"), ("PK right, rule b", "pk_right_b"),
               ("PK right, rule a", "pk_right"), ("calls", "calls"), ("prompt tokens", "prompt_tokens"), ("output tokens", "output_tokens")]
    lines = [f"| dev50 / dev50b, mean (range), {VIEW} | " + " | ".join(g for g, _ in groups) + " |", "|---" * (len(groups) + 1) + "|"]
    for label, k in metrics:
        cells = []
        for _, v in groups:
            per_set = []
            for dev in G.SETS:
                if v is None:
                    if v46 is None or dev not in v46.index:
                        per_set.append("n/a")
                        continue
                    r = v46.loc[dev]
                    per_set.append("1/1" if k is None else "n/a" if k == "unused" else cell([share(r, k) if k in SHARES else r[k]],
                                                                                           "{:.0f}" if k not in SHARES else "{:.3f}"))
                    continue
                d = df[(df["variant"] == v) & (df["set"] == dev)]
                ok = d[d["finished"] & (d.get("gt_view") == VIEW)] if "gt_view" in d else d.iloc[0:0]
                if k is None:
                    per_set.append(f"{len(ok)}/{len(G.SEEDS)}")
                else:
                    per_set.append(cell([share(r, k) if k in SHARES else r[k] for r in ok.to_dict("records")],
                                        "{:.3f}" if k in SHARES else "{:.1f}" if k in ("tables", "unused") else "{:,.0f}"))
            cells.append(" / ".join(per_set))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


DESC = {"A": "batched", "B": "batched + neutral ids", "BM": "B + merge_same_entity", "AR": "A + p2_reask"}


def figure(gt, dev="dev50", seed=0, root=OUT, variants=None, out=None):
    """out (default <root>/fig_schema_<dev>_s<seed>.png): each variant (default A and B; {variant: root} as in rows) and the GT main design,
    side by side (fig_schema_v43.draw)."""
    import matplotlib.pyplot as plt
    import fig_schema_v43 as FIG
    from s1a import step4_gt as SG
    run = G.SETS[dev]
    variants = variants or {v: root for v in ("A", "B")}
    fig, axes = plt.subplots(1, len(variants) + 1, figsize=(8 * (len(variants) + 1), 10))
    for ax, (v, vroot) in zip(axes, variants.items()):
        c = json.loads((Path(vroot) / dev / f"step4_{v}" / "final" / f"a_llama44_{run}_s{seed}" / "canonical.json").read_text(encoding="utf-8"))
        FIG.draw(ax, SC43._schema_view(c), f"Variant {v} ({DESC[v]}), {dev}, seed {seed}")
    FIG.draw(axes[-1], SC43._schema_view(SG.to_canonical(gt)), "Ground truth (schema GT v1)")
    fig.tight_layout()
    p = Path(out or Path(root) / f"fig_schema_{dev}_s{seed}.png")
    fig.savefig(p, dpi=110)
    return p


def main():
    gt = SC43.load_gt(ROOT)
    print("wrote", figure(gt))
    df = rows(gt)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
    full = df[df.get("gt_view", pd.Series(dtype=str)) == "full"] if "gt_view" in df else df
    names = [f"- {r['variant']} {r['set']} s{r['seed']}: {r['table_names']}" for r in full.to_dict("records") if r.get("finished")]
    md = "# wf_v4.8 W3: Step 4 on the loop 1 + 2 attributes after W2\n\n" + table_md(df) + "\n\nTables per chain:\n\n" + "\n".join(names) + "\n"
    (OUT / "w3.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)


if __name__ == "__main__":
    main()
