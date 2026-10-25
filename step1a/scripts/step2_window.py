"""Step 2 with a narrow context window (left / right k words) next to the masked turn context.

python scripts/step2_window.py --limit 50 [--split dev] [--out results/v3_n50]
  -> <out>/{step2_window.md, step2_window.csv, step2_window_examples.md, chosen_step2_window.json}

Units, groups and bookings as scripts/step2.py (verbatim gold mentions, gold entities, booking =
(dialogue, gold entity)). Type partition, cannot-link and average linkage always on; no C6.
"""

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import encoder  # noqa: E402
from step2 import load_units  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import split as SP  # noqa: E402
from s1a import step2 as S  # noqa: E402
from s1a import units as U  # noqa: E402
from s1a.metrics import bootstrap_ci, report_block  # noqa: E402
from chk.data import single_docs  # noqa: E402

KS = (2, 3, 5)
SIDES = ("lr", "sym")
BETAS = (0.2, 0.35, 0.5)
ALPHAS = (0.0, 0.2, 0.35, 0.5)
TS = (0.35, 0.45, 0.55)
REF = {"alpha": 0.5, "t": 0.45}
LEVELS = (1, 2, 3)
LINK = "average"
ROLE = ("Train departure", "Train destination", "Train leave at", "Train arrive by",
        "Hotel requested people", "Hotel requested stay", "Hotel stars", "Attraction name",
        "Attraction area")
BASE = {"normalize": True, "by_type": True, "cannot_link": True, "linkage": LINK, "prev_turns": 1}


def settings():
    """(k, side, beta, alpha, t) for the window grid, then beta = 0 rows (k, side = None)."""
    out = [(k, sd, b, a, t) for k in KS for sd in SIDES for b in BETAS for a in ALPHAS
           if a + b < 1 - 1e-9 for t in TS]
    out += [(None, None, 0.0, a, t) for a in ALPHAS for t in TS]
    return out


def cfg_of(k, side, beta, alpha, t):
    c = dict(BASE, alpha=alpha, t=t)
    if beta:
        c.update(window=k, beta=beta, side=side)
    return c


def name(r):
    if not r["beta"]:
        return f"no window, alpha={r['alpha']}, t={r['t']}"
    return f"k={r['k']} {r['side']}, beta={r['beta']}, alpha={r['alpha']}, t={r['t']}"


def encode_all(us, docs, by_doc, enc):
    """String, context and window vectors; window texts per (k, side)."""
    x_str = enc.encode([S.normalize(u.text) for u in us])
    x_ctx = enc.encode([S.masked_context(docs[u.doc_id], u, by_doc[u.doc_id], 1) for u in us])
    texts, vecs = {}, {}
    for k in KS:
        for sd in SIDES:
            w = [S.window_texts(docs[u.doc_id], u, by_doc[u.doc_id], k, sd) for u in us]
            texts[(k, sd)] = w
            if sd == "sym":
                vecs[(k, sd)] = (enc.encode(w), None)
            else:
                vecs[(k, sd)] = (enc.encode([a for a, _ in w]), enc.encode([b for _, b in w]))
    enc.save()
    return x_str, x_ctx, texts, vecs


def majority(us, pred):
    """cluster -> majority gold class."""
    cnt = defaultdict(Counter)
    for u, p in zip(us, pred):
        cnt[p].update(u.labels)
    return {p: c.most_common(1)[0][0] for p, c in cnt.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out) if args.out else paths.RESULTS / f"v3_n{args.limit}"
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
    print(f"{len(us)} verbatim mentions, adapter: {adapter}", flush=True)

    enc = encoder()
    x_str, x_ctx, texts, vecs = encode_all(us, docs, by_doc, enc)
    t_enc = time.time() - t0
    print(f"encoded in {t_enc:.0f}s", flush=True)

    parts = [(g, S.value_type(u.text)) for g, u in zip(groups, us)]
    pairs = S.cannot_links(us, books)
    rows, labs = [], {}
    grid = settings()
    for n, (k, sd, b, a, t) in enumerate(grid, 1):
        lv, rv = vecs[(k, sd)] if b else (None, None)
        x = S.combine_window(x_ctx, lv, rv, x_str, a, b)
        lab = S.cluster_constrained(x, parts, pairs, t, LINK)
        d = report_block(us, lab, LEVELS)
        r = {"k": k, "side": sd, "beta": b, "alpha": a, "t": t, "P": d["all"]["p"], "R": d["all"]["r"],
             "F1": d["all"]["f"], "K": d["K"], "block": d}
        rows.append(r)
        labs[id(r)] = lab
        if n % 50 == 0:
            print(f"{n}/{len(grid)} settings, {time.time() - t0:.0f}s", flush=True)
    t_grid = time.time() - t0 - t_enc

    ref = next(r for r in rows if not r["beta"] and r["alpha"] == REF["alpha"] and r["t"] == REF["t"])
    win = [r for r in rows if r["beta"]]
    best = max(win, key=lambda r: (r["F1"], r["P"]))
    ref_lab, best_lab = labs[id(ref)], labs[id(best)]
    ci_ref, ci_best = bootstrap_ci(us, ref_lab), bootstrap_ci(us, best_lab)
    half = (ci_ref[1] - ci_ref[0]) / 2
    best_cfg = cfg_of(best["k"], best["side"], best["beta"], best["alpha"], best["t"])
    check = S.run_best(us, docs, groups, books, enc, best_cfg)
    same = check == best_lab
    joint = json.loads((paths.RESULTS / "v2_n50" / "chosen_step2_joint.json").read_text(encoding="utf-8"))
    same_ref = S.run_best(us, docs, groups, books, enc, joint) == ref_lab
    enc.save()

    (out / "chosen_step2_window.json").write_text(json.dumps(
        dict(best_cfg, F1=round(best["F1"], 4), K=best["K"], n=len(us), limit=args.limit,
             split=args.split, ref_F1=round(ref["F1"], 4), clear_gain=best["F1"] - ref["F1"] > half),
        indent=1) + "\n", encoding="utf-8", newline="\n")
    write_csv(out, rows, ref, half)
    minutes = (time.time() - t0) / 60
    info = {"n": len(us), "docs": len(by_doc), "adapter": adapter, "pairs": len(pairs), "minutes": minutes,
            "t_enc": t_enc, "t_grid": t_grid, "n_grid": len(grid), "same": same,
            "same_ref": same_ref}
    write_md(out, args, info, rows, ref, best, ci_ref, ci_best, half)
    write_examples(out, us, texts, best, ref_lab, best_lab)
    print((out / "step2_window.md").read_text(encoding="utf-8")[:2500])
    print(f"done in {minutes:.1f} min -> {out}")


