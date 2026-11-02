"""wf_v3.5 extended ground truth (GT_V35_CONTRACT.md, W1): MultiWOZ 2.2 span labels, matching to dev50 mentions,
GT levels L1 (TEAR gold) / L2 (MultiWOZ schema slot) / L3 (MultiWOZ DB column), coverage tables. No LLM, no models.

Only pure functions here; the CLIs (scripts/multiwoz_span_labels.py, scripts/gt_v35.py) do the file IO.
"""

import difflib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

SPAN_COLS = ["dialogue_id", "turn", "speaker", "utterance", "char_start", "char_end", "value", "domain", "slot", "act",
             "source"]
MATCH_COLS = ["mention_id", "dialogue_id", "turn", "mw_turn", "text_match", "mw_domain", "mw_slot", "mw_act", "match",
              "request_slots"]
LEVEL_COLS = ["mention_id", "gt_L1", "gt_L2", "gt_L3", "ent_L1", "ent_L2", "ent_L3", "is_request", "request_slot",
              "is_choice"]
ENTITY_DOMAIN = {"E0": "hotel", "E1": "train", "E2": "restaurant"}  # v3.4 EntityData: train E1, hotel E0, restaurant E2
FUZZY_MIN = 0.8
OVERLAP_MIN = 0.5
COMMON_SHARE = 0.3  # DB column skipped when the value is in more than this share of rows
SKIP_COLUMNS = ("id", "location")
COLUMN_WORDS = {"pricerange": "price range", "leaveat": "leave at", "arriveby": "arrive by"}
WH_WORDS = {"what", "which", "where", "when", "who", "whom", "whose", "how"}
_QUESTION_PHRASE = re.compile(r"^(what|which|where|when|who|whom|whose|how)\b")
_RANK = {"slot": 0, "act_span": 1}


def norm(s):
    """Lowercase, whitespace collapsed, stripped."""
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def norm_value(s):
    """norm() without edge punctuation (for value equality)."""
    return re.sub(r"^\W+|\W+$", "", norm(s))


def dialogue_key(dialogue_id):
    return str(dialogue_id).removesuffix(".json")


# ---------- T1: span rows of one MultiWOZ 2.2 dialogue ----------

def spans_from_dialogue(dialogue, acts):
    """Rows (dicts with SPAN_COLS) of one dialogue. `acts` = dialog_acts.json[dialogue_id] ({turn_id: {dialog_act, span_info}})."""
    rows, seen = [], set()

    def add(turn, speaker, utt, start, end, value, domain, slot, act, source):
        key = (turn, start, end, domain, slot) if start is not None else (turn, domain, slot, "request")
        if key in seen:
            return
        seen.add(key)
        rows.append({"dialogue_id": dialogue_key(dialogue["dialogue_id"]), "turn": turn, "speaker": speaker,
                     "utterance": utt, "char_start": start, "char_end": end, "value": value, "domain": domain,
                     "slot": slot, "act": act, "source": source})

    for turn, t in enumerate(dialogue["turns"]):
        speaker = "user" if t["speaker"].upper() == "USER" else "system"
        utt = t["utterance"]
        for fr in t["frames"]:
            if speaker == "user" and fr.get("state", {}).get("active_intent", "NONE") == "NONE":
                continue
            for s in fr["slots"]:
                if "start" not in s:  # value copied from another slot, no span
                    continue
                domain, _, slot = s["slot"].partition("-")
                add(turn, speaker, utt, s["start"], s["exclusive_end"], s["value"], domain, slot, "inform", "slot")
        a = acts.get(str(t["turn_id"]), {})
        for e in a.get("span_info", []):
            domain, _, act = e[0].partition("-")
            add(turn, speaker, utt, e[3], e[4], e[2], domain.lower(), e[1], act.lower(), "act_span")
        for name, pairs in a.get("dialog_act", {}).items():
            domain, _, act = name.partition("-")
            if act.lower() == "request":
                for slot, _v in pairs:
                    add(turn, speaker, utt, None, None, "?", domain.lower(), slot, "request", "request")
    return rows


