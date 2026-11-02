"""wf_v3.6 data: the Colab batch (results/loop1_v36/colab, GT_V36_CONTRACT.md) as EntityData next to the v3.4 / v3.5
variants. No LLM, no models.

load_v36 reads the batch the way the earlier pilots were read: A s2 and AE s0/s1/s2 like the v3.1 A responses
(pilot_eval_v31._decisions; the v3.1 split pass is the fallback split, as for A r2), g like v3.2 C (decisions_b with the
v3.2 split pass, 3-order vote). load_oracle rebuilds the train entity on the oracle cluster table
(results/loop1_v35/oracle_clusters.csv) and reads the oracle jobs the same way as C; hotel and restaurant have no
two-role cluster, so their oracle rows are the C rows. `repairs` (a list or None = off) turns on the parse repair
(llm_cache.repair_undeclared) for every response read and collects {variant, ent, job, repaired_names}.
"""

import dataclasses
from dataclasses import replace
from pathlib import Path

import pandas as pd

from . import pilot_combine as PC
from . import pilot_score as PS
from . import pilot_verify as PV
from . import v34_data as D
from pilot_eval_v31 import _decisions, _examples  # noqa: E402  (scripts/ is on sys.path via s1a.v34_data)
from pilot_eval_v32 import _have, _jobs, _objs  # noqa: E402

SEEDS = (0, 1, 2)
A_LABELS = {"v2": ("A", "s2"), "ae": ("AE", None)}  # job variant -> (label letter, run_tag or None = every order)


def _add(variants, label, dec, e, ctx, entity):
    """variants[label] and variants["<letter>+namemerge <tag>"] of one decision table (as v34_data.load_all)."""
    letter, tag = label.split(" ")
    dec = dec.assign(variant=letter, run_tag=tag)
    variants[label] = D._finalize(dec, e, ctx, entity)
    variants[f"{letter}+namemerge {tag}"] = D._finalize(PS.name_merge(dec, e.mentions, entity), e, ctx, entity)


def _job_variant(jobs, ent, variant):
    return [j for j in jobs if j["ent"] == ent and j["kind"] == "entity" and j["variant"] == variant]


def _tally(repairs, rows, variant, ent):
    if repairs is not None:
        repairs.extend({"variant": variant, "ent": ent, **r} for r in rows)


def _a_style(dir36, jobs36, ent, cids, split31, repairs):
    """{label: decision table}: A s2 (job variant v2) and AE s0 / s1 / s2 / s012 (job variant ae). A job whose response
    is missing is skipped."""
    out = {}
    for var, (letter, only) in A_LABELS.items():
        tabs = {}
        for job in _job_variant(jobs36, ent, var):
            path = dir36 / "responses" / f"{job['job']}.jsonl"
            if only and job["run_tag"] != only or not path.exists():
                continue
            rows = None if repairs is None else []
            tabs[job["run_tag"]] = _decisions(job, path, cids, split31, rows)
            _tally(repairs, rows or [], f"{letter} {job['run_tag']}", ent)
        out.update({f"{letter} {tag}": t for tag, t in tabs.items()})
        if var == "ae" and len(tabs) == len(SEEDS):
            out["AE s012"] = PC.vote([tabs[f"s{s}"] for s in SEEDS])[0]
    return out


def _c_style(dir36, jobs36, ent, variant, letter, split32, repairs):
    """{label: decision table} of variant `variant` (g | oracle): one table per order and the 3-order vote, read like
    v3.2 C (decisions_b with the v3.2 split pass, PC.vote). Empty when an order is missing."""
    mine = [j for j in _job_variant(jobs36, ent, variant)]
    if not mine or not all(_have(dir36, [j for j in mine if j["run_tag"] == f"s{s}"]) for s in SEEDS):
        return {}
    tabs = []
    for s in SEEDS:
        rows = None if repairs is None else []
        tabs.append(PC.decisions_b(dir36, ent, s, split32, variant=variant, repairs=rows))
        _tally(repairs, rows or [], f"{letter} s{s}", ent)
    out = {f"{letter} s{s}": t for s, t in enumerate(tabs)}
    out[f"{letter} s012"] = PC.vote(tabs)[0]
    return out


