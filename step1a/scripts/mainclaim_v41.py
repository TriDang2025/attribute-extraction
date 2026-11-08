"""wf_v4.1 task 9: scoring for the main claim. Compare the attribute lists of loop 1, loop 2 and TEAR with the gold L2 attributes.

python scripts/mainclaim_v41.py --set dev50 [--loop2 results/wf_v41/loop2/dev50/clusters.json] [--tear <TEAR output .jsonl>]
        [--spans data/mwoz22_spans.csv ...] [--out results/wf_v41/mainclaim]
Loop 1 = the handover columns (handover/<set>/). Loop 2 = loop 1 + the kept clusters of clusters.json. TEAR = the columns of a TEAR run
(score_tear_v36 / tear_cols; needs the 2.2 spans, `--spans`, default: data/mwoz22_spans.csv and the dev50b span file when they exist). A missing
loop-2 or TEAR file is skipped with a note. Writes <out>/<set>/{compare.md, compare.csv, human_check_sheet.csv, human_check_key.csv}.
The sheet is blind (no GT label); the key holds the majority GT label. Rules: s1a/mainclaim_v41.py.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

import score_tear_v36 as ST  # noqa: E402
from s1a import gt_ext as G  # noqa: E402
from s1a import mainclaim_v41 as M  # noqa: E402
from s1a import tear_cols as TC  # noqa: E402

OUT = ROOT / "results" / "wf_v41" / "mainclaim"
SPANS = [ROOT / "data" / "mwoz22_spans.csv", ROOT / "results" / "loop1_v37" / "dev50b" / "gt" / "mwoz22_spans.csv"]
TEAR_MAP = ROOT / "config" / "tear_to_mwoz.json"
DB = ROOT.parent / "chunking" / "data" / "MULTIWOZ2.4.zip"


def load_spans(paths):
    """(spans DataFrame or None, [paths read]): the existing files, concatenated."""
    have = [Path(p) for p in paths if Path(p).exists()]
    if not have:
        return None, []
    return pd.concat([pd.read_csv(p, encoding="utf-8") for p in have], ignore_index=True).drop_duplicates(), have


def run(set_name, loop2, tear, spans_paths, out):
    handover, mt, labels, gold = M.load_set(set_name)
    gold_all = {a for g in gold.values() for a in g}
    tear_map = json.loads(TEAR_MAP.read_text(encoding="utf-8"))
    spans, read = load_spans(spans_paths)
    notes = [f"Gold attributes: {', '.join(f'{e} {len(g)}' for e, g in gold.items())} (total {len(gold_all)}); "
             f"STEP3.md: {M.STEP3_FOUND[set_name][0]}/{M.STEP3_FOUND[set_name][1]} found by the frozen handover."]
    items1 = M.loop1_items(handover, mt, labels)
    total1 = M.entity_totals(handover, mt, labels)
    s1 = M.summarize_loop("loop1", items1, total1, gold)
    k1 = sum(len(s1["found"][e] & set(gold[e])) for e in gold)
    notes.append(f"Loop 1: {k1}/{len(gold_all)} found by groups (STEP3.md {M.STEP3_FOUND[set_name][0]}/{M.STEP3_FOUND[set_name][1]}: "
                 f"{'equal' if k1 == M.STEP3_FOUND[set_name][0] else 'DIFFERENT'}); {len(items1)} columns, {len(s1['new'])} new.")
    summaries = [s1]
    if loop2 and Path(loop2).exists():
        stage1 = {doc["stage1_entity"]: e for e, doc in handover.items()}
        clusters = M.read_loop2(loop2, stage1)
        span_idx = TC.span_index(spans) if spans is not None else None
        known = M.known_labels(mt, labels)
        items2, extra, unl = M.loop2_items(clusters, known, span_idx, tear_map)
        total2 = {e: total1[e] + M.totals(extra.get(e, [])) for e in total1}
        s2 = M.summarize_loop("loop2", items1 + items2, total2, gold)
        summaries.append(s2)
        no_span = sum(m["dialogue_id"] not in (span_idx or {}) for c in clusters for m in c["mentions"])
        notes.append(f"Loop 2: {len(clusters)} clusters, {len(items2)} kept; {unl} loop-2 mentions have no GT label, {no_span} of them in "
                     "dialogues missing from the spans file (dev50 needs data/mwoz22_spans.csv, not in git: copy it from the wf-v3.6 worktree)"
                     + f". Loop 2 = loop 1 + kept clusters.")
    else:
        notes.append(f"Loop 2: skipped ({'no --loop2 given' if not loop2 else f'{loop2} not found'}).")
    if tear and Path(tear).exists():
        if spans is None:
            notes.append("TEAR: skipped, no spans file (--spans) to map the columns to gold attributes.")
        else:
            rows = [json.loads(line) for line in Path(tear).read_text(encoding="utf-8").splitlines() if line.strip()]
            db_idx = G.db_index(G.load_db(DB)) if DB.exists() else None
            cols, _, _, _ = ST.score(rows, spans, tear_map, db_idx, ())
            found, new, skipped = M.tear_items(cols, M.tear_values(rows), gold)
            summaries.append({"source": "tear", "found": found, "new": new, "n_items": dict(cols.assign(e=cols["ent"].map(M.DOMAIN_ENTITY))["e"].value_counts())})
            notes.append(f"TEAR: {len(cols)} columns from {len(rows)} rows ({Path(tear).name}), {skipped} of a domain with no gold entity skipped; "
                         "no rater files read (columns without a value match have no name label).")
    else:
        notes.append(f"TEAR: skipped ({'no --tear given' if not tear else f'{tear} not found'}).")
    notes.append("Spans read: " + (", ".join(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p) for p in read) or "none") + ".")
    rows = M.compare_rows(set_name, gold, summaries)
    sheet, key = M.sheet_rows(summaries, gold_all)
    d = Path(out) / set_name
    d.mkdir(parents=True, exist_ok=True)
    for name, df in (("compare.csv", pd.DataFrame(rows)), ("human_check_sheet.csv", sheet), ("human_check_key.csv", key)):
        df.to_csv(d / name, index=False, encoding="utf-8", lineterminator="\n")
    md = M.compare_md(set_name, gold, summaries, rows, notes)
    (d / "compare.md").write_text(md, encoding="utf-8", newline="\n")
    return md, d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", required=True, help="dev50, dev50b or a comma list")
    ap.add_argument("--loop2", type=Path)
    ap.add_argument("--tear", type=Path)
    ap.add_argument("--spans", type=Path, nargs="*", default=SPANS)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    for s in a.set.split(","):
        md, d = run(s.strip(), a.loop2, a.tear, a.spans, a.out)
        print(md)
        print(f"wrote {d}")


if __name__ == "__main__":
    main()
