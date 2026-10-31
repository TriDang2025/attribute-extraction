"""wf_v3.5 data: the v3.3 variants C, E, E1, E2 as EntityData, next to the v3.2 variants of s1a.v34_data.

load_v33 re-reads the saved v3.3 responses the way scripts/pilot_eval_v33.py does (same vote, gate and split
responses of dir32, same combined examples, P4 cue spread on for every variant, gold-share rule noise labels); no old
file is edited. Labels: "C33 s012" (v3.2 C with the cue spread; the v3.4 "C s012" has none), "E s012", "E1 s012",
"E2 s012", each also as "<letter>+namemerge s012".
"""

from dataclasses import replace
from pathlib import Path

import pandas as pd

from . import pilot_combine as PC
from . import pilot_score as PS
from . import pilot_verify as PV
from . import v34_data as D
from pilot_eval_v31 import _examples  # noqa: E402  (scripts/ is on sys.path via s1a.v34_data)
from pilot_eval_v32 import _jobs, _objs  # noqa: E402
from pilot_eval_v33 import SEEDS, TAG, VAR, _have, needed  # noqa: E402

LETTERS = {"C": "C33", "E": "E", "E1": "E1", "E2": "E2"}  # v3.3 pilot letter -> label letter here


def _finalize_cue(dec, shared, ctx, entity, left_words):
    e = shared.e
    assign, attrs, parts = PV.final_attributes(dec, e.mentions, e.ids, e.x, ctx.examples, entity, left_words)
    return D.VariantOut(dec, attrs, assign, parts)


def load_v33(shared, data, dir33, dir32):
    """({ent: EntityData holding only the v3.3 variants}, notes). Each EntityData is a copy of the v3.4 one for the same
    entity with the v3.3 + v3.2 examples in ctx_r and the rule-noise labels; a variant whose responses are missing is
    skipped with a note."""
    dir33, dir32 = Path(dir33), Path(dir32)
    e = shared.e
    labels = PS.rule_noise_labels(shared.labels_all, e.mentions)
    left_words = PV.left_word_map(e.mentions, shared.docs)
    jobs33, jobs32 = _jobs(dir33), _jobs(dir32)
    out, notes = {}, []
    for ent, ed in data.items():
        mine33, mine32 = [j for j in jobs33 if j["ent"] == ent], [j for j in jobs32 if j["ent"] == ent]
        split32 = _objs(dir32, mine32, "split")
        decs, stats = {}, {}
        if _have(dir32, needed(mine32, "C")):
            decs["C"], stats["C"] = PC.vote([PC.decisions_b(dir32, ent, s, split32) for s in SEEDS])
        else:
            notes.append(f"{ent}: C skipped, v3.2 nbhd responses missing in {dir32}")
        for letter, var in VAR.items():
            if letter == "F":
                continue
            if _have(dir33, needed(mine33, letter)):
                decs[letter], stats[letter] = PC.decisions_e(dir33, ent, var, dir32)
            else:
                notes.append(f"{ent}: {letter} skipped, `{var}` responses missing in {dir33}")
        if not decs:
            continue
        ex = pd.concat([_examples(dir33 / "examples.csv", ed.cids), _examples(dir32 / "examples.csv", ed.cids)]
                       ).drop_duplicates("ex_id")
        ctx = PS.Ctx(e.mentions, labels, shared.gv, shared.gold_attrs, e.ids, e.x, ex, ed.entity, ed.gold_ents)
        variants = {}
        for letter, dec in decs.items():
            lab = LETTERS[letter]
            dec = dec.assign(variant=lab, run_tag=TAG[letter])
            variants[f"{lab} {TAG[letter]}"] = _finalize_cue(dec, shared, ctx, ed.entity, left_words)
            merged = PS.name_merge(dec, e.mentions, ed.entity)
            variants[f"{lab}+namemerge {TAG[letter]}"] = _finalize_cue(merged, shared, ctx, ed.entity, left_words)
        out[ent] = replace(ed, ctx_a=ctx, ctx_r=ctx, variants=variants, vote_stats=stats.get("C", {}),
                           seed_decs={}, labels=labels[labels["cluster_id"].isin(ed.cids)])
    return out, notes
