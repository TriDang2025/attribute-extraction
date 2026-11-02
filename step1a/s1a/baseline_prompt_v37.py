"""wf_v3.7 T10: prompts of the LLM-only baseline (WF_V37_CONTRACT.md, W3). Pure functions; no model, no file access.

The model sees whole dialogues of one entity (speaker-tagged turns, as the pipeline shows them) and no clusters, hints
or dataset name, and lists the columns a table for the entity should store. As many whole dialogues as fit the budget
go in (a dialogue that does not fit is skipped, a shorter later one may still go in).
"""

import json
import random

from .pilot_input import est_tokens

CTX = 32768
OUT_TOKENS = 4096
BUDGET = CTX - OUT_TOKENS   # estimated tokens of one whole prompt (instruction included)
ENTITY_WORD = {"train": "train journey", "hotel": "hotel", "restaurant": "restaurant"}
ENTITY_CODE = {"train": "E1", "hotel": "E0", "restaurant": "E2"}   # as the v3.6 manifest
SERVICE = {"train": "train", "hotel": "hotel", "restaurant": "restaurant"}
VERSIONS = {"v0": None, "v1": 1, "v2": 2}   # version -> shuffle seed (None: the set order)
INSTRUCTION = (
    "Below are dialogues in which people talk about, among other things, a {word}. "
    "List the attributes (columns) that a database table for this entity should store, each with a one-sentence "
    "description.\n"
    "Return ONLY one JSON object, nothing before or after it, of the shape "
    '{{"attributes": [{{"name": "...", "description": "..."}}]}}.\n\n'
    "Dialogues:\n")
SCHEMA = {"type": "object",
          "properties": {"attributes": {"type": "array", "items": {
              "type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}},
              "required": ["name", "description"]}}},
          "required": ["attributes"]}


def render(ent, dialogues):
    """Prompt text: the instruction, then each dialogue (a string of turns joined by newlines) under a header."""
    parts = [INSTRUCTION.format(word=ENTITY_WORD[ent])]
    parts += [f"\n[dialogue {i}]\n{d}\n" for i, d in enumerate(dialogues, 1)]
    return "".join(parts)


def order(ids, version):
    """`ids` in the order of `version`: v0 as given, v1 / v2 shuffled with seed 1 / 2."""
    seed = VERSIONS[version]
    out = list(ids)
    if seed is not None:
        random.Random(seed).shuffle(out)
    return out


def fill(ent, ids, texts, version):
    """(chosen ids in prompt order, prompt text). `texts`: {id: dialogue text}. Greedy in the version's order: a
    dialogue is added when the estimated tokens of the whole prompt stay within BUDGET, else skipped."""
    chosen = []
    for did in order(ids, version):
        if est_tokens(render(ent, [texts[i] for i in chosen + [did]])) <= BUDGET:
            chosen.append(did)
    return chosen, render(ent, [texts[i] for i in chosen])


def entity_ids(ids, services, ent):
    """Ids (keeping their order) whose MultiWOZ services (`services`: {id: list}) include the entity's domain."""
    return [i for i in ids if SERVICE[ent] in services.get(i, [])]


def job_row(ent, set_name, version, n_dialogues, tokens):
    """Manifest row (v3.6 format, family baseline)."""
    name = f"baseline_{ent}_{set_name}_{version}"
    return {"job": name, "entity": ENTITY_CODE[ent], "ent": ent, "variant": "baseline", "run_tag": version,
            "kind": "entity", "stage": 1, "nbhd": None, "cluster_id": "", "prompt": f"baseline/prompts/{name}.txt",
            "schema": f"baseline/prompts/{name}.schema.json", "max_tokens": OUT_TOKENS, "format": "baseline",
            "round": 0, "carry_from": [], "family": "baseline", "set": set_name, "n_dialogues": n_dialogues,
            "est_prompt_tokens": tokens}


def schema_text():
    return json.dumps(SCHEMA, indent=1)
