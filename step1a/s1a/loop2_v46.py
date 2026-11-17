"""wf_v4.6 Y4 (diary Nov 17, roadmap P3 first half): loop 2 for the 8B design, run on the output folder of a finished loop 1 (pipeline_v45).

Loop 2 = Step 1b (top-down review) -> evidence check -> Step 3 naming of the new clusters -> merge with the loop-1 attributes.
The wf_v4.1 loop-2 code is imported, not copied (loop2_v41 evidence check, step1b_v41 input block and generic check, step3_loop2_v41 adapter,
dupcheck_l2_v41 merge rule, nov16_v41 backend / parser / a2 columns). What changes for Llama-3.1-8B (small closed questions, code does the
bookkeeping; guided JSON, temperature 0, the backend's one unguided retry; no regex `pattern` in any schema):
- Step 1b = two closed questions per entity (the input is names, summaries and capped evidence of ONE entity, never dialogues):
  1. verdicts: a keyed "exactly once" answer, one {"verdict": keep|flag, "reason"} per loop-1 attribute id (keys = the ids). The LLM may only
     flag; code never drops anything (a flag is a mark, the attribute stays in every output);
  2. missing: "Which information is still missing for this <entity>?" -> {"missing": [{name, description}]}, at most max_new (maxItems).
  3 orders (attribute order shuffled by seed 0, 1, 2). Vote (wf_v4.1 had none, one call per set): flag when a strict majority of the orders
  that answered for that attribute flag it; a suggested name counts when >= min_votes orders suggest it (key = lowercase words, so
  "Check_in time" = "check in time").
- Evidence check = loop2_v41.run_label per candidate name (the name is the only GLiNER label), thresholds from config/wf_v46_loop2.json.
- Step 3 naming = the frozen A prompt of the entity over the kept loop-2 clusters (step3_loop2_v41.Loop2Run), cut into the frozen v4.4 names
  jobs (step3_v44.names_jobs_for_v44, schema variant of config/wf_v44_step3.json; similar_batches off, no rescue / merge booster: at most 10
  clusters per entity), 3 orders, names -> v2 object -> frozen decisions + vote (step3_loop2_v41), then the v3.8 duplicate check against the
  loop-1 columns (dupcheck_l2_v41, 2 orders).

Reads (out = loop-1 run folder): <out>/step3/scores/final_columns.json, <out>/step3/a_llama44/<set>/a.columns.json (names, descriptions,
examples), results/graph_v22_<set>/ (docs, mentions, instances: the Step 1a-2 output of corpus_v45).
Writes <out>/loop2/:
  step1b/{prompts/, responses/, manifest.json, review.json (votes per entity), labels.json (names sent to the evidence check)}
  evidence/{clusters.json, evidence.csv, summary.md, run_info.json}              (loop2_v41 formats)
  step3/{prompts/, responses/, manifest_names.json, manifest_dupcheck.json, naming.json}
  columns_l2.json {entity: new columns, status new | duplicate}, merged_columns.json {entity: loop-1 + new columns, source, flag},
  attributes.json {entity: [names]} (pipeline_v45 format), a2.columns.json (Step 4 input: a + new columns),
  suggestions.csv + report.md (every suggested name: pass / fail, stage, reason), calls.csv + cost.json (every LLM call).
"""
import contextlib
import json
import re
import time
from collections import Counter
from pathlib import Path

import pandas as pd

from . import batch_v4 as B
from . import batch_v39 as B9
from . import corpus_v45 as CO
from . import dupcheck_l2_v41 as DL
from . import log_v44 as LOG
from . import loop2_v41 as L2
from . import nov16_v41 as NV
from . import paths
from . import pilot_input as PIN
from . import step1b_v41 as S1B
from . import step3_loop2_v41 as S3L
from . import step3_post_v43 as PP
from . import step3_v43 as S3
from . import step3_v44 as S3_44

CONFIG = paths.ROOT / "config" / "wf_v46_loop2.json"
DUP_MAX_TOKENS = 1024          # STEP3.md, duplicate check
VERDICTS = ["keep", "flag"]
FAMILIES = {"verdicts": "loop2_verdicts", "missing": "loop2_missing"}

