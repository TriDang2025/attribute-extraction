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
            "role_right", "role_base", "agree_groups", "agree_noise", "agree_names"]
NA = "n/a"

OPTIONS = {"unlabeled": ("old", "exclude", "noise"), "noise_kind": ("old", "pattern", "jury"),
           "cluster_label": ("old", "0.5", "0.6", "0.7"), "role_pairs": ("old", "config"), "names": ("old", "v34"),
           "found": ("old", "cov0", "cov10", "cov25"), "merge": ("old", "n10", "n20", "n30"),
           "placement": ("old", "majority"), "agreement": ("old", "split")}
DEFAULT = {"unlabeled": "exclude", "noise_kind": "pattern", "cluster_label": "0.6", "role_pairs": "config",
           "names": "v34", "found": "cov10", "merge": "n20", "placement": "majority", "agreement": "split"}


@dataclass(frozen=True)
class Rules:
    unlabeled: str = "old"      # Q3
    noise_kind: str = "old"     # Q1
    cluster_label: str = "old"  # Q2
    role_pairs: str = "old"     # Q10
    names: str = "old"          # Q4
    found: str = "old"          # Q5
    merge: str = "old"          # Q6
    placement: str = "old"      # Q9
    agreement: str = "old"      # Q7

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
        out += [f"default,{key}={o}" for o in options if o != DEFAULT[key]]
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


def load_extra(out_dir, dir32):
    """Files read once: old name rubric, jury.csv, rated names sheet (None when absent), role pairs (None until W3)."""
    def read(path):
        return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8") if path.exists() else None
    return {"old_rubric": read(dir32 / "name_rubric.csv"), "jury": read(out_dir / "jury.csv"),
            "names_rated": read(out_dir / "names_rated.csv"), "role_pairs": _call("rules_labels", "role_pairs")}


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
    cl = _call("rules_labels", "cluster_labels", ed, rules, extra)
    mc = _call("rules_labels", "mention_class", ed, rules, extra)
    out = {}
    if cl is not None:
        dec = ed.variants[label].dec.set_index("cluster_id")["action"]
        noise = [c for c in cl.loc[cl["label"] == "noise", "cluster_id"]]
        marked = sum(c in dec.index and dec[c] in PV.MARKED for c in noise)
        out.update(noise_n=len(noise), noise_marked_v=_share(marked, len(noise)))
    if mc is not None:
        out["cue_n"] = int((mc == "cue").sum())
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
    n, right = len(df), int(df["right"].astype(int).sum()) if len(df) else 0
    return {"merge_n": n, "merge_right": right, "merge_prec": _share(right, n)}


def _place_columns(ed, label, rules, extra):
    return _call("rules_groups", "placement", ed, label, rules, extra) or {}


def _name_columns(ed, label, rules, extra):
    return _call("rules_names", "name_scores", ed, label, rules, extra) or {}


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


def score_entity(ed, shared, rules, extra):
    """One dict per variant label of the entity: ent, variant, OLD_COLS, NEW_COLS. `shared` goes to the stage-2
    functions as extra["shared"]; the old columns are cached in extra["_old"]."""
    extra.setdefault("shared", shared)
    other = extra.setdefault("_other_gold", {})  # other-entity gold values per entity (rules_labels "other_entity")
    if ed.ent not in other:
        other[ed.ent] = _call("rules_labels", "other_gold_values", shared, ed)
    extra["other_gold"] = other[ed.ent]
    cache = extra.setdefault("_old", {})
    if ed.ent not in cache:
        cache[ed.ent] = old_columns(ed, extra)
    rows = []
    for label in ed.variants:
        old = cache[ed.ent][label]
        new = new_columns(ed, label, rules, extra, {**old, "agree_mean": ed.vote_stats.get("agree_mean", NA)}
                          if label == "C s012" else old)
        rows.append({"ent": ed.ent, "variant": label, **old, **new})
    return rows


def fmt(v, count=False):
    """Cell text: n/a for missing, PS._fmt for numbers, strings as they are."""
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return NA
    return PS._fmt(float(v), count)
