"""Run the paper's experiments on our data and compare with the paper.

  python -m eval.reproduce embed     --dataset conversation
  python -m eval.reproduce te        --dataset conversation --methods rag tear --seeds 0 1 2 --n 20 [--level full]
  python -m eval.reproduce discover  --dataset conversation --level 1 --seed 0 --n 20
  python -m eval.reproduce coherence --dataset conversation --level 1 --seed 0
  python -m eval.reproduce integrate --dataset conversation --level 1 --seed 0
  python -m eval.reproduce tearstar  --dataset conversation --level 1 --seed 0 --n 20
  python -m eval.reproduce report

Table extraction (Table 2) uses the full schema. Attribute recommendation and TEAR* use the
exploratory levels (hidden attributes are removed from the schema and the pool). Every
step appends to results/<dataset>/... and skips texts already done, so runs resume.
"""

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from eval.metrics import VALUE_SIMILARITIES, header_f1, recall_auc, structured_f1, table_headers
from tear_reproduction.client import CachedEmbedder, LlamaCppEmbedder, OpenAICompatibleClient
from tear_reproduction.data import load_jsonl
from tear_reproduction.pipeline import PLACEHOLDER, TearPipeline
from tear_reproduction.schema import config, full_schema

ROOT = Path(__file__).resolve().parents[1]
DATA = {
    "conversation": ("Conversation", ROOT / "data/conversation"),
    "incidents": ("Incidents", ROOT / "data/incidents_small"),
    "weather": ("Weather", ROOT / "data/weather_small"),
}
RESULTS = ROOT / "results"

# Paper Table 2, Llama-3-8B-Instruct: (RAG, TEAR) per (dataset, metric, sim).
PAPER_TABLE2 = {
    ("Incidents", "header-F1", "EM"): (81.5, 87.8), ("Incidents", "header-F1", "chrf"): (87.9, 92.5),
    ("Incidents", "header-F1", "BS"): (88.5, 93.1), ("Incidents", "structured-F1", "EM"): (61.2, 69.1),
    ("Incidents", "structured-F1", "chrf"): (73.6, 79.4), ("Incidents", "structured-F1", "BS"): (76.8, 82.9),
    ("Weather", "header-F1", "EM"): (77.3, 80.3), ("Weather", "header-F1", "chrf"): (83.5, 85.6),
    ("Weather", "header-F1", "BS"): (88.7, 90.1), ("Weather", "structured-F1", "EM"): (46.2, 51.0),
    ("Weather", "structured-F1", "chrf"): (65.4, 70.1), ("Weather", "structured-F1", "BS"): (64.3, 67.9),
    ("Conversation", "header-F1", "EM"): (84.6, 88.7), ("Conversation", "header-F1", "chrf"): (91.9, 94.5),
    ("Conversation", "header-F1", "BS"): (91.3, 93.9), ("Conversation", "structured-F1", "EM"): (76.9, 82.4),
    ("Conversation", "structured-F1", "chrf"): (81.2, 86.1), ("Conversation", "structured-F1", "BS"): (83.8, 88.4),
}


def _read(path: Path) -> List[Dict[str, Any]]:
    return load_jsonl(str(path)) if path.exists() else []


def _append(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, ensure_ascii=False) + "\n")


def _levels(key: str) -> Dict[str, Any]:
    path = DATA[key][1] / "levels.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _schema(key: str, level: str) -> List[str]:
    dataset = DATA[key][0]
    return full_schema(dataset) if level == "full" else _levels(key)["levels"][level]["schema"]


def _hidden(key: str, level: str) -> List[str]:
    return [] if level == "full" else _levels(key)["levels"][level]["hidden"]


def _tests(key: str, n: Optional[int]) -> List[Dict[str, Any]]:
    rows = load_jsonl(str(DATA[key][1] / "test.jsonl"))
    return rows[:n] if n else rows


def _client(args, seed: Optional[int] = None) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(args.base_url, args.model, embedding_model=args.embedding_model,
                                  timeout=args.timeout, temperature=0.5, top_p=0.5, seed=seed)


