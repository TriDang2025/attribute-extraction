"""wf_v3.2 pilot (PILOT_V32_CONTRACT.md "Combine rules", "Reconcile", "Module API"): combine the stage-1 responses of
results/loop1_v32 into decision tables (B = one order, C = 3-order vote, D = + noise probe, coherence gate, reconcile)
and build the stage-2 (reconcile) jobs. Plain pandas / numpy; no export, GPU or LLM, so it runs on Colab.
Every table is a PV.DEC_COLS table, scored by the unchanged scorer. Parsing goes through llm_cache.parse_job.
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from . import llm_cache as LC
from . import pilot_verify as PV

TOP_K = 5  # candidates per reconcile unit
N_LINES = 6  # example lines in a reconcile prompt
RECONCILE_MAX_TOKENS = 400
VOTE_VARIANT = "nbhd_vote3"
# The generic flag is only reported: on dev it flagged 8 clusters, 5 of them real gold attributes (days, area,
# train departure/destination share values across entities), so it is not a noise rule.
GENERIC_IN_NOISE = False


# ---------------------------------------------------------------- reading the folder
def _manifest_path(out_dir):
    return Path(out_dir) / "manifest.json"


def load_jobs(out_dir):
    """The manifest's job list (the file is {"jobs": [...]} or a bare list)."""
    m = json.loads(_manifest_path(out_dir).read_text(encoding="utf-8"))
    return m["jobs"] if isinstance(m, dict) else m


def _schema(out_dir, job):
    p = Path(out_dir) / job["schema"]
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_obj(out_dir, job):
    """Parsed response of a manifest job (the LAST row of responses/<job>.jsonl; llm_cache.parse_job of its raw
    text when the row has no usable `parsed`), or None if the file is missing, empty or the parse gave nothing."""
    path = Path(out_dir) / "responses" / f"{job['job']}.jsonl"
    if not path.exists():
        return None
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return None
    row = rows[-1]
    parsed = row.get("parsed")
    if not parsed:
        try:
            parsed, _, _ = LC.parse_job(row.get("raw") or "", job["format"], _schema(out_dir, job))
        except ValueError:
            return None
    return parsed if isinstance(parsed, dict) and parsed else None


def _jobs_of(out_dir, ent, kind, run_tag=None):
    return [j for j in load_jobs(out_dir) if j["ent"] == ent and j["kind"] == kind
            and (run_tag is None or j["run_tag"] == run_tag)]


def _by_cluster(out_dir, ent, kind):
    return {j["cluster_id"]: o for j in _jobs_of(out_dir, ent, kind) if (o := load_obj(out_dir, j)) is not None}


def _split_results(out_dir, ent):
    return _by_cluster(out_dir, ent, "split")


def _empty_row(variant, tag, cid):
    return {"variant": variant, "run_tag": tag, "cluster_id": cid, "action": "",
            **{c: "" for c in PV.DEC_COLS[3:] if c != "action"}}


# ---------------------------------------------------------------- B: one order
def decisions_b(out_dir, ent, seed=0, split_results=None, variant="nbhd", group0=None):
    """v2 decision table of the group responses (jobs of this `variant`) of one order, concatenated (before the
    name merge). `group0`: variant to read group 0 from instead (wf_v3.3 E1 shares its group-0 jobs with E).
    Each group goes through PV.decisions_from_v2 (require_mixed=False; the v3 `reason` key is ignored there).
    split_results {cluster_id: split obj}; None = the manifest's split responses of the entity, {} = no splits.
    A group whose response is missing gives rows with action "" for its cluster ids (the schema's enum)."""
    tag = f"s{seed}"
    if split_results is None:
        split_results = _split_results(out_dir, ent)
    parts = []
    for job in sorted(_jobs_of(out_dir, ent, "entity", tag), key=lambda j: (j["nbhd"] or 0)):
        if job["variant"] != (group0 if group0 and (job["nbhd"] or 0) == 0 else variant):
            continue
        obj = load_obj(out_dir, job)
        ids = LC.schema_enum(_schema(out_dir, job), "cluster_id")
        if ids is None:
            ids = [c.get("cluster_id") for c in (obj or {}).get("clusters") or [] if isinstance(c, dict)]
        parts.append(PV.decisions_from_v2(obj, list(ids), variant, tag, split_results, require_mixed=False))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=PV.DEC_COLS)