def load_mwoz(mwoz_dir, ids=None):
    """(dialogues, acts): MultiWOZ 2.2 dialogues (train/dev/test) whose id (without .json) is in `ids` (all if None), and dialog_acts.json."""
    mwoz_dir = Path(mwoz_dir)
    ids = None if ids is None else set(ids)
    dialogues = []
    for split in ("train", "dev", "test"):
        for f in sorted((mwoz_dir / split).glob("dialogues_*.json")):
            dialogues += [d for d in json.loads(f.read_text(encoding="utf-8"))
                          if ids is None or dialogue_key(d["dialogue_id"]) in ids]
    acts = json.loads((mwoz_dir / "dialog_acts.json").read_text(encoding="utf-8"))
    return dialogues, acts


def span_table(dialogues, acts):
    """DataFrame (SPAN_COLS) of the span rows of all dialogues."""
    rows = [r for d in dialogues for r in spans_from_dialogue(d, acts.get(d["dialogue_id"], {}))]
    return pd.DataFrame(rows, columns=SPAN_COLS)


# ---------- T2: matching ----------

def _find_near(utt, text, pos):
    """Start of the occurrence of `text` in `utt` (case-insensitive) nearest to `pos`; None if absent."""
    low, t = utt.lower(), text.lower()
    hits = [m.start() for m in re.finditer(re.escape(t), low)] if t else []
    return min(hits, key=lambda h: abs(h - pos)) if hits else None


def _turn_match(did, turn, text, mw_by_dialogue):
    """(mw_turn, text_match, mw_text)."""
    turns = mw_by_dialogue.get(did, {})
    nt = norm(text)
    if turn in turns and norm(turns[turn]) == nt:
        return turn, "exact", turns[turn]
    best, best_r = None, 0.0
    for k, u in turns.items():
        sm = difflib.SequenceMatcher(None, nt, norm(u), autojunk=False)
        if sm.real_quick_ratio() < FUZZY_MIN or sm.quick_ratio() < FUZZY_MIN:
            continue
        r = sm.ratio()
        if r > best_r:
            best, best_r = k, r
    if best is not None and best_r >= FUZZY_MIN:
        return best, "fuzzy", turns[best]
    return None, "none", ""


def match(mentions, spans, utterances, mw_utts=None):
    """One row per mention (MATCH_COLS).

    utterances: {(dialogue_id, turn): text}, the dev50 turn texts (char_start/char_end of `mentions` are relative to this text).
    mw_utts: {(dialogue_id, turn): text} of every MultiWOZ turn; default = the utterances found in `spans` (labelled turns only).
    """
    if mw_utts is None:
        mw_utts = {(r.dialogue_id, int(r.turn)): r.utterance for r in spans.drop_duplicates(["dialogue_id", "turn"]).itertuples()}
    mw_by_dialogue = {}
    for (d, t), u in mw_utts.items():
        mw_by_dialogue.setdefault(d, {})[t] = u
    by_turn = {}
    for r in spans.to_dict("records"):
        by_turn.setdefault((r["dialogue_id"], int(r["turn"])), []).append(r)
    req = {k: ";".join(sorted({f"{r['domain']}-{r['slot']}" for r in v if r["act"] == "request"})) for k, v in by_turn.items()}
    tcache, out = {}, []
    for m in mentions.to_dict("records"):
        did, turn = m["dialogue_id"], int(m["turn"])
        dev_text = utterances.get((did, turn), "")
        if (did, turn) not in tcache:
            tcache[(did, turn)] = _turn_match(did, turn, dev_text, mw_by_dialogue)
        mw_turn, tm, mw_text = tcache[(did, turn)]
        row = {"mention_id": m["mention_id"], "dialogue_id": did, "turn": turn, "mw_turn": mw_turn, "text_match": tm,
               "mw_domain": "", "mw_slot": "", "mw_act": "", "match": "none",
               "request_slots": req.get((did, mw_turn), "") if mw_turn is not None else ""}
        cands = [r for r in by_turn.get((did, mw_turn), []) if r["act"] != "request"] if mw_turn is not None else []
        best = _best_span(m, cands, dev_text, mw_text)
        kind = "span"
        if best is None:
            best, kind = _value_match(m, cands), "value"
        if best is not None:
            row.update(mw_domain=best["domain"], mw_slot=best["slot"], mw_act=best["act"], match=kind)
        out.append(row)
    return pd.DataFrame(out, columns=MATCH_COLS)


