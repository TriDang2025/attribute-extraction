"""wf_v4.2 compact Step 3 A prompt (plan report/3_main/wf_v4.2/plan.md, section 4; diary Nov 7 task 10).

Fits the A call into Llama-3-8B's 8,192-token window. Each change is a switch, so its effect can be shown on its own:
- C1 `window`: an example is the speaker plus about BEFORE words before and AFTER words after the [[value]] in its own
  turn; no previous turn.
- C2 `n_examples`: at most N_EXAMPLES examples per cluster (the first ones of pilot_input.select_examples).
- C3 `compact_answer`: no evidence quote, and the placement is a short code (cur, sub, oth:<E>, rel:<E>, sep) that
  parse_compact maps back to the option text, so the parsed answer has the frozen format v2 shape (evidence "").
- C5 `plan_calls`: when prompt + answer does not fit the budget, the entity is split into neighbourhoods
  (pilot_input.neighbourhoods, as v3.2 B) of at most ceil(n / parts) clusters, one call each.
- C4 (Step 4) is not here: the Step 4 code is not on this branch (wf-v3.9); it waits for wf_v4.1 (plan section 7).
The frozen prompt (pilot_input.INSTRUCTION_V2, render_v2, schema_v2) is not changed: the compact instruction is derived
from it by checked replacements, so a change to the frozen text breaks the derivation loudly.
"""
import json
import re
import numpy as np

from . import llm_cache as LC
from . import pilot_input as PIN

FORMAT = "v2c"            # manifest format of a compact answer (C3)
N_EXAMPLES = 3            # C2
BEFORE, AFTER = 8, 12     # C1 words around the value
BUDGET = 7_500            # prompt + max answer tokens per call (plan 4.2; Llama-3-8B window 8,192)
MAX_PARTS = 4             # C5 gives up above this many calls per entity

_EVIDENCE_OLD = ("Also choose where each cluster belongs: pick ONE placement from the listed options and copy its text\n"
                 "exactly. Quote one example span as evidence. ")
_EVIDENCE_NEW = "Also choose where each cluster belongs: pick ONE placement code from the listed options. "
_TURN_OLD = "Examples are marked with [[...]] inside the turn they come from."
_TURN_NEW = "Examples are marked with [[...]] inside a few words of the turn they come from."
_SHAPE_OLD = PIN.INSTRUCTION_V2[PIN.INSTRUCTION_V2.index('{"attributes"'):]
_SHAPE_NEW = ('{"attributes": [{"name": "graduation_year", "description": "year the degree was finished", "role": "end of the studies"}],\n'
              ' "clusters": [{"cluster_id": "E9#0", "attribute": "graduation_year", "mixed": false, "placement": "cur"},\n'
              '              {"cluster_id": "E9#1", "attribute": "not_attribute", "mixed": false, "placement": "cur"}]}')


def _swap(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"frozen instruction changed: {old[:50]!r} not found once")
    return text.replace(old, new)


def instruction(window=True, compact_answer=True):
    """The A instruction with the C1 / C3 wording; both False gives pilot_input.INSTRUCTION_V2 itself."""
    text = PIN.INSTRUCTION_V2
    if window:
        text = _swap(text, _TURN_OLD, _TURN_NEW)
    if compact_answer:
        text = _swap(_swap(text, _EVIDENCE_OLD, _EVIDENCE_NEW), _SHAPE_OLD, _SHAPE_NEW)
    return text


# ------------------------------------------------------------------ C3 placement codes
def code_of(option):
    """Short code of a placement option text (pilot_input.option_texts)."""
    if option == PIN.SEPARATE:
        return "sep"
    for pat, code in ((r"current entity (\S+)", "cur"), (r"sub-entity of (\S+)", "sub"),
                      (r"other entity (\S+)", "oth:{}"), (r"relationship\((\S+), (\S+)\)", "rel:{}")):
        m = re.fullmatch(pat, option)
        if m:
            return code.format(m.groups()[-1])
    raise ValueError(f"unknown placement option {option!r}")


def option_of(code, entity):
    """The option text of a code for `entity` (inverse of code_of); ValueError for an unknown code."""
    fixed = {"cur": f"current entity {entity}", "sub": f"sub-entity of {entity}", "sep": PIN.SEPARATE}
    if code in fixed:
        return fixed[code]
    kind, _, other = code.partition(":")
    if other and kind == "oth":
        return f"other entity {other}"
    if other and kind == "rel":
        return f"relationship({entity}, {other})"
    raise ValueError(f"unknown placement code {code!r}")


def entity_of(cluster_id):
    return cluster_id.rsplit("#", 1)[0]


# ------------------------------------------------------------------ rendering
def window_text(marked, before=BEFORE, after=AFTER):
    """C1: about `before` words before and `after` words after the [[value]] of a marked turn, "..." where cut."""
    a, b = marked.index("[["), marked.index("]]") + 2
    left, right = marked[:a].split(), marked[b:].split()
    lo = (["..."] if len(left) > before else []) + (left[-before:] if before else [])
    hi = right[:after] + (["..."] if len(right) > after else [])
    return " ".join(lo + [marked[a:b]] + hi)


def _example_lines(export, docs, ci, window, n_examples):
    rows = export.mentions.set_index("mention_id")
    lines = []
    for ex_id, mid in ci.examples[:n_examples]:
        r = rows.loc[mid]
        spk, prev, turn = PIN.example_text(docs[r["dialogue_id"]], r, True)
        if window:
            lines.append(f"- {ex_id} [{spk}] {window_text(turn)}")
        else:  # the frozen line (pilot_input._example_lines, context True)
            lines.append(f"- {ex_id} [{spk}]" + (f" previous turn, {prev} | " if prev else " ") + f"turn: {turn}")
    return lines


