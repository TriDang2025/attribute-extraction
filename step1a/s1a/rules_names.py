"""wf_v3.4 name rules (SCORER_V34_CONTRACT.md, W5): Q4 name rubric (sheet, scores), Q7 order agreement, Q8 order range
and gain verdict. No LLM: names are rated by two blind raters from results/loop1_v34/names_to_rate.csv (labels in
name_rubric_prompt.md) and read back as extra["names_rated"].

CLI (from step1a/): python -m s1a.rules_names --run results/graph_v22_dev50 --dir32 results/loop1_v32
--dir31 results/loop1_v31 --out results/loop1_v34   (writes names_to_rate.csv and name_sheet.csv)
"""

import argparse
import importlib
import json
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import pilot_combine as PC
from . import pilot_score as PS
from . import pilot_verify as PV
from . import shapes
from .labels import _classes

LABELS = ("right", "too_general", "wrong_role", "valid_extra", "wrong")  # best first: the lower label wins a tie
L2_LABELS = ("right", "partly", "wrong")  # names_l2_rubric.md; names=l2rated, best first
L2_FILES = ("names_l2_rater1.csv", "names_l2_rater2.csv")
L2_KEY_FILE = "names_to_rate_l2_key.csv"  # row -> JOIN_KEYS (+ variant, for audit); written by s1a.names_l2
RATE_COLS = ["ent", "name", "description", "majority_gold_attr", "role", "cluster_label", "top_values"]
SHEET_COLS = ["row", "ent", "variant label", "attr_id", "name", "description", "majority_gold_attr", "role",
              "cluster_label", "top_values", "old_final", "freq", "valid_extra_candidate"]
JOIN_KEYS = ["ent", "name", "description", "majority_gold_attr"]
SEEDS = ("C s0", "C s1", "C s2")
ORDER_VARIANTS = ("C s0", "C s1", "C s2", "A r1", "A r2")
GAIN_VARIANTS = ("B s0", "C s012", "D s012")
GAIN_MIN = 2
INVALID_RUNS_PATH = Path(__file__).resolve().parents[1] / "config" / "invalid_runs.json"
OLD_CLUSTER_LABEL = {"gold": "real", "valid_new": "real", "noise": "noise"}
_DURATION = re.compile(r"\d+\s*(?:minutes?|mins?|hours?|hrs?)", re.I)
TOP_N = 5


# ---- name sheet (Q4)

def _is_code_value(text):
    return shapes.kind(text) is not None or bool(_DURATION.fullmatch(str(text).strip()))


def _cluster_label_map(ed, extra):
    """{cluster_id: real/mixed/noise}: extra["cluster_labels"][ent] (W3), else W3's function if it exists, else the
    old labels.csv mapping."""
    pre = (extra.get("cluster_labels") or {}).get(ed.ent)
    if pre is None:
        try:
            from .score_rules import Rules
            fn = importlib.import_module("s1a.rules_labels").cluster_labels
            pre = fn(ed, Rules.default(), extra)
        except (ModuleNotFoundError, AttributeError):
            pre = None
    if pre is not None:
        return dict(zip(pre["cluster_id"], pre["label"]))
    return {c: OLD_CLUSTER_LABEL.get(lab, "mixed") for c, lab in zip(ed.labels["cluster_id"], ed.labels["label"])}


