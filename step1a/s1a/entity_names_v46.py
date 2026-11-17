"""wf_v4.6 Y3: LLM names for the predicted entities (replaces corpus_v45.entity_names, which uses the MultiWOZ keyword list), and the merge of
entities that get the same name.

- One call per predicted entity (the Step 1a k-means entities E0..): 5 example mentions with a short context and the top values; guided
  JSON {"name": str} (no regex pattern, no length limits: a pattern broke vLLM guided decoding in v4.4), temperature 0, the backend's one
  unguided retry. Jobs and answers live under <out>/names/ (prompts/, responses/), so log_v44.call_rows(<out>/names) gives the call log.
- A name is cleaned to lowercase snake_case, 1-3 words; an unusable answer falls back to the entity id in lowercase ("e2").
- Equal names stay separate entities for Step 3 (frozen; its keys must be unique: name, name_2, ...). The merge map {name: [entity ids]}
  goes to <out>/entity_names.json; `merge_a_columns` joins the columns of the entities of a group into one block (heading = name) in the
  Step 4 input a_llama44/<set>/a.columns.json, and only when some group has two or more entities (else the file is not touched).
Writer -> reader: names_for_run -> run_dir/entities.json ({entity id: key}; corpus_v45.entity_map) and <out>/entity_names.json
(pipeline_v46); merge_step4_input -> a.columns.json with a `mention_ids` field per column (step4_v44.mention_ids_of reads it first).
"""
import json
import re
import zlib
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from . import batch_v4 as B
from . import corpus_v45 as CO
from . import nov16_v41 as NV
from . import step4_v44 as S4

SEED = 0
N_EXAMPLES = 5
N_VALUES = 8
CONTEXT_CHARS = 140
MAX_WORDS = 3
MAX_TOKENS = 32
JOB_FIELDS = {"family": "ename", "format": "judge", "run_tag": "n0", "kind": "entity", "stage": 1}

INSTRUCTION = """Below are mentions taken from dialogues. They all belong to one entity type, which will become a table in a database.
Name the entity type with one short noun phrase: lowercase, snake_case, 1 to 3 words (for example flight, movie_ticket).

Most frequent values: {values}

Example mentions (value, with its sentence):
{examples}

Return JSON: {{"name": "<entity type>"}}
"""


