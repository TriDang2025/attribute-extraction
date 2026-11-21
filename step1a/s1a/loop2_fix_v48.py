"""wf_v4.8 W2: code-only precision fixes on the final loop-2 columns (columns_l2.json rows + evidence clusters). No LLM, no gold.

One switch each (config/wf_v48_loop2.json), applied in this order on the new columns (status "new") of one entity:
  drop_name_values  F4: drop a mention whose value is the column's own name: no digit, at least one token of the column name or its
                    suggested label, and no other token except generic English stop words (scikit-learn list, not a hand-made list).
                    Tokens match after a plural "s" is cut, or by prefix when both have >= 4 letters (seat ~ seating).
  loop1_embed       F3: a new column is a duplicate of a loop-1 column when >= `share` of its mentions have a value whose normalized form
                    (lowercase, no digits or punctuation) has bge-m3 cosine >= `tau` with a normalized value of that loop-1 column, and
                    >= `l1_share` of the loop-1 column's mentions are close to a value of the new column.
  mix               F2: flag (never drop) a new column when two other, distinct new columns (Jaccard < `distinct_jaccard`), neither
                    holding `share` alone, together hold >= `share` of its mentions (by value).
  join_new          F1: join new, unflagged columns whose distinct value sets have Jaccard >= `jaccard` (transitively); the joined column
                    keeps the name of its largest part.
  mix and join_new compare all values the column was found with (F4-dropped ones too).
Columns carry their own mention lists, so every step sees the result of the steps before it.
"""
import re
from collections import Counter

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

STEPS = ("drop_name_values", "loop1_embed", "mix", "join_new")


def norm(text):
    """Lowercase, digits and punctuation removed, single spaces."""
    return " ".join(re.sub(r"[^a-z]+", " ", str(text).lower()).split())


def _stem(t):
    return t[:-1] if len(t) > 3 and t.endswith("s") else t


def same_token(a, b):
    a, b = _stem(a), _stem(b)
    return a == b or (min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)))


def is_name_value(value, names):
    """True when `value` only restates one of `names` (F4 rule above)."""
    if re.search(r"\d", str(value)):
        return False
    name_toks = [t for n in names for t in norm(n).split()]
    toks = norm(value).split()
    hit = [t for t in toks if any(same_token(t, n) for n in name_toks)]
    return bool(hit) and all(t in hit or t in ENGLISH_STOP_WORDS for t in toks)


def columns_of(rows, clusters):
    """Working columns from columns_l2.json rows of one entity: each row + its mentions (from the clusters) + flags."""
    return [{**r, "mentions": [m for cid in r["clusters"] for m in clusters[cid]["mentions"]],
             "labels": [clusters[cid]["label"] for cid in r["clusters"]], "mix": False, "dropped": Counter(),
             "joined": list(r.get("joined", []))} for r in rows]


def values(col):
    return Counter(m["norm_value"] for m in col["mentions"] if m["norm_value"])


def drop_name_values(cols):
    """F4 on the new columns: (columns, changed names)."""
    changed = []
    for c in (c for c in cols if c["status"] == "new"):
        names = [c["name"].replace("_", " "), *c["labels"]]
        drop = [m for m in c["mentions"] if is_name_value(m["norm_value"], names)]
        if drop:
            c["dropped"].update(m["norm_value"] for m in drop)
            c["mentions"] = [m for m in c["mentions"] if m not in drop]
            changed.append(c["name"])
    return cols, changed


def loop1_share(vals, l1_vals, close):
    """(share of the new mentions, share of the loop-1 mentions) whose normalized value is close (close(a, b) -> bool) to a normalized value
    on the other side. vals, l1_vals: Counters of values."""
    def side(a, b):
        na, nb = Counter(), {norm(v) for v in b} - {""}
        for v, k in a.items():
            na[norm(v)] += k
        na.pop("", None)
        total = sum(na.values())
        return sum(k for v, k in na.items() if any(close(v, w) for w in nb)) / total if total else 0.0
    return side(vals, l1_vals), side(l1_vals, vals)


def loop1_embed(cols, loop1, sim, tau, share, l1_share):
    """F3: loop1 = {loop-1 column name: Counter of values}; sim(a, b) -> cosine of two normalized strings. A new column is a duplicate of
    the loop-1 column with the highest new-side share, when that share >= `share` and the loop-1-side share >= `l1_share` (so one stray
    value in a big catch-all loop-1 column does not count). (columns, changed)."""
    changed = []
    for c in (c for c in cols if c["status"] == "new"):
        vals = values(c)
        scores = [(*loop1_share(vals, lv, lambda a, b: sim(a, b) >= tau), name) for name, lv in loop1.items()]
        ok = [s for s in scores if s[0] >= share and s[1] >= l1_share]
        if ok:
            s_new, s_l1, name = max(ok)
            c.update(status="duplicate", duplicate_of=[name],
                     reason=f"loop-1 values, cosine >= {tau}: {s_new:.2f} of its mentions, {s_l1:.2f} of the loop-1 column's")
            changed.append(f"{c['name']} -> {name}")
    return cols, changed


