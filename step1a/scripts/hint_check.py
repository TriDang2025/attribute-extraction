"""Offline check of the merge-hint modes (string, window, filtered) on the pilot entities.

python scripts/hint_check.py --run results/graph_v22_dev50 --ents train,hotel,restaurant --out results/loop1_v31 [--encode]
  --encode builds <run>/spans/window_vectors.npz (bge-m3 of each mention's context; only if missing; one writer
  of the bge-m3 cache at a time). -> <out>/hints.csv: entity, mode, cluster_id, other, rank, cosine_pct, same_class
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from s1a import hints as H  # noqa: E402
from s1a import mentions as MN  # noqa: E402
from s1a import paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--ents", default="train,hotel,restaurant")
    ap.add_argument("--out", default="results/loop1_v31")
    ap.add_argument("--encode", action="store_true")
    a = ap.parse_args()
    run, out = paths.ROOT / a.run, paths.ROOT / a.out
    export = MN.load(run / "spans")
    npz = run / "spans" / "window_vectors.npz"
    if a.encode and not npz.exists():
        from run import encoder
        enc = encoder()
        H.save_window(npz, export.ids, H.encode_windows(export, enc))
        enc.save()
        print(f"wrote {npz}", flush=True)
    ids, wx = H.load_window(npz)
    if not np.array_equal(ids, export.ids):
        raise SystemExit("window_vectors.npz ids differ from the export's ids; rebuild with --encode")
    maj = H.majority_classes(export.mentions)
    rows = []
    for gold in a.ents.split(","):
        ent = PIN.find_pilot_entity(export.mentions, gold)
        for mode in H.MODES:
            hints = H.merge_hints(export, ent, mode, wx, k=3)
            rows += [dict(entity=gold, mode=mode, cluster_id=c, other=h["other"], rank=h["rank"],
                          cosine_pct=round(h["pct"], 1), same_class=H.same_class(c, h["other"], maj))
                     for c, lst in hints.items() for h in lst]
    df = pd.DataFrame(rows, columns=["entity", "mode", "cluster_id", "other", "rank", "cosine_pct", "same_class"])
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "hints.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(f"{'entity':11}{'mode':10}{'hints':>6}{'same':>6}{'prec':>7}{'top1':>7}  top hubs")
    for (gold, mode), g in df.groupby(["entity", "mode"], sort=False):
        top1 = g[g["rank"] == 1]
        hubs = ", ".join(f"{c}:{n}" for c, n in Counter(g["other"]).most_common(3))
        print(f"{gold:11}{mode:10}{len(g):6}{int(g['same_class'].sum()):6}"
              f"{g['same_class'].mean() if len(g) else float('nan'):7.2f}"
              f"{top1['same_class'].mean() if len(top1) else float('nan'):7.2f}  {hubs}")
    print(f"wrote {out / 'hints.csv'}")


if __name__ == "__main__":
    main()
