"""wf_v4.7 Z2: replay the loop-2 code steps of the v4.6 run with other rules. No LLM calls: the cached Step 1b answers
(<run>/loop2/step1b/review.json) give the names; real bge-m3 + GLiNER (CPU) give the spans; no gold.

python scripts/replay_v47.py [--sets dev50,dev50b] [--limit N] [--runs results/wf_v46/y3] [--out results/wf_v47/z2]
  -> <out>/<set>/names.csv   one row per suggested name: spans, dialogues, support, span overlap, value Jaccard / containment with the
                             closest loop-1 column, and pass / fail under each rule
     <out>/<set>/spans.json  the GLiNER spans per name (all entity turns, with the retrieval rank), so later steps need no rerun
GLiNER runs on the top-k entity turns by bge-m3 cosine (the v4.6 spans: base, checked against the v4.6 evidence.csv); a voted name that
fails on size alone also gets a pass over all entity turns (rule 6; no other name can flip). Rules (each alone, on top of base):
  base  v4.6: voted (>= 2 of 3) and screened, top-k spans, n_dialogues >= 3, support >= 0.05, span overlap < 0.5
  r1    overlap on values: the span-overlap test is replaced by value Jaccard with every loop-1 column < --jaccard
  r1c   (extra) as r1 with containment |new & col| / |new| < --jaccard (a small new set inside a big column)
  r3    duplicate check on values: a base pass whose value Jaccard with a loop-1 column >= --jaccard is a duplicate
  r4    vote 1 of 3: the unvoted names go on (same screen and evidence check as base)
  r5    name + description as the GLiNER label (only names with a real description; "..." = the v4.6 format bug, no change)
  r6    support over all entity turns, not only the top-k: n_dialogues and support from every span; overlap as base (top-k)
r2 (never merge two names) changes no evidence result; it is counted from the v4.6 naming (merged names) in the Z2 report.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import pandas as pd  # noqa: E402

from s1a import batch_v4 as B  # noqa: E402
from s1a import corpus_v45 as CO  # noqa: E402
from s1a import loop2_v41 as L2  # noqa: E402
from s1a import loop2_v46 as L  # noqa: E402
from s1a import step1b_v41 as S1B  # noqa: E402
from s1a import step3_post_v43 as PP  # noqa: E402
from s1a import step3_v44 as S3_44  # noqa: E402

RUN_OF = {"dev50": "c_n50", "dev50b": "c_n50b"}
RULES = ["base", "r1", "r1c", "r3", "r4", "r5", "r6"]


def set_inputs(run_dir, run_set):
    """(finals {entity: loop-1 columns}, cols_by_ent {entity: Step 1b columns}, stage1_of, review) of a v4.6 run folder."""
    finals = B.read_json(run_dir / "step3" / "scores" / "final_columns.json")[run_set]
    a_file = S3_44.a_llama44_file(run_set, run_dir / "step3")
    pre = a_file.with_name("a.premerge.columns.json")
    cols_by_ent = {}
    for c in B.read_json(pre if pre.exists() else a_file):
        cols_by_ent.setdefault(S1B._entity(c), []).append(c)
    stage1_of = {ent: cs[0]["entity"] for ent, cs in finals.items() if cs}
    return finals, cols_by_ent, stage1_of, B.read_json(run_dir / "loop2" / "step1b" / "review.json")


def screened(review, cols_by_ent, cfg):
    """Every suggested name with its v4.6 screen: [{entity, name, description, votes, stage, reason}] (stage "" = to evidence, "vote" =
    unvoted but otherwise clean: r4 sends it on, "check" = fails the name screen in every rule)."""
    rows = []
    n_orders = len(cfg["step1b"]["orders"])
    one = {**cfg, "step1b": {**cfg["step1b"], "min_votes": 1}}
    for ent, cols in cols_by_ent.items():
        existing, values = {L.norm_key(x["name"]) for x in cols}, S1B.example_values(cols)
        for s in review[ent]["suggestions"]:
            stage, reason = L.screen(s, n_orders, existing, values, cfg)
            if stage == "vote":
                st1, r1 = L.screen({**s, "voted": True}, n_orders, existing, values, one)
                stage, reason = ("check", r1) if st1 else ("vote", reason)
            rows.append({"entity": ent, "name": s["key"], "description": s["description"], "votes": s["votes"], "stage": stage, "reason": reason})
    return rows


def real_description(d, name):
    d = (d or "").strip()
    return bool(d) and d.strip(". ") != "" and d.lower() != name.lower()


def value_sets(finals, mt):
    """{entity: {column name: set of norm values}} of the loop-1 columns."""
    nv = dict(zip(mt["mention_id"].astype(int), mt["norm_value"].astype(str)))
    return {e: {c["name"]: {nv[int(i)] for i in c["mention_ids"] if nv.get(int(i))} for c in cs} for e, cs in finals.items()}


def closest(vals, cols, mode):
    """(score, column) of the loop-1 column closest to the value set: Jaccard or containment (share of vals in the column)."""
    best = (0.0, "")
    for name, cv in cols.items():
        inter = len(vals & cv)
        den = len(vals | cv) if mode == "jaccard" else len(vals)
        best = max(best, (inter / den if den else 0.0, name))
    return round(best[0], 3), best[1]


def spans(lab, ctx, k):
    """GLiNER mentions of one label on the top-k entity turns by bge-m3 cosine (k = 10**9: all turns); each mention gets its turn's rank."""
    allowed = L2.entity_turn_filter(ctx["inst"], lab["stage1"])
    hits = L2.retrieve(ctx["items"], ctx["vecs"], ctx["encoder"].encode([L2.query_text(lab)])[0], k, allowed)
    windows = {}
    for r, (it, _) in enumerate(hits):
        windows.setdefault(it["doc_id"], []).append((it["start"], it["end"], r))
    raw = L2.extract(hits, lab["label"], ctx["predict"], ctx["cfg"]["threshold"])
    ms = L2.make_mentions(raw, ctx["docs"], allowed, 0)
    for r, m in zip(raw, ms):
        m["rank"] = next(k for s, e, k in windows[r["doc_id"]] if s <= r["char_start"] < e)
    return ms