def _variant_rows(ed, label, cl_label):
    """One dict per non-missing attribute of one variant label (name may be "" for a marked cluster)."""
    vo = ed.variants[label]
    m = ed.mentions
    mid = m["mention_id"].astype(int)
    gold = dict(zip(mid, m["gold_attr"]))
    norm = dict(zip(mid, m["norm_value"]))
    raw = dict(zip(mid, m["text"]))
    size = m.groupby("cluster_id").size().to_dict()
    by_cluster = {c: list(g.astype(int)) for c, g in m.groupby("cluster_id")["mention_id"]}
    rows = []
    for _, a in vo.attrs[vo.attrs["status"] != "missing"].iterrows():
        members = [c for c in a["clusters"].split(";") if c]
        big = min(members, key=lambda c: (-size.get(c, 0), c))
        ids = [i for i, aid in vo.assign.items() if aid == a["attr_id"]] if a["source"] == "split" else by_cluster.get(big, [])
        tops = [v for v, _ in Counter(norm[i] for i in ids).most_common(TOP_N)]
        maj = PS._majority_gold(vo.assign, a["attr_id"], gold)
        codes = np.mean([_is_code_value(raw[i]) for i in ids]) if ids else 0.0
        rows.append({"ent": ed.ent, "variant label": label, "attr_id": a["attr_id"], "name": a["name"],
                     "description": a.get("description", ""), "majority_gold_attr": maj,
                     "role": (PS._role_slot(maj) or "") if maj else "", "cluster_label": cl_label.get(big, ""),
                     "top_values": "|".join(tops), "valid_extra_candidate": bool(not maj and codes >= 0.5)})
    return rows


def _old_finals(old_rubric):
    if old_rubric is None or not len(old_rubric):
        return {}
    return {(r["variant"], str(r["run_tag"]), r["attr_id"]): r["final"] for _, r in old_rubric.fillna("").iterrows()
            if r["final"]}


def name_sheet(data, old_rubric, extra=None):
    """One row per distinct (ent, variant label, attr_id, name) of A r1, A r2, B s0, C s0/s1/s2, C s012, D s012 (not
    the +namemerge labels). `row` is the id of the names_to_rate row (see names_to_rate), "" for a marked cluster.
    old_final: old rubric `final` matched by (variant letter, run_tag, attr_id); A r2 falls back to variant v2 of the
    v3.1 rubric (old_rubric may be both files concatenated). freq: number of variant labels that produce the same
    (ent, name, majority_gold_attr)."""
    from .v34_data import VARIANTS
    extra = extra or {}
    old = _old_finals(old_rubric)
    rows = []
    for ed in data.values():
        cl = _cluster_label_map(ed, extra)
        for label in VARIANTS:
            rows += _variant_rows(ed, label, cl)
    sheet = pd.DataFrame(rows).drop_duplicates(["ent", "variant label", "attr_id", "name"], ignore_index=True)
    letter_tag = sheet["variant label"].str.split(" ", n=1, expand=True)
    sheet["old_final"] = [next((old[k] for k in ((lt, tg, a),) + ((("v2", tg, a),) if lt == "A" else ()) if k in old), "")
                          for lt, tg, a in zip(letter_tag[0], letter_tag[1], sheet["attr_id"])]
    key = ["ent", "name", "majority_gold_attr"]
    sheet["freq"] = sheet.groupby(key)["variant label"].transform("nunique")
    rate = names_to_rate(sheet)
    sheet = sheet.merge(rate[RATE_COLS + ["row"]], on=RATE_COLS, how="left")
    sheet["row"] = sheet["row"].fillna(-1).astype(int).map(lambda r: "" if r < 0 else r)
    return sheet[SHEET_COLS]


def names_to_rate(sheet):
    """Distinct (ent, name, description, majority_gold_attr, role, cluster_label, top_values) rows with a name, with a
    `row` id: what the blind raters label. Free of variant labels and old ratings."""
    r = sheet[sheet["name"] != ""][RATE_COLS].drop_duplicates(ignore_index=True)
    r.insert(0, "row", range(len(r)))
    return r


def _role_slots(extra, rules):
    """Slot names in a role pair: extra["role_pairs"] (tuples of slot names) when rules.role_pairs is config, else
    the old PS.ROLE_SLOTS."""
    pairs = extra.get("role_pairs")
    if rules.role_pairs == "old" or not pairs:
        return set(PS.ROLE_SLOTS)
    return {str(s).lower().replace("_", " ") for p in pairs for s in p[:2]}


