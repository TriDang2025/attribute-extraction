"""wf_v4 Step 4 scorer (diary tasks 6-7): score a canonical schema JSON against the GT designs of s1a/step4_gt.py. No LLM, no models.

Flow: map_columns (handover column -> GT column by majority gt_L2) -> resolve the output columns -> for every acceptable GT design
(8: booking tables split or folded into the place table, see step4_gt) -> match_tables -> metrics; keep the design with the best
(grouping F1, then table F1; ties: the first design = main). reachable_only drops the GT columns that no handover column can reach
(reachable status of the set in gt["reachable"][set]) and the GT tables left without a reachable column; the output columns that map
to a dropped GT column are removed from the output as neutral, and an output table whose mapped columns are all dropped goes with them.

Choices:
- Mapping: the most common gt_L2 over ALL mentions of the handover column (an empty gt_L2 is a label of its own; if it is the top label the
  column is unmapped = None), plurality, min_purity default 0.0 (purity and n are reported); names are normalised by case and spaces.
  A column with a `gt` field uses it (purity 1). Unknown names map to None.
- Table matching: one-to-one, greedy by the number of distinct GT columns an output table shares with a GT table (most first; ties by output
  table name, then GT table name); only pairs with at least one shared column.
- New id/link columns (new true, no `gt`): after matching, a new column in the output PK takes the GT PK of the matched GT table, a new
  column in an output FK takes a free added foreign-key column of it (if free). Others stay unmatched (counted as `new_unmatched`, not
  wrong). Credited new columns are not scored for type.
- Types: TYPE_OK below; GT "unknown" is not scored.
- Relationships: output pairs = relationships plus foreign keys, unordered, deduplicated; a pair is correct if its matched GT tables are a
  hard link or a soft link of the design (soft links are never required). Recall is over hard links only. Direction and kind are judged on
  matched hard links only (GT kind is one_to_many, from = the table holding the FK).
- Hard links in the reachable-only GT stay when both tables stay, even if the FK column itself is not reachable.
"""

from collections import Counter, defaultdict
from itertools import combinations

from .step4_gt import all_designs, gt_names, map_handover, norm

TYPE_OK = {"time": {"time"}, "day": {"day", "text"}, "text": {"text"}, "duration": {"duration", "integer", "decimal"},
           "price": {"price", "decimal", "text"}, "id": {"id", "text"}, "number": {"integer", "decimal"}}


def share(k, n):
    return {"k": k, "n": n, "share": k / n if n else None}


def f1(p, r):
    p, r = (p or 0.0), (r or 0.0)
    return 2 * p * r / (p + r) if p + r else 0.0


def map_columns(schema, set_name, handover_dir, gt_levels, gt=None, min_purity=0.0):
    """{source: {"gt", "purity", "n", "entity"}} for every output column and unused entry with a Step-3 source ("<entity>:<id>").
    Columns whose majority label is below min_purity map to None. A `gt` field is not handled here (resolve uses it first)."""
    names = gt_names(gt) if gt else None
    full = map_handover(handover_dir, set_name, gt_levels, names)
    wanted = {c["source"] for t in schema["tables"] for c in t["columns"] if c.get("source")} | {u["source"] for u in schema.get("unused", [])}
    out = {}
    for s in wanted:
        m = dict(full.get(s) or {"gt": None, "purity": 0.0, "n": 0, "entity": s.split(":")[0]})
        if m["purity"] < min_purity:
            m["gt"] = None
        out[s] = m
    return out


# ---- output side

