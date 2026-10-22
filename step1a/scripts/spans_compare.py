"""GLiNER vs spaCy label-free spans, scored with the v2 protocol (Part 4 of Step 1a).

python scripts/spans_compare.py --export-texts --limit 50 --out results/v2_n50   (writes texts.jsonl)
  spaCy venv: python scripts/spacy_extract.py --texts results/v2_n50/texts.jsonl --out results/v2_n50/spacy_spans.jsonl
python scripts/spans_compare.py --limit 50 --out results/v2_n50
  -> spans_compare.{md,csv}, spans_compare_examples.md. GLiNER spans come from the cache, never run.
Extractors: GLiNER 0.3 / 0.5, spaCy (overlaps resolved, longest wins), union(GLiNER 0.5, spaCy).
Two-stage clustering (P4) is `cluster_eval`; pass stage2_fn to swap in another Step 2.
"""

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from relabel import entity_groups, stage2  # noqa: E402
from run import build_units, encoder  # noqa: E402
from s1a import gold, paths  # noqa: E402
from s1a import segment as S  # noqa: E402
from s1a import spacy_spans as SS  # noqa: E402
from s1a import units as U  # noqa: E402
from hbe.metrics import external  # noqa: E402

try:  # Part 1 scoring; a local fallback keeps this script usable until it exists
    from s1a import metrics as M
    match_all = M.match_all
except (ImportError, AttributeError):
    M = None
    match_all = None

GLINER_KEY = "25_100_m45"
GL_THRESHOLDS = (0.3, 0.5)
SEG_SIZE, SEG_TAU, STAGE2_T = (25, 100), 0.45, 0.4
LEVELS = (1, 2, 3)
GROUPS = {"food": ("food",), "type": ("type",), "area": ("area",), "price range": ("price",),
          "numbers (people/stay/stars)": ("people", "stay", "star")}


def _match_fallback(spans, mentions):
    """Local stand-in for metrics.match_all: a span takes the labels of its best-overlapping
    verbatim mention; returns the indices of mentions overlapped by some span."""
    by_doc = defaultdict(list)
    for i, m in enumerate(mentions):
        if m.verbatim:
            by_doc[m.doc_id].append((i, m))
    hit = set()
    for u in spans:
        u.labels, u.label, u.hidden = frozenset(), "", {}
        best, ov = None, 0
        for i, m in by_doc[u.doc_id]:
            o = min(u.end, m.end) - max(u.start, m.start)
            if o > 0:
                hit.add(i)
                if o > ov:
                    best, ov = m, o
        if best is not None:
            u.labels, u.label, u.hidden = best.labels, sorted(best.labels)[0], best.hidden
    return hit


def cover(spans, mentions):
    """Match spans to mentions (sets span.labels / label); returns matched mention indices."""
    for u in spans:
        u.labels = frozenset()
    return set((match_all or _match_fallback)(spans, mentions))


# ------------------------------------------------------------------ span sets
def gliner_units(path, docs, thr):
    out = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        doc = docs.get(r["doc_id"])
        for s, e, tag, score in (r["spans"] if doc else []):
            if score >= thr:
                u = U.Unit("span", r["doc_id"], "", doc.text[s:e], s, e, U.turn_of(doc, s))
                u.tag, u.score = "gliner", float(score)
                out.append(u)
    return out


def to_units(docs, by_doc):
    """{doc_id: [[s, e, source, ...]]} -> Units (tag = source)."""
    out = []
    for did, doc in docs.items():
        for s, e, src, *_ in by_doc.get(did, []):
            u = U.Unit("span", did, "", doc.text[s:e], s, e, U.turn_of(doc, s))
            u.tag, u.score = src, 1.0
            out.append(u)
    return out