VERDICTS_INSTRUCTION = """\
Below are the attributes found so far for one kind of thing, a {entity}, by analysing a corpus of dialogues. Each attribute is a kind
of information that people give in the dialogues about such a thing, with a description (when there is one), the type of its values, a
few example values (each with a short piece of text around it) and counts. Lines labelled "checker" are automatic and can be wrong.

Question: is each attribute a good attribute of a {entity}? Answer exactly once for every attribute, using the attribute id as the key,
with one verdict and one short reason:
- keep: a clear, useful attribute of a {entity};
- flag: doubtful (noise, too general, two meanings mixed, or not about a {entity}).
You can only keep or flag an attribute; nothing is removed or renamed.
{json_only} Shape (the ids here are made up):
{{"x:1": {{"verdict": "keep", "reason": "..."}}, "x:2": {{"verdict": "flag", "reason": "..."}}}}

Attributes ({n}):
"""

MISSING_INSTRUCTION = """\
Below are the attributes found so far for one kind of thing, a {entity}, by analysing a corpus of dialogues. Each attribute is a kind
of information that people give in the dialogues about such a thing, with a description (when there is one), the type of its values, a
few example values (each with a short piece of text around it) and counts. Lines labelled "checker" are automatic and can be wrong.

Question: which information is still missing for this {entity}? List attributes that a {entity} normally has and that people would
plausibly mention in such dialogues, but that are missing from the list. At most {max_new}; fewer, or an empty list, is fine. Do not list
an attribute that is already in the list under another name. For each give a name ({max_words} plain words or fewer that a text tagger
can search for, such as "loan period") and a one-line description. Names must be general words that fit any collection of texts about
such things: no example values, no names of places, people or brands, and no names of datasets.
{json_only} Shape (the name here is made up):
{{"missing": [{{"name": "due date", "description": "..."}}]}}

Attributes ({n}):
"""


# ------------------------------------------------------------------ config
def load_config(path=CONFIG, **sections):
    """The loop-2 config; `sections` ({"evidence": {...}}) override single keys inside a section."""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for sec, over in sections.items():
        if sec not in cfg:
            raise ValueError(f"unknown config section {sec!r}")
        unknown = set(over) - set(cfg[sec])
        if unknown:
            raise ValueError(f"unknown {sec} keys {sorted(unknown)}")
        cfg[sec] = {**cfg[sec], **over}
    return cfg


def norm_key(name):
    """Vote key of a name: lowercase words (spaces, underscores and punctuation all separate words)."""
    return " ".join(S1B._words(name))


# ------------------------------------------------------------------ Step 1b: prompts and schemas
def _text(n):
    return {"type": "string", "maxLength": n}


def verdicts_schema(ids, reason_max=120):
    """Keyed schema: exactly one {verdict, reason} per attribute id (all required, no other key)."""
    one = {"type": "object", "properties": {"verdict": {"enum": VERDICTS}, "reason": _text(reason_max)},
           "required": ["verdict", "reason"], "additionalProperties": False}
    return {"type": "object", "properties": {i: one for i in ids}, "required": list(ids), "additionalProperties": False}


def missing_schema(max_new=10, name_max=60, description_max=200):
    """{"missing": [{name, description}]} with at most max_new items."""
    item = {"type": "object", "properties": {"name": _text(name_max), "description": _text(description_max)},
            "required": ["name", "description"], "additionalProperties": False}
    return {"type": "object", "properties": {"missing": {"type": "array", "items": item, "maxItems": max_new}}, "required": ["missing"],
            "additionalProperties": False}


def question_prompts(entity, cols, cfg):
    """{"verdicts": (prompt, schema), "missing": (prompt, schema)} of one entity's columns (S1B.render: capped examples per attribute)."""
    c = cfg["step1b"]
    block = S1B.render(cols) + "\nReturn the JSON object now.\n"
    head = dict(entity=entity, n=len(cols), json_only=S1B._JSON_ONLY)
    v = VERDICTS_INSTRUCTION.format(**head)
    m = MISSING_INSTRUCTION.format(**head, max_new=c["max_new"], max_words=c["max_name_words"])
    for text in (v, m):
        if B._DATASET_WORDS.search(text):
            raise ValueError("dataset name in the instruction")
    return {"verdicts": (v + block, verdicts_schema([x["id"] for x in cols], c["reason_max_chars"])),
            "missing": (m + block, missing_schema(c["max_new"], c["name_max_chars"], c["description_max_chars"]))}