def resolve(schema, names, mapping):
    """Output tables with a GT name per column: {"name","cols":[{name,type,gt,new,direct,source,purity,n}],"pk","fks","unused"}."""
    def lookup(c):
        if c.get("gt"):
            return names.get(norm(c["gt"])), 1.0, None, True
        m = (mapping or {}).get(c.get("source")) if c.get("source") else None
        if m and m["gt"]:
            return names.get(norm(m["gt"])), m["purity"], m["n"], False
        return None, (m or {}).get("purity", 0.0), (m or {}).get("n", 0), False

    tables = []
    for t in schema["tables"]:
        cols = []
        for c in t["columns"]:
            g, p, n, direct = lookup(c)
            cols.append({"name": c["name"], "type": c.get("type"), "gt": g, "new": bool(c.get("new")), "direct": direct,
                         "source": c.get("source"), "purity": p, "n": n, "credited": False})
        tables.append({"name": t["name"], "cols": cols, "pk": list(t.get("primary_key") or []),
                       "fks": [dict(f) for f in t.get("foreign_keys") or []]})
    unused = [{"source": u["source"], "gt": lookup(u)[0]} for u in schema.get("unused", [])]
    rels = [(r["from"], r["to"], r.get("kind", "one_to_many")) for r in schema.get("relationships", [])]
    flags = {frozenset((d["source"], d["duplicate_of"])) for d in schema.get("duplicate_flags", [])}
    return {"tables": tables, "unused": unused, "rels": rels, "flags": flags}


def drop_neutral(out, keep):
    """Reachable-only: remove mapped columns whose GT column is not in `keep` (set of kept GT names), unmapped output tables
    stay; a table whose mapped columns are all removed is removed with its relationships."""
    tables, gone = [], set()
    for t in out["tables"]:
        mapped = [c for c in t["cols"] if c["gt"]]
        kept = [c for c in t["cols"] if not c["gt"] or c["gt"] in keep]
        if mapped and not any(c["gt"] in keep for c in mapped):
            gone.add(t["name"])
            continue
        tables.append({**t, "cols": kept})
    return {"tables": tables, "unused": [u for u in out["unused"] if not u["gt"] or u["gt"] in keep],
            "rels": [r for r in out["rels"] if r[0] not in gone and r[1] not in gone], "flags": out["flags"]}


# ---- GT side

def view(design, reach):
    """GT view of a design: tables {name: {entity, cols {name: col}, pk}}, hard links {frozenset: from table}, soft pairs.
    reach: {gt column: yes|no} or None (full GT)."""
    tables = {}
    for tn, t in design["tables"].items():
        cols = {c["name"]: c for c in t["columns"] if reach is None or reach.get(c["name"]) == "yes"}
        if reach is None or any(reach.get(c["name"]) == "yes" for c in t["columns"]):
            tables[tn] = {"entity": t["entity"], "cols": cols, "pk": list(t["primary_key"])}
    hard = {frozenset((f["table"], f["ref_table"])): f["table"] for f in design["foreign_keys"]
            if f["table"] in tables and f["ref_table"] in tables}
    return {"tables": tables, "hard": hard, "design": design["name"]}


def soft_pairs(gt, v):
    return {frozenset((s["from_table"], t)) for s in gt["soft_links"] for t, _ in s["to"]
            if s["from_table"] in v["tables"] and t in v["tables"]}


def match_tables(out, v):
    """{output table: GT table}, one-to-one, greedy by shared distinct GT columns (see module doc)."""
    gt_of = {c: tn for tn, t in v["tables"].items() for c in t["cols"]}
    counts = []
    for t in out["tables"]:
        cnt = Counter(gt_of[g] for g in {c["gt"] for c in t["cols"] if c["gt"] in gt_of})
        counts += [(-k, t["name"], tn) for tn, k in cnt.items()]
    match, used = {}, set()
    for _, o, tn in sorted(counts):
        if o not in match and tn not in used:
            match[o] = tn
            used.add(tn)
    return match


