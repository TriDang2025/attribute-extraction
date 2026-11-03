"""wf_v3.8 W3 (diary 2 Nov, task 12): why A s012 misses noise clusters and marks real ones as noise. No models, no LLM.

Cases of one run read at L2 under rules v1.1 (model-free noise set):
- every noise cluster (label noise): caught or missed by the vote, with what each order did;
- every marked cluster that is not noise (label real / mixed / unknown): the false positives.
Each case carries model-free proxies (distinct values, value-type mix, share in system turns, share inside questions,
nearest other column) and a GUESS whether the planned evidence checks would catch it. The guesses are rules over those
proxies (`Thresholds`), not results of any check.

Guess semantics: a check "flags" a cluster when the proxy says its mentions do not support a column of their own.
- missed noise cluster: would_catch = at least one check flags it (it would be demoted from the schema);
- marked non-noise cluster: would_rescue = no check flags it (the evidence would support a column, so the mark could be undone).
Check proxies: example = more than `question_share` of the mentions sit inside questions, or the value types are mixed
(the name is not read, so "does the value fit the name" is only approximated); neighbour = the centroid is at least
`neighbour_sim` cosine to the nearest other kept column (it would fit that column, so it is a duplicate, not a column of its
own); counting = fewer than `min_mentions` mentions, `min_dialogues` dialogues or `min_distinct` distinct values, or the
dominant value type covers less than `type_share` of the mentions.
"""

import re
from collections import Counter
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import noise_v36 as NV
from . import pilot_verify as PV
from . import rules_labels as RL
from . import v34_data as VD
from . import value_types as VT

ORDERS = ("A s0", "A s1", "A s2")
VOTE = "A s012"
NOISE_CAUGHT, NOISE_MISSED, MARKED_NOT_NOISE = "noise_caught", "noise_missed", "marked_not_noise"


@dataclass(frozen=True)
class Thresholds:
    min_mentions: int = 3
    min_dialogues: int = 2
    min_distinct: int = 2
    type_share: float = 0.8      # counting: dominant value type must cover this share
    question_share: float = 0.5  # example: flag when this share of mentions sits inside a question
    neighbour_sim: float = 0.8   # neighbour: cosine to the nearest other kept column


# ---- mention level

def mention_kind(cls, is_choice):
    """Kind of a mention class (rules_labels.mention_class value): "choice" (number of results), "no_l2_label" (noise
    without a label at L2), "request" (unlabelled request phrase), "labelled" (has an L2 attribute)."""
    if cls == "noise":
        return "choice" if is_choice else "no_l2_label"
    return "request" if cls == "request" else "labelled"


def in_question(turn_text, text):
    """True when the first occurrence of `text` (case-insensitive) in `turn_text` sits in a sentence that ends with "?"."""
    i = turn_text.lower().find(str(text).lower())
    if i < 0 or not str(text):
        return False
    start = max(turn_text.rfind(c, 0, i) for c in ".!?") + 1
    ends = [j for j in (turn_text.find(c, i + len(str(text))) for c in ".!?") if j >= 0]
    end = min(ends) if ends else len(turn_text) - 1
    return turn_text[end:end + 1] == "?" and start <= i


