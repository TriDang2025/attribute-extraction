"""wf_v4.5 (diary Nov 15) W2, part 1: Steps 1a-2 on a raw corpus, without gold.

A corpus is a JSONL file, one dialogue per line: {"id", "text"} with "User: ..." / "System: ..." lines (TEAR's format). The run writes the same
layout as scripts/export_mentions.py, into results/graph_v22_<set>/ (the folder name the frozen Step 3 / Step 4 code reads):
  docs.jsonl, gold_values.csv (empty), gold_attrs.txt (empty), spans/{mentions,clusters,instances}.csv, vectors.npz, labels.csv (every cluster
  "unlabelled": no gold), entities.json ({entity id: name}).
Frozen settings: GLiNER generic labels once per turn, threshold 0.5; segments 5/25 snapped, merge 0.40 (plug_in.DEFAULT_SEG); stage 1 k-means
k = 5 (mentions.build); variant F_m2_t06_bk. The entity names are not gold: every predicted entity is named by the most frequent keyword of
segment.ENTITY_WORDS in the text of its segments (instances); no keyword -> its id; a repeated name gets "_2".
"""
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd

from . import labels as LB
from . import mentions as MN
from . import paths
from . import segment as SG

from chk.data import make_doc  # noqa: E402

VARIANT = "F_m2_t06_bk"
SEED = 42
SET_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def run_dir(set_name, root=paths.ROOT):
    return Path(root) / "results" / f"graph_v22_{set_name}"


def read_corpus(path):
    """{dialogue id: Doc} from a corpus JSONL (turns = the lines of `text`; no domains, so no gold gaps)."""
    docs = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            turns = [t for t in r["text"].split("\n") if t.strip()]
            docs[r["id"]] = make_doc(r["id"], [{"id": r["id"], "turns": turns, "domains": [""] * len(turns)}])
    return docs


def entity_names(instances, docs):
    """{entity id: name}: the most frequent ENTITY_WORDS keyword over the entity's segments (ties: alphabetical), else the id; unique."""
    votes = {}
    for r in instances.itertuples():
        doc = docs[r.dialogue_id]
        text = doc.text[doc.spans[r.start_turn][0]:doc.spans[r.end_turn][1]]
        votes.setdefault(r.entity, Counter()).update(SG.entity_words(text))
    names, used = {}, Counter()
    for e in sorted(votes, key=lambda x: int(x[1:])):
        top = sorted(votes[e].items(), key=lambda kv: (-kv[1], kv[0]))
        base = top[0][0] if top else e.lower()
        used[base] += 1
        names[e] = base if used[base] == 1 else f"{base}_{used[base]}"
    return names


def _gliner_on_gpu():
    """spans.load with the model moved to CUDA when there is a GPU (same model and weights; the laptop stays on CPU)."""
    from . import spans as SP
    load = SP.load

    def load_gpu():
        m = load()
        import torch
        return m.to("cuda") if torch.cuda.is_available() else m
    return SP, load, load_gpu


def step1a(corpus, set_name, enc, root=paths.ROOT, log=print, fresh=False):
    """Steps 1a-2 of the corpus into run_dir(set_name). fresh=True: empty run caches and the encoder's in-memory cache first, so the
    time is that of this corpus alone. Returns {"docs", "mentions", "clusters", "entities", "seconds"}."""
    if not SET_RE.match(set_name):
        raise ValueError(f"set name {set_name!r}: lowercase letters, digits, _ only")
    sys.path.insert(0, str(paths.ROOT / "scripts"))
    import export_mentions as EM   # Step 1a only (GLiNER, chunker): not loaded by the LLM session
    out = run_dir(set_name, root)
    if fresh:
        import shutil
        shutil.rmtree(out / "cache", ignore_errors=True)
        enc.cache.clear()
    t0 = time.time()
    docs = read_corpus(corpus)
    MN.save_shared(out, docs, [], {})
    inp = MN.Inputs(mentions=[], tables={})
    SP, load, load_gpu = _gliner_on_gpu()
    SP.load = load_gpu
    try:
        t_g = time.time()
        inp.spans, inp.segs = EM.span_inputs(docs, enc, out / "cache")
    finally:
        SP.load = load
    t_spans = time.time() - t_g
    EM.apply_variant(inp, VARIANT)
    e = MN.build("spans", docs, enc, SEED, inp=inp)
    MN.save(e, out / "spans")
    LB.gold_labels(e.mentions).to_csv(out / "spans" / "labels.csv", index=False, encoding="utf-8", lineterminator="\n")
    names = entity_names(e.instances, docs)
    (out / "entities.json").write_text(json.dumps(names, indent=1) + "\n", encoding="utf-8", newline="\n")
    enc.save()
    info = {"docs": len(docs), "mentions": len(e.mentions), "clusters": len(e.clusters), "entities": names,
            "seconds": {"spans_and_segments": round(t_spans, 1), "total": round(time.time() - t0, 1)}}
    log(f"step 1a-2 {set_name}: {info}")
    return info


def entity_map(set_name, root=paths.ROOT, min_clusters=1):
    """{name: entity id} of the run's predicted entities that have at least `min_clusters` clusters (all predicted entities by default)."""
    names = json.loads((run_dir(set_name, root) / "entities.json").read_text(encoding="utf-8"))
    cl = pd.read_csv(run_dir(set_name, root) / "spans" / "clusters.csv", dtype=str, keep_default_na=False)
    n = cl["entity"].value_counts()
    return {name: e for e, name in names.items() if n.get(e, 0) >= min_clusters}
