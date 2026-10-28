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
# name rubric (NAMING_RULE.md): the sheet columns and the categories a rater picks
RUBRIC_COLS = ["variant", "run_tag", "entity", "attr_id", "name", "description", "majority_gold_attr", "top_values",
               "label", "category", "rater1", "rater2", "final"]
RUBRIC_HAND = ["category", "rater1", "rater2", "final"]
CATEGORIES = ("exact", "synonym", "too_general", "wrong_role", "wrong", "noise_named", "noise_marked")
RIGHT_NAMES = ("exact", "synonym")
REAL_LABELS = ("gold", "valid_new")
ROLE_SLOTS = {"departure", "destination", "leave at", "arrive by"}  # the slots of the two role pairs


def _recall():
    from . import recall
    return recall


def _ratio(num, den):
    return (num / den if den else float("nan")), den


def mode(values):
    values = [v for v in values if v]
    return Counter(values).most_common(1)[0][0] if values else ""


def _ents(entity_gold):
    """Gold entity names as a tuple: "train" -> ("train",), ["restaurant", "taxi"] -> both."""
    return (entity_gold,) if isinstance(entity_gold, str) else tuple(entity_gold)


def train_attrs(gold_values, attrs, entity_gold="train"):
    """Gold classes whose gold entity (mode of entity_gold) is entity_gold (a name or a list of names)."""
    ents = set(_ents(entity_gold))
    ent = {}
    for _, r in gold_values.iterrows():
        for c in _classes(r["gold_attr"]):
            ent.setdefault(c, []).append(r["entity_gold"])
    return [a for a in attrs if mode(ent.get(a, [])) in ents]


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
    return " ".join(words[1:] if words and words[0] in _ents(entity_gold) else words)


def _tokens(s, entity_gold):
    toks = [re.sub(r"s$", "", w) for w in re.findall(r"[a-z0-9]+", s.lower())
            if w not in _ents(entity_gold) and w not in STOP]
    return set(toks)


def _majority_gold(assign, attr_id, gold):
    """Most common gold class (ties: name order) over the mentions assigned to attr_id; "" if none."""
    cnt = Counter(c for i, aid in assign.items() if aid == attr_id for c in _classes(gold[i]))
    return sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if cnt else ""


def name_check_table(attrs_by_file, mentions, entity_gold="train"):
    """Rows (variant, run_tag, attr): name vs the majority gold_attr of the attribute's mentions, pre-filled by token
    overlap (auto_right 1/0); `manual` is empty here and, when filled, overrides auto in `right`."""
    rows = []
    for (variant, tag), (attrs, assign) in attrs_by_file.items():
        gold = {int(i): g for i, g in zip(mentions["mention_id"], mentions["gold_attr"])}
        for _, a in attrs[attrs["name"] != ""].iterrows():
            maj = _majority_gold(assign, a["attr_id"], gold)
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


