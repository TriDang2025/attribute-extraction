"""wf_v3.7 part 1 (WF_V37_CONTRACT.md, W1): checks on the cached dev50 data under rules v1.1 at GT level 2. No LLM, no models.

python scripts/score_v37.py --dir33 ../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [same arguments as score_v36.py, with --out results/loop1_v37; --names36 results/loop1_v36 = where the v3.6 L2 name ratings are]
Writes <out>/{ceiling_dev50.md/.csv (T1), loss_dev50.md/.csv (T1), a_s012.md/.csv (T2), names_to_rate_l2_v37.csv +
names_to_rate_l2_v37_key.csv (T2, only when A s012 has unrated names), dup_columns.md/.csv (T3), train_stability.md (T4),
all_variants_v11.md/.csv (T5), exit_bar.md (T7)}. `exit_bar_from_dirs(args)` runs only the exit bar from a run directory
(--run) and a GT directory (--gt), so it can be rerun on dev50b or with the baseline. Rated v3.7 names are read from
names_l2_v37_rater{1,2}.csv in --out.
"""

import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import a_s012_v37 as AS  # noqa: E402
from s1a import ceiling_v37 as CE  # noqa: E402
from s1a import columns_v37 as CV  # noqa: E402
from s1a import exit_v37 as EX  # noqa: E402
from s1a import rules_groups as RG  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import stability_v37 as ST  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from score_v35 import score_levels  # noqa: E402
from score_v36 import (ROWS, all_variants_md, load_bundles, make_parser, write, write_csv)  # noqa: E402

LEVEL = 2
SETTING = "v1.1"
ROWS_V37 = list(ROWS)
ROWS_V37.insert(ROWS_V37.index(("range", "A")) + 1, "A s012")
A_RUNS = ("A r1", "A r2", "A s2")
DUP_VARIANTS = ("A r1", "A r2", "A s2", "A s012", "AE s012", "Oracle s012", "E1 s012")
T2_VARIANTS = ("A r1", "A r2", "A s2", "A s012", "AE s0", "AE s1", "AE s2", "AE s012")
SHORT = {"A r1": "A r1 (order 0)", "A r2": "A r2 (order 1)", "A s2": "A s2 (order 2)"}


def parser():
    ap = make_parser(Path("results/loop1_v37"), __doc__)
    ap.add_argument("--names36", type=Path, default=Path("results/loop1_v36"), help="folder with the v3.6 L2 name ratings")
    return ap


# ---- data

def load(a):
    """(shared, bundles {v34, v33, v36 (with A s012), oracle}, notes, gt table, repairs)."""
    repairs = []
    shared, bundles, notes = load_bundles(a, repairs)
    bundles["v36"] = AS.bundle_with_a_s012(shared, bundles["v34"], bundles["v36"])
    return shared, bundles, notes, VD.read_gt_levels(a.gt / "gt_levels.csv")


def levels(bundles, gt):
    """{name: bundle read at GT level 2}."""
    return {k: VD.with_level(b, gt, LEVEL) for k, b in bundles.items()}


def a_data(lev):
    """{ent: EntityData at L2} holding the variants of the v3.4 and v3.6 bundles (A r1 / r2 / s2 / s012, AE, C, ...)."""
    return AS.merge_variants(lev["v34"], lev["v36"])


def label_data(lev, label):
    """{ent: EntityData} of the bundle that holds variant `label` (A* in v34 / v36, Oracle*, E1*)."""
    key = "oracle" if label.startswith("Oracle") else "v33" if label.startswith("E1") else "v36" if label in ("A s2", "A s012") \
        or label.startswith("AE") else "v34"
    return lev[key]


# ---- the tables

