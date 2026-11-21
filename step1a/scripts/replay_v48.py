"""wf_v4.8 W2: replay the loop-2 precision fixes (s1a/loop2_fix_v48.py) on the cached v4.7 run-1 loop-2 output. No LLM, no gold.

python scripts/replay_v48.py [--sets dev50,dev50b] [--tau-sweep]
  -> results/wf_v48/w2/<set>/changes.csv           every change of every fix: alone (variant = the fix) and with all fixes on (variant all)
     results/wf_v48/w2/<set>/new_columns.csv       the new columns with all fixes on (status, mix flag, values, joins, dropped values)
     results/wf_v48/w2/<set>/columns_l2.json, merged_columns.json, attributes.json, a2.columns.json   loop-2 outputs with all fixes on
                                                   (same formats as loop2_v46; a2.columns.json = the Step 4 input for W3)
     results/wf_v48/w2/tau_sweep.csv               --tau-sweep: loop1_embed alone per cosine threshold (tau is set on dev50)
Reads results/wf_v47/z4/run1/<set>/ (loop-1 columns step3/, loop-2 loop2/) and results/graph_v22_<set>/spans/mentions.csv (loop-1 values).
Config: config/wf_v48_loop2.json. bge-m3 (CPU, data/cache) embeds the normalized values.
"""
import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from s1a import batch_v4 as B  # noqa: E402
from s1a import loop2_fix_v48 as F  # noqa: E402
from s1a import loop2_v46 as L  # noqa: E402
from s1a import nov16_v41 as NV  # noqa: E402
from s1a import step3_v44 as S3_44  # noqa: E402

RUNS = ROOT / "results" / "wf_v47" / "z4" / "run1"
OUT = ROOT / "results" / "wf_v48" / "w2"
CONFIG = ROOT / "config" / "wf_v48_loop2.json"
RUN_OF = {"dev50": "c_n50", "dev50b": "c_n50b"}
TAUS = (0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)


def inputs(set_name):
    run_dir = RUNS / set_name
    finals = B.read_json(run_dir / "step3" / "scores" / "final_columns.json")[RUN_OF[set_name]]
    l2 = run_dir / "loop2"
    clusters = {c["id"]: c for c in B.read_json(l2 / "evidence" / "clusters.json")}
    mt = pd.read_csv(ROOT / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False,
                     usecols=["mention_id", "norm_value"])
    nv = dict(zip(mt["mention_id"].astype(int), mt["norm_value"]))
    loop1 = {e: {c["name"]: Counter(nv[int(i)] for i in c["mention_ids"] if nv.get(int(i))) for c in cs} for e, cs in finals.items()}
    return run_dir, finals, B.read_json(l2 / "columns_l2.json"), clusters, loop1


def similarity(encoder, texts):
    """sim(a, b) -> bge-m3 cosine of two normalized strings, from one batch encode of `texts`."""
    texts = sorted(set(texts) - {""})
    vec = dict(zip(texts, encoder.encode(texts)))
    return lambda a, b: 1.0 if a == b else float(np.dot(vec[a], vec[b]))


def all_texts(columns_l2, clusters, loop1):
    vals = {m["norm_value"] for rows in columns_l2.values() for r in rows for cid in r["clusters"] for m in clusters[cid]["mentions"]}
    vals |= {v for cols in loop1.values() for vs in cols.values() for v in vs}
    return [F.norm(v) for v in vals]


def only(cfg, step):
    return {k: {**v, "on": k == step} for k, v in cfg.items() if k in F.STEPS}


def replay(columns_l2, clusters, loop1, sim, cfg):
    """({entity: working columns}, [(entity, step, change)])."""
    cols, changes = {}, []
    for ent, rows in columns_l2.items():
        cols[ent], log = F.apply(copy.deepcopy(rows), clusters, loop1.get(ent, {}), sim, cfg)
        changes += [(ent, step, ch) for step, chs in log.items() for ch in chs]
    return cols, changes


