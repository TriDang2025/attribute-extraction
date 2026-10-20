"""Example showcase: real dialogues -> chunks of each method, side by side, plus the score tables.

  python scripts/make_showcase.py --out PATH.html
Reads results/S_n50 and results/T_seed{42,0,1}_n50 (the 5% runs).
"""

import argparse
import csv
import html
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chk import config, data, metrics  # noqa: E402

METHODS = ["rsc@bge-m3", "chroma@bge-m3", "chonkie@potion", "chonkie@bge-m3", "fixed", "texttiling"]
LABEL = {"rsc@bge-m3": "1. RSC (bge-m3)", "chroma@bge-m3": "2. Chroma cluster (bge-m3)",
         "chonkie@potion": "3a. Chonkie (potion, default)", "chonkie@bge-m3": "3b. Chonkie (bge-m3)",
         "fixed": "Baseline: fixed 400 tok", "texttiling": "Baseline: TextTiling"}
SEEDS = (42, 0, 1)
esc = html.escape


def load_chunks(run):
    out = {}
    for m in METHODS:
        f = run / "chunks" / f"{m.replace('@', '_')}.jsonl"
        out[m] = {json.loads(l)["doc_id"]: json.loads(l)["chunks"] for l in open(f, encoding="utf-8")}
    return out


def method_view(doc, chunks, t_from, t_to):
    """Per method: spans, gap set, and for each chunk the list of (turn, start, end) pieces in the window."""
    spans, _ = metrics.align(doc.text, chunks)
    gaps, inside = metrics.cuts_to_gaps(doc, spans)
    lo, hi = doc.spans[t_from][0], doc.spans[t_to - 1][1]
    boxes = []
    for ci, (s, e) in enumerate(spans):
        if e <= lo or s >= hi:
            continue
        pieces = []
        for t in range(t_from, t_to):
            ts, te = doc.spans[t]
            a, b = max(s, ts), min(e, te)
            if a < b:
                pieces.append((t, a, b, a > ts, b < te))  # cut-in-turn at start / end
        boxes.append((ci, s, e, pieces))
    return {"boxes": boxes, "gaps": gaps, "n": len(spans), "inside": inside}


def render_example(ex_id, title, note, doc, chunks_by_m, t_from=0, t_to=None):
    t_to = t_to or doc.n_turns
    gold = {g for g in doc.gold_gaps if t_from <= g < t_to - 1}
    views = {m: method_view(doc, chunks_by_m[m][doc.doc_id], t_from, t_to) for m in METHODS}
    # summary table
    rows = []
    for m in METHODS:
        v = views[m]
        g = {x for x in v["gaps"] if t_from <= x < t_to - 1}
        hit = len(g & gold)
        near = metrics.boundary_counts(gold, g, 1)[0]
        rows.append(f"<tr><td>{LABEL[m]}</td><td>{len([b for b in v['boxes']])}</td>"
                    f"<td>{hit}/{len(gold)}</td><td>{near}/{len(gold)}</td><td>{len(g - gold)}</td>"
                    f"<td>{sum(1 for b in v['boxes'] for p in b[3] if p[3])}</td></tr>")
    table = ("<div class='tw'><table class='mini'><tr><th>Method</th><th>Chunks shown</th><th>Topic switches cut exactly</th>"
             "<th>Within 1 turn</th><th>Extra cuts</th><th>Cuts inside a turn</th></tr>" + "".join(rows) + "</table></div>")
    # raw column
    raw = []
    for t in range(t_from, t_to):
        s, e = doc.spans[t]
        if t > t_from and doc.dialogue[t] != doc.dialogue[t - 1]:
            raw.append(f"<div class='sw dlg'>new dialogue {esc(doc.dialogue[t])} · topic: {doc.domains[t]}</div>")
        elif t > t_from and t - 1 in gold:
            raw.append(f"<div class='sw'>topic switch → {doc.domains[t]}</div>")
        raw.append(f"<div class='turn d-{doc.domains[t]}'><span class='tn'>{t}</span>{esc(doc.text[s:e])}</div>")
    cols = [f"<div class='col'><div class='ch'>Input + gold topics</div>{''.join(raw)}</div>"]
    for m in METHODS:
        v = views[m]
        out = []
        for bi, (ci, s, e, pieces) in enumerate(v["boxes"]):
            first_t = pieces[0][0] if pieces else None
            badge = ""
            if bi > 0 and first_t is not None:
                g = first_t - 1 if not pieces[0][3] else None
                if pieces[0][3]:
                    badge = "<span class='b mid'>cut inside turn</span>"
                elif g in gold:
                    badge = "<span class='b ok'>cut = topic switch</span>"
                else:
                    badge = "<span class='b extra'>extra cut</span>"
            body = []
            for t, a, b, cut_start, cut_end in pieces:
                if t > t_from and t - 1 in gold and not cut_start and a == doc.spans[t][0] and pieces[0][0] != t:
                    body.append("<div class='miss'>missed topic switch</div>")
                txt = esc(doc.text[a:b])
                pre = "<span class='scis'>✂</span>…" if cut_start else ""
                post = "…<span class='scis'>✂</span>" if cut_end else ""
                body.append(f"<div class='turn d-{doc.domains[t]}'><span class='tn'>{t}</span>{pre}{txt}{post}</div>")
            out.append(f"<div class='box c{bi % 2}'><div class='bh'>chunk {ci} · {e - s} chars {badge}</div>{''.join(body)}</div>")
        cols.append(f"<div class='col'><div class='ch'>{LABEL[m]}</div>{''.join(out)}</div>")
    return (f"<section id='{ex_id}'><h2>{esc(title)}</h2><p class='note'>{note}</p>{table}"
            f"<div class='grid'>{''.join(cols)}</div></section>")


