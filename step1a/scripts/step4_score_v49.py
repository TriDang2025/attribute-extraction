"""wf_v4.9 V1: rescore the cached v4.8 W3 Step 4 chains with scorable loop-2 columns (s1a/l2ids_v49.py).

python scripts/step4_score_v49.py [--l2-ids on|off]
on  -> results/wf_v49/v1/{scores.csv, v1.md}; score-map copies with L2_ ids in results/wf_v49/v1/<set>/step4_<A|B>/score_map (wf_v48 is read only).
off -> the W3 scoring, results/wf_v49/v1/scores_off.csv, compared with results/wf_v48/w3/scores.csv.
Views: "spans" = loop-2 mentions labelled by the 2.2 spans; "spans+hc" = plus the W1 human-check attribute for a loop-2 column without a span label.
Scoring reuses step4_score_v48.rows (-> step4_score_v46.score_chain / chain_mapping); gold is used for scoring only.
"""
import argparse
import json
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import gpu_v48 as G48  # noqa: E402
import mainclaim_v41 as MC  # noqa: E402
import score_v4 as SCR  # noqa: E402
import step4_score_v46 as S46  # noqa: E402
import step4_score_v48 as S48  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import l2ids_v49 as L  # noqa: E402
from s1a import mainclaim_v41 as M  # noqa: E402
from s1a import step4_gt as SG  # noqa: E402
from s1a import step4_pick_v49 as PK  # noqa: E402
from s1a import step4_score_v43 as SC43  # noqa: E402
from s1a import tear_cols as TC  # noqa: E402

OUT = ROOT / "results" / "wf_v49" / "v1"
W1 = ROOT / "results" / "wf_v48" / "w1"
V1_VARIANTS = {v: G48.OUT for v in ("A", "B")}   # {variant: root}, as step4_score_v48.rows; explicit so a registered AR (gpu_v49) is not scored here
VIEWS = ("spans", "spans+hc")
VIEW = S48.VIEW
CHECK = ("internet", "parking")


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def prepare(dev, run, names, variants=V1_VARIANTS, out=OUT):
    """{cols, levels (extended gt_L2), override (human-check fallback)} of one set; also writes the score-map copies with L2_ ids of every
    variant folder <root>/<dev>/step4_<v> that has a score map, to <out>/<dev>/step4_<v>/score_map (a variant not run yet has none)."""
    cols = L.loop2_columns(read_json(G48.W2 / dev / "merged_columns.json"))
    entity_of = {k: v["gt_entity"] for k, v in read_json(W1 / dev / "entity_map.json").items()}
    _, mt, labels, _ = M.load_set(dev)
    spans, _ = MC.load_spans(MC.SPANS)
    lab = L.loop2_labels(G48.LOOP1 / dev / "loop2" / "evidence" / "clusters.json", entity_of, M.known_labels(mt, labels),
                         TC.span_index(spans), json.loads(MC.TEAR_MAP.read_text(encoding="utf-8")))
    levels = L.extend(SG.read_gt_levels(ROOT / SCR.GT_LEVELS[dev]), lab, cols)
    key = pd.read_csv(W1 / dev / "human_check_key.csv", dtype=str, keep_default_na=False).to_dict("records")
    ids = L.column_ids(cols)
    seen = set()
    for v, root in variants.items():
        src = Path(root) / dev / f"step4_{v}" / "score_map" / "a_llama44" / run
        dst = Path(out) / dev / f"step4_{v}" / "score_map" / "a_llama44" / run
        for f in sorted(src.glob("*.json")):
            doc = read_json(f)
            for c in doc["columns"]:
                k = f"{f.stem}:{c['id']}"
                if k in ids:
                    c["mention_ids"] = ids[k]
                    seen.add(k)
            B.write_json(dst / f.name, doc)
    if seen != set(ids):
        raise ValueError(f"{dev}: loop-2 columns not in the score map: {sorted(set(ids) - seen)}")
    return {"cols": cols, "levels": levels, "override": L.fallback(cols, key, names)}


def opts_for(prep, view, out=OUT):
    def opts(v, dev):
        p = prep[dev]
        return {"handover": Path(out) / dev / f"step4_{v}" / "score_map" / "a_llama44", "gt_levels": p["levels"],
                "tweak": partial(L.apply_fallback, override=p["override"]) if view == "spans+hc" else None}
    return opts


