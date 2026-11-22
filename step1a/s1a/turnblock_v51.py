"""wf_v5.1 R2 (S6): same-turn block for joins. One attribute rarely appears twice in one turn with two different values; if two clusters /
columns often do ("from X to Y", "leave after A, arrive by B"), they are two roles and must not be joined.

share(A, B) = fraction of the mentions of A and B that sit in the same turn as a mention of the other side with a different value.
count(A, B) = number of turns that hold such a pair. blocked(...) = share > min_share and count >= min_count.
"Different value": normalized strings (lower case, no punctuation or leading article, single spaces) where neither contains the other,
and the two char spans do not overlap (two clusters reading the same text are not two values). Generic: no word lists, no gold.
Switch: the Step 3 reconcile / duplicate check / vote code calls `blocked(...)` (off = never called; `min_share=None` = never blocks).
CPU only.
"""

import re
from collections import defaultdict

ARTICLE = re.compile(r"^(the|a|an)\s+")


def norm_value(v):
    """Lower case, punctuation to space, leading article dropped, single spaces."""
    s = re.sub(r"[^\w\s:]", " ", str(v).lower())
    return ARTICLE.sub("", " ".join(s.split()))


def different(a, b):
    """Two normalized values differ when neither contains the other (the same value in a longer or shorter form is one value)."""
    return bool(a) and bool(b) and a not in b and b not in a


class TurnIndex:
    """Mention table as {mention_id: (turn key, normalized value, char start, char end)}; mentions = DataFrame indexed by mention_id with
    dialogue_id, turn, norm_value (or text), char_start, char_end (graph_v22_<set>/spans/mentions.csv)."""

    def __init__(self, mentions):
        col = "norm_value" if "norm_value" in mentions.columns else "text"
        self.m = {int(i): ((r.dialogue_id, int(r.turn)), norm_value(getattr(r, col)), int(r.char_start), int(r.char_end))
                  for i, r in zip(mentions.index, mentions.itertuples())}


def pair_stats(index, ids_a, ids_b):
    """{share, count, hits, n}: n = mentions of both sides, hits = mentions with a different-valued mention of the other side in the same
    turn, count = turns with such a pair, share = hits / n (0 when empty). A mention in both sides counts once per side it is in."""
    by_turn = defaultdict(lambda: ([], []))
    for side, ids in enumerate((ids_a, ids_b)):
        for i in ids:
            by_turn[index.m[int(i)][0]][side].append(int(i))
    hit_a, hit_b, turns = set(), set(), set()
    for turn, (xs, ys) in by_turn.items():
        for x in xs:
            _, vx, sx, ex = index.m[x]
            for y in ys:
                _, vy, sy, ey = index.m[y]
                if x != y and different(vx, vy) and (ex <= sy or ey <= sx):
                    hit_a.add(x)
                    hit_b.add(y)
                    turns.add(turn)
    n = len(set(ids_a)) + len(set(ids_b))
    hits = len(hit_a) + len(hit_b)
    return {"share": hits / n if n else 0.0, "count": len(turns), "hits": hits, "n": n}


def blocked(pair, index, min_share=0.1, min_count=1):
    """True when the join of the two sides in `pair` = (mention ids of side A, mention ids of side B) is blocked: share > min_share and
    count >= min_count. Works for two clusters, a part and a column, or two columns (sides = all their mention ids).
    min_share None = switch off."""
    if min_share is None:
        return False
    s = pair_stats(index, *pair)
    return s["share"] > min_share and s["count"] >= min_count


def unjoin_blocked(clusters, size, is_blocked):
    """Split the clusters of one column into groups that hold no blocked pair: cannot-link greedy, biggest cluster first, a cluster joins the
    first group with no blocked pair to it (else a new group). clusters = cluster ids; size = {cluster id: n mentions};
    is_blocked(a, b) -> bool. Returns a list of cluster lists; one group when nothing is blocked."""
    groups = []
    for c in sorted(clusters, key=lambda c: (-size[c], c)):
        for g in groups:
            if not any(is_blocked(c, o) for o in g):
                g.append(c)
                break
        else:
            groups.append([c])
    return groups


def apply_to_columns(columns, cluster_of, names, index, min_share=0.1, min_count=1):
    """Replay: un-join the blocked pairs of final columns (final_columns.json entries; cid, name, groups, members "cluster@group",
    mention_ids). Per column the clusters are cut into groups with no blocked pair (unjoin_blocked; sides = the mention ids of each
    cluster in the column). The biggest group keeps the column (name, cid); every other group is a new column (cid = max cid + k,
    `unjoined_from` = old cid) named by the pre-merge name of its biggest cluster (names = nojoin_v50.premerge_names), else
    "<column name> <cluster id>". Unblocked columns are returned unchanged."""
    out, next_cid = [], max((c["cid"] for c in columns), default=0) + 1
    for col in columns:
        ids = [int(i) for i in col["mention_ids"]]
        clusters = list(dict.fromkeys(m.split("@")[0] for m in col["members"]))
        mine = {c: [i for i in ids if cluster_of.get(i) == c] for c in clusters}
        groups = unjoin_blocked(clusters, {c: len(v) for c, v in mine.items()},
                                lambda a, b: blocked((mine[a], mine[b]), index, min_share, min_count)) if len(clusters) > 1 else [clusters]
        if len(groups) == 1:
            out.append(col)
            continue
        for k, g in enumerate(groups):
            gm = [i for i in ids if cluster_of.get(i) in g]
            mem = [m for m in col["members"] if m.split("@")[0] in g]
            new = {**col, "members": mem, "mention_ids": gm, "n_mentions": len(gm), "groups": [m.split("@")[1] for m in mem]}
            if k:
                new.update(cid=next_cid, name=names.get(g[0]) or f"{col['name']} {g[0]}", unjoined_from=col["cid"])
                next_cid += 1
            out.append(new)
    return out
