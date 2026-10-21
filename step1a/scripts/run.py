"""Step 1a experiment: cluster segments and gold values of the first N Conversation dialogues.

python scripts/run.py --limit 50     -> results/n50/{metrics.csv, summary.md, attribute_purity.csv, examples.md}
"""

import argparse
import csv
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import paths  # noqa: E402
from s1a import units as U  # noqa: E402
from s1a.cluster import n_clusters, runs, spaces  # noqa: E402

import chk.config as chk_config  # noqa: E402
from chk.data import load_dialogues, single_docs  # noqa: E402
from hbe.metrics import external  # noqa: E402

VARIANTS = ("value", "window", "turn")
KEYS = ("unit", "variant", "space", "umap_seed", "method", "setting", "seed", "n", "gold_k",
        "K", "noise_pct", "purity", "bcubed_precision", "bcubed_recall", "bcubed_f1", "ari", "nmi")


def encoder():
    # own cache, seeded once from the chunking cache (Chroma chunks are already embedded there)
    src = chk_config.CACHE / "bge-m3.pkl"
    chk_config.CACHE = paths.CACHE
    if not (paths.CACHE / "bge-m3.pkl").exists() and src.exists():
        paths.CACHE.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, paths.CACHE / "bge-m3.pkl")
    from chk.embed import Encoder
    return Encoder()


