"""Chunk the Conversation dialogues with every method, then score them.

  python scripts/run.py --setting S [--limit 50]          # single dialogues
  python scripts/run.py --setting T --seed 42 [--limit 50] # 20 dialogues stitched per document
  python scripts/run.py ... --methods rsc@bge-m3,chonkie@potion --eval-only

Chunks go to results/<run>/chunks/<method>.jsonl (resumable), scores to results/<run>/metrics.csv.
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chk import config, data, embed, methods, metrics  # noqa: E402

ALL = ["rsc@bge-m3", "chroma@bge-m3", "chonkie@potion", "chonkie@bge-m3", "fixed", "texttiling"]
_tok = None


def ntok(text):
    global _tok
    if _tok is None:
        import tiktoken
        _tok = tiktoken.get_encoding("cl100k_base")
    return len(_tok.encode(text, disallowed_special=()))


def limit_ok(method, chunk, n_chunks):
    """Does a chunk respect the method's own published size limit?"""
    if method.startswith("rsc"):
        return len(chunk) <= config.RSC["t_final"] and (n_chunks == 1 or len(chunk) >= config.RSC["t_merge"])
    if method.startswith("chroma"):
        return ntok(chunk) <= config.CHROMA["max_chunk_size"]
    if method.startswith("chonkie"):
        return ntok(chunk) <= config.CHONKIE["chunk_size"]  # cl100k approximates the model tokenizer
    if method == "fixed":
        return ntok(chunk) <= config.FIXED["chunk_size"]
    return True


def build(enc):
    lc = embed.langchain_embeddings(enc)
    ef = embed.chroma_embedding_function(enc)
    fns = {"rsc@bge-m3": lambda t: methods.rsc(t, enc, lc),
           "chroma@bge-m3": lambda t: methods.chroma(t, ef),
           "fixed": methods.fixed,
           "texttiling": methods.texttiling}
    ch_bge = embed.chonkie_embeddings(enc)
    fns["chonkie@bge-m3"] = lambda t: methods.chonkie(t, ch_bge)
    potion = {}

    def chonkie_potion(t):
        if not potion:
            potion["e"] = embed.chonkie_potion()
        return methods.chonkie(t, potion["e"])
    fns["chonkie@potion"] = chonkie_potion
    return fns


def chunk_all(name, fn, docs, out, enc):
    path = out / "chunks" / f"{name.replace('@', '_')}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if path.exists():
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            done[r["doc_id"]] = r
    with open(path, "a", encoding="utf-8") as f:
        for i, doc in enumerate(docs):
            if doc.doc_id in done:
                continue
            t0 = time.perf_counter()
            chunks = fn(doc.text)
            r = {"doc_id": doc.doc_id, "seconds": time.perf_counter() - t0, "chunks": chunks}
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            done[doc.doc_id] = r
            if (i + 1) % 50 == 0:
                enc.save()
                print(f"  {name}: {i + 1}/{len(docs)}", flush=True)
    enc.save()
    return [done[d.doc_id] for d in docs]


