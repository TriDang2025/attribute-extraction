"""wf_v4.3 (diary Nov 13) U2: Step 3 v4.3 for Llama-3.1-8B. Small closed questions; code does the bookkeeping.

Change from option B (keyed_v42): no free attribute list (Llama looped and invented names there). The model answers ONE name per cluster
id; code builds the attribute list from the names.
- Prompt: a short instruction, the U1 worked examples (examples_v43.STEP3_EXAMPLE_1 / _2, under "Worked examples (other domain):"), the
  other entities of the run for context (as the frozen prompt shows them), and the frozen cluster blocks (head + "Examples:" + example
  lines, copied from the frozen A prompts) of ONE batch of 5 clusters.
- Batches: each order s0 / s1 / s2 keeps the cluster order of the frozen s0 / s1 / s2 prompt (results/wf_v42/t1b_step3_keyed/prompts, the
  prompts of STEP3.md step 1-2) and cuts it into batches of 5, so batch neighbours differ per order. 3 entities x 3 orders x 2 sets.
- Schema: {"<cluster id>": name} (keyed, required, no other keys); name = "not_attribute" or snake_case, at most 60 characters.
- Merge by code: the names of the batches of one entity and order are joined (every cluster exactly once); a name is normalised (lower
  case, runs of other characters -> "_") and equal names are one attribute. The v2 object the frozen decision code reads is built from
  them: attributes = the distinct names, each used by at least one cluster ("names no cluster uses" is 0 by design); description and
  role are empty. `mixed` and `placement` are not asked: the frozen scoring path reads `mixed` only with require_mixed=True (not used
  for A s012: run_data_v37.load_a), the split pass runs on every candidate cluster anyway, and placement / evidence are handover
  information that no later scoring step reads.
- The A answers of the 3 orders then go through the frozen vote, split pass, reconcile and v3.8 duplicate check (step3_post_v43).
The job format is "judge" (nov16_v41.PLAIN_FORMATS: plain JSON), because nov16_v41.parse_answer is frozen and knows no names format; the
real format is `format43` in the manifest row. Names are validated here (validate_names), not by the parser.
"""
import json
import re
from pathlib import Path

import pandas as pd

from . import batch_v4 as B
from . import examples_v43 as EX
from . import pilot_input as PIN
from . import pilot_verify as PV
from . import step3_post_v43 as PP
from . import step4_inputs as I

ROOT = PP.ROOT
OUT = ROOT / "results" / "wf_v43" / "u2"
BATCH = 5
ORDERS = (0, 1, 2)
NAME_MAX = 60
NAME_PATTERN = "^(not_attribute|[a-z][a-z0-9_]{1,58})$"
NOT_ATTRIBUTE = "not_attribute"
NAMES_MAX_TOKENS = 400
INSTRUCTION = """\
Below are clusters of values taken from the dialogue turns of one entity (a candidate table). Each cluster is a candidate column.
The examples of a cluster are marked with [[...]] inside the turn they come from.
Give every cluster ONE name: a short snake_case attribute name (for example graduation_year), or "not_attribute" for noise
(yes, ok, thanks, booking words, values that a database would not store).
Use role-specific names: values that play different roles (where something starts and where it ends, the earliest and the latest
time allowed) get different names. Clusters that hold the same kind of value with the same role get exactly the same name."""
EXAMPLES_HEAD = "Worked examples (other domain):"
A_ROW = {"variant": "v2", "kind": "entity", "cluster_id": "", "format": "v2", "family": "a", "assembled": True, "prompt": "", "schema": ""}


# ---------------------------------------------------------------- prompts and schema
def parse_frozen_prompt(text):
    """{"entity", "others": [lines of the other-entities block], "blocks": [(cluster id, block text)] in prompt order} of a frozen A prompt
    (pilot_input.render_v2: instruction, entity line, options block, one block per cluster)."""
    parts = text.strip("\n").split("\n\n")
    blocks = [(m.group(1), p) for p in parts if (m := re.match(r"### (\S+)", p))]
    opts = next(p for p in parts if p.startswith("Placement options")).split("\n")
    k = next(i for i, line in enumerate(opts) if line.startswith("Other entities"))
    entity = re.match(r"Entity (\S+): \d+ clusters", next(p for p in parts if p.startswith("Entity ")))
    if not blocks or entity is None:
        raise ValueError("not a frozen A prompt (no cluster blocks or no entity line)")
    return {"entity": entity.group(1), "others": opts[k:], "blocks": blocks}


