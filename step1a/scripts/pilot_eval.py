"""Step-3 pilot evaluation (LOOP1_CONTRACT.md, T5 eval): LLM responses -> decisions, verification, scores.

python scripts/pilot_eval.py --run results/graph_v22_dev50 --dir results/loop1_check/pilot_train
Reads <dir>/responses_<variant>_<run_tag>.jsonl and <dir>/examples.csv; writes decisions.csv, verification.csv,
name_check.csv (fill `manual` with 1/0 to override the auto value; kept on re-runs), scores.md; GLiNER
outputs are cached per name in <dir>/gliner_cache/.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import mentions as MN  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from s1a import pilot_score as PS  # noqa: E402
from s1a import pilot_verify as PV  # noqa: E402

ORDER = ["full r1", "full r2", "nocontext r1", "nohints r1"]


def _read(path, **kw):
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8", **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--gold-entity", default="train")
    a = ap.parse_args()

    e = MN.load(a.run / "spans")
    docs, gv, gold_attrs = MN.load_shared(a.run)
    labels = _read(a.run / "spans" / "labels.csv")
    examples = _read(a.dir / "examples.csv")
    entity = PIN.find_pilot_entity(e.mentions, a.gold_entity)
    cids = sorted(c for c in e.mentions.loc[e.mentions["entity"] == entity, "cluster_id"].unique() if c)
    ctx = PS.Ctx(e.mentions, labels, gv, gold_attrs, e.ids, e.x, examples, entity, a.gold_entity)
    extract = PV.gliner_extractor()

    decs, vers, by_file = {}, [], {}
    for path in sorted(a.dir.glob("responses_*.jsonl")):
        variant, tag = PV.response_key(path)
        dec = PV.decisions_table(PV.load_objects(path), cids, variant, tag)
        assign, attrs, parts = PV.final_attributes(dec, e.mentions, e.ids, e.x, examples, entity)
        ver = PV.verify(attrs, assign, e.mentions, docs, e.instances, entity, extract,
                        a.dir / "gliner_cache", variant, tag)
        decs[f"{variant} {tag}"], by_file[(variant, tag)] = dec, (dec, attrs, assign, parts, ver)
        vers.append(ver)
    if not decs:
        sys.exit(f"no responses_*.jsonl in {a.dir}")

    old = _read(a.dir / "name_check.csv") if (a.dir / "name_check.csv").exists() else None
    names = PS.apply_manual(PS.name_check_table({k: (v[1], v[2]) for k, v in by_file.items()}, e.mentions,
                                                a.gold_entity), old)
    results = {}
    for (variant, tag), (dec, attrs, assign, parts, ver) in by_file.items():
        results[f"{variant} {tag}"] = PS.score_file(dec, attrs, assign, parts, ctx, ver, names)
    results = {k: results[k] for k in sorted(results, key=lambda k: ORDER.index(k) if k in ORDER else len(ORDER))}
    stab = PS.stability(decs["full r1"], decs["full r2"]) if "full r1" in decs and "full r2" in decs else None

    pd.concat(decs.values()).to_csv(a.dir / "decisions.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.concat(vers).to_csv(a.dir / "verification.csv", index=False, encoding="utf-8", lineterminator="\n")
    names.to_csv(a.dir / "name_check.csv", index=False, encoding="utf-8", lineterminator="\n")
    (a.dir / "scores.md").write_text(PS.render_scores(results, stab, entity,
                                     f"{len(cids)} clusters, {len(ctx.train)} train gold classes."),
                                     encoding="utf-8", newline="\n")
    print(f"wrote decisions.csv, verification.csv, name_check.csv, scores.md in {a.dir}")


if __name__ == "__main__":
    main()