def _rated_by_key(rated, labels=LABELS):
    """{(ent, name, description, majority_gold_attr): label}; several rows for one key keep the lowest label."""
    rank = {lab: i for i, lab in enumerate(labels)}
    out = {}
    for _, r in rated.iterrows():
        lab = str(r["label"]).strip().lower()
        if lab not in rank:
            raise ValueError(f"names_rated: unknown label {r['label']!r}, expected one of {tuple(labels)}")
        k = tuple(r[c] for c in JOIN_KEYS)
        if k not in out or rank[lab] > rank[out[k]]:
            out[k] = lab
    return out


def read_l2_rated(folder, files=L2_FILES, key_file=L2_KEY_FILE):
    """names=l2rated: DataFrame (JOIN_KEYS + label) from names_l2_rater1.csv / names_l2_rater2.csv (columns row, label)
    joined to the key file by row; the lower label of the two raters wins. None when a file is missing. `files` /
    `key_file`: other rater and key file names (wf_v3.7: names_l2_v37_rater{1,2}.csv + names_to_rate_l2_v37_key.csv)."""
    folder = Path(folder)
    paths = [folder / f for f in (*files, key_file)]
    if not all(p.exists() for p in paths):
        return None
    read = lambda p: pd.read_csv(p, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")  # noqa: E731
    key = read(paths[2])[["row"] + JOIN_KEYS].drop_duplicates("row")
    rows = pd.concat([read(p)[["row", "label"]] for p in paths[:2]], ignore_index=True).merge(key, on="row")
    got = _rated_by_key(rows, L2_LABELS)
    return pd.DataFrame([dict(zip(JOIN_KEYS, k), label=lab) for k, lab in got.items()],
                        columns=JOIN_KEYS + ["label"])


def _level_rows(ed, label):
    """[(row at the level, row at L1)] of one variant label, paired by attr_id. A level copy of the data
    (v34_data.with_level, ed.mentions_l1 set) has its majority gold attr at the level; the rated sheet was keyed on the
    L1 majority, so the L1 row is the rating key. Without a level copy both rows are the same."""
    rows = _variant_rows(ed, label, {})
    if getattr(ed, "mentions_l1", None) is None:
        return [(r, r) for r in rows]
    l1 = {r["attr_id"]: r for r in _variant_rows(replace(ed, mentions=ed.mentions_l1, mentions_l1=None), label, {})}
    return [(r, l1[r["attr_id"]]) for r in rows]


def name_scores(ed, label, rules, extra):
    """{name_right, name_base, name_acc, valid_extra, role_right, role_base, names_unrated} of one variant label from
    extra["names_rated"]. base = gold attrs in ctx.train; name_right = those with >= 1 group (attribute) rated right
    (a group counts for its majority gold attr); valid_extra = groups rated valid_extra; role_* = the same over gold
    attrs whose slot is in a role pair; names_unrated = groups with a name that has no rating (variants of a newer
    pilot than the rated sheet). {} when no rated sheet is given.
    GT level L2 / L3 (level copy): the rating is looked up with the L1 majority attr, since the raters saw it. A group
    rated right counts for its L1 majority attr (when that attr is in the level's base). APPROXIMATION: a group rated
    valid_extra whose majority gold attr at the level is an attr that has no L1 mention (a non-L1 attr) in the level's
    base counts as right for that attr; the raters never judged the level's attr itself.
    names=l2rated, GT level L2 / L3: the approximation is replaced. A group with a name is looked up in extra["names_l2"]
    (read_l2_rated: raters judged the name against the level majority attr's L2 slot name and description) under
    (ent, name, description, majority attr at the level); label right counts for that attr (when it is in the base). A
    name without a rating (a majority attr the sheet does not hold, e.g. an L3 DB column) counts as not right and is
    reported in names_unrated; valid_extra is 0 (the L2 labels are right / partly / wrong). L1 stays as names=v34."""
    rated = extra.get("names_rated")
    if rated is None:
        return {}
    l2 = rules.names == "l2rated" and getattr(ed, "level", 0) >= 2
    if l2 and extra.get("names_l2") is None:
        raise ValueError("names=l2rated needs extra['names_l2'] (names_l2_rater{1,2}.csv; score_rules.load_extra l2_dir)")
    got_l2 = _rated_by_key(extra["names_l2"], L2_LABELS) if l2 else {}
    ctx = ed.ctx_a if label.startswith("A") else ed.ctx_r
    base = list(ctx.train)
    got = _rated_by_key(rated)
    l1_attrs = {c for g in (ed.mentions_l1["gold_attr"] if getattr(ed, "mentions_l1", None) is not None else []) for c in _classes(g)}
    right, extras, unrated = set(), 0, 0
    for r, r1 in _level_rows(ed, label):
        if l2:
            if not r["majority_gold_attr"]:
                continue  # no L2 majority: not on the sheet, not scored
            lab = got_l2.get(tuple(r[c] for c in JOIN_KEYS)) if r["name"] else None
            unrated += bool(r["name"]) and lab is None
            if lab == "right" and r["majority_gold_attr"] in base:
                right.add(r["majority_gold_attr"])
            continue
        lab = got.get(tuple(r1[c] for c in JOIN_KEYS)) if r["name"] else None
        unrated += bool(r["name"]) and lab is None
        if lab == "right" and r1["majority_gold_attr"] in base:
            right.add(r1["majority_gold_attr"])
        elif lab == "valid_extra" and r["majority_gold_attr"] in base and r["majority_gold_attr"] not in l1_attrs                 and getattr(ed, "mentions_l1", None) is not None:
            right.add(r["majority_gold_attr"])
        extras += lab == "valid_extra"
    slots = _role_slots(extra, rules)
    role_base = [a for a in base if PS._slot(a, ed.gold_ents) in slots]
    return {"name_right": len(right), "name_base": len(base), "name_acc": len(right) / len(base) if base else np.nan,
            "valid_extra": extras, "role_right": len(right & set(role_base)), "role_base": len(role_base),
            "names_unrated": unrated}


# ---- order effects (Q7)

def _seed_state(ed):
    """{cluster_id: [per seed (marked, group signature, norm name, vote key)]} for C s0/s1/s2."""
    per = []
    for s in SEEDS:
        t = {r["cluster_id"]: r for _, r in ed.seed_decs[s].iterrows()}
        st = {}
        for c, r in t.items():
            act = r["action"]
            if act in ("keep", "merge"):
                grp = "|".join(sorted({c} | set(json.loads(r["merge_with"] or "[]"))))
            else:
                grp = f"{act}:{r['split']}" if act == "split" else ""
            st[c] = (act in PV.MARKED, grp, PV.norm_name(r["name"]), PC._key(r))
        per.append(st)
    cids = sorted(set().union(*per))
    return {c: [p.get(c) for p in per] for c in cids}


def _cluster_majority(ed):
    gold = ed.mentions.groupby("cluster_id")["gold_attr"].apply(
        lambda g: PS.mode(c for ga in g for c in _classes(ga)))
    return gold.to_dict()


def _name_key(name, maj, entity_gold):
    """Name identity that ignores wording: "gold:<attr>" when the name overlaps its cluster's majority gold attr (the
    name check rule), else the normalised name."""
    if maj and PS._tokens(name, entity_gold) & PS._tokens(maj, entity_gold):
        return f"gold:{maj}"
    return PV.norm_name(name)


def order_diffs(ed):
    """For C s0/s1/s2, every cluster whose decision differs across the 3 orders, typed (first match wins):
    noise (marked in some orders, not others); membership (different cluster set in its group); wording (names differ
    but all mean the cluster's majority gold attr, or share a word when it has no gold); meaning (other name
    differences). Columns: ent, cluster_id, type, majority_gold, s0/s1/s2 name and group."""
    maj = _cluster_majority(ed)
    rows = []
    for c, st in _seed_state(ed).items():
        if any(s is None for s in st) or len({s[:3] for s in st}) == 1:
            continue
        marked, groups, names = {s[0] for s in st}, {s[1] for s in st}, [s[2] for s in st]
        if len(marked) > 1:
            kind = "noise"
        elif len(groups) > 1:
            kind = "membership"
        else:
            m = maj.get(c, "")
            toks = [PS._tokens(n, ed.gold_ents) for n in names]
            same = (len({_name_key(n, m, ed.gold_ents) for n in names}) == 1 if m
                    else all(a & b for a in toks for b in toks))
            kind = "wording" if same else "meaning"
        rows.append({"ent": ed.ent, "cluster_id": c, "type": kind, "majority_gold": maj.get(c, ""),
                     **{f"s{i}_{f}": v for i, s in enumerate(st) for f, v in (("name", s[2]), ("group", s[1]))}})
    return pd.DataFrame(rows)


def agreement(ed, rules, extra):
    """{agree_groups, agree_noise, agree_names}: mean over clusters of (orders agreeing with the most common choice /
    3 orders). old: all three are the v3.2 vote agreement (whole decision key, all clusters). split: noise = marked or
    not; groups and names are over clusters not marked in any order; groups = cluster set of the group; names ignore
    wording (_name_key)."""
    state = _seed_state(ed)
    n = len(SEEDS)

    def share(keys):
        return Counter(keys).most_common(1)[0][1] / n

    full = [share([s[3] for s in st]) for st in state.values() if all(s is not None and s[3] is not None for s in st)]
    if rules.agreement == "old":
        v = float(np.mean(full)) if full else np.nan
        return {"agree_groups": v, "agree_noise": v, "agree_names": v}
    maj = _cluster_majority(ed)
    live = [(c, st) for c, st in state.items() if all(s is not None for s in st)]
    kept = [(c, st) for c, st in live if not any(s[0] for s in st)]

    def mean(vals):
        return float(np.mean(vals)) if vals else np.nan

    return {"agree_groups": mean([share([s[1] for s in st]) for _, st in kept]),
            "agree_noise": mean([share([s[0] for s in st]) for _, st in live]),
            "agree_names": mean([share([_name_key(s[2], maj.get(c, ""), ed.gold_ents) for s in st]) for c, st in kept])}


# ---- order range and gain verdict (Q8)

def invalid_runs(path=INVALID_RUNS_PATH):
    """[{ent, variant, reason}] of runs left out of order_range and gain_verdict (config/invalid_runs.json)."""
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))["runs"] if path.exists() else []


