"""wf_v3.7 T11 (prep): score the LLM-only baseline against the L2 slots (WF_V37_CONTRACT.md, W3). No LLM, no model.

Flow: responses (`baseline_<ent>_<set>_<v>.jsonl`) -> `attribute_lists` -> `rating_sheet` (blind: one row per (set, ent,
version, name), shuffled; the slot shown is the lexically closest L2 base slot, `candidate_slot`) -> raters answer
right / partly / wrong (names_l2_rubric.md) -> `read_ratings` -> `score_rows` / `table`.

Counts per (set, version) or the union of the versions of a set, summed over the entities:
- right: L2 base attributes covered by a name rated right (k of the base size);
- partly: names rated partly;
- wrong_attr: names rated wrong whose candidate slot shares a word with them (they look like a slot but mean something
  else); extras_no_gt: names rated wrong that share no word with any slot (no GT slot at all);
- no_support: names (any label) with no value in the set's dialogues of the entity (`supported`);
- columns: distinct normalised names.
The lexical candidate is a limit: a name that fits another slot than its candidate is rated against the wrong slot.
"""

import re

import pandas as pd

from . import llm_cache as LC
from . import names_l2 as NL
from . import shapes
from .pilot_verify import norm_name

LABEL_RANK = {"right": 2, "partly": 1, "wrong": 0}
STOP = {"the", "of", "a", "an", "for", "to", "in", "is", "and", "or", "that", "this", "by", "at", "on", "with", "as", "it",
        "its", "be", "s"}
WORD_ALIAS = {"arriveby": "arrival", "leaveat": "departure", "pricerange": "price range", "bookpeople": "people",
              "bookday": "day", "bookstay": "stay", "booktime": "time", "ref": "reference", "trainid": "train id"}
TYPED = {"phone": "phone", "telephone": "phone", "postcode": "postcode", "postal": "postcode", "zip": "postcode",
         "reference": "ref", "confirmation": "ref", "booking": "ref", "price": "price", "cost": "price", "fare": "price",
         "trainid": "train", "train": "train"}
ROW_COLS = ["row", "set", "ent", "version", "name", "description", "l2_attr", "overlap"]


def words(text):
    """Lowercase alphanumeric words of `text` (snake_case and camelCase split), minus stop words."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(text or ""))
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def _stem(w):
    return w[:5]


def _stems(text):
    return {_stem(w) for w in words(text)}


def slot_words(attr, slot, desc):
    """Word stems of an L2 slot: its attribute name, slot name (aliases expanded) and schema description."""
    parts = [attr, desc] + [WORD_ALIAS.get(p, p) for p in slot.split("-")[1:]]
    return set().union(*(_stems(p) for p in parts))


def _bigrams(s):
    s = re.sub(r"[^a-z]", "", s.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def candidate_slot(name, description, slots):
    """(attr, overlap): the L2 base attr whose words overlap most with the name and its description. `slots`:
    {attr: (slot, schema description)}. Score = 2 x shared stems of name and the attr / slot names + shared stems of
    name and description with the slot words; ties go to the closer slot name (character bigrams), then the attr name.
    overlap = shared stems of the name itself and the winner's slot words (0 = nothing in common)."""
    mine, mine_all = _stems(name), _stems(name) | _stems(description)

    def score(attr):
        slot, desc = slots[attr]
        short = slot.split("-", 1)[-1]
        b, c = _bigrams(name), _bigrams(short)
        return (len(mine & (_stems(attr) | _stems(short))) * 2 + len(mine_all & slot_words(attr, slot, desc)),
                len(b & c) / max(1, len(b | c)))

    best = sorted(slots, key=lambda a: (-score(a)[0], -score(a)[1], a))[0]
    return best, len(mine & slot_words(best, *slots[best]))


def attribute_lists(responses):
    """({(set, ent, version): [{name, description}]}, notes) from `responses` {(set, ent, version): raw text} (the last
    row of each response file). A response that does not parse gives no list and a note; duplicate names are dropped."""
    out, notes = {}, []
    for key, raw in sorted(responses.items()):
        obj, errs = LC.parse_baseline(raw)
        if errs:
            notes.append(f"{'/'.join(key)}: {errs[0]}")
            continue
        seen, atts = set(), []
        for a in obj["attributes"]:
            n = norm_name(a["name"])
            if n and n not in seen:
                seen.add(n)
                atts.append({"name": a["name"], "description": a["description"]})
        out[key] = atts
    return out, notes


def rating_sheet(lists, slots_by_ent, seed=NL.SEED):
    """(rater, key): the blind rater copy (NL.RATER_COLS) and the key (ROW_COLS), one row per (set, ent, version, name),
    shuffled with `seed`; the rater copy has no set, version or overlap. `slots_by_ent`: {ent: {attr: (slot, schema
    description)}} of the L2 base."""
    rows = []
    for (s, ent, v), atts in sorted(lists.items()):
        for a in atts:
            attr, ov = candidate_slot(a["name"], a["description"], slots_by_ent[ent])
            rows.append({"set": s, "ent": ent, "version": v, "name": a["name"], "description": a["description"],
                         "l2_attr": attr, "overlap": ov})
    key = pd.DataFrame(rows, columns=ROW_COLS[1:]).sample(frac=1, random_state=seed, ignore_index=True)
    key.insert(0, "row", range(len(key)))
    slot = [slots_by_ent[e][a][0] for e, a in zip(key["ent"], key["l2_attr"])]
    desc = [slots_by_ent[e][a][1] for e, a in zip(key["ent"], key["l2_attr"])]
    rater = pd.DataFrame({"row": key["row"], "ent": key["ent"], "group_name": key["name"],
                          "group_description": key["description"], "top_values": "", "l2_attr": key["l2_attr"],
                          "l2_slot": slot, "l2_slot_description": desc})[NL.RATER_COLS]
    return rater, key[ROW_COLS]