# SFR-Embedding-Mistral is instruction-tuned; its model card uses this instruction for
# semantic similarity, applied to both texts so Eq. 10 stays symmetric.
SFR_PREFIX = "Instruct: Retrieve semantically similar text.\nQuery: "


def _embedder(args, key: str) -> CachedEmbedder:
    name = args.embedding_model.replace("/", "_")
    prefix = SFR_PREFIX if "sfr" in args.embedding_model.lower() else ""
    backend = LlamaCppEmbedder(args.embedding_url) if args.embedding_url else _client(args)
    return CachedEmbedder(backend, str(DATA[key][1] / f"embeddings_{name}.json"), prefix)


def _previews(key: str) -> Dict[str, str]:
    path = DATA[key][1] / "previews.jsonl"
    return {r["id"]: r["sequence"] for r in _read(path)}


def _pipeline(args, key, level, retrieval, seed, schema=None) -> TearPipeline:
    dataset = DATA[key][0]
    pool = load_jsonl(str(DATA[key][1] / "pool.jsonl"))
    return TearPipeline(_client(args, seed), pool, dataset, schema or _schema(key, level),
                        shots=config(dataset)["shots"], retrieval=retrieval,
                        embedder=_embedder(args, key), max_attempts=args.max_attempts)


def _run_te(args, key, level, method, seed, out: Path, schema=None) -> None:
    from surrogate.serialize import preview_for_schema
    pipe = _pipeline(args, key, level, "rag" if method == "rag" else "tear", seed, schema)
    previews = _previews(key)
    done = {r["id"] for r in _read(out)}
    for row in _tests(key, args.n):
        if row["id"] in done:
            continue
        start = time.time()
        hp = vp = None
        if method != "rag":
            hp, vp = preview_for_schema(previews[row["id"]], pipe.schema, full_schema(pipe.dataset))
        pipe.calls = []
        try:
            result = pipe.extract(row["text"], hp, vp)
            record = {"id": row["id"], **result}
        except ValueError as error:  # model output that never parsed; endpoint errors stop the run
            record = {"id": row["id"], "table": {"headers": [], "rows": []}, "error": str(error)[:300]}
        record.update({"schema": pipe.schema, "seconds": round(time.time() - start, 1), "calls": pipe.calls})
        _append(out, record)
        print(f"{out.name} {row['id']} {record['seconds']}s{' ERROR' if 'error' in record else ''}", flush=True)


def cmd_embed(args):
    emb = _embedder(args, args.dataset)
    texts = [r["text"].strip() for r in load_jsonl(str(DATA[args.dataset][1] / "pool.jsonl"))]
    texts += [r["text"].strip() for r in _tests(args.dataset, args.n)]
    start = time.time()
    emb.embed(texts)
    print(f"embedded {len(texts)} texts in {time.time() - start:.0f}s")


def cmd_te(args):
    for seed in args.seeds:
        for method in args.methods:
            out = RESULTS / args.dataset / f"te_{method}_L{args.level}_s{seed}.jsonl"
            _run_te(args, args.dataset, args.level, method, seed, out)


def cmd_discover(args):
    pipe = _pipeline(args, args.dataset, args.level, "tear", args.seed)
    tables = {r["id"]: r["table"] for r in _read(RESULTS / args.dataset / f"te_tear_L{args.level}_s{args.seed}.jsonl")}
    out = RESULTS / args.dataset / f"disc_L{args.level}_s{args.seed}.jsonl"
    done = {r["id"] for r in _read(out)}
    for row in _tests(args.dataset, args.n):
        if row["id"] in done:
            continue
        if row["id"] not in tables:
            raise SystemExit(f"run `te --methods tear --level {args.level} --seeds {args.seed}` first ({row['id']} missing)")
        start = time.time()
        pipe.calls = []
        try:
            result = pipe.discover(row["text"], tables[row["id"]])
            record = {"id": row["id"], **result}
        except ValueError as error:  # model output that never parsed; endpoint errors stop the run
            record = {"id": row["id"], "proposals": [], "error": str(error)[:300]}
        record.update({"seconds": round(time.time() - start, 1), "calls": pipe.calls})
        _append(out, record)
        print(f"{out.name} {row['id']} {record['seconds']}s {len(record['proposals'])} proposals", flush=True)


