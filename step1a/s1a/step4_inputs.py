"""wf_v4 Step 4 inputs (diary 5 Nov, task 2): the seven inputs of the schema-creation prompts, for dev50 and dev50b.

Column dicts are those of step4_prompts (id "<entity>:<id>", name, description, role, value_type, examples, counts, signal, flag); here
`examples` is a list of [value, short context] pairs, `data_signal` (input b only) is the task-1 card, `entity` and `gt` are set in c1 / c2.
  a  main: the handover columns with examples + context, counts and the checker evidence
  b  a + the task-1 data signals (cards.json)
  c1 every non-added GT column of the six place / booking tables (upper bound; ids "gt:<n>", examples from the gold mentions)
  c2 c1 limited to the columns the handover can reach (reachable_<set>.csv == yes)
  d  flat baseline (canonical schema: one table per entity with all its columns; no LLM)
  e  dialogues only (whole dialogues filled greedily up to the token budget; three orders)
  f  signals only (canonical schema from the task-1 signals by fixed rules; no LLM)
Pure functions take DataFrames / dicts; the `load_*` helpers read files. The GT is read only for c1 and c2 (scoring and the upper bound).

Choices (see also results/wf_v4/inputs/README of the run in the report):
- examples: the k most frequent distinct `norm_value` of the column's mentions (ties: alphabetical); each with the context of its first mention,
  cut to `width` characters around the value ("..." marks a cut and counts in the width).
- column order: seed 0 = input order (handover order = by name; GT inputs: by name within the entity); seeds 1, 2 shuffle inside each entity block.
- (f) thresholds: community edges = same-entity NPMI > 0 (Louvain, weight NPMI, seed 0); a column with n_instances >= 3 and share of
  instances with >= 2 values >= 0.5 gets its own table; the identifier of a table is its highest name_score column if that is >= 0.5,
  else a new id column; singleton communities join the entity's main table (the community with the entity's best name_score column when
  that score is >= 0.5, else the largest); cross-entity links: co-occurrence NPMI >= 0.2 and count >= 3, plus cross-entity FDs that hold
  (the dependent side refers); a pair without FD: the table with the higher max n_instances refers (ties by name).
"""
import json
import random
import re
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd

from . import step4_gt as G
from .baseline_prompt_v37 import order as dialogue_order
from .pilot_input import est_tokens
from .step4_prompts import build_prompt_41, build_prompt_e, canon_type, columns_from_handover, render_columns
from .step4_sql import _add_link, _canon_table, _column, _ensure_pk
from .value_types import value_type_v35

ROOT = Path(__file__).resolve().parents[1]
ENTITIES = G.ENTITIES
GT_TABLES = ("train", "train_booking", "hotel", "hotel_booking", "restaurant", "restaurant_booking")
GT_LEVELS = {"dev50": "results/loop1_v35/gt_levels.csv", "dev50b": "results/loop1_v37/dev50b/gt/gt_levels.csv"}
N_EXAMPLES, WIDTH = 5, 80
FIRST_LIMIT = 20000          # estimated tokens of a first prompt (4.1 or e)
E_BUDGET = FIRST_LIMIT
VERSIONS = ("v0", "v1", "v2")
# (f) thresholds
MULTI_SHARE, MULTI_MIN_N, NAME_MIN, LINK_NPMI, LINK_COUNT = 0.5, 3, 0.5, 0.2, 3