# ---------------------------------------------------------------- shared table helpers
def _key(row):
    """Vote key of a decision row: normalized name, "not attribute", "attribute cue", "unsure", or None for an
    omitted cluster."""
    act = row["action"]
    if act == "not_attribute":
        return PV.NOT_ATTRIBUTE_KEY
    if act == "attribute_cue":
        return PV.ATTRIBUTE_CUE_KEY
    if act == "unsure":
        return "unsure"
    if act == "":
        return None
    return PV.norm_name(row["name"]) or "unsure"


def _links(dec):
    return {r["cluster_id"]: set(json.loads(r["merge_with"] or "[]")) for _, r in dec.iterrows()}


def _set_groups(dec, links):
    """Rewrite action keep/merge and merge_with of keep/merge rows from `links` (symmetrized, restricted to
    keep/merge rows); other rows are untouched."""
    out = dec.copy()
    live = {r["cluster_id"] for _, r in out.iterrows() if r["action"] in ("keep", "merge")}
    sym = {c: set() for c in live}
    for c in live:
        for t in links.get(c, ()):
            if t in live and t != c:
                sym[c].add(t)
                sym[t].add(c)
    for i, r in out.iterrows():
        if r["cluster_id"] in live:
            others = sorted(sym[r["cluster_id"]])
            out.at[i, "action"] = "merge" if others else "keep"
            out.at[i, "merge_with"] = json.dumps(others)
    return out


def _name_join(dec, cooccur=()):
    """The scorer's name merge without the export: join keep/merge groups with the same normalized name and
    placement unless two of their clusters share an instance (`cooccur`: cluster pairs that do, from
    stage2_inputs.json)."""
    from .pilot_score import _norm_placement
    together = {frozenset(p) for p in cooccur}
    rows = {r["cluster_id"]: r for _, r in dec.iterrows() if r["action"] in ("keep", "merge")}
    parent = {c: c for c in rows}
    for c, t in ((c, t) for c, ts in _links(dec).items() if c in rows for t in ts if t in rows):
        parent[PV._find(parent, c)] = PV._find(parent, t)
    members = {}
    for c in rows:
        members.setdefault(PV._find(parent, c), set()).add(c)
    cand = sorted(c for c in rows if PV.norm_name(rows[c]["name"]))
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            ra, rb = PV._find(parent, a), PV._find(parent, b)
            if (ra != rb and PV.norm_name(rows[a]["name"]) == PV.norm_name(rows[b]["name"])
                    and _norm_placement(rows[a]["placement"]) == _norm_placement(rows[b]["placement"])
                    and not any(frozenset((x, y)) in together for x in members[ra] for y in members[rb])):
                parent[rb] = ra
                members[ra] |= members.pop(rb)
    links = {c: set(members[PV._find(parent, c)]) - {c} for c in rows}
    return _set_groups(dec, links)


def _mark_not_attribute(out, i):
    out.at[i, "action"] = "not_attribute"
    for col in ("name", "description", "evidence"):
        out.at[i, col] = ""
    out.at[i, "merge_with"] = "[]"
    out.at[i, "split"] = "[]"


