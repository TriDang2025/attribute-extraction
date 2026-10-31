"""wf_v3.4 label rules (SCORER_V34_CONTRACT.md, W3): Q3 unlabelled mentions, Q1 noise kinds, Q2 cluster-label
thresholds, Q10 role pairs. Pure functions of EntityData (ed) and a Rules-like object (duck typing: unlabeled,
noise_kind, cluster_label); no models. `extra` is a dict: "jury" (DataFrame cluster_id, jury), optional "other_gold"
({normalised value: gold entity} of the other entities; default: derived from ed.mentions)."""

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from . import pilot_score as PS
from .labels import _classes

ROOT = Path(__file__).resolve().parents[1]
ROLE_PAIRS_PATH = "config/role_pairs.json"
THRESHOLDS = {"0.5": 0.5, "0.6": 0.6, "0.7": 0.7}
NOISE_KINDS = ("question", "result_count", "general", "broken")
KINDS = ("question", "result_count", "other_entity", "general", "broken", "odd_format", "other")
SPECIAL = ("unlabeled", "noise", "cue", "wrong_entity")  # not an attribute class: left out of top_attr
FREQUENT_DIALOGUES = 0.20  # other_entity=wrong_entity: a gold value in >= 20% of the dialogues is "frequent"
FREQUENT_ENTITIES = 2      # ... or in >= 2 entities
OLD_LABEL = {"gold": "real", "valid_new": "real", "noise": "noise"}

# closed English lists (no dataset words)
QUESTION_WORDS = ("what", "which", "where", "when", "who", "whom", "whose", "why", "how")
DETERMINERS = ("the", "a", "an", "this", "that", "these", "those", "some", "any", "my", "your", "our", "their", "its",
               "his", "her", "another", "each", "every", "no", "all", "both", "many", "few", "several", "same")
FUNCTION_WORDS = frozenset(DETERMINERS) | frozenset(
    "to of in on at by for from with without and or but nor so if than then as into onto over under about after "
    "before during until up down out off is are was were be been being am do does did has have had will would can "
    "could shall should may might must it i you we they he she me him us them there here not just also very "
    "too only".split())
NUMBER_WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve")
UNITS = ("minutes", "minute", "mins", "min", "hours", "hour", "hrs", "hr", "pounds", "pound", "gbp", "quid", "days",
         "day", "nights", "night", "weeks", "week")

_NUM = r"(?:\d+(?:[.,:]\d+)?|" + "|".join(NUMBER_WORDS) + ")"
_QUESTION = re.compile(r"(?:" + "|".join(QUESTION_WORDS) + r")\b", re.I)
_UNIT = re.compile(rf"{_NUM}\s*(?:{'|'.join(UNITS)})", re.I)
_COUNT = re.compile(rf"(?:there\s+(?:are|is)\s+)?{_NUM}\s+[a-z]+s", re.I)
_GENERAL = re.compile(rf"(?:{'|'.join(DETERMINERS)})(?:\s+[a-z]+){{1,2}}")
_TIME = re.compile(r"\d{1,2}\s?[:.h]\s?\d{2}(?:\s?[ap]m)?|\d{1,2}\s?[ap]m", re.I)
_PRICE = re.compile(r"[£$€]\s?\d+(?:\.\d+)?|\d+(?:\.\d+)?\s?[£$€]")
_NUMBER = re.compile(r"\d+(?:\.\d+)?(?:st|nd|rd|th)?")
_CODE = re.compile(r"[A-Za-z0-9]+(?: ?[A-Za-z0-9]+)?")


def _norm(text):
    return " ".join(str(text).lower().split())


def _words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def _is_question(value):
    return bool(_QUESTION.match(value.strip()))


def _is_result_count(value, turn_text):
    v = value.strip()
    if _UNIT.fullmatch(v):
        return False
    if _COUNT.fullmatch(v):
        return True
    return bool(_NUMBER.fullmatch(v) and re.search(rf"there\s+(?:are|is)\s+(?:\w+\s+)?{re.escape(v)}\b", turn_text, re.I))


def _is_general(value):
    v = value.strip()
    return not re.search(r"\d", v) and v == v.lower() and bool(_GENERAL.fullmatch(v))


