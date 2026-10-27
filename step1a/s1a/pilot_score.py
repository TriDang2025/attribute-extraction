"""Step-3 pilot scores (LOOP1_CONTRACT.md, T5 eval): the section 2.10 checks of one response file against its
initial target, name_check.csv, and the scores.md tables across response files.

`score_file` returns {measure: value} and {measure + "_n": count}; `CHECKS` holds every measure with its block,
text and target. Purity and recall come from s1a.recall (`_recall()` is the only place it is imported, so
tests can swap it).
"""

import json
import re
from collections import Counter
from itertools import product
from types import SimpleNamespace

import numpy as np
import pandas as pd

from . import mentions as _mentions  # noqa: F401  (puts scripts/ on sys.path)
from . import pilot_verify as PV
from .labels import _classes
from v21_run import one_to_one  # noqa: E402

# (key, block, text, target kind, target value); kind ">=" / "<=" / "" (report only) / "after>=before"
CHECKS = [
    ("merge_pure", "Merges", "Merge groups whose gold-labelled clusters share one gold_attr", ">=", 0.8),
    ("merge_frag", "Merges", "Same-class fragment pairs that were merged", ">=", 0.6),
    ("split_done", "Splits", "Mixed {departure, destination} / {leave at, arrive by} clusters that were split", ">=", 1.0),
    ("split_side", "Splits", "Example mentions on the right side of a split", ">=", 0.7),
    ("noise_marked", "Noise", "Noise clusters marked not_attribute/unsure", ">=", 0.7),
    ("noise_kept", "Noise", "Noise clusters given keep + a name (count)", "<=", 2),
    ("place_right", "Placement", "Clusters placed in the right entity", ">=", 0.8),
    ("recall_after", "Train attributes", "Strict recall over train gold classes, after (before in the note)", "after>=before", None),
    ("recall_after_kept", "Train attributes", "Same, marked attributes removed", "", None),
    ("p1_after", "Train attributes", "One-to-one precision after", ">=", 0.6),
    ("sugg_right", "Suggestions", "Followed merge hints that were right (report only)", "", None),
    ("j_right", "Verification", "Mean Jaccard of right names", "", None),
    ("j_wrong", "Verification", "Mean Jaccard of wrong names", "", None),
]
SPLIT_KINDS = ({"departure", "destination"}, {"leave at", "arrive by"})
SPLIT_MIN_SIZE, SPLIT_MIN_SECOND = 8, 0.25  # a split target: >= k examples' worth of members, second class >= 25%
STOP = {"the", "of", "a", "an", "at", "by", "to", "for", "in", "and"}
YES, NO = {"1", "y", "yes", "true", "right"}, {"0", "n", "no", "false", "wrong"}
NAME_COLS = ["variant", "run_tag", "attr_id", "name", "majority_gold_attr", "auto_right", "manual", "right"]


def _recall():
    from . import recall
    return recall


def _ratio(num, den):
    return (num / den if den else float("nan")), den


def mode(values):
    values = [v for v in values if v]
    return Counter(values).most_common(1)[0][0] if values else ""


def train_attrs(gold_values, attrs, entity_gold="train"):
    """Gold classes whose gold entity (mode of entity_gold) is entity_gold."""
    ent = {}
    for _, r in gold_values.iterrows():
        for c in _classes(r["gold_attr"]):
            ent.setdefault(c, []).append(r["entity_gold"])
    return [a for a in attrs if mode(ent.get(a, [])) == entity_gold]


def merge_hints(mentions, ids, x, entity, k=3):
    """{cluster_id: [k nearest other clusters of the entity by centroid cosine]}."""
    idx = {int(i): n for n, i in enumerate(ids)}
    pm = mentions[(mentions["entity"] == entity) & (mentions["cluster_id"] != "")]
    cen = {}
    for cid, g in pm.groupby("cluster_id"):
        c = x[[idx[int(i)] for i in g["mention_id"]]].mean(axis=0)
        cen[cid] = c / max(np.linalg.norm(c), 1e-9)
    names = sorted(cen)
    sim = np.stack([cen[c] for c in names]) @ np.stack([cen[c] for c in names]).T
    out = {}
    for i, c in enumerate(names):
        order = [names[j] for j in np.argsort(-sim[i], kind="stable") if j != i]
        out[c] = order[:k]
    return out


