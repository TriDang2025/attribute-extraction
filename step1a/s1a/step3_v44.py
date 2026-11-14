"""wf_v4.4 (diary Nov 14) T1 + T4: Step 3 v4.4 for Llama-3.1-8B-Instruct. Base: step3_v43 (names per cluster, batches of 5, 3 orders, the
frozen vote). New code only; the v4.3 files are imported, never edited. Switches and thresholds: config/wf_v44_step3.json.

T1 guided names fix: v4.3's guided names answers failed on 137/138 calls. Schema variants (names_schema_v44):
  v0 as v4.3 | v1 no regex `pattern` on the values | v2 keys without "#" (E0#3 -> E0_3, mapped back by code) | v3 = v1 + v2 |
  v4 = v3 without maxLength (a hedge, tried last). probe_jobs / evaluate_probe pick the first of v1, v2, v3, v4, v0 whose 3 guided
  answers parse with 0 errors and no retry (results/wf_v44/t1/choice.json, read by T4).
T4 boosters, each with a switch (all off + variant v0 = the v4.3 names jobs and prompts):
  similar_batches  clusters of an entity ordered by a nearest-neighbour chain over bge-m3 cluster centroids, batches cut from the chain.
  rescue           every cluster named not_attribute gets a yes/no question ("Is this information about <entity>?"); on yes, a name.
  merge            pairs of column names of one entity with name cosine >= merge.cosine get a yes/no ("Same information?"); yes pairs merge.
Stages (every stage is built from the answers before it):
  names + keyed split (split_v44, T2) -> rescue questions -> rescue names -> merge questions -> assemble the 18 A answers by code ->
  reconcile -> v3.8 duplicate check (step3_post_v43) -> score (step3_post_v43.score) -> a_llama44 (write_a_llama44).
Run folder `out` = the v4.3 U2 layout plus manifest_{names,split44,rescue_q,rescue_n,merge}.json, blocks.json (cluster blocks of the
frozen prompts, so later stages need no frozen files) and config_used.json. `orders` (config) smaller than 3: the missing orders are copies
of order 0 in the A answers (the vote of identical answers is that answer); used by the ablation runs (order 0 only).
Name vectors: results/wf_v44/t4/name_vecs.npz, written only by the full T4 run (NameVectors.save); other runs read it and keep new
names in memory.
"""
import copy
import json
import re
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from . import batch_v4 as B
from . import examples_v43 as EX
from . import llm_cache as LC
from . import log_v44 as LOG
from . import mentions as MN
from . import nov16_v41 as NV
from . import pilot_input as PIN
from . import split_v44 as SP
from . import step3_post_v43 as PP
from . import step3_v43 as S3
from . import step4_inputs as I

ROOT = PP.ROOT
RES = ROOT / "results" / "wf_v44"
OUT_T1, OUT_T4, OUT_ABLATE = RES / "t1", RES / "t4", RES / "t4_ablate"
CONFIG = ROOT / "config" / "wf_v44_step3.json"
NOT_ATTRIBUTE = S3.NOT_ATTRIBUTE
NAME_MAX = S3.NAME_MAX
VARIANTS = ("v0", "v1", "v2", "v3", "v4")
PROBE_ORDER = ("v1", "v2", "v3", "v4", "v0")
WIRE_HASH = ("v2", "v3", "v4")                  # variants whose keys have no "#"
NO_PATTERN = ("v1", "v3", "v4")
NO_MAXLEN = ("v4",)
YESNO_MAX_TOKENS = 30
SWITCHES = ("similar_batches", "rescue", "merge")
_ID_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*#\d+")
_MARK_RE = re.compile(r"\[\[(.+?)\]\]")


# ---------------------------------------------------------------- config
def load_config(path=CONFIG, switches=None, **override):
    """The step 3 config (json) with `switches` ({name: bool}) and top-level `override`s applied; unknown switch names raise."""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg = {**cfg, **override, "switches": {**cfg["switches"], **(switches or {})}}
    bad = [k for k in cfg["switches"] if k not in SWITCHES]
    if bad:
        raise ValueError(f"unknown switch {bad}; choose from {SWITCHES}")
    return cfg


def with_switches(cfg, switches):
    """Copy of `cfg` with `switches` ({name: bool}) set; unknown names raise."""
    bad = [k for k in switches if k not in SWITCHES]
    if bad:
        raise ValueError(f"unknown switch {bad}; choose from {SWITCHES}")
    c = copy.deepcopy(cfg)
    c["switches"].update(switches)
    return c


def names_variant(cfg, choice_path=None):
    """The names schema variant of a run: config "names_variant", or the T1 choice file when it is "from_choice"."""
    v = cfg["names_variant"]
    if v == "from_choice":
        p = Path(choice_path or RES / "t1" / "choice.json")
        if not p.exists():
            raise FileNotFoundError(f"{p} not found: run the T1 probe first or set names_variant in the config")
        v = B.read_json(p)["chosen"]
    if v not in VARIANTS:
        raise ValueError(f"unknown names variant {v!r}; choose from {VARIANTS}")
    return v


# ---------------------------------------------------------------- T1: names schema variants
def wire_id(cid, variant):
    """The key the model sees for cluster id `cid` ("E0#3" -> "E0_3" for the #-free variants)."""
    return cid.replace("#", "_") if variant in WIRE_HASH else cid