def _best_span(m, cands, dev_text, mw_text):
    start, end = int(m["char_start"]), int(m["char_end"])
    if dev_text != mw_text:  # shift offsets into the MultiWOZ utterance
        s = _find_near(mw_text, str(m["text"]), start)
        if s is None:
            return None
        start, end = s, s + len(str(m["text"]))
    n = max(end - start, 1)
    best, key = None, None
    for r in cands:
        ov = min(end, int(r["char_end"])) - max(start, int(r["char_start"]))
        inside = ov > 0 and ov == int(r["char_end"]) - int(r["char_start"])  # span fully inside the mention ("8.08 pounds")
        if ov / n < OVERLAP_MIN and not inside:
            continue
        k = (ov, -_RANK[r["source"]])
        if key is None or k > key:
            best, key = r, k
    return best


def _value_match(m, cands):
    targets = {norm_value(m["text"]), norm_value(m.get("norm_value", ""))} - {""}
    hits = [r for r in cands if norm_value(r["value"]) in targets]
    return min(hits, key=lambda r: _RANK[r["source"]]) if hits else None


# ---------- T4/T3: levels ----------

def load_db(zip_path):
    """{domain: [row dict]} for train / hotel / restaurant from MULTIWOZ2.4.zip."""
    z = zipfile.ZipFile(zip_path)
    return {d: json.loads(z.read(f"MULTIWOZ2.4/{d}_db.json")) for d in ("train", "hotel", "restaurant")}


def db_index(db):
    """{domain: {norm value: [column, ...]}} without id-like columns and columns holding the value in > 30% of rows."""
    index = {}
    for domain, rows in db.items():
        count = {}
        for r in rows:
            for col, v in r.items():
                if col.lower() in SKIP_COLUMNS or isinstance(v, (dict, list)):
                    continue
                nv = norm_value(v)
                if nv:
                    count[(nv, col)] = count.get((nv, col), 0) + 1
        idx = {}
        for (nv, col), c in count.items():
            if c / len(rows) <= COMMON_SHARE:
                idx.setdefault(nv, []).append((c, col))
        index[domain] = {nv: [col for _, col in sorted(v)] for nv, v in idx.items()}
    return index


def slot_name(domain, slot, tear_map):
    """TEAR attribute name if tear_map maps one to "<domain>-<slot>", else "<Domain> <slot>"."""
    key = f"{domain}-{slot}"
    for attr, s in tear_map.items():
        if not attr.startswith("_") and s == key:
            return attr
    return f"{domain.capitalize()} {slot}"


def column_name(domain, column, tear_map):
    """Attribute name of a DB column: through tear_map like slot_name (leaveAt -> "Train leave at"), else
    "<Domain> <column>" with the slot names split as in the TEAR attrs (pricerange -> price range)."""
    col = column.lower()
    name = slot_name(domain, col, tear_map)
    return name if name != f"{domain.capitalize()} {col}" else f"{domain.capitalize()} {COLUMN_WORDS.get(col, col)}"


def _left_tokens(m, utterances):
    utt = utterances.get((m["dialogue_id"], int(m["turn"])))
    if utt is not None:
        before = utt[:int(m["char_start"])]
    else:  # fall back to the mention's context window
        ctx, text = str(m.get("context", "")), str(m["text"])
        i = ctx.lower().find(text.lower())
        before = ctx[:i] if i >= 0 else ""
    return [re.sub(r"\W", "", t).lower() for t in before.split()[-3:]]


def _request_slot(m, mt, domain, utterances):
    """The requested slot of the mention's cluster domain, or "" if the mention is not a question phrase."""
    # a "Booking-Request" belongs to the cluster's domain, as in levels() for L2
    slots = [f"{domain}-{s.partition('-')[2]}" for s in str(mt.get("request_slots", "") or "").split(";")
             if s.startswith((f"{domain}-", "booking-"))]
    if not slots:
        return ""
    if _QUESTION_PHRASE.match(norm(m["text"])) or WH_WORDS & set(_left_tokens(m, utterances)):
        return slots[0]
    return ""


