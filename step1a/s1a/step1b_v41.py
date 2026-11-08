"""wf_v4.1 Step 1b (diary 6 Nov, task 1): top-down review and suggestion over the frozen Step-3 attributes. Pure functions; no model, no files.

One call per set. Input: the input-(a) column dicts of Step 4 (results/wf_v4/inputs/<set>/a.columns.json, made by step4_inputs from the frozen
Step-3 handover: name, description, role, value type, counts, a few example values with a short piece of text, checker evidence). The LLM sees
only these names, summaries and capped evidence (MAX_EXAMPLES examples per attribute), never whole dialogues.

The answer, per heading (entity):
- summary: one sentence on what the heading is about;
- decisions: one per attribute: keep | rename (new_name) | merge (merge_into = another attribute of the same heading) | flag, with a reason.
  The LLM never drops an attribute: every action keeps it in the list (merge and flag are proposals for later steps);
- new_attributes: at most MAX_NEW expected-but-unseen attributes, each with a description, an expected type and one extractor label
  (for the loop-2 named probe: RAG + GLiNER with that label as the only label).
Labels must be generic: `generic_errors` rejects a label or name that repeats a name-like example value of the input (capitalised in
its context, or with a digit) or a dataset / corpus word.
"""
import re

from .pilot_input import est_tokens
from .step4_prompts import TYPES, _JSON_ONLY, _TYPE_HELP, _arr, _entity, _obj, _S, render_column

MAX_NEW = 10
MAX_EXAMPLES = 3
ACTIONS = ["keep", "rename", "merge", "flag"]
MAX_LABEL_WORDS = 4
GENERIC_OK = {"free", "none", "yes", "number", "name", "time", "price", "type", "area", "address", "phone", "code", "people", "hours"}
# ^ words that can be example values but are ordinary attribute words (a value "free" must not ban the label "free parking")
CORPUS_WORDS = re.compile(r"\b(multi ?woz|woz|dstc|sgd|dataset|corpus|dialogues?|annotat\w*|slot)\b", re.I)

INSTRUCTION = """\
Below are the attributes found so far by analysing a corpus of dialogues. Each attribute is a kind of information that people
give in the dialogues, with a description, the type of its values, a few example values (each with a short piece of text
around it) and counts. The attributes are listed under {n_ent} headings: the things the dialogues are about. Lines labelled
"checker" and "checker evidence" are automatic and can be wrong; decide from the descriptions and examples.

Do two things for every heading.
1. Review every attribute of the heading and choose exactly one action, with one short reason:
   - keep: a good attribute with a good name;
   - rename: a good attribute with a poor or unclear name; give the better name in new_name;
   - merge: the same information as another attribute of the same heading; give that attribute's id in merge_into;
   - flag: doubtful (noise, too general, two meanings mixed, or under the wrong heading); say why in the reason.
   Never drop an attribute: every attribute keeps its place in the list whatever the action; merge and flag are only proposals.
   Use "" for new_name and merge_into when the action needs none.
2. Suggest attributes that such a thing normally has and that people would plausibly mention in such dialogues, but that are
   missing from the list. At most {max_new} per heading; fewer, or none, is fine. Do not suggest an attribute that is already in
   the list under another name. For each give a name, a one-sentence description, the expected type of its values (one of:
   {types}; {type_help}) and one extractor label: {max_words} plain words or fewer that a text tagger can search for, such as
   "author name" or "loan period". Names and labels must be general words that fit any collection of texts about such
   things: no example values, no names of places, people or brands, and no names of datasets.
Also give a one-sentence summary of what each heading is about.
{json_only} Shape (the names and ids here are made up):
{{"headings": [{{"heading": "x", "summary": "...",
   "decisions": [{{"id": "x:1", "action": "keep", "new_name": "", "merge_into": "", "reason": "..."}},
                 {{"id": "x:2", "action": "merge", "new_name": "", "merge_into": "x:1", "reason": "..."}}],
   "new_attributes": [{{"name": "due date", "description": "...", "type": "date", "label": "due date", "reason": "..."}}]}}]}}
Every heading appears exactly once and every attribute id exactly once.

Attributes ({n_cols}):
"""


def render(cols):
    """Attribute block: `== heading ==` blocks in input order, MAX_EXAMPLES examples per attribute."""
    out, last = [], None
    for c in cols:
        if _entity(c) != last:
            last = _entity(c)
            out.append(f"== {last} ==")
        out.append(render_column(c, MAX_EXAMPLES))
    return "\n".join(out) + "\n"


def build_prompt(cols):
    """(prompt text, JSON schema) of the Step-1b call over `cols` (input-(a) column dicts of one set)."""
    ents = list(dict.fromkeys(_entity(c) for c in cols))
    ids = [c["id"] for c in cols]
    text = INSTRUCTION.format(n_ent=len(ents), n_cols=len(ids), max_new=MAX_NEW, types=", ".join(TYPES), type_help=_TYPE_HELP,
                              max_words=MAX_LABEL_WORDS, json_only=_JSON_ONLY) + render(cols) + "\nReturn the JSON object now.\n"
    new_attr = _obj({"name": _S, "description": _S, "type": {"enum": TYPES}, "label": _S, "reason": _S})
    decision = _obj({"id": {"enum": ids}, "action": {"enum": ACTIONS}, "new_name": _S, "merge_into": {"enum": ids + [""]}, "reason": _S})
    heading = _obj({"heading": {"enum": ents}, "summary": _S, "decisions": _arr(decision),
                    "new_attributes": {**_arr(new_attr), "maxItems": MAX_NEW}})
    return text, _obj({"headings": {**_arr(heading), "minItems": len(ents), "maxItems": len(ents)}})


