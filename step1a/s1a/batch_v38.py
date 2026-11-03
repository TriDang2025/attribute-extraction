"""wf_v3.8 Colab batch (contract WF_V38_BATCH.md): pure functions, no I/O, no models.

- column_table: the columns of one variant (A s012, with or without the split pass) of one entity, with description, members,
  counts and the per-member mention pools that the sampler reads.
- sample_examples: up to k examples of a column, round-robin over its members (largest first), seeded.
- centroids / nearest: bge-m3 centroid of each column and its nearest other columns by cosine.
- render_dupcheck / render_evidence and their schemas: the prompts of task 7 (duplicate check) and tasks 8-9 (examples).
- check_joins: the code check applied when scoring a duplicate check (role pairs by the method's own names only).
"""

import zlib
from collections import Counter

import numpy as np

from . import role_guard as RGD
from .value_types import value_type_v35

N_EXAMPLES = 10        # task 8: examples of a column
N_NEIGHBOURS = 2       # task 9: nearest other columns
N_PER_NEIGHBOUR = 5    # task 9: examples taken from each neighbour
N_VALUES = 3           # task 7: example values shown per column
NAME_PAIRS = RGD.PAIRS[:2]   # start vs end place, earliest vs latest time; never location vs address
MAX_TOKENS = {"dupcheck": 1024, "example": 512, "neighbour": 512}


# ---- columns

def _top_values(values, n=N_VALUES):
    return [v for v, _ in sorted(Counter(values).items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def column_description(groups, desc_of, size_of):
    """Description of a column: that of its biggest group (by mentions) that has one; "" when none has."""
    for g in sorted(groups, key=lambda g: (-size_of.get(g, 0), g)):
        if desc_of.get(g, ""):
            return desc_of[g]
    return ""


def column_table(attrs, assign, mentions, gc):
    """List of column dicts (sorted by name, cid 1..n) of one entity and variant.
    attrs: variant attrs (attr_id, description); assign {mention_id: attr_id}; mentions: DataFrame with mention_id, cluster_id,
    dialogue_id, norm_value, text; gc: columns_v37.group_columns frame (attr_id, column). A column is a distinct name; its
    groups are the attr_ids with that name, its members the distinct (cluster_id, attr_id) pairs of its mentions (a split part
    is one member, a merged group has one member per cluster), its mentions those of its groups. Keys: cid, name, description,
    groups, members, mention_ids, n_mentions, n_dialogues, n_values, value_types ("type:n|..."), top_values, pools
    ([(member key, [(mention_id, dialogue_id, norm_value)])], largest member first)."""
    col_of = dict(zip(gc["attr_id"], gc["column"]))
    desc_of = {r["attr_id"]: (r["description"] or "") for _, r in attrs.iterrows()}
    size_of = Counter(assign.values())
    by_col = {c: {} for c in sorted(set(col_of.values()))}
    for r in mentions.itertuples(index=False):
        g = assign.get(int(r.mention_id))
        c = col_of.get(g)
        if c is not None:
            by_col[c].setdefault((r.cluster_id, g), []).append((int(r.mention_id), r.dialogue_id, r.norm_value, r.text))
    out = []
    for i, (name, members) in enumerate(by_col.items(), 1):
        groups = sorted(g for g, c in col_of.items() if c == name)
        rows = [x for ms in members.values() for x in ms]
        pools = sorted(((f"{c}@{g}", [x[:3] for x in ms]) for (c, g), ms in members.items()), key=lambda p: (-len(p[1]), p[0]))
        types = Counter(value_type_v35(x[3]) for x in rows)
        out.append({"cid": i, "name": name, "description": column_description(groups, desc_of, size_of), "groups": groups,
                    "members": sorted(members), "mention_ids": [x[0] for x in rows], "n_mentions": len(rows),
                    "n_dialogues": len({x[1] for x in rows}), "n_values": len({x[2] for x in rows}),
                    "value_types": "|".join(f"{t}:{n}" for t, n in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))),
                    "top_values": _top_values([x[2] for x in rows]), "pools": pools})
    return out


# ---- examples

def sample_examples(pools, k, seed, salt):
    """[(mention_id, member key)]: up to k mentions, one member per turn of a round-robin over `pools` ([(key, [(mention_id,
    dialogue_id, norm_value)])], largest first). Inside a member the pick is random (rng seeded by `seed` and `salt`) among
    mentions of a dialogue not used yet and a value not shown yet, else a dialogue not used yet, else any."""
    rng = np.random.default_rng([seed, zlib.crc32(str(salt).encode())])
    left = [(key, [items[i] for i in rng.permutation(len(items))]) for key, items in pools]
    picked, dialogues, values = [], set(), set()
    while len(picked) < k and any(items for _, items in left):
        for key, items in left:
            if len(picked) >= k:
                break
            if not items:
                continue
            j = next((j for j, x in enumerate(items) if x[1] not in dialogues and x[2] not in values), None)
            if j is None:
                j = next((j for j, x in enumerate(items) if x[1] not in dialogues), 0)
            mid, did, val = items.pop(j)
            dialogues.add(did)
            values.add(val)
            picked.append((mid, key))
    return picked