def levels(mentions, matched, tear_map, db, schema=None, utterances=None, entity_domain=None):
    """One row per mention (LEVEL_COLS).

    schema: set of "domain-slot" names of schema.json (default: no filter). utterances: dev50 turn texts, used for the
    request pattern (default: the mention's context window). is_request is a bool, request_slot the requested slot.
    entity_domain: {stage-1 entity id: domain} (default ENTITY_DOMAIN, the dev50 ids; other runs: run_data_v37.entity_ids).
    """
    index = db_index(db)
    entity_domain = ENTITY_DOMAIN if entity_domain is None else entity_domain
    utterances = utterances or {}
    mt = matched.set_index("mention_id").to_dict("index")
    out = []
    for m in mentions.to_dict("records"):
        t = mt[m["mention_id"]]
        g1 = "" if pd.isna(m["gold_attr"]) else m["gold_attr"]
        e1 = "" if pd.isna(m["entity_gold"]) else m["entity_gold"]
        is_choice = t["match"] != "none" and t["mw_slot"] == "choice"
        g2, e2 = g1, e1
        domain = entity_domain.get(m["entity"], "")
        # "Booking-*" acts have no schema domain: the booking belongs to the cluster's entity
        mdom = domain if t["mw_domain"] == "booking" and domain else t["mw_domain"]
        if not g2 and t["match"] != "none" and not is_choice and (schema is None or f"{mdom}-{t['mw_slot']}" in schema):
            g2, e2 = slot_name(mdom, t["mw_slot"], tear_map), mdom
        g3, e3 = g2, e2
        if not g3 and not is_choice and domain:
            cols = index.get(domain, {}).get(norm_value(m["norm_value"]), [])
            if cols:
                g3, e3 = column_name(domain, cols[0], tear_map), domain
        rs = _request_slot(m, t, domain, utterances) if domain else ""
        out.append({"mention_id": m["mention_id"], "gt_L1": g1, "gt_L2": g2, "gt_L3": g3, "ent_L1": e1, "ent_L2": e2,
                    "ent_L3": e3, "is_request": bool(rs), "request_slot": rs, "is_choice": is_choice})
    return pd.DataFrame(out, columns=LEVEL_COLS)


# ---------- coverage ----------

def fmt_count(k, n):
    return f"{k}/{n} ({k / n:.3f})" if n else f"{k}/0 (n/a)"


def coverage(mentions, lv, old=None, entity_domain=None):
    """(table, extra): table = labelled share per level by entity x speaker ("k/n (0.xxx)");
    extra = dict of counts for the v3.4 unknown clusters and "other" values.

    mentions needs columns entity, speaker, cluster_id, norm_value, mention_id. old = {"q2": q2_table df, "q1": q1_table_values df}
    (both optional). A cluster / value counts as labelled when any of its mentions has the label; the cluster
    count is also given for >= 50% of its mentions. entity_domain: as in levels().
    """
    d = mentions.merge(lv, on="mention_id")
    d["entity_name"] = d["entity"].map(ENTITY_DOMAIN if entity_domain is None else entity_domain).fillna("other")
    rows = []
    for (ent, sp), g in [(k, g) for k, g in d.groupby(["entity_name", "speaker"])] + [(("all", "all"), d)]:
        rows.append({"entity": ent, "speaker": sp, "n": len(g),
                     **{f"L{i}": fmt_count(int((g[f"gt_L{i}"] != "").sum()), len(g)) for i in (1, 2, 3)}})
    table = pd.DataFrame(rows)
    extra = {}
    if old is not None and old.get("q2") is not None:
        unk = set(old["q2"].loc[old["q2"]["label_0.6"] == "unknown", "cluster_id"])
        extra["unknown_clusters"] = len(unk)
        for i in (2, 3):
            lab = d[d["cluster_id"].isin(unk)].groupby("cluster_id")[f"gt_L{i}"].agg(lambda s: (s != "").mean())
            extra[f"unknown_L{i}_any"] = int((lab > 0).sum())
            extra[f"unknown_L{i}_half"] = int((lab >= OVERLAP_MIN).sum())
    if old is not None and old.get("q1") is not None:
        oth = old["q1"][old["q1"]["kind"] == "other"]
        extra["other_values"] = len(oth)
        extra["other_mentions"] = int(oth["n"].sum())
        keys = set(zip(oth["cluster_id"], oth["norm_value"]))
        inm = d[[k in keys for k in zip(d["cluster_id"], d["norm_value"])]]
        extra["other_mentions_by_key"] = len(inm)  # mentions of those (cluster, value) pairs; can exceed the table's n
        for i in (1, 2, 3):
            extra[f"other_mentions_L{i}"] = int((inm[f"gt_L{i}"] != "").sum())
            lab = d.assign(_l=d[f"gt_L{i}"] != "").groupby(["cluster_id", "norm_value"])["_l"].any()
            extra[f"other_L{i}_any"] = int(sum(bool(lab.get((r.cluster_id, r.norm_value), False)) for r in oth.itertuples()))
    return table, extra
