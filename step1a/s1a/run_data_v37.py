"""wf_v3.7 T9/T13: EntityData of a Step 1a run without any LLM response, so that the recall and ceiling code (W1's
ceiling_v37.ceiling_for) runs on a run dir such as results/graph_v22_dev50b or graph_v23_dev50. Mirrors the context
part of v34_data.load_all: Ctx with the L1 train attributes, clustered mentions with speaker / turn text; variants empty.
The run needs spans/{mentions,clusters,instances}.csv, vectors.npz, labels.csv (graph_run.py --stage labels).

load_a reads the A jobs of the v3.7 Colab batch (results/loop1_v37/colab, scripts/pilot_build_v37.py) for one run the way
v36_data reads A: `_decisions` with the split pass of the same run (tag r1 as fallback for every order) and the parse
repair on when `repairs` is a list; variants "A s0" / "A s1" / "A s2" and the 3-order vote "A s012" (PC.vote), each also
+namemerge (v36_data._add). The ctx examples are the batch's examples.csv rows of that run's A and split jobs (the split parts of PV.final_attributes
resolve the example ids of the split prompts; without them a split cluster stays one unsplit group).
"""

import copy
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pandas as pd

from . import mentions as MN
from . import pilot_combine as PC
from . import pilot_score as PS
from . import v34_data as VD
from . import v36_data as V36
from pilot_eval_v31 import _decisions, _read  # noqa: E402  (scripts/ is on sys.path via s1a.v34_data)
from pilot_eval_v32 import _objs  # noqa: E402

GOLD_ENTS = {"train": ["train"], "hotel": ["hotel"], "restaurant": ["restaurant", "taxi"]}


def entity_ids(mentions, gold_ents=None):
    """{ent: stage-1 entity id} (train / hotel / restaurant -> "E1" ...): among the stage-1 entities whose clustered
    gold-labelled mentions have the ent (or one of its gold entities) as most common entity_gold, the one with most
    clustered mentions (small entities such as E4 of dev50 also lean to train). Ids of different runs differ (k-means),
    so they are looked up, never hard-coded. Raises when an ent has no entity or two ents share one."""
    gold_ents = gold_ents or GOLD_ENTS
    clustered = mentions[mentions["cluster_id"] != ""]
    size = clustered["entity"].value_counts()
    m = clustered[clustered["entity_gold"] != ""]
    top = {e: Counter(g["entity_gold"]).most_common(1)[0][0] for e, g in m.groupby("entity")}
    out = {}
    for ent, golds in gold_ents.items():
        hit = sorted(e for e, g in top.items() if g in golds)
        best = [e for e in hit if top[e] == ent] or hit   # a taxi-dominated entity only when no ent-dominated one exists
        if not best:
            raise ValueError(f"{ent}: no stage-1 entity (top entity_gold {top})")
        out[ent] = max(best, key=lambda e: (size[e], e))
    if len(set(out.values())) != len(out):
        raise ValueError(f"two ents share one stage-1 entity: {out}")
    return out


def entity_data(run):
    """(Shared, {ent: EntityData}) of a run dir: no variants, no responses."""
    run = Path(run)
    e = MN.load(run / "spans")
    docs, gv, gold_attrs = MN.load_shared(run)
    labels_all = VD._read(run / "spans" / "labels.csv")
    clusters = VD._read(run / "spans" / "clusters.csv")
    shared = VD.Shared(e, docs, gv, gold_attrs, labels_all, clusters)
    examples = pd.DataFrame(columns=["ex_id", "cluster_id", "mention_id"])
    out = {}
    for ent, entity in entity_ids(e.mentions).items():
        cids = sorted(c for c in e.mentions.loc[e.mentions["entity"] == entity, "cluster_id"].unique() if c)
        ctx = PS.Ctx(e.mentions, labels_all, gv, gold_attrs, e.ids, e.x, examples, entity, GOLD_ENTS[ent])
        pm = e.mentions[(e.mentions["entity"] == entity) & (e.mentions["cluster_id"] != "")]
        out[ent] = VD.EntityData(ent, entity, GOLD_ENTS[ent], cids, VD._with_context(pm, docs),
                                 labels_all[labels_all["cluster_id"].isin(cids)], ctx, ctx, {}, {}, {})
    return shared, out


# ---- the A jobs of the v3.7 Colab batch

SEEDS = V36.SEEDS


def batch_jobs(dir37, run, ent):
    """(A jobs, split jobs) of the manifest of `dir37` for one run and entity (family a / split)."""
    m = json.loads((Path(dir37) / "manifest.json").read_text(encoding="utf-8"))
    mine = [j for j in (m["jobs"] if isinstance(m, dict) else m) if j.get("run") == run and j["ent"] == ent]
    return [j for j in mine if j["family"] == "a"], [j for j in mine if j["family"] == "split"]


def batch_examples(dir37, jobs, cids):
    """examples.csv rows of the given jobs (column `variant` = job name) for clusters `cids`, one row per ex_id."""
    ex = _read(Path(dir37) / "examples.csv")
    ex = ex[ex["variant"].isin({j["job"] for j in jobs}) & ex["cluster_id"].isin(cids)]
    return ex.drop_duplicates("ex_id")


def load_a(shared, data, dir37, run, repairs=None):
    """({ent: EntityData with variants A s0 / s1 / s2 / s012 (+namemerge)}, notes) for the entity data `data` of the run
    `run` (a key of the manifest `runs`; `data` from entity_data(<that run dir>)). A job without a response is skipped;
    A s012 needs all three orders. `repairs`: None = as saved; a list = parse repair on, one row per repaired response."""
    dir37 = Path(dir37)
    out, notes = {}, []
    for ent, ed in data.items():
        a_jobs, split_jobs = batch_jobs(dir37, run, ent)
        split = {ent: {"r1": _objs(dir37, split_jobs, "split")}}
        ctx = copy.copy(ed.ctx_a)
        ctx.examples = batch_examples(dir37, a_jobs + split_jobs, ed.cids)  # split parts name the split prompt's example ids
        tabs = {}
        for job in sorted(a_jobs, key=lambda j: j["run_tag"]):
            path = dir37 / "responses" / f"{job['job']}.jsonl"
            if not path.exists():
                notes.append(f"{ent}: {job['job']} skipped, no response in {dir37}")
                continue
            rows = None if repairs is None else []
            tabs[job["run_tag"]] = _decisions(job, path, ed.cids, split, rows)
            V36._tally(repairs, rows or [], f"A {job['run_tag']}", ent)
        decs = {f"A {tag}": t for tag, t in tabs.items()}
        if len(tabs) == len(SEEDS):
            decs["A s012"] = PC.vote([tabs[f"s{s}"] for s in SEEDS])[0]
        else:
            notes.append(f"{ent}: A s012 skipped, {len(tabs)} of {len(SEEDS)} orders")
        variants = {}
        for label, dec in decs.items():
            V36._add(variants, label, dec, shared.e, ctx, ed.entity)
        out[ent] = replace(ed, ctx_a=ctx, ctx_r=ctx, variants=variants, vote_stats={}, seed_decs={})
    return out, notes