def neighbour_examples(cols, cid, neighbours, per, seed):
    """[(mention_id, source cid)] for task 9: `per` examples from each neighbour column (sampled as sample_examples, seeded by
    the neighbour's own cid), then shuffled with a seed of the target column so no source is contiguous."""
    items = [(mid, n) for n in neighbours for mid, _ in sample_examples(cols[n]["pools"], per, seed, f"col{n}")]
    order = np.random.default_rng([seed, 1, cid]).permutation(len(items))
    return [items[i] for i in order]


# ---- neighbours

def centroids(columns, ids, x):
    """{cid: unit vector}: mean of the mention vectors of the column (`ids` = mention ids of the rows of `x`), normalised."""
    pos = {int(m): i for i, m in enumerate(ids)}
    out = {}
    for c in columns:
        if not c["mention_ids"]:
            continue
        v = x[[pos[m] for m in c["mention_ids"]]].mean(axis=0)
        out[c["cid"]] = v / np.linalg.norm(v)
    return out


def nearest(cent, cid, k=N_NEIGHBOURS):
    """The k other cids with the highest cosine to column `cid` (ties by lower cid); fewer when the entity has fewer columns."""
    sims = sorted(((float(cent[cid] @ v), o) for o, v in cent.items() if o != cid), key=lambda t: (-t[0], t[1]))
    return [o for _, o in sims[:k]]


# ---- prompts

DUP_INSTRUCTION = """\
Below is a list of columns proposed for one table. Each column has an id, a name, a description and example values.
Some columns are the same attribute listed twice (the same kind of value, with the same role, under two names or in two parts).
Find them: list every group of two or more columns that are the same attribute with the same role. Do not join columns that
are different attributes, and do not join columns whose values play different roles (for example where something starts
and where it ends). Leave a column out when it has no twin."""


def render_dupcheck(cols, roles=None):
    """Prompt of one duplicate check. cols: column dicts (cid, name, description, top_values); roles {cid: role}. An empty
    description or role is not shown; a column with no mentions shows examples "(none)"."""
    roles = roles or {}
    lines = []
    for c in cols:
        parts = [f"{c['cid']}. name: {c['name']}"]
        if c["description"]:
            parts.append(f"description: {c['description']}")
        if roles.get(c["cid"]):
            parts.append(f"role: {roles[c['cid']]}")
        parts.append("examples: " + ("; ".join(c["top_values"]) or "(none)"))
        lines.append(" | ".join(parts))
    return "\n\n".join([DUP_INSTRUCTION, f"Columns ({len(cols)}):\n" + "\n".join(lines),
                        'Return ONLY one JSON object, nothing before or after it, in this shape (other ids): '
                        '{"joins": [{"columns": [3, 7], "reason": "same value, same role"}]}. Use [] when nothing is joined.']) + "\n"


def schema_dupcheck(ids):
    return {"type": "object",
            "properties": {"joins": {"type": "array", "items": {"type": "object", "properties": {
                "columns": {"type": "array", "items": {"enum": list(ids)}}, "reason": {"type": "string"}},
                "required": ["columns", "reason"]}}},
            "required": ["joins"]}


def attribute_label(name, description):
    return f"{name} ({description})" if description else name


EVIDENCE_INSTRUCTION = """\
Below are examples taken from conversations. In each example one value is marked with [[ ]].
For each example, answer whether the marked value fits the attribute named at the end of this text.
Answer "yes" or "no" for every example."""


def render_evidence(name, description, lines):
    """Prompt of one example / neighbour check. lines: the example lines ("- <id> [speaker] ... turn: ... [[value]] ...")."""
    label = attribute_label(name, description)
    return "\n\n".join([EVIDENCE_INSTRUCTION, "Examples:\n" + "\n".join(lines),
                        f"Question for each example: Does the marked value fit the attribute {label}?",
                        'Return ONLY one JSON object, nothing before or after it, one answer per example: '
                        '{"answers": [{"id": 1, "fits": "yes"}, {"id": 2, "fits": "no"}]}']) + "\n"


def schema_evidence(ids):
    return {"type": "object",
            "properties": {"answers": {"type": "array", "items": {"type": "object", "properties": {
                "id": {"enum": list(ids)}, "fits": {"enum": ["yes", "no"]}}, "required": ["id", "fits"]}}},
            "required": ["answers"]}


def est_output_tokens(family, n):
    """Estimated output tokens: evidence answers are about 12 tokens each plus 8; a duplicate check has no earlier answer to
    measure, so it is a flat guess."""
    return 200 if family == "dupcheck" else 8 + 12 * n


# ---- join code check

def join_names(cols_by_id, join, roles=None):
    """{cid: "name role"} texts of a join's columns, as role_guard reads them."""
    roles = roles or {}
    return {c: f"{cols_by_id[c]['name']} {roles.get(c, '')}" for c in join["columns"]}


def check_joins(joins, cols_by_id, roles=None):
    """(kept, rejected): a join is rejected when two of its columns form a role pair using only the columns' own names (and
    roles) and the word sets NAME_PAIRS. Never reads the GT. Each join is returned as given."""
    kept, rejected = [], []
    for j in joins:
        t = join_names(cols_by_id, j, roles)
        ids = list(t)
        bad = any(RGD.forbidden_merge(t[a], t[b], NAME_PAIRS) for i, a in enumerate(ids) for b in ids[i + 1:])
        (rejected if bad else kept).append(j)
    return kept, rejected