def score_df(a, shared, bundles, gt, rated, setting=SETTING):
    """Score rows at L2 of every variant of every bundle under `setting` (a Rules string). names=l2rated settings read the
    combined v3.6 + v3.7 ratings."""
    extra = SR.load_extra(a.gt, a.dir32, l2_dir=a.names36)
    extra["gt_levels"] = gt
    extra["names_l2"] = rated
    return pd.concat([score_levels(setting, (LEVEL,), bundles["v34"], shared, extra, bundles["v33"]),
                      score_levels(setting, (LEVEL,), bundles["v36"], shared, extra),
                      score_levels(setting, (LEVEL,), bundles["oracle"], shared, extra)], ignore_index=True)


def noise_rows(bundles, gt, variants):
    extra = {"gt_levels": gt}
    return AS.noise_rows_for(bundles.values(), extra, variants)


def dup_all(lev, rules, labels=DUP_VARIANTS):
    return pd.concat([CV.dup_rows(ed, v, rules, {}) for v in labels for ed in label_data(lev, v).values() if v in ed.variants],
                     ignore_index=True)


def exit_runs(lev, ceil, noise, dup, rules, labels):
    """{label: EX.run_metrics} for the runs in `labels` (data of lev read at L2)."""
    runs = {}
    for v in labels:
        data = label_data(lev, v)
        found = set().union(*(EX.found_set(ed, v, rules, {}) for ed in data.values()))
        nz = noise[noise["variant"] == v][["noise_n", "noise_marked", "marked_n", "marked_noise"]].sum()
        runs[v] = EX.run_metrics(found, ceil, nz, CV.dup_summary(dup[dup["variant"] == v])["mean"])
    return runs


def write_exit(out, runs, notes):
    groups = {"A, 3 orders (A r1 / A r2 / A s2)": list(A_RUNS), "A s012 (vote)": ["A s012"]}
    table = EX.bar_rows(runs, groups)
    write(out / "exit_bar.md", EX.exit_md(table, runs, notes))
    return table


def exit_bar_from_dirs(a):
    """The exit bar alone, from the run directory `a.run` and the GT directory `a.gt` (plus the response folders of
    `a`): loads the bundles, scores the ceiling, A r1 / r2 / s2 and A s012 and writes <a.out>/exit_bar.md."""
    shared, bundles, notes, gt = load(a)
    lev = levels(bundles, gt)
    rules = CE.rules_v11(LEVEL)
    ceil = CE.ceiling_table(lev["v34"], LEVEL, rules)
    noise = noise_rows(bundles, gt, A_RUNS + ("A s012",))
    dup = dup_all(lev, rules, A_RUNS + ("A s012",))
    return write_exit(a.out, exit_runs(lev, ceil, noise, dup, rules, A_RUNS + ("A s012",)), notes)


def rated_ratings(a):
    return AS.read_l2_rated(a.names36, a.out)


