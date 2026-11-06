"""wf_v4 task 7: list every error of a Step-4 schema against the best-matching GT design, with the step that caused it and whether the
input column was already wrong (Step 3). Pure functions on the scorer's own mapping / resolve / match functions (step4_score.py).

Steps: 4.1 grouping (real column unused, column in wrong table, noise or wrong-entity column placed, duplicate columns in one table not
flagged), 4.3 relationships (missing table, extra table, missing / extra link, wrong direction or kind), 4.4 keys (wrong or missing
primary key, relationship without foreign key, wrong type).

Choices:
- The design is the one `step4_score.score` picks on the full GT (grouping F1, then table F1); the match and the credited new id columns
  are computed exactly as in `score_design`.
- Step-3 error of a handover column (`step3_status`, all columns of the set): it maps to no GT column; its GT column belongs to another
  entity; purity < PURE (0.6); or it is not the largest column among the columns with the same GT label (that one is the original, the
  others are duplicates). New columns (no source) are never a Step-3 error.
- An error about columns is "step3 yes" when any of its source columns is a Step-3 error. A missing table is "yes" when no GT column of
  it is reachable in the set; an extra table when every sourced column in it is a Step-3 error; other table-level errors (links, keys) are "no".
- An unused column is an error only when its GT column is placed nowhere else (a duplicate that is unused is right). A column whose GT
  column is placed correctly elsewhere but is also copied into a wrong table is still listed (marked "copy").
- New id / link columns are not listed as wrong (as in the scorer); their key and link errors show up under 4.4.
"""
from collections import Counter, defaultdict
from itertools import combinations

from . import step4_gt as G
from . import step4_score as S

PURE = G.PURITY
STEPS = ("4.1", "4.3", "4.4")


def step3_status(full, gt_entity):
    """{"<entity>:<id>": reason} for every handover column that is already wrong; correct columns are absent.
    full: step4_gt.map_handover output; gt_entity: {GT column name: entity}."""
    bad, ok = {}, defaultdict(list)
    for cid, m in full.items():
        g = m["gt"]
        if g is None:
            bad[cid] = "maps to no GT column"
        elif gt_entity.get(g) != m["entity"]:
            bad[cid] = f"maps to {g!r} of another entity ({gt_entity.get(g)})"
        elif m["purity"] < PURE:
            bad[cid] = f"purity {m['purity']:.2f} < {PURE}"
        else:
            ok[g].append(cid)
    for g, ids in ok.items():
        keep = sorted(ids, key=lambda i: (-full[i]["n"], i))[0]
        for i in ids:
            if i != keep:
                bad[i] = f"duplicate of {keep} (same GT label {g!r})"
    return bad


def _label(c):
    return f"{c['name']!r} [{c['source']}]" if c["source"] else repr(c["name"])


