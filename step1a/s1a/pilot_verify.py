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

ACTIONS = ("keep", "merge", "split", "not_attribute", "unsure", "attribute_cue")
MARKED = ("not_attribute", "unsure", "attribute_cue")  # clusters that are not a column
NOT_ATTRIBUTE_KEY = "not attribute"  # norm_name("not_attribute")
ATTRIBUTE_CUE_KEY = "attribute cue"  # norm_name("attribute_cue")
J_MIN = 0.2
DEC_COLS = ["variant", "run_tag", "cluster_id", "name", "description", "value_type", "action",
            "merge_with", "split", "placement", "evidence"]
ATTR_COLS = ["attr_id", "name", "clusters", "n_mentions", "status", "source", "description"]
VERIFY_COLS = ["variant", "run_tag", "attr_id", "name", "status", "n_gliner", "n_values", "jaccard", "unverified"]
DESC_LABEL_CHARS = 60  # the description label of the GLiNER check is trimmed to this length


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


def norm_name(name):
    """Name key: lowercase, `_`, `-` and space equal, runs of them collapsed."""
    return re.sub(r"[\s_\-]+", " ", str(name or "").lower()).strip()


def _split_obj(path):
    """Parsed dict of the LAST row of one split response file (raw JSON as the fallback), else {}."""
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    if not rows:
        return {}
    parsed = rows[-1].get("parsed")
    if parsed is None:
        try:
            parsed = json.loads(rows[-1].get("raw") or "{}")
        except ValueError:
            parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def load_split_results(dir):
    """{(ent, run_tag): {cluster_id: parsed split object}} from <dir>/<ent>_split_<cid>_<tag>.jsonl
    (the cluster id is written with "#" as "-": E1-1 = E1#1)."""
    out = {}
    for path in sorted(Path(dir).glob("*_split_*.jsonl")):
        ent, rest = path.stem.split("_split_", 1)
        cid, tag = rest.rsplit("_", 1)
        out.setdefault((ent, tag), {})[cid.replace("-", "#")] = _split_obj(path)
    return out


def decisions_from_v2(obj, cluster_ids, variant, run_tag, split_results=None, require_mixed=True):
    """v1-style decision table (DEC_COLS) from a v2 object {attributes, clusters} (PILOT_V31_CONTRACT adapter).

    Clusters sharing an attribute -> merge (merge_with = the others); a single one -> keep; "not_attribute" ->
    not_attribute; "attribute_cue" -> attribute_cue (a question about an attribute, not a column); a name not in the list -> unsure; omitted clusters get action "". A cluster that is `mixed`
    (any cluster when require_mixed is False) and has a split result {is_mixed: true, parts: [{name, examples}]}
    -> split with those parts. Not-attribute, attribute-cue and unsure rows carry no name."""
    obj = obj if isinstance(obj, dict) else {}
    attrs = {norm_name(a.get("name")): a for a in obj.get("attributes") or [] if isinstance(a, dict) and a.get("name")}
    by = {str(c.get("cluster_id", "")): c for c in obj.get("clusters") or [] if isinstance(c, dict)}
    split_results = split_results or {}
    kind, split = {}, {}
    for cid in cluster_ids:
        c = by.get(cid)
        if c is None:
            continue
        key = norm_name(c.get("attribute"))
        s = split_results.get(cid) or {}
        parts = [p for p in s.get("parts") or [] if isinstance(p, dict)
                 and any(str(e).startswith(f"{cid}:") for e in p.get("examples") or [])]  # parts with no own example are dropped
        if key == NOT_ATTRIBUTE_KEY:
            kind[cid] = "not_attribute"
        elif key == ATTRIBUTE_CUE_KEY:
            kind[cid] = "attribute_cue"
        elif key not in attrs:
            kind[cid] = "unsure"
        elif s.get("is_mixed") and len(parts) >= 2 and (c.get("mixed") or not require_mixed):
            kind[cid], split[cid] = "split", parts
        else:
            kind[cid] = key
    groups = {}
    for cid, k in kind.items():
        if k not in MARKED + ("split",):
            groups.setdefault(k, []).append(cid)
    rows = []
    for cid in cluster_ids:
        if cid not in by:
            rows.append({"variant": variant, "run_tag": run_tag, "cluster_id": cid, "action": "",
                         **{col: "" for col in DEC_COLS[3:] if col != "action"}})
            continue
        c, k = by[cid], kind[cid]
        a = attrs.get(norm_name(c.get("attribute"))) if k not in MARKED else None
        others = [o for o in groups.get(k, []) if o != cid]
        action = k if k in MARKED or k == "split" else ("merge" if others else "keep")
        rows.append({"variant": variant, "run_tag": run_tag, "cluster_id": cid,
                     "name": str(a.get("name") or "") if a else "",
                     "description": str(a.get("description") or "") if a else "", "value_type": "",
                     "action": action, "merge_with": json.dumps(others),
                     "split": json.dumps([{"name": str(p.get("name") or ""), "examples": list(p.get("examples") or [])}
                                          for p in split.get(cid, [])]),
                     "placement": str(c.get("placement") or ""), "evidence": str(c.get("evidence") or "")})
    return pd.DataFrame(rows, columns=DEC_COLS)