def mark_context(turn_text, text, width=110):
    """The turn with the mention marked [[...]], cut to about `width` characters around it."""
    marked = NV.mark_value(turn_text, text)
    i = marked.find("[[")
    if len(marked) <= width or i < 0:
        return marked
    lo = max(0, min(i - width // 3, len(marked) - width))
    return ("..." if lo else "") + marked[lo:lo + width] + ("..." if lo + width < len(marked) else "")


def examples_of(m, k=3):
    """[(text, speaker, context)] of up to k mentions with distinct lowercase texts, lowest mention_id first."""
    out, seen = [], set()
    for _, r in m.sort_values("mention_id").iterrows():
        key = str(r["text"]).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((str(r["text"]), r["speaker"], mark_context(r["turn_text"], r["text"])))
        if len(out) == k:
            break
    return out


# ---- cluster proxies

def cluster_proxies(m):
    """Model-free proxies of the mentions `m` of one cluster (columns text, dialogue_id, speaker, turn_text): n, n_dialogues,
    n_distinct (lowercase texts), top_type / type_share (value_types.value_type_v35), n_types, share_system (mentions in
    system turns), share_question (mentions inside a question sentence)."""
    n = len(m)
    types = Counter(VT.value_type_v35(t) for t in m["text"])
    top, top_n = types.most_common(1)[0] if types else ("", 0)
    return {"n": n, "n_dialogues": int(m["dialogue_id"].nunique()), "n_distinct": int(m["text"].str.lower().nunique()),
            "top_type": top, "type_share": top_n / n if n else 0.0, "n_types": len(types),
            "share_system": float((m["speaker"] == "system").mean()) if n else 0.0,
            "share_question": float(np.mean([in_question(t, x) for t, x in zip(m["turn_text"], m["text"])])) if n else 0.0}


def nearest_other(centroids, cid, allowed):
    """(cluster id, cosine) of the centroid in `centroids` {cid: vector} nearest to cid's, among the ids in `allowed`
    (cid itself is skipped); ("", nan) when there is none."""
    best, sim = "", float("nan")
    v = np.asarray(centroids[cid], dtype=float)
    v = v / max(np.linalg.norm(v), 1e-9)
    for o in sorted(allowed):
        if o == cid or o not in centroids:
            continue
        w = np.asarray(centroids[o], dtype=float)
        s = float(v @ (w / max(np.linalg.norm(w), 1e-9)))
        if np.isnan(sim) or s > sim:
            best, sim = o, s
    return best, sim


def guess_checks(p, sim, th=Thresholds()):
    """GUESS of the evidence checks from the proxies `p` (cluster_proxies) and the nearest-column cosine `sim` (nan =
    no other column): {example_flag, neighbour_fit, counting_flag} (bools). See the module doc for the rules."""
    return {"example_flag": bool(p["share_question"] > th.question_share or p["type_share"] < th.type_share),
            "neighbour_fit": bool(not np.isnan(sim) and sim >= th.neighbour_sim),
            "counting_flag": bool(p["n"] < th.min_mentions or p["n_dialogues"] < th.min_dialogues
                                  or p["n_distinct"] < th.min_distinct or p["type_share"] < th.type_share)}


def any_check(g):
    """True when at least one guessed check flags the cluster as having no column of its own."""
    return g["example_flag"] or g["neighbour_fit"] or g["counting_flag"]


# ---- what the model did

def where_it_went(vo, cid):
    """(action, name, group size) of cluster `cid` in a VariantOut: the decision row's action, the output attribute that
    holds the cluster (name, number of clusters in it); ("-", "", 0) when the variant has no row for it."""
    rows = vo.dec[vo.dec["cluster_id"] == cid]
    if not len(rows):
        return "-", "", 0
    action = rows.iloc[0]["action"] or "-"
    for _, a in vo.attrs.iterrows():
        cl = str(a["clusters"]).split(";")
        if cid in cl and a["status"] == "keep":
            return action, str(a["name"]), len(cl)
    return action, str(rows.iloc[0]["name"]), 0


def order_text(action, name, size):
    """"not_attribute", "keep 'name'" or "merge 'name' (3 clusters)"."""
    return " ".join(x for x in (action, f"'{name}'" if name else "", f"({size} clusters)" if size > 1 else "") if x)


def reason_code(case_type, n_marked, label, top_attr, n, gold_ents, kind, request_share=0.0):
    """Machine reason of a case (the counts per reason come from this):
    noise_caught -> caught_all_orders | caught_by_vote; noise_missed -> kept_all_orders:<kind> | vote_lost_mark:<kind>
    (kind = dominant noise-mention kind); marked_not_noise -> real_other_domain | real_tiny | real_marked | request_phrases |
    mixed_cluster | unknown_cluster (a real cluster whose top attribute is of another domain than the entity / has <= 2 mentions; a
    non-real cluster with >= half request mentions = question phrases for a slot; any other non-real cluster)."""
    if case_type == NOISE_CAUGHT:
        return "caught_all_orders" if n_marked == len(ORDERS) else "caught_by_vote"
    if case_type == NOISE_MISSED:
        return f"{'kept_all_orders' if n_marked == 0 else 'vote_lost_mark'}:{kind}"
    if label != "real":
        return "request_phrases" if request_share >= 0.5 else f"{label}_cluster"
    if str(top_attr).split(" ")[0].lower() not in gold_ents:
        return "real_other_domain"
    return "real_tiny" if n <= 2 else "real_marked"


def reason_text(c):
    """One line for case dict `c` (fields of build_cases)."""
    ex = ", ".join(f"'{e[0]}'" for e in c["examples"])
    real = f"; {c['top_share']:.0%} {c['top_attr']}" if c["top_share"] > 0 else ""
    share = f"{c['noise_share']:.0%} noise{real}"
    code, voted = c["reason_code"], c["a_s012"]
    if code.startswith("caught"):
        return f"caught: {voted}; marked in {c['n_marked']}/3 orders; {c['kind_text']} ({ex})."
    if code.startswith(("kept_all_orders", "vote_lost_mark")):
        order = ("kept in all 3 orders" if code.startswith("kept") else f"marked in only {c['n_marked']}/3 orders, vote kept it")
        what = ("choice mentions (a count or choice word)" if c["main_kind"] == "choice" else
                "mentions with no L2 label (generic words, not an attribute value)")
        return f"missed: {order}; s012 = {voted}; {share}; {what}, e.g. {ex}."
    top = f"{c['top_attr'] or 'none'} {c['top_share']:.2f}"
    if code == "real_other_domain":
        return f"false mark: values of another domain's attribute ({top}) inside this entity, e.g. {ex}; s012 = {voted}."
    if code in ("real_tiny", "real_marked"):
        return f"false mark: real {top} cluster with {c['n']} mention(s), marked in {c['n_marked']}/3 orders, e.g. {ex}."
    if code == "request_phrases":
        return (f"false mark: {c['request_share']:.0%} request phrases (questions for a slot, e.g. {ex}), neither noise nor a "
                f"value; marked in {c['n_marked']}/3 orders, s012 = {voted}.")
    return (f"false mark: mixed cluster (top {top}, {c['noise_share']:.0%} noise); marked in {c['n_marked']}/3 orders, "
            f"e.g. {ex}.")


# ---- the cases of one run

def build_cases(bundle, gt, shared, label=VOTE, orders=ORDERS, th=Thresholds()):
    """DataFrame, one row per case of the A runs in `bundle` ({ent: EntityData} with variants `orders` + `label`, as loaded)
    read at L2 with gt (the gt_levels table): noise clusters (caught or missed by `label`) and marked clusters that are
    not noise. Mentions are counted over every cluster of the entity; `noise_share_all` is the cluster's share of all
    noise mentions pooled over the entities."""
    rules = NV.mwoz_rules(2)
    extra = {"gt_levels": gt}
    lev = VD.with_level(bundle, gt, 2)
    pos = {int(i): k for k, i in enumerate(shared.e.ids)}
    per, total_noise = {}, 0
    for ent, ed in lev.items():
        cl = RL.cluster_labels(ed, rules, extra).set_index("cluster_id")
        cls = RL.mention_class(ed, rules, extra)
        m = ed.mentions.assign(cls=cls.reindex(ed.mentions["mention_id"].astype(int)).values)
        m = m.assign(kind=[mention_kind(c, ch) for c, ch in zip(m["cls"], m["is_choice"])])
        total_noise += int((m["kind"].isin(("choice", "no_l2_label"))).sum())
        per[ent] = (ed, cl, m)
    rows = []
    for ent, (ed, cl, m) in per.items():
        dec = ed.variants[label].dec
        marked = set(dec.loc[dec["action"].isin(PV.MARKED), "cluster_id"])
        cent = {c: shared.e.x[[pos[int(i)] for i in g["mention_id"]]].mean(axis=0) for c, g in m.groupby("cluster_id")}
        kept = {c for c in cent if c not in marked}
        for cid, r in cl.iterrows():
            noise, mk = r["label"] == "noise", cid in marked
            if not (noise or mk):
                continue
            g = m[m["cluster_id"] == cid]
            case_type = (NOISE_CAUGHT if mk else NOISE_MISSED) if noise else MARKED_NOT_NOISE
            kinds = Counter(k for k in g["kind"] if k in ("choice", "no_l2_label"))
            main = kinds.most_common(1)[0][0] if kinds else ""
            went = {v: where_it_went(ed.variants[v], cid) for v in (label, *orders) if v in ed.variants}
            n_marked = sum(went[v][0] in PV.MARKED for v in orders if v in went)
            p = cluster_proxies(g)
            own = {c for c in kept if c != cid}
            near, sim = nearest_other(cent, cid, own - set(_group_clusters(ed.variants[label], cid)))
            chk = guess_checks(p, sim, th)
            req = float((g["kind"] == "request").mean())
            code = reason_code(case_type, n_marked, r["label"], r["top_attr"], int(r["n"]), ed.gold_ents, main, req)
            c = {"ent": ent, "cluster_id": cid, "case_type": case_type, "label": r["label"], "n": int(r["n"]),
                 "noise_mentions": int(sum(kinds.values())), "kinds": dict(kinds), "main_kind": main,
                 "kind_text": ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())),
                 "noise_share_all": sum(kinds.values()) / total_noise if total_noise else float("nan"),
                 "noise_share": float(r["noise_share"]), "request_share": req, "top_attr": r["top_attr"], "top_share": float(r["top_share"]),
                 "examples": examples_of(g), "a_s012": order_text(*went[label]),
                 **{f"order_{o[-2:]}": order_text(*went[o]) if o in went else "-" for o in orders},
                 "n_marked": n_marked, "evidence": str(ed.variants[label].dec.set_index("cluster_id")["evidence"].get(cid, "")),
                 **p, "nearest_column": near, "nearest_sim": sim, **chk, "reason_code": code}
            c["reason"] = reason_text(c)
            c["guess_catch"] = bool(any_check(chk)) if case_type == NOISE_MISSED else None
            c["guess_rescue"] = bool(not any_check(chk)) if case_type == MARKED_NOT_NOISE else None
            rows.append(c)
    return pd.DataFrame(rows)


