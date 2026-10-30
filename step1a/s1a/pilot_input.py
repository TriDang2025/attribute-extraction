"""T5 input: the Step-3 pilot prompt for one predicted entity (contract: LOOP1_CONTRACT.md, "T5 input").

One prompt holds every cluster of the entity: counts, 8 diverse examples, a low-confidence flag, merge
hints and placement hints. Hints are labelled "suggestion, no decision". Withheld: gold entity and
attribute names, identifier/column/table hints, spans sub-entities. Three variants: full, nocontext
(values only), nohints (no merge/placement hints). Example choice is seeded and deterministic.
"""

import re
import zlib
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from . import graph as GR
from . import llm_cache as LC
from . import mentions as MN
from . import signals as SG
from . import step2 as S2

VARIANTS = ("full", "nocontext", "nohints")
VARIANTS_V2 = ("v2", "v2_hints", "v2_nocontext")
K_EXAMPLES = 8
N_MERGE = 3
CARD_SEP = 1.2      # mean distinct values per instance above this favours a separate table
TOP_OTHER = 3       # biggest clusters shown per other entity
TURN_CHARS = 400    # a longer turn is cut around the mention
PREV_CHARS = 200
SEPARATE = "separate table"
SIGNALS = ("entity share", "co-occurrence", "similarity", "cardinality", "shared values")
INSTRUCTION = """\
You help design a database schema from a dialogue corpus. Below is ONE entity (a candidate table) found
by clustering text spans. Each cluster of the entity is a candidate attribute (column). For EVERY cluster:
1. Give it a short database attribute name (snake_case, e.g. "graduation_year") and a one-sentence description,
   or mark it as not an attribute.
2. Choose one action: keep (a real attribute as it is), merge (same attribute as other listed clusters; list
   them in merge_with), split (the cluster mixes several attributes; list the parts in split, each with
   a name and the example ids that belong to it), not_attribute (noise or not a database attribute),
   unsure.
3. Choose where the attribute belongs: pick ONE placement from the listed options and copy its text exactly.
4. Quote one example span from the cluster as evidence.
Examples are marked with [[...]] inside the turn they come from. Lines labelled "suggestion, no decision"
are weak automatic hints; they can be wrong, so decide from the examples.
Return ONLY one JSON array, one object per cluster, nothing before or after it. Each object:
{"cluster_id": "E1#3", "name": "str", "description": "str",
 "value_type": "time|day|number|name|code|other",
 "action": "keep|merge|split|not_attribute|unsure",
 "merge_with": ["E1#5"], "split": [{"name": "str", "examples": ["E1#3:0"]}],
 "placement": "<option text exactly as listed>", "evidence": "<one quoted example>"}
Use [] for merge_with and split when they do not apply."""

INSTRUCTION_V2 = """\
You help design a database schema from a dialogue corpus. Below is ONE entity (a candidate table) found
by clustering text spans. Each cluster of the entity is a candidate attribute (column). Work in two steps.
1. Write the list of the entity's distinct attributes, each once: a snake_case name, a one-sentence
   description and a short role. Use role-specific names: when values play different roles (where
   something starts vs where it ends, the earliest vs the latest time allowed), give each role its own
   attribute and put the role in the name; do not use one general name for both.
2. Assign EVERY cluster to one listed attribute by name. Several clusters may share one attribute (then they
   are the same attribute). Use "not_attribute" for noise. Noise is common: yes, ok, thanks, booking words,
   and values that a database would not store. If a cluster holds two attributes (two roles), assign its
   most frequent attribute and set "mixed" to true.
Also choose where each cluster belongs: pick ONE placement from the listed options and copy its text
exactly. Quote one example span as evidence. Examples are marked with [[...]] inside the turn they come from.
Lines labelled "automatic suggestion" are weak hints and can be wrong; decide from the examples.
Return ONLY one JSON object, nothing before or after it. Example of the shape (other names and values):
{"attributes": [{"name": "graduation_year", "description": "year the degree was finished", "role": "end of the studies"}],
 "clusters": [{"cluster_id": "E9#0", "attribute": "graduation_year", "evidence": "I finished in [[2019]]",
               "mixed": false, "placement": "current entity E9"},
              {"cluster_id": "E9#1", "attribute": "not_attribute", "evidence": "[[ok]] thanks",
               "mixed": false, "placement": "current entity E9"}]}"""

INSTRUCTION_SPLIT = """\
Below are examples of ONE cluster of values taken from a dialogue corpus. Decide whether the cluster mixes
two or more attributes (roles): values that look alike but play different roles in the dialogue.
Examples are marked with [[...]] inside the turn they come from.
If it does mix, give the parts: for each part a snake_case name, a short role, and the ids of the examples
that belong to it. Every example must be in exactly one part. If it does not mix, give is_mixed false and
no parts.
Return ONLY one JSON object, nothing before or after it:
{"cluster_id": "C#0", "is_mixed": true,
 "parts": [{"name": "str", "role": "str", "examples": ["C#0:s0"]}]}"""