def build_extractors(docs, gl_path, spacy_path):
    """name -> Units, plus the raw spaCy units (every candidate, overlaps kept)."""
    gl = {t: gliner_units(gl_path, docs, t) for t in GL_THRESHOLDS}
    raw = SS.load_raw(spacy_path)
    raw_sp = {d: [[s, e, f"spacy:{src}", lab] for s, e, src, lab in sp] for d, sp in raw.items()}
    uni = {}
    for did in docs:
        g = [[u.start, u.end, "gliner", u.score] for u in gl[0.5] if u.doc_id == did]
        uni[did] = SS.union(g, raw_sp.get(did, []))
    ex = {f"GLiNER {t}": gl[t] for t in GL_THRESHOLDS}
    ex["spaCy"] = to_units(docs, {d: SS.union(sp, []) for d, sp in raw_sp.items()})
    ex["union(GLiNER 0.5, spaCy)"] = to_units(docs, uni)
    return ex, to_units(docs, raw_sp)


# ------------------------------------------------------------------ P1 / P2 / P3
def value_keys(mentions):
    """(doc, value) -> indices of its verbatim mentions."""
    out = defaultdict(list)
    for i, m in enumerate(mentions):
        if m.verbatim:
            out[(m.doc_id, m.value)].append(i)
    return out


def recall_stats(matched, mentions, vkeys):
    ver = [i for i, m in enumerate(mentions) if m.verbatim]
    r = dict(mention_recall=len([i for i in ver if i in matched]) / max(1, len(ver)),
             value_recall=sum(any(i in matched for i in ix) for ix in vkeys.values()) / max(1, len(vkeys)),
             n_mentions=len(ver), n_values=len(vkeys))
    for k in LEVELS:
        for hid in (False, True):
            sub = [i for i in ver if bool(mentions[i].hidden.get(k)) == hid]
            r[f"L{k}_{'hidden' if hid else 'visible'}"] = (
                len([i for i in sub if i in matched]) / len(sub) if sub else float("nan"))
    return r


def per_class(matched, mentions, vkeys):
    """label -> (n values, value recall); a value counts for each label of its first mention."""
    acc = defaultdict(lambda: [0, 0])
    for ix in vkeys.values():
        hit = any(i in matched for i in ix)
        for lab in mentions[ix[0]].labels:
            acc[lab][0] += 1
            acc[lab][1] += hit
    return {lab: (n, h / n) for lab, (n, h) in acc.items()}


def per_doc(matched, mentions):
    acc = defaultdict(lambda: [0, 0])
    for i, m in enumerate(mentions):
        if m.verbatim:
            acc[m.doc_id][0] += 1
            acc[m.doc_id][1] += i in matched
    return {d: (n, h / n) for d, (n, h) in acc.items()}


def groups_of(labels):
    slots = [lab.split(" ", 1)[-1].lower() for lab in labels]
    return [g for g, keys in GROUPS.items() if any(k in s for s in slots for k in keys)]


# ------------------------------------------------------------------ P4
def segments(docs, enc):
    """25/100 + merge 0.45 segments of every doc, as Units."""
    src = paths.RESULTS / "n50" / "entity_seg" / f"chunks_{SEG_SIZE[0]}_{SEG_SIZE[1]}.jsonl"
    have = {}
    for line in open(src, encoding="utf-8"):
        r = json.loads(line)
        have[r["doc_id"]] = r["chunks"]
    segs = []
    for did, doc in docs.items():
        sp = S.merge_adjacent(doc.text, S.piece_spans(doc, have[did]), enc, SEG_TAU)
        segs += U.chroma_units(doc, S.as_chunks(doc, sp))
    return segs