def _words(s):
    return re.findall(r"[a-z0-9]+", str(s).lower())


def _name_like(value, context):
    """True when a value looks like a name or code: it has a digit, or it is written with a capital letter in its own context (not at
    the start of the context or of a sentence). Ordinary words that happen to be values ("contact number", "free") are not name-like."""
    if any(ch.isdigit() for ch in value):
        return True
    i = context.lower().find(value.lower()) if context else -1
    before = context[:i].rstrip() if i > 0 else ""
    return bool(before) and not before.endswith((".", "!", "?")) and context[i].isupper()  # a capital after a sentence end is no name


def example_values(cols):
    """Normalised name-like example values of the input (full values such as "ashley hotel" or "cambridge"): a label must not contain
    one. Single words of a multi-word value are not banned ("hotel" stays usable), nor are the heading names."""
    heads = {" ".join(_words(_entity(c))) for c in cols}
    vals = set()
    for c in cols:
        for e in c.get("examples") or []:
            val, ctx = (e[0], e[1] or "") if isinstance(e, (list, tuple)) else (e, "")
            v = " ".join(_words(val))
            if v and v not in heads and _name_like(str(val), ctx):
                vals.add(v)
    return vals


def generic_errors(text, values):
    """Why a name or label is not generic (empty list = fine)."""
    errs = []
    if CORPUS_WORDS.search(str(text)):
        errs.append(f"corpus word in {text!r}")
    t = f" {' '.join(_words(text))} "
    if any(f" {v} " in t for v in values if v not in GENERIC_OK):
        errs.append(f"example value in {text!r}")
    return errs



def validate(a, cols):
    """Errors of a parsed answer: headings, one decision per attribute, action fields, new-attribute limits, generic labels."""
    ids = {c["id"]: _entity(c) for c in cols}
    ents = list(dict.fromkeys(ids.values()))
    names = {" ".join(_words(c["name"])) for c in cols}
    values = example_values(cols)
    errs, seen_h, seen = [], [], {}
    for h in a.get("headings", []):
        e = h.get("heading")
        if e not in ents:
            errs.append(f"unknown heading {e!r}")
        elif e in seen_h:
            errs.append(f"heading {e!r} twice")
        seen_h.append(e)
        for d in h.get("decisions", []):
            i, act = d.get("id"), d.get("action")
            if i not in ids:
                errs.append(f"unknown id {i!r}")
                continue
            if i in seen:
                errs.append(f"id {i!r} decided twice")
            seen[i] = d
            if ids[i] != e:
                errs.append(f"id {i!r} under heading {e!r}, belongs to {ids[i]!r}")
            if act not in ACTIONS:
                errs.append(f"{i}: bad action {act!r}")
            if act == "rename" and not str(d.get("new_name", "")).strip():
                errs.append(f"{i}: rename without new_name")
            if act == "merge":
                m = d.get("merge_into", "")
                if m not in ids or m == i or ids.get(m) != ids[i]:
                    errs.append(f"{i}: bad merge_into {m!r}")
        new = h.get("new_attributes", [])
        if len(new) > MAX_NEW:
            errs.append(f"heading {e!r}: {len(new)} new attributes (max {MAX_NEW})")
        for n in new:
            lab = str(n.get("label", ""))
            if not lab.strip():
                errs.append(f"{e}: new attribute {n.get('name')!r} without label")
            if len(_words(lab)) > MAX_LABEL_WORDS:
                errs.append(f"{e}: label {lab!r} longer than {MAX_LABEL_WORDS} words")
            if n.get("type") not in TYPES:
                errs.append(f"{e}: bad type {n.get('type')!r}")
            if " ".join(_words(n.get("name", ""))) in names:
                errs.append(f"{e}: new attribute {n.get('name')!r} repeats an existing name")
            for t in (n.get("name", ""), lab):
                errs += [f"{e}: {x}" for x in generic_errors(t, values)]
    errs += [f"heading {x!r} missing" for x in ents if x not in seen_h]
    errs += [f"id {i!r} without a decision" for i in ids if i not in seen]
    return errs


def summary(a, cols):
    """Counts of a parsed answer: actions per heading and new attributes per heading."""
    out = {}
    for h in a.get("headings", []):
        acts = {k: 0 for k in ACTIONS}
        for d in h.get("decisions", []):
            if d.get("action") in acts:
                acts[d["action"]] += 1
        out[h.get("heading")] = {**acts, "new": len(h.get("new_attributes", []))}
    return out


def labels(a, cols):
    """Loop-2 label list [{entity, name, label, description, value_type}] from the new attributes that pass the generic check."""
    values, out = example_values(cols), []
    for h in a.get("headings", []):
        for n in h.get("new_attributes", []):
            if n.get("label") and not generic_errors(n["label"], values) and not generic_errors(n.get("name", ""), values):
                out.append({"entity": h["heading"], "name": n.get("name", ""), "label": n["label"], "description": n.get("description", ""),
                            "value_type": n.get("type", "text")})
    return out


def prompt_tokens(text):
    return est_tokens(text)


def fake_answer(cols):
    """A valid answer for tests and the notebook dry run: keep everything, one generic new attribute per heading."""
    heads = {}
    for c in cols:
        heads.setdefault(_entity(c), []).append(c["id"])
    return {"headings": [{"heading": e, "summary": f"fake summary of {e}",
                          "decisions": [{"id": i, "action": "keep", "new_name": "", "merge_into": "", "reason": "fake"} for i in ids],
                          "new_attributes": [{"name": "contact number", "description": "a number to call", "type": "text",
                                              "label": "contact number", "reason": "fake"}]} for e, ids in heads.items()]}