@dataclass
class ClusterInput:
    cluster_id: str
    n_mentions: int
    n_values: int
    low_conf: bool
    examples: list                 # [(ex_id, mention_id)]
    merge: list = field(default_factory=list)      # [dict(other, pct, exclusive, left, right, same_type)]
    placement: list = field(default_factory=list)  # [dict(option, score, signals {name: value})], ranked


@dataclass
class PilotInput:
    entity: str
    clusters: list
    options: list                  # [(option text, description)]
    others: dict                   # other entity -> top values of its biggest clusters


# ------------------------------------------------------------------ pilot entity
def find_pilot_entity(mentions, gold_entity="train"):
    """The predicted entity whose clustered mentions have majority `entity_gold` == gold_entity
    (unmatched spans, entity_gold "", do not vote); most train-heavy first if several."""
    m = mentions[(mentions["cluster_id"] != "") & (mentions["entity_gold"] != "")]
    best = []
    for ent, g in m.groupby("entity"):
        cnt = Counter(g["entity_gold"])
        top = max(cnt.values())
        if cnt.get(gold_entity, 0) == top:
            best.append((-top / len(g), ent))
    if not best:
        raise ValueError(f"no predicted entity has majority entity_gold == {gold_entity!r}")
    return sorted(best)[0][1]


# ------------------------------------------------------------------ examples
# wf_v3.3 P3: words left of a span that mark where something starts / ends (used only for example choice)
CUE_ROLES = {"start": frozenset({"from", "leaving", "leave", "depart", "departing", "departs", "after"}),
             "end": frozenset({"to", "arrive", "arriving", "arrives", "into", "by", "before"})}


def _role_first(by_val, pools, roles, words):
    """(did, mid) of the best mention whose left word is in `words`: the most frequent value among such
    mentions (ties by value), its first such mention in the pool order; removed from the pool. None if none."""
    cnt = Counter()
    for v, items in by_val.items():
        cnt[v] = sum(1 for _, mid in items if roles.get(mid, "") in words)
    best = [v for v in cnt if cnt[v] > 0]
    if not best:
        return None
    v = min(best, key=lambda x: (-cnt[x], x))
    i = next(j for j, (_, mid) in enumerate(pools[v]) if roles.get(mid, "") in words)
    return pools[v].pop(i)


def select_examples(g, k=K_EXAMPLES, seed=0, roles=None):
    """Mention ids of one cluster's mentions `g` (rows of mentions.csv): round-robin over the distinct
    values (most frequent first), within a value a mention from a dialogue not yet used when possible.
    Fewer than k when the cluster is smaller; never k copies of one value when more values exist.
    `roles` {mention_id: left word}: when the cluster has both start and end mentions (CUE_ROLES), the
    first two picks are one of each (most frequent value of each role); the rest is the round-robin."""
    rng = np.random.default_rng([seed, zlib.crc32(str(g["cluster_id"].iloc[0]).encode())])
    by_val = {}
    for v, did, mid in zip(g["norm_value"], g["dialogue_id"], g["mention_id"]):
        by_val.setdefault(v, []).append((did, int(mid)))
    order = sorted(by_val, key=lambda v: (-len(by_val[v]), v))
    pools = {}
    for v in order:
        items = by_val[v]
        pools[v] = [items[i] for i in rng.permutation(len(items))]
    picked, used = [], set()
    if roles and k >= 2:
        has = {r: any(roles.get(int(m), "") in w for m in g["mention_id"]) for r, w in CUE_ROLES.items()}
        if all(has.values()):
            for r in ("start", "end"):
                did, mid = _role_first(by_val, pools, roles, CUE_ROLES[r])
                used.add(did)
                picked.append(mid)
    while len(picked) < k and any(pools.values()):
        for v in order:
            if len(picked) >= k:
                break
            if not pools[v]:
                continue
            i = next((j for j, (d, _) in enumerate(pools[v]) if d not in used), 0)
            did, mid = pools[v].pop(i)
            used.add(did)
            picked.append(mid)
    return picked


