"""wf_v5.1 R0: score taxi as its own entity (s1a/taxi_v51.py), rescore v5.0 before (switch off) and after (on), dev50 and dev50b. CPU only.

python scripts/r0_taxi_v51.py [--work DIR]  -> results/wf_v51/r0/{r0.md, r0.csv}; scratch (score maps, loop-2 files) in --work
Found L2 = scripts/g3_nojoin_v50 formula (the v4.9 set = loop 1 + 2 + human check, minus the loop-1 span finds a change loses, plus new ones) on the
v5.0 final columns (context split, variant big40: results/wf_v50/g3/ctxsplit/big40/<set>/final_columns.json). With the taxi rule the taxi
attributes of the base set are recomputed on the predicted entity matched to taxi (loop 1 + 2 span finds, mainclaim_v41.run in a scratch dir);
the human check never credited a taxi attribute (fails fast if it did). Step 4: scripts/g5_score_v50.main run twice with its OUT pointed at the
scratch dir, the taxi rule off / on; off must equal results/wf_v50/g5/scores.csv.
Other workers: `found_l2(final_columns, set_name, taxi_rule=True|False)` -> set of found gold attributes; wrap any other call of the main-claim
scorers (mainclaim_v41 / v46) in `rule(True)` to score taxi as an entity.
"""
import argparse
import contextlib
import io
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import g3_nojoin_v50 as G3  # noqa: E402
import g5_score_v50 as G5  # noqa: E402
import mainclaim_v41 as MCS  # noqa: E402
import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v47 as M47  # noqa: E402
import mainclaim_v48 as M48  # noqa: E402
import mainclaim_v49 as M49  # noqa: E402
import step4_score_v48 as S48  # noqa: E402
from s1a import mainclaim_v41 as MC  # noqa: E402
from s1a import step4_inputs as I  # noqa: E402
from s1a import taxi_v51 as T  # noqa: E402

OUT = ROOT / "results" / "wf_v51" / "r0"
BIG40 = ROOT / "results" / "wf_v50" / "g3" / "ctxsplit" / "big40"
SETS = G3.SETS
RULE = ("taxi gold attributes are scored on the predicted entity that the usual entity match (the GT entity most of its mentions belong to) "
        "maps to taxi, with the same purity 0.6 / coverage 0.10 found rule; for TEAR, a column whose header domain is taxi counts for taxi.")
STEP4_METRICS = ("table_f1", "grouping_f1", "gt_columns_placed")
WORK = OUT / "work"


@contextmanager
def rule(on=True):
    """Taxi rule on: taxi_v51.taxi_scoring + mainclaim_v46 scores a predicted entity matched to taxi. on=False changes nothing (= v5.0)."""
    with T.taxi_scoring(on), patch.object(M46, "GOLD_ENTITIES", (*M46.GOLD_ENTITIES, T.TAXI) if on else M46.GOLD_ENTITIES):
        yield


def final_v50(set_name):
    """The v5.0 final columns of a set (context split big40), {entity key: columns}."""
    return json.loads((BIG40 / set_name / "final_columns.json").read_text(encoding="utf-8"))[M46.RUN_OF[set_name]]


def gold_lists(set_name, on):
    with rule(on):
        return MC.load_set(set_name)[3]


def span_marks(set_name, final, on, work=None):
    """{source: set of gold attributes found by span} of loop 1 and loop 1 + 2 for `final` (mainclaim_v41.run in a scratch dir, no human
    answers). Loop 2 = the v4.7 run-1 new-column clusters, as results/wf_v48/w1."""
    d = Path(work or WORK) / ("on" if on else "off") / set_name
    d.mkdir(parents=True, exist_ok=True)
    _, _, emap, _, _ = G3.load(set_name)
    with rule(on):
        l2 = M47.loop2_file(M48.RUN)(None, emap, d)
        MCS.run(set_name, l2, None, MCS.SPANS, d.parent, handover=M46.handover(final, emap))
    with patch.object(M49, "W1", d.parent):
        marks, _ = M49.found_marks(set_name)
    return {s: set(m) for s, m in marks.items() if s in ("loop1", "loop2")}


def found_l2(final_columns, set_name, taxi_rule=False, work=None, detail=False):
    """Set of gold L2 attributes found on `set_name` (found L2 with human check, as wf_v5.0 G3) for `final_columns` ({entity key: columns}, the
    Step 3 final columns of the run). taxi_rule False = the v5.0 number exactly; True = taxi scored as its own entity. The gold count
    (len of the gold list) is the same either way. detail=True: (found, loop-1 span finds of `final_columns`, column rows of G3.score)."""
    v49, _ = M49.found_v49(set_name)
    mt, labels, emap, cached, _ = G3.load(set_name)
    gold_off, gold_on = gold_lists(set_name, False), gold_lists(set_name, True)
    taxi = set(T.moved_attrs(gold_off, gold_on))
    base = set(v49["loop2"])
    if taxi_rule:
        human_taxi = (base - span_marks(set_name, cached, False, work)["loop2"]) & taxi
        if human_taxi:
            raise ValueError(f"{set_name}: the human check credits taxi attributes {sorted(human_taxi)}; they need an entity check first")
        base = (base - taxi) | (span_marks(set_name, cached, True, work)["loop2"] & taxi)
    gold_by_ent = gold_on if taxi_rule else gold_off
    with rule(taxi_rule):
        f_ref = G3.score(cached, emap, mt, labels, gold_by_ent)[0]
        f_new, rows_new = G3.score(final_columns, emap, mt, labels, gold_by_ent)
    found = T.adjust(base, f_ref, f_new)
    return (found, f_new, rows_new) if detail else found