def _found_table(rows, invalid=None):
    """DataFrame ent x variant of found_n (numeric; n/a becomes NaN) from score rows (list of dicts or DataFrame).
    Cells of invalid runs (list of {ent, variant}; None = the config file) are NaN."""
    df = pd.DataFrame(rows)
    df["found_n"] = pd.to_numeric(df["found_n"], errors="coerce")
    t = df.pivot_table(index="ent", columns="variant", values="found_n", aggfunc="first", dropna=False)
    for r in invalid_runs() if invalid is None else invalid:
        if r["ent"] in t.index and r["variant"] in t.columns:
            t.loc[r["ent"], r["variant"]] = np.nan
    return t


def order_range(rows, invalid=None):
    """found_n per entity (plus a total row "all") for C s0/s1/s2 and A r1/r2. range_C and range_A = max - min within
    one method (order alone); range = the larger of the two, so a method difference (A vs C) is not order noise.
    Invalid runs are dropped: the entity's range uses the runs left, the "all" row sums only entities where every run
    of the method is valid. Column `invalid` lists the dropped runs of the row."""
    t = _found_table(rows, invalid)
    t = t[[v for v in ORDER_VARIANTS if v in t.columns]]
    bad = {e: [f"{v}" for v in t.columns if np.isnan(t.loc[e, v])] for e in t.index}
    per_ent = {meth: [v for v in t.columns if v.startswith(meth + " ")] for meth in ("C", "A")}
    out = t.copy()
    for meth, cols in per_ent.items():
        out[f"range_{meth}"] = t[cols].max(axis=1) - t[cols].min(axis=1) if cols else float("nan")
    total = {}
    for meth, cols in per_ent.items():
        ok = t.index[t[cols].notna().all(axis=1)] if cols else []
        total[f"range_{meth}"] = (t.loc[ok, cols].sum().max() - t.loc[ok, cols].sum().min()) if len(ok) else float("nan")
    out.loc["all"] = t.sum(min_count=len(t))  # NaN where a run of the variant is invalid in some entity
    for k, v in total.items():
        out.loc["all", k] = v
    out["range"] = out[["range_C", "range_A"]].max(axis=1)
    bad["all"] = [f"{e} {v}" for e in t.index for v in bad[e]]
    out["invalid"] = ["; ".join(bad[e]) for e in out.index]
    return out.reset_index()


