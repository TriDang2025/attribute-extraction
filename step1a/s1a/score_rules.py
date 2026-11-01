"""wf_v3.4 scorer framework (SCORER_V34_CONTRACT.md, W2): one switch per rule (Q1-Q10), the v3.2 columns unchanged.

`score_entity(ed, shared, rules, extra)` returns one row per variant label of the entity: the old columns (OLD_COLS,
the v3.2 scorer with no GLiNER) plus the new columns (NEW_COLS) from the stage-2 modules s1a.rules_labels /
rules_groups / rules_names. Each stage-2 function is looked up lazily; a missing one gives "n/a" in its columns.
A new column copies its old value when the rule that drives it is "old" (COPY_OLD), so the "old" setting
reproduces the v3.2 summary.
"""

import importlib
from dataclasses import dataclass, fields, replace

import numpy as np
import pandas as pd

from . import pilot_score as PS
from . import pilot_verify as PV

OLD_COLS = ["merge_pure", "merge_frag", "split_done", "split_side", "noise_marked", "noise_kept", "place_right",
            "recall_after", "p1_after", "real_acc", "noise_rub", "role_acc"]
NEW_COLS = ["noise_n", "noise_marked_v", "cue_n", "found_n", "gold_n", "recall_v", "merge_n", "merge_right",
            "merge_prec", "place_acc", "place_n", "place_base", "name_right", "name_base", "name_acc", "valid_extra",
            "role_right", "role_base", "agree_groups", "agree_noise", "agree_names", "unknown_n", "merge_unjudged",
            "wrong_entity_n", "names_unrated", "cue_clusters", "cue_request", "cue_share"]
NA = "n/a"

OPTIONS = {"unlabeled": ("old", "exclude", "noise"), "noise_kind": ("old", "pattern", "jury", "mwoz"),
           "cluster_label": ("old", "0.5", "0.6", "0.7"), "role_pairs": ("old", "config"), "names": ("old", "v34", "l2rated"),
           "found": ("old", "cov0", "cov10", "cov25"), "merge": ("old", "n10", "n20", "n30"),
           "placement": ("old", "majority"), "agreement": ("old", "split"), "gt": ("old", "L1", "L2", "L3"),
           "unknown": ("old", "out"), "merge_gold": ("old", "min2"), "marked_found": ("old", "skip"),
           "other_entity": ("old", "wrong_entity")}
DEFAULT = {"unlabeled": "exclude", "noise_kind": "pattern", "cluster_label": "0.6", "role_pairs": "config",
           "names": "v34", "found": "cov10", "merge": "n20", "placement": "majority", "agreement": "split",
           "gt": "L1", "unknown": "out", "merge_gold": "min2", "marked_found": "skip", "other_entity": "wrong_entity"}
NO_SWEEP = ("gt",)  # the GT level changes the data, not the scorer: scripts/score_v35.py sets it per run
# these need level data or rated files that the sweep does not have (scripts/noise_v36.py, scripts/names_l2_v36.py)
NO_SWEEP_VALUES = (("noise_kind", "mwoz"), ("names", "l2rated"))


@dataclass(frozen=True)
class Rules:
    unlabeled: str = "old"      # Q3
    noise_kind: str = "old"     # Q1; mwoz = model-free noise from the GT level (rules_labels.mention_class)
    cluster_label: str = "old"  # Q2
    role_pairs: str = "old"     # Q10
    names: str = "old"          # Q4
    found: str = "old"          # Q5
    merge: str = "old"          # Q6
    placement: str = "old"      # Q9
    agreement: str = "old"      # Q7
    gt: str = "old"             # GT level: old = L1 (the field only; the level is applied to the data by the caller)
    unknown: str = "old"        # out = unknown clusters leave the noise base and merge judging
    merge_gold: str = "old"     # min2 = members without a gold top attr are left out; judge when >= 2 have gold
    marked_found: str = "old"   # skip = a group whose decision is marked cannot be the best group for found
    other_entity: str = "old"   # wrong_entity = other-entity mentions get class wrong_entity (not real, not noise)

    def __post_init__(self):
        for f in fields(self):
            if getattr(self, f.name) not in OPTIONS[f.name]:
                raise ValueError(f"Rules.{f.name}={getattr(self, f.name)!r}: expected one of {OPTIONS[f.name]}")

    @staticmethod
    def old():
        return Rules()

    @staticmethod
    def default():
        return Rules(**DEFAULT)

    @staticmethod
    def parse(setting):
        """"old" | "default" | "default,found=cov25,merge=n10" | "old,unlabeled=exclude"; the first token may be left out."""
        tokens = [t.strip() for t in setting.split(",") if t.strip()]
        rules = Rules.old()
        if tokens and "=" not in tokens[0]:
            base = tokens.pop(0)
            if base not in ("old", "default"):
                raise ValueError(f"unknown base setting {base!r}: expected old or default")
            rules = Rules.default() if base == "default" else Rules.old()
        for t in tokens:
            key, _, value = t.partition("=")
            if key not in OPTIONS or not value:
                raise ValueError(f"bad rule {t!r}: expected <rule>=<option>, rules are {sorted(OPTIONS)}")
            rules = replace(rules, **{key: value})
        return rules