def _proposals(key, level, seed):
    """Z: the union of new headers over all pseudo-tables, with their contexts (A.4)."""
    texts = {r["id"]: r["text"].strip() for r in _tests(key, None)}
    contexts: Dict[str, List[Dict[str, Any]]] = {}
    canonical: Dict[str, str] = {}
    for record in _read(RESULTS / key / f"disc_L{level}_s{seed}.jsonl"):
        for proposal in record["proposals"]:
            if PLACEHOLDER.match(proposal["name"]):
                continue
            norm = " ".join(proposal["name"].split()).lower()
            name = canonical.setdefault(norm, " ".join(proposal["name"].split()))
            contexts.setdefault(name, []).append({"text": texts[record["id"]], "values": proposal["values"]})
    return contexts


def cmd_coherence(args):
    from tear_reproduction.coherence import CoherenceScorer
    out = RESULTS / args.dataset / f"coh_L{args.level}_s{args.seed}.json"
    contexts = _proposals(args.dataset, args.level, args.seed)
    schema = _schema(args.dataset, args.level)
    start = time.time()
    scorer = CoherenceScorer()
    scores = scorer.score(DATA[args.dataset][0], schema, list(contexts), permutations=10, seed=args.seed)
    out.write_text(json.dumps({"scores": scores, "seconds": round(time.time() - start, 1)}, indent=1), encoding="utf-8")
    print(f"scored {len(scores)} proposals in {time.time() - start:.0f}s")


def cmd_integrate(args):
    from tear_reproduction.integration import HybridIntegrator
    key, level, seed = args.dataset, args.level, args.seed
    contexts = _proposals(key, level, seed)
    scores = json.loads((RESULTS / key / f"coh_L{level}_s{seed}.json").read_text(encoding="utf-8"))["scores"]
    schema = _schema(key, level)
    pool = load_jsonl(str(DATA[key][1] / "pool.jsonl"))
    # Known attributes in a judged set get a definition from their pool values (A.4 context).
    for attribute in schema:
        rows = [r for r in pool if attribute in r["table"]["headers"]][:3]
        contexts.setdefault(attribute, [
            {"text": r["text"], "values": [v for row in r["table"]["rows"]
                                           for v in row[r["table"]["headers"].index(attribute)]]} for r in rows])
    integrator = HybridIntegrator(_client(args, seed), DATA[key][0], schema, scores)
    start = time.time()
    result = integrator.integrate(list(_proposals(key, level, seed)), contexts)
    ranked = sorted(result["candidates"], key=lambda z: -scores.get(z, 0.0))
    frequency = {z: len(c) for z, c in _proposals(key, level, seed).items()}
    out = {"ranked": ranked, "scores": {z: scores.get(z, 0.0) for z in ranked},
           "cfr_ranked": sorted(frequency, key=lambda z: (-frequency[z], z)),
           "judgments": integrator.log, "definitions": integrator.definitions,
           "seconds": round(time.time() - start, 1), **{k: v for k, v in result.items() if k != "candidates"}}
    (RESULTS / key / f"ar_L{level}_s{seed}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Z={result['proposal_count']} P*={result['low_diversity_sets']} calls={result['llm_calls']} Z'={len(ranked)}")


def elbow(values: List[float]) -> int:
    """Kneedle-style elbow of a descending curve: the rank farthest below the chord."""
    n = len(values)
    if n <= 2:
        return n
    hi, lo = values[0], values[-1]
    span = (hi - lo) or 1.0
    best, k = -1.0, 1
    for i, v in enumerate(values):
        x, y = i / (n - 1), (v - lo) / span
        gap = (1 - x) - y
        if gap > best:
            best, k = gap, i + 1
    return k


