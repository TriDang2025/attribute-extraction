"""wf_v3.6 W3, part 4 (GT_V36_CONTRACT.md): noise with the L2 ground truth. No models, no LLM.

- Task 13: the mentions with no MultiWOZ match, grouped by kind (value-shape rules first, then closed word lists,
  then "other"), and the sheet that lets a Haiku pass split "other".
- Task 14: the model-free noise set (Rules.noise_kind = "mwoz", see rules_labels._mwoz_classes) at L2 against the
  rules v1 default at L1, with the clusters that changed and why.
- Task 15: noise at L2 per variant (noise marked, precision of the marks, real clusters marked), over any
  {ent: EntityData} bundles, so the v3.6 batch decisions use the same function.
"""

import re
from collections import Counter
from dataclasses import replace

import pandas as pd

from . import pilot_verify as PV
from . import rules_labels as RL
from . import score_rules as SR
from .score_rules import fmt_count

# ---- Task 13: kinds of unmatched mentions

_TIME = re.compile(r"(?:\d{1,2}\s?[:.h]\s?\d{2}|\d{1,2}\s?[ap]\.?m\.?)(?:\s?[ap]m)?", re.I)
_PRICE = re.compile(r"[£$€]\s?\d+(?:\.\d+)?|\d+(?:\.\d+)?\s?(?:[£$€]|gbp|pounds?)", re.I)
_PHONE = re.compile(r"(?:\+?\d[\d ]{8,13}\d)")
_POSTCODE = re.compile(r"[a-z]{1,2}\d{1,2}\s?\d[a-z]{2}", re.I)
_REF = re.compile(r"(?=[a-z0-9]*\d)(?=[a-z0-9]*[a-z])[a-z0-9]{4,}", re.I)
_NUMBER = re.compile(r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)(?:st|nd|rd|th)?"
                     r"(?:\s(?:minutes?|mins?|hours?|days?|nights?|people|tickets?))?", re.I)
_DAY = re.compile(r"(?:mon|tues?|wednes|thurs?|fri|satur|sun)day|today|tomorrow", re.I)
YES_NO = frozenset("yes no ok okay thanks thank sure please great fine yeah yep nope bye goodbye hello hi".split())
BOOKING = frozenset("book booked booking bookings reserve reserved reservation reservations table tables room rooms "
                    "ticket tickets seats seat reference".split())
CHOICE = frozenset("both either any anything another other others neither whichever some all".split())
REQUEST_FIRST = frozenset("what which where when who whose whom why how".split())
REQUEST_LAST = frozenset("number address postcode price fee cost phone".split())
GENERIC_FIRST = frozenset("the a an this that these those it they them one your their its my our".split())
GENERIC_NOUNS = frozenset("restaurant restaurants hotel hotels guesthouse guesthouses train trains taxi station town city "
                          "place places venue area side part night nights day days date time".split())
UNMATCHED_KINDS = ("time", "number", "price", "ref code", "phone", "postcode", "day", "yes/no/ok/thanks",
                   "booking word", "choice word", "request word", "pronoun/generic noun", "other")


def _tokens(text):
    return re.findall(r"[a-z0-9']+", str(text).lower())


def unmatched_kind(text):
    """Kind of an unmatched mention by its text alone. Order: value shapes (time, price, phone, postcode, number, day,
    ref code), then word lists (yes/no, booking, choice, request, pronoun/generic noun), else "other". A request
    phrase starts with a wh-word / "how" (checked before the booking words) or ends with a slot noun ("their phone
    number", "total fee"; checked after them)."""
    v = str(text).strip()
    w = _tokens(v)
    shapes = (("time", _TIME), ("price", _PRICE), ("phone", _PHONE), ("postcode", _POSTCODE), ("number", _NUMBER),
              ("day", _DAY), ("ref code", _REF))
    for kind, rx in shapes:
        if rx.fullmatch(v):
            return kind
    if w and all(t in YES_NO for t in w):
        return "yes/no/ok/thanks"
    if w and w[0] in REQUEST_FIRST:  # "how many seats" is a request, not a booking word
        return "request word"
    if w and any(t in BOOKING for t in w) and len(w) <= 3:
        return "booking word"
    if w and w[0] in CHOICE:
        return "choice word"
    if w and w[-1] in REQUEST_LAST:
        return "request word"
    if w and (w[0] in GENERIC_FIRST or all(t in GENERIC_NOUNS or t in GENERIC_FIRST for t in w)):
        return "pronoun/generic noun"
    return "other"