def job_name(set_name, ent, question, order):
    return f"l2s1b_{set_name}_{re.sub(r'[^A-Za-z0-9]+', '_', ent).strip('_')}_{question}_s{order}"


def build_step1b(out, set_name, cols_by_ent, cfg):
    """Prompts + schemas + manifest.json under `out` (= <loop2>/step1b): per entity, question and order one job; the attribute order of
    order o is B9.shuffled_order(cols, o, "<set>/<entity>"). Returns the jobs."""
    c, jobs = cfg["step1b"], []
    for ent, cols in cols_by_ent.items():
        for o in c["orders"]:
            texts = question_prompts(ent, B9.shuffled_order(cols, o, f"{set_name}/{ent}"), cfg)
            for q, (text, schema) in texts.items():
                name = job_name(set_name, ent, q, o)
                B.write(out / "prompts" / f"{name}.txt", text)
                B.write_json(out / "prompts" / f"{name}.schema.json", schema)
                tokens = c["verdict_tokens_per_attribute"] * len(cols) + 100 if q == "verdicts" else c["missing_tokens"]
                jobs.append({"job": name, "family": FAMILIES[q], "format": "s1b", "set": set_name, "ent": ent, "question": q, "order": o,
                             "run_tag": name, "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
                             "max_tokens": tokens, "est_prompt_tokens": PIN.est_tokens(text)})
    B.write_json(out / "manifest.json", {"stage": 1, "jobs": jobs})
    return jobs


# ------------------------------------------------------------------ Step 1b: parse, vote, screen
def parse_verdicts(parsed, ids):
    """({id: {verdict, reason}} of the valid entries, errors). An id with no valid entry gets no vote (code never turns it into a drop)."""
    if not isinstance(parsed, dict):
        return {}, ["answer is not a JSON object"]
    out, errs = {}, [f"unknown key {k!r}" for k in parsed if k not in ids]
    for i in ids:
        v = parsed.get(i)
        if isinstance(v, dict) and v.get("verdict") in VERDICTS:
            out[i] = {"verdict": v["verdict"], "reason": str(v.get("reason", "")).strip()}
        else:
            errs.append(f"no valid verdict for {i}")
    return out, errs


def parse_missing(parsed, max_new):
    """([{name, description}] valid, distinct by key, at most max_new; errors). A bare list is accepted (unguided retry)."""
    items = parsed.get("missing") if isinstance(parsed, dict) else parsed
    if not isinstance(items, list):
        return [], ["answer has no missing list"]
    out, errs, seen = [], [], set()
    for it in items:
        name = str(it.get("name", "")).strip() if isinstance(it, dict) else ""
        if not norm_key(name):
            errs.append(f"item without name: {it!r}")
        elif norm_key(name) not in seen:
            seen.add(norm_key(name))
            out.append({"name": name, "description": str(it.get("description", "")).strip()})
    if len(out) > max_new:
        errs.append(f"{len(out)} items, max {max_new}: extra items dropped")
        out = out[:max_new]
    return out, errs


def vote_verdicts(per_order, ids):
    """{id: {verdict, flags, votes, reasons}}: flag when a strict majority of the orders that gave a valid verdict flag it (a tie, or no
    vote, keeps). per_order = {order: {id: {verdict, reason}}}. Nothing is ever removed."""
    out = {}
    for i in ids:
        votes = [v[i] for v in per_order.values() if i in v]
        flags = [x for x in votes if x["verdict"] == "flag"]
        out[i] = {"verdict": "flag" if len(flags) * 2 > len(votes) else "keep", "flags": len(flags), "votes": len(votes),
                  "reasons": [x["reason"] for x in flags if x["reason"]]}
    return out


def vote_names(per_order, min_votes):
    """Every name suggested in any order: [{key, name, description, orders, votes, voted}] best first. A name counts once per order;
    name and description come from the lowest order that gave them; voted = suggested in >= min_votes orders."""
    seen = {}
    for o in sorted(per_order):
        for it in per_order[o]:
            k = norm_key(it["name"])
            g = seen.setdefault(k, {"key": k, "name": k, "description": "", "orders": []})
            if o not in g["orders"]:
                g["orders"].append(o)
            g["description"] = g["description"] or it["description"]
    rows = [{**g, "votes": len(g["orders"]), "voted": len(g["orders"]) >= min_votes} for g in seen.values()]
    return sorted(rows, key=lambda r: (-r["votes"], r["orders"][0], r["key"]))