def cmd_tearstar(args):
    key, level, seed = args.dataset, args.level, args.seed
    ar = json.loads((RESULTS / key / f"ar_L{level}_s{seed}.json").read_text(encoding="utf-8"))
    k = elbow([ar["scores"][z] for z in ar["ranked"]])
    hidden = {" ".join(h.split()).lower(): h for h in _hidden(key, level)}
    accepted = [hidden[" ".join(z.split()).lower()] for z in ar["ranked"][:k] if " ".join(z.split()).lower() in hidden]
    full = full_schema(DATA[key][0])
    schema = [a for a in full if a in set(_schema(key, level)) | set(accepted)]
    meta = RESULTS / key / f"tearstar_L{level}_s{seed}.json"
    meta.write_text(json.dumps({"k": k, "accepted": accepted, "schema": schema}, indent=1), encoding="utf-8")
    print(f"elbow k={k}, accepted {accepted}")
    out = RESULTS / key / f"te_tearstar_L{level}_s{seed}.jsonl"
    if not accepted:
        # Nothing accepted: the schema is unchanged, so TEAR* is the same TEW run as TEAR.
        source = RESULTS / key / f"te_tear_L{level}_s{seed}.jsonl"
        out.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        print("no attribute accepted; TEAR* = TEAR at this level")
        return
    _run_te(args, key, level, "tear", seed, out, schema=schema)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def _te_scores(path: Path, gold: Dict[str, Any], sims) -> Dict[tuple, float]:
    rows = [r for r in _read(path) if r["id"] in gold]
    out = {}
    for sim in sims:
        f = VALUE_SIMILARITIES[sim]
        out[("header-F1", sim)] = statistics.mean(header_f1(table_headers(r["table"]), table_headers(gold[r["id"]]), f) for r in rows)
        out[("structured-F1", sim)] = statistics.mean(structured_f1(r["table"], gold[r["id"]], f, f) for r in rows)
    return out, len(rows), sum(1 for r in rows if "error" in r)


def _fmt(values: List[float]) -> str:
    mean = 100 * statistics.mean(values)
    std = 100 * statistics.pstdev(values) if len(values) > 1 else 0.0
    return f"{mean:.1f}±{std:.1f}"