def _cuts_word(value, turn_text):
    """True when the span occurs in the turn only inside longer words."""
    v = value.strip()
    hits = list(re.finditer(re.escape(v), turn_text, re.I)) if v and turn_text else []
    if not hits:
        return False
    return not any(not (m.start() and turn_text[m.start() - 1].isalnum())
                   and not (m.end() < len(turn_text) and turn_text[m.end()].isalnum()) for m in hits)


def _is_broken(value, turn_text):
    w = _words(value)
    return bool(w) and (w[0] in FUNCTION_WORDS - set(DETERMINERS) or w[-1] in FUNCTION_WORDS
                        or _cuts_word(value, turn_text))


def _is_odd_format(value):
    v = value.strip()
    code = len(v.replace(" ", "")) >= 4 and _CODE.fullmatch(v) and re.search(r"\d", v) and re.search(r"[A-Za-z]", v)
    return bool(_TIME.fullmatch(v) or _PRICE.fullmatch(v) or _UNIT.fullmatch(v) or _NUMBER.fullmatch(v) or code)


def noise_kinds_matching(value, turn_text, gold_values_other):
    """All kinds (KINDS order; ["other"] when none) whose pattern matches. gold_values_other: set or dict of
    normalised gold values of the other entities."""
    value = str(value)
    tests = {"question": lambda: _is_question(value), "result_count": lambda: _is_result_count(value, turn_text),
             "other_entity": lambda: _norm(value) in gold_values_other, "general": lambda: _is_general(value),
             "broken": lambda: _is_broken(value, turn_text), "odd_format": lambda: _is_odd_format(value)}
    return [k for k in KINDS[:-1] if tests[k]()] or ["other"]


def noise_kind_of(value, turn_text, gold_values_other):
    """Kind of a non-gold value by general patterns (first match in KINDS order):
    question / result_count / other_entity / general / broken / odd_format / other."""
    return noise_kinds_matching(value, turn_text, gold_values_other)[0]


# ---- Q3 / Q1: per-mention class

def other_gold_values(shared, ed):
    """{normalised value: gold entity} of gold values of entities outside ed.gold_ents (own-entity values excluded)."""
    gv = shared.gv
    own = {_norm(v) for v in gv.loc[gv["entity_gold"].isin(ed.gold_ents), "value"]}
    other = gv[~gv["entity_gold"].isin(ed.gold_ents)]
    return {_norm(v): e for v, e in zip(other["value"], other["entity_gold"]) if _norm(v) not in own}


def _other_gold(ed, extra):
    per_ent = (extra or {}).get("_other_gold") or {}  # score_rules caches the full values per entity
    if per_ent.get(ed.ent) is not None:
        return per_ent[ed.ent]
    if extra and extra.get("other_gold") is not None:
        return extra["other_gold"]
    m = ed.mentions
    m = m[(m["gold_attr"] != "") & ~m["entity_gold"].isin(list(ed.gold_ents) + [""])]
    return {_norm(v): e for v, e in zip(m["norm_value"], m["entity_gold"])}


def frequent_values(shared):
    """Set of normalised gold values that are too common to prove another entity: in gold of >= 2 entities, or in >= 20%
    of the dialogues (len(shared.docs))."""
    gv = shared.gv
    norm = gv["value"].map(_norm)
    ents = gv.groupby(norm)["entity_gold"].nunique()
    dialogues = gv.groupby(norm)["dialogue_id"].nunique() / max(len(shared.docs), 1)
    return set(ents[ents >= FREQUENT_ENTITIES].index) | set(dialogues[dialogues >= FREQUENT_DIALOGUES].index)


def _frequent(extra):
    """extra["frequent"] (tests), else computed once from extra["shared"] (cached in extra["_frequent"]), else empty."""
    extra = extra if extra is not None else {}
    if extra.get("frequent") is not None:
        return extra["frequent"]
    if "_frequent" not in extra and extra.get("shared") is not None:
        extra["_frequent"] = frequent_values(extra["shared"])
    return extra.get("_frequent", set())


def _jury_of(extra):
    jury = (extra or {}).get("jury")
    if jury is None:
        raise ValueError("noise_kind=jury needs extra['jury'] (jury.csv)")
    return dict(zip(jury["cluster_id"], jury["jury"]))