def screen(sugg, n_orders, existing_keys, values, cfg):
    """(stage, reason) of a voted suggestion that must stop before the evidence check, else ("", ""): vote, repeats an existing
    attribute, too long, not generic (S1B.generic_errors: corpus word or an example value)."""
    c = cfg["step1b"]
    if not sugg["voted"]:
        return "vote", f"suggested in {sugg['votes']} of {n_orders} orders (needs {c['min_votes']})"
    if sugg["key"] in existing_keys:
        return "check", "repeats an existing attribute name"
    if len(sugg["key"].split()) > c["max_name_words"]:
        return "check", f"name longer than {c['max_name_words']} words"
    errs = S1B.generic_errors(sugg["key"], values)
    return ("check", "; ".join(errs)) if errs else ("", "")


def collect_step1b(out, jobs, cols_by_ent, cfg):
    """review {entity: {verdicts, suggestions, orders_answered, errors}} from the responses under `out` (= <loop2>/step1b)."""
    c, review = cfg["step1b"], {}
    for ent, cols in cols_by_ent.items():
        ids, ver, mis, errs = [x["id"] for x in cols], {}, {}, []
        for j in (j for j in jobs if j["ent"] == ent):
            row = B.last_row(out / "responses" / f"{j['job']}.jsonl")
            if row is None:
                errs.append(f"{j['job']}: no response")
                continue
            if j["question"] == "verdicts":
                got, e = parse_verdicts(row["parsed"], ids)
                if got:
                    ver[j["order"]] = got
            else:
                got, e = parse_missing(row["parsed"], c["max_new"])
                if not any("no missing list" in x for x in e):
                    mis[j["order"]] = got
            errs += [f"{j['job']}: {x}" for x in e] + [f"{j['job']}: finish {row['finish_reason']}"] * (row.get("finish_reason") == "length")
        review[ent] = {"verdicts": vote_verdicts(ver, ids), "suggestions": vote_names(mis, c["min_votes"]),
                       "orders_answered": {"verdicts": sorted(ver), "missing": sorted(mis)}, "errors": errs}
    return review


# ------------------------------------------------------------------ evidence check
def labels_of(review, cols_by_ent, cfg):
    """(labels for loop2_v41.run_label, screened rows). A row per suggested name: entity, name, votes, orders, description, stage, reason
    ("" = goes on to the evidence check). Labels: the name is the only GLiNER label; value_type "text" (no type is asked)."""
    labels, rows = [], []
    for ent, cols in cols_by_ent.items():
        existing = {norm_key(x["name"]) for x in cols}
        values = S1B.example_values(cols)
        n_orders = len(cfg["step1b"]["orders"])
        for s in review[ent]["suggestions"]:
            stage, reason = screen(s, n_orders, existing, values, cfg)
            rows.append({"entity": ent, "name": s["key"], "votes": s["votes"], "orders": s["orders"], "description": s["description"],
                         "stage": stage, "reason": reason})
            if not stage:
                labels.append({"entity": ent, "name": s["key"], "label": s["key"], "description": s["description"] or s["key"],
                               "value_type": "text"})
    return labels, rows


def run_evidence(ri, labels, finals, stage1_of, encoder, gliner_loader, cfg, log=print):
    """Loop-2 clusters (loop2_v41.run_label) of the labels, in label order; one cluster id L2_<entity>#<n> per label."""
    if not labels:
        return []
    docs, mt, inst = ri.docs, ri.export.mentions, ri.export.instances
    items = L2.turn_items(docs)
    item_vecs = encoder.encode([it["text"] for it in items])
    predict = PP.script("loop2_v41").GlinerPredictor(gliner_loader())
    next_id, nums, clusters = int(mt["mention_id"].max()) + 1, Counter(), []
    for lab in L2.check_labels(labels):
        n = nums[lab["entity"]]
        nums[lab["entity"]] += 1
        c = L2.run_label(lab, n, docs, items, item_vecs, encoder, predict, mt, inst, finals[lab["entity"]], stage1_of[lab["entity"]],
                         next_id, cfg["evidence"])
        next_id += c["n_mentions"]
        clusters.append(c)
        log(f"{c['id']} {c['label']}: {c['n_mentions']} spans, keep={c['keep']} ({c['reason']})")
    return clusters