def mark_value(turn_text, text):
    """turn_text with the first case-insensitive occurrence of `text` wrapped in [[ ]] (the text is appended when it
    does not occur: a fuzzy turn match can move it)."""
    i = turn_text.lower().find(str(text).lower())
    if i < 0:
        return f"{turn_text} [[{text}]]"
    return f"{turn_text[:i]}[[{turn_text[i:i + len(text)]}]]{turn_text[i + len(text):]}"


def unmatched_table(mentions, matched, turn_text):
    """One row per mention with match == "none": mention_id, dialogue_id, turn, speaker, text, kind, turn_marked.
    `mentions`: mentions.csv rows (mention_id, dialogue_id, turn, text); `matched`: mwoz_match.csv; `turn_text`:
    callable (dialogue_id, turn) -> (speaker, flattened turn text)."""
    ids = set(matched.loc[matched["match"] == "none", "mention_id"].astype(int))
    rows = []
    for r in mentions[mentions["mention_id"].astype(int).isin(ids)].to_dict("records"):
        speaker, text = turn_text(r["dialogue_id"], int(r["turn"]))
        rows.append({"mention_id": int(r["mention_id"]), "dialogue_id": r["dialogue_id"], "turn": int(r["turn"]),
                     "speaker": speaker, "text": r["text"], "kind": unmatched_kind(r["text"]),
                     "turn_marked": mark_value(text, r["text"])})
    return pd.DataFrame(rows, columns=["mention_id", "dialogue_id", "turn", "speaker", "text", "kind", "turn_marked"])


def unmatched_summary(df, examples=2):
    """One row per kind (UNMATCHED_KINDS order, empty kinds kept): kind, n, share, example_1, example_2 (turns with the
    value in [[ ]]; distinct values first, then in mention order)."""
    rows = []
    for kind in UNMATCHED_KINDS:
        g = df[df["kind"] == kind].sort_values("mention_id")
        distinct = list(g.assign(low=g["text"].str.lower()).drop_duplicates("low")["turn_marked"])
        ex = distinct + [t for t in g["turn_marked"] if t not in distinct]
        rows.append({"kind": kind, "n": len(g), "share": len(g) / len(df) if len(df) else float("nan"),
                     **{f"example_{i + 1}": ex[i] if i < len(ex) else "" for i in range(examples)}})
    return pd.DataFrame(rows)


def other_sheet(df):
    """The rows of kind "other" for a Haiku pass: row, mention_id, text, turn_marked."""
    o = df[df["kind"] == "other"].sort_values("mention_id").reset_index(drop=True)
    return pd.DataFrame({"row": range(len(o)), "mention_id": o["mention_id"], "text": o["text"],
                         "turn_marked": o["turn_marked"]})


# ---- Task 14: model-free noise set

def mwoz_rules(level=2):
    """Rules v1 with the model-free noise (noise_kind=mwoz) at GT level `level`."""
    return replace(SR.Rules.default(), noise_kind="mwoz", gt=f"L{level}")


def _cluster_info(ed, rules, extra):
    """(cluster_labels DataFrame, {cluster_id: Counter of mention classes}) of `ed` read at rules.gt."""
    led = SR.level_entity(ed, rules, extra)
    cl = RL.cluster_labels(led, rules, extra).set_index("cluster_id")
    cls = RL.mention_class(led, rules, extra)
    named = (*RL.SPECIAL, "real_extra")
    kinds = {c: Counter(x if x in named or x.startswith("other_entity") else "labelled"
                        for x in cls.reindex(g["mention_id"].astype(int)))
             for c, g in led.mentions.groupby("cluster_id")}
    return cl, kinds