def _group_clusters(vo, cid):
    """The clusters of the output attribute that holds `cid` in a VariantOut (just [cid] when it is in none)."""
    for _, a in vo.attrs.iterrows():
        cl = str(a["clusters"]).split(";")
        if cid in cl:
            return cl
    return [cid]


# ---- tables

def csv_frame(cases):
    """The cases as a flat frame for CSV: examples become three text / context columns; lists and dicts become strings."""
    d = cases.copy()
    for i in range(3):
        d[f"example{i + 1}"] = [f"{e[i][0]} ({e[i][1]})" if len(e) > i else "" for e in d["examples"]]
        d[f"context{i + 1}"] = [e[i][2] if len(e) > i else "" for e in d["examples"]]
    d["kinds"] = d["kind_text"]
    return d.drop(columns=["examples", "kind_text"])


def reason_counts(cases):
    """Series of case counts per (case_type, reason_code), sorted by case type then count."""
    return cases.groupby(["case_type", "reason_code"]).size().sort_values(ascending=False).sort_index(level=0, sort_remaining=False)


def guess_summary(cases):
    """dict of the guessed catch counts: missed noise clusters the checks would probably catch (any / per check), and
    marked non-noise clusters they would probably rescue."""
    miss = cases[cases["case_type"] == NOISE_MISSED]
    fp = cases[cases["case_type"] == MARKED_NOT_NOISE]
    return {"missed": len(miss), "catch_any": int(miss["guess_catch"].sum()), "catch_example": int(miss["example_flag"].sum()),
            "catch_neighbour": int(miss["neighbour_fit"].sum()), "catch_counting": int(miss["counting_flag"].sum()),
            "fp": len(fp), "rescue": int(fp["guess_rescue"].sum())}


