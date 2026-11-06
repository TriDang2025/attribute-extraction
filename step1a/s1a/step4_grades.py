"""wf_v4 task 11: read the answers of the blind grading (task 9) and compute the agreement and control checks (pure functions; the script
scripts/read_grades_v4.py does the file I/O).

Choices:
- Item scores: grouping, names, relationships, keys, design_quality, overall (1-5). `mean6` = their mean, the packet's total score.
- Judge agreement: first answers (repeat 1) of the two judges on the same codes; exact = same score, within 1 = |difference| <= 1; for the
  answerability questions exact agreement of the yes / partly / no answers.
- Self-agreement: answer 1 against `_r2` of the same judge and code, same measures.
- Controls, per judge and set: rank of each candidate by mean6 (1 = best, ties share the better rank). GT near top = rank <= 2, d near
  bottom = rank >= n - 1, planted GT in the middle = rank 3 .. n - 2 (n candidates graded in the set), also reported: planted below GT and
  above d.
- Planted errors named: lower-cased text of all reasons (not the answerability ones), "_" read as a space. merge: both table names
  appear; fk_removed: the FK column name appears or both the table and the referenced table; column_moved: the column name appears.
- Spearman: average ranks, Pearson on ranks, over all candidates graded by the judge (both sets pooled); pairs with a missing automatic score are dropped.
"""
import json
import re
from collections import defaultdict
from itertools import combinations

ITEMS = ("grouping", "names", "relationships", "keys", "design_quality", "overall")
ANSWERS = ("yes", "partly", "no")
FILE = re.compile(r"^(.+)_([A-Z]{4})(_r2)?\.json$")
AUTO = ("grouping_f1", "table_f1", "rel_recall", "pk_right")


def parse_answer(text, code=None):
    """Parsed answer dict from the judge's text (a code fence or text around the JSON is stripped). Raises ValueError when it is not
    valid: not JSON, a score outside 1-5, not 8 answerability items, an answer other than yes / partly / no, a different code."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    if not t.startswith("{"):
        i, j = t.find("{"), t.rfind("}")
        if i < 0 or j < i:
            raise ValueError("no JSON object")
        t = t[i:j + 1]
    d = json.loads(t)
    for k in ITEMS:
        s = d.get(k, {}).get("score") if isinstance(d.get(k), dict) else None
        if not isinstance(s, int) or isinstance(s, bool) or not 1 <= s <= 5:
            raise ValueError(f"{k}: score must be an integer 1-5, got {s!r}")
    a = d.get("answerability")
    if not isinstance(a, list) or len(a) != 8 or any(x.get("answer") not in ANSWERS for x in a):
        raise ValueError("answerability: need 8 items answered yes / partly / no")
    if code and d.get("code") != code:
        raise ValueError(f"code {d.get('code')!r} differs from the file name code {code!r}")
    return d


def answer_row(judge, code, repeat, d):
    """Flat CSV row of one parsed answer."""
    row = {"judge": judge, "code": code, "repeat": repeat, "model": d.get("model", "")}
    row.update({k: d[k]["score"] for k in ITEMS})
    row["mean6"] = sum(d[k]["score"] for k in ITEMS) / len(ITEMS)
    ans = [x["answer"] for x in sorted(d["answerability"], key=lambda x: x.get("q", 0))]
    row.update({f"q{i}": a for i, a in enumerate(ans, 1)})
    row.update({f"n_{a}": ans.count(a) for a in ANSWERS})
    row["reasons"] = " | ".join(f"{k}: {d[k].get('reason', '')}" for k in ITEMS)
    return row


def spearman(x, y):
    """Spearman rho of two lists (pairs with None dropped); None when fewer than 3 pairs or no variance."""
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 3:
        return None
    ra, rb = _avg_ranks([p[0] for p in pairs]), _avg_ranks([p[1] for p in pairs])
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((a - ma) * (b - mb) for a, b in zip(ra, rb))
    va, vb = sum((a - ma) ** 2 for a in ra), sum((b - mb) ** 2 for b in rb)
    return cov / (va * vb) ** 0.5 if va and vb else None


def _avg_ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r, i = [0.0] * len(v), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def _agree(pairs):
    """{"n", "exact", "within1"} (shares, None when n = 0) over pairs of numbers."""
    n = len(pairs)
    return {"n": n, "exact": sum(a == b for a, b in pairs) / n if n else None,
            "within1": sum(abs(a - b) <= 1 for a, b in pairs) / n if n else None}


def _qa(codes, ra, rb):
    pairs = [(ra[c][f"q{i}"], rb[c][f"q{i}"]) for c in codes for i in range(1, 9)]
    return {"n": len(pairs), "exact": sum(x == y for x, y in pairs) / len(pairs) if pairs else None}


def _compare(ra, rb):
    """Agreement per item and on answerability between two {code: row} dicts."""
    codes = sorted(set(ra) & set(rb))
    out = {k: _agree([(ra[c][k], rb[c][k]) for c in codes]) for k in ITEMS}
    out["answerability"] = _qa(codes, ra, rb)
    return out


def judge_agreement(rows, j1, j2):
    """Agreement of two judges' first answers per item and on the answerability questions."""
    pick = lambda j: {r["code"]: r for r in rows if r["judge"] == j and r["repeat"] == 1}  # noqa: E731
    return _compare(pick(j1), pick(j2))


def self_agreement(rows, judge):
    """Answer 1 against the repeat of the same judge and code, per item and on answerability."""
    pick = lambda n: {r["code"]: r for r in rows if r["judge"] == judge and r["repeat"] == n}  # noqa: E731
    return _compare(pick(1), pick(2))