def taxi_mentions(set_name):
    """[(run entity key, matched GT entity, share, GT-taxi mentions in it)] of the predicted entities that hold taxi mentions."""
    _, _, emap, _, _ = G3.load(set_name)
    gt = pd.read_csv(ROOT / I.GT_LEVELS[set_name], dtype=str, keep_default_na=False, usecols=["mention_id", "ent_L2"])
    n = pd.read_csv(ROOT / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv", dtype=str, keep_default_na=False,
                    usecols=["mention_id", "entity"]).merge(gt, on="mention_id").query("ent_L2 == 'taxi'").groupby("entity").size()
    return [(k, ent, share, int(n.get(st, 0))) for k, (st, ent, share) in emap.items() if n.get(st, 0)]


def step4(on, work):
    """Step 4 scores (g5_score_v50.main with OUT = scratch) with the taxi rule off / on: scores DataFrame."""
    d = Path(work) / ("on" if on else "off") / "g5"
    with rule(on), patch.object(G5, "OUT", d), contextlib.redirect_stdout(io.StringIO()):
        G5.main()
    return pd.read_csv(d / "scores.csv", keep_default_na=False)


def step4_means(df, variant="ARMg"):
    """{set: {metric: mean share over the finished seeds}} of one variant (main view: Y1 rule, spans+hc)."""
    d = df[(df["variant"] == variant) & (df["l2_view"] == "spans+hc") & (df["gt_view"] == S48.VIEW) & (df["finished"].astype(str) == "True")]
    return {s: {k: sum(S48.share(r, k) for r in g.to_dict("records")) / len(g) for k in STEP4_METRICS} for s, g in d.groupby("set")}


def fmt(k, n):
    return f"{k}/{n} ({k / n:.3f})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", type=Path, default=WORK)
    work = ap.parse_args().work
    OUT.mkdir(parents=True, exist_ok=True)
    rows, md = [], ["# wf_v5.1 R0: taxi scored as its own entity", "", f"Rule: {RULE}", ""]
    gained = {}
    for s in SETS:
        n = len(M49.found_v49(s)[1])
        final = final_v50(s)
        v49, _ = M49.found_v49(s)
        off, on = found_l2(final, s, False, work), found_l2(final, s, True, work)
        cached = G3.load(s)[3]
        v49_on = found_l2(cached, s, True, work)
        gained[s] = (sorted(on - off), sorted(off - on))
        rows += [{"set": s, "metric": "found L2 v5.0", "gold_n": n, "off": len(off), "on": len(on)},
                 {"set": s, "metric": "found L2 v4.9 (cached columns)", "gold_n": n, "off": len(v49["loop2"]), "on": len(v49_on)}]
        md.append(f"- {s}: gold {n} before and after (the taxi attributes move from the restaurant list to the taxi list); "
                  f"v5.0 = {fmt(len(off), n)} before, {fmt(len(on), n)} after; v4.9 columns {fmt(len(v49['loop2']), n)} before, {fmt(len(v49_on), n)} after.")
        md.append("  Taxi mentions by predicted entity: " + (", ".join(f"{k} (matched {e}, {sh}): {c}" for k, e, sh, c in taxi_mentions(s)) or "none") + ".")
    s4 = {on: step4(on, work) for on in (False, True)}
    ref = pd.read_csv(ROOT / "results" / "wf_v50" / "g5" / "scores.csv", keep_default_na=False)
    same = s4[False].equals(ref)
    m_off, m_on = step4_means(s4[False]), step4_means(s4[True])
    for s in SETS:
        for k in STEP4_METRICS:
            rows.append({"set": s, "metric": f"Step 4 ARMg {k} (mean seeds 0-2)", "gold_n": "", "off": round(m_off[s][k], 3), "on": round(m_on[s][k], 3)})
    pd.DataFrame(rows).to_csv(OUT / "r0.csv", index=False, encoding="utf-8", lineterminator="\n")
    md += ["", "## Before / after (v5.0 final columns)", "", "| set | metric | before (off) | after (taxi rule) |", "|---|---|---|---|"]
    for r in rows:
        f = (lambda v: fmt(v, r["gold_n"])) if r["gold_n"] != "" else str
        md.append(f"| {r['set']} | {r['metric']} | {f(r['off'])} | {f(r['on'])} |")
    md += ["", "## Gained / lost attributes (v5.0 found L2, after vs before)", ""]
    md += [f"- {s}: gained {', '.join(g) or 'none'}; lost {', '.join(l) or 'none'}" for s, (g, l) in gained.items()]
    md += ["", "## Checks", "", f"- Step 4 scores with the rule off equal results/wf_v50/g5/scores.csv: {same}.",
           f"- Step 4 scores with the rule on equal the rule off: {s4[True].equals(s4[False])} (the Step 4 scorer maps a column to a GT column by its "
           "majority gt_L2 label over every entity file, so the predicted entity never mattered for it)."]
    (OUT / "r0.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