def summary_line(name, cases, noise_n):
    """One line of counts for a run: noise clusters caught (of noise_n), marks by label, missed kinds, guessed catches."""
    c = cases[cases["case_type"] == NOISE_CAUGHT]
    fp = cases[cases["case_type"] == MARKED_NOT_NOISE]
    miss = cases[cases["case_type"] == NOISE_MISSED]
    g = guess_summary(cases)
    marks = len(c) + len(fp)
    return (f"{name}: noise caught {len(c)}/{noise_n}; marks {marks} = {len(c)} noise + {int((fp['label'] == 'real').sum())} real + "
            f"{int((fp['label'] == 'mixed').sum())} mixed + {int((fp['label'] == 'unknown').sum())} unknown; missed {len(miss)} "
            f"(kinds {dict(Counter(miss['main_kind']))}, kept in all orders {int(miss['reason_code'].str.startswith('kept').sum())}); "
            f"guess: checks catch {g['catch_any']}/{g['missed']} misses, rescue {g['rescue']}/{g['fp']} false marks.")


def cases_md(cases, title, summary_lines, th=Thresholds()):
    """Markdown report of the cases: per-case blocks in three sections, counts per reason, the guess table."""
    f = lambda b: "n/a" if b is None or (isinstance(b, float) and np.isnan(b)) else ("yes" if b else "no")  # noqa: E731
    lines = [f"# {title}", "", *[f"- {s}" for s in summary_lines], "",
             "Noise = the model-free MultiWOZ noise set (rules v1.1, L2): choice mentions, or no L2 label and not a request. "
             "A s012 = vote of 3 orders (s0 / s1 / s2). Marked = not_attribute / unsure / attribute_cue. The response has no "
             "free-text reason: the only text field is `evidence`, a quoted example, shown where it exists.", "",
             "## Guesses about the planned evidence checks (not results)", "",
             f"Rules over model-free proxies, thresholds {th}. example flags: > {th.question_share:.0%} of mentions inside a "
             f"question, or dominant value type < {th.type_share:.0%}. neighbour: cosine to the nearest other kept column >= "
             f"{th.neighbour_sim} (it would fit that column). counting flags: < {th.min_mentions} mentions, < {th.min_dialogues} "
             f"dialogues, < {th.min_distinct} distinct values, or dominant type < {th.type_share:.0%}. Missed noise: caught = any "
             "check flags it. False mark: rescued = no check flags it. The example proxy does not read the attribute name.", ""]
    g = guess_summary(cases)
    lines += [f"- missed noise clusters: {g['catch_any']}/{g['missed']} probably caught (example {g['catch_example']}, "
              f"neighbour {g['catch_neighbour']}, counting {g['catch_counting']})",
              f"- marked non-noise clusters: {g['rescue']}/{g['fp']} probably rescued", "",
              "## Counts per reason", "", "| case type | reason | cases |", "|---|---|---|"]
    lines += [f"| {t} | {r} | {n} |" for (t, r), n in reason_counts(cases).items()]
    titles = {NOISE_CAUGHT: "(a) noise clusters caught", NOISE_MISSED: "(a) noise clusters missed",
              MARKED_NOT_NOISE: "(b) marked clusters that are not noise"}
    for t, head in titles.items():
        lines += ["", f"## {head}", ""]
        for _, c in cases[cases["case_type"] == t].iterrows():
            lines += [f"### {c['ent']} {c['cluster_id']}: {c['n']} mentions, label {c['label']}", "",
                      f"- reason: {c['reason']}",
                      f"- share of all noise mentions {c['noise_share_all']:.3f} ({c['noise_mentions']} noise mentions"
                      + (f": {c['kind_text']}" if c["kind_text"] else "") + f"); top L2 attribute {c['top_attr'] or 'none'} {c['top_share']:.2f}",
                      f"- A s012: {c['a_s012']}; s0: {c['order_s0']}; s1: {c['order_s1']}; s2: {c['order_s2']}"
                      + (f"; evidence {c['evidence']}" if c["evidence"] else ""),
                      f"- proxies: distinct {c['n_distinct']}, dialogues {c['n_dialogues']}, type {c['top_type']} {c['type_share']:.2f}, "
                      f"system turns {c['share_system']:.2f}, in questions {c['share_question']:.2f}, nearest column "
                      f"{c['nearest_column'] or '-'} ({c['nearest_sim']:.2f})",
                      f"- guess: example flag {f(c['example_flag'])}, fits neighbour {f(c['neighbour_fit'])}, counting flag "
                      f"{f(c['counting_flag'])}; " + (f"would catch {f(c['guess_catch'])}" if c["guess_catch"] is not None else
                                                      f"would rescue {f(c['guess_rescue'])}" if c["guess_rescue"] is not None else "already caught")]
            lines += [f"- example {i + 1}: {e[0]} ({e[1]}): {e[2]}" for i, e in enumerate(c["examples"])]
            lines.append("")
    return "\n".join(lines) + "\n"

