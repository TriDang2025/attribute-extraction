"""wf_v3.5 W4 (GT_V35_CONTRACT.md): role evidence for two-role clusters (departure/destination, leave at/arrive by) and
the train instability list. No LLM.

gold role per mention = the L2 slot when it is a role slot of a pair in config/role_pairs.json, for train / taxi only.
Two-role cluster = both slots of one pair, each >= 20% of the cluster's labelled mentions.
T15 role_word_eval: J = role from the cue words before the value (pilot_input.CUE_ROLES: start / end words).
T16 context_split: KMeans k=2 on bge-m3 vectors of the turn with the value replaced by "[V]" when silhouette >= thr.
Both parts are mapped to their own majority gold role, so the table is an upper bound for what a split can give.
T27 train_instability: C s0/s1/s2 clusters whose decision differs across orders, with a reason.
"""

import re

import numpy as np
import pandas as pd

from . import pilot_input as PIN
from . import rules_labels as RL
from . import rules_names as RN
from .labels import _classes

ROLE_DOMAINS = ("train", "taxi")
MIN_SHARE = 0.20           # each role of a two-role cluster, over its labelled mentions
LEFT_WORDS = 3             # words before the value that J inspects
SPLIT_THR = 0.25           # silhouette threshold for context_split (fixed in advance)
MIXED_SHARE = 0.6          # a cluster whose top gold attr is below this share is "mixed"
EVAL_COLS = ["cluster_id", "n", "n_gold_role", "covered", "correct", "accuracy", "coverage"]
_PUNCT = re.compile(r"^\W+|\W+$")
# wf_v3.6: the cue words that are not about the domain (from / to ... work for any pair); the rest of CUE_ROLES are the
# domain words (leave / depart / arrive and their forms)
CUE_GENERAL = {"start": frozenset({"from", "after"}), "end": frozenset({"to", "into", "by", "before"})}
CUE_DOMAIN = {side: PIN.CUE_ROLES[side] - CUE_GENERAL[side] for side in PIN.CUE_ROLES}


def _key(slot):
    return re.sub(r"\s+", "", str(slot).lower())


def _role_table(pairs):
    """{slot key (no spaces): (pair index, side 0/1, canonical slot)}."""
    return {_key(s): (i, side, s) for i, p in enumerate(pairs) for side, s in enumerate(p)}


def gold_role(gold_l2, pairs=None):
    """Series (same index) of the role slot ("departure", "leave at", ...) of each L2 label, "" when it is not a role.
    Only train / taxi labels count; "A;B" labels count when exactly one part is a role slot."""
    table = _role_table(pairs if pairs is not None else RL.role_pairs())

    def one(label):
        roles = set()
        for part in str(label if pd.notna(label) else "").split(";"):
            dom, _, slot = part.strip().partition(" ")
            if dom.lower() in ROLE_DOMAINS and _key(slot) in table:
                roles.add(table[_key(slot)][2])
        return roles.pop() if len(roles) == 1 else ""

    return gold_l2.map(one)


def _side(role, pairs):
    """0 = start side (departure, leave at), 1 = end side (destination, arrive by); None for "" or a non-role."""
    t = _role_table(pairs).get(_key(role))
    return None if t is None else t[1]


def two_role_clusters(mentions, gold_role_s, labelled, pairs=None, min_share=MIN_SHARE):
    """{cluster_id: pair} for clusters where both slots of one pair are each >= min_share of the labelled mentions.
    gold_role_s, labelled: Series indexed like mentions (labelled = bool, mention has any gold label)."""
    pairs = pairs if pairs is not None else RL.role_pairs()
    out = {}
    for c, g in mentions.groupby("cluster_id"):
        lab = int(labelled.loc[g.index].sum())
        if not lab:
            continue
        cnt = gold_role_s.loc[g.index].value_counts()
        for p in pairs:
            if all(cnt.get(s, 0) / lab >= min_share for s in p):
                out[c] = p
                break
    return out


def _local_start(row):
    """Offset of the value inside turn_text: `local_start` when given and right, else the first occurrence."""
    text, turn = str(row["text"]), str(row["turn_text"])
    ls = row.get("local_start", None)
    if ls is not None and pd.notna(ls) and turn[int(ls):int(ls) + len(text)] == text:
        return int(ls)
    return turn.find(text)