def gain_verdict(rows, base="A r1", invalid=None):
    """For B s0, C s012, D s012: gain = found_n over `base` (per entity and total). A gain counts if total >= 2, no
    entity loses an attribute, and total > the order-only range of the total. Entities where the variant or the base
    run is invalid are left out of the gain."""
    t = _found_table(rows, invalid)
    ents = [e for e in t.index]
    rng = order_range(rows, invalid).set_index("ent").loc["all", "range"]
    out = []
    for v in GAIN_VARIANTS:
        if v not in t.columns:
            continue
        d = t[v] - t[base]
        total = float(d.sum())
        ok = total >= GAIN_MIN and bool((d.dropna() >= 0).all()) and total > (0 if np.isnan(rng) else rng)
        why = ("" if ok else "total < %d" % GAIN_MIN if total < GAIN_MIN else "an entity loses one"
               if (d < 0).any() else "within order range")
        out.append({"variant": v, **{e: d[e] for e in ents}, "total_gain": total, "order_range": rng, "counts": ok,
                    "reason": why})
    return pd.DataFrame(out)


# ---- CLI

def main():
    from .v34_data import load_all
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="results/graph_v22_dev50")
    ap.add_argument("--dir32", default="results/loop1_v32")
    ap.add_argument("--dir31", default="results/loop1_v31")
    ap.add_argument("--out", default="results/loop1_v34")
    a = ap.parse_args()
    read = lambda p: pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")  # noqa: E731
    old = [read(Path(d) / "name_rubric.csv") for d in (a.dir32, a.dir31) if (Path(d) / "name_rubric.csv").exists()]
    shared, data = load_all(a.run, a.dir32, a.dir31)
    from .rules_labels import other_gold_values
    from .score_rules import Rules
    extra = {"cluster_labels": {}}
    for ed in data.values():  # default cluster labels with the full other-entity gold values
        extra["cluster_labels"][ed.ent] = importlib.import_module("s1a.rules_labels").cluster_labels(
            ed, Rules.default(), {"other_gold": other_gold_values(shared, ed)})
    sheet = name_sheet(data, pd.concat(old, ignore_index=True) if old else None, extra)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sheet.to_csv(out / "name_sheet.csv", index=False, encoding="utf-8")
    rate = names_to_rate(sheet)
    rate.to_csv(out / "names_to_rate.csv", index=False, encoding="utf-8")
    print(f"name_sheet.csv {len(sheet)} rows, names_to_rate.csv {len(rate)} rows")
    for ed in data.values():
        d = order_diffs(ed)
        counts = d["type"].value_counts().to_dict() if len(d) else {}
        from .score_rules import Rules
        old_a = agreement(ed, Rules.old(), {})
        new_a = agreement(ed, Rules.default(), {})
        print(ed.ent, "order diffs", counts, "| vote agree_mean", ed.vote_stats["agree_mean"],
              "| old", {k: round(v, 3) for k, v in old_a.items()}, "| split", {k: round(v, 3) for k, v in new_a.items()})


if __name__ == "__main__":
    main()