def placement_entity(text, current):
    """Entity of a placement option: another predicted entity by its id, else the current one (current entity,
    sub-entity, relationship(current, X) and separate table all stay with the current entity); None if empty."""
    t = (text or "").lower()
    if not t:
        return None
    if any(w in t for w in ("sub-entity", "sub entity", "relationship", "separate table")):
        return current
    m = re.search(r"\bE\d+\b", text)
    return m.group(0) if m else (current if "current" in t else None)


def _slot(attr, entity_gold):
    words = attr.lower().split()
    return " ".join(words[1:] if words and words[0] == entity_gold else words)


def _tokens(s, entity_gold):
    toks = [re.sub(r"s$", "", w) for w in re.findall(r"[a-z0-9]+", s.lower()) if w != entity_gold and w not in STOP]
    return set(toks)


def name_check_table(attrs_by_file, mentions, entity_gold="train"):
    """Rows (variant, run_tag, attr): name vs the majority gold_attr of the attribute's mentions, pre-filled by token
    overlap (auto_right 1/0); `manual` is empty here and, when filled, overrides auto in `right`."""
    rows = []
    for (variant, tag), (attrs, assign) in attrs_by_file.items():
        gold = {int(i): g for i, g in zip(mentions["mention_id"], mentions["gold_attr"])}
        for _, a in attrs[attrs["name"] != ""].iterrows():
            cnt = Counter(c for i, aid in assign.items() if aid == a["attr_id"] for c in _classes(gold[i]))
            maj = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if cnt else ""
            auto = int(bool(_tokens(a["name"], entity_gold) & _tokens(maj, entity_gold)))
            rows.append({"variant": variant, "run_tag": tag, "attr_id": a["attr_id"], "name": a["name"],
                         "majority_gold_attr": maj, "auto_right": auto, "manual": "", "right": auto})
    return pd.DataFrame(rows, columns=NAME_COLS)


def apply_manual(table, old=None):
    """Carry `manual` over from an earlier name_check.csv (same variant, run_tag, attr_id) and set `right`."""
    t = table.copy()
    if old is not None and len(old):
        prev = {(r["variant"], str(r["run_tag"]), r["attr_id"]): str(r["manual"]).strip()
                for _, r in old.fillna("").iterrows()}
        t["manual"] = [prev.get((r["variant"], str(r["run_tag"]), r["attr_id"]), "") for _, r in t.iterrows()]
    man = t["manual"].fillna("").astype(str).str.strip().str.lower()
    t["right"] = [1 if m in YES else 0 if m in NO else int(a) for m, a in zip(man, t["auto_right"])]
    return t


class Ctx:
    """Everything the checks need besides one response file's decisions."""

    def __init__(self, mentions, labels, gold_values, gold_attrs, ids, x, examples, entity, entity_gold="train"):
        self.mentions, self.labels, self.gv, self.ids, self.x = mentions, labels, gold_values, ids, x
        self.examples, self.entity, self.entity_gold = examples, entity, entity_gold
        self.pm = mentions[(mentions["entity"] == entity) & (mentions["cluster_id"] != "")]
        self.train = train_attrs(gold_values, gold_attrs, entity_gold)
        self.label = labels.set_index("cluster_id")
        self.cluster_gold = {c: mode(g["entity_gold"]) for c, g in self.pm.groupby("cluster_id")}
        clustered = mentions[mentions["cluster_id"] != ""]
        self.entity_gold_of = {e: mode(g["entity_gold"]) for e, g in clustered.groupby("entity")}
        self.hints = merge_hints(mentions, ids, x, entity)
        self.recall_before = self._recall_of(mentions)

    def _recall_of(self, mentions, drop=()):
        m = mentions if not drop else mentions.assign(
            cluster_id=mentions["cluster_id"].where(~mentions["cluster_id"].isin(drop), ""))
        t = _recall().recall_table(m, self.gv, self.train)
        return float(t["strict"].astype(bool).mean()) if len(t) else float("nan")


def _gold_cluster(ctx, cid):
    """gold_attr of a gold-labelled cluster, else None."""
    if cid in ctx.label.index and ctx.label.at[cid, "label"] == "gold":
        return ctx.label.at[cid, "gold_attr"]
    return None


def _merge_checks(attrs, ctx):
    groups = [a["clusters"].split(";") for _, a in attrs.iterrows() if a["source"] == "merge"]
    ok = den = 0
    for g in groups:
        gold = [x for x in (_gold_cluster(ctx, c) for c in g) if x]
        if len(gold) >= 2:
            den += 1
            ok += len(set(gold)) == 1
    where = {c: a["attr_id"] for _, a in attrs.iterrows() if a["source"] != "split" for c in a["clusters"].split(";")}
    gold_c = sorted(c for c in ctx.cluster_gold if _gold_cluster(ctx, c))
    pairs = [(a, b) for i, a in enumerate(gold_c) for b in gold_c[i + 1:] if _gold_cluster(ctx, a) == _gold_cluster(ctx, b)]
    hit = sum(where.get(a) is not None and where.get(a) == where.get(b) for a, b in pairs)
    return {"merge_pure": _ratio(ok, den), "merge_frag": _ratio(hit, len(pairs))}


