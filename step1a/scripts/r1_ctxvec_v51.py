"""wf_v5.1 R1: cluster the Step 1a mentions on value + context (s1a/ctxvec_v51.py) and replay the cached wf_v5.0 Step 3 names on the new
clusters. alpha 0 must reproduce the adopted clusters (checked). Chosen on dev50, dev50b scored with the same settings. CPU; bge-m3 on the
context texts (cached in step1a/data/cache; the vectors are also written to results/wf_v51/r1/ctx_vectors_<set>.npz).

python scripts/r1_ctxvec_v51.py  -> results/wf_v51/r1/{r1_alpha.csv, r1.md, examples.md, clusters_<set>.csv (one column per alpha/t), ctx_vectors_<set>.npz}
Replay: a new cluster with Jaccard >= 0.8 to an old cluster (one-to-one) takes that cluster's cached Step 3 column ("strict", unmatched new
clusters are dropped = lower bound); "lenient" also lets an unmatched new cluster take the old cluster holding >= half of its mentions
(upper bound: Step 3 would name the pieces alike). Found L2 = G3 rule: v4.9 set (loop 1 + 2, human check) minus loop-1 finds lost plus new ones.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402

import g3_nojoin_v50 as G3  # noqa: E402
import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v49 as M49  # noqa: E402
from run import encoder  # noqa: E402
from s1a import ctxvec_v51 as CV  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import step2 as S2  # noqa: E402
from s1a import trace_v50 as T  # noqa: E402

OUT = ROOT / "results" / "wf_v51" / "r1"
CTXSPLIT = ROOT / "results" / "wf_v50" / "g3" / "ctxsplit" / "big40"
SETS = ("dev50", "dev50b")
T_GRID = (0.4, 0.3, 0.25, 0.2, 0.15, 0.1)   # distance thresholds tried for alpha > 0 (0.4 = adopted)
SETTINGS = [(a, t) for a in CV.ALPHAS for t in T_GRID if (a, t) != (0.0, 0.4)]
SETTINGS = [(0.0, 0.4)] + SETTINGS   # alpha 0 with a smaller t is the control: finer clusters without any context
V50 = {"dev50": 34, "dev50b": 30}   # found L2, v5.0 context split big40 (wf_v5.0 g3s3.md)


def units_of(mt):
    """Span units of the exported mentions (the cluster_fn reads doc_id, turn, start, end, text), groups (stage-1 entity) and books."""
    spans = [SimpleNamespace(doc_id=r.dialogue_id, turn=int(r.turn), start=int(r.char_start), end=int(r.char_end), text=r.text)
             for r in mt.itertuples()]
    groups = [int(e[1:]) if e else -1 for e in mt["entity"]]
    return spans, groups, list(mt["instance_id"])


def recluster(mt0, docs, enc, settings):
    """{(alpha, t): cluster id per mention (row order of mt0)}."""
    spans, groups, books = units_of(mt0)
    out = {}
    for a, t in settings:
        _x, lab = CV.cluster_fn(a, t)(spans, docs, enc, groups, books)
        out[(a, t)] = MN.cluster_ids([f"E{g}" if g >= 0 else "" for g in groups], lab)
    return out


def by_entity(mt, col="cluster_id"):
    """{stage-1 entity: {cluster id: [mention ids]}}."""
    out = {}
    for e, g in mt[mt[col] != ""].groupby("entity"):
        out[e] = {c: list(ix) for c, ix in g.groupby(col).groups.items()}
    return out


def evaluate(set_name, alpha, t, new_ids, ctx):
    """One table row (+ detail) for one alpha."""
    mt, labels, emap, final, step3 = ctx["load"]
    v49, gold = ctx["v49"], ctx["gold"]
    gold_by_ent = ctx["gold_by_ent"]
    mt1 = mt.copy()
    mt1["cluster_id"] = new_ids
    old_cl, new_cl = by_entity(mt), by_entity(mt1)
    old_of, new_of = mt["cluster_id"].to_dict(), mt1["cluster_id"].to_dict()
    row = {"set": set_name, "alpha": alpha, "t": t, "K_all": sum(len(v) for v in new_cl.values())}
    res = {}
    for mode in ("strict", "lenient"):
        after, n_match = {}, 0
        for key, cols in final.items():
            stage1 = emap[key][0]
            old = {c: set(ids) for c, ids in old_cl.get(stage1, {}).items()}
            new = {c: set(ids) for c, ids in new_cl.get(stage1, {}).items()}
            match = CV.match_clusters(old, new, CV.JACCARD, lenient=(mode == "lenient"))
            n_match += len(match)
            nof = {i: c for c, ids in new.items() for i in ids}
            oof = {i: old_of[i] for i in nof}
            after[key] = CV.carry_columns(cols, oof, nof, match)
        f1, rows = G3.score(after, emap, mt1, labels, gold_by_ent)
        res[mode] = (f1, rows, n_match, after)
    f0, rows0 = ctx["base"]
    for mode, (f1, rows, n_match, _after) in res.items():
        kinds = pd.Series([r["kind"] for r in rows]).value_counts()
        k0 = pd.Series([r["kind"] for r in rows0]).value_counts()
        row[f"found_loop1_{mode}"] = len(f1)
        row[f"found_L2_{mode}"] = len((v49["loop2"] - (f0 - f1)) | (f1 - f0))
        row[f"lost_{mode}"] = "; ".join(sorted(f0 - f1))
        row[f"gained_{mode}"] = "; ".join(sorted(f1 - f0))
        row[f"cols_{mode}"] = len(rows)
        row[f"new_wrong_cols_{mode}"] = int(kinds.get("dup", 0) + kinds.get("other", 0) - k0.get("dup", 0) - k0.get("other", 0))
    row["unchanged_clusters"] = res["strict"][2]
    # gold counts over the scored entities
    mixed, frag, s3 = {}, {}, set()
    for ent, key in ctx["key_of"].items():
        stage1, attrs = emap[key][0], set(gold_by_ent.get(ent, []))
        cl = new_cl.get(stage1, {})
        mixed |= {f"{c}": pair for c, pair in CV.role_clusters(cl, labels, attrs).items()}
        frag |= {a: cs for a, cs in CV.fragmented(cl, labels, attrs).items()}
        s3 |= CV.s3_attrs(cl, labels, attrs, ctx["total"][stage1], lambda a, s=stage1: ctx["share"][(a, s)] >= T.S1_SHARE)
    row["K_scored"] = sum(len(new_cl.get(emap[k][0], {})) for k in ctx["key_of"].values())
    row["mixed_clusters"] = len(mixed)
    row["s3_attrs"] = len(s3)
    row["s3_names"] = "; ".join(sorted(s3))
    row["fragmented_attrs"] = len(frag)
    row["fragmented_names"] = "; ".join(sorted(frag))
    return row, {"mixed": mixed, "frag": frag, "s3": s3, "mt1": mt1, "after": {m: v[3] for m, v in res.items()}}


def context_of(set_name):
    mt, labels, emap, final, step3 = G3.load(set_name)
    v49, gold = M49.found_v49(set_name)
    gold_by_ent = {}
    for a, e in gold.items():
        gold_by_ent.setdefault(e, []).append(a)
    key_of = {gt: k for k, (_s1, gt, _sh) in emap.items() if gt in M46.GOLD_ENTITIES}
    stage1s = {emap[k][0] for k in key_of.values()}
    sub = mt[(mt["cluster_id"] != "") & mt["entity"].isin(stage1s)]
    total = {s: pd.Series([a for i in sub.index[sub["entity"] == s] for a in set(labels.get(i, []))]).value_counts().to_dict() for s in stage1s}
    share = {(a, emap[key_of[e]][0]): T.entity_share(mt, labels, a, emap[key_of[e]][0])[0] for a, e in gold.items()}
    base = G3.score(final, emap, mt, labels, gold_by_ent)
    return {"load": (mt, labels, emap, final, step3), "v49": v49, "gold": gold, "gold_by_ent": gold_by_ent, "key_of": key_of,
            "total": total, "share": share, "base": base}


def reference_rows(set_name, ctx):
    """v4.9 (cached) and the v5.0 context split big40, scored the same way."""
    mt, labels, emap, final, _ = ctx["load"]
    f0, rows0 = ctx["base"]
    after = json.loads((CTXSPLIT / set_name / "final_columns.json").read_text(encoding="utf-8"))[M46.RUN_OF[set_name]]
    f1, rows1 = G3.score(after, emap, mt, labels, ctx["gold_by_ent"])
    k0, k1 = (pd.Series([r["kind"] for r in rs]).value_counts() for rs in (rows0, rows1))
    l2 = len((ctx["v49"]["loop2"] - (f0 - f1)) | (f1 - f0))
    return [{"set": set_name, "alpha": "v4.9 (cached)", "found_L2_strict": len(ctx["v49"]["loop2"]), "found_L2_lenient": len(ctx["v49"]["loop2"]),
             "cols_strict": len(rows0), "new_wrong_cols_strict": 0},
            {"set": set_name, "alpha": "v5.0 context split", "found_L2_strict": l2, "found_L2_lenient": l2, "cols_strict": len(rows1),
             "new_wrong_cols_strict": int(k1.get("dup", 0) + k1.get("other", 0) - k0.get("dup", 0) - k0.get("other", 0))}]


def select(df, alpha=None):
    """(alpha, t) chosen on dev50 only: alpha > 0 (or the given alpha), scored-entity cluster count <= 1.5 x the adopted one, then the most
    found L2 in the lenient replay, then fewer mixed-role clusters, fewer fragmented attributes, smaller alpha."""
    d = df[(df["set"] == "dev50") & df["alpha"].map(lambda a: isinstance(a, float) and (a > 0 if alpha is None else a == alpha))]
    k0 = float(df[(df["set"] == "dev50") & (df["alpha"] == 0.0) & (df["t"] == 0.4)]["K_scored"].iloc[0])
    d = d[d["K_scored"] <= 1.5 * k0]
    d = d.sort_values(["found_L2_lenient", "mixed_clusters", "fragmented_attrs", "alpha"], ascending=[False, True, True, True])
    return float(d.iloc[0]["alpha"]), float(d.iloc[0]["t"])


def raw_snippet(docs, r, left=CV.LEFT, right=CV.RIGHT):
    """"left words [value] right words" of one mention row (unmasked, for reading)."""
    doc = docs[r.dialogue_id]
    lo, hi = MN.turn_bounds(doc, int(r.turn))
    a, b = int(r.char_start), int(r.char_end)
    lw = doc.text[lo:a].split()[-left:]
    rw = doc.text[b:hi].split()[:right]
    return " ".join(lw + [f"[{doc.text[a:b]}]"] + rw)


def clusters_at(mt, new_ids):
    mt1 = mt.copy()
    mt1["cluster_id"] = new_ids
    return by_entity(mt1)


def scored_clusters(ctx, cl):
    """[(entity, stage-1 id, clusters, gold attrs)] of the scored entities."""
    emap = ctx["load"][2]
    return [(e, emap[k][0], cl.get(emap[k][0], {}), set(ctx["gold_by_ent"].get(e, []))) for e, k in ctx["key_of"].items()]


def separation(mixed, clusters, labels, vec):
    """Per mixed-role cluster: share of its two roles' mentions that 2-means on the context vectors puts in the right part."""
    out = []
    for cid, (a1, a2) in mixed.items():
        ids = [i for i in clusters[cid] if a1 in labels.get(i, []) or a2 in labels.get(i, [])]
        y = np.array([a1 in labels.get(i, []) for i in ids])
        if y.all() or not y.any():
            continue
        lab = KMeans(2, n_init=10, random_state=0).fit(np.stack([vec[i] for i in ids])).labels_
        out.append((cid, a1, a2, len(ids), round(float(max((lab == y).mean(), (lab != y).mean())), 2)))
    return out