def load_v36(shared, data, dir36, dir32, dir31, repairs=None):
    """({ent: EntityData holding A s2, AE s0-s2, AE s012, g s0-s2, g s012, each also +namemerge}, notes). Each is a copy
    of the v3.4 EntityData of the entity (A-style labels read ctx_a, the others ctx_r, as the scorer does)."""
    dir36, dir32, dir31 = Path(dir36), Path(dir32), Path(dir31)
    jobs36, jobs32 = _jobs(dir36), _jobs(dir32)
    split31 = {}
    for (ent, tag), objs in PV.load_split_results(dir31 / "responses").items():
        split31.setdefault(ent, {})[tag] = objs
    e, out, notes = shared.e, {}, []
    for ent, ed in data.items():
        split32 = _objs(dir32, [j for j in jobs32 if j["ent"] == ent], "split")
        decs = {}
        decs.update(_a_style(dir36, jobs36, ent, ed.cids, split31, repairs))
        decs.update(_c_style(dir36, jobs36, ent, "g", "g", split32, repairs))
        notes += [f"{ent}: {name} skipped, responses missing in {dir36}" for name in ("A s2", "AE s012", "g s012")
                  if name not in decs]
        variants = {}
        for label, dec in decs.items():
            _add(variants, label, dec, e, ed.ctx_a if label.startswith("A") else ed.ctx_r, ed.entity)
        out[ent] = replace(ed, variants=variants, vote_stats={}, seed_decs={})
    return out, notes


# ---- oracle (T14)

def oracle_ids(path):
    """{mention_id (int): oracle_cluster_id} of results/loop1_v35/oracle_clusters.csv."""
    t = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    return dict(zip(t["mention_id"].astype(int), t["oracle_cluster_id"]))


def with_oracle_ids(mentions, ids):
    """`mentions` with cluster_id replaced by the oracle id where `ids` has one (mention_id -> id), else kept."""
    return mentions.assign(cluster_id=[ids.get(int(m), c) for m, c in zip(mentions["mention_id"], mentions["cluster_id"])])


def oracle_labels(labels, cids):
    """labels.csv rows for oracle cluster ids: each id ("E1#0.b") takes the row of its original cluster ("E1#0")."""
    by = labels.set_index("cluster_id")
    rows = []
    for cid in cids:
        r = by.loc[cid.split(".")[0]].copy()
        rows.append({**r.to_dict(), "cluster_id": cid})
    return pd.DataFrame(rows, columns=["cluster_id"] + [c for c in labels.columns if c != "cluster_id"])


def load_oracle(shared, data, dir36, dir32, oracle_csv, repairs=None):
    """({ent: EntityData}, notes): variants "Oracle s0", "Oracle s1", "Oracle s2", "Oracle s012" (+namemerge for train).
    Train: the entity rebuilt on the oracle cluster table (every two-role cluster split by gold role), the oracle jobs
    read like C (the v3.2 split pass applies to the clusters that were not split). Hotel and restaurant: the copy of
    the C rows (C s0 / s1 / s2 / s012), since no cluster of theirs is split."""
    dir36, dir32 = Path(dir36), Path(dir32)
    jobs36, jobs32 = _jobs(dir36), _jobs(dir32)
    ids = oracle_ids(oracle_csv)
    out, notes = {}, []
    for ent, ed in data.items():
        if not _job_variant(jobs36, ent, "oracle"):
            variants = {}
            for k, v in ed.variants.items():
                letter, tag = k.split(" ")
                if letter == "C":
                    variants[f"Oracle {tag}"] = v
                elif letter == "C+namemerge":
                    variants[f"Oracle+namemerge {tag}"] = v
            out[ent] = replace(ed, variants=variants)
            continue
        e2 = dataclasses.replace(shared.e, mentions=with_oracle_ids(shared.e.mentions, ids))
        men = with_oracle_ids(ed.mentions, ids)
        cids = sorted(c for c in men["cluster_id"].unique() if c)
        labels = oracle_labels(shared.labels_all, cids)
        ex = _examples(dir36 / "examples.csv", cids)
        ctx = PS.Ctx(e2.mentions, labels, shared.gv, shared.gold_attrs, e2.ids, e2.x, ex, ed.entity, ed.gold_ents)
        split32 = _objs(dir32, [j for j in jobs32 if j["ent"] == ent], "split")
        decs = _c_style(dir36, jobs36, ent, "oracle", "Oracle", split32, repairs)
        if not decs:
            notes.append(f"{ent}: oracle skipped, responses missing in {dir36}")
            continue
        variants = {}
        for label, dec in decs.items():
            _add(variants, label, dec, e2, ctx, ed.entity)
        out[ent] = replace(ed, mentions=men, cids=cids, labels=labels, ctx_a=ctx, ctx_r=ctx, variants=variants,
                           vote_stats={}, seed_decs={})
    return out, notes
