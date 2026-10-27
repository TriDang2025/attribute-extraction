"""Step-3 pilot (LOOP1_CONTRACT.md, T5 eval): LLM decisions -> final attributes, and GLiNER verification.

`decisions_table` reads one response file (one object per cluster), `final_attributes` applies
keep / merge groups (transitive) / split parts (nearest example-vector centroid); not_attribute and
unsure are marked, never deleted. `verify` runs GLiNER with the generated name as the only label over
the pilot entity's instance turns and compares its values with the attribute's mentions (Jaccard).
GLiNER is only called through an injectable `extract_fn(name, doc, windows) -> [span text]`.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import spans as SP
from . import step2 as S2
from .units import turn_of

ACTIONS = ("keep", "merge", "split", "not_attribute", "unsure")
MARKED = ("not_attribute", "unsure")
J_MIN = 0.2
DEC_COLS = ["variant", "run_tag", "cluster_id", "name", "description", "value_type", "action",
            "merge_with", "split", "placement", "evidence"]
ATTR_COLS = ["attr_id", "name", "clusters", "n_mentions", "status", "source"]
VERIFY_COLS = ["variant", "run_tag", "attr_id", "name", "status", "n_gliner", "n_values", "jaccard", "unverified"]


def response_key(path):
    """(variant, run_tag) from responses_<variant>_<run_tag>.jsonl."""
    _, variant, tag = Path(path).stem.split("_", 2)
    return variant, tag


def load_objects(path):
    """Parsed objects (list of dicts) of one response file: the LAST row's `parsed`, else json.loads(raw).
    Earlier rows (a rerun with another model or params appends one) are ignored."""
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    if not rows:
        return []
    parsed = rows[-1].get("parsed")
    if parsed is None:
        try:
            parsed = json.loads(rows[-1].get("raw") or "[]")
        except ValueError:
            parsed = []
    return [o for o in (parsed if isinstance(parsed, list) else [parsed]) if isinstance(o, dict)]


def decisions_table(objs, cluster_ids, variant, run_tag):
    """One row per cluster id (ones the response omits get action ""); unknown actions become "unsure"."""
    by = {str(o.get("cluster_id", "")): o for o in objs}
    rows = []
    for cid in cluster_ids:
        o = by.get(cid)
        if o is None:
            rows.append({"variant": variant, "run_tag": run_tag, "cluster_id": cid, "action": "",
                         **{c: "" for c in DEC_COLS[3:] if c != "action"}})
            continue
        act = o.get("action") if o.get("action") in ACTIONS else "unsure"
        rows.append({"variant": variant, "run_tag": run_tag, "cluster_id": cid,
                     "name": str(o.get("name") or ""), "description": str(o.get("description") or ""),
                     "value_type": str(o.get("value_type") or ""), "action": act,
                     "merge_with": json.dumps(list(o.get("merge_with") or [])),
                     "split": json.dumps(list(o.get("split") or [])),
                     "placement": str(o.get("placement") or ""), "evidence": str(o.get("evidence") or "")})
    return pd.DataFrame(rows, columns=DEC_COLS)


def _find(parent, a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def split_parts(dec_row, ex_mention, ids_idx, x):
    """[(name, unit centroid of its example vectors, [ex_id])] of a split decision; [] if fewer than 2 usable parts."""
    parts = []
    for p in json.loads(dec_row["split"] or "[]"):
        eids = [e for e in (p.get("examples") or [])  # only this cluster's examples
                if str(e).startswith(f"{dec_row['cluster_id']}:") and e in ex_mention and ex_mention[e] in ids_idx]
        if eids:
            c = x[[ids_idx[ex_mention[e]] for e in eids]].mean(axis=0)
            parts.append((str(p.get("name") or ""), c / max(np.linalg.norm(c), 1e-9), eids))
    return parts if len(parts) >= 2 else []


def final_attributes(dec, mentions, ids, x, examples, entity):
    """(assign {mention_id: attr_id}, attrs DataFrame, parts {cluster_id: [(name, [ex_id])]}).

    Merge groups are the transitive union of merge_with (ids outside the pilot entity are ignored; split
    clusters stay out of groups). A split part gets each mention of its cluster whose vector is nearest to
    the part's example centroid. attrs columns: ATTR_COLS (status keep|not_attribute|unsure|missing).
    """
    pm = mentions[(mentions["entity"] == entity) & (mentions["cluster_id"] != "")]
    sizes = pm.groupby("cluster_id").size().to_dict()
    row = {r["cluster_id"]: r for _, r in dec.iterrows()}
    ex_mention = dict(zip(examples["ex_id"], examples["mention_id"].astype(int)))
    ids_idx = {int(i): k for k, i in enumerate(ids)}
    parts = {c: split_parts(row[c], ex_mention, ids_idx, x) for c in sizes if c in row and row[c]["action"] == "split"}
    parts = {c: p for c, p in parts.items() if p}
    parent = {c: c for c in sizes if c not in parts}
    for c in list(parent):
        if c in row and row[c]["action"] == "merge":
            for t in json.loads(row[c]["merge_with"] or "[]"):
                if t in parent:
                    parent[_find(parent, c)] = _find(parent, t)
    groups = {}
    for c in sorted(parent):
        groups.setdefault(_find(parent, c), []).append(c)
    assign, attrs = {}, []
    for members in groups.values():
        members.sort(key=lambda c: (-sizes[c], c))
        named = [c for c in members if c in row and row[c]["name"]]
        acts = [row[c]["action"] if c in row and row[c]["action"] else "missing" for c in members]
        status = "keep" if any(a in ("keep", "merge") for a in acts) else acts[0]
        attr_id = "|".join(sorted(members))
        attrs.append({"attr_id": attr_id, "name": row[named[0]]["name"] if named else "",
                      "clusters": ";".join(sorted(members)), "n_mentions": sum(sizes[c] for c in members),
                      "status": status, "source": "merge" if len(members) > 1 else "keep"})
        for c in members:
            assign.update({int(i): attr_id for i in pm.loc[pm["cluster_id"] == c, "mention_id"]})
    for c, ps in parts.items():
        cen = np.stack([p[1] for p in ps])
        ms = pm.loc[pm["cluster_id"] == c, "mention_id"].astype(int).tolist()
        near = (x[[ids_idx[i] for i in ms]] @ cen.T).argmax(axis=1)
        for k, (name, _, _) in enumerate(ps):
            mine = [i for i, n in zip(ms, near) if n == k]
            attrs.append({"attr_id": f"{c}/{k}", "name": name, "clusters": c, "n_mentions": len(mine),
                          "status": "keep", "source": "split"})
            assign.update({i: f"{c}/{k}" for i in mine})
    return (assign, pd.DataFrame(attrs, columns=ATTR_COLS),
            {c: [(p[0], p[2]) for p in ps] for c, ps in parts.items()})


def relabel(mentions, assign):
    """Copy of mentions with cluster_id = attribute id for the assigned mentions."""
    out = mentions.copy()
    new = out["mention_id"].astype(int).map(assign)
    out["cluster_id"] = new.where(new.notna(), out["cluster_id"])
    return out


def pilot_turns(instances, entity):
    """{dialogue_id: set of turns} of the entity's instances."""
    out = {}
    for _, r in instances[instances["entity"] == entity].iterrows():
        out.setdefault(r["dialogue_id"], set()).update(range(int(r["start_turn"]), int(r["end_turn"]) + 1))
    return out