# ------------------------------------------------------------------ Step 3 naming of the kept clusters
@contextlib.contextmanager
def _entities_and_run_key(stage1_of, set_name):
    """pilot_build_v37.a_prompts finds the entity by gold majority and names_jobs_for_v44 reads PP.RUN_KEY: point both at the corpus run
    (restored on exit; the same patch pipeline_v45.use_corpus makes for loop 1)."""
    find, rk = PIN.find_pilot_entity, PP.RUN_KEY
    PIN.find_pilot_entity = lambda mentions, ent: stage1_of[ent]
    PP.RUN_KEY = {**rk, set_name: f"l2_{set_name}"}
    try:
        yield
    finally:
        PIN.find_pilot_entity, PP.RUN_KEY = find, rk


def naming_prompts(ri, kept, stage1_of, set_name):
    """{entity: {order: frozen A prompt text}} over the kept clusters (step3_loop2_v41.Loop2Run + pilot_build_v37.a_prompts)."""
    pbv = PP.script("pilot_build_v37")
    merged = S3L.merge_mentions(ri.export.mentions, kept)
    run = S3L.Loop2Run(ri, merged, kept)
    out = {}
    with _entities_and_run_key(stage1_of, set_name):
        for ent in dict.fromkeys(c["entity"] for c in kept):
            out[ent] = pbv.a_prompts(run, ent)[3]
    return out


def names_jobs(out, set_name, prompts, stage1_of, cfg):
    """Names jobs (frozen v4.4 batches / schema) of every entity and order, files written under `out` (= <loop2>/step3)."""
    s3cfg = S3_44.load_config(switches={"similar_batches": False}, orders=cfg["step3"]["orders"])
    variant = S3_44.names_variant(s3cfg)
    jobs = []
    with _entities_and_run_key(stage1_of, set_name):
        for ent, texts in prompts.items():
            for o in cfg["step3"]["orders"]:
                rows, files = S3_44.names_jobs_for_v44(set_name, ent, o, texts[o], variant, s3cfg)
                S3_44.write_job_files(out, files)
                jobs += rows
    B.write_json(out / "manifest_names.json", {"stage": 0, "names_variant": variant, "jobs": jobs})
    return jobs


def voted_names(out, jobs):
    """{entity: (voted decision table, vote stats, cluster ids, errors)} from the names responses: per order names -> frozen v2 object ->
    frozen decisions; then the frozen vote over the orders (step3_loop2_v41.order_table / voted_table)."""
    res = {}
    for ent in dict.fromkeys(j["ent"] for j in jobs):
        tables, errs, cids = [], [], None
        for o in sorted({j["order"] for j in jobs if j["ent"] == ent}):
            js = sorted((j for j in jobs if j["ent"] == ent and j["order"] == o), key=lambda j: j["batch"])
            maps = []
            for j in js:
                row = B.last_row(out / "responses" / f"{j['job']}.jsonl")
                m, e = S3_44.validate_names_v44(row["raw"], j["cluster_ids"], j["names_variant"]) if row else ({}, ["no response"])
                maps.append(m)
                errs += [f"{j['job']}: {x}" for x in e]
            cids = js[0]["frozen_ids"]
            tables.append(S3L.order_table(S3.v2_object(S3.merge_names(maps)[0], cids), cids, f"s{o}"))
        dec, stats = S3L.voted_table(tables)
        res[ent] = (dec, stats, cids, errs)
    return res


def dupcheck_jobs(out, set_name, ent, finals, dec, clusters, stage1):
    """(jobs, old, new) of the v3.8 duplicate check of one entity: loop-1 columns + the new columns named by `dec`. No new column: no job."""
    old = DL.old_columns({"columns": [{**c, "id": c["cid"]} for c in finals]})
    new = DL.new_columns(dec, clusters, max((c["cid"] for c in old), default=0) + 1)
    jobs = []
    for o, (text, schema) in (DL.prompts(old, new, f"{set_name}/{ent}") if new else {}).items():
        name = f"dupcheck_l2_{set_name}_{re.sub(r'[^A-Za-z0-9]+', '_', ent).strip('_')}_o{o}"
        B.write(out / "prompts" / f"{name}.txt", text)
        B.write_json(out / "prompts" / f"{name}.schema.json", schema)
        jobs.append({"job": name, "ent": ent, "entity": stage1, "family": "dupcheck_l2", "format": "dupcheck", "order_seed": o,
                     "run_tag": f"o{o}", "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json",
                     "max_tokens": DUP_MAX_TOKENS, "n_columns": len(old) + len(new), "est_prompt_tokens": PIN.est_tokens(text)})
    return jobs, old, new


