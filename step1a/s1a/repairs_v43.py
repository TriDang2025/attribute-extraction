"""wf_v4.3 U5: every repair the Step 4 assembler makes to the model answers, by type, replayed on the cached answers.

Where the repairs happen (all in code that runs after the model, none in the prompts):
- keyed_v42.unkey / _unique_names: a repeated 4.2 table name is renamed to <name>_<group> ("name_renamed", counted by keyed_v42.renamed_42).
- batch_v4.repair_41: unknown / repeated columns dropped, columns the model left out put into `unused` (typed below).
- batch_v4.repair_43: relationships / new tables that name unknown tables, relate a table to itself or repeat are dropped (typed below).
- batch_v4.repair_44: five kinds, counted by the function itself.
Events that are not repairs of the text but change which answer is used (read from the cached rows): "unguided_retry" (VllmBackend reran a
guided answer with parse errors unguided and kept the better row), "unguided_job" (guided decoding failed, the job ran unguided),
"cut_off" (finish_reason "length").

`typed_41` / `typed_43` redo repair_41 / repair_43 with one counter per type and a switch per type; their total and their output with no
switch off equal the frozen functions (replay_typed checks it and reports a mismatch as the error "count mismatch"). Nothing here edits an
existing module. The same report works for v4.3 chains: `side_by_side` reads results/wf_v43/u4/**/repairs.json (log_v43.RepairLog.save).
"""
import json
import re
from collections import Counter
from pathlib import Path

from . import batch_v4 as B
from . import keyed_v42 as K
from . import step4_prompts as SP
from .log_v43 import RepairLog

TYPES_41 = ("col_unknown", "col_twice", "unused_bad", "col_unplaced")
TYPES_43 = ("new_table_invalid", "rel_unknown_table", "rel_self", "rel_repeat")
TYPES_44 = ("key_listed", "dup_listed", "col_missing", "fk_col_added", "fk_ref_to_pk")
TYPE_STEP = {**{t: "4.1" for t in TYPES_41}, "name_renamed": "4.2", **{t: "4.3" for t in TYPES_43}, **{t: "4.4" for t in TYPES_44},
             "unguided_retry": "event", "unguided_job": "event", "cut_off": "event"}
ALL_TYPES = tuple(TYPE_STEP)


# ---------------------------------------------------------------- typed copies of repair_41 / repair_43
def _note(log, kind, where, item):
    if log is not None:
        log.add(kind, where, item if isinstance(item, str) else json.dumps(item, ensure_ascii=False))


def typed_41(a41, cols, off=(), log=None):
    """(a41 fixed, Counter by TYPES_41): batch_v4.repair_41 with a counter per type; a type in `off` is not repaired. `log` (RepairLog)
    gets one add(kind, where, detail) per repair."""
    ids = [c["id"] for c in cols]
    n, seen, used, groups, unused = Counter(), set(), set(), [], []
    for g in a41.get("groups", []):
        keep = []
        for c in g.get("columns", []):
            if c in ids and c not in seen:
                keep.append(c)
                seen.add(c)
            else:
                kind = "col_unknown" if c not in ids else "col_twice"
                n[kind] += 1
                _note(log, kind, g.get("group"), c)
                if kind in off:
                    keep.append(c)
        if keep:
            groups.append({**g, "columns": keep})
    for u in a41.get("unused", []):
        c = u.get("column")
        if c in ids and c not in seen and c not in used:
            unused.append(u)
            used.add(c)
        else:
            n["unused_bad"] += 1
            _note(log, "unused_bad", "unused", c)
            if "unused_bad" in off:
                unused.append(u)
    for c in ids:
        if c not in seen and c not in used:
            n["col_unplaced"] += 1
            _note(log, "col_unplaced", "unused", c)
            if "col_unplaced" not in off:
                unused.append({"column": c, "reason": "not placed by the model"})
    return {**a41, "groups": groups, "unused": unused}, n


