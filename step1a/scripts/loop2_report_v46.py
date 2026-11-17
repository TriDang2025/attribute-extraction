"""wf_v4.6 Y5-Y7: loop-2 tables of the GPU run and the worked-example figure.

python scripts/loop2_report_v46.py  -> results/wf_v46/loop2/{loop2.md, new_columns.csv, fig_worked_example.png}
Reads results/wf_v46/y3/<set>/loop2/ (step1b/review.json, suggestions.csv, columns_l2.json, evidence/clusters.json, cost.json) and the
scoring-only entity map of scripts/mainclaim_v46.py (results/wf_v46/mainclaim/<set>/entity_map.json). No LLM, no models.
"""
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

Y3 = ROOT / "results" / "wf_v46" / "y3"
MC = ROOT / "results" / "wf_v46" / "mainclaim"
OUT = ROOT / "results" / "wf_v46" / "loop2"
SETS = ("dev50", "dev50b")
N_SENT = 2
EXAMPLE = ("dev50", "amenities")       # (set, new column) of the figure


def load(dev):
    d = Y3 / dev / "loop2"
    rj = lambda p: json.loads((d / p).read_text(encoding="utf-8"))  # noqa: E731
    cl = rj("evidence/clusters.json")
    return {"review": rj("step1b/review.json"), "sug": pd.read_csv(d / "suggestions.csv", keep_default_na=False), "cols": rj("columns_l2.json"),
            "clusters": {c["id"]: c for c in (cl.get("clusters") if isinstance(cl, dict) else cl)}, "cost": rj("cost.json"),
            "emap": json.loads((MC / dev / "entity_map.json").read_text(encoding="utf-8"))}


def entity_rows(dev, x):
    """Per entity: GT entity (scoring only), attributes, flagged, suggested names, voted (>= 2 of 3 orders), passed evidence, new columns."""
    rows = []
    for ent, rv in x["review"].items():
        s = x["sug"][x["sug"]["entity"] == ent]
        new = [c for c in x["cols"].get(ent, []) if c["status"] == "new"]
        rows.append({"set": dev, "entity": ent, "gt_entity": x["emap"][ent]["gt_entity"], "attributes": len(rv["verdicts"]),
                     "flagged": sum(v["verdict"] == "flag" for v in rv["verdicts"].values()), "suggested": len(s),
                     "voted": int((s["stage"] != "vote").sum()), "passed_evidence": int(s["stage"].isin(["added", "dupcheck", "step3"]).sum()),
                     "new_columns": len(new)})
    return rows


def new_columns(dev, x):
    """One row per new loop-2 column: name, entity, GT entity, mentions, top values, Step 1b names behind it, N_SENT evidence sentences."""
    out = []
    for ent, cols in x["cols"].items():
        for c in cols:
            if c["status"] != "new":
                continue
            ms = [m for cid in c["clusters"] for m in x["clusters"][cid]["mentions"]]
            seen, sents = set(), []
            for m in ms:
                if m["dialogue_id"] not in seen:
                    seen.add(m["dialogue_id"])
                    sents.append(f"{m['context']} [{m['dialogue_id']}, value: {m['text']}]")
            names = sorted({x["clusters"][cid]["name"] for cid in c["clusters"]})
            out.append({"set": dev, "entity": ent, "gt_entity": x["emap"][ent]["gt_entity"], "column": c["name"], "step1b_names": "; ".join(names),
                        "n_mentions": c["n_mentions"], "top_values": "; ".join(c["top_values"]), "evidence": sents[:N_SENT]})
    return out