# ---------------------------------------------------------------- examples
def snippet(text, context, width=WIDTH):
    """`context` cut to `width` characters around `text` ("..." at a cut, counted in the width)."""
    n = len(context)
    if n <= width:
        return context
    i = context.lower().find(str(text).lower())
    mid = i + len(str(text)) // 2 if i >= 0 else width // 2
    start = max(0, min(mid - width // 2, n - width))
    end = start + width
    pre, post = ("..." if start > 0 else ""), ("..." if end < n else "")
    return pre + context[start + len(pre):end - len(post)] + post


def examples_of(rows, k=N_EXAMPLES, width=WIDTH):
    """[[norm_value, context snippet]] of the k most frequent distinct norm_values of `rows` (mention DataFrame: norm_value, text,
    context; sorted by mention_id); the snippet comes from the first mention of the value."""
    cnt = Counter(rows["norm_value"])
    out = []
    for v, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:k]:
        r = rows[rows["norm_value"] == v].iloc[0]
        out.append([v, snippet(r["text"], r["context"], width)])
    return out


def dominant_type(texts):
    """{dominant, share, counts} of value_type_v35 over the mention texts (the handover format)."""
    cnt = Counter(value_type_v35(t) for t in texts)
    if not cnt:
        return {"dominant": "", "share": 0.0, "counts": {}}
    top = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return {"dominant": top[0], "share": top[1] / sum(cnt.values()), "counts": dict(cnt)}


# ---------------------------------------------------------------- loading
def load_mentions(set_name, root=ROOT):
    """Mention table of the set indexed by mention_id (dialogue_id, text, norm_value, context)."""
    m = pd.read_csv(Path(root) / "results" / f"graph_v22_{set_name}" / "spans" / "mentions.csv",
                    usecols=["mention_id", "dialogue_id", "text", "norm_value", "context"], dtype=str, keep_default_na=False)
    m["mention_id"] = m["mention_id"].astype(int)
    return m.set_index("mention_id").sort_index()


def load_handover(set_name, root=ROOT):
    return {e: json.loads((Path(root) / "handover" / set_name / f"{e}.json").read_text(encoding="utf-8")) for e in ENTITIES}


def load_cards(set_name, root=ROOT):
    return json.loads((Path(root) / "results" / "wf_v4" / "signals" / set_name / "cards.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- inputs a, b
def main_columns(handover, mentions, k=N_EXAMPLES, width=WIDTH):
    """Input (a): the handover columns of the entities (dict entity -> parsed handover file), examples with context."""
    cols = []
    for ent in ENTITIES:
        data = handover[ent]
        for c, raw in zip(columns_from_handover(ent, data), data["columns"]):
            rows = mentions.loc[[i for i in raw["mention_ids"] if i in mentions.index]]
            cols.append({**c, "examples": examples_of(rows, k, width)})
    return cols


def with_signals(cols, cards):
    """Input (b): the columns of (a) plus `data_signal` = the task-1 card of each column."""
    return [{**c, "data_signal": cards[c["id"]]} for c in cols]


# ---------------------------------------------------------------- inputs c1, c2
def gt_columns(gt, levels, mentions, k=N_EXAMPLES, width=WIDTH, reachable=None):
    """Inputs (c1) / (c2): the non-added GT columns of the six tables of the main design, ids "gt:<n>" numbered in the listed order (entity, then name; not the GT table order); `levels` = Series
    mention_id -> gt_L2; examples and counts from the mentions whose gt_L2 (split on ";") holds the GT name; `reachable` = {GT column:
    "yes"|...}: keep only "yes" (c2). Every column has the `gt` field."""
    labels = {i: set(G.split_labels(v)) for i, v in levels.items()}
    cols = []
    for tn in GT_TABLES:
        t = gt["tables"][tn]
        for c in t["columns"]:
            if c["source"] == "added" or (reachable is not None and reachable.get(c["name"]) != "yes"):
                continue
            rows = mentions.loc[[i for i in mentions.index if c["name"] in labels.get(i, ())]]
            cols.append({"id": "", "entity": t["entity"], "name": c["name"], "description": c.get("description", ""), "role": "",
                         "value_type": dominant_type(rows["text"]), "examples": examples_of(rows, k, width),
                         "n_mentions": len(rows), "n_dialogues": rows["dialogue_id"].nunique(), "signal": "", "flag": "", "gt": c["name"]})
    cols.sort(key=lambda c: (ENTITIES.index(c["entity"]), c["name"].lower()))   # neutral order: by entity, then name (not by GT table)
    return [{**c, "id": f"gt:{n}"} for n, c in enumerate(cols, 1)]


def load_reachable_yes(set_name, root=ROOT):
    rows = G.load_reachable(Path(root) / "results" / "wf_v4" / "gt" / f"reachable_{set_name}.csv")
    return {r["gt_column"]: r["reachable"] for r in rows}


# ---------------------------------------------------------------- column order, token check
def order_columns(cols, seed):
    """Seed 0: input order; seed 1, 2, ...: shuffled inside each entity block (entity blocks keep their order)."""
    if not seed:
        return list(cols)
    rng = random.Random(seed)
    out = []
    for ent in dict.fromkeys(c.get("entity") or c["id"].split(":")[0] for c in cols):
        block = [c for c in cols if (c.get("entity") or c["id"].split(":")[0]) == ent]
        rng.shuffle(block)
        out += block
    return out


def first_prompt(cols):
    """(prompt, schema) of 4.1 for these columns in their order."""
    return build_prompt_41(render_columns(cols), cols)


# ---------------------------------------------------------------- input d: flat baseline
def flat_schema(cols):
    """Canonical schema (d): one table per entity holding all its columns; no keys, no relationships."""
    tables = []
    for ent in ENTITIES:
        mine = [c for c in cols if c["id"].split(":")[0] == ent]
        tables.append(_canon_table(ent, f"All columns found for {ent}.", f"one {ent}",
                                   [_column(c["name"], canon_type(c.get("value_type")), c["id"]) for c in mine], [], []))
    return {"tables": tables, "relationships": [], "unused": [], "duplicate_flags": []}


# ---------------------------------------------------------------- input e: dialogues only
def dialogue_text(texts):
    """Dialogue block of the (e) prompt: each dialogue under a numbered header."""
    return "".join(f"\n[dialogue {i}]\n{t}\n" for i, t in enumerate(texts, 1))


def fill_dialogues(texts, ids, version, budget=E_BUDGET):
    """(chosen ids in prompt order, prompt text). Greedy in the version's order (v0 set order, v1 / v2 shuffled, seeds 1 / 2): a whole
    dialogue is added when the estimated tokens of the whole prompt stay below `budget`, else skipped."""
    chosen = []
    for did in dialogue_order(ids, version):
        if est_tokens(build_prompt_e(dialogue_text([texts[i] for i in chosen + [did]]))[0]) < budget:
            chosen.append(did)
    return chosen, build_prompt_e(dialogue_text([texts[i] for i in chosen]))[0]


def load_docs(set_name, root=ROOT):
    """(ids in set order, {id: text}) from results/graph_v22_<set>/docs.jsonl."""
    ids, texts = [], {}
    for line in (Path(root) / "results" / f"graph_v22_{set_name}" / "docs.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            ids.append(r["dialogue_id"])
            texts[r["dialogue_id"]] = r["text"]
    return ids, texts


# ---------------------------------------------------------------- input f: signals only
def _snake(name):
    return re.sub(r"\W+", "_", str(name).lower()).strip("_") or "x"


def _num(key):
    ent, i = key.split(":")
    return ENTITIES.index(ent), int(i)


def _best(keys, rows):
    """Column with the highest name_score (ties: more mentions, then id)."""
    return sorted(keys, key=lambda k: (-rows.name_score[k], -rows.n_mentions[k], _num(k)))[0]


def signals_schema(df, pairs, fd, hand):
    """Canonical schema (f) from the task-1 signals (rules in the module doc). df, pairs, fd = columns.csv, pairs.csv, fd.csv as
    DataFrames; hand = {column id: {"name", "value_type"}} from the handover."""
    rows = df.set_index("column_id")
    c = {"tables": [], "relationships": [], "unused": [], "duplicate_flags": []}
    tabs, where, used = {}, {}, set()

    def new_table(name, ent, desc, cols, ident):
        base, n = name, 2
        while name in used:
            name, n = f"{base}_{n}", n + 1
        used.add(name)
        names = {}
        for k in cols:
            nm = hand[k]["name"]
            names[k] = nm if nm not in names.values() else f"{nm} {k.split(':')[1]}"
        t = _canon_table(name, desc, f"one {name.replace('_', ' ')}",
                         [_column(names[k], canon_type(hand[k].get("value_type")), k) for k in cols],
                         [names[ident]] if ident else [], [])
        c["tables"].append(t)
        tabs[name] = t
        for k in cols:
            where[k] = name
        if not ident:
            _ensure_pk(t)
        return name

    for ent in ENTITIES:
        ids = sorted(df[df["entity"] == ent]["column_id"], key=_num)
        child = [k for k in ids if rows.n_instances[k] >= MULTI_MIN_N and rows.share_multi_value[k] >= MULTI_SHARE]
        rest = [k for k in ids if k not in child]
        if not rest:
            continue
        g = nx.Graph()
        g.add_nodes_from(rest)
        for r in pairs[(pairs["scope"] == "same_entity") & (pairs["npmi"] > 0)].itertuples():
            if r.col_a in g and r.col_b in g:
                g.add_edge(r.col_a, r.col_b, w=float(r.npmi))
        comms = sorted((sorted(x, key=_num) for x in nx.community.louvain_communities(g, weight="w", seed=0)),
                       key=lambda x: (-len(x), _num(x[0])))
        best = _best(rest, rows)
        main = next((x for x in comms if best in x), comms[0]) if rows.name_score[best] >= NAME_MIN else comms[0]
        subs = [x for x in comms if x is not main and len(x) >= 2]
        main = sorted(main + [k for x in comms if x is not main and len(x) < 2 for k in x], key=_num)
        parent = new_table(ent, ent, f"{ent} (main table)", main, _best(main, rows) if rows.name_score[_best(main, rows)] >= NAME_MIN else None)
        for x in subs:
            top = _best(x, rows)
            sub = new_table(f"{ent}_{_snake(hand[top]['name'])}", ent, f"{ent}: columns that occur together ({hand[top]['name']})", x,
                            top if rows.name_score[top] >= NAME_MIN else None)
            _add_link(c, tabs, sub, parent, "one_to_many")
        for k in child:
            sub = new_table(f"{ent}_{_snake(hand[k]['name'])}", ent, f"{ent}: several values of {hand[k]['name']} per booking", [k], None)
            _add_link(c, tabs, sub, parent, "one_to_many")
    # cross-entity links
    weight = {t: max(rows.n_instances[k] for k, tn in where.items() if tn == t) for t in set(where.values())}
    links = {}
    cr = pairs[(pairs["scope"] == "cross_entity") & (pairs["npmi"] >= LINK_NPMI) & (pairs["count"] >= LINK_COUNT)]
    for r in cr.itertuples():
        a, b = where.get(r.col_a), where.get(r.col_b)
        if a and b and a != b:
            frm, to = sorted((a, b), key=lambda t: (-weight[t], t))
            links.setdefault(frozenset((a, b)), (frm, to))
    for r in fd[(fd["scope"] == "cross_entity") & (fd["status"] == "holds")].itertuples():
        a, b = where.get(r.x), where.get(r.y)       # x -> y: the table of y (dependent) refers to the table of x
        if a and b and a != b:
            links[frozenset((a, b))] = (b, a)
    for frm, to in sorted(links.values()):
        _add_link(c, tabs, frm, to, "one_to_many")
    return c


def load_signals_schema(set_name, root=ROOT):
    d = Path(root) / "results" / "wf_v4" / "signals" / set_name
    df = pd.read_csv(d / "columns.csv")
    pairs, fd = pd.read_csv(d / "pairs.csv"), pd.read_csv(d / "fd.csv")
    hand = {f"{e}:{col['id']}": {"name": col["name"], "value_type": col.get("value_type")}
            for e, data in load_handover(set_name, root).items() for col in data["columns"]}
    return signals_schema(df, pairs, fd, hand)
