"""wf_v4.8 W1: count the filled human-check rows with the `same_as` column (rows are real or not; repeats link to a partner row or a loop-1 column).

same_as forms: "" (no partner), "14" (repeat of row 14), "loop-1 cuisine column" (repeats a loop-1 column: real, not new),
"20; loop-1 cuisine column" (both), "mix of 8 + 22" (mixes two other rows). Repeat links are joined transitively; a group that touches
a loop-1 column is a loop-1 repeat as a whole. Each group counts once.
"""
import re

from s1a import mainclaim_v41 as M


def parse_same_as(text):
    """(partner row ids, repeats a loop-1 column, is a mix) of one same_as cell."""
    t = (text or "").strip().lower()
    if t.startswith("mix"):
        return set(), False, True
    parts = [p.strip() for p in t.split(";") if p.strip()]
    ids = {int(p) for p in parts if p.isdigit()}
    bad = [p for p in parts if not p.isdigit() and not re.match(r"loop-1 .+ column$", p)]
    if bad:
        raise ValueError(f"same_as not understood: {text!r}")
    return ids, any(not p.isdigit() for p in parts), False


def groups(rows):
    """Real rows (dicts with id, real, same_as, ...) -> list of groups {"ids": sorted ids, "kind": new | loop1_repeat | mix}.
    Links to rows outside `rows` (another source) are ignored."""
    real = {int(r["id"]): r for r in rows if M.parse_real(r["real"])}
    parent = {i: i for i in real}

    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i

    info = {i: parse_same_as(r.get("same_as", "")) for i, r in real.items()}
    for i, (ids, _, _) in info.items():
        for j in ids & real.keys():
            parent[find(i)] = find(j)
    out = {}
    for i in real:
        out.setdefault(find(i), []).append(i)
    res = []
    for ids in out.values():
        kind = ("mix" if any(info[i][2] for i in ids) else "loop1_repeat" if any(info[i][1] for i in ids) else "new")
        res.append({"ids": sorted(ids), "kind": kind})
    return sorted(res, key=lambda g: g["ids"])


def summary(rows):
    """Counts of one source's sheet rows: rows, real rows, groups per kind, repeat rows (rows with a same_as link, mixes left out).
    new_not_gold = new groups with no row whose name matches a gold attribute (key column name_match)."""
    gs = groups(rows)
    real = [r for r in rows if M.parse_real(r["real"])]
    by_id = {int(r["id"]): r for r in rows}
    new = [g for g in gs if g["kind"] == "new"]
    return {"rows": len(rows), "real_rows": len(real),
            "new_groups": len(new),
            "new_not_gold": sum(not any(by_id[i].get("name_match") for i in g["ids"]) for g in new),
            "loop1_repeat_groups": sum(g["kind"] == "loop1_repeat" for g in gs),
            "mix": sum(g["kind"] == "mix" for g in gs),
            "repeat_rows": sum(bool(r.get("same_as", "").strip()) and not parse_same_as(r["same_as"])[2] for r in real)}