def _split_checks(dec, parts, ctx):
    pt = _recall().purity_table(ctx.pm)
    ex_mention = dict(zip(ctx.examples["ex_id"], ctx.examples["mention_id"].astype(int)))
    gold = dict(zip(ctx.mentions["mention_id"].astype(int), ctx.mentions["gold_attr"]))
    targets, done, right, total = [], 0, 0, 0
    for cid, g in pt.groupby("cluster_id"):
        if _gold_cluster(ctx, cid):
            continue
        g = g.sort_values(["n_class", "gold_attr"], ascending=[False, True])
        top = g["gold_attr"].tolist()[:2]
        if (len(top) == 2 and g["size"].iloc[0] >= SPLIT_MIN_SIZE and g["purity"].iloc[1] >= SPLIT_MIN_SECOND
                and {_slot(a, ctx.entity_gold) for a in top} in SPLIT_KINDS):
            targets.append((cid, top))
    for cid, top in targets:
        if cid not in parts:
            continue
        done += 1
        hits = [[sum(c in _classes(gold[ex_mention[e]]) for e in eids) for c in top] for _, eids in parts[cid]]
        # sides: the class per part that maximises right examples, with both classes used (a real separation)
        best = max(sum(h[k] for h, k in zip(hits, ks)) for ks in product(range(2), repeat=len(hits)) if len(set(ks)) == 2)
        right += best
        total += sum(len(eids) for _, eids in parts[cid])
    return {"split_done": _ratio(done, len(targets)), "split_side": _ratio(right, total)}


def _noise_checks(dec, ctx):
    noise = [c for c in ctx.cluster_gold if c in ctx.label.index and ctx.label.at[c, "label"] == "noise"]
    row = {r["cluster_id"]: r for _, r in dec.iterrows()}
    marked = sum(c in row and row[c]["action"] in PV.MARKED for c in noise)
    kept = sum(c in row and row[c]["action"] == "keep" and bool(row[c]["name"]) for c in noise)
    return {"noise_marked": _ratio(marked, len(noise)), "noise_kept": (float(kept), len(noise))}


def _placement_checks(dec, ctx):
    ok = den = 0
    for _, r in dec.iterrows():
        ent = placement_entity(r["placement"], ctx.entity)
        want = ctx.cluster_gold.get(r["cluster_id"], "")
        if r["action"] == "" or not r["placement"] or not want:
            continue
        den += 1
        ok += ent is not None and ctx.entity_gold_of.get(ent, "") == want
    return {"place_right": _ratio(ok, den)}


def _train_checks(relabelled, attrs, ctx):
    marked = set(attrs.loc[attrs["status"].isin(PV.MARKED), "attr_id"])
    after = ctx._recall_of(relabelled)
    kept = ctx._recall_of(relabelled, drop=marked)
    pm = relabelled[(relabelled["entity"] == ctx.entity) & (relabelled["cluster_id"] != "") & (relabelled["gold_attr"] != "")]
    units = [SimpleNamespace(labels=set(_classes(g))) for g in pm["gold_attr"]]
    p1 = one_to_one(units, list(pm["cluster_id"]))[0] if len(units) else float("nan")
    return {"recall_after": (after, len(ctx.train)), "recall_after_kept": (kept, len(ctx.train)), "p1_after": (p1, len(units))}


def _suggestion_checks(dec, ctx):
    ok = den = 0
    for _, r in dec.iterrows():
        if r["action"] != "merge":
            continue
        for t in json.loads(r["merge_with"] or "[]"):
            if t in ctx.hints.get(r["cluster_id"], []):
                a, b = _gold_cluster(ctx, r["cluster_id"]), _gold_cluster(ctx, t)
                if a and b:
                    den += 1
                    ok += a == b
    return {"sugg_right": _ratio(ok, den)}


def _verification_checks(ver, names):
    out = {}
    if len(ver):
        j = ver.merge(names[["variant", "run_tag", "attr_id", "right"]], on=["variant", "run_tag", "attr_id"], how="left")
        for key, flag in (("j_right", 1), ("j_wrong", 0)):
            s = j.loc[j["right"] == flag, "jaccard"]
            out[key] = (float(s.mean()) if len(s) else float("nan"), len(s))
    return out