# ---------------------------------------------------------------- C: vote
def vote(tables):
    """(voted table, {agree_mean, agree_full_share, ties}) over the decision tables of the orders (seed 0 first).
    Per cluster: majority of the vote keys (norm name; not_attribute and unsure count); a tie falls back to the
    first table that holds one of the tied keys (seed 0). Winner row = the lowest-seed row with that key
    (name, description, placement, evidence, split); its merge_with is kept only for clusters that also voted
    that key. Agreement = orders agreeing with the winner / orders. `mixed` is not in the table, so it is not voted
    (it only matters where a split result exists, and the gate decides that)."""
    n = len(tables)
    per = [{r["cluster_id"]: r for _, r in t.iterrows()} for t in tables]
    cids = list(dict.fromkeys(c for t in tables for c in t["cluster_id"]))
    winner, rows, agree, ties = {}, {}, [], 0
    for cid in cids:
        keys = [_key(p[cid]) if cid in p else None for p in per]
        counts = Counter(k for k in keys if k is not None)
        if not counts:
            winner[cid] = None
            rows[cid] = _empty_row(VOTE_VARIANT, f"s0-{n - 1}", cid)
            continue
        top = max(counts.values())
        tied = [k for k, c in counts.items() if c == top]
        if len(tied) > 1:
            ties += 1
        win = next(k for k in keys if k in tied)  # first table (lowest seed) holding a tied key
        winner[cid] = win
        agree.append(counts[win] / n)
        src = next(p[cid] for p, k in zip(per, keys) if k == win)
        rows[cid] = {c: src[c] for c in PV.DEC_COLS}
    links = {}
    for cid, r in rows.items():
        if r["action"] in ("keep", "merge"):
            links[cid] = {t for t in json.loads(r["merge_with"] or "[]") if winner.get(t) == winner[cid]}
    out = pd.DataFrame([rows[c] for c in cids], columns=PV.DEC_COLS)
    out["variant"], out["run_tag"] = VOTE_VARIANT, f"s0-{n - 1}"
    out = _set_groups(out, links)
    stats = {"agree_mean": float(np.mean(agree)) if agree else 0.0,
             "agree_full_share": float(np.mean([a == 1.0 for a in agree])) if agree else 0.0, "ties": ties}
    return out, stats


# ---------------------------------------------------------------- D: noise
def generic_flags(mentions, run_entities=None):
    """Cluster ids that are generic: >= 50% of their mentions have a norm_value that also occurs in clusters of 2+
    other entities of the run. `mentions` has entity, cluster_id, norm_value; `run_entities` = entity tags of the run
    (None = all entities in `mentions`)."""
    m = mentions[mentions["cluster_id"] != ""]
    if run_entities is not None:
        m = m[m["entity"].isin(set(run_entities))]
    ents_of = m.groupby("norm_value")["entity"].agg(set).to_dict()
    flagged = set()
    for cid, g in m.groupby("cluster_id"):
        e = g["entity"].iloc[0]
        share = np.mean([len(ents_of[v] - {e}) >= 2 for v in g["norm_value"]])
        if share >= 0.5:
            flagged.add(cid)
    return flagged


def apply_noise(dec, probe, generic):
    """(table, stats) after the noise rules. A cluster becomes not_attribute if probe = noise, or the vote said
    not_attribute and probe != attribute, or it is generic and probe != attribute (a cluster without a probe
    answer counts as "unsure"). A voted not_attribute with probe = attribute and a probe name becomes its own
    attribute (rescued). Stats count each cluster once, in the order probe, vote, generic."""
    out = dec.copy()
    stats = {"marked_by_probe": 0, "by_vote": 0, "by_generic": 0, "rescued": 0}
    for i, r in dec.iterrows():
        cid, verdict = r["cluster_id"], (probe.get(r["cluster_id"]) or {}).get("verdict", "unsure")
        if r["action"] == "":
            continue
        voted_na = r["action"] == "not_attribute"
        if verdict == "noise":
            stats["marked_by_probe"] += 1
        elif voted_na and verdict != "attribute":
            stats["by_vote"] += 1
        elif cid in generic and verdict != "attribute":
            stats["by_generic"] += 1
        else:
            name = str((probe.get(cid) or {}).get("name") or "").strip()
            if voted_na and verdict == "attribute" and name:
                stats["rescued"] += 1
                out.at[i, "action"], out.at[i, "name"] = "keep", name
            continue
        if not voted_na:
            _mark_not_attribute(out, i)
    return _set_groups(out, _links(out)), stats


# ---------------------------------------------------------------- D: gate
def _usable_parts(cid, s):
    """Split parts of a split result that own at least one of this cluster's examples (as decisions_from_v2)."""
    return [p for p in (s or {}).get("parts") or [] if isinstance(p, dict)
            and any(str(e).startswith(f"{cid}:") for e in p.get("examples") or [])]


def apply_gate(dec, gate, split_results):
    """Split only where the gate says coherent false AND the split result is_mixed with >= 2 usable parts; the
    cluster leaves its merge group (action split, merge_with []). A cluster with no gate answer counts as coherent."""
    out = dec.copy()
    for i, r in dec.iterrows():
        cid = r["cluster_id"]
        if r["action"] not in ("keep", "merge") or (gate.get(cid) or {}).get("coherent", True) is not False:
            continue
        s = (split_results or {}).get(cid) or {}
        parts = _usable_parts(cid, s)
        if s.get("is_mixed") and len(parts) >= 2:
            out.at[i, "action"] = "split"
            out.at[i, "merge_with"] = "[]"
            out.at[i, "split"] = json.dumps([{"name": str(p.get("name") or ""), "role": str(p.get("role") or ""),
                                              "examples": list(p.get("examples") or [])} for p in parts])
    return _set_groups(out, _links(out))