def schema():
    """One required string property; no `pattern`, no length limits."""
    return {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"], "additionalProperties": False}


def top_values(df, n=N_VALUES):
    """The n most frequent norm values (ties: alphabetical)."""
    c = Counter(df["norm_value"])
    return [v for v, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def pick_examples(df, entity, k=N_EXAMPLES, seed=SEED):
    """k mention rows of the entity, seeded by (seed, entity id): distinct norm values first, then the rest of the shuffled order."""
    rng = np.random.default_rng([seed, zlib.crc32(entity.encode("utf-8"))])
    rows = df.sort_values("mention_id").iloc[rng.permutation(len(df))]
    seen, first, rest = set(), [], []
    for r in rows.itertuples():
        (rest if r.norm_value in seen else first).append(r)
        seen.add(r.norm_value)
    return (first + rest)[:k]


def render(df, entity, k=N_EXAMPLES, seed=SEED):
    """Prompt text of one entity from its mention rows (columns mention_id, text, norm_value, context)."""
    ex = "\n".join(f'{i}. "{r.text}" in: "{r.context[:CONTEXT_CHARS]}"' for i, r in enumerate(pick_examples(df, entity, k, seed), 1))
    return INSTRUCTION.format(values=" | ".join(top_values(df)), examples=ex)


def clean_name(text):
    """Lowercase snake_case name of 1..MAX_WORDS words from a model answer, or None when nothing usable (not a string, empty, too long)."""
    if not isinstance(text, str):
        return None
    words = [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w]
    return "_".join(words) if 1 <= len(words) <= MAX_WORDS else None


def parse_name(parsed):
    """Cleaned name of a parsed answer {"name": str}, or None."""
    return clean_name(parsed.get("name")) if isinstance(parsed, dict) else None


def unique_keys(names):
    """{entity id: unique key} from {entity id: name}, entity ids in numeric order: the name, then name_2, name_3, ... (never a key already used)."""
    keys, used = {}, set()
    for e in sorted(names, key=lambda x: int(x[1:])):
        key, n = names[e], 1
        while key in used:
            n += 1
            key = f"{names[e]}_{n}"
        used.add(key)
        keys[e] = key
    return keys


def merge_map(names):
    """{name: [entity ids]} (numeric order of the ids, names by first entity). Groups with two or more ids are merged at the Step 4 input."""
    groups = {}
    for e in sorted(names, key=lambda x: int(x[1:])):
        groups.setdefault(names[e], []).append(e)
    return groups


# ---------------------------------------------------------------- the LLM calls
def build_jobs(set_name, out, mentions, entities, seed=SEED):
    """Write <out>/prompts/ename_<set>_<entity>.{txt,schema.json}; return the jobs of the entities that have mentions."""
    out = Path(out)
    jobs = []
    for e in entities:
        df = mentions[mentions["entity"] == e]
        if df.empty:
            continue
        name = f"ename_{set_name}_{e}"
        B.write(out / "prompts" / f"{name}.txt", render(df, e, seed=seed))
        B.write_json(out / "prompts" / f"{name}.schema.json", schema())
        jobs.append({"job": name, "entity": e, "ent": e, "set": set_name, "run": set_name, "prompt": f"prompts/{name}.txt",
                     "schema": f"prompts/{name}.schema.json", "max_tokens": MAX_TOKENS, **JOB_FIELDS})
    return jobs


def read_names(out, jobs):
    """{entity id: cleaned name or None} from the response rows of the jobs."""
    res = {}
    for j in jobs:
        row = B.last_row(Path(out) / "responses" / f"{j['job']}.jsonl")
        res[j["entity"]] = parse_name(row["parsed"]) if row else None
    return res


def names_for_run(set_name, run_out, backend, root=CO.paths.ROOT, seed=SEED, log=print):
    """Name the entities of results/graph_v22_<set>/ with the LLM and write the result. Returns the record
    {"names": {id: name}, "keys": {id: unique key}, "groups": {name: [ids]}, "fallback": [ids], "calls": backend info}.
    Writes run_dir/entities.json = {id: key} (what corpus_v45.entity_map reads) and <run_out>/entity_names.json = the record."""
    rd = CO.run_dir(set_name, root)
    ids = list(json.loads((rd / "entities.json").read_text(encoding="utf-8")))
    m = pd.read_csv(rd / "spans" / "mentions.csv", usecols=["mention_id", "text", "norm_value", "context", "entity"], dtype=str, keep_default_na=False)
    m["mention_id"] = m["mention_id"].astype(int)
    names_out = Path(run_out) / "names"
    jobs = build_jobs(set_name, names_out, m, ids, seed)
    info = backend.run(names_out, jobs) if jobs else {"jobs": 0, "run": 0, "parse_errors": 0}
    got = read_names(names_out, jobs)
    names = {e: got.get(e) or e.lower() for e in ids}
    rec = {"names": names, "keys": unique_keys(names), "groups": merge_map(names), "fallback": [e for e in ids if not got.get(e)], "calls": info}
    (rd / "entities.json").write_text(json.dumps(rec["keys"], indent=1) + "\n", encoding="utf-8", newline="\n")
    B.write_json(Path(run_out) / "entity_names.json", rec)
    log(f"entity names {set_name}: {names}; merged groups {list(key_groups(rec))}; fallback {rec['fallback']}")
    return rec


# ---------------------------------------------------------------- merge at the Step 4 input
def key_groups(rec, present=None):
    """{name: [Step 3 keys]} of the groups with two or more entities (empty: nothing to merge). present: only the keys that run through Step 3
    (entities with no cluster do not)."""
    g = {n: [rec["keys"][e] for e in es if present is None or rec["keys"][e] in present] for n, es in rec["groups"].items()}
    return {n: ks for n, ks in g.items() if len(ks) > 1}


def merge_step4_input(cols, mention_ids, groups):
    """Step 4 input columns with the entities of each group joined into one block. cols = a.columns.json rows (ids "<key>:<n>"); mention_ids =
    {column id: [mention ids]} (final_columns.json); groups = {name: [Step 3 keys]}. Blocks keep the order of the first key of each group;
    inside a group: keys in the given order, then column order; ids "<name>:<1..>". Every column gets its `mention_ids` (the reader
    step4_v44.mention_ids_of uses that field, as the old ids no longer exist in final_columns.json)."""
    name_of = {k: n for n, ks in groups.items() for k in ks}
    rank = {k: i for ks in groups.values() for i, k in enumerate(ks)}
    blocks = {}
    for c in cols:
        key = c["id"].split(":")[0]
        blocks.setdefault(name_of.get(key, key), []).append((rank.get(key, 0), c))
    out = []
    for name, rows in blocks.items():
        for n, (_, c) in enumerate(sorted(rows, key=lambda r: r[0]), 1):    # stable: column order kept inside a key
            out.append({**c, "id": f"{name}:{n}", "mention_ids": list(mention_ids[c["id"]])})
    return out


def merge_a_columns(step3_out, set_name, groups, log=print):
    """Rewrite <step3_out>/a_llama44/<set>/a.columns.json with merge_step4_input (original kept as a.premerge.columns.json); no groups: no-op.
    Returns the number of columns written, or None."""
    if not groups:
        return None
    p = S4.columns_path("a_llama44", set_name, {"a_llama44": Path(step3_out) / "a_llama44"})
    cols = B.read_json(p)
    final = B.read_json(Path(step3_out) / "scores" / "final_columns.json")[set_name]
    ids = {f"{e}:{c['cid']}": c["mention_ids"] for e, cs in final.items() for c in cs}
    B.write_json(p.with_name("a.premerge.columns.json"), cols)
    merged = merge_step4_input(cols, ids, groups)
    B.write_json(p, merged)
    log(f"step 4 input: merged {groups}: {len(cols)} columns -> {len(merged)}, "
        f"{len({c['id'].split(':')[0] for c in cols})} tables -> {len({c['id'].split(':')[0] for c in merged})}")
    return len(merged)


# ---------------------------------------------------------------- fake model (laptop plumbing, tests)
class FakeNames(NV.FakeLLM):
    """FakeLLM that answers the entity-name jobs: name = "Fake Entity <k>" with k = entity number mod `n_names` (so equal names occur)."""

    def __init__(self, n_names=3, **kw):
        super().__init__(**kw)
        self.n_names = n_names

    def respond(self, job, prompt, schema):
        if job["family"] == "ename":
            self.n_made += 1
            return json.dumps({"name": f"Fake Entity {int(job['entity'][1:]) % self.n_names}"})
        return super().respond(job, prompt, schema)