def _find(parent, a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def split_parts(dec_row, ex_mention, ids_idx, x):
    """[(name, unit centroid of its example vectors, [ex_id], merge_into)] of a split decision; [] if fewer than 2
    usable parts. merge_into: the clusters of the attribute a wf_v3.2 reconcile joined the part to ([] if none)."""
    parts = []
    for p in json.loads(dec_row["split"] or "[]"):
        eids = [e for e in (p.get("examples") or [])  # only this cluster's examples
                if str(e).startswith(f"{dec_row['cluster_id']}:") and e in ex_mention and ex_mention[e] in ids_idx]
        if eids:
            c = x[[ids_idx[ex_mention[e]] for e in eids]].mean(axis=0)
            parts.append((str(p.get("name") or ""), c / max(np.linalg.norm(c), 1e-9), eids, list(p.get("merge_into") or [])))
    return parts if len(parts) >= 2 else []


def left_word_map(mentions, docs=None):
    """{mention_id: left word} for the P4 cue spread: the mentions table's `left_word` column when it has one, else
    computed with mentions.left_word from docs {dialogue_id: Doc} (columns dialogue_id, turn, char_start)."""
    ids = mentions["mention_id"].astype(int)
    if "left_word" in mentions.columns:
        return dict(zip(ids, mentions["left_word"].astype(str)))
    from . import mentions as MN  # heavy import, only for the fallback
    return {int(i): MN.left_word(docs[d], int(t), int(s)) for i, d, t, s in
            zip(ids, mentions["dialogue_id"], mentions["turn"], mentions["char_start"])}


def _cue_parts(ms, near, ps, ex_mention, left_words):
    """Part index of each mention of a split cluster: the one part whose cue set (left words of its example
    mentions) holds the mention's left word, else the nearest centroid (`near`)."""
    cues = [{left_words.get(ex_mention[e], "") for e in p[2] if e in ex_mention} - {""} for p in ps]
    out = []
    for i, n in zip(ms, near):
        hit = [k for k, c in enumerate(cues) if left_words.get(i, "") in c]
        out.append(hit[0] if len(hit) == 1 else n)
    return out


def final_attributes(dec, mentions, ids, x, examples, entity, left_words=None):
    """(assign {mention_id: attr_id}, attrs DataFrame, parts {cluster_id: [(name, [ex_id])]}).

    left_words {mention_id: word} (left_word_map) switches on the P4 cue spread of split clusters; None = nearest
    centroid only.

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
                      "status": status, "source": "merge" if len(members) > 1 else "keep",
                      "description": row[named[0]]["description"] if named else ""})
        for c in members:
            assign.update({int(i): attr_id for i in pm.loc[pm["cluster_id"] == c, "mention_id"]})
    attr_of = {m: a for a in attrs for m in a["clusters"].split(";")}
    for c, ps in parts.items():
        cen = np.stack([p[1] for p in ps])
        ms = pm.loc[pm["cluster_id"] == c, "mention_id"].astype(int).tolist()
        near = (x[[ids_idx[i] for i in ms]] @ cen.T).argmax(axis=1)
        if left_words is not None:
            near = _cue_parts(ms, near, ps, ex_mention, left_words)
        for k, (name, _, _, into) in enumerate(ps):
            mine = [i for i, n in zip(ms, near) if n == k]
            target = attr_of.get(into[0]) if into else None
            if target is not None:  # reconcile joined the part to an existing attribute
                target["n_mentions"] += len(mine)
                assign.update({i: target["attr_id"] for i in mine})
                continue
            attrs.append({"attr_id": f"{c}/{k}", "name": name, "clusters": c, "n_mentions": len(mine),
                          "status": "keep", "source": "split", "description": ""})
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


def verify(attrs, assign, mentions, docs, instances, entity, extract_fn, cache_dir=None, variant="", run_tag="",
           use_description=False):
    """One row per named attribute: A = GLiNER values for its label, B = normalized values of its mentions;
    J = |A and B| / |A or B|; unverified = J < 0.2 (the attribute is kept).
    use_description=True: the label is the attribute's description (first 60 chars; attributes without one are
    skipped) and the rows get label_kind "description" (default: the name, no label_kind column)."""
    turns = pilot_turns(instances, entity)
    norm = dict(zip(mentions["mention_id"].astype(int), mentions["norm_value"]))
    by_attr = {}
    for mid, aid in assign.items():
        by_attr.setdefault(aid, set()).add(S2.normalize(norm[mid]).lower())
    rows = []
    for _, a in attrs[attrs["name"] != ""].iterrows():
        label = str(a["description"] or "").strip()[:DESC_LABEL_CHARS].strip() if use_description else a["name"]
        if not label:
            continue
        A = span_values(label, docs, turns, extract_fn, cache_dir)
        B = by_attr.get(a["attr_id"], set())
        j = jaccard(A, B)
        rows.append({"variant": variant, "run_tag": run_tag, "attr_id": a["attr_id"], "name": a["name"],
                     "status": a["status"], "n_gliner": len(A), "n_values": len(B), "jaccard": j,
                     "unverified": j < J_MIN})
    if use_description:
        return pd.DataFrame(rows, columns=VERIFY_COLS).assign(label_kind="description")
    return pd.DataFrame(rows, columns=VERIFY_COLS)
