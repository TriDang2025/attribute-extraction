"""wf_v4.1 loop 2: named probe + evidence check (logic in s1a/loop2_v41.py).

python scripts/loop2_v41.py --set dev50 --labels results/wf_v41/loop2/labels_placeholder_dev50.json [--k 40 --threshold 0.3]
  -> results/wf_v41/loop2/<set>/{clusters.json, evidence.csv, summary.md, run_info.json}
Run in the chunking venv (gliner + sentence-transformers). Uses the bge-m3 cache of data/cache: one writer at a time.
Thresholds: config/wf_v41_loop2.json (flags --k / --threshold override k and threshold).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import loop2_v41 as L2  # noqa: E402
from s1a import paths, split  # noqa: E402
from s1a import spans as SP  # noqa: E402
from chk.data import single_docs  # noqa: E402

CONFIG = paths.ROOT / "config" / "wf_v41_loop2.json"
SETS = {"dev50": ("dev", 50), "dev50b": ("dev50b", 50)}


class GlinerPredictor:
    """`predict(texts, label, threshold)` on a loaded GLiNER model."""

    def __init__(self, model):
        self.model = model

    def __call__(self, texts, label, threshold):
        return self.model.inference(texts, [label], threshold=threshold, batch_size=8)


def load_handover(set_name, entity):
    p = paths.ROOT / "handover" / set_name / f"{entity}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def run(set_name, labels, cfg, encoder, predict):
    """All clusters of one set; returns (clusters, notes)."""
    name, limit = SETS[set_name]
    docs = {d.doc_id: d for d in single_docs(split.dialogues(name, limit))}
    run_dir = paths.RESULTS / f"graph_v22_{set_name}" / "spans"
    mt = pd.read_csv(run_dir / "mentions.csv", keep_default_na=False)
    inst = pd.read_csv(run_dir / "instances.csv", keep_default_na=False)
    items = L2.turn_items(docs)
    item_vecs = encoder.encode([it["text"] for it in items])
    next_id, nums, clusters, notes = int(mt["mention_id"].max()) + 1, {}, [], []
    for lab in labels:
        ho = load_handover(set_name, lab["entity"])
        if ho is None:
            notes.append(f"no handover for {lab['entity']}: all turns searched, no columns checked")
        n = nums.get(lab["entity"], 0)
        nums[lab["entity"]] = n + 1
        c = L2.run_label(lab, n, docs, items, item_vecs, encoder, predict, mt, inst,
                         ho["columns"] if ho else [], ho["stage1_entity"] if ho else None, next_id, cfg)
        next_id += c["n_mentions"]
        clusters.append(c)
        print(f"{c['id']} {c['label']}: {c['n_mentions']} spans, keep={c['keep']} ({c['reason']})", flush=True)
    return clusters, sorted(set(notes)), len(docs), len(items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="dev50", choices=list(SETS))
    ap.add_argument("--labels", required=True)
    ap.add_argument("--k", type=int)
    ap.add_argument("--threshold", type=float)
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg |= {k: v for k, v in (("k", args.k), ("threshold", args.threshold)) if v is not None}
    from run import encoder as make_encoder
    enc = make_encoder()
    probe(args.set, Path(args.labels), cfg, enc, GlinerPredictor(SP.load()), paths.RESULTS / "wf_v41" / "loop2" / args.set)
    enc.save()


def probe(set_name, labels_path, cfg, enc, predict, out):
    """Run loop 2 on one set and write <out>/{clusters.json, evidence.csv, summary.md, run_info.json}; returns the clusters."""
    labels = L2.check_labels(json.loads(Path(labels_path).read_text(encoding="utf-8")))
    t0 = time.time()
    clusters, notes, n_docs, n_items = run(set_name, labels, cfg, enc, predict)
    secs = time.time() - t0
    out.mkdir(parents=True, exist_ok=True)
    (out / "clusters.json").write_text(json.dumps(clusters, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    pd.DataFrame(L2.evidence_rows(clusters)).to_csv(out / "evidence.csv", index=False, encoding="utf-8", lineterminator="\n")
    (out / "summary.md").write_text(L2.summary_md(clusters, set_name, cfg, Path(labels_path).as_posix(), secs), encoding="utf-8", newline="\n")
    per_entity = {e: dict(kept=sum(c["keep"] for c in clusters if c["entity"] == e),
                          dropped=sum(not c["keep"] for c in clusters if c["entity"] == e))
                  for e in dict.fromkeys(c["entity"] for c in clusters)}
    info = dict(set=set_name, seconds=round(secs, 1), config=cfg, labels_file=Path(labels_path).as_posix(), n_labels=len(labels),
                n_dialogues=n_docs, n_turn_items=n_items, counts=per_entity, notes=notes,
                gliner_model=str(SP.MODEL))
    (out / "run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8", newline="\n")
    print(f"done in {secs:.0f}s -> {out}")
    return clusters


if __name__ == "__main__":
    main()
