"""wf_v5.0 G3 (S3): replay the context split (s1a/ctxsplit_v50.py) on the cached wf_v4.6 Y3 Step 3 outputs. Variants are chosen on
dev50 only; dev50b is scored with the same settings, unchanged. CPU (bge-m3 on the left contexts, cached in step1a/data/cache).

python scripts/g3_ctxsplit_v50.py  -> results/wf_v50/g3/ctxsplit/{g3s3.md, g3s3.csv, columns_<variant>_<set>.csv,
                                                                  <variant>/<set>/final_columns.json}
Scoring = scripts/g3_nojoin_v50.score (found rule of the scorer on the loop-1 groups; column kinds gold / dup / other).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import g3_nojoin_v50 as G3  # noqa: E402
import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v49 as M49  # noqa: E402
from run import encoder  # noqa: E402
from s1a import ctxsplit_v50 as CS  # noqa: E402
from s1a import mentions as MN  # noqa: E402

OUT = G3.OUT / "ctxsplit"
VARIANTS = {"all": (2, 99, 0), "two_parts": (2, 2, 0), "big40": (2, 99, 40)}   # (min_parts, max_parts, min_size) of the reassigned clusters


def context_vectors(set_name, mt, enc):
    docs, _, _ = MN.load_shared(ROOT / "results" / f"graph_v22_{set_name}")
    ctx = {i: CS.left_context(docs[r.dialogue_id].text, MN.turn_bounds(docs[r.dialogue_id], int(r.turn))[0], int(r.char_start))
           for i, r in zip(mt.index, mt.itertuples())}
    uniq = sorted(set(ctx.values()))
    x = np.asarray(enc.encode(uniq), dtype=float)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    by_text = dict(zip(uniq, x))
    return {i: by_text[t] for i, t in ctx.items()}, ctx


def run_set(set_name, enc):
    mt, labels, emap, final, step3 = G3.load(set_name)
    v49, gold = M49.found_v49(set_name)
    gold_by_ent = {}
    for a, e in gold.items():
        gold_by_ent.setdefault(e, []).append(a)
    cols = json.loads((step3 / "columns.json").read_text(encoding="utf-8"))[M46.RUN_OF[set_name]]
    vec, _ctx = context_vectors(set_name, mt, enc)
    f0, c0 = G3.score(final, emap, mt, labels, gold_by_ent)
    rows, col_rows = [], [{**r, "variant": "v4.9"} for r in c0]
    for name, (lo, hi, size) in VARIANTS.items():
        after = {k: CS.apply(final[k], cols[k]["parts"], CS.reassign(cols[k]["parts"], vec, lo, hi, size)) for k in final}
        d = OUT / name / set_name
        d.mkdir(parents=True, exist_ok=True)
        (d / "final_columns.json").write_text(json.dumps({M46.RUN_OF[set_name]: after}, indent=1, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
        f1, c1 = G3.score(after, emap, mt, labels, gold_by_ent)
        col_rows += [{**r, "variant": name} for r in c1]
        k0, k1 = pd.Series([r["kind"] for r in c0]).value_counts(), pd.Series([r["kind"] for r in c1]).value_counts()
        rows.append({"set": set_name, "variant": name, "found_span_loop1": f"{len(f0)} -> {len(f1)}",
                     "found_L2": f"{len(v49['loop2'])} -> {len((v49['loop2'] - (f0 - f1)) | (f1 - f0))}",
                     "gained": "; ".join(sorted(f1 - f0)), "lost": "; ".join(sorted(f0 - f1)),
                     "cols_total": f"{len(c0)} -> {len(c1)}",
                     **{f"cols_{k}": f"{k0.get(k, 0)} -> {k1.get(k, 0)}" for k in ("gold", "dup", "other")},
                     "new_wrong_cols": int(k1.get("dup", 0) + k1.get("other", 0) - k0.get("dup", 0) - k0.get("other", 0))})
    pd.DataFrame(col_rows).to_csv(OUT / f"columns_{set_name}.csv", index=False, encoding="utf-8", lineterminator="\n")
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    enc = encoder()
    df = pd.DataFrame([r for s in G3.SETS for r in run_set(s, enc)])
    enc.save()
    df.to_csv(OUT / "g3s3.csv", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / "g3s3.md").write_text("# wf_v5.0 G3: context split of two-role clusters (S3), replay on cached outputs\n\n"
                                 + df.to_markdown(index=False) + "\n", encoding="utf-8", newline="\n")
    print(df.T.to_string())


if __name__ == "__main__":
    main()