def judge(ms, lab, ctx):
    """evidence dict + v4.6 decision of a mention list (L2.evidence / L2.decide; no spans = fail)."""
    ents = sorted(ctx["inst"][ctx["inst"]["entity"] == lab["stage1"]]["instance_id"])
    ev = L2.evidence(ms, ents, ctx["finals"][lab["entity"]], ctx["mt"], ctx["encoder"], len(ctx["docs"]))
    keep, reason = L2.decide(ev, ctx["cfg"]) if ms else (False, "no spans")
    return ev, keep, reason


def name_row(s, ctx, jac, store):
    """One names.csv row: the evidence numbers and the result of every rule for one screened name."""
    lab = {"entity": s["entity"], "name": s["name"], "label": s["name"], "description": s["description"] or s["name"],
           "value_type": "text", "stage1": ctx["stage1_of"][s["entity"]]}
    row = {k: s[k] for k in ("entity", "name", "votes", "stage", "reason")}
    if s["stage"] == "check":
        return {**row, **{r: False for r in RULES}}
    k = ctx["cfg"]["k"]
    voted = s["stage"] == ""
    ms_top = spans(lab, ctx, k)
    ev, keep, why = judge(ms_top, lab, ctx)
    vals = {m["norm_value"] for m in ms_top if m["norm_value"]}
    jv, jcol = closest(vals, ctx["vsets"][s["entity"]], "jaccard")
    cv, ccol = closest(vals, ctx["vsets"][s["entity"]], "containment")
    size_ok = ev["n_dialogues"] >= ctx["cfg"]["min_dialogues"] and ev["support"] >= ctx["cfg"]["min_support"] and bool(ms_top)
    over_ok = ev["overlap"] < ctx["cfg"]["max_overlap"]
    ms_all, ev6 = ms_top, ev            # r6 can only flip a voted name that fails on size alone: only those get the all-turns pass
    if voted and ms_top and over_ok and not size_ok:
        ms_all = spans(lab, ctx, 10 ** 9)
        ev6 = judge(ms_all, lab, ctx)[0]
    six_ok = ev6["n_dialogues"] >= ctx["cfg"]["min_dialogues"] and ev6["support"] >= ctx["cfg"]["min_support"] and over_ok and bool(ms_top)
    r5 = None
    if real_description(s["description"], s["name"]):
        r5 = judge(spans({**lab, "label": f"{s['name']}, {s['description']}"}, ctx, k), lab, ctx)[1]
    store[f"{s['entity']}|{s['name']}"] = [{x: m[x] for x in ("dialogue_id", "turn", "instance_id", "char_start", "char_end", "text",
                                                              "norm_value", "score", "rank")} for m in ms_all]
    return {**row, "n_spans_topk": len(ms_top), "n_spans_all": len(ms_all), "n_dialogues": ev["n_dialogues"], "support": round(ev["support"], 3),
            "n_dialogues_all": ev6["n_dialogues"], "support_all": round(ev6["support"], 3), "overlap": round(ev["overlap"], 3),
            "overlap_column": ev["overlap_column"], "jaccard": jv, "jaccard_column": jcol, "containment": cv, "containment_column": ccol,
            "base_reason": why, "top_values": " | ".join(L2.top_values(ms_top)),
            "base": voted and keep, "r1": voted and size_ok and jv < jac, "r1c": voted and size_ok and cv < jac,
            "r3": voted and keep and jv < jac, "r4": keep, "r5": voted and (keep if r5 is None else r5), "r6": voted and six_ok}


