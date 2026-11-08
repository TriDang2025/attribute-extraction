"""wf_v4.1 Step 3 naming for loop 2: adapter from loop-2 clusters to the inputs of the frozen Step 3 A prompt (pure; no I/O).

Loop 2 (s1a/loop2_v41.py) writes clusters.json: one cluster per label, ids "L2:<entity>#<n>", the mentions inline. The frozen A
prompt (pilot_input.render_v2 + schema_v2, STEP3.md) wants a PilotInput whose clusters are ClusterInput(cluster_id, n_mentions,
n_values, low_conf, examples [(ex_id, mention_id)]) and whose mentions are looked up by mention_id in export.mentions. Nothing
in the frozen code changes: the loop-2 mentions are appended to a COPY of the loop-1 mentions table (cluster_id = the L2 id,
entity = the stage-1 id) and the loop-1 PilotInput of the same entity supplies `options` and `others` (same placement options
and other-entity values as the loop-1 A prompt).

Design: only the selected loop-2 clusters of one entity go to the prompt ("new clusters only"); render_v2 has no slot for the
entity's existing columns, so they are not shown (see the report in check.md).
"""

from dataclasses import replace

import pandas as pd

from . import pilot_input as PIN

MENTION_COLS = ["mention_id", "input", "dialogue_id", "turn", "char_start", "char_end", "text", "norm_value", "left_word",
                "context", "cluster_id", "entity", "entity_gold", "instance_id", "gold_attr", "gliner_score"]


def select_clusters(clusters, include_dropped=False):
    """Loop-2 clusters with spans that go to Step 3: the kept ones (`keep`), or every cluster when `include_dropped`
    (dry run only). Clusters without mentions never go."""
    return [c for c in clusters if c["mentions"] and (include_dropped or c["keep"])]


def loop2_rows(clusters):
    """mentions.csv rows (MENTION_COLS) of the loop-2 mentions of `clusters`; cluster_id = the L2 id, entity = stage1_entity."""
    rows = []
    for c in clusters:
        if not c["stage1_entity"]:
            raise ValueError(f"{c['id']} has no stage1_entity (no handover): cannot place it in a stage-1 entity")
        for m in c["mentions"]:
            rows.append(dict(mention_id=int(m["mention_id"]), input="loop2", dialogue_id=m["dialogue_id"], turn=int(m["turn"]),
                             char_start=int(m["char_start"]), char_end=int(m["char_end"]), text=m["text"],
                             norm_value=m["norm_value"], left_word=m["left_word"], context=m["context"], cluster_id=c["id"],
                             entity=c["stage1_entity"], entity_gold="", instance_id=m["instance_id"], gold_attr="",
                             gliner_score=float(m["score"])))
    return rows


def merge_mentions(base, clusters):
    """A copy of the loop-1 mentions table `base` with the loop-2 mentions of `clusters` appended. Fails on a mention id
    that already exists (loop 2 numbers its mentions from max + 1; a table of another run would collide)."""
    new = pd.DataFrame(loop2_rows(clusters), columns=MENTION_COLS)
    dup = set(new["mention_id"]) & set(base["mention_id"])
    if dup or new["mention_id"].duplicated().any():
        raise ValueError(f"mention ids not unique after the merge: {sorted(dup)[:5]}")
    return pd.concat([base, new], ignore_index=True)


def l2_input(base_inp, merged, clusters, k=PIN.K_EXAMPLES, seed=0):
    """PilotInput of the loop-2 `clusters` of ONE stage-1 entity: entity, options and others from the loop-1 input
    `base_inp` (PIN.build_input on the loop-1 export); examples chosen by PIN.select_examples over `merged`
    (merge_mentions), ex ids "<cid>:<j>" as in the loop-1 prompt; low_conf False; n_values = distinct norm values."""
    cis = []
    for c in sorted(clusters, key=lambda c: PIN._cluster_number(c["id"])):
        if c["stage1_entity"] != base_inp.entity:
            raise ValueError(f"{c['id']} belongs to {c['stage1_entity']}, not {base_inp.entity}")
        g = merged[merged["cluster_id"] == c["id"]]
        cis.append(PIN.ClusterInput(c["id"], len(g), g["norm_value"].nunique(), False,
                                    [(f"{c['id']}:{j}", mid) for j, mid in enumerate(PIN.select_examples(g, k, seed))]))
    return PIN.PilotInput(base_inp.entity, cis, base_inp.options, base_inp.others)


class Loop2Run:
    """Duck-types pilot_build_v37.RunInput for a_prompts: docs, export (with the merged mentions) and inp(entity, k)."""

    def __init__(self, base_run, merged, clusters, seed=0):
        self.docs, self.seed = base_run.docs, seed
        self.export = replace(base_run.export, mentions=merged)
        self._base, self._clusters = base_run, clusters

    def inp(self, entity, k):
        mine = [c for c in self._clusters if c["stage1_entity"] == entity]
        return l2_input(self._base.inp(entity, k), self.export.mentions, mine, k, self.seed)


# ------------------------------------------------------------------ reading the answers
def order_table(parsed, cluster_ids, tag):
    """Decision table (pilot_verify.DEC_COLS) of one order's parsed v2 answer."""
    from . import pilot_verify as PV
    return PV.decisions_from_v2(parsed, list(cluster_ids), "A", tag, None, require_mixed=False)


def voted_table(tables):
    """The frozen 3-order vote over the tables that exist (1 to 3 orders)."""
    from . import pilot_combine as PC
    return PC.vote(tables)


def answer_rows(dec, clusters):
    """[dict(cluster, label, keep, name, action, placement, merge_with)] of a decision table, one per cluster."""
    by = {c["id"]: c for c in clusters}
    return [dict(cluster=r["cluster_id"], label=by[r["cluster_id"]]["label"], keep=by[r["cluster_id"]]["keep"],
                 name=r["name"], action=r["action"] or "(no answer)", placement=r["placement"], merge_with=r["merge_with"])
            for _, r in dec.iterrows()]