def cmd_report(args):
    sims = [s for s in ("EM", "chrf", "BS") if s != "BS" or not args.no_bs]
    lines, data = ["# Reproduction results (Llama-3-8B-Instruct, CPU)", ""], {"table2": [], "ar": [], "tearstar": []}
    lines += ["## Table 2: table extraction, full schema", "",
              "| Dataset | Metric | sim. | Paper RAG | Ours RAG | Paper TEAR | Ours TEAR |", "|---|---|---|---|---|---|---|"]
    notes = []
    for key, (dataset, folder) in DATA.items():
        gold = {r["id"]: r["table"] for r in _read(folder / "test.jsonl")}
        per = {}
        for method in ("rag", "tear"):
            for path in sorted((RESULTS / key).glob(f"te_{method}_Lfull_s*.jsonl")):
                scores, n, errors = _te_scores(path, gold, sims)
                notes.append(f"{dataset} {method.upper()} {path.stem.split('_')[-1]}: {n} texts, {errors} failed")
                for metric_sim, value in scores.items():
                    per.setdefault((method, *metric_sim), []).append(value)
        for metric in ("header-F1", "structured-F1"):
            for sim in sims:
                paper = PAPER_TABLE2[(dataset, metric, sim)]
                ours = [per.get((m, metric, sim)) for m in ("rag", "tear")]
                cells = [_fmt(v) if v else "n/a" for v in ours]
                lines.append(f"| {dataset} | {metric} | {sim} | {paper[0]} | {cells[0]} | {paper[1]} | {cells[1]} |")
                data["table2"].append({"dataset": dataset, "metric": metric, "sim": sim, "paper_rag": paper[0],
                                       "paper_tear": paper[1],
                                       "ours_rag": round(100 * statistics.mean(ours[0]), 1) if ours[0] else None,
                                       "ours_tear": round(100 * statistics.mean(ours[1]), 1) if ours[1] else None})
    lines += ["", *[f"- {n}" for n in notes], ""]

    lines += ["## Figure 4: attribute recommendation recall-AUC (%)", "",
              "| Dataset | Level | Hidden | Z | P* | Judge calls | Z' | elbow k | Accepted | TEAR chrf | TEAR BS | CFR chrf | CFR BS |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, (dataset, folder) in DATA.items():
        for path in sorted((RESULTS / key).glob("ar_L*_s*.json")):
            level, seed = path.stem.split("_")[1][1:], path.stem.split("_")[2][1:]
            ar = json.loads(path.read_text(encoding="utf-8"))
            hidden = _hidden(key, level)
            pad = max(len(ar["ranked"]), len(ar["cfr_ranked"]))
            row = {"dataset": dataset, "level": level, "seed": seed}
            for name, ranked in (("tear", ar["ranked"]), ("cfr", ar["cfr_ranked"])):
                for sim in ("chrf", "BS"):
                    if sim == "BS" and args.no_bs:
                        continue
                    row[f"{name}_{sim}"] = round(100 * recall_auc(ranked, hidden, VALUE_SIMILARITIES[sim], pad_to=pad), 1)
            star_path = RESULTS / key / f"tearstar_L{level}_s{seed}.json"
            star = json.loads(star_path.read_text(encoding="utf-8")) if star_path.exists() else {}
            lines.append(f"| {dataset} | {level} (seed {seed}) | {len(hidden)} | {ar['proposal_count']} | {ar['low_diversity_sets']} | "
                         f"{ar['llm_calls']} | {len(ar['ranked'])} | {star.get('k', '')} | {len(star.get('accepted', []))} | "
                         f"{row.get('tear_chrf', '')} | {row.get('tear_BS', '')} | {row.get('cfr_chrf', '')} | {row.get('cfr_BS', '')} |")
            data["ar"].append(row)
    lines += ["", "The paper reports Figure 4 as bars only (roughly 40-80% for Llama-3-8B).", ""]

    lines += ["## Figure 5/17: TEAR vs TEAR* under exploratory schemas (scored against the full-schema gold)", "",
              "| Dataset | Level | Method | header-F1 EM | header-F1 chrf | structured-F1 EM | structured-F1 chrf |", "|---|---|---|---|---|---|---|"]
    for key, (dataset, folder) in DATA.items():
        gold = {r["id"]: r["table"] for r in _read(folder / "test.jsonl")}
        for level in ("1", "2", "3"):
            for method in ("tear", "tearstar"):
                paths = sorted((RESULTS / key).glob(f"te_{method}_L{level}_s*.jsonl"))
                if not paths:
                    continue
                vals = [_te_scores(p, gold, ["EM", "chrf"])[0] for p in paths]
                cells = [_fmt([v[(m, s)] for v in vals]) for m in ("header-F1", "structured-F1") for s in ("EM", "chrf")]
                lines.append(f"| {dataset} | {level} | {'TEAR*' if method == 'tearstar' else 'TEAR'} | " + " | ".join(cells) + " |")
                data["tearstar"].append({"dataset": dataset, "level": level, "method": method, "cells": cells})
    report = "\n".join(lines) + "\n"
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "report.md").write_text(report, encoding="utf-8")
    (RESULTS / "report.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("embed", "te", "discover", "coherence", "integrate", "tearstar", "report"))
    parser.add_argument("--dataset", choices=sorted(DATA), default="conversation")
    parser.add_argument("--methods", nargs="+", default=["rag", "tear"], choices=("rag", "tear"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--level", default="full")
    parser.add_argument("--n", type=int, default=20, help="Number of test texts (paper: all).")
    parser.add_argument("--base-url", default="http://localhost:1234/v1")
    parser.add_argument("--model", default="meta-llama-3-8b-instruct")
    parser.add_argument("--embedding-model", default="sfr-embedding-mistral-q4_k_m")
    parser.add_argument("--embedding-url", default="http://localhost:8082",
                        help="llama.cpp server for SFR-Embedding-Mistral; '' to use --base-url /embeddings.")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--no-bs", action="store_true")
    args = parser.parse_args(argv)
    globals()[f"cmd_{args.command}"](args)


if __name__ == "__main__":
    main()