def names_sheet(a, bundles, gt, rated):
    """Blind sheet of A s012's names that have no L2 rating (T2). Returns the number of unrated rows; leaves the files as
    they are when nothing is unrated (the ratings of an earlier sheet are then in `rated`)."""
    rows = AS.unrated_names(bundles["v36"], "A s012", rated, gt)
    if not len(rows):
        return 0
    tear_map = {k: v for k, v in json.loads(Path("config/tear_to_mwoz.json").read_text(encoding="utf-8")).items()
                if not k.startswith("_")}
    schema = json.loads((a.mwoz / "schema.json").read_text(encoding="utf-8"))
    slot_desc = {s["name"]: s["description"] for svc in schema for s in svc["slots"]}
    key_old = pd.read_csv(a.names36 / RN.L2_KEY_FILE, dtype=str, keep_default_na=False, encoding="utf-8")
    rater, key = AS.sheet_files(rows, key_old, tear_map, slot_desc)
    write_csv(rater, a.out / "names_to_rate_l2_v37.csv")
    write_csv(key, a.out / AS.NAMES_V37_KEY)
    return len(rater)


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    invalid = RN.invalid_runs(a.invalid)
    shared, bundles, notes, gt = load(a)
    rules = CE.rules_v11(LEVEL)
    lev = levels(bundles, gt)
    rated = rated_ratings(a)
    n_sheet = names_sheet(a, bundles, gt, rated)

    # T5: v1.1 re-score of the main table
    df = score_df(a, shared, bundles, gt, rated)
    df_l2r = score_df(a, shared, bundles, gt, rated, f"{SETTING},names=l2rated")
    df = df.assign(display=df["variant"].map(lambda v: SHORT.get(v, v)))
    write_csv(df, a.out / "all_variants_v11.csv")
    md_notes = [f"Note: {n}" for n in notes] + [
        "Rules v1.1 = rules v1 with noise_kind=mwoz (RULES_V1_1.md): the noise set is the MultiWOZ-only one (13 clusters at L2). "
        "A s012 = the 3-order vote of A r1 / A r2 / A s2."]
    write(a.out / "all_variants_v11.md", all_variants_md(
        df, invalid, md_notes, df_l2r, levels=(LEVEL,), rows=ROWS_V37, title="wf_v3.7 all variants, rules v1.1 at L2",
        rules="Rules v1.1 (noise = MultiWOZ-only noise set)"))

    # T1: ceiling and loss
    ceil = CE.ceiling_table(lev["v34"], LEVEL, rules)
    write_csv(ceil, a.out / "ceiling_dev50.csv")
    write(a.out / "ceiling_dev50.md", CE.ceiling_md(ceil))
    loss = CE.loss_table(a_data(lev), ceil, A_RUNS, rules)
    write_csv(loss, a.out / "loss_dev50.csv")
    write(a.out / "loss_dev50.md", CE.loss_md(loss, A_RUNS, ceil))

    # T3: duplicate columns
    dup = dup_all(lev, rules)
    write_csv(dup, a.out / "dup_columns.csv")
    write(a.out / "dup_columns.md", CV.dup_md(dup, DUP_VARIANTS))

    # T2: A s012 against AE s012
    nz = noise_rows(bundles, gt, T2_VARIANTS + ("Oracle s012", "E1 s012"))
    columns = {v: sum(CV.n_columns(ed, v) for ed in label_data(lev, v).values()) for v in T2_VARIANTS}
    t2 = AS.summary_rows(df, df_l2r, nz, columns, T2_VARIANTS)
    write_csv(t2, a.out / "a_s012.csv")
    sheet_note = (f"{n_sheet} names of A s012 have no L2 rating: blind sheet {a.out / 'names_to_rate_l2_v37.csv'} (+ key); "
                  "rated files names_l2_v37_rater{1,2}.csv go in the same folder." if n_sheet else
                  "Every name of A s012 is on a rated L2 sheet (v3.6 or v3.7).")
    write(a.out / "a_s012.md", AS.a_s012_md(t2, [sheet_note]))

    # T4: train stability
    ent = lev["v34"]["train"]
    two = ST.two_role(ent)
    ids = {c: [int(m) for m in g["mention_id"]] for c, g in ent.mentions.groupby("cluster_id") if c in two}
    agree = {"C": ST.agreement(ent, "C", rules, {}), "Oracle": ST.agreement(lev["oracle"]["train"], "Oracle", rules, {})}
    flips = {"C": ST.role_flips(ent, "C", two, ids), "Oracle": ST.role_flips(lev["oracle"]["train"], "Oracle", two, ids)}
    write(a.out / "train_stability.md", ST.stability_md(agree, flips, [
        f"Two-role train clusters of dev50 at L2: {len(two)}. Oracle splits each of them by gold role (so every Oracle side "
        "that is a gold role is an upper bound); C does not."]))

    # T7: exit bar
    labels = A_RUNS + ("A s012",)
    runs = exit_runs(lev, ceil, noise_rows(bundles, gt, labels), dup, rules, labels)
    write_exit(a.out, runs, notes)

    print(f"rows {len(df)}; unrated names of A s012 sent to the sheet: {n_sheet}")
    print(CE.ceiling_counts(ceil).to_string(index=False))
    print(t2.to_string(index=False))
    for n in notes:
        print("note:", n)


if __name__ == "__main__":
    main()