def single_changes():
    """Settings of the sweep: old, default, and default with one rule changed to each other option."""
    out = ["old", "default"]
    for key, options in OPTIONS.items():
        if key in NO_SWEEP:
            continue
        out += [f"default,{key}={o}" for o in options if o != DEFAULT[key] and (key, o) not in NO_SWEEP_VALUES]
    return out


# ---- lazy stage-2 lookup

def _lookup(module, name):
    """Function `name` of `s1a.<module>`, or None when the module or the function does not exist yet."""
    full = f"s1a.{module}"
    try:
        mod = importlib.import_module(full)
    except ModuleNotFoundError as err:
        if err.name != full:
            raise
        return None
    return getattr(mod, name, None)


def _call(module, name, *args):
    fn = _lookup(module, name)
    return None if fn is None else fn(*args)


def load_extra(out_dir, dir32, l2_dir=None):
    """Files read once: old name rubric, jury.csv, rated names sheet (None when absent), role pairs (None until W3).
    l2_dir (names=l2rated): the folder with names_l2_rater{1,2}.csv and names_to_rate_l2_key.csv; "names_l2" is None
    when it is not given or the rated files are absent."""
    def read(path):
        return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8") if path.exists() else None
    return {"old_rubric": read(dir32 / "name_rubric.csv"), "jury": read(out_dir / "jury.csv"),
            "names_rated": read(out_dir / "names_rated.csv"), "role_pairs": _call("rules_labels", "role_pairs"),
            "names_l2": None if l2_dir is None else _call("rules_names", "read_l2_rated", l2_dir)}


# ---- old columns

def _split_label(label):
    variant, tag = label.rsplit(" ", 1)
    return variant, tag


def old_columns(ed, extra):
    """{label: {OLD_COLS}} exactly as pilot_eval_v31.score_entries with no GLiNER (empty verification table)."""
    final = {_split_label(lab): (vo.attrs, vo.assign) for lab, vo in ed.variants.items()}
    names = PS.apply_manual(PS.name_check_table(final, ed.mentions, ed.gold_ents))
    empty = pd.DataFrame(columns=PV.VERIFY_COLS)
    rubric = extra.get("old_rubric")
    acc = {}
    if rubric is not None and len(rubric):
        acc = PS.rubric_accuracy(rubric[rubric["entity"] == ed.entity])
    out = {}
    for lab, vo in ed.variants.items():
        ctx = ed.ctx_a if lab.startswith("A") else ed.ctx_r
        r = PS.score_file(vo.dec, vo.attrs, vo.assign, vo.parts, ctx, empty, names)
        ra = acc.get(_split_label(lab), {})
        row = {k: r.get(k) for k in OLD_COLS}
        row.update(real_acc=ra.get("real_acc"), noise_rub=ra.get("noise_marked"), role_acc=ra.get("role_acc"))
        out[lab] = row
    return out


# ---- new columns

def _share(num, den):
    return num / den if den else float("nan")


def _noise_columns(ed, label, rules, extra):
    """noise base = clusters labelled noise (an unknown cluster is never in it); unknown_n and wrong_entity_n are
    reported under every setting."""
    cl = _call("rules_labels", "cluster_labels", ed, rules, extra)
    mc = _call("rules_labels", "mention_class", ed, rules, extra)
    out = {}
    if cl is not None:
        dec = ed.variants[label].dec.set_index("cluster_id")["action"]
        noise = [c for c in cl.loc[cl["label"] == "noise", "cluster_id"]]
        marked = sum(c in dec.index and dec[c] in PV.MARKED for c in noise)
        out.update(noise_n=len(noise), noise_marked_v=_share(marked, len(noise)),
                   unknown_n=int((cl["label"] == "unknown").sum()))
    if mc is not None:
        out.update(cue_n=int((mc == "cue").sum()), wrong_entity_n=int((mc == "wrong_entity").sum()))
    return out


def _found_columns(ed, label, rules, extra):
    df = _call("rules_groups", "found", ed, label, rules, extra)
    if df is None:
        return {}
    n, total = int(df["found"].astype(int).sum()), len(df)
    return {"found_n": n, "gold_n": total, "recall_v": _share(n, total)}


def _merge_columns(ed, label, rules, extra):
    df = _call("rules_groups", "merges", ed, label, rules, extra)
    if df is None:
        return {}
    judged = df[df["judged"].astype(bool)] if "judged" in df.columns else df
    n, right = len(judged), int(judged["right"].astype(int).sum()) if len(judged) else 0
    return {"merge_n": n, "merge_right": right, "merge_prec": _share(right, n), "merge_unjudged": len(df) - n}


def _place_columns(ed, label, rules, extra):
    return _call("rules_groups", "placement", ed, label, rules, extra) or {}


def _name_columns(ed, label, rules, extra):
    return _call("rules_names", "name_scores", ed, label, rules, extra) or {}