def cluster_eval(spans, enc, segs, value_recall, stage2_fn=None, t=STAGE2_T):
    """Two-stage clustering of matched spans (span.labels / span.label set by cover).
    stage2_fn(xs, groups, t) -> cluster labels, default relabel.stage2. Returns attribute
    P/R/F1 (lenient B-cubed on matched spans, metrics.report_block), K, share of clusters with no gold span, end-to-end
    (value_recall x F1; mean over 3 seeds) and the largest non-gold clusters (seed 42)."""
    stage2_fn = stage2_fn or stage2
    xs = enc.encode([u.text for u in spans])
    scored = [i for i, u in enumerate(spans) if u.labels]
    gold_lab = [spans[i].label or sorted(spans[i].labels)[0] for i in scored]
    res, lab0 = [], None
    for g in entity_groups(spans, segs, enc).values():
        lab = stage2_fn(xs, g, t)
        lab0 = lab if lab0 is None else lab0
        if M is not None:  # lenient multi-label B-cubed (Part 1)
            a = M.report_block(spans, lab, levels=())["all"]
            m = dict(bcubed_precision=a["p"], bcubed_recall=a["r"], bcubed_f1=a["f"])
        else:
            m = external(gold_lab, [lab[i] for i in scored])
        has_gold = defaultdict(bool)
        for i, c in enumerate(lab):
            has_gold[c] |= bool(spans[i].labels)
        res.append((m, len(has_gold), sum(not v for v in has_gold.values()) / max(1, len(has_gold))))
    mean = lambda f: float(np.mean([f(r) for r in res]))  # noqa: E731
    f1 = mean(lambda r: r[0]["bcubed_f1"])
    clusters = defaultdict(list)
    for i, c in enumerate(lab0):
        clusters[c].append(i)
    nongold = sorted((ix for ix in clusters.values() if not any(spans[i].labels for i in ix)),
                     key=len, reverse=True)[:10]
    return dict(P=mean(lambda r: r[0]["bcubed_precision"]), R=mean(lambda r: r[0]["bcubed_recall"]),
                F1=f1, K=mean(lambda r: r[1]), nongold_pct=100 * mean(lambda r: r[2]),
                end_to_end=value_recall * f1, labels=lab0,
                top_nongold=[(len(ix), Counter(spans[i].text.lower() for i in ix).most_common(8))
                             for ix in nongold])