def _unlabeled_class(row, rules, other, jury, frequent):
    if rules.noise_kind == "pattern":
        kind = noise_kind_of(row["text"], row["turn_text"], other)
        norm = _norm(row["text"])
        wrong = getattr(rules, "other_entity", "old") == "wrong_entity" and norm not in frequent
        mapped = {"question": "cue", "result_count": "noise", "general": "noise", "broken": "noise",
                  "odd_format": "real_extra",
                  "other_entity": "wrong_entity" if wrong else f"other_entity:{other.get(norm, '')}"}
        if kind in mapped:
            return mapped[kind]
    elif rules.noise_kind == "jury":
        j = jury.get(row["cluster_id"])
        if j in ("noise", "real"):
            return "noise" if j == "noise" else "real_extra"
    return "noise" if rules.unlabeled == "noise" else "unlabeled"


def mention_class(ed, rules, extra):
    """Series indexed by mention_id: gold attr ("A;B" kept) / unlabeled / noise / cue / real_extra /
    other_entity:<Entity> / wrong_entity. Q3: exclude keeps "unlabeled" (the shares leave it out), noise turns it into
    "noise"; Q1 pattern / jury first re-classify the unlabelled mentions. other_entity=wrong_entity turns
    other_entity:<E> into "wrong_entity" unless the value is frequent (frequent_values)."""
    m = ed.mentions
    other = _other_gold(ed, extra) if rules.noise_kind == "pattern" else {}
    frequent = _frequent(extra) if getattr(rules, "other_entity", "old") == "wrong_entity" else set()
    jury = _jury_of(extra) if rules.noise_kind == "jury" else {}
    choice = m["is_choice"] if "is_choice" in m.columns else pd.Series(False, index=m.index)  # T6 (with_level data)
    cls = [g if g else "noise" if ch else _unlabeled_class(r, rules, other, jury, frequent)
           for g, ch, (_, r) in zip(m["gold_attr"], choice, m.iterrows())]
    return pd.Series(cls, index=m["mention_id"].astype(int).values, name="class")


def cue_scores(ed, label, gt_levels):
    """T5: the variant's `attribute_cue` clusters scored against the request flag of gt_levels (is_request per
    mention_id). dict(cue_n = cue clusters, cue_request = cue clusters whose mentions are >= 50% request mentions,
    cue_share = cue_request / cue_n, NaN when there is none)."""
    dec = ed.variants[label].dec
    cues = set(dec.loc[dec["action"] == "attribute_cue", "cluster_id"])
    req = dict(zip(gt_levels["mention_id"].astype(int), gt_levels["is_request"].astype(bool)))
    m = ed.mentions[ed.mentions["cluster_id"].isin(cues)]
    flags = pd.Series([req.get(int(i), False) for i in m["mention_id"]], index=m.index).groupby(m["cluster_id"]).mean()
    hit = int((flags >= 0.5).sum())
    return {"cue_n": len(cues), "cue_request": hit, "cue_share": hit / len(cues) if cues else float("nan")}


# ---- Q2: cluster labels

def _top(attr, n):
    ranked = sorted(attr.items(), key=lambda kv: (-kv[1], kv[0]))[:2] + [("", 0)] * 2
    return [(a, c / n if n else float("nan")) for a, c in ranked[:2]]


def cluster_labels(ed, rules, extra):
    """One row per cluster of the entity: n, n_counted (unlabeled dropped when rules.unlabeled == "exclude"),
    top/second attribute class and share, noise_share (noise + cue), label real/mixed/noise.
    Threshold t from rules.cluster_label: real if top_share >= t, else noise if noise_share >= t, else mixed;
    "old": label from labels.csv (gold, valid_new -> real; noise -> noise; other -> mixed). No counted mention: unknown
    (out of the noise base, counted in the report)."""
    m = ed.mentions.assign(cls=mention_class(ed, rules, extra).values)
    old = dict(zip(ed.labels["cluster_id"], ed.labels["label"]))
    rows = []
    for cid, g in m.groupby("cluster_id", sort=True):
        counted = [c for c in g["cls"] if not (rules.unlabeled == "exclude" and c == "unlabeled")]
        n = len(counted)
        attr = Counter(c for cl in counted for c in _classes(cl) if c not in SPECIAL)
        noise = sum(cl in ("noise", "cue") for cl in counted)
        (a1, s1), (a2, s2) = _top(attr, n)
        ns = noise / n if n else float("nan")
        if rules.cluster_label == "old":
            label = OLD_LABEL.get(old.get(cid, ""), "mixed")
        elif not n:  # every mention left out (unlabeled under exclude): no evidence either way
            label = "unknown"
        else:
            t = THRESHOLDS[rules.cluster_label]
            label = "real" if s1 >= t else "noise" if ns >= t else "mixed"
        rows.append({"cluster_id": cid, "n": len(g), "n_counted": n, "top_attr": a1, "top_share": s1,
                     "second_attr": a2, "second_share": s2, "noise_share": ns, "label": label})
    return pd.DataFrame(rows, columns=["cluster_id", "n", "n_counted", "top_attr", "top_share", "second_attr",
                                       "second_share", "noise_share", "label"])