def resolve_entity(out, jobs, old, new):
    """(final new columns of DL.resolve, errors): an order without a valid answer joins nothing (the columns stay new)."""
    parsed, errs = [], []
    for j in jobs:
        row = B.last_row(out / "responses" / f"{j['job']}.jsonl")
        ok = row is not None and isinstance(row["parsed"], dict) and not row["errors"]
        errs += [] if ok else [f"{j['job']}: no valid answer, no joins"]
        parsed.append(row["parsed"] if ok else {"joins": []})
    return DL.resolve(old, new, parsed), errs


# ------------------------------------------------------------------ outputs
def outcomes(rows, final, dec_by_ent, clusters):
    """Final outcome per suggested name (rows of labels_of, in place): stage evidence / step3 / dupcheck / added, passed, reason."""
    by_label = {(c["entity"], c["label"]): c for c in clusters}
    for r in rows:
        r["passed"] = False
        c = by_label.get((r["entity"], r["name"])) if not r["stage"] else None
        if r["stage"] or c is None:
            continue
        r["cluster"] = c["id"]
        if not c["keep"]:
            r["stage"], r["reason"] = "evidence", c["reason"]
            continue
        act = dec_by_ent.get(r["entity"], {}).get(c["id"], "")
        hit = next((f for f in final.get(r["entity"], []) if c["id"] in f["clusters"]), None)
        if hit is None:
            r["stage"], r["reason"] = "step3", f"Step 3 named the cluster {act or 'nothing'}, no new column"
        elif hit["status"] == "duplicate":
            r["stage"], r["reason"] = "dupcheck", f"duplicate of {', '.join(hit['duplicate_of'])} ({hit['reason']})"
        else:
            r["stage"], r["passed"], r["reason"] = "added", True, f"new column {hit['name']}" + (f" (joined {', '.join(hit['joined'])})" if hit["joined"] else "")


def merged_columns(finals, review, final, clusters_by_id):
    """{entity: loop-1 columns (flag = the Step 1b vote, kept in every case) + the new columns with status new}."""
    out = {}
    for ent, cols in finals.items():
        votes = review.get(ent, {}).get("verdicts", {})
        rows = [{"cid": c["cid"], "name": c["name"], "description": c["description"], "n_mentions": c["n_mentions"], "source": "loop1",
                 "flag": votes.get(f"{ent}:{c['cid']}", {}).get("verdict", "keep"),
                 "flag_reasons": votes.get(f"{ent}:{c['cid']}", {}).get("reasons", [])} for c in cols]
        n = max((c["cid"] for c in cols), default=0)
        for f in (f for f in final.get(ent, []) if f["status"] == "new"):
            n += 1
            ids = sorted(m["mention_id"] for cid in f["clusters"] for m in clusters_by_id[cid]["mentions"])
            rows.append({"cid": n, "name": f["name"], "description": f["description"], "n_mentions": f["n_mentions"], "source": "loop2",
                         "flag": "keep", "flag_reasons": [], "clusters": f["clusters"], "top_values": f["top_values"], "mention_ids": ids})
        out[ent] = rows
    return out


def report_md(set_name, review, rows, cfg):
    lines = [f"# Loop 2 (8B design), {set_name}", "",
             "Config: " + ", ".join(f"{k}={v}" for k, v in cfg["evidence"].items()) + f", min_votes={cfg['step1b']['min_votes']}.", "",
             "## Step 1b verdicts (flags are marks; nothing is dropped)", "", "| entity | attributes | flagged | orders answered (verdicts / missing) |",
             "|---|---|---|---|"]
    for ent, r in review.items():
        oa = r["orders_answered"]
        lines.append(f"| {ent} | {len(r['verdicts'])} | {sum(v['verdict'] == 'flag' for v in r['verdicts'].values())} | "
                     f"{len(oa['verdicts'])} / {len(oa['missing'])} |")
    lines += ["", "## Suggested names", "", "| entity | name | votes | result | failed at | reason |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['entity']} | {r['name']} | {r['votes']} | {'pass' if r['passed'] else 'fail'} | {'' if r['passed'] else r['stage']} | "
              f"{r['reason'].replace('|', '/')} |" for r in rows]
    errs = [f"- {ent}: {e}" for ent, r in review.items() for e in r["errors"]]
    return "\n".join(lines + (["", "## Answer errors", *errs] if errs else []) + [""])