def gain(r, ref, half):
    d = r["F1"] - ref["F1"]
    return "clear gain" if d > half else ("within CI" if d > 0 else "no gain")


def write_csv(out, rows, ref, half):
    keys = ["k", "side", "beta", "alpha", "t", "P", "R", "F1", "K"]
    with open(out / "step2_window.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(keys + ["dF1", "stop_rule"] + [f"{s}L{k}" for k in LEVELS for s in "vh"])
        for r in rows:
            lv = [round(r["block"][f"{s}_L{k}"]["f"], 4) for k in LEVELS for s in ("visible", "hidden")]
            w.writerow([round(r[k], 4) if isinstance(r[k], float) else r[k] for k in keys]
                       + [round(r["F1"] - ref["F1"], 4), gain(r, ref, half)] + lv)


def _row(r, ref, half):
    return (f"| {name(r)} | {r['P']:.3f} | {r['R']:.3f} | {r['F1']:.3f} | {r['K']} | "
            f"{r['F1'] - ref['F1']:+.3f} | {gain(r, ref, half)} |")


HEAD = ["| Setting | P | R | F1 | K | dF1 vs ref | stop rule |", "|---|---|---|---|---|---|---|"]


def _span(vals):
    v = sorted(set(vals), key=str)
    return ", ".join(map(str, v))


def write_md(out, args, info, rows, ref, best, ci_ref, ci_best, half):
    win = [r for r in rows if r["beta"]]
    top = sorted(win, key=lambda r: (-r["F1"], -r["P"]))
    L = [f"# Step 2 with a narrow context window ({args.split}, {args.limit} dialogues)", "",
         f"{info['n']} verbatim gold mentions in {info['docs']} dialogues ({info['adapter']}); groups = gold "
         f"entity, booking = (dialogue, gold entity); type partition, {info['pairs']} cannot-link pairs, "
         f"{LINK} linkage, no C6. Vector = alpha * masked turn context + beta * window + "
         f"(1 - alpha - beta) * normalized string; window = mean of left and right k-word vectors (lr) "
         f"or one k + target + k vector (sym), both inside the mention's own turn.", "",
         f"**Tuning and scoring use the same {info['docs']} dialogues**, so the best row is optimistic.", "",
         f"{info['n_grid']} settings ({len(win)} with a window); encoding {info['t_enc']:.0f}s, grid "
         f"{info['t_grid']:.0f}s, total {info['minutes']:.1f} min. run_best on the chosen cfg gives the same "
         f"labels: {info['same']}; run_best on v2_n50/chosen_step2_joint.json gives the reference "
         f"labels: {info['same_ref']}.", "",
         "Stop rule: \"clear gain\" only if F1 - reference F1 > half-width of the reference's bootstrap "
         f"95% CI ({half:.3f}).", "",
         "## 1. Reference (joint setting, no window)", ""] + HEAD + [_row(ref, ref, half)]
    L += ["", f"Reference bootstrap 95% CI: {ci_ref[0]:.3f}-{ci_ref[1]:.3f}.", "",
          "Best without a window (beta = 0, same alpha / t grid): "
          + name(max([r for r in rows if not r["beta"]], key=lambda r: r["F1"]))
          + f" F1 {max(r['F1'] for r in rows if not r['beta']):.3f}.", "",
          "## 2. Top 15 window settings", ""] + HEAD + [_row(r, ref, half) for r in top[:15]]
    near = [r for r in win if r["F1"] >= best["F1"] - 0.01]
    L += ["", "## 3. Plateau", "",
          f"{len(near)} window settings within 0.01 of the best F1 ({best['F1']:.3f}). Ranges: k {{{_span(r['k'] for r in near)}}}, "
          f"side {{{_span(r['side'] for r in near)}}}, alpha {{{_span(r['alpha'] for r in near)}}}, "
          f"beta {{{_span(r['beta'] for r in near)}}}, t {{{_span(r['t'] for r in near)}}}.", ""]
    L += best_section(ref, best, ci_best)
    L += ["## 5. Best per side and per k", "", "| Group | Best setting | F1 | K | dF1 |", "|---|---|---|---|---|"]
    for key, vals in (("side", SIDES), ("k", KS)):
        for v in vals:
            b = max((r for r in win if r[key] == v), key=lambda r: r["F1"])
            L.append(f"| {key}={v} | {name(b)} | {b['F1']:.3f} | {b['K']} | {b['F1'] - ref['F1']:+.3f} |")
    (out / "step2_window.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def best_section(ref, best, ci_best):
    a, b = ref["block"], best["block"]
    L = [f"## 4. Best setting: {name(best)}", "",
         f"F1 {best['F1']:.3f} (bootstrap 95% CI {ci_best[0]:.3f}-{ci_best[1]:.3f}), K {best['K']}; "
         f"reference F1 {ref['F1']:.3f}, K {ref['K']}.", "",
         "Per-class recall (role-pair classes):", "", "| Class | n | ref | best | delta |", "|---|---|---|---|---|"]
    for c in ROLE:
        pa, pb = a["per_class"].get(c), b["per_class"].get(c)
        if pa is None:
            L.append(f"| {c} | 0 | - | - | - |")
            continue
        L.append(f"| {c} | {pa['n']} | {pa['recall']:.2f} | {pb['recall']:.2f} | {pb['recall'] - pa['recall']:+.2f} |")
    L += ["", "Top-10 confused (gold -> cluster majority):", "", "| ref | n | best | n |", "|---|---|---|---|"]
    ca, cb = a["confused"], b["confused"]
    for i in range(max(len(ca), len(cb))):
        x = f"{ca[i][0][0]} -> {ca[i][0][1]} | {ca[i][1]}" if i < len(ca) else " | "
        y = f"{cb[i][0][0]} -> {cb[i][0][1]} | {cb[i][1]}" if i < len(cb) else " | "
        L.append(f"| {x} | {y} |")
    L += ["", "Visible / hidden attributes per TEAR level (F1):", "", "| Subset | n | ref | best |", "|---|---|---|---|"]
    for k in LEVELS:
        for s in ("visible", "hidden"):
            key = f"{s}_L{k}"
            L.append(f"| {key} | {a[key]['n']} | {a[key]['f']:.3f} | {b[key]['f']:.3f} |")
    return L + [""]


def write_examples(out, us, texts, best, ref_lab, best_lab):
    """10 role-pair mentions with window texts and cluster before / after; fixed ones first."""
    ma, mb = majority(us, ref_lab), majority(us, best_lab)
    cand = defaultdict(list)
    for i, u in enumerate(us):
        cls = sorted(set(u.labels) & set(ROLE))
        if not cls:
            continue
        ok_a, ok_b = ma[ref_lab[i]] in u.labels, mb[best_lab[i]] in u.labels
        rank = 0 if (not ok_a and ok_b) else 1 if (ok_a and not ok_b) else 2 if not ok_b else 3
        cand[cls[0]].append((rank, i))
    for v in cand.values():
        v.sort()
    pick = []
    while len(pick) < 10 and any(cand.values()):
        for c in ROLE:
            if cand.get(c) and len(pick) < 10:
                pick.append(cand[c].pop(0))
    tag = {0: "FIXED", 1: "BROKEN", 2: "still wrong", 3: "right both"}
    k, sd = best["k"], best["side"]
    L = ["# Step 2 window examples", "", f"Best setting: {name(best)}. Windows shown for k={k}, {sd} "
         "(lr: left | right). Cluster = its majority gold class and size; before = reference (no window).", ""]
    size_a, size_b = Counter(ref_lab), Counter(best_lab)
    for rank, i in pick:
        u, w = us[i], texts[(k, sd)][i]
        wt = f"`{w[0]}` | `{w[1]}`" if sd == "lr" else f"`{w}`"
        L += [f"- \"{u.text}\" ({'|'.join(sorted(u.labels))}) [{tag[rank]}]", f"  - window: {wt}",
              f"  - before: {ma[ref_lab[i]]} (size {size_a[ref_lab[i]]}); after: {mb[best_lab[i]]} "
              f"(size {size_b[best_lab[i]]})"]
    (out / "step2_window_examples.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