def beats(df, a, t):
    """R1 at (a, t) beats the v5.0 context split: lenient found L2 above it on dev50, not below on dev50b, no new wrong columns."""
    r = {s: df[(df["set"] == s) & (df["alpha"] == a) & (df["t"] == t)].iloc[0] for s in SETS}
    return (r["dev50"]["found_L2_lenient"] > V50["dev50"] and r["dev50b"]["found_L2_lenient"] >= V50["dev50b"]
            and all(r[s]["new_wrong_cols_lenient"] <= 0 for s in SETS))


def write_examples(setting, wide):
    """examples.md: two mixed-role clusters of the adopted clustering (dev50), their roles with context snippets, and where the chosen setting goes."""
    mt0, ids, docs, _cx, ctx = wide["dev50"]
    mt, labels = ctx["load"][0], ctx["load"][1]
    old = clusters_at(mt, ids[(0.0, 0.4)])
    new_of = {i: c for cl in clusters_at(mt, ids[setting]).values() for c, m in cl.items() for i in m}
    rows = mt0.set_index(mt0["mention_id"].astype(int))
    lines = ["# wf_v5.1 R1 examples: two mixed-role clusters (dev50)", "",
             f"Before = adopted clusters (alpha 0). After = alpha {setting[0]}, t {setting[1]} (chosen on dev50). Snippets: 4 words left, [value], 2 words right "
             "(the vector sees the value masked as its type tag).", ""]
    cands = []   # (roles share one value type, size, entity, cluster id, pair, mention ids): same-type roles first (the S3 case), then the biggest
    for ent, _s1, cl, attrs in scored_clusters(ctx, old):
        for cid, pair in CV.role_clusters(cl, labels, attrs).items():
            types = [Counter(S2.value_type(rows.loc[i, "text"]) for i in cl[cid] if a in labels.get(i, [])).most_common(1)[0][0] for a in pair]
            cands.append((types[0] == types[1], len(cl[cid]), ent, cid, pair, cl[cid]))
    seen, shown = set(), 0
    for _same, _n, ent, cid, pair, ids_c in sorted(cands, key=lambda c: (not c[0], -c[1])):
        if frozenset(pair) in seen or shown == 2:
            continue
        seen.add(frozenset(pair))
        shown += 1
        lines += [f"## {shown}. cluster {cid} ({ent}, {len(ids_c)} mentions): roles {pair[0]} / {pair[1]}", ""]
        for a in pair:
            mem = [i for i in ids_c if a in labels.get(i, [])]
            lines.append(f"- {a} ({len(mem)} mentions)")
            lines += [f"  - `{raw_snippet(docs, rows.loc[i])}`" for i in mem[:2]]
        lines += ["", f"After (alpha {setting[0]}, t {setting[1]}): the {len(ids_c)} mentions go to", "",
                  f"| new cluster | mentions from this cluster | {pair[0]} | {pair[1]} |", "|---|---|---|---|"]
        cnt = {}
        for i in ids_c:
            cnt.setdefault(new_of.get(i, ""), []).append(i)
        for nc, mem in sorted(cnt.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"| {nc or '(none)'} | {len(mem)} | {sum(pair[0] in labels.get(i, []) for i in mem)} | {sum(pair[1] in labels.get(i, []) for i in mem)} |")
        lines.append("")
    (OUT / "examples.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_report(df, setting, wide):
    a_sel, t_sel = setting
    cols = ["set", "alpha", "t", "K_scored", "mixed_clusters", "s3_attrs", "fragmented_attrs", "found_L2_strict", "found_L2_lenient",
            "cols_lenient", "new_wrong_cols_lenient"]
    ok = df[df["alpha"].map(lambda a: isinstance(a, float))]
    best = {a: select(df, a) if a > 0 else (0.0, 0.4) for a in CV.ALPHAS}
    sep = []
    for s in SETS:
        mt0, ids, _docs, cx, ctx = wide[s]
        mt, labels = ctx["load"][0], ctx["load"][1]
        vec = dict(zip(mt0["mention_id"].astype(int), cx))
        cl = clusters_at(mt, ids[(0.0, 0.4)])
        for _e, _s1, c, attrs in scored_clusters(ctx, cl):
            sep += [(s, *r) for r in separation(CV.role_clusters(c, labels, attrs), c, labels, vec)]
    sep = pd.DataFrame(sep, columns=["set", "cluster", "role 1", "role 2", "mentions", "2-means agreement"])
    sep.to_csv(OUT / "r1_separation.csv", index=False, encoding="utf-8", lineterminator="\n")
    verdict = ["| alpha | t (best on dev50) | beats the context split? | dev50 found L2 (lenient / strict) | dev50b found L2 (lenient / strict) |", "|---|---|---|---|---|"]
    for a in CV.ALPHAS[1:]:
        t = best[a][1]
        r = {s: ok[(ok["set"] == s) & (ok["alpha"] == a) & (ok["t"] == t)].iloc[0] for s in SETS}
        verdict.append(f"| {a} | {t} | {'yes' if beats(df, a, t) else 'no'} | {r['dev50']['found_L2_lenient']} / {r['dev50']['found_L2_strict']} "
                       f"| {r['dev50b']['found_L2_lenient']} / {r['dev50b']['found_L2_strict']} |")
    any_beat = any(beats(df, a, best[a][1]) for a in CV.ALPHAS[1:])
    lines = ["# wf_v5.1 R1: cluster on value + context (replay on the cached v5.0 Step 3)", "",
             "## TL;DR", "",
             f"- alpha 0 reproduces the adopted clusters exactly (dev50 {len(wide['dev50'][0])} and dev50b {len(wide['dev50b'][0])} mentions: same cluster ids, same replayed columns and found L2).",
             f"- Chosen on dev50: alpha {a_sel}, t {t_sel}. Beats the v5.0 context split (34 | 30)? **{'yes' if beats(df, a_sel, t_sel) else 'no'}**; "
             f"any alpha beats it: **{'yes' if any_beat else 'no'}**.",
             "- Mixing the context in changes the cosine scale (context vectors are alike), so alpha >= 0.5 at the adopted t 0.4 merges almost everything (K 117 -> 15). "
             "A smaller t is needed; the alpha 0 control with the same t shows what finer clusters alone do.",
             "- Replay limit: a changed cluster has no cached name. Strict = only clusters with Jaccard >= 0.8 keep their name (lower bound); lenient = a changed cluster also "
             "takes the old cluster that holds half of its mentions (upper bound, hides fragmentation). Real value needs a GPU rerun.", "",
             "## Per alpha (t best on dev50 by the selection rule)", "", *verdict, "",
             "Reference, same replay: v5.0 context split found L2 34 | 30; v4.9 cached 33 | 28.", "",
             "## Table at the adopted t 0.4 (as briefed)", "", ok[ok["t"] == 0.4][cols].to_markdown(index=False), "",
             f"## Table at t {t_sel} (chosen); alpha 0 = control without context", "", ok[ok["t"] == t_sel][cols].to_markdown(index=False), "",
             "All settings: `r1_alpha.csv`.", "",
             "## Reference rows", "", df[df["alpha"].map(lambda a: not isinstance(a, float))][["set", "alpha", "found_L2_strict", "cols_strict", "new_wrong_cols_strict"]].to_markdown(index=False), "",
             "## Do the context vectors separate the roles at all?", "",
             "Mixed-role clusters of the adopted clustering; 2-means on the context vectors of the two roles' mentions (1.0 = perfect split, 0.5 = chance).", "",
             sep.to_markdown(index=False), "",
             "## Choices and definitions", "",
             "- Context text: turn text from 4 words left to 2 words right of the value inside its turn (speaker prefix cut), the value itself replaced by its type tag `<<[TAG]>>` "
             "(masked, not dropped), other values of the dialogue masked by their type tags (step2.window_texts); bge-m3 (same encoder and cache as the value vectors), unit vectors.",
             "- v = unit((1 - alpha) v_value + alpha v_context), v_value = the adopted value vector (shape text for codes), used in the agglomerative step (average linkage, by stage-1 entity and value type) and in the fold (min size 2, cosine 1 - t, booking check).",
             "- t grid 0.4 (adopted), 0.3, 0.25, 0.2, 0.15, 0.1 with fold cosine 1 - t; the same grid for alpha 0 as control. Stage-1 entities are kept (only stage 2 is rerun).",
             "- Mixed-role cluster: two gold L2 attributes of the entity, each >= 3 mentions and >= 25% of the cluster. Fragmented attribute: majority (>= 50%, >= 3 mentions) of >= 2 clusters. "
             "S3 attributes: gold attributes with no cluster passing the scorer found rule (trace_v50 clusters checkpoint, attributes mostly in the scored entity). Scored entities = train / hotel / restaurant.",
             "- Selection on dev50: alpha > 0, K <= 1.5 x adopted, then most lenient found L2, fewest mixed clusters, fewest fragmented attributes, smallest alpha. dev50b scored with the same alpha and t.",
             "- Found L2 = G3 rule: v4.9 set (loop 1 + 2, human check) minus loop-1 finds lost plus new ones; columns replayed from the cached final columns (reconcile and duplicate check already applied); empty cached columns stay.",
             "- Gold only to score and trace. No MultiWOZ words or lists in the new code (the adopted value shapes of F_m2_t06_bk are unchanged).", ""]
    (OUT / "r1.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return best


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    enc = encoder()
    rows, wide = [], {}
    for s in SETS:
        d = ROOT / "results" / f"graph_v22_{s}"
        docs, _, _ = MN.load_shared(d)
        mt0 = pd.read_csv(d / "spans" / "mentions.csv", dtype=str, keep_default_na=False)
        spans, _, _ = units_of(mt0)
        cx = CV.context_vectors(spans, docs, enc).astype(np.float32)
        np.savez(OUT / f"ctx_vectors_{s}.npz", mention_id=mt0["mention_id"].astype(int).to_numpy(), x=cx)
        enc.save()
        ids = recluster(mt0, docs, enc, SETTINGS)
        enc.save()
        ctx = context_of(s)
        same = list(mt0["cluster_id"]) == ids[(0.0, 0.4)]
        print(f"{s}: alpha 0 reproduces cluster ids exactly: {same}", flush=True)
        if not same:
            raise SystemExit("alpha 0 differs from the adopted clustering")
        rows += reference_rows(s, ctx)
        for a, t in SETTINGS:
            row, _det = evaluate(s, a, t, ids[(a, t)], ctx)
            rows.append({**row, "alpha0_identical": same})
        wide[s] = (mt0, ids, docs, cx, ctx)
        out = mt0[["mention_id", "dialogue_id", "turn", "text", "entity", "gold_attr"]].copy()
        for (a, t), v in ids.items():
            out[f"cluster_a{a}_t{t}"] = v
        out.to_csv(OUT / f"clusters_{s}.csv", index=False, encoding="utf-8", lineterminator="\n")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "r1_alpha.csv", index=False, encoding="utf-8", lineterminator="\n")
    setting = select(df)
    print("chosen on dev50:", setting)
    best = write_report(df, setting, wide)
    write_examples(setting, wide)
    print(best)


if __name__ == "__main__":
    main()