def write_calls(l2dir):
    """calls.csv (one row per LLM call: job, tokens, seconds, finish, guided, retried) and cost.json (per stage folder + total)."""
    rows = LOG.call_rows(l2dir)
    if rows:
        pd.DataFrame(rows).to_csv(l2dir / "calls.csv", index=False, encoding="utf-8", lineterminator="\n")
    cost = {}
    for stage in ("step1b", "step3"):
        rs = [r for r in rows if r["file"].startswith(stage + "/")]
        secs = [r["job_seconds"] for r in rs if r.get("job_seconds") not in (None, "")]
        cost[stage] = {**LOG.call_totals(rs), "model_seconds": round(sum(float(s) for s in secs), 1) if secs else None}
    cost["total"] = {k: sum(cost[s][k] for s in ("step1b", "step3")) for k in ("calls", "prompt_tokens", "output_tokens")}
    B.write_json(l2dir / "cost.json", cost)
    return cost


# ------------------------------------------------------------------ the loop
def run_loop2(out, set_name, backend, encoder, gliner_loader, cfg=None, log=print, root=paths.ROOT):
    """Loop 2 on the loop-1 folder `out` (pipeline_v45 layout). backend.run(folder, jobs) answers jobs (VllmBackend44 or a fake);
    encoder.encode(list[str]) -> unit vectors (bge-m3); gliner_loader() -> a loaded GLiNER model (called only when a name reaches the
    evidence check). Returns a dict of counts, the cost and the written folder."""
    out, cfg, t0 = Path(out), cfg or load_config(), time.time()
    l2 = out / "loop2"
    finals = B.read_json(out / "step3" / "scores" / "final_columns.json")[set_name]
    a_file = S3_44.a_llama44_file(set_name, out / "step3")
    pre = a_file.with_name("a.premerge.columns.json")       # entity_names_v46.merge_a_columns ran: loop 2 works on the unmerged columns
    a_cols = B.read_json(pre if pre.exists() else a_file)
    cols_by_ent = {}
    for c in a_cols:
        cols_by_ent.setdefault(S1B._entity(c), []).append(c)
    stage1_of = {ent: cs[0]["entity"] for ent, cs in finals.items() if cs}
    ri = PP.script("pilot_build_v37").RunInput(CO.run_dir(set_name, root), 0)

    log(f"loop 2 step 1b: {len(cols_by_ent)} entities, {len(a_cols)} attributes")
    s1 = l2 / "step1b"
    jobs = build_step1b(s1, set_name, cols_by_ent, cfg)
    backend.run(s1, jobs)
    review = collect_step1b(s1, jobs, cols_by_ent, cfg)
    labels, rows = labels_of(review, cols_by_ent, cfg)
    B.write_json(s1 / "review.json", review)
    B.write_json(s1 / "labels.json", labels)

    log(f"loop 2 evidence check: {len(labels)} names")
    t1 = time.time()
    clusters = run_evidence(ri, labels, finals, stage1_of, encoder, gliner_loader, cfg, log)
    ev = l2 / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    B.write_json(ev / "clusters.json", clusters)
    pd.DataFrame(L2.evidence_rows(clusters)).to_csv(ev / "evidence.csv", index=False, encoding="utf-8", lineterminator="\n")
    B.write(ev / "summary.md", L2.summary_md(clusters, set_name, cfg["evidence"], (s1 / "labels.json").as_posix(), time.time() - t1))
    B.write_json(ev / "run_info.json", {"set": set_name, "config": cfg["evidence"], "n_labels": len(labels),
                                        "n_kept": sum(c["keep"] for c in clusters), "seconds": round(time.time() - t1, 1)})

    kept = S3L.select_clusters(clusters)
    log(f"loop 2 step 3: {len(kept)} clusters pass the evidence check")
    s3, final, dec_by_ent, naming = l2 / "step3", {}, {}, {}
    if kept:
        s3_jobs = names_jobs(s3, set_name, naming_prompts(ri, kept, stage1_of, set_name), stage1_of, cfg)
        backend.run(s3, s3_jobs)
        by_id = {c["id"]: c for c in clusters}
        dup_jobs = []
        for ent, (dec, stats, cids, errs) in voted_names(s3, s3_jobs).items():
            dec_by_ent[ent] = dict(zip(dec["cluster_id"], dec["action"]))
            jobs_e, old, new = dupcheck_jobs(s3, set_name, ent, finals[ent], dec, by_id, stage1_of[ent])
            dup_jobs += jobs_e
            naming[ent] = {"vote": stats, "errors": errs, "old": old, "new": new, "dup_jobs": jobs_e}
        B.write_json(s3 / "manifest_dupcheck.json", {"stage": 2, "jobs": dup_jobs})
        if cfg["step3"]["dupcheck"]:
            backend.run(s3, dup_jobs)
        for ent, n in naming.items():
            if cfg["step3"]["dupcheck"]:
                final[ent], errs = resolve_entity(s3, n["dup_jobs"], n["old"], n["new"])
            else:     # no check: every new column stays new
                final[ent], errs = DL.resolve(n["old"], n["new"], []), []
            n["errors"] += errs
        B.write_json(s3 / "naming.json", {e: {k: v for k, v in n.items() if k in ("vote", "errors")} for e, n in naming.items()})
    outcomes(rows, final, dec_by_ent, clusters)

    clusters_by_id = {c["id"]: c for c in clusters}
    merged = merged_columns(finals, review, final, clusters_by_id)
    B.write_json(l2 / "columns_l2.json", final)
    B.write_json(l2 / "merged_columns.json", merged)
    B.write_json(l2 / "attributes.json", {e: [c["name"] for c in cs] for e, cs in merged.items()})
    B.write_json(l2 / "a2.columns.json", NV.a2_columns(a_cols, final, clusters_by_id)[0])
    pd.DataFrame(rows).to_csv(l2 / "suggestions.csv", index=False, encoding="utf-8", lineterminator="\n")
    B.write(l2 / "report.md", report_md(set_name, review, rows, cfg))
    cost = write_calls(l2)
    info = {"entities": len(cols_by_ent), "attributes": len(a_cols), "flagged": sum(v["verdict"] == "flag" for r in review.values() for v in r["verdicts"].values()),
            "suggested": len(rows), "voted": sum(r["votes"] >= cfg["step1b"]["min_votes"] for r in rows), "evidence_kept": len(kept),
            "new_columns": sum(f["status"] == "new" for fs in final.values() for f in fs),
            "duplicates": sum(f["status"] == "duplicate" for fs in final.values() for f in fs),
            "cost": cost, "seconds": round(time.time() - t0, 1), "folder": l2.as_posix()}
    B.write_json(l2 / "run_info.json", info)
    return info


