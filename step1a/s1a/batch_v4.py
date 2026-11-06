"""wf_v4 Colab batch (contract WF_V4_BATCH.md): chains of the four Step-4 prompts, the dialogues-only calls and the placement chain.

Stages: 1 = the first call of every chain (4.1 of 24 main chains + the placement base chain, and the 6 (e) calls); 2, 3, 4 = 4.2, 4.3, 4.4 of
every chain that is still valid; 5 .. 4+n = one placement call per held-out column and mode (with / without the signal card).
`build_stage1(root, out)` writes stage 1 (prompts, manifest.json, chains.json, placement.json); `build_stage(out, k, root)` writes
manifest_stage<k>.json from the responses of the earlier stages (nothing is stored between stages except the response files); `assemble_all`
writes canonical JSON, SQL and operations per finished chain. All functions are pure apart from the files named.

Responses: <out>/responses/<job>.jsonl, last row = the answer (llm_cache rows: raw, parsed, errors). A chain stops at the first call whose
row is missing, has parse errors or fails the validator (step4_prompts.validate_*); it is listed in chain_status.json.
Repairs (counted in the status, never silent): 4.1 columns missing from the answer go to `unused` ("not placed by the model"), a column given
twice keeps its first group; 4.3 relationships / new tables that name unknown tables, relate a table to itself or repeat are dropped.
"""
import json
import re
from pathlib import Path

from . import llm_cache as LC
from . import step4_inputs as I
from . import step4_prompts as SP
from . import step4_sql as SQL
from .pilot_input import est_tokens

