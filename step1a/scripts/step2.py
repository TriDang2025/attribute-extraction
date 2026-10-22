"""Step 2 ladder with gold entities fixed: cluster verbatim gold mentions inside each gold entity.

python scripts/step2.py --limit 50 [--split dev] [--out results/v2_n50]
  -> <out>/{step2.md, step2.csv, step2_examples.md, chosen_step2.json}
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

from run import encoder  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import split as SP  # noqa: E402
from s1a import step2 as S  # noqa: E402
from s1a import units as U  # noqa: E402
from chk.data import single_docs  # noqa: E402

T_GRID = [round(0.2 + 0.05 * i, 2) for i in range(9)]
LINKAGES = ("average", "complete", "single")
ALPHAS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
T_RETUNE = (0.2, 0.3, 0.4, 0.5, 0.6)
THETAS = (0.6, 0.7, 0.8, 0.9)
LEVELS = (1, 2, 3)


# ---------- units and scoring (Part 1 contract, with a fallback) ----------

def load_units(docs, tables):
    """Verbatim gold mentions via s1a.gold when importable, else units.value_units wrapped."""
    try:
        from s1a import gold
        ms = gold.mentions_for(docs, tables)
        return [m for m in ms if m.verbatim and m.start >= 0], "s1a.gold.mentions_for"
    except ImportError:
        out = []
        for did, doc in docs.items():
            if did in tables:
                for u in U.value_units(doc, tables[did])[0]:
                    u.labels, u.hidden = frozenset({u.label}), {}
                    out.append(u)
        return out, "fallback units.value_units"


try:
    from s1a import metrics as MET
    from s1a.metrics import format_block, report_block
except ImportError:  # fallback: plain scores only
    MET, format_block = None, None

    def report_block(units, pred, levels=LEVELS):
        from hbe.metrics import bcubed
        p, r, f = bcubed([u.label for u in units], pred)
        return {"K": len(set(pred)), "all": {"p": p, "r": r, "f": f, "n": len(units)}}


def single_f1(units, pred):
    from hbe.metrics import external
    return external([u.label for u in units], pred)["bcubed_f1"]


def score(units, pred, stage, config, cfg=None):
    d = report_block(units, [str(p) for p in pred], LEVELS)
    row = {"stage": stage, "config": config, "P": d["all"]["p"], "R": d["all"]["r"],
           "F1": d["all"]["f"], "K": d["K"], "single_F1": single_f1(units, pred)}
    for k in LEVELS:
        for side in ("visible", "hidden"):
            b = d.get(f"{side}_L{k}")
            row[f"{side[0]}L{k}"] = b["f"] if b and b["n"] else None
    row["cfg"] = cfg
    return row, d


# ---------- gold slot types ----------

def expected_type(cls):
    slot = cls.split(" ", 1)[1].lower() if " " in cls else cls.lower()
    if "day" in slot:
        return "day"
    if any(w in slot for w in ("leave at", "arrive by", "time")):
        return "time"
    if any(w in slot for w in ("people", "stay", "stars")):
        return "number"
    if "reference" in slot:
        return "id"
    return "text"


def typer_report(us):
    conf, ex, ok = Counter(), defaultdict(list), 0
    for u in us:
        pred = S.value_type(u.text)
        exp = sorted({expected_type(c) for c in u.labels})
        if pred in exp:
            ok += 1
        else:
            key = ("/".join(exp), pred)
            conf[key] += 1
            if len(ex[key]) < 6:
                ex[key].append(u.text)
    return ok / max(1, len(us)), conf, ex


# ---------- the ladder ----------

def fmt(x):
    return "-" if x is None else f"{x:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out) if args.out else paths.RESULTS / f"v2_n{args.limit}"
    if not out.is_absolute():
        out = paths.ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    docs = {d.doc_id: d for d in single_docs(SP.dialogues(args.split, args.limit))}
    tables = U.load_tables(paths.TEAR_DATA, list(docs))
    us, adapter = load_units(docs, tables)
    groups = [S.gold_entity(u, docs[u.doc_id]) for u in us]
    books = [(u.doc_id, g) for u, g in zip(us, groups)]
    by_doc = defaultdict(list)
    for u in us:
        by_doc[u.doc_id].append(u)
    n_cls = len(set().union(*(u.labels for u in us))) if us else 0
    print(f"{len(us)} verbatim mentions, {n_cls} classes, adapter: {adapter}", flush=True)

    enc = encoder()
    x_raw = enc.encode([u.text for u in us])
    x_norm = enc.encode([S.normalize(u.text) for u in us])
    contexts = [S.masked_context(docs[u.doc_id], u, by_doc[u.doc_id], 1) for u in us]
    x_ctx = enc.encode(contexts)
    enc.save()
    print(f"encoded in {time.time() - t0:.0f}s", flush=True)

    rows, main_rows, blocks = [], [], {}

    def add(stage, config, pred, cfg=None, main=False, block=False):
        r, d = score(us, pred, stage, config, cfg)
        rows.append(r)
        if main:
            main_rows.append(r)
        if block:
            blocks[f"{stage} {config}"] = d
        return r

    # C0 original
    base = {"normalize": False, "alpha": None, "by_type": False, "cannot_link": False,
            "theta": None, "t": 0.4, "linkage": "average", "prev_turns": 1}
    c0 = add("C0", "raw strings, average, t=0.4", S.cluster_threshold(x_raw, groups, 0.4), dict(base),
             main=True, block=True)
    # C1 ceilings
    add("C1", "string ceiling (normalized string -> majority gold class)", S.string_ceiling(us, groups),
        main=True)
    add("C1", "oracle k per entity (normalized string vectors, average)",
        S.oracle_k(x_norm, us, groups, "average"), main=True)
    # C2 fair baseline
    c2 = None
    for link in LINKAGES:
        for t in T_GRID:
            cfg = dict(base, normalize=True, t=t, linkage=link)
            r = add("C2 grid", f"normalized, {link}, t={t}", S.cluster_threshold(x_norm, groups, t, link), cfg)
            if c2 is None or r["F1"] > c2["F1"]:
                c2 = r
    rows.append(dict(c2, stage="C2"))
    main_rows.append(rows[-1])
    blocks["C2 " + c2["config"]] = score(us, S.cluster_threshold(x_norm, groups, c2["cfg"]["t"],
                                                                  c2["cfg"]["linkage"]), "", "")[1]
    t, link = c2["cfg"]["t"], c2["cfg"]["linkage"]
    # C3 + context
    c3 = None
    for a in ALPHAS:
        cfg = dict(c2["cfg"], alpha=a)
        r = add("C3 alpha", f"alpha={a}, {link}, t={t}",
                S.cluster_threshold(S.combine(x_ctx, x_norm, a), groups, t, link), cfg)
        if c3 is None or r["F1"] > c3["F1"]:
            c3 = r
    rows.append(dict(c3, stage="C3"))
    main_rows.append(rows[-1])
    a = c3["cfg"]["alpha"]
    x3 = S.combine(x_ctx, x_norm, a)
    c3t = c3
    for tt in T_RETUNE:
        cfg = dict(c3["cfg"], t=tt)
        r = add("C3 retune", f"alpha={a}, {link}, t={tt}", S.cluster_threshold(x3, groups, tt, link), cfg)
        if r["F1"] > c3t["F1"]:
            c3t = r
    rows.append(dict(c3t, stage="C3 retuned"))
    main_rows.append(rows[-1])
    t = c3t["cfg"]["t"]
    cfg = c3t["cfg"]
    # C4 + partition by type
    parts = [(g, S.value_type(u.text)) for g, u in zip(groups, us)]
    cfg = dict(cfg, by_type=True)
    add("C4", f"+ partition by type (alpha={a}, {link}, t={t})", S.cluster_threshold(x3, parts, t, link),
        cfg, main=True)
    acc, tconf, tex = typer_report(us)
    # C5 + cannot-link
    pairs = S.cannot_links(us, books)
    cfg = dict(cfg, cannot_link=True)
    lab5 = S.cluster_constrained(x3, parts, pairs, t, link)
    add("C5", f"+ cannot-link ({len(pairs)} pairs)", lab5, cfg, main=True)
    # C6 + merge split clusters
    c6, logs = None, {}
    for th in THETAS:
        lab6, log = S.merge_split_clusters(lab5, x_ctx, books, th, groups)
        logs[th] = log
        r = add("C6 theta", f"theta={th} ({len(log)} merges)", lab6, dict(cfg, theta=th))
        if c6 is None or r["F1"] > c6["F1"]:
            c6 = r
    rows.append(dict(c6, stage="C6"))
    main_rows.append(rows[-1])

    cands = [r for r in rows if r["cfg"] is not None and not r["stage"].endswith(("grid", "alpha", "retune", "theta"))]
    best = max(cands, key=lambda r: r["F1"])
    best_lab = S.run_best(us, docs, groups, books, enc, best["cfg"])
    blocks["chosen " + best["stage"] + " " + best["config"]] = score(us, best_lab, "", "")[1]
    enc.save()
    (out / "chosen_step2.json").write_text(json.dumps(
        dict(best["cfg"], stage=best["stage"], F1=round(best["F1"], 4), n=len(us), limit=args.limit),
        indent=1) + "\n", encoding="utf-8", newline="\n")

    keys = ["stage", "config", "P", "R", "F1", "K", "single_F1"] + [f"{s}L{k}" for k in LEVELS for s in "vh"]
    with open(out / "step2.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(keys + ["cfg"])
        for r in rows:
            w.writerow([round(r[k], 4) if isinstance(r[k], float) else r[k] for k in keys]
                       + [json.dumps(r["cfg"])])
    minutes = (time.time() - t0) / 60
    write_md(out, args, us, adapter, n_cls, main_rows, rows, blocks, best, acc, tconf, tex, len(pairs), minutes)
    write_examples(out, us, logs, c6["cfg"]["theta"], contexts, tconf, tex)
    print((out / "step2.md").read_text(encoding="utf-8")[:3000])
    print(f"done in {minutes:.1f} min -> {out}")


def write_md(out, args, us, adapter, n_cls, main_rows, rows, blocks, best, acc, tconf, tex, n_pairs, minutes):
    L = [f"# Step 2 with gold entities fixed ({args.split}, {args.limit} dialogues)", "",
         f"{len(us)} verbatim gold mentions, {n_cls} classes, {len(set(u.doc_id for u in us))} dialogues; "
         f"units from {adapter}. Groups = gold entity of the mention; booking = (dialogue, gold entity). "
         f"Run time {minutes:.1f} min.", "",
         "**Tuning uses the same dialogues it reports on** (t, linkage, alpha, theta are picked by F1 "
         "on these mentions), so rows after C2 are optimistic.", "",
         "Lenient multi-label B-cubed (s1a.metrics.report_block); single F1 = old single-label score on "
         "the joined label. vL/hL = F1 on mentions of visible / hidden attributes at TEAR level L. "
         "Delta = F1 change vs the previous carried row (ceilings vs C0).", "",
         "| Stage | Config | P | R | F1 | K | Delta F1 | single F1 | vL1 | hL1 | vL2 | hL2 | vL3 | hL3 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    prev = None
    for r in main_rows:
        ref = main_rows[0] if r["stage"] == "C1" else prev
        dlt = "" if ref is None or r is ref else f"{r['F1'] - ref['F1']:+.3f}"
        L.append(f"| {r['stage']} | {r['config']} | {fmt(r['P'])} | {fmt(r['R'])} | {fmt(r['F1'])} | {r['K']} | "
                 f"{dlt} | {fmt(r['single_F1'])} | " + " | ".join(fmt(r[f'{s}L{k}']) for k in LEVELS for s in "vh") + " |")
        if r["stage"] != "C1":
            prev = r
    L += ["", f"Chosen: {best['stage']} {best['config']} (F1 {best['F1']:.3f}) -> chosen_step2.json "
          f"(`s1a.step2.run_best`).", ""]
    # C2 grid
    L += ["## C2 grid (normalized strings): F1 (K)", "",
          "| linkage | " + " | ".join(f"t={t}" for t in T_GRID) + " |", "|---" * (len(T_GRID) + 1) + "|"]
    grid = {r["config"]: r for r in rows if r["stage"] == "C2 grid"}
    for link in LINKAGES:
        L.append(f"| {link} | " + " | ".join(
            f"{grid[f'normalized, {link}, t={t}']['F1']:.3f} ({grid[f'normalized, {link}, t={t}']['K']})"
            for t in T_GRID) + " |")
    for stage, title in (("C3 alpha", "C3 context weight alpha"), ("C3 retune", "C3 threshold re-tune"),
                         ("C6 theta", "C6 merge threshold theta")):
        L += ["", f"## {title}", "", "| Config | P | R | F1 | K |", "|---|---|---|---|---|"]
        L += [f"| {r['config']} | {fmt(r['P'])} | {fmt(r['R'])} | {fmt(r['F1'])} | {r['K']} |"
              for r in rows if r["stage"] == stage]
    L += ["", f"## C4 typer", "", f"Type accuracy vs gold slot type: {acc:.3f} ({len(us)} mentions). "
          "Expected: day -> day; leave at / arrive by / time -> time; people / stay / stars -> number; "
          "reference -> id; else text.", "", "| expected | predicted | n | examples |", "|---|---|---|---|"]
    L += [f"| {e} | {p} | {n} | " + ", ".join(f'"{x}"' for x in tex[(e, p)]) + " |"
          for (e, p), n in tconf.most_common(12)]
    L += ["", f"C5 uses {n_pairs} cannot-link pairs (same dialogue and entity, different normalized string).", ""]
    if format_block:
        L += ["## Report blocks", ""]
        for title, d in blocks.items():
            L.append(format_block(d, title))
    (out / "step2.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def _desc(us, ix, n=8):
    s = Counter(us[i].text.lower() for i in ix).most_common(n)
    g = Counter(c for i in ix for c in us[i].labels).most_common(3)
    return ", ".join(f'"{t}"x{k}' for t, k in s), "; ".join(f"{c} {k}" for c, k in g), (g[0][0] if g else None)


def write_examples(out, us, logs, theta, contexts, tconf, tex):
    L = ["# Step 2 examples", "", f"## Top-10 merges at theta={theta} (C6, most similar first)", "",
         "Right = both clusters have the same majority gold class.", ""]
    for k, (cos, a, b) in enumerate(sorted(logs.get(theta, []), key=lambda x: -x[0])[:10], 1):
        sa, ga, ma = _desc(us, a)
        sb, gb, mb = _desc(us, b)
        L += [f"{k}. cos {cos:.3f}, {'RIGHT' if ma == mb else 'WRONG'}",
              f"   - A ({len(a)}): {sa} | gold: {ga}", f"   - B ({len(b)}): {sb} | gold: {gb}"]
    if not logs.get(theta):
        L.append("(no merges)")
    L += ["", "## Masked contexts (first 8 mentions)", ""]
    L += [f"- \"{u.text}\" ({'|'.join(sorted(u.labels))}): {c.replace(chr(10), ' / ')[:300]}"
          for u, c in list(zip(us, contexts))[:8]]
    (out / "step2_examples.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