# ---------------------------------------------------------------- units and reconcile
def units_from_dec(dec):
    """Reconcile units of a decision table, deterministic: one attribute unit (uid a<k>) per merge group of
    keep/merge rows and one part unit (uid <cid>-p<j>) per part of a split row. Dicts: uid, kind attr|part, name,
    description, clusters (attr: member cids; part: [cid]), examples (part: its ex ids)."""
    def num(c):
        return (c.split("#")[0], int(c.rsplit("#", 1)[1]) if c.rsplit("#", 1)[-1].isdigit() else 0, c)
    rows = {r["cluster_id"]: r for _, r in dec.iterrows()}
    parent = {c: c for c, r in rows.items() if r["action"] in ("keep", "merge")}
    for c in list(parent):
        for t in json.loads(rows[c]["merge_with"] or "[]"):
            if t in parent:
                parent[PV._find(parent, c)] = PV._find(parent, t)
    groups = {}
    for c in parent:
        groups.setdefault(PV._find(parent, c), []).append(c)
    units = []
    for k, members in enumerate(sorted((sorted(m, key=num) for m in groups.values()), key=lambda m: num(m[0]))):
        named = [c for c in members if rows[c]["name"]]
        head = rows[named[0]] if named else rows[members[0]]
        units.append({"uid": f"a{k}", "kind": "attr", "name": head["name"], "description": head["description"],
                      "clusters": members, "examples": []})
    for c in sorted((c for c, r in rows.items() if r["action"] == "split"), key=num):
        for j, p in enumerate(json.loads(rows[c]["split"] or "[]")):
            units.append({"uid": f"{c}-p{j}", "kind": "part", "name": str(p.get("name") or ""),
                          "description": str(p.get("role") or ""), "clusters": [c],
                          "examples": list(p.get("examples") or [])})
    return units


def apply_reconcile(dec, units, answers):
    """Table after the reconcile answers. answers {unit_id: {same_as: candidate name | "none"}}. An attribute unit
    that names another attribute unit is merged with it (union-find over units; all member clusters link up).
    A part unit that names an attribute gets that name; a part with "none" stays the new attribute the split
    made it. Names are matched by norm_name; an unknown name counts as "none".
    The part dict gets `merge_into` (the target's clusters); PV.final_attributes then gives the part's mentions
    to that attribute."""
    by_name = {PV.norm_name(u["name"]): u for u in units if u["kind"] == "attr" and PV.norm_name(u["name"])}
    uf = {u["uid"]: u["uid"] for u in units if u["kind"] == "attr"}
    part_target = {}
    for u in units:
        t = by_name.get(PV.norm_name((answers.get(u["uid"]) or {}).get("same_as", "none")))
        if t is None or t["uid"] == u["uid"]:
            continue
        if u["kind"] == "attr":
            uf[PV._find(uf, u["uid"])] = PV._find(uf, t["uid"])
        else:
            part_target[u["uid"]] = t
    cl = {u["uid"]: u["clusters"] for u in units if u["kind"] == "attr"}
    comp = {}
    for uid in uf:
        comp.setdefault(PV._find(uf, uid), []).extend(cl[uid])
    links = _links(dec)
    for members in comp.values():
        for c in members:
            links.setdefault(c, set()).update(members)
    out = _set_groups(dec, links)
    for u in units:
        if u["uid"] not in part_target:
            continue
        t = part_target[u["uid"]]
        i = out.index[out["cluster_id"] == u["clusters"][0]][0]
        parts = json.loads(out.at[i, "split"])
        j = int(u["uid"].rsplit("-p", 1)[1])
        parts[j]["name"], parts[j]["merge_into"] = t["name"], list(t["clusters"])
        out.at[i, "split"] = json.dumps(parts)
    return out