def kept_clusters(cols, clusters):
    """The evidence clusters with only the mentions their (fixed) column kept."""
    out = dict(clusters)
    for cs in cols.values():
        for c in cs:
            keep = {m["mention_id"] for m in c["mentions"]}
            for cid in c["clusters"]:
                out[cid] = {**clusters[cid], "mentions": [m for m in clusters[cid]["mentions"] if m["mention_id"] in keep]}
    return out


def write_outputs(set_name, run_dir, finals, cols, clusters, d):
    final = {e: [F.to_row(c) for c in cs] for e, cs in cols.items()}
    filt = kept_clusters(cols, clusters)
    review = B.read_json(run_dir / "loop2" / "step1b" / "review.json")
    merged = L.merged_columns(finals, review, final, filt)
    a_file = S3_44.a_llama44_file(RUN_OF[set_name], run_dir / "step3")
    pre = a_file.with_name("a.premerge.columns.json")
    a2 = NV.a2_columns(B.read_json(pre if pre.exists() else a_file), final, filt)[0]
    for name, doc in (("columns_l2.json", final), ("merged_columns.json", merged), ("a2.columns.json", a2),
                      ("attributes.json", {e: [c["name"] for c in cs] for e, cs in merged.items()})):
        B.write_json(d / name, doc)
    rows = [{"set": set_name, "entity": e, "name": r["name"], "status": r["status"], "mix": r["mix"], "n_mentions": r["n_mentions"],
             "top_values": " | ".join(r["top_values"]), "joined": " | ".join(r["joined"]), "duplicate_of": " | ".join(r["duplicate_of"]),
             "dropped_values": " | ".join(f"{v} x{k}" for v, k in r["dropped_values"].items())} for e, rs in final.items() for r in rs]
    pd.DataFrame(rows).to_csv(d / "new_columns.csv", index=False, encoding="utf-8", lineterminator="\n")
    return rows


def run_set(set_name, cfg, encoder, out=OUT):
    run_dir, finals, columns_l2, clusters, loop1 = inputs(set_name)
    sim = similarity(encoder, all_texts(columns_l2, clusters, loop1))
    d = Path(out) / set_name
    d.mkdir(parents=True, exist_ok=True)
    changes = []
    for step in F.STEPS:
        changes += [(step, *c) for c in replay(columns_l2, clusters, loop1, sim, only(cfg, step))[1]]
    cols, ch_all = replay(columns_l2, clusters, loop1, sim, cfg)
    changes += [("all", *c) for c in ch_all]
    pd.DataFrame(changes, columns=["variant", "entity", "step", "change"]).to_csv(d / "changes.csv", index=False, encoding="utf-8", lineterminator="\n")
    return changes, write_outputs(set_name, run_dir, finals, cols, clusters, d)


def tau_sweep(sets, cfg, encoder, out=OUT):
    rows = []
    for s in sets:
        _, _, columns_l2, clusters, loop1 = inputs(s)
        sim = similarity(encoder, all_texts(columns_l2, clusters, loop1))
        for tau in TAUS:
            c = only(cfg, "loop1_embed")
            c["loop1_embed"]["tau"] = tau
            ch = replay(columns_l2, clusters, loop1, sim, c)[1]
            rows.append({"set": s, "tau": tau, "n_changed": len(ch), "changes": " ; ".join(f"{e}: {x}" for e, _, x in ch)})
    df = pd.DataFrame(rows)
    Path(out).mkdir(parents=True, exist_ok=True)
    df.to_csv(Path(out) / "tau_sweep.csv", index=False, encoding="utf-8", lineterminator="\n")
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", default="dev50,dev50b")
    ap.add_argument("--tau-sweep", action="store_true")
    a = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    sets = [s.strip() for s in a.sets.split(",")]
    from run import encoder as make_encoder
    enc = make_encoder()
    try:
        if a.tau_sweep:
            print(tau_sweep(sets, cfg, enc).to_string())
            return
        for s in sets:
            changes, rows = run_set(s, cfg, enc)
            print(f"== {s}")
            for c in changes:
                print("  ", c)
            print(pd.DataFrame(rows)[["entity", "name", "status", "mix", "n_mentions", "top_values", "joined", "dropped_values"]].to_string())
    finally:
        enc.save()


if __name__ == "__main__":
    main()