def run_set(set_name, runs, out, jac, limit, encoder, predict, log=print):
    run_set_name = RUN_OF[set_name]
    run_dir = Path(runs) / set_name
    cfg = L.load_config()
    finals, cols_by_ent, stage1_of, review = set_inputs(run_dir, run_set_name)
    ri = PP.script("pilot_build_v37").RunInput(CO.run_dir(run_set_name), 0)
    items = L2.turn_items(ri.docs)
    ctx = {"cfg": cfg["evidence"], "finals": finals, "stage1_of": stage1_of, "docs": ri.docs, "mt": ri.export.mentions,
           "inst": ri.export.instances, "items": items, "vecs": encoder.encode([it["text"] for it in items]), "encoder": encoder,
           "predict": predict, "vsets": value_sets(finals, ri.export.mentions)}
    names = screened(review, cols_by_ent, cfg)[:limit]
    rows, store, t0 = [], {}, time.time()
    for i, s in enumerate(names, 1):
        rows.append(name_row(s, ctx, jac, store))
        log(f"{set_name} {i}/{len(names)} {s['entity']} | {s['name']}: base={rows[-1]['base']} ({time.time() - t0:.0f} s)")
    d = Path(out) / set_name
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(d / "names.csv", index=False, encoding="utf-8", lineterminator="\n")
    (d / "spans.json").write_text(json.dumps(store, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", default="dev50,dev50b")
    ap.add_argument("--runs", default=str(ROOT / "results" / "wf_v46" / "y3"))
    ap.add_argument("--out", default=str(ROOT / "results" / "wf_v47" / "z2"))
    ap.add_argument("--jaccard", type=float, default=0.5)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    from run import encoder as make_encoder
    from s1a import spans as SP
    enc = make_encoder()
    predict = PP.script("loop2_v41").GlinerPredictor(SP.load())
    try:
        for s in a.sets.split(","):
            df = run_set(s.strip(), a.runs, a.out, a.jaccard, a.limit, enc, predict)
            print(s, {r: int(df[r].sum()) for r in RULES})
    finally:
        enc.save()


if __name__ == "__main__":
    main()