# ---------------------------------------------------------------- D chain
def _generic(out_dir, ent):
    """Generic cluster ids of the entity from <out_dir>/generic.json ({ent: [cluster ids]}, written next to the
    export by the build step through generic_flags); empty if the file is absent."""
    p = Path(out_dir) / "generic.json"
    return set(json.loads(p.read_text(encoding="utf-8")).get(ent, [])) if p.exists() else set()


def _stage1_d(out_dir, ent, generic=None):
    """(table before reconcile, stats): vote of the 3 orders -> noise -> name join -> gate."""
    seeds = sorted({int(j["run_tag"][1:]) for j in _jobs_of(out_dir, ent, "entity") if j["variant"] == "nbhd"})
    dec, stats = vote([decisions_b(out_dir, ent, s, split_results={}) for s in seeds])
    probe = _by_cluster(out_dir, ent, "noise")
    flagged = _generic(out_dir, ent) if generic is None else generic
    dec, nstats = apply_noise(dec, probe, flagged if GENERIC_IN_NOISE else set())
    nstats["generic_flagged"] = len(flagged)
    p = Path(out_dir) / "stage2_inputs.json"
    cooccur = json.loads(p.read_text(encoding="utf-8")).get(ent, {}).get("cooccur", []) if p.exists() else []
    dec = _name_join(dec, cooccur)
    gate, split = _by_cluster(out_dir, ent, "gate"), _split_results(out_dir, ent)
    gated = apply_gate(dec, gate, split)
    stats = {**stats, **nstats, "gate_failed": sum(1 for g in gate.values() if g.get("coherent") is False),
             "split": int((gated["action"] == "split").sum())}
    return gated, stats


def decisions_d(out_dir, ent, generic=None):
    """(final table, stats) of variant D: vote -> noise -> gate -> reconcile (reconcile skipped while no reconcile
    response exists). The scorer's name_merge can still be applied on top. `generic` overrides generic.json."""
    dec, stats = _stage1_d(out_dir, ent, generic)
    units = units_from_dec(dec)
    answers = {}
    by_uid = {u["uid"]: u["clusters"] for u in units}
    stale = 0
    for j in _jobs_of(out_dir, ent, "reconcile"):
        o = load_obj(out_dir, j)
        if o is None:
            continue
        if "unit_clusters" in j and list(j["unit_clusters"]) != list(by_uid.get(j["unit_id"], [])):
            stale += 1  # the unit ids moved since stage 2 was built: never apply an answer to another unit
            continue
        answers[j["unit_id"]] = o
    out = apply_reconcile(dec, units, answers)
    stats["reconcile_answers"], stats["reconcile_stale"] = len(answers), stale
    stats["reconcile_merged"] = sum(1 for a in answers.values() if PV.norm_name(a.get("same_as", "none")) not in ("none", ""))
    out["variant"], out["run_tag"] = "full", "vote3"
    return out, stats


# ---------------------------------------------------------------- wf_v3.3: E variants and carry-over
E_SEEDS = (0, 1, 2)
CARRY_TOKEN = "{{CARRY_OVER}}"
CARRY_HEAD = ("Attributes already found in other parts of this entity (reuse the exact name and list it again in your\n"
              "attributes if a cluster is the same attribute; otherwise make a new one):")
NOT_COLUMN_KEYS = (PV.NOT_ATTRIBUTE_KEY, PV.ATTRIBUTE_CUE_KEY)


def render_carry(attrs):
    """The carry-over block for [(name, description)]: unique by norm_name (first seen wins), not_attribute and
    attribute_cue left out. "" when nothing is left."""
    seen, lines = set(NOT_COLUMN_KEYS), []
    for name, desc in attrs:
        key = PV.norm_name(name)
        if key and key not in seen:
            seen.add(key)
            lines.append(f"- {name}: {desc}" if str(desc or "").strip() else f"- {name}")
    return CARRY_HEAD + "\n" + "\n".join(lines) if lines else ""


def _carry_attrs(out_dir, parents):
    """[(name, description)] of the parsed responses of the parent jobs, in parent order. Raises when a parent
    response is missing or unparsable."""
    attrs = []
    for j in parents:
        obj = load_obj(out_dir, j)
        if obj is None:
            raise ValueError(f"carry-over parent {j['job']} has no parsed response in {Path(out_dir) / 'responses'}")
        attrs += [(str(a.get("name") or ""), str(a.get("description") or ""))
                  for a in obj.get("attributes") or [] if isinstance(a, dict)]
    return attrs