# ---- report tables

def _mentions_of(data):
    return pd.concat([d.mentions.assign(ent=d.ent) for d in data.values()], ignore_index=True)


def q3_tables(data, seed=0):
    """dict of DataFrames: counts (ent x speaker: n, n_unlabeled, share_unlabeled), cluster_share (per cluster),
    examples (30 random unlabelled mentions, seed 0: 10 per entity, 5 from system turns)."""
    m = _mentions_of(data)
    m = m.assign(unlabeled=m["gold_attr"] == "")
    agg = dict(n=("unlabeled", "size"), n_unlabeled=("unlabeled", "sum"))
    counts = m.groupby(["ent", "speaker"]).agg(**agg).reset_index()
    share = m.groupby(["ent", "cluster_id"]).agg(**agg).reset_index()
    for t in (counts, share):
        t["share_unlabeled"] = t["n_unlabeled"] / t["n"]
    share["old_label"] = share["cluster_id"].map({c: l for d in data.values()
                                                  for c, l in zip(d.labels["cluster_id"], d.labels["label"])})
    parts = []
    for _, g in m[m["unlabeled"]].groupby("ent"):
        for system in (True, False):
            pool = g[(g["speaker"] == "system") == system]
            parts.append(pool.sample(min(5, len(pool)), random_state=seed))
    cols = ["ent", "cluster_id", "mention_id", "speaker", "text", "turn_text", "prev_turn"]
    return {"counts": counts, "cluster_share": share, "examples": pd.concat(parts)[cols].reset_index(drop=True)}


def q1_table(data, shared):
    """dict: values (distinct non-gold values per entity: n, top cluster, 2 example turns, kind, doubtful,
    doubt_reason) and kind_counts (mentions per kind x entity)."""
    rows = []
    for ent, d in data.items():
        other = other_gold_values(shared, d)
        old = d.labels.set_index("cluster_id")["label"]
        u = d.mentions[d.mentions["gold_attr"] == ""]
        for norm, g in u.groupby("norm_value", sort=True):
            kinds = [noise_kinds_matching(t, tt, other) for t, tt in zip(g["text"], g["turn_text"])]
            first = [k[0] for k in kinds]
            kind = Counter(first).most_common(1)[0][0]
            reasons = []
            if len(set(first)) > 1:
                reasons.append("kind varies by turn")
            if len(kinds[first.index(kind)]) > 1:
                reasons.append("matches " + "+".join(kinds[first.index(kind)]))
            if kind in NOISE_KINDS and old.reindex(g["cluster_id"]).eq("gold").all():
                reasons.append("in a gold cluster")
            rows.append({"ent": ent, "value": g["text"].iloc[0], "norm_value": norm, "n": len(g),
                         "cluster_id": g["cluster_id"].mode().iloc[0], "example_1": g["turn_text"].iloc[0],
                         "example_2": g["turn_text"].iloc[min(1, len(g) - 1)], "kind": kind,
                         "doubtful": bool(reasons), "doubt_reason": "; ".join(reasons)})
    values = pd.DataFrame(rows).sort_values(["ent", "n", "norm_value"], ascending=[True, False, True],
                                            ignore_index=True)
    return {"values": values, "kind_counts": values.groupby(["kind", "ent"])["n"].sum().unstack(fill_value=0)
            .reset_index()}


