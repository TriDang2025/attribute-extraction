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
from . import mentions as MN
from . import signals as SG
from . import step2 as S2

VARIANTS = ("full", "nocontext", "nohints")
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
def select_examples(g, k=K_EXAMPLES, seed=0):
    """Mention ids of one cluster's mentions `g` (rows of mentions.csv): round-robin over the distinct
    values (most frequent first), within a value a mention from a dialogue not yet used when possible.
    Fewer than k when the cluster is smaller; never k copies of one value when more values exist."""
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


def build_input(export, docs, entity, k=K_EXAMPLES, seed=0, graphs=None):
    """The pilot input of `entity` from a loaded export and docs ({doc_id: Doc})."""
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
                          [(f"{c}:{j}", mid) for j, mid in enumerate(select_examples(g, k, seed))])
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


def render(inp, export, docs, variant="full"):
    """The prompt text of one variant."""
    if variant not in VARIANTS:
        raise ValueError(variant)
    rows = export.mentions.set_index("mention_id")
    parts = [INSTRUCTION, f"Entity {inp.entity}: {len(inp.clusters)} clusters.", _render_options(inp)]
    for ci in inp.clusters:
        head = (f"### {ci.cluster_id}  (mentions {ci.n_mentions}, distinct values {ci.n_values}"
                f"{', low confidence' if ci.low_conf else ''})")
        lines = [head, "Examples:"]
        for ex_id, mid in ci.examples:
            r = rows.loc[mid]
            spk, prev, turn = example_text(docs[r["dialogue_id"]], r, variant != "nocontext")
            if variant == "nocontext":
                lines.append(f"- {ex_id}: {turn}")
            else:
                lines.append(f"- {ex_id} [{spk}]" + (f" previous turn, {prev} | " if prev else " ") + f"turn: {turn}")
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