# ------------------------------------------------------------------ main
def export_texts(docs, out):
    with open(out / "texts.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for did, doc in docs.items():
            f.write(json.dumps({"doc_id": did, "text": doc.text,
                                "turns": [list(t) for t in doc.spans]}) + "\n")
    print(f"wrote {out / 'texts.jsonl'} ({len(docs)} docs)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", required=True)
    ap.add_argument("--export-texts", action="store_true")
    ap.add_argument("--gliner", help="GLiNER span cache (default results/n50/entity_seg/gliner_25_100_m45.jsonl)")
    ap.add_argument("--spacy", help="spaCy spans jsonl (default <out>/spacy_spans.jsonl)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    docs, _sets, _ = build_units(args.limit)
    if args.export_texts:
        return export_texts(docs, out)
    gl_path = Path(args.gliner) if args.gliner else paths.RESULTS / "n50" / "entity_seg" / f"gliner_{GLINER_KEY}.jsonl"
    spacy_path = Path(args.spacy) if args.spacy else out / "spacy_spans.jsonl"
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    docs_t = {d: v for d, v in docs.items() if d in tables}
    mentions = gold.mentions_for(docs_t, tables)
    vkeys = value_keys(mentions)
    ex, raw_units = build_extractors(docs_t, gl_path, spacy_path)
    n_docs = len(docs_t)
    print(f"{len(mentions)} mentions, {len(vkeys)} verbatim values, scoring path: "
          f"{'s1a.metrics' if match_all else 'local fallback'}", flush=True)

    def finish(name, us, matched):
        r = recall_stats(matched, mentions, vkeys)
        r["tight_recall"] = M.span_recall(us, mentions)["tight_mention"] if M is not None else float("nan")
        return r | dict(extractor=name, n_spans=len(us), spans_per_dlg=len(us) / n_docs,
                        span_precision=sum(bool(u.labels) for u in us) / max(1, len(us)))

    stats, matched_of = {}, {}
    for name, us in ex.items():
        matched_of[name] = cover(us, mentions)
        stats[name] = finish(name, us, matched_of[name])
    src_matched = {}  # raw spaCy candidates by source (overlaps kept)
    for src in ("ner", "np", "num"):
        us = [u for u in raw_units if u.tag == f"spacy:{src}"]
        src_matched[src] = cover(us, mentions)
        stats[f"spaCy raw {src}"] = finish(f"spaCy raw {src}", us, src_matched[src])
    enc = encoder()
    segs = segments(docs_t, enc)
    cl = {}
    for name, us in ex.items():
        cover(us, mentions)  # cover() above reset labels of the shared lists; set them again
        cl[name] = cluster_eval(us, enc, segs, stats[name]["value_recall"])
        print(f"{name}: attr F1 {cl[name]['F1']:.3f} K {cl[name]['K']:.0f} "
              f"{time.time() - t0:.0f}s", flush=True)
    enc.save()
    write_outputs(out, docs_t, mentions, vkeys, ex, stats, matched_of, src_matched, cl, time.time() - t0)
    print(f"done in {time.time() - t0:.0f}s -> {out / 'spans_compare.md'}")


def _p(x, d=3):
    return "-" if x != x else f"{x:.{d}f}"


def write_outputs(out, docs, mentions, vkeys, ex, stats, matched_of, src_matched, cl, secs):
    names = list(ex)
    raw_names = [f"spaCy raw {s}" for s in ("ner", "np", "num")]
    L = [f"# GLiNER vs spaCy spans ({len(docs)} dialogues)", "",
         f"Gold: {len(vkeys)} verbatim values, {sum(m.verbatim for m in mentions)} verbatim mentions "
         "(non-verbatim ones are left out of recall). A span matches a mention when their char spans "
         "overlap. spaCy = ner + noun chunks + numbers, overlaps resolved longest-first; "
         f"GLiNER from cache {GLINER_KEY}. Run {secs / 60:.1f} min.", "",
         "## P1/P2 Span finding", "",
         "| Extractor | Spans/dlg | Span precision | Mention recall | Tight mention recall | Value recall | "
         + " | ".join(f"L{k} vis / hid" for k in LEVELS) + " |", "|---|---|---|---|---|---|---|---|---|"]
    for n in names + raw_names:
        r = stats[n]
        L.append(f"| {n} | {r['spans_per_dlg']:.1f} | {_p(r['span_precision'])} | {_p(r['mention_recall'])} | "
                 f"{_p(r['tight_recall'])} | {_p(r['value_recall'])} | " + " | ".join(
                     f"{_p(r[f'L{k}_visible'], 2)} / {_p(r[f'L{k}_hidden'], 2)}" for k in LEVELS) + " |")
    L += ["", "Value recall by class (n = verbatim values):", ""]
    pc = {n: per_class(matched_of[n], mentions, vkeys) for n in names}
    classes = sorted(pc[names[0]], key=lambda c: -pc[names[0]][c][0])
    L += ["| Class | n | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for c in classes:
        L.append(f"| {c} | {pc[names[0]][c][0]} | "
                 + " | ".join(_p(pc[n].get(c, (0, float("nan")))[1], 2) for n in names) + " |")
    L += ["", "Worst 10 dialogues by mention recall:", ""]
    for n in names:
        worst = sorted(per_doc(matched_of[n], mentions).items(), key=lambda kv: kv[1][1])[:10]
        L.append(f"- {n}: " + ", ".join(f"{d} {r:.2f} (n={k})" for d, (k, r) in worst))

    # P3
    L += ["", "## P3 Values GLiNER 0.5 missed", ""]
    g5 = matched_of["GLiNER 0.5"]
    missed = {k: ix for k, ix in vkeys.items() if not any(i in g5 for i in ix)}
    cov = {"spaCy": matched_of["spaCy"], "ner": src_matched["ner"], "np": src_matched["np"],
           "num": src_matched["num"], "union": matched_of["union(GLiNER 0.5, spaCy)"]}

    def hit(ix, s):
        return any(i in cov[s] for i in ix)

    L += [f"{len(missed)} of {len(vkeys)} values missed by GLiNER 0.5; share now covered by "
          "spaCy overall, by raw spaCy source, and by the union:", "",
          "| Group | Missed (of n) | spaCy | ner | np | num | union |", "|---|---|---|---|---|---|---|"]
    csv_rows = []

    def prow(label, keys, total):
        n = len(keys)
        sh = {s: sum(hit(vkeys[k], s) for k in keys) / n if n else float("nan") for s in cov}
        L.append(f"| {label} | {n} (of {total}) | " + " | ".join(_p(sh[s], 2) for s in cov) + " |")
        csv_rows.append(dict(section="p3_missed", extractor=label, key=label, n=n,
                             **{f"cov_{s}": sh[s] for s in cov}))

    prow("all classes", list(missed), len(vkeys))
    for g in GROUPS:
        allg = [k for k, ix in vkeys.items() if g in groups_of(mentions[ix[0]].labels)]
        prow(g, [k for k in allg if k in missed], len(allg))
    L += ["", "By class:", "",
          "| Class | Missed (of n) | spaCy | ner | np | num | union |", "|---|---|---|---|---|---|---|"]
    for c in classes:
        allc = [k for k, ix in vkeys.items() if c in mentions[ix[0]].labels]
        prow(c, [k for k in allc if k in missed], len(allc))

    # P4
    L += ["", "## P4 Two-stage clustering on each extractor's spans", "",
          f"Segments {SEG_SIZE[0]}/{SEG_SIZE[1]} + merge {SEG_TAU}; stage 1 k-means k=5 (3 seeds); stage 2 "
          f"agglomerative t={STAGE2_T} on bge-m3 of span text. All spans are clustered, matched spans are "
          "scored (B-cubed vs class). End-to-end = value recall x attribute F1.", "",
          "| Extractor | Attr P | Attr R | Attr F1 | K | Non-gold clusters % | Value recall | End-to-end |",
          "|---|---|---|---|---|---|---|---|"]
    for n in names:
        c = cl[n]
        L.append(f"| {n} | {_p(c['P'])} | {_p(c['R'])} | {_p(c['F1'])} | {c['K']:.0f} | "
                 f"{c['nongold_pct']:.0f} | {_p(stats[n]['value_recall'])} | {_p(c['end_to_end'])} |")
    if M is not None and hasattr(M, "report_block"):
        L += ["", "metrics.report_block per extractor:", ""]
        for n in names:
            try:
                L += [M.format_block(M.report_block(ex[n], cl[n]["labels"], levels=LEVELS), n), ""]
            except Exception as e:  # noqa: BLE001 - report, never crash the run
                L.append(f"- {n}: report_block failed ({type(e).__name__}: {e})")
    L += ["", "## P5", "", "FrameNet frame elements as a further span source (typed, schema-free) is later work."]
    (out / "spans_compare.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")

    fields = ["section", "extractor", "key", "n", "value"] + [f"cov_{s}" for s in cov]
    rows = []
    for n in names + raw_names:
        rows += [dict(section="overall", extractor=n, key=k, value=v)
                 for k, v in stats[n].items() if k != "extractor"]
    for n in names:
        rows += [dict(section="class_value_recall", extractor=n, key=c, n=k, value=v)
                 for c, (k, v) in pc[n].items()]
        rows += [dict(section="p4", extractor=n, key=k, value=cl[n][k]) for k in ("P", "R", "F1", "K", "nongold_pct", "end_to_end")]
    with open(out / "spans_compare.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows + csv_rows)

    E = ["# Span comparison examples", "", "## Largest clusters made only of non-gold spans", ""]
    for n in names:
        E += [f"### {n}", ""]
        for i, (size, top) in enumerate(cl[n]["top_nongold"], 1):
            E.append(f"{i}. size {size}: " + ", ".join(f"\"{t}\" x{k}" for t, k in top))
        E.append("")
    E += ["## Gold values still missed by the union", ""]
    for (d, v) in sorted(k for k in missed if not hit(vkeys[k], "union"))[:60]:
        E.append(f"- {d}: \"{v}\" ({', '.join(sorted(mentions[vkeys[(d, v)][0]].labels))})")
    (out / "spans_compare_examples.md").write_text("\n".join(E) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