def credit_new(out, v, match):
    """Give each new id/link column of a matched table the GT column it stands for (see module doc)."""
    for t in out["tables"]:
        tn = match.get(t["name"])
        if tn is None:
            continue
        gt = v["tables"][tn]
        free = [c for c in gt["cols"] if c not in {x["gt"] for x in t["cols"] if x["gt"]}]
        fk_cols = {c for f in t["fks"] for c in f["columns"]}
        for c in t["cols"]:
            if not c["new"] or c["gt"] or c["type"] != "id":
                continue
            if c["name"] in t["pk"]:
                cand = [g for g in gt["pk"] if g in free]
            elif c["name"] in fk_cols:
                cand = [g for g in free if gt["cols"][g]["source"] == "added" and gt["cols"][g]["role"] == "foreign_key"]
            else:
                cand = []
            if cand:
                c["gt"], c["credited"] = cand[0], True
                free.remove(cand[0])


def _pairs(items, key):
    return {frozenset(p) for p in combinations(sorted(items), 2) if key[p[0]] == key[p[1]]}


def grouping(items, out_t, gt_t):
    """(precision share, recall share, F1) over the items = GT columns present in output and GT."""
    po, pg = _pairs(items, out_t), _pairs(items, gt_t)
    tp = len(po & pg)
    p, r = share(tp, len(po)), share(tp, len(pg))
    f = None if p["share"] is None and r["share"] is None else f1(p["share"], r["share"])
    return p, r, f