def figure(row, path):
    """Three boxes: Step 1b suggestion -> evidence sentences -> final column."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    boxes = [("1. Step 1b (Llama-3.1-8B)", f'"Which information is still missing\nfor this {row["entity"]}?"\n\nsuggested: {row["step1b_names"]}\n(3 of 3 orders)'),
             ("2. Evidence check (bge-m3 + GLiNER)", "\n\n".join(textwrap.fill(s, 34) for s in row["evidence"])),
             ("3. New column (Step 3 naming)", f'{row["column"]}\n\n{row["n_mentions"]} mentions\nvalues: {textwrap.fill(row["top_values"], 30)}')]
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    for i, (title, body) in enumerate(boxes):
        x0 = 0.2 + i * 4
        ax.add_patch(FancyBboxPatch((x0, 0.2), 3.4, 3.4, boxstyle="round,pad=0.05", fc="#f4f6fb", ec="#4a5a80"))
        ax.text(x0 + 1.7, 3.85, title, ha="center", va="center", fontsize=10, weight="bold")
        ax.text(x0 + 0.15, 3.4, body, ha="left", va="top", fontsize=8.2, family="DejaVu Sans")
        if i < 2:
            ax.annotate("", xy=(x0 + 3.95, 1.9), xytext=(x0 + 3.45, 1.9), arrowprops=dict(arrowstyle="->", lw=1.6, color="#4a5a80"))
    ax.set_title(f"Loop 2, one new attribute ({row['set']}, entity '{row['entity']}' = GT {row['gt_entity']})", fontsize=11)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {dev: load(dev) for dev in SETS}
    ents = pd.DataFrame([r for dev, x in data.items() for r in entity_rows(dev, x)])
    news = [r for dev, x in data.items() for r in new_columns(dev, x)]
    pd.DataFrame([{**r, "evidence": " || ".join(r["evidence"])} for r in news]).to_csv(OUT / "new_columns.csv", index=False, encoding="utf-8",
                                                                                     lineterminator="\n")
    lines = ["# Loop 2 with Llama-3.1-8B (wf_v4.6 Y5-Y7)", "", "## Step 1b and evidence check per entity", "",
             "GT entity = scoring only (majority of the mentions). Voted = suggested in >= 2 of 3 orders.", "",
             "| set | entity | GT entity | attributes | flagged | suggested names | voted | passed evidence | new columns |", "|---" * 9 + "|"]
    lines += [f"| {r.set} | {r.entity} | {r.gt_entity} | {r.attributes} | {r.flagged} | {r.suggested} | {r.voted} | {r.passed_evidence} | {r.new_columns} |"
              for r in ents.itertuples()]
    for dev, x in data.items():
        st = x["sug"]["stage"].value_counts().to_dict()
        ev = x["sug"][x["sug"]["stage"] == "evidence"]["reason"].str.extract(r"^(overlap|no spans|n_dialogues|support)")[0].value_counts().to_dict()
        c = x["cost"]
        lines += ["", f"- {dev}: failed at vote {st.get('vote', 0)}, at evidence {st.get('evidence', 0)} (first reason: "
                  + ", ".join(f"{k} {v}" for k, v in ev.items()) + f"), duplicate of a loop-1 column {st.get('dupcheck', 0)}, added {st.get('added', 0)}. "
                  f"Calls {c['total']['calls']} (Step 1b {c['step1b']['calls']}, Step 3 {c['step3']['calls']}), tokens {c['total']['prompt_tokens']:,} / "
                  f"{c['total']['output_tokens']:,}; finish length {c['step3'].get('finish', {}).get('length', 0)}, retried "
                  f"{c['step1b']['retried'] + c['step3']['retried']}."]
    lines += ["", "## New columns (loop 2)", ""]
    for r in news:
        lines += [f"- **{r['column']}** ({r['set']}, {r['entity']} = GT {r['gt_entity']}; from \"{r['step1b_names']}\"; {r['n_mentions']} mentions; "
                  f"values: {r['top_values']})"] + [f"  - {s}" for s in r["evidence"]]
    (OUT / "loop2.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    ex = next(r for r in news if (r["set"], r["column"]) == EXAMPLE)
    figure(ex, OUT / "fig_worked_example.png")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
