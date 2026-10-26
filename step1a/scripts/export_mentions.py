"""Task 0: export the frozen pipeline's mentions, clusters, instances and vectors (GRAPH_CONTRACT.md).

python scripts/export_mentions.py --split dev --limit 50 --input both --out results/graph_dev50 [--seed 42]
  -> <out>/{docs.jsonl, gold_values.csv, gold_attrs.txt} and <out>/<spans|gold>/{mentions,clusters,instances}.csv, vectors.npz
Caches (resumable) go to <out>/cache; the dev caches of the n50 runs seed them. Encodes with bge-m3: run alone.
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import entity_seg as ES  # noqa: E402
import gliner_labels as GL  # noqa: E402
import plug_in as PI  # noqa: E402
from run import encoder  # noqa: E402
from s1a import gold, paths  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import spans as SP  # noqa: E402
from s1a import split as SPL  # noqa: E402
from s1a import units as U  # noqa: E402
from chk.data import single_docs  # noqa: E402

SEED_FILES = (  # (file to seed from, name in the run cache)
    (paths.RESULTS / "n50" / "entity_seg" / "chunks_5_25.jsonl", "chunks_5_25.jsonl"),
    (paths.RESULTS / "v3_n50" / "gliner_labels" / "gliner_turn_generic.jsonl", "gliner_labels/gliner_turn_generic.jsonl"),
    (paths.RESULTS / "v3_n50" / "gliner_labels" / "gliner_turn_generic.meta.json", "gliner_labels/gliner_turn_generic.meta.json"))


def seed_cache(cache):
    for src, name in SEED_FILES:
        dst = cache / name
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def span_inputs(docs, enc, cache):
    """GLiNER spans (generic labels, threshold 0.5, once per turn) and 5/25 snapped merged segments."""
    gdir = cache / "gliner_labels"
    missing = [d for d in docs if d not in GL.read_cache(gdir / "gliner_turn_generic.jsonl")]
    model = SP.load() if missing else None
    have, _ = GL.extract_set(model, docs, "generic", gdir)
    spans = GL.to_units(have, docs, 0.5)
    size, tau, snap, kw = PI.parse_seg(PI.DEFAULT_SEG)
    ES.load_chunks(cache, docs, enc, size)
    return spans, PI.segments(docs, enc, size, tau, snap, kw, cache)


def prepare(split, limit, out, with_spans=True):
    """Docs, pipeline Inputs and the encoder of one split; writes the shared files of <out>."""
    t0 = time.time()
    docs = {d.doc_id: d for d in single_docs(SPL.dialogues(split, limit))}
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    docs = {d: v for d, v in docs.items() if d in tables}
    classes = gold.merge_classes(gold.load_all_tables())
    mentions = gold.mentions_for(docs, tables, classes=classes)
    MN.save_shared(out, docs, mentions, classes)
    print(f"{len(docs)} docs, {len(mentions)} gold mentions ({sum(m.verbatim for m in mentions)} verbatim), "
          f"{len(set(classes.values()))} classes", flush=True)
    enc = encoder()
    cache = out / "cache"
    seed_cache(cache)
    inp = MN.Inputs(mentions=mentions, tables=tables)
    if with_spans:
        inp.spans, inp.segs = span_inputs(docs, enc, cache)
        print(f"{len(inp.spans)} spans, {len(inp.segs)} segments, {time.time() - t0:.0f}s", flush=True)
    return docs, inp, enc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("dev", "test"), default="dev")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--input", choices=("spans", "gold", "both"), default="both")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--variant", help="v2.1 spans variant from s1a/combos.py (span filter + cluster_fn)")
    ap.add_argument("--from-run", help="run dir whose cache/ seeds this one (e.g. results/graph_dev50)")
    args = ap.parse_args()
    out = Path(args.out)
    out = out if out.is_absolute() else paths.ROOT / out
    t0 = time.time()
    inputs = ("spans", "gold") if args.input == "both" else (args.input,)
    if args.from_run and not (out / "cache").exists():
        shutil.copytree(paths.ROOT / args.from_run / "cache", out / "cache")
    docs, inp, enc = prepare(args.split, args.limit, out, "spans" in inputs)
    if args.variant:
        from s1a.combos import CONFIGS
        v = CONFIGS[args.variant]
        inp.spans = v.span_filter(inp.spans) if v.span_filter else inp.spans
        inp.cluster_fn = v.cluster_fn
        print(f"variant {args.variant}: {v.note}; {len(inp.spans)} spans", flush=True)
    for name in inputs:
        t1 = time.time()
        e = MN.build(name, docs, enc, args.seed, inp=inp)
        MN.save(e, out / name)
        print(f"{name}: {len(e.mentions)} mentions, {len(e.clusters)} clusters, {len(e.instances)} instances, "
              f"x {e.x.shape}, {time.time() - t1:.0f}s -> {out / name}", flush=True)
    enc.save()
    print(f"done in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