def low_conf_clusters(mentions, entity):
    """Clusters of the entity whose mean gliner_score is in the bottom third (n // 3 clusters)."""
    m = mentions[(mentions["entity"] == entity) & (mentions["cluster_id"] != "")]
    means = m.groupby("cluster_id")["gliner_score"].mean()
    order = sorted(means.index, key=lambda c: (means[c], c))
    return set(order[:len(order) // 3])


# ------------------------------------------------------------------ example text
def _speaker(doc, turn):
    lo, hi = doc.spans[turn]
    m = S2._SPEAKER.match(doc.text, lo, hi)
    return m.group(1).lower() if m else "unknown"


def _flat(s):
    return re.sub(r"\s+", " ", s).strip()


def _cut(text, a, b, limit):
    """text cut to about `limit` chars around [a, b) (the marked mention), with "..." at cut ends."""
    if len(text) <= limit:
        return text
    pad = max(0, (limit - (b - a)) // 2)
    lo, hi = max(0, a - pad), min(len(text), b + pad)
    return ("..." if lo else "") + text[lo:hi] + ("..." if hi < len(text) else "")


def example_text(doc, row, context=True):
    """(speaker, previous turn or "", turn with the mention as [[...]]); `context` False: value only."""
    s, e, turn = int(row["char_start"]), int(row["char_end"]), int(row["turn"])
    if not context:
        return _speaker(doc, turn), "", f"[[{row['text']}]]"
    lo, hi = MN.turn_bounds(doc, turn)
    t = doc.text[lo:hi]
    marked = t[:s - lo] + "[[" + t[s - lo:e - lo] + "]]" + t[e - lo:]
    a = s - lo
    marked = _flat(_cut(marked, a, a + (e - s) + 4, TURN_CHARS))
    prev = ""
    if turn > 0:
        plo, phi = MN.turn_bounds(doc, turn - 1)
        prev = f"{_speaker(doc, turn - 1)}: " + _flat(doc.text[plo:phi])[:PREV_CHARS]
    return _speaker(doc, turn), prev, marked


# ------------------------------------------------------------------ hints
def right_word(doc, turn, end):
    """Nearest word right of `end` inside the turn, as `mentions.left_word` ("" if none)."""
    _, hi = MN.turn_bounds(doc, turn)
    for tok in doc.text[end:hi].split():
        w = MN._PUNCT.sub("", tok).lower()
        if w:
            return w
    return ""


def _top_words(words):
    return {w for w, _ in Counter(w for w in words if w).most_common(SG.TOP_LEFT)}


def _percentile(pairs, v):
    """Share (0-100) of the entity's cluster-pair cosines that are <= v; nan without pairs."""
    return float(100.0 * (pairs <= v + 1e-12).mean()) if len(pairs) else float("nan")


def _majority_type(texts):
    return Counter(S2.value_type(t) for t in texts).most_common(1)[0][0]


def _entity_share(g, inst_x):
    """Share of the mentions in, or one turn next to, an instance (inst_x: dialogue -> [(start, end)])."""
    hit = sum(any(a - 1 <= t <= b + 1 for a, b in inst_x.get(d, ())) for d, t in zip(g["dialogue_id"], g["turn"]))
    return hit / len(g)


def _cardinality(g):
    return float(g.groupby("instance_id")["norm_value"].nunique().mean())


def _shared_values(g, vals_x):
    """Share of the cluster's distinct values also found, in the same dialogue, in the other entity
    (vals_x: dialogue -> set of norm values)."""
    mine = {(v, d) for v, d in zip(g["norm_value"], g["dialogue_id"])}
    shared = {v for v, d in mine if v in vals_x.get(d, ())}
    return len(shared) / g["norm_value"].nunique()


def _npmi_mean(graph, c, others):
    """Mean positive NPMI between c and each of `others` in `graph` (no edge counts 0)."""
    if not others:
        return float("nan")
    return float(np.mean([max(graph[c][o]["npmi"], 0.0) if graph.has_edge(c, o) else 0.0 for o in others]))


def option_texts(entity, others):
    """Placement options in fixed order: (text, description)."""
    opts = [(f"current entity {entity}", f"the attribute belongs to {entity}"),
            (f"sub-entity of {entity}", f"a part of {entity} that has attributes of its own")]
    for o in others:
        opts.append((f"other entity {o}", f"the attribute belongs to {o}"))
    for o in others:
        opts.append((f"relationship({entity}, {o})", f"links {entity} and {o}"))
    opts.append((SEPARATE, "a table of its own (several values per entity instance)"))
    return opts


def _scaled_card(card):
    return float(np.clip((card - 1.0) / (CARD_SEP - 1.0) / 2.0, 0.0, 1.0))  # CARD_SEP -> 0.5


def build_input(export, docs, entity, k=K_EXAMPLES, seed=0, graphs=None, roles=None):
    """The pilot input of `entity` from a loaded export and docs ({doc_id: Doc}); `roles` as select_examples."""
    m = export.mentions
    m = m[m["cluster_id"] != ""]
    graphs = graphs or GR.build_graphs(export)
    cents = GR.centroids(export)
    mine = m[m["entity"] == entity]
    cids = sorted(mine["cluster_id"].unique(), key=lambda c: int(c.rsplit("#", 1)[1]))
    ents = sorted(set(m["entity"]) - {entity})
    low = low_conf_clusters(export.mentions, entity)
    cos = {(a, b): float(cents[a] @ cents[b]) for a, b in combinations(cids, 2)}
    pairs = np.array(list(cos.values()))

    def cosine(a, b):
        return cos[(a, b)] if (a, b) in cos else cos[(b, a)]

    by_cluster = {c: g for c, g in m.groupby("cluster_id")}
    by_entity = {e: sorted(m[m["entity"] == e]["cluster_id"].unique(), key=lambda c: int(c.rsplit("#", 1)[1]))
                 for e in [entity] + ents}
    inst = {}
    for r in export.instances.itertuples():
        inst.setdefault(r.entity, {}).setdefault(r.dialogue_id, []).append((r.start_turn, r.end_turn))
    vals = {}
    for e, d, v in zip(m["entity"], m["dialogue_id"], m["norm_value"]):
        vals.setdefault(e, {}).setdefault(d, set()).add(v)
    others = {}
    for e in ents:
        big = sorted(by_entity[e], key=lambda c: (-len(by_cluster[c]), c))[:TOP_OTHER]
        others[e] = [(c, str(export.clusters.set_index("cluster_id").at[c, "top_values"]).split("|")[:3])
                     for c in big]
    # words and types per cluster
    left, right, vtype, instset = {}, {}, {}, {}
    for c in cids:
        g = by_cluster[c]
        left[c] = _top_words(g["left_word"])
        right[c] = _top_words(right_word(docs[d], t, e) for d, t, e in zip(g["dialogue_id"], g["turn"], g["char_end"]))
        vtype[c] = _majority_type(g["text"])
        instset[c] = set(g["instance_id"])

    clusters = []
    for c in cids:
        g = by_cluster[c]
        ci = ClusterInput(c, len(g), g["norm_value"].nunique(), c in low,
                          [(f"{c}:{j}", mid) for j, mid in enumerate(select_examples(g, k, seed, roles))])
        near = sorted((o for o in cids if o != c), key=lambda o: (-cosine(c, o), o))[:N_MERGE]
        for o in near:
            ci.merge.append(dict(other=o, pct=_percentile(pairs, cosine(c, o)),
                                 exclusive=not (instset[c] & instset[o]),
                                 left=sorted(left[c] & left[o]), right=sorted(right[c] & right[o]),
                                 same_type=vtype[c] == vtype[o]))
        card = _cardinality(g)
        for text, _ in option_texts(entity, ents):
            sig, ref, rel = {}, None, text.startswith("relationship(")
            if text == f"current entity {entity}":
                ref = entity
            elif text.startswith("other entity "):
                ref = text.split()[-1]
            elif rel:
                ref = text.rstrip(")").split(", ")[-1]
            elif text == SEPARATE:
                sig["cardinality"] = _scaled_card(card)
            if ref is not None:
                rest = [o for o in by_entity[ref] if o != c]
                if not rel:
                    sig["entity share"] = _entity_share(g, inst.get(ref, {}))
                sig["co-occurrence"] = _npmi_mean(graphs.co[entity] if ref == entity else graphs.cross, c, rest)
                if rest:
                    sig["similarity"] = max(_percentile(pairs, float(cents[c] @ cents[o])) for o in rest) / 100
                if rel:
                    sig["shared values"] = _shared_values(g, vals.get(ref, {}))
            sig = {n: v for n, v in sig.items() if not np.isnan(v)}
            score = float(np.mean(list(sig.values()))) if sig else float("nan")
            ci.placement.append(dict(option=text, score=score, signals=sig, raw_card=card if text == SEPARATE else None))
        ci.placement.sort(key=lambda p: (np.isnan(p["score"]), -p["score"] if not np.isnan(p["score"]) else 0))
        clusters.append(ci)
    return PilotInput(entity, clusters, option_texts(entity, ents), others)


# ------------------------------------------------------------------ rendering
def _fmt(x):
    return f"{x:.2f}"


def _render_options(inp):
    lines = ["Placement options (copy one exactly into \"placement\"):"]
    lines += [f"- {t}: {d}" for t, d in inp.options]
    lines.append("Other entities (id, top values of their 3 biggest clusters):")
    for e, big in inp.others.items():
        lines.append(f"- {e}: " + "; ".join(f"{', '.join(vs)}" for _, vs in big))
    return "\n".join(lines)


def _render_hints(ci, entity, context=True):
    """`context` False (nocontext variant): no shared left / right words, which are context cues."""
    out = ["Merge suggestions (suggestion, no decision), nearest clusters first:"]
    for h in ci.merge:
        words = (f"shared left words: {', '.join(h['left']) or '-'}; "
                 f"shared right words: {', '.join(h['right']) or '-'}; ") if context else ""
        out.append(f"- {h['other']}: cosine percentile {h['pct']:.0f}; "
                   f"never in the same instance: {'yes' if h['exclusive'] else 'no'}; "
                   f"{words}same value type: {'yes' if h['same_type'] else 'no'}")
    out.append("Placement suggestions (suggestion, no decision), ranked:")
    for i, p in enumerate(ci.placement, 1):
        if not p["signals"]:
            out.append(f"{i}. {p['option']}: no signal")
            continue
        det = ", ".join(f"{n} {_fmt(v)}" for n, v in p["signals"].items())
        if p["raw_card"] is not None:
            det += f" (mean distinct values per instance {_fmt(p['raw_card'])}; above {CARD_SEP} favours a separate table)"
        out.append(f"{i}. {p['option']}: {_fmt(p['score'])} ({det})")
    return "\n".join(out)


def _cluster_head(ci):
    return (f"### {ci.cluster_id}  (mentions {ci.n_mentions}, distinct values {ci.n_values}"
            f"{', low confidence' if ci.low_conf else ''})")


def _example_lines(export, docs, ci, context):
    rows = export.mentions.set_index("mention_id")
    lines = []
    for ex_id, mid in ci.examples:
        r = rows.loc[mid]
        spk, prev, turn = example_text(docs[r["dialogue_id"]], r, context)
        if context:
            lines.append(f"- {ex_id} [{spk}]" + (f" previous turn, {prev} | " if prev else " ") + f"turn: {turn}")
        else:
            lines.append(f"- {ex_id}: {turn}")
    return lines


def _cluster_block(export, docs, ci, context=True):
    """Head line, "Examples:" and the example lines of one cluster."""
    return [_cluster_head(ci), "Examples:", *_example_lines(export, docs, ci, context)]


def render(inp, export, docs, variant="full"):
    """The prompt text of one variant."""
    if variant not in VARIANTS:
        raise ValueError(variant)
    parts = [INSTRUCTION, f"Entity {inp.entity}: {len(inp.clusters)} clusters.", _render_options(inp)]
    for ci in inp.clusters:
        lines = [_cluster_head(ci), "Examples:", *_example_lines(export, docs, ci, variant != "nocontext")]
        if variant != "nohints":
            lines.append(_render_hints(ci, inp.entity, variant != "nocontext"))
        parts.append("\n".join(lines))
    parts.append("Return the JSON array now.")
    return "\n\n".join(parts) + "\n"


def examples_table(inp):
    import pandas as pd
    return pd.DataFrame([(ex, ci.cluster_id, mid) for ci in inp.clusters for ex, mid in ci.examples],
                        columns=["ex_id", "cluster_id", "mention_id"])


def est_tokens(text):
    return int(len(text) / 3.5)


# ------------------------------------------------------------------ wf_v3.1: format v2, split pass, schemas
def render_v2(inp, export, docs, variant="v2", hints=None, order_seed=None):
    """Prompt text of output format v2. `variant` v2 / v2_hints / v2_nocontext; `hints` {cluster_id: [dict(other, ..)]}
    is shown only for v2_hints; `order_seed` shuffles the cluster order (default: id order)."""
    if variant not in VARIANTS_V2:
        raise ValueError(variant)
    cl = list(inp.clusters)
    if order_seed is not None:
        cl = [cl[i] for i in np.random.default_rng(order_seed).permutation(len(cl))]
    parts = [INSTRUCTION_V2, f"Entity {inp.entity}: {len(cl)} clusters.", _render_options(inp)]
    for ci in cl:
        lines = _cluster_block(export, docs, ci, variant != "v2_nocontext")
        h = (hints or {}).get(ci.cluster_id) if variant == "v2_hints" else None
        if h:
            lines.append("Possibly the same attribute as: " + ", ".join(x["other"] for x in h)
                         + " (automatic suggestion, may be wrong)")
        parts.append("\n".join(lines))
    parts.append("Return the JSON object now.")
    return "\n\n".join(parts) + "\n"


def split_candidates(export, entity, min_mentions=8, min_share=0.15):
    """Cluster ids of `entity` with >= min_mentions mentions where >= min_share of the cluster's instances
    hold 2+ distinct norm values of the cluster; in cluster-number order."""
    m = export.mentions
    m = m[(m["entity"] == entity) & (m["cluster_id"] != "")]
    out = []
    for c, g in m.groupby("cluster_id"):
        if len(g) >= min_mentions and (g.groupby("instance_id")["norm_value"].nunique() >= 2).mean() >= min_share:
            out.append(c)
    return sorted(out, key=lambda c: int(c.rsplit("#", 1)[1]))


def cluster_example_lines(export, docs, entity, cluster_id, k, seed, tag):
    """(ClusterInput, example lines) of one cluster with k examples; ex ids `<cid>:<tag><j>`."""
    m = export.mentions
    g = m[(m["entity"] == entity) & (m["cluster_id"] == cluster_id)]
    if g.empty:
        raise ValueError(f"{cluster_id} is not a cluster of {entity}")
    exs = [(f"{cluster_id}:{tag}{j}", mid) for j, mid in enumerate(select_examples(g, k, seed))]
    ci = ClusterInput(cluster_id, len(g), g["norm_value"].nunique(), False, exs)
    return ci, _example_lines(export, docs, ci, True)


def render_split(export, docs, entity, cluster_id, k=16, seed=0):
    """(prompt text, [(ex_id, mention_id)]) of the split pass for one cluster; ex ids `<cid>:s<j>`."""
    ci, ex_lines = cluster_example_lines(export, docs, entity, cluster_id, k, seed, "s")
    lines = [f"Cluster {cluster_id} of entity {entity} (mentions {ci.n_mentions}, distinct values {ci.n_values}).",
             "Examples:", *ex_lines]
    return "\n\n".join([INSTRUCTION_SPLIT, "\n".join(lines), "Return the JSON object now."]) + "\n", ci.examples


def schema_v1(inp):
    """JSON schema of format v1 (wf_v3 array) with enums for cluster_id, merge_with and placement."""
    import copy
    ids = [c.cluster_id for c in inp.clusters]
    item = copy.deepcopy(LC._ITEM_SCHEMA)
    item["properties"]["cluster_id"] = {"enum": ids}
    item["properties"]["merge_with"] = {"type": "array", "items": {"enum": ids}}
    item["properties"]["placement"] = {"enum": [t for t, _ in inp.options]}
    return {"type": "array", "items": item}


def _schema_attr_clusters(ids, options, reason=False):
    """JSON schema {attributes[], clusters[]}; `reason` adds the required string `reason` after cluster_id."""
    attr = {"type": "object",
            "properties": {k: {"type": "string"} for k in ("name", "description", "role")},
            "required": ["name", "description", "role"]}
    props = {"cluster_id": {"enum": ids}}
    if reason:
        props["reason"] = {"type": "string"}
    props.update({"attribute": {"type": "string"}, "evidence": {"type": "string"}, "mixed": {"type": "boolean"},
                  "placement": {"enum": options}})
    clu = {"type": "object", "properties": props, "required": list(props)}
    return {"type": "object",
            "properties": {"attributes": {"type": "array", "items": attr},
                           "clusters": {"type": "array", "items": clu}},
            "required": ["attributes", "clusters"]}


def schema_v2(inp):
    """JSON schema of format v2: attributes[] and clusters[] (one per cluster id)."""
    return _schema_attr_clusters([c.cluster_id for c in inp.clusters], [t for t, _ in inp.options])


def schema_split(cluster_id, ex_ids):
    """JSON schema of the split-pass answer."""
    part = {"type": "object",
            "properties": {"name": {"type": "string"}, "role": {"type": "string"},
                           "examples": {"type": "array", "items": {"enum": list(ex_ids)}}},
            "required": ["name", "role", "examples"]}
    return {"type": "object",
            "properties": {"cluster_id": {"enum": [cluster_id]}, "is_mixed": {"type": "boolean"},
                           "parts": {"type": "array", "items": part}},
            "required": ["cluster_id", "is_mixed", "parts"]}


# ------------------------------------------------------------------ wf_v3.2: neighbourhoods, format v3, probes
N_OUTSIDE = 3         # clusters of other groups shown as "elsewhere"
NBHD_MAX = 20
NOISE_K = 6
GATE_K = 16
REASON_LINE = ('Each cluster object starts with "reason": at most 25 words on why the cluster belongs to that '
               'attribute, written before "attribute".')
INSTRUCTION_V3 = INSTRUCTION_V2 + "\n" + REASON_LINE

INSTRUCTION_NOISE = """\
Below are examples of ONE cluster of spans taken from a dialogue corpus. Decide: is this a value that a database
column would store (a real attribute value, such as a place, a time, a name or a number of people)? Or is it noise
(chit-chat, yes/no/ok, booking words, filler)?
Examples are marked with [[...]] inside the turn they come from.
Give a short reason, then a verdict: "attribute", "noise" or "unsure". If the verdict is attribute, give its
database column name in snake_case; otherwise give an empty name. If unsure, answer unsure.
Return ONLY one JSON object, nothing before or after it:
{"cluster_id": "C#0", "reason": "str", "verdict": "attribute|noise|unsure", "name": "snake_case or empty"}"""

INSTRUCTION_GATE = """\
Below are examples of ONE cluster of spans taken from a dialogue corpus. Decide whether the cluster is coherent:
all its values are ONE attribute with one role.
Examples are marked with [[...]] inside the turn they come from.
Step 1: summarise in one line what the values are.
Step 2: does that summary fit all the examples as ONE attribute with one role? If different examples play
different roles (for example where something starts vs where it ends), the answer is no.
If unsure, answer coherent true.
Return ONLY one JSON object, nothing before or after it:
{"cluster_id": "C#0", "summary": "str", "coherent": true}"""

INSTRUCTION_RECONCILE = """\
Below is ONE attribute (a candidate database column) with example values from a dialogue corpus, and a list of
candidate attributes of the same table. Decide whether it is the SAME attribute as one candidate: the same kind
of value playing the same role. Values that play different roles (where something starts vs where it ends,
the earliest vs the latest time) are different attributes.
Examples are marked with [[...]] inside the turn they come from.
Give a short reason, then "same_as": the name of that candidate, or "none" if it is its own attribute.
If unsure, answer none.
Return ONLY one JSON object, nothing before or after it:
{"unit_id": "a0", "reason": "str", "same_as": "<candidate name or none>"}"""


CUE_LINE = ('Use "attribute_cue" for clusters whose examples are questions or requests about an attribute rather '
            'than its values (what day, how many tickets, which area); it means an attribute exists but this '
            'cluster is not a column.')
NOISE_RULE = ("If fewer than half of a cluster's examples are real values that a database would store, choose "
              '"not_attribute" (or "attribute_cue" for questions).')
CARRY_PLACEHOLDER = "{{CARRY_OVER}}"
_NOISE_SENT = ('Use "not_attribute" for noise. Noise is common: yes, ok, thanks, booking words,\n'
               '   and values that a database would not store.')
_EX_TAIL = '"mixed": false, "placement": "current entity E9"}]}'
assert _NOISE_SENT in INSTRUCTION_V3 and INSTRUCTION_V3.count(_EX_TAIL) == 1
INSTRUCTION_V33 = (INSTRUCTION_V3
                   .replace(_NOISE_SENT, 'Use "not_attribute" for noise. ' + CUE_LINE + '\n   Noise is common: yes, ok, '
                            'thanks, booking words,\n   and values that a database would not store. ' + NOISE_RULE)
                   .replace(_EX_TAIL, '"mixed": false, "placement": "current entity E9"},\n'
                            '              {"cluster_id": "E9#2", "attribute": "attribute_cue", '
                            '"evidence": "[[what day]] do you want?",\n'
                            '               "mixed": false, "placement": "current entity E9"}]}'))


def _cluster_number(cid):
    return int(cid.rsplit("#", 1)[1])


def neighbourhoods(export, entity, max_size=NBHD_MAX):
    """Groups of the entity's cluster ids: ceil(n / max_size) groups by average-linkage agglomerative clustering
    on the cosine of the cluster centroids, then rebalanced so no group has more than max_size clusters (the
    member farthest from its group centroid moves to the nearest group with room). Deterministic; each cluster
    in exactly one group; clusters in cluster-number order, groups ordered by their first cluster."""
    from scipy.cluster.hierarchy import cut_tree, linkage
    m = export.mentions
    cids = sorted(m[(m["entity"] == entity) & (m["cluster_id"] != "")]["cluster_id"].unique(), key=_cluster_number)
    g = -(-len(cids) // max_size)
    if g <= 1:
        return [cids] if cids else []
    cents = GR.centroids(export)
    x = np.array([cents[c] for c in cids], dtype=np.float64)
    label = cut_tree(linkage(x, method="average", metric="cosine"), n_clusters=g).ravel()
    groups = [[i for i in range(len(cids)) if label[i] == k] for k in range(g)]

    def centre(members):
        v = x[members].mean(axis=0)
        return v / np.linalg.norm(v)

    while max(len(a) for a in groups) > max_size:
        src = max(range(g), key=lambda k: (len(groups[k]), -k))
        cs = centre(groups[src])
        mover = min(groups[src], key=lambda i: (float(x[i] @ cs), i))  # least similar to its own group
        room = [k for k in range(g) if k != src and len(groups[k]) < max_size]
        dst = max(room, key=lambda k: (float(x[mover] @ centre(groups[k])), -k))
        groups[src].remove(mover)
        groups[dst].append(mover)
    groups = sorted((sorted(a) for a in groups if a), key=lambda a: a[0])
    return [[cids[i] for i in a] for a in groups]


def outside_context(export, groups, gi, n=N_OUTSIDE):
    """[(cluster_id, top values)] of the n clusters of other groups nearest (cosine) to the centroid of
    groups[gi]."""
    cents = GR.centroids(export)
    c = np.mean([cents[x] for x in groups[gi]], axis=0)
    c = c / np.linalg.norm(c)
    others = [x for k, g in enumerate(groups) if k != gi for x in g]
    near = sorted(others, key=lambda o: (-float(cents[o] @ c), o))[:n]
    tv = export.clusters.set_index("cluster_id")["top_values"]
    return [(o, str(tv[o]).split("|")[:3]) for o in near]


def nbhd_target(n_group):
    """T of "Aim for about T attributes": a third of the group's clusters, at least 1."""
    return max(1, round(n_group / 3))


def render_v3(inp, export, docs, group_ids, outside, target, order_seed=None, carry=None, cue_rule=False):
    """Prompt text of output format v3 for one neighbourhood: only the clusters `group_ids` (in that order, or
    shuffled with `order_seed`), the `outside` lines [(cluster_id, values)] and the attribute-count target.
    wf_v3.3: `cue_rule` True uses INSTRUCTION_V33; `carry` (a text block, or CARRY_PLACEHOLDER) goes after the
    outside block and before the clusters. The defaults give the v3.2 prompt."""
    by_id = {c.cluster_id: c for c in inp.clusters}
    cl = [by_id[c] for c in group_ids]
    if order_seed is not None:
        cl = [cl[i] for i in np.random.default_rng(order_seed).permutation(len(cl))]
    parts = [INSTRUCTION_V33 if cue_rule else INSTRUCTION_V3, f"Entity {inp.entity}: {len(cl)} clusters.",
             f"Aim for about {target} attributes (between {target / 2:g} and {target * 3 / 2:g}).",
             _render_options(inp)]
    if outside:
        parts.append("\n".join(f"Elsewhere in this entity (not yours to assign): {c}: {', '.join(vs)}"
                               for c, vs in outside))
    if carry is not None:
        parts.append(carry)
    parts += ["\n".join(_cluster_block(export, docs, ci)) for ci in cl]
    parts.append("Return the JSON object now.")
    return "\n\n".join(parts) + "\n"


def schema_v3(inp, group_ids):
    """JSON schema of format v3: v2 with cluster_id an enum of `group_ids` and a required `reason` after it."""
    return _schema_attr_clusters(list(group_ids), [t for t, _ in inp.options], reason=True)


def _render_probe(instruction, export, docs, entity, cluster_id, k, seed, tag):
    ci, ex_lines = cluster_example_lines(export, docs, entity, cluster_id, k, seed, tag)
    block = "\n".join([_cluster_head(ci), "Examples:", *ex_lines])
    return "\n\n".join([instruction, block, "Return the JSON object now."]) + "\n", ci.examples


def render_noise(export, docs, entity, cluster_id, k=NOISE_K, seed=0):
    """(prompt text, [(ex_id, mention_id)]) of the noise probe of one cluster; ex ids `<cid>:n<j>`."""
    return _render_probe(INSTRUCTION_NOISE, export, docs, entity, cluster_id, k, seed, "n")


def render_gate(export, docs, entity, cluster_id, k=GATE_K, seed=0):
    """(prompt text, [(ex_id, mention_id)]) of the coherence gate of one cluster; ex ids `<cid>:g<j>`."""
    return _render_probe(INSTRUCTION_GATE, export, docs, entity, cluster_id, k, seed, "g")


def schema_noise(cluster_id):
    """JSON schema of the noise-probe answer."""
    return {"type": "object",
            "properties": {"cluster_id": {"enum": [cluster_id]}, "reason": {"type": "string"},
                           "verdict": {"enum": ["attribute", "noise", "unsure"]}, "name": {"type": "string"}},
            "required": ["cluster_id", "reason", "verdict", "name"]}


def schema_gate(cluster_id):
    """JSON schema of the coherence-gate answer."""
    return {"type": "object",
            "properties": {"cluster_id": {"enum": [cluster_id]}, "summary": {"type": "string"},
                           "coherent": {"type": "boolean"}},
            "required": ["cluster_id", "summary", "coherent"]}


def render_reconcile(unit, candidates):
    """Prompt text of the reconcile pass from plain data (no export): `unit` {unit_id, name, description,
    lines [example lines]}, `candidates` [(name, description)]."""
    head = (f"Attribute {unit['unit_id']}: {unit['name']}: {unit['description']}\n"
            + "Examples:\n" + "\n".join(unit["lines"]))
    cand = "Candidates:\n" + "\n".join(f"- {n}: {d}" for n, d in candidates)
    return "\n\n".join([INSTRUCTION_RECONCILE, head, cand, "Return the JSON object now."]) + "\n"


def schema_reconcile(unit_id, candidate_names):
    """JSON schema of the reconcile answer; same_as is a candidate name or "none"."""
    return {"type": "object",
            "properties": {"unit_id": {"enum": [unit_id]}, "reason": {"type": "string"},
                           "same_as": {"enum": list(candidate_names) + ["none"]}},
            "required": ["unit_id", "reason", "same_as"]}