def pick_examples(docs):
    by = {"single": [], "one": [], "multi": []}
    for d in docs:
        k = len(d.gold_gaps)
        key = "single" if k == 0 else "one" if k == 1 else "multi"
        by[key].append(d)
    mid = lambda L: sorted(L, key=lambda d: d.n_turns)[len(L) // 2]
    back = [d for d in by["multi"] if len(set(d.domains)) < len(d.gold_gaps) + 1]  # a topic comes back
    return [("ex1", "Example 1: one topic, no switch", mid(by["single"]),
             "The whole dialogue is one topic, so ideally a chunker keeps it together (or cuts only for size)."),
            ("ex2", "Example 2: one topic switch", mid(by["one"]), None),
            ("ex3", "Example 3: several switches", (back or by["multi"])[0], None)]


def score_tables(res):
    keys = [("chunks_per_doc", "Chunks / doc", 1), ("chars_mean", "Mean chars", 0),
            ("cuts_inside_turn_pct", "% cuts inside a turn", 0), ("Pk", "Pk ↓", 3),
            ("F1_tol1", "Boundary F1 (±1 turn) ↑", 3), ("coherence_gap", "Coherence gap ↑", 3),
            ("purity", "Topic purity ↑", 3), ("recall@1", "Retrieval R@1 ↑", 3),
            ("recall@5", "R@5 ↑", 3), ("char_precision@5", "Relevant text in top 5 ↑", 3),
            ("pct_outside_limit", "% over size limit", 1), ("sec_per_1k_tok", "Sec / 1k tokens (CPU)", 2)]
    out = []
    for name, rows in res.items():
        best = {}
        for k, _, _ in keys:
            vals = [rows[m][k] for m in METHODS if m in rows]
            if "↓" in dict((a, b) for a, b, _ in keys)[k]:
                best[k] = min(vals)
            elif "↑" in dict((a, b) for a, b, _ in keys)[k]:
                best[k] = max(vals)
        h = "<tr><th>Method</th>" + "".join(f"<th>{lab}</th>" for _, lab, _ in keys) + "</tr>"
        for m in METHODS:
            r = rows[m]
            h += f"<tr><td>{LABEL[m]}</td>" + "".join(
                f"<td class='{'best' if best.get(k) == r[k] else ''}'>{r[k]:.{d}f}</td>" for k, _, d in keys) + "</tr>"
        out.append(f"<h3>{name}</h3><div class='tw'><table class='sc'>{h}</table></div>")
    return "".join(out)


def read_metrics(run):
    return {r["method"]: {k: float(v) for k, v in r.items() if k != "method"}
            for r in csv.DictReader(open(run / "metrics.csv", encoding="utf-8"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = config.RESULTS
    dlg = data.load_dialogues(50)
    s_docs = data.single_docs(dlg)
    s_chunks = load_chunks(R / "S_n50")
    res = {"Single dialogues (50 documents)": read_metrics(R / "S_n50")}
    t_runs = [read_metrics(R / f"T_seed{s}_n50") for s in SEEDS]
    res["Stitched, 20 dialogues per document (mean of 3 seeds, 3 documents each)"] = {
        m: {k: float(np.mean([t[m][k] for t in t_runs])) for k in t_runs[0][m]} for m in METHODS}

    secs = []
    for ex_id, title, d, note in pick_examples(s_docs):
        doms = [d.domains[0]] + [d.domains[g + 1] for g in sorted(d.gold_gaps)]
        note = note or (f"Topics: {' → '.join(doms)}. Gold switches after turn(s) "
                        f"{', '.join(str(g) for g in sorted(d.gold_gaps))}.")
        secs.append(render_example(ex_id, f"{title} ({d.doc_id}, {d.n_turns} turns)", note, d, s_chunks))
    t_docs = data.stitched_docs(dlg, 42)
    t_chunks = load_chunks(R / "T_seed42_n50")
    td = t_docs[0]
    first3 = [g for g in range(td.n_turns - 1) if td.dialogue[g] != td.dialogue[g + 1]][2] + 1
    secs.append(render_example("ex4", f"Example 4: stitched document, first 3 dialogues (turns 0–{first3 - 1} of {td.n_turns})",
                               "Several dialogues joined with no separator; each new dialogue is also a gold boundary. "
                               "Only the chunks that overlap these turns are shown.", td, t_chunks, 0, first3))

    toc = "".join(f"<a href='#ex{i}'>Example {i}</a>" for i in range(1, 5))
    page = (TEMPLATE.replace("__TOC__", toc).replace("__SCORES__", score_tables(res))
            .replace("__EXAMPLES__", "".join(secs)).replace("__DIFFS__", diffs_html()))
    Path(a.out).write_text(page, encoding="utf-8")
    print(a.out, f"{Path(a.out).stat().st_size / 1e3:.0f} KB")


TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Chunking examples</title>
<style>
:root{--bg:#fbfaf7;--fg:#1f1e1c;--mut:#6d6b66;--line:#e2dfd8;--card:#fff;--ok:#15803d;--warn:#b45309;--bad:#b91c1c;--best:#e7f5ec;
--c0:#f6f4ee;--c1:#eef3f9;--train:#3b82f6;--hotel:#db2777;--restaurant:#d97706;--attraction:#16a34a;--taxi:#7c3aed;--hospital:#dc2626;--police:#4f46e5;--general:#64748b;--bus:#0891b2}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#151513;--fg:#ecebe6;--mut:#a09e98;--line:#34332f;--card:#1e1e1b;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--best:#1d3a28;--c0:#24231f;--c1:#1f2a35}}
:root[data-theme=dark]{--bg:#151513;--fg:#ecebe6;--mut:#a09e98;--line:#34332f;--card:#1e1e1b;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--best:#1d3a28;--c0:#24231f;--c1:#1f2a35}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.page{max-width:1600px;margin:0 auto;padding:20px 16px 60px}h1{font-size:24px;margin:0 0 6px}h2{font-size:19px;margin:34px 0 4px}h3{font-size:15px;margin:18px 0 6px}
.lead{color:var(--mut);max-width:900px}.toc a{margin-right:14px}a{color:var(--train)}
.tw{overflow-x:auto}table{border-collapse:collapse;font-size:13px;background:var(--card)}th,td{border:1px solid var(--line);padding:4px 8px;text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{font-weight:600;background:var(--c0)}td.best{background:var(--best);font-weight:600}
.mini{margin:8px 0 12px}.note{color:var(--mut);margin:2px 0}
.grid{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(250px,1fr);gap:10px;overflow-x:auto;padding-bottom:8px}
.col{min-width:250px}.ch{position:sticky;top:0;background:var(--bg);font-weight:600;font-size:13px;padding:4px 0;border-bottom:2px solid var(--line);margin-bottom:6px}
.turn{font-size:12.5px;line-height:1.4;padding:3px 6px 3px 8px;border-left:4px solid var(--general);margin:2px 0;background:var(--card)}
.tn{color:var(--mut);font-size:10.5px;margin-right:5px}
.d-train{border-color:var(--train)}.d-hotel{border-color:var(--hotel)}.d-restaurant{border-color:var(--restaurant)}.d-attraction{border-color:var(--attraction)}
.d-taxi{border-color:var(--taxi)}.d-hospital{border-color:var(--hospital)}.d-police{border-color:var(--police)}.d-bus{border-color:var(--bus)}
.sw{font-size:11.5px;color:var(--ok);font-weight:600;border-top:2px solid var(--ok);margin:6px 0 2px;padding-top:2px}.sw.dlg{border-top-style:double;border-top-width:4px}
.box{border:1px solid var(--line);border-radius:7px;padding:4px;margin:0 0 8px}.box.c0{background:var(--c0)}.box.c1{background:var(--c1)}
.bh{font-size:11px;color:var(--mut);margin:0 2px 3px}.b{border-radius:4px;padding:0 5px;font-size:10.5px;font-weight:600;margin-left:4px;color:#fff}
.b.ok{background:var(--ok)}.b.extra{background:var(--warn)}.b.mid{background:var(--bad)}
.miss{font-size:11px;color:var(--warn);font-weight:600;border-top:2px dashed var(--warn);margin:4px 0 2px}.scis{color:var(--bad);font-weight:700}
.df td,.df th{white-space:normal;text-align:left;vertical-align:top;max-width:460px}.df{font-size:13px}
.key{font-size:13px;color:var(--mut);margin:10px 0}.key span{display:inline-block;margin-right:12px}.dot{display:inline-block;width:10px;height:10px;border-radius:2px;vertical-align:middle;margin-right:4px}
</style></head><body><div class="page">
<h1>Chunking examples: what each method does to real dialogues</h1>
<p class="lead">5% of the Conversation set (50 MultiWOZ dialogues). Each example shows the raw input with its gold topic per turn (left),
then the chunks each method produced from exactly that text. The goal of a topic-aware chunker is to cut where the topic switches and nowhere else, without splitting a turn.</p>
<p class="toc">__TOC__<a href="#scores">Scores</a><a href="#diffs">Differences</a></p>
<div class="key"><span><span class="dot" style="background:var(--train)"></span>train</span><span><span class="dot" style="background:var(--hotel)"></span>hotel</span>
<span><span class="dot" style="background:var(--restaurant)"></span>restaurant</span><span><span class="dot" style="background:var(--attraction)"></span>attraction</span>
<span><span class="dot" style="background:var(--taxi)"></span>taxi</span>
<span><b style="color:var(--ok)">cut = topic switch</b>, <b style="color:var(--warn)">extra cut / missed switch</b>, <b style="color:var(--bad)">cut inside a turn (✂)</b></span></div>
__EXAMPLES__
<section id="scores"><h2>Scores on the 5% sample</h2>
<p class="note">Green = best in the column. Pk: chance that two turns k apart are wrongly put in the same/different chunk (lower is better). Boundary F1 counts a cut as correct within one turn of a gold switch.
Coherence gap: similarity inside chunks minus across neighbouring chunks (bge-m3). Retrieval: the user's goal text for one topic as query over all chunks; a hit = a top chunk contains that topic's turns.
bge-m3 is also the scoring model, which may favour the bge-m3 variants. Runtime is laptop CPU with a shared embedding cache, so only rough.</p>
__SCORES__</section>
__DIFFS__
</div></body></html>"""

DIFFS = [
    ("1. RSC (Latif et al., ICNLSP 2025)", [
        ("No public code; rebuilt from the paper's Algorithm 1 (pre-split 15,000, recurse above 1,500, merge below 350, hard split above 2,500 chars, δ = 3).",
         "Only the paper text exists.", "Unknown fidelity in details the paper leaves out."),
        ("Embedding model = bge-m3.", "The paper does not name its model.", "Changes where breakpoints fall."),
        ("Start at LangChain's default 95th-percentile breakpoint; each recursion lowers it by 3 points; stop at the 50th.",
         "The paper says the threshold is 'gradually reduced' but gives no start or floor.",
         "A chunk still over 1,500 chars at the floor is left to the 2,500 hard split."),
        ("LangChain's sentence regex splits only after . ? ! followed by a space, and rejoins sentences with spaces.",
         "Used as published by LangChain.", "Turns without end punctuation merge with the next turn, so about half of RSC's cuts land inside a turn."),
        ("Final split: RecursiveCharacterTextSplitter(2,500, overlap 0).", "The paper gives no overlap.", "Small."),
        ("Applied to short dialogues (about 1,000 chars).", "The paper's limits were tuned on news articles.",
         "In single dialogues the 1,500 / 2,500 limits rarely matter, so RSC mostly keeps one or two chunks."),
    ]),
    ("2. Chroma ClusterSemanticChunker (chunking_evaluation @ e708410)", [
        ("Official code, unchanged: 50-token pieces, max 400 tokens, cl100k token counting.", "-", "None."),
        ("Embeddings: bge-m3 instead of the OpenAI default.", "No API key, by choice.", "Different similarities; usually a strong open model, but not the published setup."),
        ("Scored with our turn-based metrics, not Chroma's token-IoU benchmark.", "Our data and question differ.", "Numbers are not comparable with the Chroma report."),
    ]),
    ("3. Chonkie SemanticChunker 1.7.0", [
        ("3a: package defaults unchanged (potion-base-32M, threshold 0.8, max 2,048 tokens, window 3, Savitzky-Golay 5/3).", "-", "None; this is the library as shipped."),
        ("3b: same settings with bge-m3.", "Our addition, for a same-model comparison.", "Chunk size is counted in bge-m3 tokens."),
        ("No paper exists; the docs are the reference.", "-", "Nothing published to compare with."),
    ]),
    ("Baselines", [
        ("Fixed: 400 cl100k tokens, no overlap (FixedTokenChunker from the Chroma repo).", "Cheap reference.", "Ignores topics; most cuts are inside turns."),
        ("TextTiling: NLTK defaults (w 20, k 10), one turn per paragraph.", "NLTK cuts only at paragraph breaks.", "Never cuts inside a turn; lexical, not embeddings."),
    ]),
    ("Evaluation (all methods)", [
        ("None of the sources test on dialogues, so there are no published numbers to match.", "-", "This is an application to new data, not a numeric reproduction."),
        ("Gold boundaries come from MultiWOZ turn-level dialogue acts (our rule, hand-checked on 20 dialogues).", "MultiWOZ has no segment labels.", "Some noise at turns that mention two topics."),
        ("5% sample: 50 dialogues; stitched = 3 documents per seed.", "Requested scope.", "Scores are noisy; differences of a few points may not hold on the full set."),
        ("bge-m3 is also the scoring model (coherence, retrieval).", "One shared local model.", "May favour the bge-m3 variants."),
        ("In single dialogues about 30% have no topic switch.", "Data as is.", "Methods that rarely cut (RSC, fixed) get low Pk partly by doing little; read Pk together with F1."),
        ("Runtime: laptop CPU with a shared embedding cache.", "-", "Later methods reuse cached vectors, so times are rough."),
    ]),
]


def diffs_html():
    out = ["<section id='diffs'><h2>Differences from each source</h2>"
           "<p class='note'>What we changed or had to decide, why, and the likely effect on the results.</p>"]
    for title, rows in DIFFS:
        out.append(f"<h3>{esc(title)}</h3><div class='tw'><table class='df'><tr><th>What differs</th><th>Why</th><th>Likely effect</th></tr>"
                   + "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in rows)
                   + "</table></div>")
    out.append("</section>")
    return "".join(out)


if __name__ == "__main__":
    main()
