"""wf_v3.5 no-LLM checks (GT_V35_CONTRACT.md W5: T23 noise vote 2 of 3, T26 value types, T35 attribute counts, T38 extras).

python scripts/checks_v35.py --run results/graph_v22_dev50 --dir32 results/loop1_v32 --dir31 results/loop1_v31 \
    --levels results/loop1_v35/gt_levels.csv --out results/loop1_v35
Writes <out>/noise_vote.csv, value_types.csv, value_types_summary.md, attr_counts.csv, extras_by_level.csv, extras_table.md.
Waits up to --wait-min for the levels file; without it, only the level-1 / level-free parts run.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import checks_v35 as CK  # noqa: E402
from s1a import rules_labels as RL  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import v34_data as VD  # noqa: E402

POLL_S = 180


def wait_for(path, minutes):
    deadline = time.time() + minutes * 60
    while not path.exists() and time.time() < deadline:
        print(f"waiting for {path}", flush=True)
        time.sleep(POLL_S)
    return path.exists()


def prepare_extra(shared, data, out_dir, dir32):
    """Extra dict as score_entity leaves it: files read once, shared, other-entity gold values per entity."""
    extra = SR.load_extra(out_dir, dir32)
    extra["shared"] = shared
    extra["_other_gold"] = {ent: RL.other_gold_values(shared, ed) for ent, ed in data.items()}
    return extra


def extras_md(table, summary):
    cols = list(table.columns)
    lines = ["# wf_v3.5 extras by GT level", "",
             "Distinct final attributes per variant and kind (same entity + kind + label counted once).", "",
             "| variant | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    lines += [f"| {v} | " + " | ".join(str(int(r[c])) for c in cols) + " |" for v, r in table.iterrows()]
    return "\n".join(lines + [""])


def summary_md(s):
    lines = ["# wf_v3.5 value types (value_type_v35 vs frozen step2.value_type)", ""]
    lines += [f"- {k}: {v}" for k, v in s.items()]
    return "\n".join(lines + [""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--dir32", default="results/loop1_v32")
    ap.add_argument("--dir31", default="results/loop1_v31")
    ap.add_argument("--levels", default="results/loop1_v35/gt_levels.csv")
    ap.add_argument("--out", default="results/loop1_v35")
    ap.add_argument("--wait-min", type=float, default=40)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    have = wait_for(Path(a.levels), a.wait_min)
    levels = VD.read_gt_levels(a.levels) if have else None
    if not have:
        print(f"levels file {a.levels} still missing: running the level-free parts only", flush=True)
    shared, data = VD.load_all(a.run, a.dir32, a.dir31)
    extra = prepare_extra(shared, data, Path("results/loop1_v34"), Path(a.dir32))
    rules = SR.Rules.default()

    votes = pd.concat([CK.noise_vote_scores(ed, rules, extra, levels) for ed in data.values()], ignore_index=True)
    votes.to_csv(out / "noise_vote.csv", index=False)
    print(votes.to_string(index=False), flush=True)

    mentions = pd.concat([ed.mentions.assign(ent=ed.ent) for ed in data.values()], ignore_index=True)
    clusters, summary = CK.value_type_changes(mentions)
    clusters.to_csv(out / "value_types.csv", index=False)
    (out / "value_types_summary.md").write_text(summary_md(summary), encoding="utf-8")
    print(summary, flush=True)

    counts = pd.concat([CK.attr_counts(ed, v).assign(ent=ed.ent, variant=v)
                        for ed in data.values() for v in VD.VARIANTS], ignore_index=True)
    counts.to_csv(out / "attr_counts.csv", index=False)

    if levels is not None:
        extras = pd.concat([CK.extras_by_level(ed, v, levels, rules, extra).assign(ent=ed.ent, variant=v)
                            for ed in data.values() for v in VD.VARIANTS], ignore_index=True)
        extras.to_csv(out / "extras_by_level.csv", index=False)
        table = CK.extras_table(extras)
        (out / "extras_table.md").write_text(extras_md(table, summary), encoding="utf-8")
        print(table.to_string(), flush=True)


if __name__ == "__main__":
    main()
