"""wf_v5.1 R2 (S6): same-turn block for joins (s1a/turnblock_v51.py), replay on the cached wf_v4.6 Y3 Step 3 outputs, CPU only.
The threshold is chosen on dev50 only; dev50b is scored with the same setting, unchanged. Gold is used only to label joined pairs.

python scripts/r2_turnblock_v51.py -> results/wf_v51/r2/{r2.md, r2_pairs_<set>.csv, r2_sweep.csv, replay_<set>/final_columns.json}

Unit = every pair of clusters inside one final column (both with a gold label), tagged with the join point that first put them in one
column: vote (columns.json = A s012 vote + merge + split pass), reconcile (agreed reconcile of the 2 orders), dupcheck (final). Sides of a
pair = the mention ids of each cluster inside the final column. right = same majority gold label, wrong = different.
Replay = un-join the blocked pairs of the v5.0 final columns (ctxsplit/big40), score like g3_ctxsplit_v50 (found L2 estimate).
"""

import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

import g3_nojoin_v50 as G3  # noqa: E402
import mainclaim_v46 as M46  # noqa: E402
import mainclaim_v49 as M49  # noqa: E402
from s1a import batch_v4 as B  # noqa: E402
from s1a import nojoin_v50 as NJ  # noqa: E402
from s1a import step3_post_v43 as PP  # noqa: E402
from s1a import turnblock_v51 as TB  # noqa: E402

OUT = ROOT / "results" / "wf_v51" / "r2"
BIG40 = ROOT / "results" / "wf_v50" / "g3" / "ctxsplit" / "big40"
SHARES = (0.0, 0.1, 0.2, 0.3, 0.5)
COUNTS = (1, 2)
STAGES = ("vote", "reconcile", "dupcheck")


def stage_columns(step3, run):
    """{ent: {"vote": columns, "reconcile": agreed columns, "final": final columns}} from the cached answers (final_v39.entity_columns,
    as step3_post_v43.score; no LLM, no GT)."""
    FV = PP.script("final_v39")
    jobs = PP.manifest_all(step3)
    rc_jobs = [j for j in jobs if j["family"] == "reconcile"]
    dup_jobs = {(j["set"], j["ent"], j["order_seed"]): j for j in jobs if j["family"] == "dupcheck_rc"}
    tables = B.read_json(step3 / "columns.json")[run]
    responses = PP.script("score_v38").read_responses(step3)
    out = {}
    for ent, t in tables.items():
        b = FV.entity_columns(run, ent, t, responses, rc_jobs, dup_jobs)
        out[ent] = {"vote": t["columns"], "reconcile": b["acols"], "final": b["final"]}
    return out


def clusters_of(col):
    """Cluster ids of a column; members are "cluster@group" strings (final) or [cluster, group] pairs (columns.json)."""
    return list(dict.fromkeys((m if isinstance(m, str) else "@".join(m)).split("@")[0] for m in col["members"]))


def co_grouped(columns):
    return {frozenset(p) for c in columns for p in itertools.combinations(clusters_of(c), 2)}


def top(counter):
    return counter.most_common(1)[0][0] if counter else ""


def pair_rows(set_name):
    """Rows of r2_pairs_<set>.csv: one per cluster pair inside a final column, with the turn stats and the gold verdict."""
    mt, labels, _emap, final, step3 = G3.load(set_name)
    run = M46.RUN_OF[set_name]
    stages = stage_columns(step3, run)
    index = TB.TurnIndex(mt)
    cluster_of = mt["cluster_id"].to_dict()
    rows = []
    for ent, st in stages.items():
        if [clusters_of(c) for c in st["final"]] != [clusters_of(c) for c in final[ent]]:
            raise ValueError(f"{set_name} {ent}: rebuilt final columns differ from final_columns.json")
        vote, rec = co_grouped(st["vote"]), co_grouped(st["reconcile"])
        for col in st["final"]:
            ids = [int(i) for i in col["mention_ids"]]
            mine = {c: [i for i in ids if cluster_of.get(i) == c] for c in clusters_of(col)}
            for a, b in itertools.combinations(sorted(mine), 2):
                la = top(Counter(x for i in mine[a] for x in labels.get(i, [])))
                lb = top(Counter(x for i in mine[b] for x in labels.get(i, [])))
                if not la or not lb:
                    continue
                key = frozenset((a, b))
                stage = "vote" if key in vote else "reconcile" if key in rec else "dupcheck"
                rows.append({"set": set_name, "ent": ent, "col": col["name"], "stage": stage, "a": a, "b": b, "n_a": len(mine[a]),
                             "n_b": len(mine[b]), **TB.pair_stats(index, mine[a], mine[b]), "la": la, "lb": lb, "same": la == lb})
    return pd.DataFrame(rows)


def sweep(pairs):
    """Rows: per set, join point (and "all"), share cut, min count: wrong / right joins blocked of the totals."""
    rows = []
    for s, g in pairs.groupby("set"):
        for stage in (*STAGES, "all"):
            h = g if stage == "all" else g[g["stage"] == stage]
            for sh, cnt in itertools.product(SHARES, COUNTS):
                blk = (h["share"] > sh) & (h["count"] >= cnt)
                rows.append({"set": s, "stage": stage, "share_gt": sh, "min_count": cnt,
                             "wrong_blocked": int((blk & ~h["same"]).sum()), "wrong_total": int((~h["same"]).sum()),
                             "right_blocked": int((blk & h["same"]).sum()), "right_total": int(h["same"].sum())})
    return pd.DataFrame(rows)