def names_schema_v44(ids, variant="v0"):
    """Keyed guided schema of a names answer for `variant` (see the module doc); v0 is step3_v43.names_schema."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown names variant {variant!r}; choose from {VARIANTS}")
    if variant == "v0":
        return S3.names_schema(ids)
    name = {"type": "string"}
    if variant not in NO_MAXLEN:
        name["maxLength"] = NAME_MAX
    if variant not in NO_PATTERN:
        name["pattern"] = S3.NAME_PATTERN
    keys = [wire_id(c, variant) for c in ids]
    return {"type": "object", "properties": {k: dict(name) for k in keys}, "required": keys, "additionalProperties": False}


def rewrite_ids(text, ids, variant):
    """`text` with every id of `ids` (and the worked examples' ids) written as the model sees it (identity for variants that keep "#")."""
    if variant not in WIRE_HASH:
        return text
    known = sorted(set(ids) | set(_ID_RE.findall(EX.STEP3_EXAMPLE_1 + EX.STEP3_EXAMPLE_2)), key=len, reverse=True)
    pat = re.compile("(?<![\\w#])(" + "|".join(re.escape(c) for c in known) + ")(?!\\d)")
    return pat.sub(lambda m: wire_id(m.group(1), variant), text)


def unkey_names(raw, ids, variant):
    """Raw names answer with the original cluster ids as keys (JSON text; text that is no JSON object is returned as is)."""
    try:
        obj = LC._extract_json(raw, "{", dict)
    except (ValueError, TypeError):
        return raw
    back = {wire_id(c, variant): c for c in ids}
    return json.dumps({back.get(k, k): v for k, v in obj.items()}, ensure_ascii=False)


def validate_names_v44(raw, ids, variant="v0"):
    """({cluster id: normalised name}, errors) as step3_v43.validate_names, after mapping the keys back."""
    return S3.validate_names(unkey_names(raw, ids, variant), ids)


def render_names_v44(entity, i, n_batches, n_clusters, others, blocks, variant="v0"):
    """step3_v43.render_names with the ids written for `variant`."""
    return rewrite_ids(S3.render_names(entity, i, n_batches, n_clusters, others, blocks), [c for c, _ in blocks], variant)


# ---------------------------------------------------------------- booster 1: similar batches
def cluster_vectors(set_name, root=ROOT):
    """{cluster id: unit centroid of its mention vectors (bge-m3)} read from results/graph_v22_<set>/spans/vectors.npz + mentions.csv
    (read only)."""
    ex = MN.load(Path(root) / "results" / f"graph_v22_{set_name}" / "spans")
    pos = {int(m): i for i, m in enumerate(ex.ids)}
    out = {}
    for cid, g in ex.mentions.groupby("cluster_id"):
        v = ex.x[[pos[int(m)] for m in g["mention_id"]]].mean(axis=0)
        out[str(cid)] = v / np.linalg.norm(v)
    return out


def similar_order(items, vecs, key=lambda x: x[0]):
    """`items` ordered as a nearest-neighbour chain: start at the first item, then always the unused item with the highest cosine to
    the last one (ties: earlier position). Items without a vector keep their order at the end. Pure; every item exactly once."""
    have = [x for x in items if key(x) in vecs]
    rest = [x for x in items if key(x) not in vecs]
    chain, left = [], list(have)
    while left:
        nxt = left[0] if not chain else max(left, key=lambda x: (float(vecs[key(chain[-1])] @ vecs[key(x)]), -left.index(x)))
        chain.append(nxt)
        left.remove(nxt)
    return chain + rest


# ---------------------------------------------------------------- blocks, descriptions
def block_mentions(block):
    m = re.search(r"\(mentions (\d+)", block)
    return int(m.group(1)) if m else 0


def block_values(block, k=8):
    """Distinct values marked [[...]] in the example lines of a cluster block, in order, at most `k`."""
    return list(dict.fromkeys(_MARK_RE.findall(block)))[:k]


def block_examples(block, k=2):
    """The first `k` example lines of a cluster block without their leading "- <example id> "."""
    lines = [re.sub(r"^- \S+ ", "", x) for x in block.split("\n") if x.startswith("- ")]
    return lines[:k]


def entity_description(blocks, n=3):
    """The entity in the words of the frozen "Other entities" lines: top values of its `n` biggest clusters (blocks = [(id, text)])."""
    big = sorted(blocks, key=lambda b: -block_mentions(b[1]))[:n]
    return "; ".join(", ".join(block_values(t, 3)) for _, t in big)


# ---------------------------------------------------------------- names jobs (T1 variants, booster 1)
def names_jobs_for_v44(set_name, ent, order, text, variant="v0", cfg=None, vecs=None, name_fmt="{ent}_names_{run}_s{order}_b{i}"):
    """(job rows, [(name, prompt text, schema)]) of one entity and order from its frozen A prompt `text`. With the similar_batches switch
    off (and variant v0) this is step3_v43.names_jobs_for; with it on the clusters are first ordered by similar_order over `vecs`
    ({cluster id: vector}) starting at the first cluster of the frozen order."""
    cfg = cfg or load_config()
    fp = S3.parse_frozen_prompt(text)
    frozen_ids = [c for c, _ in fp["blocks"]]
    blocks = similar_order(fp["blocks"], vecs) if cfg["switches"]["similar_batches"] else fp["blocks"]
    cut = S3.batches(blocks, cfg["batch"])
    run = PP.RUN_KEY[set_name]
    rows, files = [], []
    for i, bl in enumerate(cut, 1):
        name = name_fmt.format(ent=ent, run=run, order=order, i=i, variant=variant)
        ids = [c for c, _ in bl]
        prompt = render_names_v44(fp["entity"], i, len(cut), len(blocks), fp["others"], bl, variant)
        rows.append({"job": name, "entity": fp["entity"], "ent": ent, "set": set_name, "run": run, "family": "names", "format": "judge",
                     "format43": "names_v43", "format44": "names", "names_variant": variant, "run_tag": f"s{order}b{i}", "order": order,
                     "batch": i, "cluster_ids": ids, "frozen_ids": frozen_ids, "prompt": f"prompts/{name}.txt",
                     "schema": f"prompts/{name}.schema.json", "max_tokens": S3.NAMES_MAX_TOKENS, "est_prompt_tokens": PIN.est_tokens(prompt)})
        files.append((name, prompt, names_schema_v44(ids, variant)))
    return rows, files


def write_job_files(out, files):
    for name, prompt, schema in files:
        B.write(Path(out) / "prompts" / f"{name}.txt", prompt)
        B.write_json(Path(out) / "prompts" / f"{name}.schema.json", schema)


def probe_jobs(out, variants=PROBE_ORDER, cfg=None, set_name="dev50", order=0, batch=1):
    """The T1 probe: for every variant the same 3 cluster batches (the first batch of train / hotel / restaurant, order 0 of dev50, in the
    frozen cluster order: the v4.3 batches). Writes prompts, schemas and manifest_probe.json; returns the job rows."""
    cfg = with_switches(cfg or load_config(), {"similar_batches": False})
    rows = []
    for ent in PP.ENTS:
        text = (PP.T1B / "prompts" / f"{ent}_a_{PP.RUN_KEY[set_name]}_s{order}.txt").read_text(encoding="utf-8")
        for v in variants:
            r, f = names_jobs_for_v44(set_name, ent, order, text, v, cfg, name_fmt="{ent}_probe_{variant}_b{i}")
            write_job_files(out, f[batch - 1:batch])
            rows.append({**r[batch - 1], "family": "probe"})
    B.write_json(Path(out) / "manifest_probe.json", {"stage": 0, "jobs": rows})
    return rows


def _guided_raw(row):
    """The guided answer text of a row: guided_raw when the retry won, else raw if the row is a guided one."""
    return row.get("guided_raw") if row.get("guided_raw") is not None else (row.get("raw") if row.get("guided") else None)


def probe_row_ok(row, ids, variant):
    """True when the guided answer parsed: guided, no retry, finish stop, JSON valid and validate_names has 0 errors."""
    if not row or not row.get("guided") or row.get("retried") or row.get("errors") or row.get("finish_reason") != "stop":
        return False
    return not validate_names_v44(row.get("raw") or "", ids, variant)[1]


def evaluate_probe(out, rows=None):
    """Score the probe answers per variant, write results/<out>/choice.json (+ guided_raw.jsonl: the guided text of every probe job, also
    when it failed) and return the choice dict: chosen = the first variant of PROBE_ORDER with 3/3 ok; none ok -> the variant with the
    most ok answers (earlier in PROBE_ORDER on a tie) and passed false."""
    out = Path(out)
    rows = rows or B.read_json(out / "manifest_probe.json")["jobs"]
    table, raw_rows = {}, []
    for v in dict.fromkeys(r["names_variant"] for r in rows):
        mine = [r for r in rows if r["names_variant"] == v]
        t = table[v] = {"jobs": len(mine), "ok": 0, "retried": 0, "errors": 0, "finish": [], "guided": 0}
        for j in mine:
            last = B.last_row(out / "responses" / f"{j['job']}.jsonl")
            ok = probe_row_ok(last, j["cluster_ids"], v)
            t["ok"] += ok
            if last:
                t["retried"] += bool(last.get("retried"))
                t["errors"] += bool(last.get("errors") or (last.get("guided") and validate_names_v44(_guided_raw(last) or "", j["cluster_ids"], v)[1]))
                t["finish"].append(last.get("guided_finish_reason") or last.get("finish_reason"))
                t["guided"] += bool(last.get("guided"))
            raw_rows.append({"job": j["job"], "variant": v, "ok": ok, "guided_raw": _guided_raw(last or {}), "guided_errors": (last or {}).get("guided_errors"),
                             "finish": (last or {}).get("guided_finish_reason") or (last or {}).get("finish_reason")})
    order = [v for v in PROBE_ORDER if v in table]
    passed = [v for v in order if table[v]["ok"] == table[v]["jobs"] > 0]
    chosen = passed[0] if passed else max(order, key=lambda v: (table[v]["ok"], -order.index(v)))
    choice = {"chosen": chosen, "passed": bool(passed), "rule": "first of " + ", ".join(order) + " with all jobs guided, parsed, no retry",
              "variants": table}
    B.write_json(out / "choice.json", choice)
    (out / "guided_raw.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in raw_rows), encoding="utf-8", newline="\n")
    return choice


def run_probe(out, backend, cfg=None, variants=PROBE_ORDER):
    """T1 on `backend` (VllmBackend44 or a fake): build the probe jobs, run them, write choice.json; returns (choice, backend info)."""
    rows = probe_jobs(out, variants, cfg)
    info = backend.run(out, rows)
    return evaluate_probe(out, rows), info


# ---------------------------------------------------------------- build
def build(out, cfg=None, variant=None, vecs=None):
    """Prompts + schemas of the names jobs (orders of cfg only), the keyed split jobs, the assembled A rows (all 18) and blocks.json; returns
    (names jobs, manifest jobs). `vecs` = {set: {cluster id: vector}} for the similar_batches switch (default: cluster_vectors of the sets)."""
    cfg = cfg or load_config()
    variant = variant or names_variant(cfg)
    out = Path(out)
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    if cfg["switches"]["similar_batches"] and vecs is None:
        vecs = {s: cluster_vectors(s) for s in PP.SETS}
    names, a_rows, doc = [], [], {}
    for j in PP.t1b_a_jobs():
        order = int(j["run_tag"][1:])
        text = (PP.T1B / j["prompt"]).read_text(encoding="utf-8")
        if order in cfg["orders"]:
            rows, files = names_jobs_for_v44(j["set"], j["ent"], order, text, variant, cfg, (vecs or {}).get(j["set"]))
            write_job_files(out, files)
            names += rows
        fp = S3.parse_frozen_prompt(text)
        if order == 0:
            doc[f"{j['set']}/{j['ent']}"] = {"entity": fp["entity"], "others": fp["others"], "frozen_ids": [c for c, _ in fp["blocks"]],
                                             "desc": entity_description(fp["blocks"]), "blocks": dict(fp["blocks"])}
        a_rows.append({**S3.A_ROW, "job": j["job"], "entity": j["entity"], "ent": j["ent"], "run_tag": f"s{order}", "run": j["run"], "set": j["set"]})
    B.write_json(out / "manifest_names.json", {"stage": 0, "jobs": names})
    B.write_json(out / "blocks.json", doc)
    B.write_json(out / "config_used.json", {**cfg, "names_variant_used": variant})
    examples = [x for s in PP.SETS for x in PP.a_example_rows(s, [j for j in a_rows if j["set"] == s])]
    jobs = PP.build_common(out, a_rows, examples)
    split_rows = [j for j in jobs if j["family"] == "split"]
    SP.split_jobs(out, split_rows)
    PP.write_manifest(out, [j if j["family"] != "split" else {**j, "assembled": True} for j in jobs])
    return names, PP.read_manifest(out)


def names_jobs(out):
    return B.read_json(Path(out) / "manifest_names.json")["jobs"]


def _stage_jobs(out, name):
    p = Path(out) / name
    return B.read_json(p)["jobs"] if p.exists() else []


def blocks_doc(out):
    return B.read_json(Path(out) / "blocks.json")


# ---------------------------------------------------------------- state: names per (set, entity, order)
def read_base(out):
    """{(set, ent, order): {"frozen_ids", "names" {cid: name}, "errors", "batches", "ok", "across"}} from the names answers (keys mapped back)."""
    out, groups, res = Path(out), {}, {}
    for j in names_jobs(out):
        groups.setdefault((j["set"], j["ent"], j["order"]), []).append(j)
    for key, js in groups.items():
        js.sort(key=lambda j: j["batch"])
        maps, errs, ok = [], [], 0
        for j in js:
            last = B.last_row(out / "responses" / f"{j['job']}.jsonl")
            m, e = validate_names_v44(last["raw"], j["cluster_ids"], j["names_variant"]) if last else ({}, ["no response"])
            ok += not e
            maps.append(m)
            errs += [f"{j['job']}: {x}" for x in e] + ([f"{j['job']}: finish length"] if last and last["finish_reason"] == "length" else [])
        names, across = S3.merge_names(maps)
        res[key] = {"frozen_ids": js[0]["frozen_ids"], "names": names, "errors": errs, "batches": len(js), "ok": ok, "across": across}
    return res


def _cid(c):
    return c.replace("#", "-")


# ---------------------------------------------------------------- booster 2: recall rescue
YESNO_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string", "enum": ["yes", "no"]}}, "required": ["answer"],
                "additionalProperties": False}
YESNO_FORMAT = 'Return ONLY one JSON object, nothing before or after it: {"answer": "yes"} or {"answer": "no"}.'


def render_rescue_q(entity, desc, block):
    """Yes/no prompt for one cluster that was named not_attribute: the values and 2 example sentences."""
    vals = ", ".join(f"[[{v}]]" for v in block_values(block))
    ex = "\n".join(f"- {x}" for x in block_examples(block))
    return (f"Below is ONE cluster of values taken from the dialogue turns of entity {entity} (a candidate table). The values of {entity} are "
            f"mostly like: {desc}.\nAn earlier step called this cluster noise. Look again.\n"
            f"Is this information about the entity {entity}? Answer yes if the values are data that {entity} has (a property a database "
            f"would store for it). Answer no if they are chat words, booking words, or data about something else.\n\n"
            f"Values: {vals}\nExamples:\n{ex}\n\n{YESNO_FORMAT}\n")


def render_rescue_n(entity, others, block, used, variant):
    """Names prompt (the v4.3 one-cluster prompt) with the names already used for the entity added before the cluster."""
    cid = re.match(r"### (\S+)", block).group(1)
    text = S3.render_names(entity, 1, 1, 1, others, [(cid, block)])
    note = ("Names already used for this entity (use one of them when the cluster holds the same kind of value with the same role): "
            + (", ".join(used) if used else "none yet"))
    return rewrite_ids(text.replace("\n\n### ", "\n\n" + note + "\n\n### ", 1), [cid], variant)


def build_rescue_q(out, cfg):
    """One yes/no job per (set, cluster) that at least one order named not_attribute. Writes manifest_rescue_q.json; returns the rows."""
    out, doc, rows = Path(out), blocks_doc(out), []
    ask = {}
    for (s, ent, _), st in read_base(out).items():
        ask.setdefault((s, ent), set()).update(c for c, n in st["names"].items() if n == NOT_ATTRIBUTE)
    for (s, ent), cids in sorted(ask.items()):
        d = doc[f"{s}/{ent}"]
        for cid in [c for c in d["frozen_ids"] if c in cids]:
            name = f"{ent}_rescueq_{PP.RUN_KEY[s]}_{_cid(cid)}"
            B.write(out / "prompts" / f"{name}.txt", render_rescue_q(d["entity"], d["desc"], d["blocks"][cid]))
            B.write_json(out / "prompts" / f"{name}.schema.json", YESNO_SCHEMA)
            rows.append({"job": name, "entity": d["entity"], "ent": ent, "set": s, "run": PP.RUN_KEY[s], "family": "rescue_q", "format": "judge",
                         "format44": "yesno", "run_tag": "q", "cluster_id": cid, "prompt": f"prompts/{name}.txt",
                         "schema": f"prompts/{name}.schema.json", "max_tokens": YESNO_MAX_TOKENS})
    B.write_json(out / "manifest_rescue_q.json", {"stage": 2, "jobs": rows})
    return rows


def parse_yes_no(raw):
    """"yes" / "no" of a yes/no answer, None when it is no JSON object with answer yes / no."""
    try:
        a = LC._extract_json(raw, "{", dict).get("answer")
    except (ValueError, TypeError):
        return None
    a = str(a).strip().lower()
    return a if a in ("yes", "no") else None


def yes_no_answers(out, jobs):
    """{job name: "yes" | "no" | None (no answer or unparsable)}."""
    res = {}
    for j in jobs:
        last = B.last_row(Path(out) / "responses" / f"{j['job']}.jsonl")
        res[j["job"]] = parse_yes_no(last["raw"]) if last else None
    return res


def build_rescue_n(out, cfg, variant):
    """One names job per (set, entity, order, cluster) that the order named not_attribute and the yes/no question answered yes."""
    out, doc, rows = Path(out), blocks_doc(out), []
    ans = yes_no_answers(out, _stage_jobs(out, "manifest_rescue_q.json"))
    for (s, ent, o), st in sorted(read_base(out).items()):
        d = doc[f"{s}/{ent}"]
        used = sorted({n for n in st["names"].values() if n != NOT_ATTRIBUTE})
        for cid in [c for c in st["frozen_ids"] if st["names"].get(c) == NOT_ATTRIBUTE]:
            if ans.get(f"{ent}_rescueq_{PP.RUN_KEY[s]}_{_cid(cid)}") != "yes":
                continue
            name = f"{ent}_rescuen_{PP.RUN_KEY[s]}_s{o}_{_cid(cid)}"
            B.write(out / "prompts" / f"{name}.txt", render_rescue_n(d["entity"], d["others"], d["blocks"][cid], used, variant))
            B.write_json(out / "prompts" / f"{name}.schema.json", names_schema_v44([cid], variant))
            rows.append({"job": name, "entity": d["entity"], "ent": ent, "set": s, "run": PP.RUN_KEY[s], "family": "rescue_n", "format": "judge",
                         "format44": "names", "names_variant": variant, "run_tag": f"n{o}", "order": o, "cluster_ids": [cid],
                         "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": S3.NAMES_MAX_TOKENS})
    B.write_json(out / "manifest_rescue_n.json", {"stage": 3, "jobs": rows})
    return rows


def apply_rescue(out, base):
    """Copy of `base` where every rescued cluster has its new name (answers of the rescue names jobs; not_attribute or an invalid answer
    leaves the cluster as it was). Returns (state, {(set, ent, order): [rescued cluster ids]})."""
    out, state, named = Path(out), copy.deepcopy(base), {}
    for j in _stage_jobs(out, "manifest_rescue_n.json"):
        last = B.last_row(out / "responses" / f"{j['job']}.jsonl")
        m, _ = validate_names_v44(last["raw"], j["cluster_ids"], j["names_variant"]) if last else ({}, [])
        cid = j["cluster_ids"][0]
        if m.get(cid) and m[cid] != NOT_ATTRIBUTE:
            key = (j["set"], j["ent"], j["order"])
            state[key]["names"][cid] = m[cid]
            named.setdefault(key, []).append(cid)
    return state, named


# ---------------------------------------------------------------- booster 3: duplicate merge
class NameVectors:
    """Vectors of column names (text = the name with "_" as spaces). Loaded from an npz (names, vecs) when it exists; `encode_missing`
    adds the names it does not have through `encoder(list of str) -> (n, d) array` (unit vectors); `save` writes the npz (only the T4
    full run calls it, so that file has a single writer)."""

    def __init__(self, path=None, encoder=None):
        self.path, self.encoder, self.vecs, self.n_new = Path(path) if path else None, encoder, {}, 0
        if self.path and self.path.exists():
            z = np.load(self.path, allow_pickle=False)
            self.vecs = {str(n): v for n, v in zip(z["names"], z["vecs"])}

    @staticmethod
    def text(name):
        return str(name).replace("_", " ")

    def encode_missing(self, names):
        todo = sorted({self.text(n) for n in names} - set(self.vecs))
        if todo:
            if self.encoder is None:
                raise ValueError(f"no encoder for {len(todo)} new names (pass an encoder, e.g. bge_m3_encoder())")
            v = np.asarray(self.encoder(todo), dtype=np.float32)
            v = v / np.linalg.norm(v, axis=1, keepdims=True)
            self.vecs.update(zip(todo, v))
            self.n_new += len(todo)

    def cosine(self, a, b):
        return float(self.vecs[self.text(a)] @ self.vecs[self.text(b)])

    def save(self, path=None):
        p = Path(path or self.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        names = sorted(self.vecs)
        np.savez(p, names=np.array(names), vecs=np.stack([self.vecs[n] for n in names]) if names else np.zeros((0, 0), dtype=np.float32))
        return p


def bge_m3_encoder(model="BAAI/bge-m3", device=None):
    """Encoder for NameVectors on Colab (or a laptop with the model downloaded): sentence-transformers bge-m3, unit vectors."""
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(model, device=device)
    return lambda texts: m.encode(list(texts), batch_size=64, normalize_embeddings=True, convert_to_numpy=True)


class FakeEncoder:
    """Deterministic laptop encoder: hashed character trigrams (names that share letters get a high cosine); no model."""

    def __init__(self, dim=64):
        self.dim = dim

    def __call__(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            t = f"  {t} "
            for k in range(len(t) - 2):
                out[i, zlib.crc32(t[k:k + 3].encode()) % self.dim] += 1.0
        return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)


def name_clusters(state_key):
    """{name: [cluster ids]} of one (set, ent, order) state in frozen order, not_attribute left out."""
    res = {}
    for c in state_key["frozen_ids"]:
        n = state_key["names"].get(c)
        if n and n != NOT_ATTRIBUTE:
            res.setdefault(n, []).append(c)
    return res


def candidate_pairs(names, nv, threshold, cap):
    """[(cosine, a, b)] of the name pairs with cosine >= threshold, highest first, at most `cap` (ties by names)."""
    pairs = [(nv.cosine(a, b), a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    return sorted([p for p in pairs if p[0] >= threshold], key=lambda p: (-p[0], p[1], p[2]))[:cap]


def render_merge_q(entity, a, b, ca, cb, blocks):
    """Yes/no prompt for one pair of columns: each with its name, example values and one example sentence."""
    def side(label, name, cids):
        vals = list(dict.fromkeys(v for c in cids for v in block_values(blocks[c])))[:8]
        big = max(cids, key=lambda c: block_mentions(blocks[c]))
        ex = block_examples(blocks[big], 1)
        return f"Column {label}: {name}\n  values: " + ", ".join(f"[[{v}]]" for v in vals) + "\n  example: " + (ex[0] if ex else "")
    return (f"Below are two columns of one table (entity {entity}). Each column has a name and example values from the dialogue turns.\n"
            f"Is it the SAME information: the same kind of value with the same role, only named differently? Values that play different "
            f"roles (where something starts and where it ends, the earliest and the latest time allowed) are different information.\n\n"
            f"{side('A', a, ca)}\n{side('B', b, cb)}\n\nSame information?\n{YESNO_FORMAT}\n")


def build_merge_q(out, cfg, state, nv):
    """One yes/no job per candidate name pair of each (set, entity, order) of `state`. Writes manifest_merge.json; returns the rows."""
    out, doc, rows = Path(out), blocks_doc(out), []
    m = cfg["merge"]
    for key, st in sorted(state.items()):
        s, ent, o = key
        d, nc = doc[f"{s}/{ent}"], name_clusters(st)
        nv.encode_missing(list(nc))
        for k, (cos, a, b) in enumerate(candidate_pairs(list(nc), nv, m["cosine"], m["max_pairs"])):
            name = f"{ent}_mergeq_{PP.RUN_KEY[s]}_s{o}_p{k}"
            B.write(out / "prompts" / f"{name}.txt", render_merge_q(d["entity"], a, b, nc[a], nc[b], d["blocks"]))
            B.write_json(out / "prompts" / f"{name}.schema.json", YESNO_SCHEMA)
            rows.append({"job": name, "entity": d["entity"], "ent": ent, "set": s, "run": PP.RUN_KEY[s], "family": "merge_q", "format": "judge",
                         "format44": "yesno", "run_tag": f"m{o}", "order": o, "names": [a, b], "cosine": round(cos, 4),
                         "prompt": f"prompts/{name}.txt", "schema": f"prompts/{name}.schema.json", "max_tokens": YESNO_MAX_TOKENS})
    B.write_json(out / "manifest_merge.json", {"stage": 4, "jobs": rows})
    return rows


def merge_groups(names, pairs, counts):
    """{old name: kept name} for the yes `pairs` (union-find; the kept name of a group is the one with most clusters, then the first
    alphabetically). Names that stay are not in the result."""
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in pairs:
        parent[find(a)] = find(b)
    groups, out = {}, {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    for g in groups.values():
        keep = min(g, key=lambda x: (-counts.get(x, 0), x))
        out.update({n: keep for n in g if n != keep})
    return out


def apply_merge(out, state):
    """Copy of `state` with the yes pairs of the merge answers merged by code. Returns (state, {(set, ent, order): {old: kept}})."""
    out, state, moved = Path(out), copy.deepcopy(state), {}
    jobs = _stage_jobs(out, "manifest_merge.json")
    ans = yes_no_answers(out, jobs)
    for key, st in state.items():
        yes = [tuple(j["names"]) for j in jobs if (j["set"], j["ent"], j["order"]) == key and ans[j["job"]] == "yes"]
        nc = name_clusters(st)
        mp = merge_groups(list(nc), yes, {n: len(c) for n, c in nc.items()})
        if mp:
            st["names"] = {c: mp.get(n, n) for c, n in st["names"].items()}
            moved[key] = mp
    return state, moved


# ---------------------------------------------------------------- assemble the A answers
def assemble_a_v44(out, cfg, state):
    """Write the 18 assembled A responses (responses/<ent>_a_<run>_s<n>.jsonl) from `state` (names per set, entity, order after the
    boosters; orders not in cfg["orders"] copy order 0) and names_stats.csv; returns the stats rows."""
    out, stats = Path(out), []
    for a in [j for j in PP.read_manifest(out) if j["family"] == "a"]:
        order = int(a["run_tag"][1:])
        copy_of = order not in cfg["orders"]
        st = state[(a["set"], a["ent"], 0 if copy_of else order)]
        obj = S3.v2_object(st["names"], st["frozen_ids"])
        used = {n for n in st["names"].values() if n != NOT_ATTRIBUTE}
        errs = st["errors"]
        row = {"key": a["job"], "job": a["job"], "format": "v2", "run_tag": a["run_tag"], "guided": True, "finish_reason": "stop",
               "model": "assembled by code from the names answers", "raw": json.dumps(obj), "parsed": obj, "errors": errs, "assembled": True,
               "from_jobs": [j["job"] for j in names_jobs(out) if (j["set"], j["ent"], j["order"]) == (a["set"], a["ent"], 0 if copy_of else order)]}
        if copy_of:
            row["copy_of"] = "s0"
        (out / "responses" / f"{a['job']}.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        stats.append({"set": a["set"], "ent": a["ent"], "order": a["run_tag"], "copy_of_s0": copy_of, "clusters": len(st["frozen_ids"]),
                      "batches": st["batches"], "batches_ok": st["ok"], "clusters_named": len(st["names"]), "names": len(used),
                      "not_attribute": sum(n == NOT_ATTRIBUTE for n in st["names"].values()), "merged_across_batches": len(st["across"]),
                      "end_names": sum(PP.is_end_name(n) for n in used), "errors": len(errs)})
    pd.DataFrame(stats).to_csv(out / "names_stats.csv", index=False, encoding="utf-8", lineterminator="\n")
    return stats


def booster_stats(out, base, named, moved):
    """Rescue and merge counts (whole run; per set under "by_set"): rescue asked / yes / no / unparsed (clusters, asked once per set) and
    named (cluster x order that got a real name); merge pairs asked / yes / unparsed and merged (names removed, over entity x order)."""
    out = Path(out)
    q = _stage_jobs(out, "manifest_rescue_q.json")
    qa = yes_no_answers(out, q)
    m = _stage_jobs(out, "manifest_merge.json")
    ma = yes_no_answers(out, m)
    res = {"rescue": {"not_attribute_cluster_orders": sum(n == NOT_ATTRIBUTE for st in base.values() for n in st["names"].values()),
                      "asked": len(q), "yes": sum(v == "yes" for v in qa.values()), "no": sum(v == "no" for v in qa.values()),
                      "unparsed": sum(v is None for v in qa.values()), "names_asked": len(_stage_jobs(out, "manifest_rescue_n.json")),
                      "named": sum(len(v) for v in named.values())},
           "merge": {"pairs_asked": len(m), "yes": sum(v == "yes" for v in ma.values()), "no": sum(v == "no" for v in ma.values()),
                     "unparsed": sum(v is None for v in ma.values()), "merged": sum(len(v) for v in moved.values())}, "by_set": {}}
    for s in PP.SETS:
        res["by_set"][s] = {
            "rescue_asked": sum(j["set"] == s for j in q), "rescue_yes": sum(qa[j["job"]] == "yes" for j in q if j["set"] == s),
            "rescue_named": sum(len(v) for k, v in named.items() if k[0] == s),
            "merge_pairs_asked": sum(j["set"] == s for j in m), "merge_yes": sum(ma[j["job"]] == "yes" for j in m if j["set"] == s),
            "merged": sum(len(v) for k, v in moved.items() if k[0] == s)}
    B.write_json(out / "booster_stats.json", res)
    return res


# ---------------------------------------------------------------- run
def run(out, backend, cfg=None, encoder=None, name_vecs=None, save_vecs=False, variant=None):
    """The whole T4 chain on `backend` (VllmBackend44 or FakeStep44): names + keyed split -> (rescue questions -> rescue names) ->
    (merge questions) -> assemble A by code -> reconcile -> dupcheck. `encoder` = name encoder for the merge switch (NameVectors);
    `name_vecs` = the npz path of name vectors (read when it exists; written only when `save_vecs`, i.e. the full T4 run).
    Returns {stage: backend info, "boosters": counts, "assemble": {...}}."""
    cfg = cfg or load_config()
    variant = variant or B.read_json(Path(out) / "config_used.json")["names_variant_used"]
    sw = cfg["switches"]
    info = {"names+split": backend.run(out, names_jobs(out) + SP.read_split_jobs(out))}
    info["split_assemble"] = SP.summary(SP.assemble_split(out))
    base = read_base(out)
    state, named = base, {}
    if sw["rescue"]:
        info["rescue_q"] = backend.run(out, build_rescue_q(out, cfg))
        info["rescue_n"] = backend.run(out, build_rescue_n(out, cfg, variant))
        state, named = apply_rescue(out, base)
    moved = {}
    if sw["merge"]:
        nv = NameVectors(name_vecs, encoder)
        info["merge_q"] = backend.run(out, build_merge_q(out, cfg, state, nv))
        state, moved = apply_merge(out, state)
        if save_vecs and name_vecs:
            nv.save(name_vecs)
    else:
        for f in ("manifest_merge.json",):
            B.write_json(Path(out) / f, {"stage": 4, "jobs": []})
    if not sw["rescue"]:
        B.write_json(Path(out) / "manifest_rescue_q.json", {"stage": 2, "jobs": []})
        B.write_json(Path(out) / "manifest_rescue_n.json", {"stage": 3, "jobs": []})
    stats = assemble_a_v44(out, cfg, state)
    info["assemble"] = {"answers": len(stats), "errors": sum(r["errors"] for r in stats)}
    info["boosters"] = booster_stats(out, base, named, moved)
    info.update(PP.run_post(out, backend, stages=("reconcile", "dupcheck")))
    return info


# ---------------------------------------------------------------- calls and tokens per stage
STAGE_OF = {"names": "names", "splitk": "split", "rescue_q": "rescue_q", "rescue_n": "rescue_n", "merge_q": "merge_q",
            "reconcile": "reconcile", "dupcheck_rc": "dupcheck", "probe": "probe"}


def all_jobs(out):
    """Every job of the run folder with its family (the names / split / rescue / merge manifests, reconcile and dupcheck)."""
    out, jobs = Path(out), []
    for name in ("manifest_names.json", "manifest_split44.json", "manifest_rescue_q.json", "manifest_rescue_n.json", "manifest_merge.json",
                 "manifest_probe.json"):
        jobs += _stage_jobs(out, name)
    return jobs + [j for j in PP.manifest_all(out) if j["family"] in ("reconcile", "dupcheck_rc")]


def call_report(out):
    """{stage: {calls, prompt_tokens, output_tokens, retried, job_seconds, guided_parse_rate = 1 - retried / calls}} + "total" over the real calls of the run folder
    (assembled answers are not calls). Written to out/scores/calls_v44.json by score_v44."""
    jobs = {j["job"]: j for j in all_jobs(out)}
    rows = [r for r in LOG.call_rows(out) if r["job"] in jobs]
    res = {}
    for r in rows:
        st = STAGE_OF.get(jobs[r["job"]]["family"], jobs[r["job"]]["family"])
        d = res.setdefault(st, {"calls": 0, "prompt_tokens": 0, "output_tokens": 0, "retried": 0, "job_seconds": 0.0})
        d["calls"] += 1
        d["prompt_tokens"] += r["prompt_tokens"] or 0
        d["output_tokens"] += r["output_tokens"] or 0
        d["retried"] += bool(r["retried"])
        d["job_seconds"] = round(d["job_seconds"] + (r["job_seconds"] or 0), 2)
    res["total"] = {k: round(sum(d[k] for d in res.values()), 2) for k in ("calls", "prompt_tokens", "output_tokens", "retried", "job_seconds")}
    for d in res.values():
        d["guided_parse_rate"] = round(1 - d["retried"] / d["calls"], 3) if d["calls"] else None
    return res


# ---------------------------------------------------------------- score and a_llama44
def score_v44(out):
    """step3_post_v43.score (found L2, columns, duplicates, guard) + scores/calls_v44.json + scores/summary.md; returns the score result."""
    res = PP.score(out)
    rep = call_report(out)
    B.write_json(Path(out) / "scores" / "calls_v44.json", rep)
    text = PP.summary_md(res, "wf_v4.4 Step 3 (Llama-3.1-8B): names variant + boosters")
    text += "\n## Calls per stage (v4.4)\n\n" + "\n".join(
        f"- {k}: " + ", ".join(f"{a} {b}" for a, b in d.items()) for k, d in rep.items()) + "\n"
    bs = Path(out) / "booster_stats.json"
    if bs.exists():
        text += f"\n## Boosters\n\n```json\n{json.dumps(B.read_json(bs), indent=1)}\n```\n"
    (Path(out) / "scores" / "summary.md").write_text(text, encoding="utf-8", newline="\n")
    return res


def a_llama44_file(set_name, out=OUT_T4):
    """Absolute path of the Step 4 input `a_llama44` of a set (same format as results/wf_v4/inputs/<set>/a.columns.json)."""
    return Path(out) / "a_llama44" / set_name / "a.columns.json"


def a_llama44_files(out=OUT_T4, root=ROOT):
    """{set: path relative to `root`, forward slashes}: the `a2_files` argument of nov16_v41.step4_chains, or the `columns_file` of one
    chain of input a_llama44 (batch_v4.chain_columns reads it as it reads input a)."""
    return {s: a_llama44_file(s, out).relative_to(root).as_posix() for s in PP.SETS}


def write_a_llama44(out=OUT_T4):
    """Write a_llama44/<set>/a.columns.json from scores/final_columns.json (score_v44 output); returns {set: n columns}."""
    final = B.read_json(Path(out) / "scores" / "final_columns.json")
    sizes = {}
    for s in PP.SETS:
        cols = S3.a_columns(final[s], I.load_mentions(s, ROOT))
        B.write_json(a_llama44_file(s, out), cols)
        sizes[s] = len(cols)
    return sizes


# ---------------------------------------------------------------- full run, ablations
def full_run(out, backend, cfg=None, encoder=None, name_vecs=None, save_vecs=False, variant=None, vecs=None):
    """build -> run -> score_v44 -> write_a_llama44 into `out`; returns (backend info, a_llama44 sizes)."""
    cfg = cfg or load_config()
    build(out, cfg, variant, vecs)
    info = run(out, backend, cfg, encoder, name_vecs, save_vecs, variant)
    score_v44(out)
    return info, write_a_llama44(out)


def ablation(switch, backend, cfg=None, encoder=None, root=OUT_ABLATE, name_vecs=OUT_T4 / "name_vecs.npz", variant=None, vecs=None):
    """One ablation run: `switch` off, the others as in `cfg`, order 0 only (orders 1, 2 are copies; the post steps need both sets, so both
    sets run, the dev50 rows are the ablation). Same layout as T4 under root/<switch>/; name vectors are read, never written."""
    cfg = with_switches(cfg or load_config(), {switch: False})
    cfg["orders"] = [0]
    return full_run(Path(root) / switch, backend, cfg, encoder, name_vecs, False, variant, vecs)


# ---------------------------------------------------------------- fake backend (laptop plumbing; no model)
class FakeStep44(PP.FakeStep3):
    """FakeStep3 with valid answers for the v4.4 families: names (any key style), keyed split, rescue yes/no and names, merge yes/no."""

    def respond(self, job, prompt, schema):
        fam, props = job["family"], schema.get("properties", {})
        if fam in ("names", "probe", "rescue_n"):
            self.n_made += 1
            n = {k: int(re.search(r"(\d+)$", k).group(1)) for k in props}
            if fam == "rescue_n":
                return json.dumps({k: f"fake_rescued_{v % 3}" for k, v in n.items()})
            return json.dumps({k: "not_attribute" if v % 7 == 6 else f"fake_attr_{v % 4}" for k, v in n.items()})
        if fam == "splitk":
            self.n_made += 1
            return SP.fake_answer(schema, job["cluster_id"])
        if fam in ("rescue_q", "merge_q"):
            self.n_made += 1
            return json.dumps({"answer": "yes" if zlib.crc32(job["job"].encode()) % 2 == 0 else "no"})
        return super().respond(job, prompt, schema)