def left_tokens(before, k=LEFT_WORDS):
    """The last k words of the text before a value, lowercased, punctuation stripped (an all-punctuation word stays as "")."""
    return [_PUNCT.sub("", t).lower() for t in str(before).split()][-k:]


def side_word(left, words=None):
    """(side, word): the nearest word of `left` (nearest last) that is a start (0) / end (1) cue word of `words`
    ({"start": set, "end": set}; default pilot_input.CUE_ROLES); (None, None) when there is none."""
    words = PIN.CUE_ROLES if words is None else words
    for w in reversed(left):
        for side, name in enumerate(("start", "end")):
            if w in words[name]:
                return side, w
    return None, None


def row_left(row, k=LEFT_WORDS):
    """left_tokens of a mention row (turn text before the value); the mention's `left_word` when the turn text has no
    usable offset."""
    start = _local_start(row)
    return left_tokens(str(row["turn_text"])[:start], k) if start >= 0 else [str(row.get("left_word", ""))]


def j_word(row, k=LEFT_WORDS, words=None):
    """(side, word) of side_word over the k words before the value of a mention row (see row_left)."""
    return side_word(row_left(row, k), words)


def j_side(row, k=LEFT_WORDS, words=None):
    """0 / 1 / None: the side of j_word (start / end cue word before the value)."""
    return j_word(row, k, words)[0]


def _summary(g, pred, gold):
    """One output row: pred / gold are Series of side (0/1/None) for the gold-role mentions of cluster g."""
    covered = pred.notna()
    correct = covered & (pred == gold)
    n_gold = len(gold)
    return {"n": len(g), "n_gold_role": n_gold, "covered": int(covered.sum()), "correct": int(correct.sum()),
            "accuracy": correct.sum() / covered.sum() if covered.sum() else np.nan,
            "coverage": covered.sum() / n_gold if n_gold else np.nan}


def role_word_eval(mentions, gold_role_s, pairs=None, words=None):
    """T15: per cluster with >= 1 gold-role mention. J gives a side from the words before the value; correct when it
    equals the side of the gold role. accuracy = correct / covered, coverage = covered / n_gold_role. `words`: cue
    word sets for j_side (default: all of pilot_input.CUE_ROLES)."""
    pairs = pairs if pairs is not None else RL.role_pairs()
    rows = []
    for c, g in mentions.groupby("cluster_id"):
        gr = gold_role_s.loc[g.index]
        gr = gr[gr != ""]
        if gr.empty:
            continue
        gold = gr.map(lambda r: _side(r, pairs))
        pred = pd.Series([j_side(r, words=words) for _, r in g.loc[gr.index].iterrows()], index=gr.index, dtype=object)
        rows.append({"cluster_id": c, **_summary(g, pred, gold)})
    return pd.DataFrame(rows, columns=EVAL_COLS)


def masked_texts(mentions):
    """The turn text with the value replaced by "[V]", one per mention row."""
    out = []
    for _, r in mentions.iterrows():
        turn, text, s = str(r["turn_text"]), str(r["text"]), _local_start(r)
        out.append(turn if s < 0 else turn[:s] + "[V]" + turn[s + len(text):])
    return out


