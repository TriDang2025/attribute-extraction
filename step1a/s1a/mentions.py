"""Task 0 of the Step 1a graph work: the frozen pipeline's mentions, clusters and entity instances
as tables (contract: GRAPH_CONTRACT.md).

Two inputs: "spans" (GLiNER spans; stage 1 = k-means on segment vectors with one seed; stage 2 =
the original Step 2 (raw strings, average, t 0.4), the best on per-turn spans in v3; booking =
(dialogue, segment)) and "gold" (verbatim gold mentions grouped by gold
entity; window Step 2, booking = (dialogue, entity)). Everything the pipeline needs besides docs
and the encoder comes in `Inputs`, so tests and re-clustering on a subset of docs never touch GLiNER.
"""

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import gold as G
from . import metrics as M
from . import paths
from . import step2 as S2
from . import units as U
from chk.data import Doc

sys.path.insert(0, str(paths.ROOT / "scripts"))
import plug_in as PI  # noqa: E402  (piece_of)
import relabel as RL  # noqa: E402  (segment_clusters)

WORDS = 10  # words each side in `context`
STAGE2_T = 0.4  # original Step 2 for spans (v3: 0.614 vs 0.546 for the joint Step 2 on per-turn spans)
STEP2_GOLD = paths.RESULTS / "v3_n50" / "chosen_step2_window.json"
MENTION_INT = ("mention_id", "turn", "char_start", "char_end")
INSTANCE_INT = ("start_turn", "end_turn")
GOLD_INT = ("char_start", "char_end")
_PUNCT = re.compile(r"^\W+|\W+$")


@dataclass
class Inputs:
    """What `build` needs besides docs and the encoder."""
    mentions: list        # gold.mentions_for(...): all gold mentions incl. non-verbatim
    tables: dict          # doc_id -> gold table (instances of the gold input)
    spans: list = None    # span Units with .score (GLiNER, threshold applied); spans input
    segs: list = None     # segment Units (merged segments); spans input
    cfg_spans: dict = None  # None = original Step 2 (raw strings, t 0.4)
    cluster_fn: object = None  # spans: f(spans, docs, enc, groups, books) -> (x, labels); overrides cfg_spans
    cfg_gold: dict = None


@dataclass
class Export:
    mentions: pd.DataFrame
    clusters: pd.DataFrame
    instances: pd.DataFrame
    ids: np.ndarray
    x: np.ndarray