def evaluate(name, rows, docs, qs, q_emb, turn_emb, enc):
    seg_pk, seg_wd, inside, failed = [], [], 0, 0
    tp0 = tp1 = n_hyp = n_ref = 0
    intra, adj, pure, n_turns = [], [], 0, 0
    sizes_c, sizes_t, ok, secs, in_tok = [], [], [], 0.0, 0
    chunk_texts, chunk_meta = [], []
    for doc, r in zip(docs, rows):
        chunks = r["chunks"]
        spans, f = metrics.align(doc.text, chunks)
        failed += f
        gaps, ins = metrics.cuts_to_gaps(doc, spans)
        inside += ins
        s = metrics.pk_wd(doc.n_turns, doc.gold_gaps, gaps)
        if s:
            seg_pk.append(s[0])
            seg_wd.append(s[1])
        a = metrics.boundary_counts(doc.gold_gaps, gaps, 0)
        b = metrics.boundary_counts(doc.gold_gaps, gaps, 1)
        tp0 += a[0]
        tp1 += b[0]
        n_hyp += a[1]
        n_ref += a[2]
        segs = metrics.segments(doc.n_turns, gaps)
        i_, a_, p_ = metrics.coherence(turn_emb[doc.doc_id], segs, doc.domains)
        intra += i_
        adj += a_
        pure += p_
        n_turns += doc.n_turns
        for c in chunks:
            sizes_c.append(len(c))
            sizes_t.append(ntok(c))
            ok.append(limit_ok(name, c, len(chunks)))
        secs += r["seconds"]
        in_tok += ntok(doc.text)
        for st, en in spans:
            chunk_texts.append(doc.text[st:en].strip())
            chunk_meta.append((doc.doc_id, st, en))
    c_emb = enc.encode(chunk_texts)
    enc.save()
    ret = metrics.retrieval(q_emb, qs, c_emb, chunk_meta, {d.doc_id: d.spans for d in docs}, config.TOP_K)
    p0, r0, f0 = metrics.prf(tp0, n_hyp, n_ref)
    p1, r1, f1 = metrics.prf(tp1, n_hyp, n_ref)
    out = {"method": name, "docs": len(docs), "chunks": len(sizes_c),
           "chunks_per_doc": len(sizes_c) / len(docs),
           "chars_mean": np.mean(sizes_c), "chars_min": min(sizes_c), "chars_max": max(sizes_c),
           "tok_mean": np.mean(sizes_t), "tok_max": max(sizes_t),
           "pct_outside_limit": 100 * (1 - np.mean(ok)),
           "sec_per_1k_tok": 1000 * secs / in_tok,
           "cuts_inside_turn_pct": 100 * inside / max(1, len(sizes_c) - len(docs)),
           "align_failed": failed,
           "Pk": np.mean(seg_pk), "WindowDiff": np.mean(seg_wd),
           "P": p0, "R": r0, "F1": f0, "P_tol1": p1, "R_tol1": r1, "F1_tol1": f1,
           "intra_cos": np.mean(intra) if intra else float("nan"),
           "adjacent_cos": np.mean(adj) if adj else float("nan"),
           "purity": pure / n_turns}
    out["coherence_gap"] = out["intra_cos"] - out["adjacent_cos"]
    out.update(ret)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", choices=["S", "T"], required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--methods", default=",".join(ALL))
    ap.add_argument("--eval-only", action="store_true")
    a = ap.parse_args()

    run = f"{a.setting}" + (f"_seed{a.seed}" if a.setting == "T" else "") + (f"_n{a.limit}" if a.limit else "")
    out = config.RESULTS / run
    out.mkdir(parents=True, exist_ok=True)
    dlg = data.load_dialogues(a.limit)
    docs = data.single_docs(dlg) if a.setting == "S" else data.stitched_docs(dlg, a.seed)
    qs = data.queries(dlg, docs)
    print(f"{run}: {len(docs)} docs, {sum(d.n_turns for d in docs)} turns, "
          f"{sum(len(d.gold_gaps) for d in docs)} gold boundaries, {len(qs)} queries", flush=True)

    enc = embed.Encoder()
    fns = build(enc)
    names = a.methods.split(",")
    rows = {}
    for n in names:
        t0 = time.perf_counter()
        if a.eval_only:
            p = out / "chunks" / f"{n.replace('@', '_')}.jsonl"
            got = {json.loads(l)["doc_id"]: json.loads(l) for l in open(p, encoding="utf-8")}
            rows[n] = [got[d.doc_id] for d in docs]
        else:
            rows[n] = chunk_all(n, fns[n], docs, out, enc)
        print(f"chunked {n} in {time.perf_counter() - t0:.0f}s", flush=True)

    temb_all = enc.encode([doc.text[s:e] for doc in docs for s, e in doc.spans])
    turn_emb, i = {}, 0
    for doc in docs:
        turn_emb[doc.doc_id] = temb_all[i:i + doc.n_turns]
        i += doc.n_turns
    q_emb = enc.encode([q["text"] for q in qs])
    enc.save()

    res = []
    for n in names:
        res.append(evaluate(n, rows[n], docs, qs, q_emb, turn_emb, enc))
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[-1].items()}, flush=True)
    with open(out / "metrics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0]))
        w.writeheader()
        for r in res:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print("wrote", out / "metrics.csv")


if __name__ == "__main__":
    main()