def _fill_text(tmpl, block):
    """tmpl with the placeholder replaced by the block; with no block the placeholder line is dropped."""
    if block:
        return tmpl.replace(CARRY_TOKEN, block)
    if "\n\n" + CARRY_TOKEN in tmpl:  # its own paragraph: drop it with its separator, as in the e1 prompts
        return tmpl.replace("\n\n" + CARRY_TOKEN, "", 1)
    return "".join(ln for ln in tmpl.splitlines(keepends=True) if ln.strip() != CARRY_TOKEN).replace(CARRY_TOKEN, "")


def fill_carry(out_dir, round):
    """Write the .txt of every manifest job of this round that has carry_from, from its .tmpl.txt with the carry
    block of its parents' parsed responses (variant f: the delex map of <out_dir>/delex_map.json applied to the
    whole text). Returns the filled jobs; raises if a parent has no parsed response. Deterministic. Colab-safe:
    s1a.delex is imported only for variant f."""
    out_dir = Path(out_dir)
    jobs = load_jobs(out_dir)
    by_name = {j["job"]: j for j in jobs}
    mine = [j for j in jobs if j.get("carry_from") and j.get("round") == round]
    missing = sorted({n for j in mine for n in j["carry_from"] if load_obj(out_dir, by_name[n]) is None})
    if missing:  # checked before writing anything, so a round is never half filled
        raise ValueError(f"round {round}: carry-over parents without a parsed response (delete their "
                         f"responses/<job>.jsonl and rerun them): {missing}")
    mp = None
    done = []
    for j in mine:
        text = _fill_text((out_dir / j["prompt"]).with_suffix(".tmpl.txt").read_text(encoding="utf-8"),
                          render_carry(_carry_attrs(out_dir, [by_name[n] for n in j["carry_from"]])))
        if j["variant"] == "f":
            from . import delex
            mp = json.loads((out_dir / "delex_map.json").read_text(encoding="utf-8")) if mp is None else mp
            text = delex.apply(text, mp)
        (out_dir / j["prompt"]).write_text(text, encoding="utf-8", newline="\n")
        done.append(j)
    return done


def decisions_e(out_dir, ent, var, gate_dir):
    """(table, stats) of a wf_v3.3 variant: var e | e1 | e2 | f. Vote over the orders (seeds 0-2; f: seed 0 only) of
    its entity jobs in out_dir (e1: group 0 from the `e` jobs, groups >= 1 from `e1`), then apply_gate with the gate
    and split responses of gate_dir (the v3.2 folder; f has no gate). stats: agree_mean, agree_full_share, ties, cue
    (attribute_cue clusters), gate_failed, split."""
    seeds = (0,) if var == "f" else E_SEEDS
    tabs = [decisions_b(out_dir, ent, s, split_results={}, variant=var, group0="e" if var == "e1" else None)
            for s in seeds]
    dec, stats = vote(tabs)
    if var != "f":
        gate = _by_cluster(gate_dir, ent, "gate")
        dec = apply_gate(dec, gate, _split_results(gate_dir, ent))
        stats["gate_failed"] = sum(1 for g in gate.values() if g.get("coherent") is False)
    else:
        stats["gate_failed"] = 0
    stats["cue"] = int((dec["action"] == "attribute_cue").sum())
    stats["split"] = int((dec["action"] == "split").sum())
    dec["variant"], dec["run_tag"] = var, f"s0-{len(seeds) - 1}"
    return dec, stats


# ---------------------------------------------------------------- stage 2
def _unit_vectors(units, vec):
    """Unit vector (unit length) of every unit: mean of its clusters' centroids (attr) or of its split examples."""
    cid_x = dict(zip(vec["cluster_ids"].tolist(), vec["cluster_x"]))
    ex_x = dict(zip(vec["ex_ids"].tolist(), vec["ex_x"]))
    out = {}
    for u in units:
        rows = [cid_x[c] for c in u["clusters"] if c in cid_x] if u["kind"] == "attr" else \
               [ex_x[e] for e in u["examples"] if e in ex_x]
        if rows:
            v = np.mean(rows, axis=0)
            out[u["uid"]] = v / max(np.linalg.norm(v), 1e-9)
    return out