def typed_43(a43, a41, a42, off=(), log=None):
    """(a43 fixed, Counter by TYPES_43): batch_v4.repair_43 with a counter per type; a type in `off` is not repaired (`log`: as typed_41)."""
    old = {t["name"] for t in SP.named_tables(a41, a42)}
    new, n = [], Counter()
    for t in a43.get("new_tables", []):
        b = t.get("between", [])
        if str(t.get("name") or "").strip() and t["name"] not in old and t["name"] not in {x["name"] for x in new} \
                and len(b) == 2 and len(set(b)) == 2 and all(x in old for x in b):
            new.append(t)
        else:
            n["new_table_invalid"] += 1
            _note(log, "new_table_invalid", "new_tables", t)
            if "new_table_invalid" in off:
                new.append(t)
    names, rels, seen = old | {t["name"] for t in new}, [], set()
    for r in a43.get("relationships", []):
        key = (r.get("from"), r.get("to"), r.get("kind"))
        if r.get("from") not in names or r.get("to") not in names:
            kind = "rel_unknown_table"
        elif r["from"] == r["to"]:
            kind = "rel_self"
        elif key in seen:
            kind = "rel_repeat"
        else:
            rels.append(r)
            seen.add(key)
            continue
        n[kind] += 1
        _note(log, kind, "relationships", r)
        if kind in off:
            rels.append(r)
    return {**a43, "relationships": rels, "new_tables": new}, n


# ---------------------------------------------------------------- 4.2 renames
def raw_42_tables(raw):
    """4.2 tables of a keyed answer as unkey would list them, without the renaming (None for a cut-off / list-form answer)."""
    obj = K._load(raw)
    tables = obj.get("tables") if obj else None
    return [{"group": g, **v} for g, v in tables.items()] if isinstance(tables, dict) else None


# ---------------------------------------------------------------- replay
def replay_typed(out, chain, root, off=(), upto=4, strict=True, log=None):
    """Like batch_v4.replay, with typed repair counts and switches. off: set of type names (ALL_TYPES) or "all_44" (no 4.4 repair at all)
    that are not repaired. Returns {"ans", "counts" Counter, "error", "cols", "ignored"}; the first failing call stops the replay. With off
    empty the answers equal batch_v4.replay's. strict=False: validator errors are collected in "ignored" and the replay goes on (a missing
    or unparsable answer still stops it). `log`: RepairLog that receives the 4.1 / 4.3 repairs with their items."""
    cols = B.chain_columns(chain, root)
    ans, counts, err, ignored = {}, Counter(), None, []
    for step in range(1, upto + 1):
        row = B.last_row(Path(out) / "responses" / f"{chain['id']}_4{step}.jsonl")
        if row is None:
            err = f"4.{step}: no response"
        elif row["errors"]:
            err = f"4.{step}: parse errors {row['errors'][:2]}"
        if err:
            break
        a, errs = row["parsed"], []
        if step == 1:
            a, n = typed_41(a, cols, off, log)
            errs = SP.validate_41(a, cols)
        elif step == 2:
            nr = K.renamed_42(row["raw"])
            n = Counter({"name_renamed": nr} if nr else {})
            if nr and "name_renamed" in off:
                a = {**a, "tables": raw_42_tables(row["raw"])}
            errs = SP.validate_42(a, ans["41"])
        elif step == 3:
            a, n = typed_43(a, ans["41"], ans["42"], off, log)
            errs = SP.validate_43(a, ans["41"], ans["42"])
        else:
            if "all_44" in off:
                n = Counter()
            else:
                a, kinds = B.repair_44(a, ans["41"], ans["42"], ans["43"], cols)
                n = Counter({k: v for k, v in kinds.items() if v})
            errs = SP.validate_44(a, ans["41"], ans["42"], ans["43"], cols, strict=False)
        counts.update(n)
        if errs and strict:
            err = f"4.{step}: {len(errs)} validation errors, e.g. {errs[:2]}"
            break
        ignored += errs
        ans[f"4{step}"] = a
    return {"ans": ans, "counts": counts, "error": err, "cols": cols, "ignored": ignored}