def ranks(values):
    """{name: rank} 1 = highest value, ties share the better rank."""
    return {k: 1 + sum(v2 > v for v2 in values.values()) for k, v in values.items()}


def controls(rows, key, judge):
    """Per set: ranks of gt, d, gt_planted by mean6 and the control flags (see module doc); None when a candidate is not graded."""
    by = defaultdict(dict)
    for r in rows:
        if r["judge"] == judge and r["repeat"] == 1 and r["code"] in key["packets"]:
            p = key["packets"][r["code"]]
            by[p["set"]][p["candidate"]] = r["mean6"]
    out = {}
    for s, vals in by.items():
        rk, n = ranks(vals), len(vals)
        gt, d, pl = rk.get("gt"), rk.get("d"), rk.get("gt_planted")
        out[s] = {"n": n, "gt_rank": gt, "d_rank": d, "planted_rank": pl,
                  "gt_top": None if gt is None else gt <= 2, "d_bottom": None if d is None else d >= n - 1,
                  "planted_middle": None if pl is None else 3 <= pl <= n - 2,
                  "planted_between": None if None in (gt, d, pl) else vals["gt"] > vals["gt_planted"] > vals["d"]}
    return out


def planted_named(reasons, errors):
    """[bool] per planted error: does the reason text name it (module doc)."""
    t = reasons.lower().replace("_", " ")
    out = []
    for e in errors:
        kw = [k.lower().replace("_", " ") for k in e["keywords"]]
        if e["kind"] == "merge":
            out.append(all(k in t for k in kw))
        elif e["kind"] == "fk_removed":
            out.append(kw[0] in t or (kw[1] in t and kw[2] in t))
        else:
            out.append(kw[0] in t)
    return out


def planted_report(rows, key, judge):
    """{set: [bool, ...]} named planted errors in the judge's answer for the planted GT of each set."""
    out = {}
    for r in rows:
        p = key["packets"].get(r["code"])
        if r["judge"] == judge and r["repeat"] == 1 and p and p["candidate"] == "gt_planted":
            out[p["set"]] = planted_named(r["reasons"], key["planted"][p["set"]])
    return out


def correlations(rows, key, auto, judge):
    """[{score, metric, rho, n}] Spearman of the judge's overall / mean6 against the automatic metrics (auto: {(set, candidate): {metric: v}});
    judge "mean" averages the judges per candidate."""
    per = defaultdict(lambda: defaultdict(list))
    for r in rows:
        p = key["packets"].get(r["code"])
        if r["repeat"] == 1 and p and judge in (r["judge"], "mean"):
            for s in ("overall", "mean6"):
                per[(p["set"], p["candidate"])][s].append(r[s])
    out = []
    for s in ("overall", "mean6"):
        ids = sorted(k for k in per if per[k][s])
        x = [sum(per[k][s]) / len(per[k][s]) for k in ids]
        for m in AUTO:
            y = [(auto.get(k) or {}).get(m) for k in ids]
            out.append({"score": s, "metric": m, "rho": spearman(x, y), "n": sum(v is not None for v in y)})
    return out


def analyse(rows, key, auto=None):
    """All task-11 results as a dict."""
    judges = sorted({r["judge"] for r in rows})
    res = {"judges": judges, "n_answers": len(rows),
           "agreement": {f"{a} vs {b}": judge_agreement(rows, a, b) for a, b in combinations(judges, 2)},
           "self": {j: self_agreement(rows, j) for j in judges},
           "controls": {j: controls(rows, key, j) for j in judges},
           "planted": {j: planted_report(rows, key, j) for j in judges}}
    if auto is not None:
        res["correlations"] = {j: correlations(rows, key, auto, j) for j in judges + (["mean"] if len(judges) > 1 else [])}
    return res


def _num(v):
    return "-" if v is None else f"{v:.3f}"


def to_markdown(res):
    """task11.md text."""
    L = ["# wf_v4 task 11: grading agreement and controls", "", f"{res['n_answers']} answers from {', '.join(res['judges'])}.", ""]
    for title, block in (("Judge agreement (first answers)", res["agreement"]), ("Self-agreement (answer 1 vs repeat)", res["self"])):
        L += [f"## {title}", "", "| pair | item | n | exact | within 1 |", "|---|---|---|---|---|"]
        for who, items in block.items():
            for k, v in items.items():
                L.append(f"| {who} | {k} | {v['n']} | {_num(v['exact'])} | {_num(v.get('within1'))} |")
        L.append("")
    L += ["## Controls (rank by mean of the 6 scores, 1 = best)", "",
          "| judge | set | n | GT rank | d rank | planted rank | GT top | d bottom | planted middle | GT > planted > d |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for j, sets in res["controls"].items():
        for s, c in sorted(sets.items()):
            L.append(f"| {j} | {s} | {c['n']} | {c['gt_rank']} | {c['d_rank']} | {c['planted_rank']} | {c['gt_top']} | {c['d_bottom']} | "
                     f"{c['planted_middle']} | {c['planted_between']} |")
    L += ["", "## Planted errors named in the reasons (merge, foreign key, moved column)", "",
          "| judge | set | merge | fk removed | column moved |", "|---|---|---|---|---|"]
    for j, sets in res["planted"].items():
        for s, v in sorted(sets.items()):
            L.append(f"| {j} | {s} | " + " | ".join("yes" if x else "no" for x in v) + " |")
    if "correlations" in res:
        L += ["", "## Spearman with the automatic scores (pooled over the graded candidates)", "",
              "| judge | score | metric | rho | n |", "|---|---|---|---|---|"]
        for j, cs in res["correlations"].items():
            L += [f"| {j} | {r['score']} | {r['metric']} | {_num(r['rho'])} | {r['n']} |" for r in cs]
    return "\n".join(L) + "\n"