def choose(sw):
    """(share_gt, min_count) on dev50, join point "all": most (wrong blocked - right blocked); ties -> the higher share, then count."""
    d = sw[(sw["set"] == "dev50") & (sw["stage"] == "all")].copy()
    d["gain"] = d["wrong_blocked"] - d["right_blocked"]
    best = d.sort_values(["gain", "share_gt", "min_count"], ascending=[False, False, False]).iloc[0]
    return float(best["share_gt"]), int(best["min_count"])


def replay(set_name, share, count):
    """Un-join the blocked pairs of the v5.0 final columns (big40); row of found L2 and column counts, and the new final_columns.json."""
    mt, labels, emap, final, step3 = G3.load(set_name)
    run = M46.RUN_OF[set_name]
    v49, gold = M49.found_v49(set_name)
    gold_by_ent = {}
    for a, e in gold.items():
        gold_by_ent.setdefault(e, []).append(a)
    big = json.loads((BIG40 / set_name / "final_columns.json").read_text(encoding="utf-8"))[run]
    index, cluster_of = TB.TurnIndex(mt), mt["cluster_id"].to_dict()
    names = NJ.premerge_names(step3, run)
    after = {k: TB.apply_to_columns(cols, cluster_of, names, index, share, count) for k, cols in big.items()}
    d = OUT / f"replay_{set_name}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "final_columns.json").write_text(json.dumps({run: after}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    f0, _ = G3.score(final, emap, mt, labels, gold_by_ent)
    fb, cb = G3.score(big, emap, mt, labels, gold_by_ent)
    f1, c1 = G3.score(after, emap, mt, labels, gold_by_ent)
    l2 = lambda f: (v49["loop2"] - (f0 - f)) | (f - f0)    # noqa: E731  (found rule of g3_nojoin_v50)
    kinds = [pd.Series([r["kind"] for r in c]).value_counts() for c in (cb, c1)]
    return {"set": set_name, "gold_n": len(gold), "found_L2_v50": len(l2(fb)), "found_L2_replay": len(l2(f1)),
            "gained": "; ".join(sorted(f1 - fb)), "lost": "; ".join(sorted(fb - f1)),
            "cols_v50": len(cb), "cols_replay": len(c1),
            "new_wrong_cols": int(sum(k.get("dup", 0) + k.get("other", 0) for k in kinds[1:]) - sum(k.get("dup", 0) + k.get("other", 0) for k in kinds[:1])),
            "cols_unjoined": len(c1) - len(cb)}


def md_tables(sw, share, count):
    lines = []
    for s in ("dev50", "dev50b"):
        lines += [f"### {s}: wrong / right joins blocked (min count {count})", "",
                  "| join point | share > | wrong blocked | right blocked |", "|---|---|---|---|"]
        for stage in (*STAGES, "all"):
            for sh in SHARES:
                r = sw[(sw["set"] == s) & (sw["stage"] == stage) & (sw["share_gt"] == sh) & (sw["min_count"] == count)].iloc[0]
                mark = " **<-**" if (stage, sh) == ("all", share) else ""
                lines.append(f"| {stage} (wrong {r.wrong_total}, right {r.right_total}) | {sh} | {r.wrong_blocked}/{r.wrong_total} | "
                             f"{r.right_blocked}/{r.right_total} |{mark}")
        lines.append("")
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = pd.concat([pair_rows(s) for s in G3.SETS], ignore_index=True)
    for s, g in pairs.groupby("set"):
        g.to_csv(OUT / f"r2_pairs_{s}.csv", index=False, encoding="utf-8", lineterminator="\n")
    sw = sweep(pairs)
    sw.to_csv(OUT / "r2_sweep.csv", index=False, encoding="utf-8", lineterminator="\n")
    share, count = choose(sw)
    rep = pd.DataFrame([replay(s, share, count) for s in G3.SETS])
    rep.to_csv(OUT / "r2_replay.csv", index=False, encoding="utf-8", lineterminator="\n")
    summ = pairs.groupby(["set", "stage"]).agg(pairs=("same", "size"), wrong=("same", lambda x: int((~x).sum())),
                                               right=("same", "sum")).reset_index()
    md = ["# wf_v5.1 R2: same-turn block for joins (S6), replay on cached outputs", "",
          "Unit: every pair of clusters inside one final column of the wf_v4.6 Y3 run (both with a gold label); join point = the stage that "
          "first put the pair in one column. wrong = different majority gold label. Gold only labels the pairs. share = fraction of the "
          "pair's mentions in a turn that also holds a different-valued mention of the other side; count = turns with such a pair "
          f"(`s1a/turnblock_v51.py`).", "", "## Pairs", "", summ.to_markdown(index=False), ""]
    md += ["## Threshold sweep", ""] + md_tables(sw, share, 1) + md_tables(sw, share, 2)
    md += [f"Full grid (share > {SHARES}, min count {COUNTS}) in `r2_sweep.csv`.", "",
           f"## Chosen on dev50: share > {share}, min count {count}", "",
           "Rule: most (wrong blocked - right blocked) on dev50, join point all; ties to the higher share, then count. dev50b unchanged.", "",
           "## Replay on the v5.0 final columns (ctxsplit big40)", "", rep.to_markdown(index=False), "",
           "Estimate only: un-joined parts keep the cached pre-merge cluster names, Step 4 is not rerun; found L2 = the v5.0 set "
           "(34/40 | 30/41) minus loop-1 span finds that the block loses, plus new span finds (g3_nojoin_v50 rule, conservative)."]
    (OUT / "r2.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
