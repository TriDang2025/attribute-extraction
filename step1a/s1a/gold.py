"""Gold mentions for the v2 protocol: every occurrence of every gold value, with a label set.

- Classes: same-entity attributes that hold the same value in most dialogues are one class
  (Restaurant/Hotel name and confirmed name); the class is named after the shorter attribute.
- A hit takes the attributes having that value whose entity is the turn's gold domain; if none,
  all of them, flagged ambiguous. A hit inside a longer hit of another value is dropped.
- "yes"/"no" values and values with no hit are non-verbatim mentions (start = end = turn = -1).
- hidden[k]: some raw label is hidden at TEAR level k (levels.json).
"""

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import paths
from .units import Unit, turn_of

NON_VERBATIM = {"yes", "no"}


def load_levels(path=paths.TEAR_DATA / "levels.json"):
    d = json.loads(path.read_text(encoding="utf-8"))
    return {int(k): set(v["hidden"]) for k, v in d["levels"].items()}


def load_all_tables(tear_data=paths.TEAR_DATA):
    """id -> table for every text with a table (pool + test: 1,000)."""
    out = {}
    for name in ("pool", "test"):
        for line in open(tear_data / f"{name}.jsonl", encoding="utf-8"):
            r = json.loads(line)
            if r.get("table") and r["id"] not in out:
                out[r["id"]] = r["table"]
    return out


def norm(v):
    return str(v).strip().lower()


def entity(attr):
    return attr.split()[0].lower()


def cell_values(table):
    """attribute -> set of normalized non-empty values."""
    out = defaultdict(set)
    for row in table["rows"]:
        for header, vals in zip(table["headers"], row):
            for v in vals:
                if norm(v):
                    out[header].add(norm(v))
    return out


def merge_classes(tables, threshold=0.5):
    """attribute -> class name. Same-entity pairs whose verbatim (non yes/no) values are equal in
    >= threshold of the dialogues holding both (n_same / min(count_a, count_b)) are merged."""
    tables = tables.values() if isinstance(tables, dict) else tables
    count, same, attrs = Counter(), Counter(), set()
    for t in tables:
        cv = {a: v - NON_VERBATIM for a, v in cell_values(t).items()}
        attrs |= set(cv)
        cv = {a: v for a, v in cv.items() if v}
        count.update(list(cv))
        names = sorted(cv)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if entity(a) == entity(b) and cv[a] == cv[b]:
                    same[(a, b)] += 1
    parent = {a: a for a in attrs}

    def root(a):
        while parent[a] != a:
            a = parent[a]
        return a

    for (a, b), n in same.items():
        if n / min(count[a], count[b]) >= threshold:
            ra, rb = root(a), root(b)
            if ra != rb:
                parent[max(ra, rb, key=lambda x: (len(x), x))] = min(ra, rb, key=lambda x: (len(x), x))
    return {a: root(a) for a in attrs}


@dataclass
class Mention(Unit):
    labels: frozenset = frozenset()      # class names
    raw_labels: frozenset = frozenset()  # attribute names
    verbatim: bool = True
    ambiguous: bool = False
    hidden: dict = field(default_factory=dict)
    value: str = ""


def _mention(doc, raw, classes, levels, value, text, s=-1, e=-1, ambiguous=False):
    labels = frozenset(classes.get(a, a) for a in raw)
    verbatim = s >= 0
    return Mention("mention", doc.doc_id, "|".join(sorted(labels)), text, s, e,
                   turn_of(doc, s) if verbatim else -1, labels=labels, raw_labels=frozenset(raw),
                   verbatim=verbatim, ambiguous=ambiguous,
                   hidden={k: bool(set(raw) & h) for k, h in levels.items()}, value=value)


def mentions(doc, table, levels, classes):
    attrs_of = defaultdict(set)  # value -> attributes holding it
    for a, vs in cell_values(table).items():
        for v in vs:
            attrs_of[v].add(a)
    hits = []
    for v in attrs_of:
        if v in NON_VERBATIM:
            continue
        pat = re.compile(r"(?<!\w)" + re.escape(v) + r"(?!\w)", re.I)
        hits += [(m.start(), m.end(), v) for m in pat.finditer(doc.text)]
    keep = [(s, e, v) for s, e, v in hits
            if not any(v2 != v and s2 <= s and e <= e2 and e2 - s2 > e - s for s2, e2, v2 in hits)]
    out, found = [], set()
    for s, e, v in sorted(keep):
        dom = doc.domains[turn_of(doc, s)]
        raw = {a for a in attrs_of[v] if entity(a) == dom}
        amb = not raw
        out.append(_mention(doc, raw or attrs_of[v], classes, levels, v, doc.text[s:e], s, e, amb))
        found.add(v)
    for v in sorted(set(attrs_of) - found):
        out.append(_mention(doc, attrs_of[v], classes, levels, v, v))
    return out


def mentions_for(docs, tables, levels=None, classes=None):
    """All mentions of the docs (dict doc_id -> Doc) that have a table."""
    levels = load_levels() if levels is None else levels
    classes = merge_classes(load_all_tables()) if classes is None else classes
    return [m for did, doc in docs.items() if did in tables
            for m in mentions(doc, tables[did], levels, classes)]