def _split(x, thr, seed=0):
    """(labels 0/1 or None, silhouette) of KMeans k=2 on rows x; None when silhouette < thr or too few rows."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    if len(x) < 4:
        return None, np.nan
    lab = KMeans(n_clusters=2, n_init=10, random_state=seed).fit_predict(x)
    if len(set(lab)) < 2:
        return None, np.nan
    sil = float(silhouette_score(x, lab))
    return (lab if sil >= thr else None), sil


def _majority(roles):
    roles = [r for r in roles if r]
    return pd.Series(roles).value_counts().index[0] if roles else ""


def context_split(mentions, vectors, gold_role_s, thr=SPLIT_THR, pairs=None):
    """T16: vectors = one row per mentions row (same order). Per cluster with >= 1 gold-role mention: split when the
    silhouette of KMeans k=2 >= thr; each part (or the whole cluster) takes the majority gold role of its own mentions
    (all cluster mentions when the part has none). Columns of T15 plus split, silhouette and acc_nosplit
    (accuracy when the cluster is never split)."""
    pairs = pairs if pairs is not None else RL.role_pairs()
    vectors = np.asarray(vectors, dtype=np.float32)
    if len(vectors) != len(mentions):
        raise ValueError("vectors must have one row per mentions row")
    pos = {i: p for p, i in enumerate(mentions.index)}
    rows = []
    for c, g in mentions.groupby("cluster_id"):
        gr_all = gold_role_s.loc[g.index]
        if (gr_all == "").all():
            continue
        lab, sil = _split(vectors[[pos[i] for i in g.index]], thr)
        parts = [np.ones(len(g), bool)] if lab is None else [lab == 0, lab == 1]
        whole = _majority(gr_all)
        pred = pd.Series("", index=g.index, dtype=object)
        for part in parts:
            ids = g.index[part]
            pred.loc[ids] = _majority(gold_role_s.loc[ids]) or whole
        has = gr_all != ""
        gold = gr_all[has].map(lambda r: _side(r, pairs))
        side = pred[has].map(lambda r: _side(r, pairs) if r else None).astype(object)
        row = _summary(g, side, gold)
        row["acc_nosplit"] = float((gold == _side(whole, pairs)).mean())
        rows.append({"cluster_id": c, **row, "split": lab is not None, "silhouette": sil})
    return pd.DataFrame(rows, columns=EVAL_COLS + ["split", "silhouette", "acc_nosplit"])


def pooled(df, two_role_ids=None):
    """(n_gold_role, covered, correct, accuracy, coverage) summed over the rows (optionally only two-role clusters)."""
    d = df if two_role_ids is None else df[df["cluster_id"].isin(set(two_role_ids))]
    n, cov, ok = int(d["n_gold_role"].sum()), int(d["covered"].sum()), int(d["correct"].sum())
    return {"clusters": len(d), "n_gold_role": n, "covered": cov, "correct": ok,
            "accuracy": ok / cov if cov else np.nan, "coverage": cov / n if n else np.nan}


# ---- T27 train instability

def _cluster_attrs(g):
    cnt = pd.Series([c for ga in g["gold_attr"] for c in _classes(ga)]).value_counts()
    return cnt


def train_instability(ed, gold_l2=None, pairs=None):
    """C s0/s1/s2 clusters whose decision differs across the 3 orders (rules_names.order_diffs rows), each with a reason
    (first match wins): noise_flip (marked in some orders only); role_pair (the cluster, or the clusters grouped with it
    in any order, hold both roles of one pair); mixed_cluster (top gold attr < 60% of its labelled mentions);
    name_wording (only the name string differs); other. gold_l2: Series indexed like ed.mentions (default: gold_attr).
    Columns of order_diffs plus reason."""
    diffs = RN.order_diffs(ed)
    if diffs.empty:
        return diffs.assign(reason=pd.Series(dtype=str))
    pairs = pairs if pairs is not None else RL.role_pairs()
    m = ed.mentions
    labels = (gold_l2 if gold_l2 is not None else m["gold_attr"]).fillna("")
    roles = gold_role(labels, pairs)
    state = RN._seed_state(ed)
    by_cluster = {c: g.index for c, g in m.groupby("cluster_id")}

    def role_set(cids):
        return {r for c in cids for r in roles.loc[by_cluster.get(c, [])] if r}

    def group_members(c):
        out = {c}
        for st in state[c]:
            out |= set(st[1].split("|")) if st and st[1] and not st[1].startswith("split:") else set()
        return out

    def mixed(c):
        g = m.loc[by_cluster.get(c, [])]
        cnt = _cluster_attrs(g.assign(gold_attr=labels.loc[g.index]))
        return len(cnt) > 1 and cnt.iloc[0] / cnt.sum() < MIXED_SHARE

    reasons = []
    for _, r in diffs.iterrows():
        c = r["cluster_id"]
        rs = role_set(group_members(c))
        if r["type"] == "noise":
            reasons.append("noise_flip")
        elif any(all(s in rs for s in p) for p in pairs):
            reasons.append("role_pair")
        elif mixed(c):
            reasons.append("mixed_cluster")
        elif r["type"] == "wording":
            reasons.append("name_wording")
        else:
            reasons.append("other")
    return diffs.assign(reason=reasons)