def placement(gt, prep, df, opts, variants=V1_VARIANTS, hotel=None):
    """df plus internet_where / internet_gt / parking_where / parking_gt per finished chain (table name or "unused"; GT label of the column).
    hotel = {set: hotel entities} adds internet_hotel / parking_hotel (placed in a table whose main entity is a hotel entity, PK.in_hotel_table)."""
    rows = []
    for r in df.to_dict("records"):
        if r["finished"] and r["gt_view"] == VIEW:
            dev, run, v = r["set"], G48.SETS[r["set"]], r["variant"]
            c, mapping = S46.chain_mapping(gt, dev, run, Path(variants[v]) / dev / f"step4_{v}", r["seed"], **opts(v, dev))
            for name in CHECK:
                keys = [k for k, col in prep[dev]["cols"].items() if col["name"] == name]
                where = [t["name"] for t in c["tables"] for x in t["columns"] if x.get("source") in keys]
                where += ["unused"] * sum(u["source"] in keys for u in c.get("unused", []))
                r[f"{name}_where"] = ",".join(where) or "missing"
                if hotel:
                    r[f"{name}_hotel"] = PK.in_hotel_table(c, keys, hotel[dev])
                r[f"{name}_gt"] = ",".join(str(mapping[k]["gt"]) for k in keys if k in mapping and mapping[k]["gt"])
        rows.append(r)
    return pd.DataFrame(rows)


def label_counts(prep, names):
    """{set: (span-labelled loop-2 columns, fallback columns, columns, [unlabelled])}, on the variant A score map."""
    out = {}
    for dev, run in G48.SETS.items():
        full = SG.map_handover(OUT / dev / "step4_A" / "score_map" / "a_llama44", run, prep[dev]["levels"], names)
        lab = [k for k in prep[dev]["cols"] if full.get(k, {}).get("gt")]
        fb = [k for k in prep[dev]["override"] if k not in lab]
        out[dev] = (len(lab), len(fb), len(prep[dev]["cols"]), [k for k in prep[dev]["cols"] if k not in lab and k not in fb])
    return out


def summary_md(df, view):
    lines = [f"| {view}: {VIEW}, mean (range) | table F1 | grouping F1 | GT columns placed | unused | tables | internet: where / credited | parking: where / credited |",
             "|---" * 8 + "|"]
    for v in G48.VARIANTS:
        for dev in G48.SETS:
            d = df[(df["l2_view"] == view) & (df["variant"] == v) & (df["set"] == dev) & df["finished"] & (df["gt_view"] == VIEW)]
            if d.empty:
                continue
            recs = d.to_dict("records")
            cells = [S48.cell([S48.share(r, k) for r in recs]) for k in ("table_f1", "grouping_f1", "gt_columns_placed")]
            cells += [S48.cell([r["unused"] for r in recs], "{:.1f}"), S48.cell([r["tables"] for r in recs], "{:.1f}")]
            for n in CHECK:
                where = ", ".join(str(r[f"{n}_where"]) for r in recs)
                cells.append(f"{where} / {sum(bool(r[f'{n}_gt']) for r in recs)}/{len(recs)}")
            lines.append(f"| {v} {dev} ({len(recs)} chains) | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l2-ids", choices=("on", "off"), default="on")
    on = ap.parse_args().l2_ids == "on"
    gt = SC43.load_gt(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    if not on:
        p = OUT / "scores_off.csv"
        S48.rows(gt).to_csv(p, index=False, encoding="utf-8", lineterminator="\n")
        same = p.read_bytes() == (G48.OUT / "scores.csv").read_bytes().replace(b"\r\n", b"\n")   # the checkout may hold CRLF
        print("off switch reproduces results/wf_v48/w3/scores.csv (line endings aside):", same)
        return
    names = SG.gt_names(gt)
    prep = {dev: prepare(dev, run, names) for dev, run in G48.SETS.items()}
    parts = []
    for view in VIEWS:
        opts = opts_for(prep, view)
        parts.append(placement(gt, prep, S48.rows(gt, opts=opts, variants=V1_VARIANTS), opts).assign(l2_view=view))
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(OUT / "scores.csv", index=False, encoding="utf-8", lineterminator="\n")
    md = ["# wf_v4.9 V1: Step 4 chains of W3 with scorable loop-2 columns", "",
          "Loop-2 mentions get ids L2_<mention id>, labelled as in mainclaim_v41 (loop-1 mention with the same dialogue / turn / value, else the "
          "2.2 span); spans+hc adds the W1 human-check attribute for a loop-2 column with no span label. Scoring only.", ""]
    for dev, (n, fb, tot, rest) in label_counts(prep, names).items():
        md.append(f"- {dev}: {tot} loop-2 columns, {n} with a span label, {fb} take the human-check fallback, {len(rest)} neither ({', '.join(rest) or 'none'}).")
    for view in VIEWS:
        md += ["", summary_md(df, view)]
    (OUT / "v1.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