def gliner_extractor():
    """Default extract_fn: GLiNER medium v2.1 (loaded on first use), the name as the only label (snake_case
    as words: "arrive_by" -> "arrive by")."""
    state = {}

    def run(name, doc, windows):
        if "model" not in state:
            state["model"] = SP.load()
        return [u.text for u in SP.extract_windows(state["model"], doc, windows, labels=[name.replace("_", " ")],
                                                   threshold=SP.THRESHOLD)]
    return run


def _slug(name):
    return re.sub(r"\W+", "_", name.lower()).strip("_")[:40] + "_" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]


def span_values(name, docs, turns, extract_fn, cache_dir=None):
    """Set A: normalized GLiNER values for `name` over the pilot turns; cached per name in cache_dir."""
    path = Path(cache_dir) / f"{_slug(name)}.json" if cache_dir else None
    if path is not None and path.exists():
        return set(json.loads(path.read_text(encoding="utf-8"))["values"])
    vals = set()
    for did, ts in turns.items():
        doc = docs[did]
        wins = [w for w in SP.turn_windows(doc) if turn_of(doc, w[0]) in ts]
        if wins:
            vals.update(S2.normalize(t).lower() for t in extract_fn(name, doc, wins))
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"name": name, "values": sorted(vals)}), encoding="utf-8")
    return vals


def jaccard(a, b):
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def verify(attrs, assign, mentions, docs, instances, entity, extract_fn, cache_dir=None, variant="", run_tag=""):
    """One row per named attribute: A = GLiNER values for its name, B = normalized values of its mentions;
    J = |A and B| / |A or B|; unverified = J < 0.2 (the attribute is kept)."""
    turns = pilot_turns(instances, entity)
    norm = dict(zip(mentions["mention_id"].astype(int), mentions["norm_value"]))
    by_attr = {}
    for mid, aid in assign.items():
        by_attr.setdefault(aid, set()).add(S2.normalize(norm[mid]).lower())
    rows = []
    for _, a in attrs[attrs["name"] != ""].iterrows():
        A = span_values(a["name"], docs, turns, extract_fn, cache_dir)
        B = by_attr.get(a["attr_id"], set())
        j = jaccard(A, B)
        rows.append({"variant": variant, "run_tag": run_tag, "attr_id": a["attr_id"], "name": a["name"],
                     "status": a["status"], "n_gliner": len(A), "n_values": len(B), "jaccard": j,
                     "unverified": j < J_MIN})
    return pd.DataFrame(rows, columns=VERIFY_COLS)