def noise_sets(data, extra):
    """One row per cluster of every entity of `data`: ent, cluster_id, n, label_L1 (rules v1 default at L1),
    label_L2 (the same rules at L2), label_mwoz (noise_kind=mwoz at L2), noise_L1 / noise_mwoz (label == noise),
    changed (the two noise flags differ), why (class counts under both rules), top_values. extra must hold
    "gt_levels" and the per-entity "_other_gold" (noise_v36.prepare_extra)."""
    base = SR.Rules.default()
    rows = []
    for ent, ed in data.items():
        l1, k1 = _cluster_info(ed, replace(base, gt="L1"), extra)
        l2, k2 = _cluster_info(ed, replace(base, gt="L2"), extra)
        mw, km = _cluster_info(ed, mwoz_rules(2), extra)
        top = ed.mentions.groupby("cluster_id")["norm_value"].agg(lambda s: "|".join(v for v, _ in Counter(s).most_common(4)))
        for cid in l1.index:
            n1, nm = l1.loc[cid, "label"] == "noise", mw.loc[cid, "label"] == "noise"
            why = ""
            if n1 != nm:
                fmt = lambda c: ", ".join(f"{k} {v}" for k, v in sorted(c.items()))  # noqa: E731
                why = (f"L1 default: noise share {l1.loc[cid, 'noise_share']:.2f} ({fmt(k1[cid])}); "
                       f"mwoz L2: noise share {mw.loc[cid, 'noise_share']:.2f} ({fmt(km[cid])})")
            rows.append({"ent": ent, "cluster_id": cid, "n": int(mw.loc[cid, "n"]), "label_L1": l1.loc[cid, "label"],
                         "label_L2": l2.loc[cid, "label"], "label_mwoz": mw.loc[cid, "label"], "noise_L1": n1,
                         "noise_mwoz": nm, "changed": n1 != nm, "why": why, "top_values": top.get(cid, "")})
    return pd.DataFrame(rows)


def noise_sets_md(df):
    lines = ["# wf_v3.6 model-free noise at L2 (noise_kind=mwoz)", "",
             "A mention is noise iff it is a choice mention, or it has no label at the level and is not a request "
             "mention (a question phrase in a turn with a request act for the cluster's domain). A request mention "
             "with no label is neither noise nor an attribute. A cluster is noise when >= 60% of its counted mentions "
             "are noise (Q2 rule). Compared with the rules v1 default at L1 (pattern noise kinds; labels = TEAR "
             "gold); label_L2 = the same default rules on L2 labels.", "",
             "| entity | clusters | noise L1 default | noise L2 default | noise L2 mwoz | changed (mwoz vs L1) |",
             "|---|---|---|---|---|---|"]
    for ent, g in list(df.groupby("ent", sort=False)) + [("all", df)]:
        lines.append(f"| {ent} | {len(g)} | {int(g['noise_L1'].sum())} | {int((g['label_L2'] == 'noise').sum())} | "
                     f"{int(g['noise_mwoz'].sum())} | {int(g['changed'].sum())} |")
    ch = df[df["changed"]]
    lines += ["", f"## Clusters that changed ({len(ch)})", "",
              "| ent | cluster | n | L1 | mwoz | top values | why |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {r['ent']} | {r['cluster_id']} | {r['n']} | {r['label_L1']} | {r['label_mwoz']} | "
              f"{r['top_values']} | {r['why']} |" for _, r in ch.iterrows()]
    return "\n".join(lines) + "\n"


# ---- Task 15: noise at L2 for every variant

L2_COLS = ["variant", "ent", "noise_n", "noise_marked", "marked_n", "marked_noise", "marked_real", "marked_mixed"]


