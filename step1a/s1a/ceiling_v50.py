"""wf_v5.0 G1: text ceiling of the gold L2 attributes. Which gold attributes are mentioned in the dialogue text at all, how often,
and are they span or yes/no attributes. No models; pure functions so dev50 and dev50b use the same code.

Mention sources (one row per mention, columns MENTION_COLS):
- "tear": TEAR gold values of the set (graph_v22_<set>/gold_values.csv; L1 attributes only), verbatim or not.
- "mwoz": MultiWOZ 2.2 annotated spans (slot spans + act span_info; requests have no span and are skipped), named with
  gt_ext.slot_name. A "booking" act span takes the domain of the turn's active booking intent (booking_domains).
- "pipe": our Step 1a mentions labelled with the attribute in gt_L2 (what the scorer can credit).
A text mention = a tear or mwoz row; one (dialogue, turn, normalised value) counts once.
"""

import pandas as pd

from . import gt_ext as GT

MENTION_COLS = ["attr", "source", "dialogue_id", "turn", "value", "verbatim"]
YES_NO = {"yes", "no", "free", "none", "true", "false"}
HARD_MAX = 2   # 1..HARD_MAX text mentions = hard


def booking_domains(dialogues):
    """{(dialogue_id, turn): domain} of the active service (a book_* intent first) of each user turn, also used for the system turn after
    it. Turns with no single active service are left out."""
    out = {}
    for d in dialogues:
        did, last = GT.dialogue_key(d["dialogue_id"]), None
        for i, t in enumerate(d["turns"]):
            if t["speaker"].upper() == "USER":
                act = [(fr["service"], fr["state"]["active_intent"]) for fr in t["frames"]
                       if fr.get("state", {}).get("active_intent", "NONE") != "NONE"]
                book = [s for s, intent in act if intent.startswith("book")]
                pick = book if book else [s for s, _ in act]
                last = pick[0] if len(set(pick)) == 1 else None
            if last:
                out[(did, i)] = last
    return out


def mwoz_mentions(spans, book_dom, tear_map, gold_names):
    """MENTION_COLS rows of MultiWOZ 2.2 spans named as a gold attribute. Unresolved booking spans are dropped."""
    rows = []
    for r in spans[spans["source"] != "request"].to_dict("records"):
        dom = book_dom.get((r["dialogue_id"], int(r["turn"]))) if r["domain"] == "booking" else r["domain"]
        name = GT.slot_name(dom, r["slot"], tear_map) if dom else ""
        if name in gold_names:
            rows.append({"attr": name, "source": "mwoz", "dialogue_id": r["dialogue_id"], "turn": int(r["turn"]),
                         "value": GT.norm_value(r["value"]), "verbatim": True})
    return pd.DataFrame(rows, columns=MENTION_COLS)


def tear_mentions(gold_values, turn_of, gold_names):
    """MENTION_COLS rows of the TEAR gold values. turn_of(dialogue_id, char_start) -> turn (None for a non-verbatim value)."""
    rows = [{"attr": r["gold_attr"], "source": "tear", "dialogue_id": r["dialogue_id"],
             "turn": turn_of(r["dialogue_id"], r["char_start"]) if r["verbatim"] else None,
             "value": GT.norm_value(r["value"]), "verbatim": bool(r["verbatim"])}
            for r in gold_values.to_dict("records") if r["gold_attr"] in gold_names]
    return pd.DataFrame(rows, columns=MENTION_COLS)


def pipe_mentions(mentions, labels, gold_names):
    """MENTION_COLS rows of our Step 1a mentions; labels = {mention_id: [gt_L2 labels]}."""
    rows = [{"attr": a, "source": "pipe", "dialogue_id": m["dialogue_id"], "turn": int(m["turn"]),
             "value": GT.norm_value(m["norm_value"]), "verbatim": True}
            for m in mentions.to_dict("records") for a in labels.get(int(m["mention_id"]), []) if a in gold_names]
    return pd.DataFrame(rows, columns=MENTION_COLS)


def kind(tear_rows):
    """"yes/no" when the attribute has TEAR values and none is verbatim and all are yes/no words, else "span"."""
    if tear_rows.empty or tear_rows["verbatim"].any():
        return "span"
    return "yes/no" if set(tear_rows["value"]) <= YES_NO else "span"


def ceiling_rows(gold, found, ments):
    """One row per gold attribute. gold = {attr: entity}; found = set of found attributes; ments = all MENTION_COLS rows."""
    out = []
    for attr, ent in sorted(gold.items(), key=lambda x: (x[1], x[0])):
        m = ments[ments["attr"] == attr]
        text = m[m["source"].isin(("tear", "mwoz"))]
        verb = text[text["verbatim"]].drop_duplicates(["dialogue_id", "turn", "value"])
        nonverb = text[~text["verbatim"]].drop_duplicates(["dialogue_id", "value"])
        n_text = len(verb) + len(nonverb)
        pipe = m[m["source"] == "pipe"]
        out.append({"entity": ent, "attr": attr, "kind": kind(m[m["source"] == "tear"]),
                    "n_text": n_text, "n_tear": int((m["source"] == "tear").sum()), "n_mwoz": int((m["source"] == "mwoz").sum()),
                    "n_pipe": len(pipe), "dialogues_text": text["dialogue_id"].nunique(), "dialogues_pipe": pipe["dialogue_id"].nunique(),
                    "reachable": n_text >= 1, "hard": 1 <= n_text <= HARD_MAX, "found_v49": attr in found})
    return pd.DataFrame(out)


def summary(rows):
    """{row label: value} of the G1 table for one set."""
    reach = rows[rows["reachable"]]
    found_reach = int((reach["found_v49"]).sum())
    return {"gold attributes in L2": len(rows),
            "with >= 1 mention (reachable)": len(reach),
            "with only 1-2 mentions (hard)": int(rows["hard"].sum()),
            "found now (loops 1 + 2, human check)": int(rows["found_v49"].sum()),
            "found / reachable": f"{found_reach}/{len(reach)} ({found_reach / len(reach):.3f})" if len(reach) else "n/a",
            "found but not reachable": int((rows["found_v49"] & ~rows["reachable"]).sum()),
            "reachable with 0 pipeline mentions": int((rows["reachable"] & (rows["n_pipe"] == 0)).sum())}