# ------------------------------------------------------------------ fake model (laptop plumbing; no GPU)
class FakeLoop2LLM(NV.FakeLLM):
    """nov16_v41.FakeLLM with valid answers for the loop-2 families. Verdicts: the first attribute (smallest id) is flagged in orders 0 and 1 (a majority),
    all others kept. Missing: order 0 "parking facility, area, contact number", order 1 "parking facility, area, star rating", order 2
    "parking facility, star rating". Names: "fake_new_<n>" for cluster L2_<entity>#<n>. Duplicate check: no joins."""
    MISSING = {0: ["parking facility", "area", "contact number"], 1: ["parking facility", "area", "star rating"], 2: ["parking facility", "star rating"]}

    def respond(self, job, prompt, schema):
        fam, props = job["family"], schema.get("properties", {})
        if fam == FAMILIES["verdicts"]:
            self.n_made += 1
            first = sorted(props)[0]
            return json.dumps({k: {"verdict": "flag" if k == first and job["order"] in (0, 1) else "keep", "reason": "fake"} for k in props})
        if fam == FAMILIES["missing"]:
            self.n_made += 1
            return json.dumps({"missing": [{"name": n, "description": f"fake description of {n}"} for n in self.MISSING[job["order"]]]})
        if fam == "names":
            self.n_made += 1
            return json.dumps({k: f"fake_new_{k.rsplit('#', 1)[1]}" for k in props})
        return super().respond(job, prompt, schema)