def batches(items, size=BATCH):
    """`items` cut into consecutive batches of `size` (the last one may be shorter): every item exactly once."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def names_schema(ids):
    """Keyed guided schema: one required string per cluster id, no other keys."""
    name = {"type": "string", "maxLength": NAME_MAX, "pattern": NAME_PATTERN}
    return {"type": "object", "properties": {c: name for c in ids}, "required": list(ids), "additionalProperties": False}


def render_names(entity, i, n_batches, n_clusters, others, blocks):
    """Prompt of one batch. blocks = [(cluster id, block text)] of the batch."""
    ids = ", ".join(c for c, _ in blocks)
    return "\n\n".join([INSTRUCTION, EXAMPLES_HEAD + "\n\n" + EX.STEP3_EXAMPLE_1 + "\n\n" + EX.STEP3_EXAMPLE_2,
                        f"Entity {entity}: batch {i} of {n_batches} ({n_clusters} clusters in all). Other entities, for context:\n"
                        + "\n".join(others),
                        *[b for _, b in blocks],
                        f'Return ONLY one JSON object, nothing before or after it: one key per cluster id ({ids}) and its name as the '
                        f'value, like {{"{blocks[0][0]}": "<name>"}}.']) + "\n"


def names_jobs_for(set_name, ent, order, text):
    """(job rows, [(name, prompt text, schema)]) of one entity and order from its frozen A prompt `text`."""
    fp = parse_frozen_prompt(text)
    cut = batches(fp["blocks"])
    run = PP.RUN_KEY[set_name]
    rows, files = [], []
    for i, blocks in enumerate(cut, 1):
        name = f"{ent}_names_{run}_s{order}_b{i}"
        prompt = render_names(fp["entity"], i, len(cut), len(fp["blocks"]), fp["others"], blocks)
        rows.append({"job": name, "entity": fp["entity"], "ent": ent, "set": set_name, "run": run, "family": "names", "format": "judge",
                     "format43": "names_v43", "run_tag": f"s{order}b{i}", "order": order, "batch": i, "cluster_ids": [c for c, _ in blocks],
                     "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": NAMES_MAX_TOKENS,
                     "est_prompt_tokens": PIN.est_tokens(prompt)})
        files.append((name, prompt, names_schema([c for c, _ in blocks])))
    return rows, files


def build(out):
    """Prompts + schemas of the names jobs (manifest_names.json), the frozen split jobs and the assembled A rows (manifest.json). Reads the
    frozen A prompts of results/wf_v42/t1b_step3_keyed; returns (names jobs, manifest jobs)."""
    out = Path(out)
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    names, a_rows = [], []
    for j in PP.t1b_a_jobs():                     # the 18 frozen A prompts: set x entity x order
        order = int(j["run_tag"][1:])
        rows, files = names_jobs_for(j["set"], j["ent"], order, (PP.T1B / j["prompt"]).read_text(encoding="utf-8"))
        for name, prompt, schema in files:
            (out / "prompts" / f"{name}.txt").write_text(prompt, encoding="utf-8", newline="\n")
            B.write_json(out / "prompts" / f"{name}.schema.json", schema)
        names += rows
        a_rows.append({**A_ROW, "job": j["job"], "entity": j["entity"], "ent": j["ent"], "run_tag": f"s{order}", "run": j["run"], "set": j["set"]})
    B.write_json(out / "manifest_names.json", {"stage": 0, "jobs": names})
    examples = [x for s in PP.SETS for x in PP.a_example_rows(s, [j for j in a_rows if j["set"] == s])]
    return names, PP.build_common(out, a_rows, examples)


def names_jobs(out):
    return B.read_json(Path(out) / "manifest_names.json")["jobs"]


# ---------------------------------------------------------------- answers: validate, merge, assemble
def norm_name(name):
    """Snake_case form of a name: lower case, every run of other characters -> "_", no edge underscores ("" when nothing is left)."""
    return re.sub(r"[^a-z0-9]+", "_", str(name or "").lower()).strip("_")


def validate_names(raw, ids):
    """({cluster id: normalised name}, errors) of one names answer: a JSON object with exactly the cluster ids, every value a non-empty
    string of at most NAME_MAX characters after normalisation. Bad entries are left out of the mapping."""
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}, ["answer is not valid JSON"]
    if not isinstance(obj, dict):
        return {}, ["answer is not a JSON object"]
    errs = [f"missing cluster {c}" for c in ids if c not in obj] + [f"unknown key {k!r}" for k in obj if k not in ids]
    out = {}
    for c in ids:
        n = norm_name(obj.get(c)) if isinstance(obj.get(c), str) else ""
        if c in obj and (not n or len(n) > NAME_MAX):
            errs.append(f"bad name for {c}: {obj[c]!r}")
        elif n:
            out[c] = n
    return out, errs


def merge_names(batch_maps):
    """One {cluster id: name} from the maps of the batches (a cluster is in one batch only; a repeat raises). Equal names are equal strings
    because validate_names normalised them. Also returns the names that more than one batch used (merged by code)."""
    merged, seen = {}, {}
    for k, m in enumerate(batch_maps):
        for c, n in m.items():
            if c in merged:
                raise ValueError(f"cluster {c} is in two batches")
            merged[c] = n
            seen.setdefault(n, set()).add(k)
    return merged, sorted(n for n, ks in seen.items() if len(ks) > 1 and n != NOT_ATTRIBUTE)


def v2_object(names, order_ids):
    """The frozen v2 object {attributes, clusters} of a name mapping: attributes = distinct names (not_attribute is none) in the order of
    the clusters; a cluster without a name is left out (the frozen decision code gives it action "")."""
    attrs = list(dict.fromkeys(n for c in order_ids if (n := names.get(c)) and n != NOT_ATTRIBUTE))
    return {"attributes": [{"name": n, "description": "", "role": ""} for n in attrs],
            "clusters": [{"cluster_id": c, "attribute": names[c], "evidence": "", "mixed": False, "placement": ""}
                         for c in order_ids if c in names]}


def assemble_a(out):
    """Merge the names answers into the 18 assembled A responses (responses/<ent>_a_<run>_s<n>.jsonl, one row each, rewritten on every
    call) and return their stats rows: set, ent, order, clusters, batches, batches_ok, names (distinct), not_attribute, merged_across_batches,
    end_names, names_no_cluster (0 by design), errors. A batch with no valid answer leaves its clusters out of the object."""
    out, stats, rows = Path(out), [], []
    jobs = names_jobs(out)
    for a in [j for j in PP.read_manifest(out) if j["family"] == "a"]:
        mine = sorted((j for j in jobs if (j["set"], j["ent"], j["order"]) == (a["set"], a["ent"], int(a["run_tag"][1:]))),
                      key=lambda j: j["batch"])
        maps, errs, ok = [], [], 0
        for j in mine:
            last = B.last_row(out / "responses" / f"{j['job']}.jsonl")
            m, e = validate_names(last["raw"], j["cluster_ids"]) if last else ({}, [f"{j['job']}: no response"])
            ok += not e
            maps.append(m)
            errs += [f"{j['job']}: {x}" for x in e] + ([f"{j['job']}: finish {last['finish_reason']}"] if last and last["finish_reason"] == "length" else [])
        order_ids = [c for j in mine for c in j["cluster_ids"]]
        names, merged = merge_names(maps)
        obj = v2_object(names, order_ids)
        used = {n for n in names.values() if n != NOT_ATTRIBUTE}
        p = out / "responses" / f"{a['job']}.jsonl"
        p.write_text(json.dumps({"key": a["job"], "job": a["job"], "format": "v2", "run_tag": a["run_tag"], "guided": True,
                                 "finish_reason": "stop", "model": "assembled by code from the names answers", "raw": json.dumps(obj),
                                 "parsed": obj, "errors": errs, "assembled": True, "from_jobs": [j["job"] for j in mine]},
                                ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        stats.append({"set": a["set"], "ent": a["ent"], "order": a["run_tag"], "clusters": len(order_ids), "batches": len(mine),
                      "batches_ok": ok, "clusters_named": len(names), "names": len(used), "not_attribute": sum(n == NOT_ATTRIBUTE for n in names.values()),
                      "merged_across_batches": len(merged), "end_names": sum(PP.is_end_name(n) for n in used),
                      "names_no_cluster": len(set(a_attr["name"] for a_attr in obj["attributes"]) - used), "errors": len(errs)})
    pd.DataFrame(stats).to_csv(out / "names_stats.csv", index=False, encoding="utf-8", lineterminator="\n")
    return stats


# ---------------------------------------------------------------- run
def run(out, backend):
    """The whole U2 chain on `backend` (nov16_v41.VllmBackend or a fake): names + split pass together (independent), assemble A by code,
    then reconcile and the duplicate check, each built from the answers before it. Returns {stage: backend info, "assemble": {answers, errors}}."""
    info = {"names+split": backend.run(out, names_jobs(out) + PP.stage_jobs(out, "split"))}
    stats = assemble_a(out)
    info["assemble"] = {"answers": len(stats), "errors": sum(r["errors"] for r in stats)}
    info.update(PP.run_post(out, backend, stages=("reconcile", "dupcheck")))
    return info


# ---------------------------------------------------------------- input a_llama43 for Step 4
def a_llama43_file(set_name, out=OUT):
    """Absolute path of the Step 4 input `a_llama43` of a set (same format as results/wf_v4/inputs/<set>/a.columns.json)."""
    return Path(out) / "a_llama43" / set_name / "a.columns.json"


def a_llama43_files(out=OUT, root=ROOT):
    """{set: path relative to `root`, with forward slashes}: the `a2_files` argument of nov16_v41.step4_chains, or the `columns_file` of
    one chain of input a_llama43 (batch_v4.chain_columns reads it as it reads input a)."""
    return {s: a_llama43_file(s, out).relative_to(root).as_posix() for s in PP.SETS}


def a_columns(final_cols, mentions, k=I.N_EXAMPLES, width=I.WIDTH):
    """Input columns from the final columns of one set ({ent: [column dicts of final_columns.json]}) and the mention table (indexed by
    mention_id): ids "<ent>:<n>", examples and value type as input a (step4_inputs.examples_of / dominant_type); description and role are
    empty (Llama v4.3 names only), no checker signal or flag (the v3.8 evidence calls are not part of U2)."""
    cols = []
    for ent in PP.ENTS:
        for c in final_cols[ent]:
            df = mentions.loc[sorted(c["mention_ids"])]
            cols.append({"id": f"{ent}:{c['cid']}", "name": c["name"], "description": c["description"], "role": "",
                         "value_type": I.dominant_type(df["text"]), "examples": I.examples_of(df, k, width), "n_mentions": len(df),
                         "n_dialogues": int(df["dialogue_id"].nunique()), "signal": "", "flag": ""})
    return cols


def write_a_llama43(out=OUT):
    """Write a_llama43/<set>/a.columns.json from scores/final_columns.json (score() output); returns {set: n columns}."""
    final = B.read_json(Path(out) / "scores" / "final_columns.json")
    sizes = {}
    for s in PP.SETS:
        cols = a_columns(final[s], I.load_mentions(s, ROOT))
        B.write_json(a_llama43_file(s, out), cols)
        sizes[s] = len(cols)
    return sizes


# ---------------------------------------------------------------- figure data
def attribute_list(parsed, errors=()):
    """Facts of one A answer (frozen v2 object) for the figure: listed attributes with the number of clusters that use each, names used but
    not declared, `_end`-style names, not_attribute clusters."""
    parsed = parsed if isinstance(parsed, dict) else {}
    clusters = [c for c in parsed.get("clusters") or [] if isinstance(c, dict)]
    use = {}
    for c in clusters:
        n = PV.norm_name(c.get("attribute"))
        use[n] = use.get(n, 0) + 1
    listed = [PV.norm_name(a.get("name")) for a in parsed.get("attributes") or [] if isinstance(a, dict) and a.get("name")]
    attrs = [{"name": n, "n_clusters": use.get(n, 0), "declared": True} for n in dict.fromkeys(listed)]
    attrs += [{"name": n, "n_clusters": k, "declared": False} for n, k in use.items() if n not in listed and n not in PP.FREE_NAMES]
    return {"n_clusters": len(clusters), "n_listed": len(set(listed)), "attributes": attrs,
            "unused": [a["name"] for a in attrs if not a["n_clusters"]], "undeclared": [a["name"] for a in attrs if not a["declared"]],
            "end_names": [a["name"] for a in attrs if PP.is_end_name(a["name"])],
            "not_attribute_clusters": use.get(PV.norm_name(NOT_ATTRIBUTE), 0), "parse_errors": list(errors)}


def _rel(p):
    """`p` relative to the step1a root with forward slashes, else absolute."""
    try:
        return Path(p).relative_to(ROOT).as_posix()
    except ValueError:
        return Path(p).as_posix()


def fig_train_attrs(out=OUT, dest=None):
    """results/wf_v43/u2/fig_train_attrs.json (+ .csv): the train attribute list of dev50b, order 0, for Qwen frozen, Llama option B and Llama
    v4.3 (assembled). Returns the dict."""
    out = Path(out)
    src = {"qwen_frozen": ROOT / "results" / "loop1_v37" / "colab" / "responses" / "train_a_v22d50b_s0.jsonl",
           "llama_option_b": PP.T1B / "responses" / "train_a_v22d50b_s0.jsonl",
           "llama_v43": out / "responses" / "train_a_v22d50b_s0.jsonl"}
    doc = {"set": "dev50b", "entity": "train", "order": "s0", "sources": {}}
    for k, p in src.items():
        objs = PV.load_objects(p) if p.exists() else []
        last = B.last_row(p) or {}
        doc["sources"][k] = {"file": _rel(p), **attribute_list(objs[0] if objs else {}, last.get("errors") or [])}
    dest = Path(dest) if dest else out / "fig_train_attrs.json"
    B.write_json(dest, doc)
    rows = [{"source": k, "attribute": a["name"], "n_clusters": a["n_clusters"], "declared": a["declared"]}
            for k, s in doc["sources"].items() for a in s["attributes"]]
    pd.DataFrame(rows, columns=["source", "attribute", "n_clusters", "declared"]).to_csv(
        dest.with_suffix(".csv"), index=False, encoding="utf-8", lineterminator="\n")
    return doc