def score_file(dec, attrs, assign, parts, ctx, ver, names):
    """{measure: value, measure_n: n} for one response file (see CHECKS)."""
    relabelled = PV.relabel(ctx.mentions, assign)
    res = {}
    for part in (_merge_checks(attrs, ctx), _split_checks(dec, parts, ctx), _noise_checks(dec, ctx),
                 _placement_checks(dec, ctx), _train_checks(relabelled, attrs, ctx),
                 _suggestion_checks(dec, ctx), _verification_checks(ver, names)):
        res.update(part)
    out = {}
    for k, (v, n) in res.items():
        out[k], out[k + "_n"] = v, n
    out["recall_before"] = ctx.recall_before
    out["n_clusters"] = len(dec)
    return out


def stability(a, b):
    """(share of clusters whose action, merge_with set or name differ between two decision tables, n)."""
    bb = {r["cluster_id"]: r for _, r in b.iterrows()}
    diff = n = 0
    for _, r in a.iterrows():
        o = bb.get(r["cluster_id"])
        if o is None:
            continue
        n += 1
        same = (r["action"] == o["action"] and set(json.loads(r["merge_with"] or "[]")) == set(json.loads(o["merge_with"] or "[]"))
                and r["name"].strip().lower() == o["name"].strip().lower())
        diff += not same
    return _ratio(diff, n)


def _fmt(v, count=False):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    return f"{v:.0f}" if count else f"{v:.3f}"


def _met(key, kind, target, res):
    """ok / FAIL / '' for one value against its target."""
    v = res.get(key)
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if kind == ">=":
        return "ok" if v >= target else "FAIL"
    if kind == "<=":
        return "ok" if v <= target else "FAIL"
    if kind == "after>=before":
        return "ok" if v >= res["recall_before"] - 1e-9 else "FAIL"
    return ""


def _target_text(kind, target):
    return {">=": f">= {target}", "<=": f"<= {target}", "after>=before": ">= before (no loss)", "": "report only"}[kind]


def render_scores(results, stab=None, entity="", note=""):
    """scores.md: one block per check (value and target per response file), the comparison table, context, stability.
    results: {file label: score_file output}; stab: (value, n) of full r1 vs r2."""
    labels = list(results)
    lines = ["# Pilot scores", "", f"Pilot entity {entity}. {note}".strip(), ""]
    block = None
    for key, blk, text, kind, target in CHECKS:
        if blk != block:
            lines += [f"## {blk}", ""]
            block = blk
        lines += [f"### {text}", f"Target: {_target_text(kind, target)}", "",
                  "| response | value | n | status |", "|---|---|---|---|"]
        for lab in labels:
            r = results[lab]
            extra = f" (before {_fmt(r['recall_before'])})" if key == "recall_after" else ""
            lines.append(f"| {lab} | {_fmt(r.get(key), key == 'noise_kept')}{extra} | "
                         f"{r.get(key + '_n', '')} | {_met(key, kind, target, r)} |")
        lines.append("")
    lines += ["## Comparison", "", "| measure | target | " + " | ".join(labels) + " |",
              "|---|---|" + "---|" * len(labels)]
    for key, _, text, kind, target in CHECKS:
        lines.append(f"| {key} | {_target_text(kind, target)} | " + " | ".join(
            f"{_fmt(results[lab].get(key), key == 'noise_kept')} {_met(key, kind, target, results[lab])}".strip()
            for lab in labels) + " |")
    full, nocon = (next((lab for lab in labels if lab.startswith(p)), None) for p in ("full r1", "nocontext r1"))
    lines += ["", "## Context (full r1 vs nocontext r1)", ""]
    if full and nocon:
        lines += ["Expected: clearly lower without context.", "", "| measure | full | nocontext | delta |", "|---|---|---|---|"]
        for key, *_ in CHECKS:
            a, b = results[full].get(key), results[nocon].get(key)
            d = b - a if isinstance(a, (int, float)) and isinstance(b, (int, float)) else float("nan")
            lines.append(f"| {key} | {_fmt(a)} | {_fmt(b)} | {_fmt(d)} |")
    else:
        lines.append("full r1 or nocontext r1 missing.")
    lines += ["", "## Stability (full r1 vs r2, report only)", ""]
    lines.append(f"Clusters with a different action, merge_with or name: {_fmt(stab[0])} (n={stab[1]})" if stab else "full r1 or r2 missing.")
    return "\n".join(lines) + "\n"