def list_errors(schema, gt, set_name, mapping, full):
    """Errors of one canonical schema: list of {"step", "kind", "text", "sources", "step3" ("yes"/"no"), "step3_reason"}, plus the
    design name. mapping: step4_score.map_columns output; full: step4_gt.map_handover output of the set (all columns)."""
    res = S.score(schema, gt, set_name, False, mapping)
    design = next(d for d in G.all_designs(gt) if d["name"] == res["design"])
    v = S.view(design, None)
    main = G.main_design(gt)
    gt_entity_all = {c["name"]: t["entity"] for t in main["tables"].values() for c in t["columns"]}
    bad = step3_status(full, gt_entity_all)
    reach = gt["reachable"].get(set_name) or {}
    out = S.resolve(schema, G.gt_names(gt), mapping)
    match = S.match_tables(out, v)
    S.credit_new(out, v, match)
    gt_tab = {c: tn for tn, t in v["tables"].items() for c in t["cols"]}
    gt_col = {c: col for t in v["tables"].values() for c, col in t["cols"].items()}
    errors = []

    def add(step, kind, text, sources=(), s3=None):
        flagged = [s for s in sources if s in bad]
        yes = bool(flagged) if s3 is None else s3
        errors.append({"step": step, "kind": kind, "text": text, "sources": list(sources), "step3": "yes" if yes else "no",
                       "step3_reason": "; ".join(f"{s}: {bad[s]}" for s in flagged)})

    placed = defaultdict(list)                 # GT column -> [(table, column)]
    for t in out["tables"]:
        for c in t["cols"]:
            if c["gt"] in gt_tab:
                placed[c["gt"]].append((t["name"], c))
    # ---- 4.1 grouping
    for u in out["unused"]:
        if u["gt"] in gt_tab and u["gt"] not in placed:
            add("4.1", "real column unused", f"{u['source']} is the GT column {u['gt']!r} ({gt_tab[u['gt']]}) but was left unused",
                [u["source"]])
    for t in out["tables"]:
        for c in t["cols"]:
            if c["new"] and not c["direct"]:
                continue
            src = [c["source"]] if c["source"] else []
            g = c["gt"]
            if g is None:
                add("4.1", "noise column placed", f"{_label(c)} in {t['name']!r} maps to no GT column", src)
            elif g not in gt_tab:
                add("4.1", "noise column placed", f"{_label(c)} in {t['name']!r} maps to {g!r}, which design {design['name']!r} does not have", src)
            elif match.get(t["name"]) != gt_tab[g]:
                right = [o for o, _ in placed[g] if match.get(o) == gt_tab[g]]
                copy = f" (copy; also correctly in {right[0]!r})" if right else ""
                add("4.1", "column in wrong table",
                    f"{_label(c)} is the GT column {g!r} (GT table {gt_tab[g]}) but sits in {t['name']!r}"
                    f" ({'matched to ' + match[t['name']] if t['name'] in match else 'no GT table'}){copy}", src)
        by = defaultdict(list)
        for c in t["cols"]:
            if c["gt"] in gt_tab and c["source"]:
                by[c["gt"]].append(c["source"])
        for g, srcs in by.items():
            for a, b in combinations(srcs, 2):
                if frozenset((a, b)) not in out["flags"]:
                    add("4.1", "duplicate not flagged", f"{a} and {b} are both the GT column {g!r} in {t['name']!r} and not flagged", [a, b])
    # ---- 4.3 relationships
    for tn, t in v["tables"].items():
        if tn not in set(match.values()):
            add("4.3", "missing table", f"GT table {tn!r} ({len(t['cols'])} columns) has no output table", [],
                s3=not any(reach.get(c) == "yes" for c in t["cols"]))
    for t in out["tables"]:
        if t["name"] not in match:
            srcs = [c["source"] for c in t["cols"] if c["source"]]
            add("4.3", "extra table", f"output table {t['name']!r} matches no GT table", srcs, s3=bool(srcs) and all(s in bad for s in srcs))
    soft = S.soft_pairs(gt, v)
    names = {t["name"] for t in out["tables"]}
    fk_rels = [(t["name"], f["ref_table"], "one_to_many") for t in out["tables"] for f in t["fks"]]
    seen, found = set(), set()
    for a, b, kind in out["rels"] + fk_rels:
        key = frozenset((a, b))
        if a == b or a not in names or b not in names or key in seen:
            continue
        seen.add(key)
        if a not in match or b not in match:
            add("4.3", "extra link", f"link {a} -> {b} touches a table that matches no GT table")
            continue
        gk = frozenset((match[a], match[b]))
        if gk in v["hard"]:
            found.add(gk)
            if v["hard"][gk] != match[a]:
                add("4.3", "wrong direction", f"link {a} -> {b}: the GT foreign key is in {v['hard'][gk]!r}, the output puts it in {match[a]!r}")
            if kind != "one_to_many":
                add("4.3", "wrong kind", f"link {a} -> {b} is {kind}, GT is one_to_many")
        elif gk not in soft:
            add("4.3", "extra link", f"link {a} -> {b} (GT tables {match[a]!r}, {match[b]!r}) is not in the GT")
    matched = set(match.values())
    for gk in sorted(v["hard"], key=lambda k: sorted(k)):
        if gk not in found and gk <= matched:
            add("4.3", "missing link", f"GT link {' - '.join(sorted(gk))} (foreign key in {v['hard'][gk]!r}) is missing")
    # ---- 4.4 keys and types
    colmap = {t["name"]: {c["name"]: c["gt"] for c in t["cols"]} for t in out["tables"]}
    for t in out["tables"]:
        o = t["name"]
        if o not in match:
            continue
        want = set(v["tables"][match[o]]["pk"])
        if not t["pk"]:
            add("4.4", "missing primary key", f"{o!r} (GT {match[o]!r}) has no primary key, GT has {sorted(want)}")
        elif {colmap[o].get(k) for k in t["pk"]} != want:
            add("4.4", "wrong primary key", f"{o!r} (GT {match[o]!r}) has primary key {t['pk']}, GT has {sorted(want)}",
                [c["source"] for c in t["cols"] if c["name"] in t["pk"] and c["source"]])
    for gk in sorted(found, key=lambda k: sorted(k)):
        ms = {o for o, g in match.items() if g in gk}
        has = any(f["ref_table"] in ms and t["name"] in ms for t in out["tables"] for f in t["fks"])
        if not has:
            add("4.4", "missing foreign key", f"link {' - '.join(sorted(gk))} is a relationship but no table has a foreign key for it")
    for t in out["tables"]:
        for c in t["cols"]:
            if c["gt"] in gt_col and not c["credited"] and gt_col[c["gt"]]["type"] in S.TYPE_OK and c["type"] is not None \
                    and c["type"] not in S.TYPE_OK[gt_col[c["gt"]]["type"]]:
                add("4.4", "wrong type", f"{_label(c)} in {t['name']!r} is {c['type']}, GT {c['gt']!r} is {gt_col[c['gt']]['type']}",
                    [c["source"]] if c["source"] else [])
    return {"design": design["name"], "errors": errors}