def all_values(col):
    """Values of the kept and the dropped (F4) mentions: the mix and join tests compare what the column was found with."""
    return values(col) + col["dropped"]


def coverage(vals, *sets):
    """Share of the mentions (Counter vals) whose value is in any of `sets`."""
    total = sum(vals.values())
    return sum(k for v, k in vals.items() if any(v in s for s in sets)) / total if total else 0.0


def mix(cols, share, distinct):
    """F2: flag (never drop) a new column C when two other new columns A, B with Jaccard(A, B) < `distinct` each hold some but less than
    `share` of C's mentions, and together hold >= `share`. A column that one other column holds alone is not a mix (a duplicate, F1).
    Flags are computed on the unflagged state, so the order of the columns does not matter. (columns, changed)."""
    new = [c for c in cols if c["status"] == "new"]
    sets = {id(c): set(all_values(c)) for c in new}
    flags = []
    for c in new:
        vals, others = all_values(c), [o for o in new if o is not c]
        part = [o for o in others if 0 < coverage(vals, sets[id(o)]) < share]
        flags.append(any(jaccard(sets[id(a)], sets[id(b)]) < distinct and coverage(vals, sets[id(a)], sets[id(b)]) >= share
                         for i, a in enumerate(part) for b in part[i + 1:]))
    changed = []
    for c, f in zip(new, flags):
        if f:
            c["mix"] = True
            changed.append(c["name"])
    return cols, changed


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def join_new(cols, threshold):
    """F1: join new, unflagged columns by value Jaccard. (columns, changed)."""
    new = [c for c in cols if c["status"] == "new" and not c["mix"]]
    parent = list(range(len(new)))

    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i in range(len(new)):
        for j in range(i + 1, len(new)):
            if jaccard(set(all_values(new[i])), set(all_values(new[j]))) >= threshold:
                parent[root(j)] = root(i)
    groups = {}
    for i, c in enumerate(new):
        groups.setdefault(root(i), []).append(c)
    changed, gone = [], set()
    for g in (g for g in groups.values() if len(g) > 1):
        head = max(g, key=lambda c: (len(c["mentions"]), c["name"]))
        for c in g:
            if c is not head:
                head["clusters"] = head["clusters"] + c["clusters"]
                head["labels"] = head["labels"] + c["labels"]
                head["mentions"] = head["mentions"] + c["mentions"]
                head["dropped"] = head["dropped"] + c["dropped"]
                head["joined"] = head["joined"] + [c["name"]]
                gone.add(id(c))
                changed.append(f"{c['name']} -> {head['name']}")
    return [c for c in cols if id(c) not in gone], changed


def apply(rows, clusters, loop1, sim, cfg):
    """All switched-on fixes on one entity's columns_l2.json rows. Returns (columns, {step: changed list})."""
    cols, log = columns_of(rows, clusters), {}
    if cfg["drop_name_values"]["on"]:
        cols, log["drop_name_values"] = drop_name_values(cols)
    if cfg["loop1_embed"]["on"]:
        e = cfg["loop1_embed"]
        cols, log["loop1_embed"] = loop1_embed(cols, loop1, sim, e["tau"], e["share"], e["l1_share"])
    if cfg["mix"]["on"]:
        cols, log["mix"] = mix(cols, cfg["mix"]["share"], cfg["mix"]["distinct_jaccard"])
    if cfg["join_new"]["on"]:
        cols, log["join_new"] = join_new(cols, cfg["join_new"]["jaccard"])
    return cols, log


def to_row(c):
    """columns_l2.json row of a working column (+ mix flag, dropped values); clusters and counts follow the kept mentions."""
    vals = values(c)
    return {"name": c["name"], "description": c.get("description", ""), "clusters": c["clusters"], "mention_ids": sorted(m["mention_id"] for m in c["mentions"]),
            "top_values": [v for v, _ in sorted(vals.items(), key=lambda kv: (-kv[1], kv[0]))[:8]], "n_mentions": len(c["mentions"]),
            "status": c["status"], "duplicate_of": c.get("duplicate_of", []), "reason": c.get("reason", ""), "joined": c["joined"],
            "mix": c["mix"], "dropped_values": dict(c["dropped"])}
