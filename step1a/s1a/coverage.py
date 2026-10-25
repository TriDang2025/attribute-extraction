"""Coverage of the clustered mentions (before / after filtering), overall and per entity."""
import re

import numpy as np
import pandas as pd

WORD = re.compile(r"\S+")
SPEAKERS = ("User:", "System:")


def _doc(d):
    """(text, turns) from a docs.jsonl-style dict or an object with .text / .turns."""
    if isinstance(d, dict):
        return d["text"], d["turns"]
    return d.text, d.turns


def _kept(mentions: pd.DataFrame, cluster_ids=None) -> pd.DataFrame:
    m = mentions[mentions["cluster_id"].fillna("") != ""]
    if cluster_ids is not None:
        m = m[m["cluster_id"].isin(set(cluster_ids))]
    return m


def _overlaps(starts, ends, ms, me) -> np.ndarray:
    """For each [start, end): does it overlap any mention interval [ms, me)? (merge the union, then binary search)"""
    starts, ends = np.asarray(starts), np.asarray(ends)
    if len(ms) == 0 or len(starts) == 0:
        return np.zeros(len(starts), dtype=bool)
    order = np.argsort(ms, kind="stable")
    ms, me = np.asarray(ms)[order], np.asarray(me)[order]
    ustart, uend = [ms[0]], [me[0]]
    for s, e in zip(ms[1:], me[1:]):
        if s < uend[-1]:
            uend[-1] = max(uend[-1], e)
        else:
            ustart.append(s)
            uend.append(e)
    ustart, uend = np.array(ustart), np.array(uend)
    idx = np.searchsorted(ustart, ends, side="left") - 1  # last merged interval starting before end
    return (idx >= 0) & (uend[np.maximum(idx, 0)] > starts)


def _value_hits(mentions, gold_values, cluster_ids=None) -> pd.Series:
    """Bool per verbatim gold value (index = gold_values index): overlaps a clustered mention."""
    g = gold_values[gold_values["verbatim"].astype(bool)]
    hits = pd.Series(False, index=g.index)
    by_doc = {d: x for d, x in _kept(mentions, cluster_ids).groupby("dialogue_id")}
    for d, gg in g.groupby("dialogue_id"):
        if d in by_doc:
            m = by_doc[d]
            hits[gg.index] = _overlaps(gg["char_start"].values, gg["char_end"].values,
                                       m["char_start"].values, m["char_end"].values)
    return hits


def value_coverage(mentions, gold_values, cluster_ids=None) -> float:
    """Verbatim gold values overlapping a clustered mention / all verbatim gold values (nan if none)."""
    h = _value_hits(mentions, gold_values, cluster_ids)
    return float(h.mean()) if len(h) else float("nan")


def _words(docs) -> dict:
    """{dialogue_id: (word starts, word ends, turn index per word)}, speaker prefix words excluded."""
    out = {}
    for did, d in docs.items():
        text, turns = _doc(d)
        s, e, t = [], [], []
        for k, (a, b) in enumerate(turns):
            for i, w in enumerate(WORD.finditer(text, a, b)):
                if i == 0 and w.group() in SPEAKERS:
                    continue
                s.append(w.start())
                e.append(w.end())
                t.append(k)
        out[did] = (np.array(s, dtype=int), np.array(e, dtype=int), np.array(t, dtype=int))
    return out


def _entity_turns(export, docs, gold_values) -> dict:
    """{(dialogue_id, entity): set of turns}. Spans input: turns start_turn..end_turn of the entity's instances.
    Gold input: turns of the dialogue holding a verbatim gold value of that entity."""
    out = {}
    if len(export.mentions) and (export.mentions["input"] == "gold").all():
        g = gold_values[gold_values["verbatim"].astype(bool)]
        for did, gg in g.groupby("dialogue_id"):
            if did not in docs:
                continue
            starts = np.array([a for a, _ in _doc(docs[did])[1]])
            turn = np.searchsorted(starts, gg["char_start"].values, side="right") - 1
            for ent, t in zip(gg["entity_gold"], turn):
                out.setdefault((did, ent), set()).add(int(t))
        return out
    for r in export.instances.itertuples():
        out.setdefault((r.dialogue_id, r.entity), set()).update(range(int(r.start_turn), int(r.end_turn) + 1))
    return out


def coverage_table(export, docs, gold_values, cluster_ids=None) -> pd.DataFrame:
    """Coverage of clustered mentions (restricted to `cluster_ids` when given), rows "all" + one per entity.

    Columns word_cov, value_cov, turn_cov, instance_cov plus numerators / denominators (n_*_cov, n_*).
    - word: \\S+ words of turns (speaker prefix excluded) overlapping a clustered mention span / all words.
      Entity row: only words of the turns belonging to that entity (spans: turns start_turn..end_turn of its
      instances; gold: turns holding its verbatim gold values) and only that entity's mentions count.
    - value: verbatim gold values overlapping a clustered mention (any entity) / all verbatim gold values;
      entity row uses entity_gold == entity, so for spans input (entities E0..) it is nan; use the "all" row.
    - turn: turns with >= 1 clustered mention / all turns (entity row: its turns, its mentions).
    - instance: instances (instances.csv) with >= 1 clustered mention / all instances (entity row: by entity).
    Entities come from instances.csv."""
    m = _kept(export.mentions, cluster_ids)
    words = _words(docs)
    ent_turns = _entity_turns(export, docs, gold_values)
    by_doc = {d: x for d, x in m.groupby("dialogue_id")}
    hits = _value_hits(export.mentions, gold_values, cluster_ids)
    gv = gold_values.loc[hits.index]
    inst_hit = export.instances["instance_id"].isin(set(m["instance_id"]))
    entities = sorted(export.instances["entity"].unique())

    rows = {}
    for ent in [None] + entities:
        wn = wc = tn = tc = 0
        for did, (ws, we, wt) in words.items():
            ts = None if ent is None else ent_turns.get((did, ent), set())
            sel = np.ones(len(ws), dtype=bool) if ent is None else np.isin(wt, list(ts))
            dm = by_doc.get(did)
            if dm is not None and ent is not None:
                dm = dm[dm["entity"] == ent]
            if dm is not None and len(dm):
                cov = _overlaps(ws, we, dm["char_start"].values, dm["char_end"].values)
                mturns = set(dm["turn"].astype(int))
            else:
                cov, mturns = np.zeros(len(ws), dtype=bool), set()
            wn += int(sel.sum())
            wc += int((sel & cov).sum())
            if ent is None:
                tn += len(_doc(docs[did])[1])
                tc += len(mturns)
            else:
                tn += len(ts)
                tc += len(mturns & ts)
        if ent is None:
            vsel = np.ones(len(gv), dtype=bool)
            isel = np.ones(len(inst_hit), dtype=bool)
        else:
            vsel = (gv["entity_gold"] == ent).values
            isel = (export.instances["entity"] == ent).values
        vn, vc = int(vsel.sum()), int(hits.values[vsel].sum())
        inn, ic = int(isel.sum()), int(inst_hit.values[isel].sum())
        rows["all" if ent is None else ent] = dict(
            word_cov=wc / wn if wn else np.nan, value_cov=vc / vn if vn else np.nan,
            turn_cov=tc / tn if tn else np.nan, instance_cov=ic / inn if inn else np.nan,
            n_words_cov=wc, n_words=wn, n_values_cov=vc, n_values=vn,
            n_turns_cov=tc, n_turns=tn, n_inst_cov=ic, n_inst=inn)
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("entity")