def build_units(limit):
    dialogues = load_dialogues(limit)
    docs = {d.doc_id: d for d in single_docs(dialogues)}
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    chunks = {}
    for line in open(paths.CHROMA_CHUNKS, encoding="utf-8"):
        r = json.loads(line)
        chunks[r["doc_id"]] = r["chunks"]
    sets = defaultdict(list)
    stats = Counter()
    for did, doc in docs.items():
        if did in chunks:
            sets["chroma"] += U.chroma_units(doc, chunks[did])
        else:
            stats["no_chroma_chunks"] += 1
        sets["oracle_seg"] += U.oracle_segments(doc)
        if did not in tables:
            stats["no_table"] += 1
            continue
        vals, miss = U.value_units(doc, tables[did])
        sets["value"] += vals
        stats["values_found"] += len(vals)
        stats["values_missing"] += miss
    return docs, sets, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()
    out = paths.RESULTS / f"n{args.limit}"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    docs, sets, stats = build_units(args.limit)
    print(dict(stats), {k: len(v) for k, v in sets.items()}, flush=True)
    enc = encoder()

    jobs = [("chroma", "segment", sets["chroma"], [u.text for u in sets["chroma"]]),
            ("oracle_seg", "segment", sets["oracle_seg"], [u.text for u in sets["oracle_seg"]])]
    for v in VARIANTS:
        jobs.append(("value", v, sets["value"], [U.value_text(docs[u.doc_id], u, v) for u in sets["value"]]))

    rows, best_labels = [], {}
    for unit, variant, us, texts in jobs:
        emb = enc.encode(texts)
        enc.save()
        gold = [u.label for u in us]
        gold_k = len(set(gold))
        for space, useed, x in spaces(emb):
            for method, setting, seed, lab in runs(x, space, gold_k):
                k, noise = n_clusters(lab)
                m = external(gold, lab)
                row = dict(unit=unit, variant=variant, space=space, umap_seed=useed, method=method,
                           setting=setting, seed=seed, n=len(us), gold_k=gold_k, K=k,
                           noise_pct=round(noise, 1), **{c: round(m[c], 4) for c in KEYS if c in m})
                rows.append(row)
                key = (unit, variant)
                if key not in best_labels or row["bcubed_f1"] > best_labels[key][0]["bcubed_f1"]:
                    best_labels[key] = (row, list(lab))
        print(f"{unit}/{variant}: {len(us)} units, {time.time() - t0:.0f}s", flush=True)

    with open(out / "metrics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KEYS)
        w.writeheader()
        w.writerows(rows)
    write_summary(out, rows, best_labels, stats, sets)
    write_examples(out, sets, best_labels, docs)
    write_attribute_purity(out, sets, best_labels)
    print(f"done in {time.time() - t0:.0f}s -> {out}")


def _mean_rows(rows):
    """Average over seeds (UMAP seed and k-means seed) for each configuration."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["unit"], r["variant"], r["space"], r["method"], r["setting"])].append(r)
    out = []
    for key, rs in groups.items():
        f1 = [r["bcubed_f1"] for r in rs]
        out.append(dict(unit=key[0], variant=key[1], space=key[2], method=key[3], setting=key[4],
                        runs=len(rs), gold_k=rs[0]["gold_k"],
                        K=sum(r["K"] for r in rs) / len(rs),
                        noise=sum(r["noise_pct"] for r in rs) / len(rs),
                        f1=sum(f1) / len(f1), f1_lo=min(f1), f1_hi=max(f1),
                        nmi=sum(r["nmi"] for r in rs) / len(rs),
                        ari=sum(r["ari"] for r in rs) / len(rs),
                        purity=sum(r["purity"] for r in rs) / len(rs)))
    return out


def _line(m):
    return (f"| {m['unit']} | {m['variant']} | {m['space']} | {m['method']} | {m['setting']} | "
            f"{m['K']:.0f} | {m['noise']:.0f} | {m['f1']:.3f} ({m['f1_lo']:.2f}–{m['f1_hi']:.2f}) | "
            f"{m['nmi']:.3f} | {m['ari']:.3f} | {m['purity']:.3f} |")


def write_summary(out, rows, best_labels, stats, sets):
    means = _mean_rows(rows)
    head = ("| Unit | Variant | Space | Method | Setting | K | Noise % | B-cubed F1 (range) | NMI | ARI | Purity |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|")
    lines = ["# Step 1a, results", "", f"Units: {dict((k, len(v)) for k, v in sets.items())}; {dict(stats)}", "",
             "## Best configuration per unit type and method (mean over seeds, by B-cubed F1)", "", head]
    for unit, variant in sorted({(m["unit"], m["variant"]) for m in means}):
        for method in ("hdbscan", "agglo", "kmeans"):
            cand = [m for m in means if m["unit"] == unit and m["variant"] == variant and m["method"] == method]
            if cand:
                lines.append(_line(max(cand, key=lambda m: m["f1"])))
    lines += ["", "## At the gold number of clusters (raw vectors)", "", head]
    for m in sorted(means, key=lambda m: (m["unit"], m["variant"], m["method"])):
        if m["space"] == "raw" and m["setting"] == f"k={m['gold_k']}":
            lines.append(_line(m))
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_examples(out, sets, best_labels, docs, per_cluster=8):
    lines = ["# Step 1a, cluster examples (best configuration by B-cubed F1)", ""]
    for (unit, variant), (row, lab) in sorted(best_labels.items()):
        us = sets[unit]
        lines += [f"## {unit} / {variant}: {row['space']} {row['method']} {row['setting']} "
                  f"(K {row['K']}, F1 {row['bcubed_f1']:.3f})", ""]
        groups = defaultdict(list)
        for u, c in zip(us, lab):
            groups[c].append(u)
        for c, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            gold = Counter(u.label for u in members)
            top = ", ".join(f"{g} {n}" for g, n in gold.most_common(3))
            name = "noise" if c == -1 else f"cluster {c}"
            lines.append(f"**{name}** ({len(members)} units; gold: {top})")
            for u in members[:per_cluster]:
                shown = (U.value_text(docs[u.doc_id], u, variant) if unit == "value"
                         else u.text.replace("\n", " ")[:160])
                lines.append(f"- `{u.label}`: {shown}")
            lines.append("")
    (out / "examples.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_attribute_purity(out, sets, best_labels):
    with open(out / "attribute_purity.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant", "attribute", "n", "main_cluster", "share_in_main", "main_cluster_size",
                    "others_in_main_cluster"])
        for variant in VARIANTS:
            if ("value", variant) not in best_labels:
                continue
            _, lab = best_labels[("value", variant)]
            us = sets["value"]
            by_attr, by_cluster = defaultdict(Counter), defaultdict(Counter)
            for u, c in zip(us, lab):
                by_attr[u.label][c] += 1
                by_cluster[c][u.label] += 1
            for attr, cs in sorted(by_attr.items()):
                c, n_main = cs.most_common(1)[0]
                n = sum(cs.values())
                others = "; ".join(f"{a} {k}" for a, k in by_cluster[c].most_common() if a != attr)
                w.writerow([variant, attr, n, c, round(n_main / n, 3), sum(by_cluster[c].values()), others])


if __name__ == "__main__":
    main()