def _cue_columns(ed, label, rules, extra):
    """T5: attribute_cue clusters against the request flag; needs extra["gt_levels"] (gt_levels.csv, bool columns)."""
    gt = extra.get("gt_levels")
    r = None if gt is None else _call("rules_labels", "cue_scores", ed, label, gt)
    return {} if r is None else {"cue_clusters": r["cue_n"], "cue_request": r["cue_request"], "cue_share": r["cue_share"]}


def _agree_columns(ed, label, rules, extra):
    if label != "C s012":
        return {}
    return _call("rules_names", "agreement", ed, rules, extra) or {}


# (function, tuple of rules that must all be "old" for the copy, {new column: old column or callable(ed, old_row)})
GROUPS = [
    (_noise_columns, ("unlabeled", "noise_kind", "cluster_label"), {"noise_marked_v": "noise_marked"}),
    (_found_columns, ("found",), {"recall_v": "recall_after"}),
    (_merge_columns, ("merge",), {"merge_prec": "merge_pure"}),
    (_place_columns, ("placement",), {"place_acc": "place_right"}),
    (_name_columns, ("names",), {"name_acc": "real_acc"}),
    (_cue_columns, ("gt",), {}),
    (_agree_columns, ("agreement",), {c: "agree_mean" for c in ("agree_groups", "agree_noise", "agree_names")}),
]


def new_columns(ed, label, rules, extra, old_row):
    """{NEW_COLS: value} of one variant; "n/a" where the stage-2 function is missing, old value where the rule is old.
    old_row also holds agree_mean (the C vote's mean agreement, set for "C s012" only)."""
    row = dict.fromkeys(NEW_COLS, NA)
    for fn, driving, copies in GROUPS:
        row.update(fn(ed, label, rules, extra))
        if all(getattr(rules, r) == "old" for r in driving):
            # an old rule always shows the old measure; n/a where the old scorer has no value (e.g. A r2, +namemerge)
            row.update({new: NA if old_row.get(src) is None else old_row[src] for new, src in copies.items()})
    return row


def level_entity(ed, rules, extra):
    """`ed` read at the GT level of rules.gt (v34_data.with_level, cached in extra["_level"]); `ed` itself for the old
    setting or when extra holds no "gt_levels" table. The old columns are always scored on the original `ed`."""
    gt = extra.get("gt_levels")
    if rules.gt == "old" or gt is None:
        return ed
    from . import v34_data
    level = int(rules.gt[1])
    cache = extra.setdefault("_level", {})
    key = (id(ed), level)
    if key not in cache:
        cache[key] = (ed, v34_data.with_level({ed.ent: ed}, gt, level)[ed.ent])
    return cache[key][1]


def score_entity(ed, shared, rules, extra):
    """One dict per variant label of the entity: ent, variant, OLD_COLS, NEW_COLS. `shared` goes to the stage-2
    functions as extra["shared"]; the old columns are cached in extra["_old"]. Rules.gt L1-L3 with extra["gt_levels"]
    scores the new columns on the level copy of `ed` (level_entity)."""
    extra.setdefault("shared", shared)
    other = extra.setdefault("_other_gold", {})  # other-entity gold values per entity (rules_labels "other_entity")
    if ed.ent not in other:
        other[ed.ent] = _call("rules_labels", "other_gold_values", shared, ed)
    extra["other_gold"] = other[ed.ent]
    cache = extra.setdefault("_old", {})
    if id(ed) not in cache:
        cache[id(ed)] = old_columns(ed, extra)
    led = level_entity(ed, rules, extra)
    rows = []
    for label in ed.variants:
        old = cache[id(ed)][label]
        new = new_columns(led, label, rules, extra, {**old, "agree_mean": ed.vote_stats.get("agree_mean", NA)}
                          if label == "C s012" else old)
        rows.append({"ent": ed.ent, "variant": label, **old, **new})
    return rows


def fmt_count(k, n):
    """"4/7 (0.571)"; "0/0 (n/a)" when n is 0; "n/a" when k or n is missing."""
    try:
        k, n = float(k), float(n)
    except (TypeError, ValueError):
        return NA
    if np.isnan(k) or np.isnan(n):
        return NA
    return f"{int(k)}/{int(n)} ({k / n:.3f})" if n else f"{int(k)}/0 ({NA})"


def pooled_noise(rows):
    """dict(marked, n, share) of one variant over its entity rows (noise_marked_v x noise_n, rounded back to a count);
    rows without numbers are skipped. share is NaN when n is 0."""
    marked = n = 0
    for r in pd.DataFrame(rows).to_dict("records"):
        try:
            size, share = float(r["noise_n"]), float(r["noise_marked_v"])
        except (TypeError, ValueError):
            continue
        if np.isnan(size) or np.isnan(share):
            continue
        n += int(size)
        marked += int(round(share * size))
    return {"marked": marked, "n": n, "share": marked / n if n else float("nan")}


def fmt(v, count=False):
    """Cell text: n/a for missing, PS._fmt for numbers, strings as they are."""
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return NA
    return PS._fmt(float(v), count)