def score_design(out, gt, v):
    """Metrics dict of an (already neutral-cleaned) output against one GT view."""
    tables = out["tables"]
    match = match_tables(out, v)
    credit_new(out, v, match)
    gt_tab = {c: tn for tn, t in v["tables"].items() for c in t["cols"]}
    gt_col = {c: col for t in v["tables"].values() for c, col in t["cols"].items()}
    gt_ent = {c: v["tables"][tn]["entity"] for c, tn in gt_tab.items()}
    m = {}
    n_m = len(match)
    m["table_recall"], m["table_precision"] = share(n_m, len(v["tables"])), share(n_m, len(tables))
    m["table_f1"] = f1(m["table_recall"]["share"], m["table_precision"]["share"])
    # items: GT column -> chosen output table
    where = defaultdict(list)
    for t in tables:
        for c in t["cols"]:
            if c["gt"] in gt_tab:
                where[c["gt"]].append(t["name"])
    chosen = {g: sorted(ts, key=lambda o: (match.get(o) != gt_tab[g], o))[0] for g, ts in where.items()}
    m["placement"] = share(sum(match.get(o) == gt_tab[g] for g, o in chosen.items()), len(chosen))
    m["gt_columns_placed"] = share(len(chosen), len(gt_tab))  # wf_v4.1 task 7: report next to grouping F1
    m["grouping_precision"], m["grouping_recall"], m["grouping_f1"] = grouping(list(chosen), chosen, gt_tab)
    # primary keys: rule (a) = PK maps to the GT PK; rule (b) = (a), or the PK is one new id and every GT PK column is in the table
    colmap = {t["name"]: {c["name"]: c["gt"] for c in t["cols"]} for t in tables}
    right = right_b = 0
    for t in tables:
        o = t["name"]
        if o not in match or not t["pk"]:
            continue
        want = set(v["tables"][match[o]]["pk"])
        ok = {colmap[o].get(k) for k in t["pk"]} == want
        cols = {c["name"]: c for c in t["cols"]}
        new_id = len(t["pk"]) == 1 and t["pk"][0] in cols and cols[t["pk"][0]]["new"] and not cols[t["pk"][0]]["direct"] \
            and cols[t["pk"][0]]["type"] == "id"
        right += ok
        right_b += ok or (new_id and want <= set(colmap[o].values()))
    m["pk_right"] = share(right, n_m)
    m["pk_right_b"] = share(right_b, n_m)
    # relationships
    soft = soft_pairs(gt, v)
    seen, outpairs = set(), []
    fk_rels = [(t["name"], f["ref_table"], "one_to_many") for t in tables for f in t["fks"]]
    names = {t["name"] for t in tables}
    for a, b, kind in out["rels"] + fk_rels:
        key = frozenset((a, b))
        if a != b and a in names and b in names and key not in seen:
            seen.add(key)
            outpairs.append((a, b, kind))
    ok, found, direction, kinds = 0, set(), 0, 0
    for a, b, kind in outpairs:
        if a in match and b in match:
            key = frozenset((match[a], match[b]))
            ok += key in v["hard"] or key in soft
            if key in v["hard"]:
                found.add(key)
                direction += v["hard"][key] == match[a]
                kinds += kind == "one_to_many"
    m["rel_precision"], m["rel_recall"] = share(ok, len(outpairs)), share(len(found), len(v["hard"]))
    m["rel_direction"], m["rel_kind"] = share(direction, len(found)), share(kinds, len(found))
    # types, wrong columns, new columns
    scored = [c for t in tables for c in t["cols"] if c["gt"] in gt_col and not c["credited"] and gt_col[c["gt"]]["type"] in TYPE_OK
              and c["type"] is not None]
    m["types_right"] = share(sum(c["type"] in TYPE_OK[gt_col[c["gt"]]["type"]] for c in scored), len(scored))
    wrong = real = 0
    for t in tables:
        ent = v["tables"][match[t["name"]]]["entity"] if t["name"] in match else None
        if ent is None:
            cnt = Counter(gt_ent[c["gt"]] for c in t["cols"] if c["gt"] in gt_ent)
            ent = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if cnt else None
        for c in t["cols"]:
            if c["new"] and not c["direct"]:
                continue
            real += 1
            wrong += c["gt"] not in gt_ent or gt_ent[c["gt"]] != ent
    m["wrong_columns"] = share(wrong, real)
    newc = [c for t in tables for c in t["cols"] if c["new"] and not c["direct"]]
    m["new_unmatched"] = share(sum(not c["credited"] for c in newc), len(newc))
    # unused and duplicates
    covered = set(chosen)
    un = out["unused"]
    m["unused_real"] = share(sum(u["gt"] in gt_tab for u in un), len(un))
    m["unused_real_uncovered"] = share(sum(u["gt"] in gt_tab and u["gt"] not in covered for u in un), len(un))
    dup_pairs, flagged = 0, 0
    for t in tables:
        by = defaultdict(list)
        for c in t["cols"]:
            if c["gt"] in gt_tab and c["source"]:
                by[c["gt"]].append(c["source"])
        for srcs in by.values():
            for a, b in combinations(srcs, 2):
                dup_pairs += 1
                flagged += frozenset((a, b)) in out["flags"]
    m["duplicates"] = share(flagged, dup_pairs)  # k = flagged pairs, n = duplicate pairs
    m["match"] = match
    return m


def score(schema, gt, set_name, reachable_only=False, mapping=None):
    """Score against every acceptable design and keep the best (grouping F1, then table F1). Returns {"design", "reachable_only",
    "set", "metrics": {...}}; every share is {k, n, share}. mapping: output of map_columns (needed when columns have sources)."""
    names = gt_names(gt)
    out = resolve(schema, names, mapping)
    reach = None
    if reachable_only:
        reach = gt["reachable"].get(set_name)
        if reach is None:
            raise ValueError(f"no reachability attached for set {set_name!r} (step4_gt.attach_reachable)")
        out = drop_neutral(out, {c for c, s in reach.items() if s == "yes"})
    best = None
    for d in all_designs(gt):
        res = score_design(_copy(out), gt, view(d, reach))
        key = (res["grouping_f1"] or 0.0, res["table_f1"])
        if best is None or key > best[0]:
            best = (key, d["name"], res)
    return {"set": set_name, "reachable_only": reachable_only, "design": best[1], "metrics": best[2]}


def _copy(out):
    return {"tables": [{**t, "cols": [dict(c) for c in t["cols"]], "fks": [dict(f) for f in t["fks"]]} for t in out["tables"]],
            "unused": out["unused"], "rels": out["rels"], "flags": out["flags"]}


