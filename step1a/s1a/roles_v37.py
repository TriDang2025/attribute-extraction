"""wf_v3.7 T12/T13: cue words learned per cluster (no gold labels) and the J split of two-role clusters.

Cue words: the general ones (roles_v35.CUE_GENERAL: from, after / to, into, by, before) plus, per cluster, learned words.
Learned word: the word just before a mention (the last token of `left`); kept for a cluster when splitting the cluster by
it gives two parts that are each >= MIN_SHARE of its mentions. Side of a learned word (no gold role is used): among the
mentions it precedes, the side given by the general cue words (nearest general word in the 3 words before the value);
the word gets the majority side when there are >= MIN_EVIDENCE such mentions, they are >= EV_SHARE of the mentions the
word precedes, and the majority is >= AGREE of them; otherwise it is not used. J side of a mention = nearest word of the 3 before the value that is a general or learned
cue word of its cluster. A cluster is split when J puts >= MIN_SHARE of its mentions on each side; mentions with no cue
word form an own "unknown role" part. Pure functions of lists of left tokens (roles_v35.left_tokens).
"""

from collections import Counter

import pandas as pd

from . import roles_v35 as R

MIN_SHARE = R.MIN_SHARE   # 0.20, as the two-role cluster rule
MIN_EVIDENCE = 2
EV_SHARE = 0.2            # mentions with side evidence, over the mentions the word precedes
AGREE = 0.8
GENERAL = R.CUE_GENERAL
SIDES = ("start", "end")
UNKNOWN = 2               # part id of the mentions with no cue word (0 = start side, 1 = end side)
WORD_COLS = ["cluster_id", "word", "n_word", "n_cluster", "ev_start", "ev_end", "side"]


def _just_before(left):
    return left[-1] if left and left[-1] else ""


def learn_words(lefts, general=GENERAL, min_share=MIN_SHARE, min_evidence=MIN_EVIDENCE, agree=AGREE, ev_share=EV_SHARE):
    """(words, rows): words = {"start": set, "end": set} learned for one cluster whose mentions have the left-token lists
    `lefts` (nearest last); rows = one dict per candidate word (n_word, n_cluster, ev_start, ev_end, side or None)
    for the words that pass the share rule, to show how each was mapped."""
    n = len(lefts)
    known = set().union(*general.values())
    cnt = Counter(w for w in map(_just_before, lefts) if w and w not in known)
    words, rows = {s: set() for s in SIDES}, []
    for w, c in sorted(cnt.items()):
        if c / n < min_share or (n - c) / n < min_share:
            continue
        ev = Counter(R.side_word(left, general)[0] for left in lefts if _just_before(left) == w)
        e0, e1 = ev.get(0, 0), ev.get(1, 0)
        side = None
        if e0 + e1 >= max(min_evidence, ev_share * c) and max(e0, e1) / (e0 + e1) >= agree:
            side = 0 if e0 > e1 else 1
            words[SIDES[side]].add(w)
        rows.append({"word": w, "n_word": c, "n_cluster": n, "ev_start": e0, "ev_end": e1, "side": side})
    return words, rows


def merged(general, learned):
    return {s: frozenset(general[s]) | frozenset(learned[s]) for s in SIDES}


def cluster_sides(lefts, words):
    """J side (0 / 1 / None) of each mention of one cluster."""
    return [R.side_word(left, words)[0] for left in lefts]


def split_parts(sides, min_share=MIN_SHARE):
    """Part id per mention (0 start, 1 end, UNKNOWN = no cue word) when each of the two sides holds >= min_share of the
    cluster's mentions, else None."""
    n = len(sides)
    if not n or min(sum(s == 0 for s in sides), sum(s == 1 for s in sides)) / n < min_share:
        return None
    return [UNKNOWN if s is None else s for s in sides]


def split_labels(labels, groups, lefts, general=GENERAL, learn=True):
    """(new labels, stats) for spans with cluster labels `labels` (inside stage-1 groups `groups`) and left-token lists
    `lefts`. A split cluster's mentions get the label (label, part); other labels are returned unchanged. stats: one dict
    per split cluster (label, n, parts sizes, learned words, `members` = indices of its mentions, `parts` per member)."""
    members = {}
    for i, key in enumerate(zip(groups, labels)):
        members.setdefault(key, []).append(i)
    out, stats = list(labels), []
    for (g, lab), idx in members.items():
        ls = [lefts[i] for i in idx]
        learned, _ = learn_words(ls, general) if learn else ({s: set() for s in SIDES}, [])
        parts = split_parts(cluster_sides(ls, merged(general, learned)))
        if parts is None:
            continue
        for i, p in zip(idx, parts):
            out[i] = (lab, p)
        stats.append({"label": lab, "n": len(idx), "start": parts.count(0), "end": parts.count(1),
                      "unknown": parts.count(UNKNOWN),
                      "learned": sorted(learned["start"] | learned["end"]), "members": idx, "parts": parts})
    return out, stats


def learned_eval(mentions, gold_role_s, pairs=None, general=GENERAL, learn=True, **learn_kw):
    """T12: (role_word_eval table, learned-word table) with the cue words general + learned per cluster (learn=True) or
    general only. `mentions` as for roles_v35.role_word_eval plus turn_text / local_start (roles_v35.row_left); the gold
    roles only score, they never enter the learning. learn_kw: learn_words options."""
    parts, words = [], []
    for c, g in mentions.groupby("cluster_id"):
        lefts = [R.row_left(r) for _, r in g.iterrows()]
        learned, rows = learn_words(lefts, general, **learn_kw) if learn else ({s: set() for s in SIDES}, [])
        words += [{"cluster_id": c, **r} for r in rows]
        parts.append(R.role_word_eval(g, gold_role_s, pairs, merged(general, learned)))
    ev = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=R.EVAL_COLS)
    return ev, pd.DataFrame(words, columns=WORD_COLS)