def noise_l2_rows(data, extra, variants, invalid=(), rules=None):
    """One row per (variant label in `variants`, entity) of an {ent: EntityData} bundle, scored with the mwoz noise set
    at L2: noise_n (noise clusters), noise_marked (of them marked, i.e. action in PV.MARKED), marked_n (clusters
    marked), marked_noise / marked_real / marked_mixed (marked clusters by label). `invalid`: [{ent, variant}] left
    out (config/invalid_runs*.json). Call it once per bundle (v3.2 data, v3.3 data, later the v3.6 batch)."""
    rules = rules or mwoz_rules(2)
    skip = {(r["ent"], r["variant"]) for r in invalid}
    rows = []
    for ent, ed in data.items():
        cl = RL.cluster_labels(SR.level_entity(ed, rules, extra), rules, extra)
        label = dict(zip(cl["cluster_id"], cl["label"]))
        for v in variants:
            if v not in ed.variants or (ent, v) in skip:
                continue
            dec = ed.variants[v].dec
            marked = {c for c in dec.loc[dec["action"].isin(PV.MARKED), "cluster_id"] if c in label}
            by = Counter(label[c] for c in marked)
            noise = {c for c, lab in label.items() if lab == "noise"}
            rows.append({"variant": v, "ent": ent, "noise_n": len(noise), "noise_marked": len(noise & marked),
                         "marked_n": len(marked), "marked_noise": by["noise"], "marked_real": by["real"],
                         "marked_mixed": by["mixed"]})
    return pd.DataFrame(rows, columns=L2_COLS)


def noise_l2_table(rows):
    """Pooled over entities, one row per variant (order of first appearance): the counts of L2_COLS summed, plus
    noise_marked_kn and precision_kn ("k/n (share)")."""
    out = []
    for v, g in rows.groupby("variant", sort=False):
        s = g[["noise_n", "noise_marked", "marked_n", "marked_noise", "marked_real", "marked_mixed"]].sum()
        out.append({"variant": v, "noise_marked_kn": fmt_count(s["noise_marked"], s["noise_n"]),
                    "precision_kn": fmt_count(s["marked_noise"], s["marked_n"]), **{c: int(s[c]) for c in s.index}})
    return pd.DataFrame(out)


def noise_l2_md(table, invalid=()):
    lines = ["# wf_v3.6 noise at L2 (model-free noise set)", "",
             "Noise clusters = clusters with >= 60% noise mentions under noise_kind=mwoz at L2 (see noise_mwoz.md). "
             "Marked = decision not_attribute / unsure / attribute_cue. Pooled over the 3 entities. noise marked = "
             "noise clusters that are marked; precision = marked clusters that are noise; real marked = marked "
             "clusters labelled real (an attribute at L2); mixed marked = marked clusters labelled mixed (neither).",
             ""]
    if invalid:
        lines += ["Left out (invalid runs): " + "; ".join(f"{r['ent']} {r['variant']}" for r in invalid), ""]
    lines += ["| variant | noise marked | precision of marks | real marked as noise | mixed marked |",
              "|---|---|---|---|---|"]
    lines += [f"| {r['variant']} | {r['noise_marked_kn']} | {r['precision_kn']} | {r['marked_real']} | {r['marked_mixed']} |"
              for _, r in table.iterrows()]
    return "\n".join(lines) + "\n"


def prepare_extra(shared, data, out_dir, dir32, l2_dir=None, gt_levels=None):
    """The `extra` dict of a scoring run: files of SR.load_extra, shared, per-entity other-entity gold values (for
    every bundle in `data`, a list of {ent: EntityData}) and the GT levels table (v34_data.read_gt_levels)."""
    extra = SR.load_extra(out_dir, dir32, l2_dir)
    extra["shared"] = shared
    extra["gt_levels"] = gt_levels
    other = {}
    for bundle in data:
        for ent, ed in bundle.items():
            other.setdefault(ent, RL.other_gold_values(shared, ed))
    extra["_other_gold"] = other
    return extra
