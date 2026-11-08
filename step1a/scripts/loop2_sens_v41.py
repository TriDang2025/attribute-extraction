"""wf_v4.1 diary Nov 7 task 3: loop 2 sensitivity check (CPU only; report only, the keep rule is not changed).

python scripts/loop2_sens_v41.py --set dev50b      -> results/wf_v41/loop2_sens/<set>/{grid.csv, raw.json, run_info.json}
python scripts/loop2_sens_v41.py --report          -> results/wf_v41/loop2_sens/report.md (both sets)

Per label, GLiNER runs ONCE on all of the entity's turns at the lowest threshold (0.2). Every setting k in {20, 40, 80} x threshold in
{0.2, 0.3, 0.4} is a subset of that run: the top-k turns by retrieval cosine, spans with score >= threshold (GLiNER keeps the higher-score
span of an overlap first, so filtering by score gives the spans of a run at that threshold; src/spans.py does the same).
"support (all turns)" = the same support, computed on every entity turn instead of the top k.
Labels: the frozen Step 1b dry-run labels (results/wf_v41/step1b/labels_<set>.json). Run in the chunking venv. bge-m3 cache: one writer.
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import loop2_v41 as L2  # noqa: E402
from s1a import paths, split  # noqa: E402

KS, THRESHOLDS = (20, 40, 80), (0.2, 0.3, 0.4)
CONFIG = paths.ROOT / "config" / "wf_v41_loop2.json"
SETS = {"dev50": ("dev", 50), "dev50b": ("dev50b", 50)}
OUT = paths.RESULTS / "wf_v41" / "loop2_sens"


def label_rows(lab, number, docs, items, item_vecs, encoder, predict, mt, inst, ho, cfg0):
    """Grid rows (one per k x threshold) of one label, plus the raw spans."""
    stage1 = ho["stage1_entity"]
    allowed = L2.entity_turn_filter(inst, stage1)
    qv = encoder.encode([L2.query_text(lab)])[0]
    hits = L2.retrieve(items, item_vecs, qv, len(items), allowed)          # every entity turn, best first
    preds = predict([it["text"] for it, _ in hits], lab["label"], min(THRESHOLDS)) if hits else []
    raw = [dict(doc_id=it["doc_id"], turn=it["turn"], char_start=it["start"] + e["start"], char_end=it["start"] + e["end"],
                score=float(e["score"]), retrieval_cos=cos, rank=rank)          # as L2.extract, plus the turn's retrieval rank
           for rank, ((it, cos), ents) in enumerate(zip(hits, preds)) for e in ents]
    ent_insts = sorted(inst[inst["entity"] == stage1]["instance_id"])
    rows = []
    for t in THRESHOLDS:
        all_ms = L2.make_mentions([r for r in raw if r["score"] >= t], docs, allowed, 0)
        support_all = L2.evidence(all_ms, ent_insts, ho["columns"], mt, encoder, len(docs))["support"] if all_ms else 0.0
        for k in KS:
            cfg = cfg0 | {"k": k, "threshold": t}
            ms = L2.make_mentions([r for r in raw if r["score"] >= t and r["rank"] < k], docs, allowed, 0)
            ev = L2.evidence(ms, ent_insts, ho["columns"], mt, encoder, len(docs))
            keep, reason = L2.decide(ev, cfg) if ms else (False, "no spans")
            rows.append(dict(id=f"L2_{lab['entity']}#{number}", entity=lab["entity"], label=lab["label"], k=k, threshold=t,
                             keep=keep, n_mentions=len(ms), n_dialogues=ev["n_dialogues"], support=round(ev["support"], 4),
                             support_all_turns=round(support_all, 4), overlap=round(ev["overlap"], 3),
                             overlap_column=ev["overlap_column"], reason=reason, n_entity_turns=len(allowed)))
    return rows, raw


def run(set_name):
    from loop2_v41 import GlinerPredictor, load_handover
    from run import encoder as make_encoder
    from s1a import spans as SP
    from chk.data import single_docs
    cfg0 = json.loads(CONFIG.read_text(encoding="utf-8"))
    labels = L2.check_labels(json.loads((paths.RESULTS / "wf_v41" / "step1b" / f"labels_{set_name}.json").read_text(encoding="utf-8")))
    name, limit = SETS[set_name]
    docs = {d.doc_id: d for d in single_docs(split.dialogues(name, limit))}
    run_dir = paths.RESULTS / f"graph_v22_{set_name}" / "spans"
    mt = pd.read_csv(run_dir / "mentions.csv", keep_default_na=False)
    inst = pd.read_csv(run_dir / "instances.csv", keep_default_na=False)
    t0 = time.time()
    enc = make_encoder()
    predict = GlinerPredictor(SP.load())
    items = L2.turn_items(docs)
    item_vecs = enc.encode([it["text"] for it in items])
    rows, raws, nums = [], {}, {}
    for lab in labels:
        n = nums.get(lab["entity"], 0)
        nums[lab["entity"]] = n + 1
        r, raw = label_rows(lab, n, docs, items, item_vecs, enc, predict, mt, inst, load_handover(set_name, lab["entity"]), cfg0)
        rows += r
        raws[r[0]["id"]] = raw
        print(f"{r[0]['id']} {lab['label']}: {len(raw)} spans at {min(THRESHOLDS)}, {time.time() - t0:.0f}s", flush=True)
    enc.save()
    out = OUT / set_name
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "grid.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (out / "raw.json").write_text(json.dumps(raws, indent=1), encoding="utf-8", newline="\n")
    (out / "run_info.json").write_text(json.dumps(dict(set=set_name, seconds=round(time.time() - t0, 1), base_config=cfg0, ks=KS,
                                                       thresholds=THRESHOLDS, n_labels=len(labels)), indent=1), encoding="utf-8", newline="\n")
    print(f"done in {time.time() - t0:.0f}s -> {out}")


def report():
    lines = ["# Loop 2 sensitivity check (diary Nov 7, task 3)", "",
             "Report only: the keep rule is unchanged (n_dialogues >= 3, support >= 0.05, overlap < 0.5). Labels: the Step 1b dry-run "
             "labels. Cell = clusters kept / labels. **Bold** = the frozen default (k 40, threshold 0.3).", ""]
    for s in SETS:
        p = OUT / s / "grid.csv"
        if not p.exists():
            lines += [f"## {s}", "", "not run", ""]
            continue
        g = pd.read_csv(p, keep_default_na=False)
        g["keep"] = g["keep"].astype(str) == "True"
        n_lab = g["id"].nunique()
        lines += [f"## {s} ({n_lab} labels)", "", "| threshold \\ k | " + " | ".join(map(str, KS)) + " |", "|---|" + "---|" * len(KS)]
        for t in THRESHOLDS:
            cells = []
            for k in KS:
                kept = int(g[(g.k == k) & (g.threshold == t)]["keep"].sum())
                cells.append(f"**{kept}/{n_lab}**" if (k, t) == (40, 0.3) else f"{kept}/{n_lab}")
            lines.append(f"| {t} | " + " | ".join(cells) + " |")
        lines += ["", "Which clusters are kept (K = kept) and support at the default threshold 0.3:", "",
                  "| cluster | label | " + " | ".join(f"k{k}/t{t}" for t in THRESHOLDS for k in KS) +
                  " | support k40 | support all turns | entity turns |", "|---|---|" + "---|" * (len(KS) * len(THRESHOLDS) + 3)]
        for cid, gg in g.groupby("id", sort=False):
            marks = [("K" if bool(gg[(gg.k == k) & (gg.threshold == t)]["keep"].iloc[0]) else "-") for t in THRESHOLDS for k in KS]
            d = gg[(gg.k == 40) & (gg.threshold == 0.3)].iloc[0]
            lines.append(f"| {cid} | {d['label']} | " + " | ".join(marks) +
                         f" | {float(d['support']):.3f} | {float(d['support_all_turns']):.3f} | {d['n_entity_turns']} |")
        lines.append("")
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", choices=list(SETS))
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.set:
        run(a.set)
    if a.report:
        report()


if __name__ == "__main__":
    main()
