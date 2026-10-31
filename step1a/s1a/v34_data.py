"""wf_v3.4 data bundle (SCORER_V34_CONTRACT.md, W1): every variant A-D of the v3.1/v3.2 pilots as decision table,
attributes and mention assignment per entity, plus the per-mention evidence table. No LLM, no models.

load_all(run, dir32, dir31) re-reads the saved responses the way scripts/pilot_eval_v32.py does; no old file is edited.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from . import mentions as MN  # noqa: E402
from . import pilot_combine as PC  # noqa: E402
from . import pilot_input as PIN  # noqa: E402
from . import pilot_score as PS  # noqa: E402
from . import pilot_verify as PV  # noqa: E402
from pilot_eval_v31 import GOLD_ENTS, _decisions, _examples, _read  # noqa: E402
from pilot_eval_v32 import _have, _jobs, _objs  # noqa: E402

VARIANTS = ["A r1", "A r2", "B s0", "C s0", "C s1", "C s2", "C s012", "D s012"]
SEEDS = (0, 1, 2)
BASE_COLS = ["ent", "entity", "cluster_id", "mention_id", "value", "norm_value", "left_word", "speaker", "turn_text",
             "prev_turn", "gold_attr", "entity_gold", "old_label"]
VARIANT_FIELDS = ("name", "action", "group", "place")
ATTR_OUT_COLS = ["variant label", "ent", "attr_id", "name", "description", "clusters", "source", "status"]


@dataclass
class VariantOut:
    dec: pd.DataFrame        # decision table (decisions.csv columns)
    attrs: pd.DataFrame      # PV.final_attributes attrs
    assign: dict             # {mention_id(int): attr_id}
    parts: dict              # split parts as returned by PV.final_attributes


@dataclass
class EntityData:
    ent: str                 # train / hotel / restaurant
    entity: str              # E1 / E0 / E2
    gold_ents: list          # pilot_eval_v31.GOLD_ENTS
    cids: list               # sorted cluster ids of the entity
    mentions: pd.DataFrame   # clustered mentions: mentions.csv columns + speaker, turn_text, prev_turn
    labels: pd.DataFrame     # labels.csv rows of these clusters (old noise labels)
    ctx_a: object            # PS.Ctx with loop1_v31 examples (for A)
    ctx_r: object            # PS.Ctx with loop1_v32 examples (B, C, D)
    variants: dict           # {label: VariantOut}
    vote_stats: dict         # C vote stats (PC.vote)
    seed_decs: dict          # {"C s0": dec, "C s1": dec, "C s2": dec}


@dataclass
class Shared:
    e: object
    docs: object
    gv: object
    gold_attrs: object
    labels_all: pd.DataFrame
    clusters: pd.DataFrame


def turn_context(doc, turn):
    """(speaker, turn text, previous turn as "speaker: text" or ""); texts are whitespace-flattened, not cut."""
    lo, hi = MN.turn_bounds(doc, turn)
    prev = ""
    if turn > 0:
        plo, phi = MN.turn_bounds(doc, turn - 1)
        prev = f"{PIN._speaker(doc, turn - 1)}: " + PIN._flat(doc.text[plo:phi])
    return PIN._speaker(doc, turn), PIN._flat(doc.text[lo:hi]), prev


def _with_context(mentions, docs):
    """`mentions` plus speaker, turn_text, prev_turn columns (one lookup per distinct doc/turn)."""
    cache = {}
    rows = []
    for did, turn in zip(mentions["dialogue_id"], mentions["turn"]):
        key = (did, int(turn))
        if key not in cache:
            cache[key] = turn_context(docs[did], int(turn))
        rows.append(cache[key])
    return mentions.assign(**{c: [r[i] for r in rows] for i, c in enumerate(("speaker", "turn_text", "prev_turn"))})


def _finalize(dec, e, ctx, entity):
    assign, attrs, parts = PV.final_attributes(dec, e.mentions, e.ids, e.x, ctx.examples, entity)
    return VariantOut(dec, attrs, assign, parts)


def _entity_decs(ent, cids, dir32, dir31, jobs32, jobs31, split31):
    """({label: dec}, vote_stats, seed_decs) of VARIANTS (as is, before the name merge). Missing responses raise."""
    mine = [j for j in jobs32 if j["ent"] == ent]
    split = _objs(dir32, mine, "split")
    decs = {}
    for tag in ("r1", "r2"):
        job = next((j for j in jobs31 if j["ent"] == ent and j["kind"] == "entity" and j["variant"] == "v2"
                    and j["run_tag"] == tag), None)
        path = dir31 / "responses" / f"{job['job']}.jsonl" if job else None
        if path is None or not path.exists():
            raise FileNotFoundError(f"{ent}: no v2 {tag} response in {dir31}")
        decs[f"A {tag}"] = _decisions(job, path, cids, split31)
    for s in SEEDS:
        nbhd = [j for j in mine if j["kind"] == "entity" and j["run_tag"] == f"s{s}"]
        if not _have(dir32, nbhd):
            raise FileNotFoundError(f"{ent}: nbhd s{s} responses missing in {dir32}")
    seeds = [PC.decisions_b(dir32, ent, s, split) for s in SEEDS]
    seed_decs = {f"C s{s}": seeds[s] for s in SEEDS}
    decs["B s0"] = seeds[0]
    decs.update(seed_decs)
    decs["C s012"], vote_stats = PC.vote(seeds)
    decs["D s012"], _ = PC.decisions_d(dir32, ent)
    return {k: decs[k] for k in VARIANTS}, vote_stats, seed_decs


def load_all(run, dir32, dir31):
    """(Shared, {ent: EntityData}) for train, hotel, restaurant. Labels: VARIANTS and "<letter>+namemerge <tag>"."""
    run, dir32, dir31 = Path(run), Path(dir32), Path(dir31)
    e = MN.load(run / "spans")
    docs, gv, gold_attrs = MN.load_shared(run)
    labels_all = _read(run / "spans" / "labels.csv")
    clusters = _read(run / "spans" / "clusters.csv")
    shared = Shared(e, docs, gv, gold_attrs, labels_all, clusters)
    jobs32, jobs31 = _jobs(dir32), _jobs(dir31)
    split31 = {}
    for (ent, tag), objs in PV.load_split_results(dir31 / "responses").items():
        split31.setdefault(ent, {})[tag] = objs
    out = {}
    for ent in dict.fromkeys(j["ent"] for j in jobs32 if j["kind"] == "entity"):
        entity = next(j["entity"] for j in jobs32 if j["ent"] == ent)
        cids = sorted(c for c in e.mentions.loc[e.mentions["entity"] == entity, "cluster_id"].unique() if c)
        gold_ents = GOLD_ENTS.get(ent, [ent])

        def ctx_of(path):
            return PS.Ctx(e.mentions, labels_all, gv, gold_attrs, e.ids, e.x, _examples(path, cids), entity, gold_ents)

        ctx_a, ctx_r = ctx_of(dir31 / "examples.csv"), ctx_of(dir32 / "examples.csv")
        decs, vote_stats, seed_decs = _entity_decs(ent, cids, dir32, dir31, jobs32, jobs31, split31)
        variants = {}
        for label, dec in decs.items():
            letter, tag = label.split(" ")
            ctx = ctx_a if letter == "A" else ctx_r
            dec = dec.assign(variant=letter, run_tag=tag)
            variants[label] = _finalize(dec, e, ctx, entity)
            variants[f"{letter}+namemerge {tag}"] = _finalize(PS.name_merge(dec, e.mentions, entity), e, ctx, entity)
        pm = e.mentions[(e.mentions["entity"] == entity) & (e.mentions["cluster_id"] != "")]
        out[ent] = EntityData(ent, entity, gold_ents, cids, _with_context(pm, docs),
                              labels_all[labels_all["cluster_id"].isin(cids)], ctx_a, ctx_r, variants, vote_stats,
                              seed_decs)
    return shared, out


def _variant_columns(key, vo, men):
    """{<k>_name, <k>_action, <k>_group, <k>_place} lists for the mention table `men` of one variant."""
    k = key.replace(" ", "_")
    row = {r["cluster_id"]: r for _, r in vo.dec.iterrows()}
    cid = list(men["cluster_id"])

    def get(c, f):
        return row[c][f] if c in row else ""

    return {f"{k}_name": [get(c, "name") for c in cid], f"{k}_action": [get(c, "action") for c in cid],
            f"{k}_group": [vo.assign.get(int(m), "") for m in men["mention_id"]],
            f"{k}_place": [get(c, "placement") for c in cid]}


def evidence_table(data):
    """One row per clustered mention of every entity in `data`: BASE_COLS then, per key of VARIANTS,
    <k>_name, <k>_action, <k>_group, <k>_place (k = key with spaces as "_")."""
    frames = []
    for ed in data.values():
        m = ed.mentions
        old = ed.labels.set_index("cluster_id")["label"].to_dict()
        base = pd.DataFrame({
            "ent": ed.ent, "entity": ed.entity, "cluster_id": m["cluster_id"].values,
            "mention_id": m["mention_id"].astype(int).values, "value": m["text"].values,
            "norm_value": m["norm_value"].values, "left_word": m["left_word"].values,
            "speaker": m["speaker"].values, "turn_text": m["turn_text"].values, "prev_turn": m["prev_turn"].values,
            "gold_attr": [g or "none" for g in m["gold_attr"]], "entity_gold": m["entity_gold"].values,
            "old_label": [old.get(c, "") for c in m["cluster_id"]]})
        cols = {}
        for key in VARIANTS:
            cols.update(_variant_columns(key, ed.variants[key], m))
        frames.append(pd.concat([base, pd.DataFrame(cols, index=base.index)], axis=1))
    return pd.concat(frames, ignore_index=True)


def attrs_table(data):
    """attrs.csv rows (ATTR_OUT_COLS) for every variant label, incl. +namemerge, of every entity."""
    rows = []
    for ed in data.values():
        for label, vo in ed.variants.items():
            a = vo.attrs
            rows.append(pd.DataFrame({"variant label": label, "ent": ed.ent, "attr_id": a["attr_id"],
                                      "name": a["name"], "description": a["description"],
                                      "clusters": a["clusters"], "source": a["source"], "status": a["status"]}))
    return pd.concat(rows, ignore_index=True)[ATTR_OUT_COLS]