def _lines(u, inp):
    """Up to N_LINES example lines of a unit, round-robin over its clusters (attr) or in example order (part)."""
    if u["kind"] == "part":
        ex = inp.get("split_examples", {}).get(u["clusters"][0], {})
        return [ex[e] for e in u["examples"] if e in ex][:N_LINES]
    per = [list(inp["clusters"].get(c, {}).get("lines") or []) for c in u["clusters"]]
    out = []
    for k in range(N_LINES):
        out += [p[k] for p in per if k < len(p)]
    return out[:N_LINES]


def build_stage2(out_dir, render=None, schema=None):
    """Write the reconcile prompts/schemas and append their jobs (stage 2) to manifest.json; return the new jobs.
    Needs only the stage-1 responses, stage2_inputs.json and stage2_vectors.npz. Rerunning rewrites the same files
    and replaces (never duplicates) the reconcile jobs. `render(unit, candidates) -> text` and
    `schema(unit_id, candidate_names) -> dict` default to pilot_input.render_reconcile / schema_reconcile
    (imported here, not at module level: pilot_input pulls in the whole export stack). unit = {unit_id, entity, ent,
    kind, name, description, lines}; candidates = [(name, description)] (best first)."""
    out_dir = Path(out_dir)
    if render is None or schema is None:
        from . import pilot_input as PI
        render, schema = render or PI.render_reconcile, schema or PI.schema_reconcile
    inputs = json.loads((out_dir / "stage2_inputs.json").read_text(encoding="utf-8"))
    vec = dict(np.load(out_dir / "stage2_vectors.npz", allow_pickle=False))
    jobs = load_jobs(out_dir)
    kept = [j for j in jobs if j["kind"] != "reconcile"]
    stage1 = [j for j in kept if j["kind"] == "entity"]
    new = []
    for ent in dict.fromkeys(j["ent"] for j in stage1):
        entity = next(j["entity"] for j in stage1 if j["ent"] == ent)
        dec, _ = _stage1_d(out_dir, ent)
        units = units_from_dec(dec)
        vecs = _unit_vectors(units, vec)
        attrs = [u for u in units if u["kind"] == "attr" and u["uid"] in vecs]
        for u in units:
            cands = sorted((a for a in attrs if a["uid"] != u["uid"]), key=lambda a: a["uid"]) if u["uid"] in vecs else []
            sims = [float(vecs[a["uid"]] @ vecs[u["uid"]]) for a in cands]
            ranked = [cands[k] for k in sorted(range(len(cands)), key=lambda k: -sims[k])]  # stable: ties by uid
            seen, top = {PV.norm_name(u["name"])}, []
            for a in ranked:  # one candidate per name (the answer is matched by name), never the unit's own name
                if len(top) < TOP_K and PV.norm_name(a["name"]) and PV.norm_name(a["name"]) not in seen:
                    seen.add(PV.norm_name(a["name"]))
                    top.append(a)
            if not top:
                continue
            unit = {"unit_id": u["uid"], "entity": entity, "ent": ent, "kind": u["kind"], "name": u["name"],
                    "description": u["description"], "lines": _lines(u, inputs[ent])}
            slug = u["uid"].replace("#", "-")
            stem = f"prompts/{ent}_reconcile_{slug}"
            (out_dir / f"{stem}.txt").write_text(render(unit, [(a["name"], a["description"]) for a in top]), encoding="utf-8")
            (out_dir / f"{stem}.schema.json").write_text(
                json.dumps(schema(u["uid"], [a["name"] for a in top]), indent=1), encoding="utf-8")
            new.append({"job": f"{ent}_reconcile_{slug}_r1", "entity": entity, "ent": ent, "variant": "reconcile",
                        "run_tag": "r1", "kind": "reconcile", "stage": 2, "nbhd": None, "cluster_id": "",
                        "unit_id": u["uid"], "unit_clusters": list(u["clusters"]), "prompt": f"{stem}.txt", "schema": f"{stem}.schema.json",
                        "max_tokens": RECONCILE_MAX_TOKENS, "format": "reconcile"})
    m = json.loads(_manifest_path(out_dir).read_text(encoding="utf-8"))
    merged = kept + new
    _manifest_path(out_dir).write_text(json.dumps({**m, "jobs": merged} if isinstance(m, dict) else merged, indent=1),
                                       encoding="utf-8")
    return new