def count_table(errors):
    """{step: {"yes": n, "no": n, "all": n}} over STEPS, plus "all"."""
    c = Counter((e["step"], e["step3"]) for e in errors)
    rows = {s: {"yes": c[(s, "yes")], "no": c[(s, "no")]} for s in STEPS}
    rows["all"] = {k: sum(r[k] for r in rows.values()) for k in ("yes", "no")}
    for r in rows.values():
        r["all"] = r["yes"] + r["no"]
    return rows


def to_markdown(runs):
    """runs: {run name: {"design", "errors"}} -> markdown (one list per run and a count table)."""
    lines = ["# Step-4 errors on dev50 (full GT, best-matching design)", "",
             "Step 3 yes = the input column was already wrong (maps to no GT column, another entity, purity < 0.6, or a duplicate of a larger"
             " column with the same GT label).", ""]
    for run, r in runs.items():
        lines += [f"## {run} (design {r['design']}, {len(r['errors'])} errors)", ""]
        for i, e in enumerate(r["errors"], 1):
            tag = f" [Step 3: {e['step3_reason']}]" if e["step3"] == "yes" and e["step3_reason"] else " [Step 3: yes]" if e["step3"] == "yes" else ""
            lines.append(f"{i}. {e['step']} {e['kind']}: {e['text']}{tag}")
        lines.append("")
    lines += ["## Counts by step and by Step-3 error of the input column", "", "| run | step | Step 3 yes | Step 3 no | all |", "|---|---|---|---|---|"]
    for run, r in runs.items():
        for s, row in count_table(r["errors"]).items():
            lines.append(f"| {run} | {s} | {row['yes']} | {row['no']} | {row['all']} |")
    return "\n".join(lines) + "\n"