def read_ratings(frames):
    """{row (str): label}: `frames` are DataFrames (row, label), one per rater; the lower label wins. Unknown label:
    ValueError."""
    out = {}
    for df in frames:
        for r, lab in zip(df["row"].astype(str), df["label"].astype(str).str.strip().str.lower()):
            if lab not in LABEL_RANK:
                raise ValueError(f"unknown label {lab!r}, expected one of {tuple(LABEL_RANK)}")
            if r not in out or LABEL_RANK[lab] < LABEL_RANK[out[r]]:
                out[r] = lab
    return out


def dialogue_kinds_turns(texts):
    """(kinds, turns): shape kinds (`shapes.kind`) found among the whitespace tokens of `texts` (turn strings) and, per
    turn, the set of word stems."""
    kinds, turns = set(), []
    for t in texts:
        kinds |= {k for k in (shapes.kind(x.strip(".,;:!?()")) for x in t.split()) if k}
        turns.append(_stems(t))
    return kinds, turns


def supported(name, attr, label, l2_attrs, turns, kinds):
    """Does the set's dialogues of the entity hold a value for the listed attribute?
    - rated right / partly: its L2 slot (`attr`) has at least one L2 span there (`l2_attrs`: attrs with a span);
    - rated wrong (no GT slot): (a) a typed value: the name has a type word (TYPED: phone, postcode, reference, price,
      train id) and a token of that shape is in the dialogues (`kinds`), or (b) one turn holds every content word of the
      name, first 5 letters of each (`turns`: a set of word stems per turn)."""
    if label in ("right", "partly"):
        return attr in l2_attrs
    if any(TYPED.get(w) in kinds for w in words(name)):
        return True
    need = _stems(name)
    return bool(need) and any(need <= t for t in turns)


def merge_union(g):
    """Union of the versions of one (set, ent): rows grouped by normalised name; the best label wins, then the lower row."""
    g = g.assign(_n=[norm_name(x) for x in g["name"]], _r=[LABEL_RANK.get(x, -1) for x in g["label"]])
    return g.sort_values(["_r", "row"], ascending=[False, True]).drop_duplicates("_n").drop(columns=["_n", "_r"])


def score_rows(key, labels, base, spans_by, ctx_by):
    """DataFrame, one row per (set, ent, version or "union"): right, base_n, partly, wrong_attr, extras_no_gt, no_support,
    columns, unrated. key: rating_sheet key; labels: {row: label}; base: {ent: [attrs]}; spans_by: {(set, ent): set of
    attrs with an L2 span}; ctx_by: {(set, ent): (kinds, turns)}. Unrated rows count in columns and unrated only."""
    key = key.assign(label=[labels.get(str(r)) for r in key["row"]])
    groups = [((s, e, v), g) for (s, e, v), g in key.groupby(["set", "ent", "version"])]
    groups += [((s, e, "union"), merge_union(g)) for (s, e), g in key.groupby(["set", "ent"])]
    out = []
    for (s, e, v), g in groups:
        done = g[g["label"].notna()]
        right = {a for a, lab in zip(done["l2_attr"], done["label"]) if lab == "right" and a in base[e]}
        wrong = done[done["label"] == "wrong"]
        kinds, turns = ctx_by[(s, e)]
        nosup = sum(not supported(r.name, r.l2_attr, r.label, spans_by[(s, e)], turns, kinds) for r in done.itertuples())
        out.append({"set": s, "ent": e, "version": v, "right": len(right), "base_n": len(base[e]),
                    "partly": int((done["label"] == "partly").sum()),
                    "wrong_attr": int((wrong["overlap"] > 0).sum()), "extras_no_gt": int((wrong["overlap"] == 0).sum()),
                    "no_support": nosup, "columns": len(g), "unrated": int(g["label"].isna().sum())})
    return pd.DataFrame(out)


def table(scores):
    """(totals, md): `scores` (score_rows) summed over the entities per (set, version), and a markdown table."""
    cols = ["right", "base_n", "partly", "wrong_attr", "extras_no_gt", "no_support", "columns", "unrated"]
    tot = scores.groupby(["set", "version"], sort=True)[cols].sum().reset_index()
    lines = ["| set | version | right names | partly | wrong attributes | extras with no GT | no support | columns | unrated |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in tot.itertuples():
        lines.append(f"| {r.set} | {r.version} | {r.right}/{r.base_n} ({r.right / max(1, r.base_n):.3f}) | {r.partly} | "
                     f"{r.wrong_attr} | {r.extras_no_gt} | {r.no_support} | {r.columns} | {r.unrated} |")
    return tot, "\n".join(lines)


def a_reference(all_variants, variants, setting="v1.1", level=2):
    """DataFrame (variant, right, base_n, found, gold_n) of A at `level` from all_variants_v36.csv (a DataFrame), summed
    over the entities: right names (names L2 rated) and found attributes. The file has no counts of partly names, extras,
    no-support names or columns for A."""
    d = all_variants[(all_variants["setting"] == setting) & (all_variants["level"].astype(int) == level)]
    rows = []
    for v in variants:
        g = d[d["variant"] == v]
        if len(g):
            num = lambda c: int(g[c].astype(float).sum())  # noqa: E731
            rows.append({"variant": v, "right": num("name_right_l2rated"), "base_n": num("name_base_l2rated"),
                         "found": num("found_n"), "gold_n": num("gold_n")})
    return pd.DataFrame(rows, columns=["variant", "right", "base_n", "found", "gold_n"])