def q2_table(data, settings, extra=None, plot_path=None):
    """Per-cluster shares and labels. settings: {name: Rules-like}; the name "old" is the reference, every other
    name gives a column "label_<name>"; shares come from the first non-old setting. differs_from_old: any non-old
    label differs from the old one. plot_path: PNG of top_share sorted per entity; the outcome (saved / skipped
    when matplotlib is missing) is in the result's attrs["plot"]."""
    names = [n for n in settings if n != "old"]
    frames = []
    for ent, d in data.items():
        ex = dict(extra or {})  # other-entity gold values are per entity (score_rules caches them in "_other_gold")
        ex["other_gold"] = (ex.get("_other_gold") or {}).get(ent, ex.get("other_gold"))
        out = cluster_labels(d, settings[names[0]], ex).drop(columns="label").assign(ent=ent)
        out["label_old"] = cluster_labels(d, settings["old"], ex)["label"].values
        for n in names:
            out[f"label_{n}"] = cluster_labels(d, settings[n], ex)["label"].values
        frames.append(out)
    t = pd.concat(frames, ignore_index=True)
    t["differs_from_old"] = t[[f"label_{n}" for n in names]].ne(t["label_old"], axis=0).any(axis=1)
    t.attrs["plot"] = _plot_top_share(t, plot_path) if plot_path else "no plot requested"
    return t


def _plot_top_share(t, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return "matplotlib missing: plot skipped"
    fig, ax = plt.subplots(figsize=(7, 4))
    for ent, g in t.groupby("ent"):
        ax.plot(range(len(g)), sorted(g["top_share"].fillna(0), reverse=True), label=ent)
    for y in THRESHOLDS.values():
        ax.axhline(y, color="grey", lw=0.6, ls="--")
    ax.set_xlabel("cluster (sorted)")
    ax.set_ylabel("top attribute share")
    ax.legend()
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return f"saved {path}"


# ---- Q10: role pairs

def role_pairs(path=ROLE_PAIRS_PATH, entity=None):
    """[(slot_a, slot_b)] from the config file (a relative path resolves against step1a/); entity (e.g. "train")
    keeps only the pairs that list it."""
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    pairs = json.loads(p.read_text(encoding="utf-8"))["pairs"]
    return [tuple(x["slots"]) for x in pairs if entity is None or entity in x["entities"]]


def _shape(value):
    v = str(value).strip()
    return ("time" if _TIME.fullmatch(v) else "price" if _PRICE.fullmatch(v) else "number" if _NUMBER.fullmatch(v)
            else "code" if _is_odd_format(v) else "text")


def q10_tables(data, jaccard=0.3, path=ROLE_PAIRS_PATH):
    """dict: gold_attrs (attr, entity word, n mentions, n distinct values, shape), role_counts (PS.role_table per
    entity), proposed_pairs (attrs of one entity with value-set Jaccard >= `jaccard` and the same shape; in_config =
    the slot pair is in the config file)."""
    m = _mentions_of(data).drop_duplicates("mention_id")
    sets = {}
    for ga, nv in zip(m["gold_attr"], m["norm_value"]):
        for c in _classes(ga):
            sets.setdefault(c, []).append(nv)
    attrs = pd.DataFrame([{"attr": a, "entity": a.split()[0].lower(), "n": len(v), "n_values": len(set(v)),
                           "shape": Counter(_shape(x) for x in v).most_common(1)[0][0]}
                          for a, v in sorted(sets.items())])
    known = {frozenset(p) for p in role_pairs(path)}
    pairs = []
    for i, a in attrs.iterrows():
        for _, b in attrs.iloc[i + 1:].iterrows():
            if a["entity"] != b["entity"] or a["shape"] != b["shape"]:
                continue
            sa, sb = set(sets[a["attr"]]), set(sets[b["attr"]])
            j = len(sa & sb) / len(sa | sb)
            if j >= jaccard:
                slots = frozenset(x["attr"].split(" ", 1)[1].lower() for x in (a, b))
                pairs.append({"entity": a["entity"], "attr_a": a["attr"], "attr_b": b["attr"], "jaccard": j,
                              "shape": a["shape"], "in_config": slots in known})
    role = pd.concat([PS.role_table(d.mentions, d.entity).assign(ent=d.ent) for d in data.values()], ignore_index=True)
    return {"gold_attrs": attrs, "role_counts": role,
            "proposed_pairs": pd.DataFrame(pairs, columns=["entity", "attr_a", "attr_b", "jaccard", "shape",
                                                           "in_config"])}
