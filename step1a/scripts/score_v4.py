"""wf_v4 Step 4 scorer CLI (skeleton): one CSV row per canonical schema file, full GT and reachable-only GT.

python scripts/score_v4.py --set dev50 --out results/wf_v4/scores/x.csv schema1.json schema2.json
python scripts/score_v4.py --self-check            # GT designs against the GT -> results/wf_v4/gt/self_check.csv
Options: --gt gt/schema_gt_v1.yaml, --handover handover, --gt-dir results/wf_v4/gt (reachable_<set>.csv), --sets dev50,dev50b (self-check).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import step4_gt as G  # noqa: E402
from s1a import step4_score as S  # noqa: E402

GT_LEVELS = {"dev50": "results/loop1_v35/gt_levels.csv", "dev50b": "results/loop1_v37/dev50b/gt/gt_levels.csv"}


def load(gt_path, gt_dir, sets):
    gt = G.load_gt(gt_path)
    for s in sets:
        G.attach_reachable(gt, s, G.load_reachable(Path(gt_dir) / f"reachable_{s}.csv"))
    return gt


def score_rows(name, schema, gt, set_name, handover):
    mapping = S.map_columns(schema, set_name, handover, GT_LEVELS[set_name], gt)
    return [{"schema": name, **S.flat(S.score(schema, gt, set_name, ro, mapping))} for ro in (False, True)]


def write_rows(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("schemas", nargs="*", type=Path)
    ap.add_argument("--set", default="dev50")
    ap.add_argument("--sets", default="dev50,dev50b")
    ap.add_argument("--gt", type=Path, default=Path("gt/schema_gt_v1.yaml"))
    ap.add_argument("--gt-dir", type=Path, default=Path("results/wf_v4/gt"))
    ap.add_argument("--handover", type=Path, default=Path("handover"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    sets = a.sets.split(",") if a.self_check else [a.set]
    gt = load(a.gt, a.gt_dir, sets)
    rows = []
    if a.self_check:
        for d in G.all_designs(gt):
            canon = G.to_canonical(gt, d)
            for s in sets:
                rows += [{"schema": d["name"], **S.flat(S.score(canon, gt, s, ro))} for ro in (False, True)]
        a.out = a.out or a.gt_dir / "self_check.csv"
    else:
        for p in a.schemas:
            schema = json.loads(p.read_text(encoding="utf-8"))
            rows += score_rows(p.name, schema, gt, a.set, a.handover)
    if not a.out:
        sys.exit("--out is required")
    write_rows(a.out, rows)
    print(f"{len(rows)} rows -> {a.out}")


if __name__ == "__main__":
    main()