def check_against_frozen(out, chain, root):
    """True if the typed replay (nothing off) gives the same answers, error and repair total as batch_v4.replay."""
    t = replay_typed(out, chain, root)
    ans, rep, err, _ = B.replay(out, chain, 4, root)
    renamed = t["counts"].get("name_renamed", 0)
    return t["ans"] == ans and t["error"] == err and sum(t["counts"].values()) - renamed == rep


def events(out, chain):
    """Counter of the non-text events of a chain's cached rows (TYPE_STEP "event" types)."""
    n = Counter()
    for step in range(1, 5):
        row = B.last_row(Path(out) / "responses" / f"{chain['id']}_4{step}.jsonl")
        if row is None:
            continue
        n["unguided_retry"] += bool(row.get("retried"))
        n["unguided_job"] += row.get("guided") is False
        n["cut_off"] += row.get("finish_reason") == "length"
    return Counter({k: v for k, v in n.items() if v})


def chain_repairs(out, chain, root):
    """Typed repair counts + events of one chain over all four calls, as a RepairLog; plus its status {"error", "reached"}."""
    t = replay_typed(out, chain, root)
    log = RepairLog()
    for k, v in {**t["counts"], **events(out, chain)}.items():
        for _ in range(v):
            log.add(k, chain["id"])
    return log, {"error": t["error"], "reached": len(t["ans"])}


# ---------------------------------------------------------------- ablation
def ablate(out, chain, root, off, score, strict=True):
    """Replay with the repair types `off` not repaired. strict=True: the validators stay on, so ok is False when the unrepaired answer
    fails one (the repair cannot be undone cleanly); strict=False: the validators are ignored and only a failing assembly gives ok False.
    Else scores = score(canonical, chain), a list of score dicts (full and reachable GT). "ignored" = validator errors let through."""
    t = replay_typed(out, chain, root, off, strict=strict)
    res = {"off": "+".join(sorted(off)), "ok": False, "error": t["error"], "scores": [], "ignored": len(t["ignored"])}
    if t["error"]:
        return res
    try:
        canonical = B.assemble_chain(t["ans"], t["cols"])
    except Exception as e:  # noqa: BLE001 - any assembly failure means the unrepaired answer is unusable
        res["error"] = f"assemble: {type(e).__name__} {str(e)[:120]}"
        return res
    return {**res, "ok": True, "scores": score(canonical, chain)}


# ---------------------------------------------------------------- v4.3 side by side
def load_repairs(root):
    """{run name: counts dict} from every repairs.json (RepairLog.save) under `root` (run name = its parent folder, relative to root)."""
    root, found = Path(root), {}
    for p in sorted(root.glob("**/repairs.json")):
        found[p.parent.relative_to(root).as_posix() or "."] = RepairLog.load(p).counts
    return found


def side_by_side(old, new):
    """Rows {type, step, old, new} over the union of the types of two {run: counts} dicts (counts summed over the runs of a side), plus a
    total row. Types that neither side has are left out; the step of an unknown type is "?"."""
    so, sn = Counter(), Counter()
    for c in old.values():
        so.update(c)
    for c in new.values():
        sn.update(c)
    kinds = sorted(set(so) | set(sn), key=lambda k: (ALL_TYPES.index(k) if k in ALL_TYPES else len(ALL_TYPES), k))
    rows = [{"type": k, "step": TYPE_STEP.get(k, "?"), "old": so.get(k, 0), "new": sn.get(k, 0)} for k in kinds]
    return rows + [{"type": "total", "step": "", "old": sum(so.values()), "new": sum(sn.values())}]


def snippet(raw, needle, width=160, nth=0):
    """Raw text around the nth match (0 first, -1 last) of `needle` (a plain string), whitespace collapsed; "" if absent."""
    ms = list(re.finditer(re.escape(needle), raw or ""))
    if not ms:
        return ""
    m = ms[nth]
    s = re.sub(r"\s+", " ", raw[max(0, m.start() - width // 2): m.end() + width // 2])
    return s