def _render_codes(inp):
    lines = ['Placement codes (copy one code into "placement"):']
    lines += [f"- {code_of(t)}: {d}" for t, d in inp.options]
    lines.append("Other entities (id, top values of their 3 biggest clusters):")
    lines += [f"- {e}: " + "; ".join(", ".join(vs) for _, vs in big) for e, big in inp.others.items()]
    return "\n".join(lines)


def render_compact(inp, export, docs, order_seed=None, group_ids=None, window=True, n_examples=N_EXAMPLES,
                   compact_answer=True, part=None):
    """Prompt text of the compact A call; `group_ids` (C5) keeps only those clusters, `part` (i, n) says so in the
    header. All switches off (window False, n_examples None, compact_answer False, no group) gives render_v2(variant v2)."""
    cl = list(inp.clusters)
    if group_ids is not None:
        keep = set(group_ids)
        cl = [c for c in cl if c.cluster_id in keep]
    if order_seed is not None:
        cl = [cl[i] for i in np.random.default_rng(order_seed).permutation(len(cl))]
    head = f"Entity {inp.entity}: {len(cl)} clusters."
    if part is not None:
        head += (f" This is part {part[0]} of {part[1]}: the entity's other clusters are in other calls. Name the "
                 "attributes of these clusters only.")
    parts = [instruction(window, compact_answer), head, _render_codes(inp) if compact_answer else PIN._render_options(inp)]
    for ci in cl:
        parts.append("\n".join([PIN._cluster_head(ci), "Examples:",
                                *_example_lines(export, docs, ci, window, n_examples or len(ci.examples))]))
    parts.append("Return the JSON object now.")
    return "\n\n".join(parts) + "\n"


def schema_compact(inp, group_ids=None):
    """JSON schema of the compact answer: attributes[] as v2; clusters[] {cluster_id, attribute, mixed, placement code}."""
    ids = [c.cluster_id for c in inp.clusters if group_ids is None or c.cluster_id in set(group_ids)]
    s = PIN._schema_attr_clusters(ids, [code_of(t) for t, _ in inp.options])
    clu = s["properties"]["clusters"]["items"]
    del clu["properties"]["evidence"]
    clu["required"] = [k for k in clu["required"] if k != "evidence"]
    return s


# ------------------------------------------------------------------ parsing
def parse_compact(raw, cluster_ids):
    """(obj, errors) of a compact answer: obj in the format v2 shape (evidence "", placement codes mapped back to the
    option text); errors = the v2 checks (llm_cache.parse_response_v2) plus unknown placement codes. A cluster with an
    unknown code keeps the code as its placement, so the error is counted, never repaired."""
    try:
        obj = LC._extract_json(raw, "{", dict)
    except ValueError as e:
        return {}, [str(e)]
    errors, entity = [], entity_of(cluster_ids[0]) if cluster_ids else ""
    clusters = obj.get("clusters")
    if isinstance(clusters, list):
        out = []
        for i, c in enumerate(clusters):
            if isinstance(c, dict):
                c = {**c, "evidence": c.get("evidence", "")}
                if isinstance(c.get("placement"), str):
                    try:
                        c["placement"] = option_of(c["placement"], entity)
                    except ValueError:
                        errors.append(f"clusters[{i}] unknown placement code {c['placement']!r}")
            out.append(c)
        obj = {**obj, "clusters": out}
    v2, more = LC.parse_response_v2(json.dumps(obj), cluster_ids)
    return v2, errors + more


def parse_job(raw, fmt, schema):
    """llm_cache.parse_job plus format v2c (the compact A answer)."""
    if fmt == FORMAT:
        parsed, errs = parse_compact(raw, LC.schema_enum(schema, "cluster_id") or [])
        return parsed, errs, len(parsed.get("clusters") or [])
    return LC.parse_job(raw, fmt, schema)


# ------------------------------------------------------------------ C5 split
def plan_calls(inp, export, docs, prompt_tokens, answer_tokens, budget=BUDGET, max_parts=MAX_PARTS, **switches):
    """[(group_ids or None, part or None)]: one call for the whole entity when prompt_tokens(text) + answer_tokens(n
    clusters) <= budget, else the fewest neighbourhood groups (pilot_input.neighbourhoods, at most ceil(n / parts)
    clusters each) whose every call fits. ValueError when even max_parts calls do not fit. `switches` go to
    render_compact (order None: the order does not change the length)."""
    ids = [c.cluster_id for c in inp.clusters]

    def fits(group, part):
        text = render_compact(inp, export, docs, group_ids=group, part=part, **switches)
        return prompt_tokens(text) + answer_tokens(len(group or ids)) <= budget

    if fits(None, None):
        return [(None, None)]
    for parts in range(2, max_parts + 1):
        groups = PIN.neighbourhoods(export, inp.entity, max_size=-(-len(ids) // parts))
        if sorted(sum(groups, [])) != sorted(ids):
            raise ValueError(f"{inp.entity}: neighbourhoods do not cover the prompt's clusters")
        plan = [(g, (i, len(groups))) for i, g in enumerate(groups, 1)]
        if all(fits(g, p) for g, p in plan):
            return plan
    raise ValueError(f"{inp.entity}: {len(ids)} clusters do not fit in {max_parts} calls of {budget} tokens")
