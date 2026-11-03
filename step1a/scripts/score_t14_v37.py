"""wf_v3.7 T14: A (3 orders and the vote) on Step 1a v2.2 and v2.3, dev50 and dev50b, at L2 under rules v1.1. No LLM, no models.

python scripts/score_t14_v37.py --dir33 ../attribute-extraction-wf-v3.3/step1a/results/loop1_v33 --mwoz C:/Users/nguye/data/MultiWOZ_2.2
        [--dir37 results/loop1_v37/colab --out results/loop1_v37 --names36 results/loop1_v36 + the score_v36 arguments]
Runs (set, version): dev50 v2.2 = the existing A r1 / A r2 / A s2 (orders 0 / 1 / 2) + A s012 (results/graph_v22_dev50); the
other three read the batch responses <dir37>/responses/{ent}_a_{v23d50|v22d50b|v23d50b}_s{0,1,2}.jsonl
(s1a/run_data_v37.load_a). A run with no responses prints the missing jobs and still gets its ceiling.
Writes <out>/{t14.md, t14.csv, exit_bar_<set>_<version>.md, names_to_rate_l2_t14.csv, names_to_rate_l2_t14_key.csv}; rated names
are read from names_l2_t14_rater{1,2}.csv in <out> (rows of names_to_rate_l2_t14_key.csv; unrated = not right, counted).
Exit (e): A s012's right names (names=l2rated, summed over the entities) > the right names of the baseline's union
(<out>/baseline_v37.csv, version "union", same set); "pending the baseline" until that file exists.
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
from s1a import names_l2 as NL  # noqa: E402
from s1a import noise_v36 as NV  # noqa: E402
from s1a import rules_names as RN  # noqa: E402
from s1a import run_data_v37 as RD  # noqa: E402
from s1a import score_rules as SR  # noqa: E402
from s1a import stability_v37 as ST  # noqa: E402
from s1a import t14_v37 as T14  # noqa: E402
from s1a import v34_data as VD  # noqa: E402
from s1a import v36_data as V36  # noqa: E402
from score_v35 import score_levels  # noqa: E402
from score_v36 import make_parser, write, write_csv  # noqa: E402

LEVEL = 2
SETTING = "v1.1,names=l2rated"
GT = {"dev50": "results/loop1_v35", "dev50b": "results/loop1_v37/dev50b/gt"}
# (set, version) -> (run dir, key of the run in the batch manifest or None = the existing dev50 v2.2 data)
RUNS = {("dev50", "v2.2"): ("results/graph_v22_dev50", None), ("dev50", "v2.3"): ("results/graph_v23_dev50", "v23d50"),
        ("dev50b", "v2.2"): ("results/graph_v22_dev50b", "v22d50b"), ("dev50b", "v2.3"): ("results/graph_v23_dev50b", "v23d50b")}
OLD_ORDERS, NEW_ORDERS, VOTE = ("A r1", "A r2", "A s2"), ("A s0", "A s1", "A s2"), "A s012"


def parser():
    ap = make_parser(Path("results/loop1_v37"), __doc__)
    ap.add_argument("--dir37", type=Path, default=Path("results/loop1_v37/colab"), help="v3.7 Colab batch (responses/)")
    ap.add_argument("--names36", type=Path, default=Path("results/loop1_v36"))
    return ap


def only(bundle, labels):
    """bundle ({ent: EntityData}) keeping only the variants in `labels`."""
    return {e: replace(ed, variants={k: v for k, v in ed.variants.items() if k in labels}) for e, ed in bundle.items()}


def missing_jobs(dir37, run):
    """["<job>", ...] of the A and split jobs of manifest run `run` that have no response file in dir37/responses."""
    out = []
    for ent in ("train", "hotel", "restaurant"):
        a, split = RD.batch_jobs(dir37, run, ent)
        out += [j["job"] for j in a + split if not (Path(dir37) / "responses" / f"{j['job']}.jsonl").exists()]
    return out


def load_old(a, repairs):
    """(shared, bundle with A r1 / A r2 / A s2 / A s012, notes) of dev50 v2.2: the v3.4 and v3.6 bundles, voted like AE s012."""
    shared, data = VD.load_all(a.run, a.dir32, a.dir31, repairs)
    data36, notes = V36.load_v36(shared, data, a.dir36, a.dir32, a.dir31, repairs)
    bundle = AS.add_a_s012(shared, AS.merge_variants(data, data36))
    return shared, only(bundle, OLD_ORDERS + (VOTE,)), notes


def load_new(a, run_dir, run_key, repairs):
    shared, data = RD.entity_data(run_dir)
    bundle, notes = RD.load_a(shared, data, a.dir37, run_key, repairs)
    return shared, only(bundle, NEW_ORDERS + (VOTE,)), notes


def check_ids(bundle, gt):
    """Note when mentions of the run have no row in the GT table (a run whose mention ids differ from the GT's)."""
    ids = set(gt["mention_id"].astype(int))
    miss = sum(int(m) not in ids for ed in bundle.values() for m in ed.mentions["mention_id"])
    return [f"{miss} mentions of the run have no GT row: check that the run and the GT dir belong together"] if miss else []


def baseline_right(out, set_name):
    """Right names of the baseline union for `set_name` (baseline_v37.csv), or None when the file or the set is missing."""
    p = Path(out) / "baseline_v37.csv"
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d = d[(d["set"] == set_name) & (d["version"] == "union")]
    return int(d["right"].sum()) if len(d) else None


def exit_part(set_name, version, lev, labels, scores, noise, dup, ceil, rules, out):
    """exit_bar_<set>_<version>.md of the run: A orders as a range and the vote; (e) from the baseline file."""
    runs = {}
    for v in labels:
        found = set().union(*(EX.found_set(ed, v, rules, {}) for ed in lev.values()))
        nz = noise[noise["variant"] == v][["noise_n", "noise_marked", "marked_n", "marked_noise"]].sum()
        runs[v] = EX.run_metrics(found, ceil, nz, CV.dup_summary(dup[dup["variant"] == v])["mean"])
    orders = [v for v in labels if v != VOTE]
    groups = {f"A, {len(orders)} orders ({' / '.join(orders)})": orders, "A s012 (vote)": [VOTE]}
    table = EX.bar_rows(runs, groups)
    bl = baseline_right(out, set_name)
    right = int(scores.loc[scores["variant"] == VOTE, "name_right"].sum())
    verdict = EX.exit_e(right, bl)
    cell = "pending the baseline" if verdict is None else f"{'pass' if verdict else 'FAIL'}: A s012 right names {right} vs baseline union {bl}"
    write(Path(out) / f"exit_bar_{set_name}_{version}.md", EX.exit_md(
        table, runs, [f"(e): A s012's right names (names L2 rated, summed over entities) must be strictly more than the baseline "
                      f"union's right names of the same set (baseline_v37.csv)."],
        e={name: cell for name in groups}, title=f"wf_v3.7 exit bar, A on {set_name} {version} (L2, rules v1.1)"))


def names_sheet(a, raw, gts, rated):
    """Blind sheet of the A names of the runs in `raw` {(set, version): bundle} that have no L2 rating; row ids continue
    after the largest id of the v3.6 / v3.7 keys. Returns the number of rows; leaves existing t14 files alone when raters
    already answered."""
    parts = []
    for (s, v), bundle in raw.items():
        for label in {l for ed in bundle.values() for l in ed.variants if not l.endswith("namemerge")}:
            parts.append(AS.unrated_names(only(bundle, (label,)), label, rated, gts[s]))
    rows = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if not len(rows):
        return 0
    # first round whose answers are not in yet (a round with rater files is done: its names are in `rated`)
    sfx = next((r for r in AS.NAMES_T14_ROUNDS if not all((a.out / f).exists() for f in AS.t14_files(r)[0])), None)
    if sfx is None:
        print("names: every t14 round is rated; unrated names remain, add a round to AS.NAMES_T14_ROUNDS")
        return 0
    _, key_file, sheet_file = AS.t14_files(sfx)
    tear_map = {k: v for k, v in json.loads(Path("config/tear_to_mwoz.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
    schema = json.loads((a.mwoz / "schema.json").read_text(encoding="utf-8"))
    slot_desc = {s["name"]: s["description"] for svc in schema for s in svc["slots"]}
    done = [a.out / AS.t14_files(r)[1] for r in AS.NAMES_T14_ROUNDS[:AS.NAMES_T14_ROUNDS.index(sfx)]]
    keys = [pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8") for p in
            (a.names36 / RN.L2_KEY_FILE, a.out / AS.NAMES_V37_KEY, *done) if p.exists()]
    rater, key = AS.sheet_files(rows, pd.concat(keys, ignore_index=True), tear_map, slot_desc)
    write_csv(rater, a.out / sheet_file)
    write_csv(key, a.out / key_file)
    return len(rater)


def main():
    a = parser().parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rules = CE.rules_v11(LEVEL)
    rated = AS.read_l2_rated(a.names36, a.out)
    gts = {s: VD.read_gt_levels(Path(p) / "gt_levels.csv") for s, p in GT.items()}
    tables, ceils, raw, missing, notes = [], {}, {}, [], []
    repairs = []
    for (s, v), (run_dir, key) in RUNS.items():
        gt = gts[s]
        try:
            shared, bundle, n = load_old(a, repairs) if key is None else load_new(a, Path(run_dir), key, repairs)
        except FileNotFoundError as err:
            notes.append(f"{s} {v}: run not readable yet ({err})")
            print(notes[-1])
            continue
        notes += [f"{s} {v}: {x}" for x in n if "skipped" not in x]
        notes += [f"{s} {v}: {x}" for x in check_ids(bundle, gt)]
        gone = missing_jobs(a.dir37, key) if key else []
        if gone:
            missing.append(f"{s} {v} ({key}): {len(gone)} jobs without a response, e.g. {', '.join(gone[:3])}")
            print(missing[-1])
        lev = VD.with_level(bundle, gt, LEVEL)
        ceil = CE.ceiling_table(lev, LEVEL, rules)
        ceils[(s, v)] = ceil
        orders = OLD_ORDERS if key is None else NEW_ORDERS
        labels = [l for l in (*orders, VOTE) if all(l in ed.variants for ed in bundle.values())]
        if not labels:
            continue
        raw[(s, v)] = bundle
        extra = SR.load_extra(a.gt, a.dir32)
        extra["gt_levels"], extra["names_l2"] = gt, rated
        scores = score_levels(SETTING, (LEVEL,), only(bundle, labels), shared, extra)
        noise = NV.noise_l2_rows(bundle, {"gt_levels": gt}, labels)
        dup = pd.concat([CV.dup_rows(ed, l, rules, {}) for l in labels for ed in lev.values()], ignore_index=True)
        cols = {l: sum(CV.n_columns(ed, l) for ed in lev.values()) for l in labels}
        agree = (RN.agreement(ST.with_seed_labels(lev["train"], orders), rules, {}) if all(o in labels for o in orders) else None)
        tables.append(T14.run_rows(s, v, orders, VOTE, scores, noise, cols, dup, ceil, agree))
        exit_part(s, v, lev, labels, scores, noise, dup, ceil, rules, a.out)
    rows = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame(columns=T14.ROW_COLS)
    n_sheet = names_sheet(a, raw, gts, rated) if raw else 0
    if n_sheet:
        notes.append(f"{n_sheet} A names have no L2 rating: blind sheet in {a.out} (names_to_rate_l2_t14[_2..].csv + key); "
                     "rated files names_l2_t14[_2..]_rater{1,2}.csv go in the same folder.")
    write_csv(rows, a.out / "t14.csv")
    decision = T14.decide(rows)
    write(a.out / "t14.md", T14.t14_md(rows, decision, ceils, missing, notes))
    print(f"rows {len(rows)}; ceilings {len(ceils)}; names sheet {n_sheet} rows")
    print(decision[2])


if __name__ == "__main__":
    main()
