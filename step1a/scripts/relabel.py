"""What do value clusters capture? Score the same clusterings against three gold labels:
attribute ("Train day"), entity ("Train") and slot ("day", entity removed).

python scripts/relabel.py --limit 50   -> results/n50/relabel.md (embeddings come from the cache)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import VARIANTS, build_units, encoder  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import units as U  # noqa: E402
from hbe.metrics import external  # noqa: E402

SEEDS = (42, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()
    docs, sets, _ = build_units(args.limit)
    enc = encoder()
    us = sets["value"]
    golds = {"attribute": [u.label for u in us],
             "entity": [u.label.split()[0] for u in us],
             "slot": [u.label.split(" ", 1)[1] for u in us]}
    ks = {g: len(set(v)) for g, v in golds.items()}
    lines = ["# Value clusters scored against attribute, entity and slot", "",
             f"{len(us)} value units. Gold classes: " + ", ".join(f"{g} {k}" for g, k in ks.items()), "",
             "k-means on raw bge-m3 vectors, k = number of classes of the target label, mean B-cubed F1 "
             "(NMI) over 3 seeds. Each row's clustering is scored against all three labels.", "",
             "| Variant | k (target) | vs attribute | vs entity | vs slot |", "|---|---|---|---|---|"]
    for variant in VARIANTS:
        x = enc.encode([U.value_text(docs[u.doc_id], u, variant) for u in us])
        for target in ("entity", "slot", "attribute"):
            k = ks[target]
            scores = {g: [] for g in golds}
            for s in SEEDS:
                lab = KMeans(k, n_init=10, random_state=s).fit_predict(x)
                for g, gold in golds.items():
                    m = external(gold, lab)
                    scores[g].append((m["bcubed_f1"], m["nmi"]))
            cell = {g: f"{np.mean([a for a, _ in v]):.3f} ({np.mean([b for _, b in v]):.2f})"
                    for g, v in scores.items()}
            lines.append(f"| {variant} | {k} ({target}) | {cell['attribute']} | {cell['entity']} | {cell['slot']} |")
    lines += two_stage(docs, sets, enc, golds)
    enc.save()
    out = paths.RESULTS / f"n{args.limit}" / "relabel.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


THRESHOLDS = (0.3, 0.4, 0.5)


def entity_groups(us, segs, enc, k=5):
    """Stage 1 per seed: k-means on segment vectors; each unit takes its segment's cluster
    (-1 when no segment holds it)."""
    xc = enc.encode([c.text for c in segs])
    out = {}
    for s in SEEDS:
        clab = KMeans(k, n_init=10, random_state=s).fit_predict(xc)
        g = []
        for u in us:
            ci = next((i for i, c in enumerate(segs)
                       if c.doc_id == u.doc_id and c.start <= u.start < c.end), None)
            g.append(int(clab[ci]) if ci is not None else -1)
        out[s] = g
    return out


def stage2(xv, groups, t):
    """Stage 2: agglomerative (cosine, average, distance threshold t) inside each group."""
    lab = np.empty(len(groups), dtype=object)
    for g in set(groups):
        idx = [i for i, x in enumerate(groups) if x == g]
        if len(idx) == 1:
            sub = [0]
        else:
            sub = AgglomerativeClustering(n_clusters=None, distance_threshold=t,
                                          metric="cosine", linkage="average").fit_predict(xv[idx])
        for i, c in zip(idx, sub):
            lab[i] = f"{g}:{c}"
    return list(lab)


def two_stage(docs, sets, enc, golds):
    """Entity first (from the segment holding the value), then value strings clustered inside
    each entity group (agglomerative, cosine, average linkage, distance threshold: no gold k)."""
    us = sets["value"]
    xv = enc.encode([u.text for u in us])
    groupings = {"oracle entity (gold)": {0: golds["entity"]},
                 "Chroma chunk cluster (k-means k=5)": entity_groups(us, sets["chroma"], enc)}
    lines = ["", "## Two-stage: entity group first, then value strings inside each group", "",
             "Mean over 3 k-means seeds for the Chroma grouping. No gold k is used in stage 2.", "",
             "| Stage 1 | Stage 2 threshold | K | vs attribute F1 (NMI) | vs entity F1 | vs slot F1 |",
             "|---|---|---|---|---|---|"]
    for name, by_seed in groupings.items():
        for t in THRESHOLDS:
            res = []
            for groups in by_seed.values():
                lab = stage2(xv, groups, t)
                m ={gname: external(gold, lab) for gname, gold in golds.items()}
                res.append((len(set(lab)), m))
            K = np.mean([r[0] for r in res])
            f = {g: np.mean([r[1][g]["bcubed_f1"] for r in res]) for g in golds}
            nmi = np.mean([r[1]["attribute"]["nmi"] for r in res])
            lines.append(f"| {name} | {t} | {K:.0f} | {f['attribute']:.3f} ({nmi:.2f}) | "
                         f"{f['entity']:.3f} | {f['slot']:.3f} |")
    return lines


if __name__ == "__main__":
    main()
