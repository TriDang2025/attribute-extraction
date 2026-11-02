"""wf_v3.7 T10: prompts of the LLM-only baseline (contract: WF_V37_CONTRACT.md, W3). No model, no LLM.

python scripts/baseline_build_v37.py --mwoz C:/Users/nguye/data/MultiWOZ_2.2 [--out results/loop1_v37/colab]
  -> <out>/baseline/prompts/baseline_<ent>_<set>_<v0|v1|v2>.txt + .schema.json, <out>/baseline/prompt_stats.md,
     and the rows (family baseline) in <out>/manifest.json (rows of other families are kept, old baseline rows replaced).
Sets: dev50 = TEAR pool[0:50], dev50b = pool[50:100] of chunking/data/conversation_ids.txt. The dialogues of an entity are
those of the set whose MultiWOZ 2.2 `services` include the domain. Text = chk.data.load_dialogues turns ("User: ...").
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from s1a import baseline_prompt_v37 as BP  # noqa: E402
from s1a import gt_ext, paths  # noqa: E402
from s1a import pilot_input as PIN  # noqa: E402
from chk import config  # noqa: E402
from chk.data import load_dialogues  # noqa: E402

SETS = {"dev50": (0, 50), "dev50b": (50, 100)}
OUT_ESTIMATE = 1000   # estimated output tokens per call (not measured)


def set_ids():
    ids = [x.strip() for x in open(config.IDS, encoding="utf-8") if x.strip()]
    return {name: ids[a:b] for name, (a, b) in SETS.items()}


def stats_md(rows):
    """Markdown of prompt_stats.md from rows (dict: job, ent, set, version, n_available, n_dialogues, tokens)."""
    lines = ["# wf_v3.7 LLM-only baseline prompts", "",
             f"Tokens are estimated as chars / 3.5. Budget per prompt: {BP.CTX} - {BP.OUT_TOKENS} = {BP.BUDGET} "
             f"estimated tokens (instruction included). Output tokens are an ESTIMATE of {OUT_ESTIMATE} per call, not "
             f"measured. v0 = set order, v1 / v2 = shuffled with seed 1 / 2; a dialogue that does not fit is skipped.", "",
             "| prompt | set | entity | dialogues used / available | est. prompt tokens | est. output tokens |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {r['job']} | {r['set']} | {r['ent']} | {r['n_dialogues']}/{r['n_available']} | {r['tokens']} | "
              f"{OUT_ESTIMATE} |" for r in rows]
    lines += ["", "## Totals", "", "| set | prompts | dialogues used | est. prompt tokens | est. output tokens |",
              "|---|---|---|---|---|"]
    for s in [*SETS, "all"]:
        sub = [r for r in rows if s in ("all", r["set"])]
        lines.append(f"| {s} | {len(sub)} | {sum(r['n_dialogues'] for r in sub)} | {sum(r['tokens'] for r in sub)} | "
                     f"{OUT_ESTIMATE * len(sub)} |")
    lines += ["", "## By entity, set and version (dialogues used)", "", "| entity | set | available | v0 | v1 | v2 |",
              "|---|---|---|---|---|---|"]
    for ent in BP.ENTITY_WORD:
        for s in SETS:
            sub = {r["version"]: r for r in rows if r["ent"] == ent and r["set"] == s}
            if sub:
                lines.append(f"| {ent} | {s} | {sub['v0']['n_available']} | "
                             + " | ".join(str(sub[v]["n_dialogues"]) for v in BP.VERSIONS) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mwoz", required=True, type=Path, help="MultiWOZ 2.2 folder (dialogues' services)")
    ap.add_argument("--out", type=Path, default=Path("results/loop1_v37/colab"))
    a = ap.parse_args()
    out = paths.ROOT / a.out
    (out / "baseline" / "prompts").mkdir(parents=True, exist_ok=True)

    sets = set_ids()
    allids = [i for v in sets.values() for i in v]
    texts = {d["id"]: "\n".join(d["turns"]) for d in load_dialogues(len(allids))}
    dialogues, _ = gt_ext.load_mwoz(a.mwoz, allids)
    services = {gt_ext.dialogue_key(d["dialogue_id"]): d["services"] for d in dialogues}
    missing = [i for i in allids if i not in services]
    if missing:
        raise SystemExit(f"{len(missing)} ids not in MultiWOZ 2.2: {missing[:5]}")

    rows, jobs = [], []
    for s, ids in sets.items():
        for ent in BP.ENTITY_WORD:
            eids = BP.entity_ids(ids, services, ent)
            for v in BP.VERSIONS:
                chosen, text = BP.fill(ent, eids, texts, v)
                tok = PIN.est_tokens(text)
                job = BP.job_row(ent, s, v, len(chosen), tok)
                (out / job["prompt"]).write_text(text, encoding="utf-8", newline="\n")
                (out / job["schema"]).write_text(BP.schema_text(), encoding="utf-8", newline="\n")
                jobs.append(job)
                rows.append({"job": job["job"], "ent": ent, "set": s, "version": v, "n_available": len(eids),
                             "n_dialogues": len(chosen), "tokens": tok, "ids": chosen})
    md = stats_md(rows)
    (out / "baseline" / "prompt_stats.md").write_text(md, encoding="utf-8", newline="\n")
    (out / "baseline" / "dialogues_used.json").write_text(
        json.dumps({r["job"]: r["ids"] for r in rows}, indent=1), encoding="utf-8", newline="\n")
    mpath = out / "manifest.json"
    man = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"run": "results/graph_v22_dev50", "jobs": []}
    man["jobs"] = [j for j in man["jobs"] if j.get("family") != "baseline"] + jobs
    mpath.write_text(json.dumps(man, indent=1), encoding="utf-8", newline="\n")
    print(md)


if __name__ == "__main__":
    main()