ROOT = Path(__file__).resolve().parents[1]
CTX = 32768
MAX_TOKENS = {"s4_41": 6000, "s4_42": 3000, "s4_43": 3000, "s4_44": 6000, "s4_e": 8000, "s4_place": 1000}
FAMILIES = tuple(MAX_TOKENS)
STEP_FAMILY = {1: "s4_41", 2: "s4_42", 3: "s4_43", 4: "s4_44"}
INPUTS, SETS, SEEDS, E_VERSIONS = ("a", "b", "c1", "c2"), ("dev50", "dev50b"), (0, 1, 2), I.VERSIONS
BASE_SET, MODES = "dev50", ("sig", "nosig")
LIMIT_FIRST, LIMIT_ANY = 20000, 30000    # exact prompt tokens (the notebook stops above these)
FIRST_STEPS = ("s4_41", "s4_e")
INPUT_DIR = "results/wf_v4/inputs"
PLACEMENT_CONFIG = "config/wf_v4_placement.json"
_DATASET_WORDS = re.compile(r"\b(multiwoz|tear|hansard)\b", re.I)


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path, obj):
    write(path, json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def last_row(path):
    """Last JSON row of a response file, or None when the file is missing or empty."""
    p = Path(path)
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    return rows[-1] if rows else None


# ---------------------------------------------------------------- jobs
class Jobs:
    """Writes prompt + schema files of the jobs of one stage under <out>/prompts and collects the manifest rows."""

    def __init__(self, out, stage):
        self.out, self.stage, self.jobs = Path(out), stage, []

    def emit(self, name, family, text, schema, run_tag, set_name, ent="", **extra):
        if _DATASET_WORDS.search(text):
            raise ValueError(f"{name}: dataset name in the prompt")
        write(self.out / "prompts" / f"{name}.txt", text)
        write(self.out / "prompts" / f"{name}.schema.json", json.dumps(schema, indent=1))
        self.jobs.append({"job": name, "ent": ent, "entity": "", "family": family, "set": set_name, "format": family, "run_tag": run_tag,
                          "stage": self.stage, "round": 0, "carry_from": [], "prompt": f"prompts/{name}.txt",
                          "schema": f"prompts/{name}.schema.json", "max_tokens": MAX_TOKENS[family],
                          "est_prompt_tokens": est_tokens(text), **extra})

    def save(self):
        name = "manifest.json" if self.stage == 1 else f"manifest_stage{self.stage}.json"
        write_json(self.out / name, {"stage": self.stage, "jobs": self.jobs})
        return self.jobs


# ---------------------------------------------------------------- chains
def chain_id(inp, set_name, seed):
    return f"{inp}_{set_name}_s{seed}"


def main_chains():
    return [{"id": chain_id(i, s, d), "kind": "main", "input": i, "set": s, "seed": d, "exclude": []}
            for i in INPUTS for s in SETS for d in SEEDS]


def chain_columns(chain, root=ROOT):
    """Ordered column dicts of a chain (input file minus the excluded ids, then the seed order)."""
    cols = read_json(Path(root) / INPUT_DIR / chain["set"] / f"{chain['input']}.columns.json")
    return I.order_columns([c for c in cols if c["id"] not in chain["exclude"]], chain["seed"])


def build_placement(root=ROOT, config=None):
    """placement.json content: the held-out attributes of the config mapped to the BASE_SET handover columns that found them (column ids
    of the `found_by` field of results/wf_v4/gt/reachable_<set>.csv: the GT label holds >= 0.6 of the column's labelled mentions; the
    plurality rule of the brief fails for "Train requested people", whose most common gt_L2 is empty). The GT is used only here, to build
    this test. Returns {"set", "attributes": [{gt, kind, columns, also_hold_out}], "hold_out": ids left out of the base chain,
    "steps": [{attr, column}] one per held-out column in config order; also_hold_out columns are left out and never placed}."""
    from . import step4_gt as G
    cfg = read_json(config or Path(root) / PLACEMENT_CONFIG)
    found = {r["gt_column"]: r["found_by"].split() for r in G.load_reachable(Path(root) / "results" / "wf_v4" / "gt" / f"reachable_{BASE_SET}.csv")}
    attrs, hold, steps = [], [], []
    for a in cfg:
        if not found.get(a["gt"]):
            raise ValueError(f"no {BASE_SET} handover column found {a['gt']!r}")
        also = {n: found.get(n, []) for n in a.get("also_hold_out", [])}
        attrs.append({"gt": a["gt"], "kind": a["kind"], "columns": found[a["gt"]], "also_hold_out": also})
        hold += found[a["gt"]] + [c for v in also.values() for c in v]
        steps += [{"attr": len(attrs) - 1, "column": c} for c in found[a["gt"]]]
    return {"set": BASE_SET, "attributes": attrs, "hold_out": hold, "steps": steps}


def all_chains(out):
    return read_json(Path(out) / "chains.json")


def place_column(out, step, mode, root=ROOT):
    """Column dict of a placement step: from input b (with the signal card) in mode sig, from input a in mode nosig."""
    plc = read_json(Path(out) / "placement.json")
    cid = plc["steps"][step]["column"]
    cols = read_json(Path(root) / INPUT_DIR / plc["set"] / f"{'b' if mode == 'sig' else 'a'}.columns.json")
    return next(c for c in cols if c["id"] == cid)


def build_stage1(root=ROOT, out=None):
    """Write stage 1 under `out` (default results/wf_v4/colab): prompts, manifest.json, chains.json, placement.json. Returns the jobs."""
    root = Path(root)
    out = Path(out or root / "results" / "wf_v4" / "colab")
    plc = build_placement(root)
    chains = main_chains() + [{"id": chain_id("base", BASE_SET, 0), "kind": "base", "input": "a", "set": BASE_SET, "seed": 0,
                               "exclude": plc["hold_out"]}]
    write_json(out / "chains.json", chains)
    write_json(out / "placement.json", plc)
    jobs = Jobs(out, 1)
    for ch in chains:
        cols = chain_columns(ch, root)
        text, schema = SP.build_prompt_41(SP.render_columns(cols), cols)
        jobs.emit(f"{ch['id']}_41", "s4_41", text, schema, ch["id"], ch["set"], ent=ch["input"], chain=ch["id"], step=1, n_columns=len(cols))
    for s in SETS:
        for v in E_VERSIONS:
            text = (root / INPUT_DIR / s / f"e_{v}.prompt.txt").read_text(encoding="utf-8")
            jobs.emit(f"e_{s}_{v}", "s4_e", text, SP.build_prompt_e("")[1], f"e_{v}", s, ent="e", chain=f"e_{s}_{v}", step=1)
    return jobs.save()


# ---------------------------------------------------------------- repairs
def repair_41(a41, cols):
    """(a41 fixed, number of repairs): see module doc."""
    ids = [c["id"] for c in cols]
    seen, used, groups, n = set(), set(), [], 0
    for g in a41.get("groups", []):
        keep = []
        for c in g.get("columns", []):
            if c in ids and c not in seen:
                keep.append(c)
                seen.add(c)
            else:
                n += 1
        if keep:
            groups.append({**g, "columns": keep})
    unused = []
    for u in a41.get("unused", []):
        c = u.get("column")
        if c in ids and c not in seen and c not in used:
            unused.append(u)
            used.add(c)
        else:
            n += 1
    for c in ids:
        if c not in seen and c not in used:
            unused.append({"column": c, "reason": "not placed by the model"})
            n += 1
    return {**a41, "groups": groups, "unused": unused}, n


def repair_43(a43, a41, a42):
    """(a43 fixed, number of repairs): see module doc."""
    old = {t["name"] for t in SP.named_tables(a41, a42)}
    new, n = [], 0
    for t in a43.get("new_tables", []):
        b = t.get("between", [])
        if str(t.get("name") or "").strip() and t["name"] not in old and t["name"] not in {x["name"] for x in new} \
                and len(b) == 2 and len(set(b)) == 2 and all(x in old for x in b):
            new.append(t)
        else:
            n += 1
    names, rels, seen = old | {t["name"] for t in new}, [], set()
    for r in a43.get("relationships", []):
        key = (r.get("from"), r.get("to"), r.get("kind"))
        if r.get("from") in names and r.get("to") in names and r["from"] != r["to"] and key not in seen:
            rels.append(r)
            seen.add(key)
        else:
            n += 1
    return {**a43, "relationships": rels, "new_tables": new}, n


def replay(out, chain, upto, root=ROOT):
    """Answers of a chain's calls 1..upto: (answers {"41": ..}, repairs, error or None, cols). The first failing call stops the replay."""
    cols = chain_columns(chain, root)
    ans, repairs = {}, 0
    for step in range(1, upto + 1):
        row = last_row(Path(out) / "responses" / f"{chain['id']}_4{step}.jsonl")
        if row is None:
            return ans, repairs, f"4.{step}: no response", cols
        if row["errors"]:
            return ans, repairs, f"4.{step}: parse errors {row['errors'][:2]}", cols
        a = row["parsed"]
        if step == 1:
            a, n = repair_41(a, cols)
            errs = SP.validate_41(a, cols)
        elif step == 2:
            n, errs = 0, SP.validate_42(a, ans["41"])
        elif step == 3:
            a, n = repair_43(a, ans["41"], ans["42"])
            errs = SP.validate_43(a, ans["41"], ans["42"])
        else:
            n, errs = 0, SP.validate_44(a, ans["41"], ans["42"], ans["43"], cols)
        repairs += n
        if errs:
            return ans, repairs, f"4.{step}: {len(errs)} validation errors, e.g. {errs[:2]}", cols
        ans[f"4{step}"] = a
    return ans, repairs, None, cols


def assemble_chain(ans, cols):
    """Canonical schema of a finished chain; columns and unused entries that come from a GT column (c1, c2) carry its `gt` field."""
    c = SQL.assemble(ans["41"], ans["42"], ans["43"], ans["44"], cols)
    gt = {x["id"]: x["gt"] for x in cols if x.get("gt")}
    for t in c["tables"]:
        for col in t["columns"]:
            if col["source"] in gt:
                col["gt"] = gt[col["source"]]
    for u in c["unused"]:
        if u["source"] in gt:
            u["gt"] = gt[u["source"]]
    return c


# ---------------------------------------------------------------- placement chain
def place_state(out, mode, upto, root=ROOT):
    """(schemas after each of the first `upto` steps, answers, error or None) of one placement mode, replayed from the base chain."""
    base = next(c for c in read_json(Path(out) / "chains.json") if c["kind"] == "base")
    ans, _, err, cols = replay(out, base, 4, root)
    if err:
        return [], [], f"base chain: {err}"
    cur, schemas, answers = assemble_chain(ans, cols), [], []
    for j in range(upto):
        row = last_row(Path(out) / "responses" / f"place_{mode}_{j}.jsonl")
        if row is None or row["errors"]:
            return schemas, answers, f"place step {j}: " + ("no response" if row is None else f"parse errors {row['errors'][:2]}")
        errs = SP.validate_place(row["parsed"], cur)
        if errs:
            return schemas, answers, f"place step {j}: {errs[:2]}"
        cur = SQL.apply_placement(cur, row["parsed"], place_column(out, j, mode, root))
        schemas.append(cur)
        answers.append(row["parsed"])
    return schemas, answers, None


def n_place_steps(out):
    return len(read_json(Path(out) / "placement.json")["steps"])


# ---------------------------------------------------------------- later stages
def build_stage(out, k, root=ROOT):
    """Write stage k (2 .. 4+n_steps) from the responses of the earlier stages; returns the jobs (chains that stopped are skipped) and
    rewrites chain_status.json."""
    out, root = Path(out), Path(root)
    jobs, status = Jobs(out, k), []
    if k <= 4:
        for ch in all_chains(out):
            ans, rep, err, cols = replay(out, ch, k - 1, root)
            status.append({"chain": ch["id"], "ok": err is None, "reached": k - 1 if err is None else len(ans), "repairs": rep, "error": err})
            if err:
                continue
            build = {2: lambda: SP.build_prompt_42(ans["41"], cols), 3: lambda: SP.build_prompt_43(ans["41"], ans["42"], cols),
                     4: lambda: SP.build_prompt_44(ans["41"], ans["42"], ans["43"], cols)}[k]
            text, schema = build()
            jobs.emit(f"{ch['id']}_4{k}", STEP_FAMILY[k], text, schema, ch["id"], ch["set"], ent=ch["input"], chain=ch["id"], step=k)
    else:
        j = k - 5
        if j >= n_place_steps(out):
            raise ValueError(f"stage {k}: only {n_place_steps(out)} placement steps")
        for mode in MODES:
            schemas, _, err = place_state(out, mode, j, root)
            status.append({"chain": f"place_{mode}", "ok": err is None, "reached": len(schemas), "repairs": 0, "error": err})
            if err:
                continue
            cur = schemas[-1] if schemas else assemble_base(out, root)
            text, schema = SP.build_prompt_place(cur, place_column(out, j, mode, root))
            jobs.emit(f"place_{mode}_{j}", "s4_place", text, schema, f"place_{mode}", BASE_SET, ent=mode, chain=f"place_{mode}", step=k - 4)
    write_json(out / f"chain_status_stage{k}.json", status)
    return jobs.save()


def assemble_base(out, root=ROOT):
    base = next(c for c in read_json(Path(out) / "chains.json") if c["kind"] == "base")
    ans, _, err, cols = replay(out, base, 4, root)
    if err:
        raise ValueError(f"base chain: {err}")
    return assemble_chain(ans, cols)


# ---------------------------------------------------------------- assembly
def assemble_all(out, root=ROOT):
    """Write <out>/final/<run>/{canonical.json, schema.sql, operations.json} for every finished chain and (e) call, and for the placement
    chains the schema after each step (canonical_<j>.json) plus answers.json; <out>/final/status.json lists every run (ok or the error).
    Returns the status rows."""
    out, root = Path(out), Path(root)
    final, status = out / "final", []

    def save(tag, c):
        write_json(final / tag / "canonical.json", c)
        write(final / tag / "schema.sql", SQL.to_sql(c))
        write_json(final / tag / "operations.json", SQL.to_operations(c))

    for ch in all_chains(out):
        ans, rep, err, cols = replay(out, ch, 4, root)
        if not err:
            save(ch["id"], assemble_chain(ans, cols))
        status.append({"run": ch["id"], "kind": ch["kind"], "ok": err is None, "repairs": rep, "error": err})
    for s in SETS:
        for v in E_VERSIONS:
            name = f"e_{s}_{v}"
            row = last_row(out / "responses" / f"{name}.jsonl")
            errs = ["no response"] if row is None else (row["errors"] or SP.validate_e(row["parsed"]))
            if not errs:
                save(name, SQL.from_e(row["parsed"]))
            status.append({"run": name, "kind": "e", "ok": not errs, "repairs": 0, "error": None if not errs else str(errs[:2])})
    if (out / "placement.json").exists():
        n = n_place_steps(out)
        for mode in MODES:
            schemas, answers, err = place_state(out, mode, n, root)
            for j, c in enumerate(schemas):
                write_json(final / f"place_{mode}" / f"canonical_{j}.json", c)
            if schemas:
                save(f"place_{mode}", schemas[-1])
            write_json(final / f"place_{mode}" / "answers.json", answers)
            status.append({"run": f"place_{mode}", "kind": "place", "ok": err is None, "repairs": 0, "error": err})
    write_json(final / "status.json", status)
    return status
