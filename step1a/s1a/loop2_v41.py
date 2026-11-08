"""wf_v4.1 loop 2: "Named Probe + Evidence Check" (pure logic; models are injected).

For each label (entity, name, description, value_type): retrieve the set's most similar turns by
bge-m3 cosine, run GLiNER with that label as the only label on them, make one new cluster of the
spans, then check the cluster against the entity's instances and the existing handover columns.
Everything with a model takes it as an argument: `encoder.encode(list[str]) -> L2-normalised array`,
`predict(texts, label, threshold) -> [[{"start", "end", "score"}, ...] per text]`.
"""

import re
from collections import Counter

import numpy as np

from . import mentions as MN
from . import spans as SP
from . import step2 as S2
from .value_types import value_type_v35

LABEL_KEYS = ("entity", "name", "label", "description", "value_type")


def check_labels(labels):
    """Fail fast on a labels list that is not [{entity, name, label, description, value_type}]."""
    if not isinstance(labels, list) or not labels:
        raise ValueError("labels file must hold a non-empty JSON list")
    for i, r in enumerate(labels):
        miss = [k for k in LABEL_KEYS if not str(r.get(k, "")).strip()]
        if miss:
            raise ValueError(f"label {i} misses {miss}")
    return labels


# ------------------------------------------------------------------ retrieval
def turn_items(docs):
    """One item per GLiNER turn window of every doc: dict(doc_id, turn, start, end, text)."""
    out = []
    for did, doc in docs.items():
        for a, b in SP.turn_windows(doc):
            out.append(dict(doc_id=did, turn=_turn_of(doc, a), start=a, end=b, text=doc.text[a:b]))
    return out


def _turn_of(doc, pos):
    for t, (s, e) in enumerate(doc.spans):
        if s <= pos < e:
            return t
    raise ValueError(f"offset {pos} is in no turn of {doc.doc_id}")


def entity_turn_filter(instances, stage1_entity):
    """{(doc_id, turn): instance_id} of the turns inside predicted segments of one stage-1 entity."""
    out = {}
    for r in instances[instances["entity"] == stage1_entity].itertuples():
        for t in range(int(r.start_turn), int(r.end_turn) + 1):
            out.setdefault((r.dialogue_id, t), r.instance_id)
    return out


def query_text(lab):
    return f"{lab['label']}: {lab['description']}"


def retrieve(items, item_vecs, query_vec, k, allowed=None):
    """Top-k items by cosine to the query; `allowed` = {(doc_id, turn): ...} restricts the pool.
    Returns [(item, cosine)] best first."""
    idx = [i for i, it in enumerate(items) if allowed is None or (it["doc_id"], it["turn"]) in allowed]
    if not idx:
        return []
    sims = item_vecs[idx] @ query_vec
    order = np.argsort(-sims, kind="stable")[:k]
    return [(items[idx[j]], float(sims[j])) for j in order]


# ------------------------------------------------------------------ spans and clusters
def extract(hits, label, predict, threshold):
    """GLiNER spans (one label) on the retrieved turns -> raw span dicts (absolute offsets, raw score)."""
    if not hits:
        return []
    preds = predict([it["text"] for it, _ in hits], label, threshold)
    out = []
    for (it, cos), ents in zip(hits, preds):
        for e in ents:
            out.append(dict(doc_id=it["doc_id"], turn=it["turn"], char_start=it["start"] + e["start"],
                            char_end=it["start"] + e["end"], score=float(e["score"]), retrieval_cos=cos))
    return out


def make_mentions(raw, docs, instance_of, first_id):
    """Fill text, norm_value, left_word, context and instance_id of raw spans; ids from first_id."""
    out = []
    for i, r in enumerate(raw):
        doc = docs[r["doc_id"]]
        s, e, t = r["char_start"], r["char_end"], r["turn"]
        text = doc.text[s:e]
        out.append(dict(
            mention_id=first_id + i, dialogue_id=r["doc_id"], turn=t, instance_id=instance_of.get((r["doc_id"], t), ""),
            char_start=s, char_end=e, text=text, norm_value=S2.normalize(text).lower(),
            left_word=MN.left_word(doc, t, s), context=MN.context(doc, t, s, e), score=r["score"],
            retrieval_cos=r["retrieval_cos"]))
    return out


