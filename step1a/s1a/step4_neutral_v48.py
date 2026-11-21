"""wf_v4.8 W3 variant B: neutral table ids in pass 2 of Step 4 (chain key `neutral_ids` of s1a/step4_v44.py; off = v4.3 / v4.6 as before).

Why: with LLM entity names (e.g. "location") pass 2 put every dev50 column in one table (wf_v4.6). Pass 1 is unchanged (frozen prompt).
Pass 2 lists the tables as table_1, table_2, ... (pass-1 order); the pass-1 names are shown only as a hint line under the table list. The
schema enum holds the neutral ids (plus the third option), so the answer can only name a neutral id. After pass 2, code names each table
from its columns: the most common Step 1a entity heading of the columns placed there (ties: first in column order), made unique with
_2, _3 ... (step4_v43._uniq rules). Pairs, keys and the assembly then see these names. Works with p2_batch (each batch gets the same list).
"""
from collections import Counter

from . import step4_prompts as SP
from . import step4_v43 as V

HINT = ("Table hints (the names given to these tables before; use them only as a hint, the columns decide): {pairs}.\n")


def neutral(names):
    """table_1 ... table_n for the pass-1 names."""
    return [f"table_{i + 1}" for i in range(len(names))]


def build_p2(build, cols, names):
    """(text, schema, format) of a neutral pass 2: `build(cols, ids)` is the chain's pass-2 builder; the hint line goes after the table list."""
    ids = neutral(names)
    text, schema, fmt = build(cols, ids)
    line = "Tables: " + ", ".join(ids) + "\n"
    if line not in text:
        raise ValueError("pass-2 prompt has no 'Tables: ...' line; neutral ids need it")
    hint = HINT.format(pairs=", ".join(f"{i} = {n}" for i, n in zip(ids, names)))
    return text.replace(line, line + hint, 1), schema, fmt


def name_tables(assign, kept, cols, log=None, where=""):
    """(assign with code names, names in the order of `kept`, {neutral id: name}): each neutral table is named after the most common entity
    heading of its columns. assign = {column id: neutral id or None}."""
    by = {}
    for c in cols:
        t = assign.get(c["id"])
        if t is not None:
            by.setdefault(t, []).append(V._slug(SP._entity(c)))
    taken, rename = set(), {}
    for t in kept:
        cnt = Counter(by.get(t, []))
        best = max(cnt.values(), default=0)
        base = next((e for e in by.get(t, []) if cnt[e] == best), t)
        name = base
        k = 2
        while name in taken:
            name = f"{base}_{k}"
            k += 1
        taken.add(name)
        rename[t] = name
        if log is not None:
            log.add("neutral_table_named", where, f"{t} -> {name}")
    return {i: (rename.get(t) if t is not None else None) for i, t in assign.items()}, [rename[t] for t in kept], rename