def flat(result):
    """Flat dict for a CSV row: share metrics as <name>_k, <name>_n, <name>; floats as is; the table match as text."""
    row = {"set": result["set"], "reachable_only": result["reachable_only"], "design": result["design"]}
    for k, v in result["metrics"].items():
        if k == "match":
            row["match"] = ";".join(f"{o}={g}" for o, g in sorted(v.items()))
        elif isinstance(v, dict):
            row[f"{k}_k"], row[f"{k}_n"], row[k] = v["k"], v["n"], v["share"]
        else:
            row[k] = v
    return row


# ---- stability

def _groups(schema, names, mapping):
    out = resolve(schema, names, mapping)
    g = {}
    for t in sorted(out["tables"], key=lambda t: t["name"]):
        for c in t["cols"]:
            if c["gt"]:
                g.setdefault(c["gt"], t["name"])
    return g


def stability(schemas, mapping=None, gt=None):
    """Mean pairwise grouping F1 between runs over the GT columns mapped in both (2 * tp / (pairs in a + pairs in b), the F1 of one
    grouping against the other). mapping: one map_columns dict for all runs or a list of dicts. Returns {"mean", "pairs", "n_runs"};
    mean None when no pair of runs shares two mapped columns."""
    names = gt_names(gt) if gt else {}
    maps = mapping if isinstance(mapping, list) else [mapping] * len(schemas)
    groups = [_groups(s, names or _identity(s), m) for s, m in zip(schemas, maps)]
    vals = []
    for a, b in combinations(groups, 2):
        common = sorted(set(a) & set(b))
        pa, pb = _pairs(common, a), _pairs(common, b)
        if pa or pb:
            vals.append(2 * len(pa & pb) / (len(pa) + len(pb)))
    return {"mean": sum(vals) / len(vals) if vals else None, "pairs": len(vals), "n_runs": len(schemas)}


def _identity(schema):
    """Names of the columns that carry a gt field (when no GT is given)."""
    return {norm(c["gt"]): c["gt"] for t in schema["tables"] for c in t["columns"] if c.get("gt")}


# ---- placement into an existing schema (diary task 13)

def placement_vs_gt(schemas, answers, attributes, gt, set_name, handover_dir, gt_levels):
    """One row per held-out attribute: the chosen option and table against the expected ones. `attributes`: [{"gt": GT column name,
    "kind": expected option P1..P5, "columns": [Step-3 column ids of the attribute]}]; `schemas[i]` = canonical schema right after
    attribute i was placed; `answers[i]` = its parsed placement answer (None when the call failed). Expected option = the config kind;
    expected table = the GT table of the attribute (main design). table_ok: the output table that holds the column is matched
    (match_tables, whole GT) to the attribute's GT table in at least one acceptable design (a booking column in the place table counts)."""
    names = gt_names(gt)
    rows = []
    for attr, schema, ans in zip(attributes, schemas, answers):
        mapping = map_columns(schema, set_name, handover_dir, gt_levels, gt)
        out = resolve(schema, names, mapping)
        holder = next((t["name"] for t in schema["tables"] for c in t["columns"] if c.get("source") in attr["columns"]), None)
        expected, ok_designs = None, 0
        for i, d in enumerate(all_designs(gt)):
            v = view(d, None)
            want = next((tn for tn, t in v["tables"].items() if attr["gt"] in t["cols"]), None)
            if i == 0:
                expected = want
            ok_designs += want is not None and holder is not None and match_tables(out, v).get(holder) == want
        rows.append({"gt": attr["gt"], "expected_option": attr["kind"], "option": (ans or {}).get("option"),
                     "option_ok": bool(ans) and ans.get("option") == attr["kind"], "expected_table": expected, "table": holder,
                     "table_ok": ok_designs > 0})
    return rows