def _norm_placement(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def name_merge(dec, mentions, entity):
    """Decision table with variant "<variant>+namemerge": clusters of the entity with the same normalized name
    (PV.norm_name) and the same placement are merged unless that would put two clusters of one instance_id into one
    attribute. The response's own merge groups (merge_with, split clusters left out) are kept as they are; a
    candidate union is checked on the instance sets of both groups. Only keep/merge rows take part."""
    pm = mentions[(mentions["entity"] == entity) & (mentions["cluster_id"] != "")]
    rows = {r["cluster_id"]: r for _, r in dec.iterrows()}
    parent = {c: c for c in rows if rows[c]["action"] != "split"}
    for c, r in rows.items():
        if r["action"] == "merge":
            for t in json.loads(r["merge_with"] or "[]"):
                if c in parent and t in parent:
                    parent[PV._find(parent, c)] = PV._find(parent, t)
    insts = {}
    for c in parent:
        root = PV._find(parent, c)
        insts.setdefault(root, set()).update(pm.loc[pm["cluster_id"] == c, "instance_id"])
    cand = sorted(c for c in parent if rows[c]["action"] in ("keep", "merge") and PV.norm_name(rows[c]["name"]))
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            ra, rb = PV._find(parent, a), PV._find(parent, b)
            if (ra != rb and PV.norm_name(rows[a]["name"]) == PV.norm_name(rows[b]["name"])
                    and _norm_placement(rows[a]["placement"]) == _norm_placement(rows[b]["placement"])
                    and not insts[ra] & insts[rb]):
                parent[rb] = ra
                insts[ra] |= insts.pop(rb)
    groups = {}
    for c in parent:
        groups.setdefault(PV._find(parent, c), []).append(c)
    out = dec.copy()
    out["variant"] = out["variant"] + "+namemerge"
    for members in groups.values():
        if len(members) > 1:
            for c in members:
                if rows[c]["action"] in ("keep", "merge"):
                    k = out.index[out["cluster_id"] == c][0]
                    out.at[k, "action"] = "merge"
                    out.at[k, "merge_with"] = json.dumps(sorted(m for m in members if m != c))
    return out


def rubric_sheet(attrs_by_file, mentions, labels, clusters_table, old=None):
    """Name rubric sheet (NAMING_RULE.md): one row per attribute of each response file, status keep or marked (not
    attributes are rows too: a noise cluster correctly marked is `noise_marked`). attrs_by_file {(variant, run_tag):
    (attrs, assign)} as for name_check_table. majority_gold_attr: most common gold class of the attribute's mentions;
    top_values: up to 5 values of its largest cluster (clusters_table top_values; split parts: their mentions);
    label: gold / valid_new / noise of the largest member cluster. category / rater1 / rater2 / final are left empty
    and, when `old` (an earlier sheet) has them for the same (variant, run_tag, attr_id), carried over."""
    gold = {int(i): g for i, g in zip(mentions["mention_id"], mentions["gold_attr"])}
    norm = dict(zip(mentions["mention_id"].astype(int), mentions["norm_value"]))
    lab = dict(zip(labels["cluster_id"], labels["label"]))
    top = dict(zip(clusters_table["cluster_id"], clusters_table["top_values"]))
    ent = mentions.groupby("cluster_id")["entity"].first().to_dict()
    csize = mentions.groupby("cluster_id").size().to_dict()
    prev = {}
    if old is not None and len(old):
        prev = {(r["variant"], str(r["run_tag"]), r["attr_id"]): r for _, r in old.fillna("").iterrows()}
    rows = []
    for (variant, tag), (attrs, assign) in attrs_by_file.items():
        for _, a in attrs[attrs["status"] != "missing"].iterrows():
            members = a["clusters"].split(";")
            big = min(members, key=lambda c: (-csize.get(c, 0), c))
            if a["source"] == "split":
                vals = [v for v, _ in Counter(norm[i] for i, aid in assign.items() if aid == a["attr_id"]).most_common(5)]
            else:
                vals = [v for v in str(top.get(big, "")).split("|") if v][:5]
            old_row = prev.get((variant, str(tag), a["attr_id"]), {})
            rows.append({"variant": variant, "run_tag": tag, "entity": ent.get(big, ""), "attr_id": a["attr_id"],
                         "name": a["name"], "description": a.get("description", ""),
                         "majority_gold_attr": _majority_gold(assign, a["attr_id"], gold), "top_values": "|".join(vals),
                         "label": lab.get(big, ""), **{c: str(old_row.get(c, "")) for c in RUBRIC_HAND}})
    return pd.DataFrame(rows, columns=RUBRIC_COLS)


def rubric_accuracy(sheet):
    """{(variant, run_tag): dict} over the rows with a `final` category (blank rows are not counted):
    real_acc/real_n: gold + valid_new rows whose final is exact or synonym;
    noise_marked/noise_n: noise rows whose final is noise_marked (the others are noise_named);
    role_acc/role_n: real rows whose majority gold slot is departure/destination/leave at/arrive by and whose final
    is exact or synonym; role_wrong: those with final wrong_role. An empty denominator gives nan."""
    out = {}
    done = sheet[sheet["final"].fillna("").astype(str).str.strip() != ""]
    for key, g in done.groupby(["variant", "run_tag"]):
        fin = g["final"].astype(str).str.strip().str.lower()
        real, noise = g["label"].isin(REAL_LABELS), g["label"] == "noise"
        slot = g["majority_gold_attr"].astype(str).str.lower().str.split(n=1).str[-1]
        role = real & slot.isin(ROLE_SLOTS)
        out[key] = {"real_acc": _ratio(fin[real].isin(RIGHT_NAMES).sum(), real.sum())[0], "real_n": int(real.sum()),
                    "noise_marked": _ratio((fin[noise] == "noise_marked").sum(), noise.sum())[0],
                    "noise_n": int(noise.sum()),
                    "role_acc": _ratio(fin[role].isin(RIGHT_NAMES).sum(), role.sum())[0], "role_n": int(role.sum()),
                    "role_wrong": int((fin[role] == "wrong_role").sum())}
    return out


def _rubric_lines(rubric):
    """The "## Name rubric" block of scores.md; "rubric not filled" when no row has a final category."""
    acc = rubric_accuracy(rubric) if rubric is not None and len(rubric) else {}
    lines = ["", "## Name rubric (NAMING_RULE.md)", ""]
    if not acc:
        return lines + ["rubric not filled"]
    lines += ["| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |",
              "|---|---|---|---|---|---|---|---|"]
    for (variant, tag), r in acc.items():
        lines.append(f"| {variant} {tag} | {_fmt(r['real_acc'])} | {r['real_n']} | {_fmt(r['noise_marked'])} | "
                     f"{r['noise_n']} | {_fmt(r['role_acc'])} | {r['role_n']} | {r['role_wrong']} |")
    return lines


class Ctx:
    """Everything the checks need besides one response file's decisions."""

    def __init__(self, mentions, labels, gold_values, gold_attrs, ids, x, examples, entity, entity_gold="train",
                 split_kinds=None):
        """entity_gold: one gold entity name or a list (restaurant pilot entity: ["restaurant", "taxi"]).
        split_kinds: None = a split target is any cluster whose top two classes are both gold classes of the entity
        (on wf_v3's train entity this gives the same targets as the old rule); SPLIT_KINDS = only the role pairs."""
        self.mentions, self.labels, self.gv, self.ids, self.x = mentions, labels, gold_values, ids, x
        self.examples, self.entity, self.entity_gold = examples, entity, entity_gold
        self.split_kinds = split_kinds
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
        if _gold_cluster(ctx, cid) or (cid in ctx.label.index and ctx.label.at[cid, "label"] == "noise"):
            continue  # gold clusters are pure; noise clusters are scored by the noise check, not as split targets
        g = g.sort_values(["n_class", "gold_attr"], ascending=[False, True])
        top = g["gold_attr"].tolist()[:2]
        kind_ok = ({_slot(a, ctx.entity_gold) for a in top} in ctx.split_kinds if ctx.split_kinds is not None
                   else all(a in ctx.train for a in top))
        if len(top) == 2 and g["size"].iloc[0] >= SPLIT_MIN_SIZE and g["purity"].iloc[1] >= SPLIT_MIN_SECOND and kind_ok:
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
        if r["action"] == "" or not r["placement"] or not want or want not in ctx.entity_gold_of.values():
            continue  # no predicted entity has this gold entity as majority (e.g. taxi): no right answer
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


def render_scores(results, stab=None, entity="", note="", rubric=None, pair=("full", "nocontext"),
                  stab_pair=("full r1", "r2")):
    """scores.md: one block per check (value and target per response file), the comparison table, context, stability.
    results: {file label: score_file output}; stab: (value, n) of the stab_pair responses; pair: variant names of the
    context comparison (their r1 runs); rubric: name rubric sheet -> a "Name rubric" block at the end (None: no block)."""
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
    full, nocon = (next((lab for lab in labels if lab == f"{p} r1"), None) for p in pair)
    lines += ["", f"## Context ({pair[0]} r1 vs {pair[1]} r1)", ""]
    if full and nocon:
        lines += ["Expected: clearly lower without context.", "", f"| measure | {pair[0]} | {pair[1]} | delta |",
                  "|---|---|---|---|"]
        for key, *_ in CHECKS:
            a, b = results[full].get(key), results[nocon].get(key)
            d = b - a if isinstance(a, (int, float)) and isinstance(b, (int, float)) else float("nan")
            lines.append(f"| {key} | {_fmt(a)} | {_fmt(b)} | {_fmt(d)} |")
    else:
        lines.append(f"{pair[0]} r1 or {pair[1]} r1 missing.")
    lines += ["", f"## Stability ({stab_pair[0]} vs {stab_pair[1]}, report only)", ""]
    lines.append(f"Clusters with a different action, merge_with or name: {_fmt(stab[0])} (n={stab[1]})" if stab
                 else f"{stab_pair[0]} or {stab_pair[1]} missing.")
    if rubric is not None:
        lines += _rubric_lines(rubric)
    return "\n".join(lines) + "\n"