def value_types(texts):
    cnt = Counter(value_type_v35(t) for t in texts)
    if not cnt:
        return {"dominant": "", "share": 0.0, "counts": {}}
    dom, n = cnt.most_common(1)[0]
    return {"dominant": dom, "share": n / sum(cnt.values()), "counts": dict(cnt)}


def top_values(ms, n=3):
    cnt = Counter(m["norm_value"] for m in ms)
    return [v for v, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


# ------------------------------------------------------------------ evidence
def overlaps(a, b):
    """Char ranges (dialogue, start, end) overlap by >= 1 char."""
    return a[0] == b[0] and min(a[2], b[2]) > max(a[1], b[1])


def cohesion(values, encoder):
    """Mean pairwise cosine of the mentions' values (each mention counts; identical values give 1);
    None below 2 mentions."""
    if len(values) < 2:
        return None
    uniq = sorted(set(values))
    pos = {v: i for i, v in enumerate(uniq)}
    x = encoder.encode(uniq)
    sims = x @ x.T
    ix = np.array([pos[v] for v in values])
    full = sims[np.ix_(ix, ix)]
    n = len(values)
    return float((full.sum() - np.trace(full)) / (n * (n - 1)))


def column_index(columns, mention_table):
    """{mention_id: column name} of the handover columns, and {mention_id: row} of the mention table."""
    col_of = {mid: c["name"] for c in columns for mid in c["mention_ids"]}
    rows = {int(r.mention_id): r for r in mention_table.itertuples() if int(r.mention_id) in col_of}
    return col_of, rows


def evidence(ms, entity_instances, columns, mention_table, encoder, n_dialogues_total=0):
    """Evidence numbers of one cluster's mentions `ms`.
    entity_instances: instance ids of the entity (stage-1) in the set; columns: handover columns of the entity;
    mention_table: the set's mentions.csv rows (mention_id, dialogue_id, instance_id, char_start, char_end).
    support = share of the entity's instances with >= 1 span (share of the set's dialogues, n_dialogues_total,
    when the entity has no instance rows)."""
    insts = {m["instance_id"] for m in ms if m["instance_id"]}
    dlgs = {m["dialogue_id"] for m in ms}
    if entity_instances:
        support, support_unit = len(insts & set(entity_instances)) / len(entity_instances), "instances"
    else:
        support, support_unit = len(dlgs) / max(1, n_dialogues_total), "dialogues (no instances)"
    col_of, col_rows = column_index(columns, mention_table)
    over, conn = Counter(), Counter()
    n_over = 0
    for m in ms:
        hit = {col_of[mid] for mid, r in col_rows.items()
               if overlaps((m["dialogue_id"], m["char_start"], m["char_end"]), (r.dialogue_id, r.char_start, r.char_end))}
        n_over += bool(hit)
        over.update(hit)
    for name in {col_of[mid] for mid, r in col_rows.items() if r.instance_id in insts}:
        conn[name] = len({r.instance_id for mid, r in col_rows.items() if col_of[mid] == name and r.instance_id in insts})
    top_over = over.most_common(1)
    return dict(
        n_mentions=len(ms), n_dialogues=len(dlgs), n_instances=len(insts), n_entity_instances=len(entity_instances),
        support=support, support_unit=support_unit, cohesion=cohesion([m["norm_value"] for m in ms], encoder),
        overlap=n_over / len(ms) if ms else 0.0, overlap_column=top_over[0][0] if top_over else "",
        overlap_by_column=dict(over.most_common()), connection=dict(conn.most_common()),
        n_connected_columns=len(conn), mean_score=float(np.mean([m["score"] for m in ms])) if ms else 0.0)


def decide(ev, cfg):
    """(keep, reason) by the config thresholds: n_dialogues >= min_dialogues, support >= min_support,
    overlap < max_overlap. The reason lists every failed test."""
    fails = []
    if ev["n_dialogues"] < cfg["min_dialogues"]:
        fails.append(f"n_dialogues {ev['n_dialogues']} < {cfg['min_dialogues']}")
    if ev["support"] < cfg["min_support"]:
        fails.append(f"support {ev['support']:.3f} < {cfg['min_support']}")
    if ev["overlap"] >= cfg["max_overlap"]:
        fails.append(f"overlap {ev['overlap']:.3f} >= {cfg['max_overlap']} (mostly column '{ev['overlap_column']}')")
    return not fails, "; ".join(fails) if fails else "all checks passed"


# ------------------------------------------------------------------ one label / all labels
def run_label(lab, number, docs, items, item_vecs, encoder, predict, mention_table, instances, columns,
              stage1_entity, first_id, cfg):
    """One cluster record (clusters.json format) for one label."""
    allowed = entity_turn_filter(instances, stage1_entity) if stage1_entity else None
    qv = encoder.encode([query_text(lab)])[0]
    hits = retrieve(items, item_vecs, qv, cfg["k"], allowed)
    raw = extract(hits, lab["label"], predict, cfg["threshold"])
    ms = make_mentions(raw, docs, allowed or {}, first_id)
    ent_insts = sorted(instances[instances["entity"] == stage1_entity]["instance_id"]) if stage1_entity else []
    ev = evidence(ms, ent_insts, columns, mention_table, encoder, len(docs))
    keep, reason = decide(ev, cfg) if ms else (False, "no spans")
    return dict(
        id=f"L2:{lab['entity']}#{number}", entity=lab["entity"], stage1_entity=stage1_entity, label=lab["label"],
        name=lab["name"], description=lab["description"], label_value_type=lab["value_type"],
        value_type=value_types([m["text"] for m in ms]), n_mentions=len(ms), n_dialogues=ev["n_dialogues"],
        n_instances=ev["n_instances"], top_values=top_values(ms), evidence=ev, keep=keep, reason=reason,
        retrieval=dict(k=cfg["k"], n_turns_retrieved=len(hits), threshold=cfg["threshold"],
                       scope="entity segments" if allowed is not None else "all turns",
                       min_cosine=min((c for _, c in hits), default=None)),
        mentions=ms)


def evidence_rows(clusters):
    """Flat rows for evidence.csv."""
    rows = []
    for c in clusters:
        e = c["evidence"]
        top_conn = next(iter(e["connection"].items()), ("", 0))
        rows.append(dict(
            id=c["id"], entity=c["entity"], label=c["label"], keep=c["keep"], reason=c["reason"],
            n_mentions=e["n_mentions"], n_dialogues=e["n_dialogues"], n_instances=e["n_instances"],
            n_entity_instances=e["n_entity_instances"], support=round(e["support"], 4),
            cohesion="" if e["cohesion"] is None else round(e["cohesion"], 4), overlap=round(e["overlap"], 4),
            overlap_column=e["overlap_column"], connected_columns=e["n_connected_columns"],
            top_connection=top_conn[0], top_connection_instances=top_conn[1], mean_score=round(e["mean_score"], 4),
            value_type=c["value_type"]["dominant"], top_values="|".join(c["top_values"]),
            n_turns_retrieved=c["retrieval"]["n_turns_retrieved"], scope=c["retrieval"]["scope"]))
    return rows


def summary_md(clusters, set_name, cfg, labels_path, seconds):
    """summary.md text: thresholds, counts per entity, one line per cluster."""
    lines = [f"# Loop 2 named probe, {set_name}", "",
             f"Labels: `{labels_path}`; run {seconds:.0f} s. Config: " + ", ".join(f"{k}={v}" for k, v in cfg.items()) + ".",
             "Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.", "",
             "| entity | labels | kept | dropped |", "|---|---|---|---|"]
    for ent in dict.fromkeys(c["entity"] for c in clusters):
        cs = [c for c in clusters if c["entity"] == ent]
        lines.append(f"| {ent} | {len(cs)} | {sum(c['keep'] for c in cs)} | {sum(not c['keep'] for c in cs)} |")
    lines += ["", "| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for c in clusters:
        e = c["evidence"]
        coh = "-" if e["cohesion"] is None else f"{e['cohesion']:.3f}"
        lines.append(f"| {c['id']} | {c['label']} | {'keep' if c['keep'] else 'drop'} | {e['n_mentions']} | "
                     f"{e['n_dialogues']} | {e['support']:.3f} | {coh} | {e['overlap']:.2f} ({e['overlap_column'] or '-'}) | "
                     f"{', '.join(c['top_values'])} | {re.sub(r'[|]', '/', c['reason'])} |")
    return "\n".join(lines) + "\n"