def _load_cfg(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def turn_bounds(doc, turn):
    """(start, end) of the turn's text without its speaker prefix."""
    lo, hi = doc.spans[turn]
    m = S2._SPEAKER.match(doc.text, lo, hi)
    return (m.end() if m else lo), hi


def left_word(doc, turn, start):
    """Nearest word left of `start` inside the turn: lowercased, punctuation stripped, "" if none."""
    lo, _ = turn_bounds(doc, turn)
    for tok in reversed(doc.text[lo:max(lo, start)].split()):
        w = _PUNCT.sub("", tok).lower()
        if w:
            return w
    return ""


def context(doc, turn, start, end, k=WORDS):
    """The turn's text from k words before the mention to k words after it (speaker prefix excluded)."""
    lo, hi = turn_bounds(doc, turn)
    left = [m.start() for m in re.finditer(r"\S+", doc.text[lo:max(lo, start)])][-k:]
    right = [m.end() for m in re.finditer(r"\S+", doc.text[end:hi])][:k]
    return doc.text[lo + left[0] if left else start:end + right[-1] if right else end]


def cluster_ids(entities, labels):
    """"<entity>#<k>", k numbering each entity's clusters in order of first appearance; "" without entity."""
    nxt, seen, out = Counter(), {}, []
    for e, lab in zip(entities, labels):
        if not e:
            out.append("")
            continue
        if (e, lab) not in seen:
            seen[(e, lab)] = nxt[e]
            nxt[e] += 1
        out.append(f"{e}#{seen[(e, lab)]}")
    return out


def cluster_table(m):
    rows = []
    for cid, g in m[m.cluster_id != ""].groupby("cluster_id", sort=False):
        cnt = Counter(g.norm_value)
        top = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        rows.append((cid, g.entity.iloc[0], len(g), len(cnt), "|".join(v for v, _ in top)))
    rows.sort(key=lambda r: (r[1], int(r[0].rsplit("#", 1)[1])))
    return pd.DataFrame(rows, columns=["cluster_id", "entity", "n_mentions", "n_values", "top_values"])


def _mention_table(inp_name, units, docs, entity, entity_gold, instance, gold_attr, score, cid):
    rows = []
    for i, u in enumerate(units):
        doc = docs[u.doc_id]
        rows.append(dict(
            mention_id=i, input=inp_name, dialogue_id=u.doc_id, turn=u.turn, char_start=u.start,
            char_end=u.end, text=u.text, norm_value=S2.normalize(u.text).lower(),
            left_word=left_word(doc, u.turn, u.start), context=context(doc, u.turn, u.start, u.end),
            cluster_id=cid[i], entity=entity[i], entity_gold=entity_gold[i], instance_id=instance[i],
            gold_attr=gold_attr[i], gliner_score=score[i]))
    cols = ["mention_id", "input", "dialogue_id", "turn", "char_start", "char_end", "text", "norm_value",
            "left_word", "context", "cluster_id", "entity", "entity_gold", "instance_id", "gold_attr",
            "gliner_score"]
    return pd.DataFrame(rows, columns=cols)


def _instances(rows):
    return pd.DataFrame(rows, columns=["instance_id", "entity", "dialogue_id", "start_turn", "end_turn"])


def _spans(docs, enc, seed, inp):
    spans = [u for u in inp.spans if u.doc_id in docs]
    segs = [c for c in inp.segs if c.doc_id in docs]
    mentions = [m for m in inp.mentions if m.doc_id in docs]
    M.match_all(spans, mentions)
    clab = RL.segment_clusters(segs, enc, k=min(5, len(segs)), seeds=(seed,))[seed]
    piece = PI.piece_of(spans, segs)
    groups = [int(clab[p]) if p >= 0 else -1 for p in piece]
    books = [(u.doc_id, p) for u, p in zip(spans, piece)]
    if inp.cluster_fn:
        x, lab = inp.cluster_fn(spans, docs, enc, groups, books)
    elif inp.cfg_spans:
        x, ctx = S2.step2_vectors(spans, docs, enc, inp.cfg_spans)
        lab = S2.step2_cluster(spans, groups, books, x, ctx, inp.cfg_spans)
    else:
        x = enc.encode([u.text for u in spans])
        lab = RL.stage2(x, groups, STAGE2_T)
    entity = [f"E{g}" if g >= 0 else "" for g in groups]
    local, per_doc, inst_rows = {}, Counter(), []
    for gi, c in enumerate(segs):
        local[gi] = per_doc[c.doc_id]
        per_doc[c.doc_id] += 1
        doc = docs[c.doc_id]
        ts = U.turns_overlapping(doc, c.start, c.end) or [U.turn_of(doc, c.start)]
        inst_rows.append((f"{c.doc_id}|{local[gi]}", f"E{clab[gi]}", c.doc_id, min(ts), max(ts)))
    instance = [f"{u.doc_id}|{local[p]}" if p >= 0 else "" for u, p in zip(spans, piece)]
    entity_gold = [S2.gold_entity(mentions[u.matched[0]], docs[u.doc_id]).lower() if u.matched else ""
                   for u in spans]
    gold_attr = [";".join(sorted(u.labels)) for u in spans]
    m = _mention_table("spans", spans, docs, entity, entity_gold, instance, gold_attr,
                       [float(u.score) for u in spans], cluster_ids(entity, lab))
    return m, _instances(inst_rows), x


def _gold(docs, enc, inp):
    cfg = inp.cfg_gold or _load_cfg(STEP2_GOLD)
    mentions = [m for m in inp.mentions if m.doc_id in docs]
    units = [m for m in mentions if m.verbatim]
    groups = [S2.gold_entity(m, docs[m.doc_id]) for m in units]
    books = [(m.doc_id, g) for m, g in zip(units, groups)]
    x, ctx = S2.step2_vectors(units, docs, enc, cfg)
    lab = S2.step2_cluster(units, groups, books, x, ctx, cfg)
    entity = [g.lower() for g in groups]
    inst_rows = []
    for did, doc in docs.items():
        if did not in inp.tables:
            continue
        for ent in sorted({G.entity(a) for a in G.cell_values(inp.tables[did])}):
            ts = [t for t, d in enumerate(doc.domains) if d.lower() == ent]
            inst_rows.append((f"{did}|{ent}", ent, did, min(ts, default=-1), max(ts, default=-1)))
    m = _mention_table("gold", units, docs, entity, entity, [f"{u.doc_id}|{e}" for u, e in zip(units, entity)],
                       [";".join(sorted(u.labels)) for u in units], [1.0] * len(units),
                       cluster_ids(entity, lab))
    return m, _instances(inst_rows), x


def build(input, docs, enc, seed=42, *, inp):
    """Mentions, clusters, instances and Step-2 vectors of one input ("spans" | "gold") over docs
    ({doc_id: Doc}). `inp` holds the rest of the pipeline's inputs; a subset of docs and another
    seed re-cluster for the stability runs."""
    if input == "spans":
        m, inst, x = _spans(docs, enc, seed, inp)
    elif input == "gold":
        m, inst, x = _gold(docs, enc, inp)
    else:
        raise ValueError(input)
    x = S2._unit(np.asarray(x, dtype=float)).astype(np.float32)
    return Export(m, cluster_table(m), inst, m.mention_id.to_numpy(), x)


# ------------------------------------------------------------------ files
def _csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def _read(path, ints=(), floats=()):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    for c in ints:
        df[c] = df[c].astype(int)
    for c in floats:
        df[c] = df[c].astype(float)
    return df


def save(e, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _csv(e.mentions, out_dir / "mentions.csv")
    _csv(e.clusters, out_dir / "clusters.csv")
    _csv(e.instances, out_dir / "instances.csv")
    np.savez(out_dir / "vectors.npz", mention_id=np.asarray(e.ids, dtype=int), x=e.x.astype(np.float32))


def load(out_dir):
    out_dir = Path(out_dir)
    v = np.load(out_dir / "vectors.npz")
    return Export(_read(out_dir / "mentions.csv", MENTION_INT, ("gliner_score",)),
                  _read(out_dir / "clusters.csv", ("n_mentions", "n_values")),
                  _read(out_dir / "instances.csv", INSTANCE_INT), v["mention_id"], v["x"])


def gold_table(docs, mentions):
    """One row per gold mention (verbatim or not), as gold_values.csv."""
    rows = []
    for m in mentions:
        ent = S2.gold_entity(m, docs[m.doc_id] if m.verbatim else None).lower()
        rows.append((m.doc_id, ";".join(sorted(m.labels)), ent, m.value, m.start, m.end, m.verbatim))
    return pd.DataFrame(rows, columns=["dialogue_id", "gold_attr", "entity_gold", "value", "char_start",
                                       "char_end", "verbatim"])


def save_shared(run_dir, docs, mentions, classes):
    """docs.jsonl, gold_values.csv, gold_attrs.txt (classes: gold.merge_classes(...))."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "docs.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for did, d in docs.items():
            f.write(json.dumps({"dialogue_id": did, "text": d.text, "turns": [list(t) for t in d.spans]}) + "\n")
    _csv(gold_table(docs, mentions), run_dir / "gold_values.csv")
    (run_dir / "gold_attrs.txt").write_text("\n".join(sorted(set(classes.values()))) + "\n",
                                            encoding="utf-8", newline="\n")


def load_shared(run_dir):
    """(docs {doc_id: Doc} without domains, gold_values DataFrame, gold_attrs list)."""
    run_dir = Path(run_dir)
    docs = {}
    for line in open(run_dir / "docs.jsonl", encoding="utf-8"):
        r = json.loads(line)
        docs[r["dialogue_id"]] = Doc(r["dialogue_id"], r["text"], [tuple(t) for t in r["turns"]], [], [])
    gv = _read(run_dir / "gold_values.csv", GOLD_INT)
    gv["verbatim"] = gv["verbatim"] == "True"
    attrs = (run_dir / "gold_attrs.txt").read_text(encoding="utf-8").splitlines()
    return docs, gv, [a for a in attrs if a]
