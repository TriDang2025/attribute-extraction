"""Conversation dialogues (MultiWOZ 2.4) with gold turn domains, documents and retrieval queries.

Gold domain of a turn:
- system turn 2k-1 uses the domains in its dialogue acts (key k in dialogue_acts.json), ignoring
  `general` and `Booking`; if the previous turn's domain is among them it is kept (no switch);
  with no act domain, the domain whose belief state changed at that turn is used;
- a user turn takes the domain of the system turn that answers it;
- turns still unlabelled inherit from the previous turn (leading ones from the first label).
A gold boundary is a turn gap where the domain (or, when stitched, the dialogue) changes.
"""

import json
import random
import re
import zipfile
from dataclasses import dataclass, field

from . import config

DOMAINS = ("attraction", "hospital", "hotel", "police", "restaurant", "taxi", "train", "bus")


def clean_turn(text):
    return re.sub(r"\s+", " ", text).strip()


def _flat_state(meta):
    out = {}
    for dom, v in meta.items():
        for part in ("semi", "book"):
            for k, x in v.get(part, {}).items():
                if k == "booked":
                    x = json.dumps(x) if x else ""
                if x not in ("", "not mentioned", "none"):
                    out[(dom, part, k)] = x
    return out


def turn_domains(log, acts):
    n = len(log)
    dom = [None] * n
    prev_state, last = {}, None
    for i in range(1, n, 2):
        a = acts.get(str((i + 1) // 2))
        cand = []
        if isinstance(a, dict):
            for key in a:
                d = key.split("-")[0].lower()
                if d in DOMAINS and d not in cand:
                    cand.append(d)
        state = _flat_state(log[i].get("metadata") or {})
        changed = sorted({k[0] for k, v in state.items() if prev_state.get(k) != v})
        prev_state = state
        if not cand:
            cand = [d for d in changed if d in DOMAINS]
        if cand:
            dom[i] = last if last in cand else cand[0]
            last = dom[i]
        if dom[i] is not None:
            dom[i - 1] = dom[i]
    # fill: inherit forward, leading turns from the first label
    first = next((d for d in dom if d), "general")
    cur = first
    for i in range(n):
        if dom[i] is None:
            dom[i] = cur
        cur = dom[i]
    return dom


def _goal_queries(goal):
    """Goal message sentences grouped by the domain they describe."""
    msg = goal.get("message", [])
    if isinstance(msg, str):  # WOZ dialogues: one string "Task 01234: You are looking for ..."
        msg = [re.sub(r"^Task \d+:\s*", "", msg)]
    found = [d for d in DOMAINS if goal.get(d)]
    out, cur = {}, None
    for s in msg:
        s = clean_turn(re.sub(r"<[^>]+>", "", s))
        low = s.lower()
        if low.startswith(("you are traveling", "you are looking for information")):
            continue  # task intro, no domain
        if any(p in low for p in _NEW_GOAL):
            # the domain named first in the sentence ("places to go ... same area as the restaurant")
            pos = {d: min(low.find(w) for w in words if w in low)
                   for d, words in _DOMAIN_WORDS.items() if d in found and any(w in low for w in words)}
            cur = min(pos, key=pos.get) if pos else None
        if cur:
            out.setdefault(cur, []).append(s)
    return {d: " ".join(v) for d, v in out.items()}


_NEW_GOAL = ("looking for", "you want to find", "want to book a taxi", "you were robbed",
             "you got injured", "you are injured")
_DOMAIN_WORDS = {
    "train": ("train",), "taxi": ("taxi",), "hospital": ("hospital", "injured"),
    "police": ("police", "robbed"),
    "hotel": ("place to stay", "hotel", "guesthouse", "guest house"),
    "restaurant": ("restaurant", "place to dine", "place to eat"),
    "attraction": ("places to go", "attraction", "place to go", "things to do"),
}


def load_dialogues(limit=None):
    ids = [l.strip() for l in open(config.IDS, encoding="utf-8") if l.strip()]
    if limit:
        ids = ids[:limit]
    with zipfile.ZipFile(config.MULTIWOZ_ZIP) as z:
        data = json.loads(z.read("MULTIWOZ2.4/data.json"))
        acts = json.loads(z.read("MULTIWOZ2.4/dialogue_acts.json"))
    out = []
    for did in ids:
        d = data[did + ".json"]
        log = d["log"]
        turns = [("User" if i % 2 == 0 else "System") + ": " + clean_turn(t.get("text", ""))
                 for i, t in enumerate(log)]
        out.append({"id": did, "turns": turns, "domains": turn_domains(log, acts.get(did, {})),
                    "queries": _goal_queries(d["goal"])})
    return out


@dataclass
class Doc:
    doc_id: str
    text: str
    spans: list            # (start, end) of each turn in text
    domains: list          # gold domain per turn
    dialogue: list         # dialogue id per turn
    gold_gaps: set = field(default_factory=set)  # gap g = between turn g and g+1

    @property
    def n_turns(self):
        return len(self.spans)


def make_doc(doc_id, dialogues):
    parts, spans, domains, dial, pos = [], [], [], [], 0
    for dlg in dialogues:
        for t, d in zip(dlg["turns"], dlg["domains"]):
            if parts:
                pos += 1  # "\n"
            spans.append((pos, pos + len(t)))
            parts.append(t)
            pos += len(t)
            domains.append(d)
            dial.append(dlg["id"])
    gaps = {g for g in range(len(spans) - 1)
            if domains[g] != domains[g + 1] or dial[g] != dial[g + 1]}
    return Doc(doc_id, "\n".join(parts), spans, domains, dial, gaps)


def single_docs(dialogues):
    return [make_doc(d["id"], [d]) for d in dialogues]


def stitched_docs(dialogues, seed, size=config.STITCH_SIZE):
    order = list(dialogues)
    random.Random(seed).shuffle(order)
    return [make_doc(f"stitch{seed}_{i // size:03d}", order[i:i + size])
            for i in range(0, len(order), size)]


def queries(dialogues, docs):
    """One query per (dialogue, goal domain); gold = that dialogue's turns with that domain."""
    where = {}
    for doc in docs:
        for t, did in enumerate(doc.dialogue):
            where.setdefault(did, (doc.doc_id, []))[1].append(t)
    out = []
    for dlg in dialogues:
        doc_id, turn_ids = where[dlg["id"]]
        for dom, q in dlg["queries"].items():
            gold = [t for t, d in zip(turn_ids, dlg["domains"]) if d == dom]
            if gold:
                out.append({"qid": f"{dlg['id']}:{dom}", "text": q, "doc_id": doc_id, "turns": gold})
    return out
