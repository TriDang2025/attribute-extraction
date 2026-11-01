"""wf_v3.6 task 16: the blind L2 name-rating sheet (GT_V36_CONTRACT.md, W3). No LLM.

Raters see a group name and description with its top values, and the L2 slot (name + schema.json description) that
the group's mentions mostly carry. They answer right / partly / wrong (names_l2_rubric.md). The rater copy has no
variant column and shuffled rows; the key file maps the shuffled `row` back to the scorer's join keys. The scorer side
is rules_names.read_l2_rated (names=l2rated).
"""

import pandas as pd

from . import rules_names as RN
from . import v34_data as VD

RATER_COLS = ["row", "ent", "group_name", "group_description", "top_values", "l2_attr", "l2_slot", "l2_slot_description"]
KEY_COLS = ["row", *RN.JOIN_KEYS, "variants", "n_variants"]
SEED = 0
RUBRIC = """# Names against L2 slot names: rubric (wf_v3.6)

Each row is one attribute group that a system proposed for a dialogue entity (hotel, restaurant, train). You see the
group's name and description, its most frequent values, and the MultiWOZ slot (name and schema description) that most
of the group's values carry. Judge only whether the group's name fits that slot. Answer with exactly one label:

- **right**: the name means the slot (for example "arrival_time" for train-arriveby; "reference_number" for a
  booking reference). Wording may differ.
- **partly**: the name is related but too general, too specific, or mixes the slot with another (for example
  "time" for train-arriveby, or "location" for train-destination).
- **wrong**: the name means something else (for example "departure" for train-destination, or "price" for
  hotel-stars).

Rules:
- Use the values to understand the group; judge the name, not the values.
- If unsure between right and partly, pick partly; if unsure between partly and wrong, pick wrong.
- Use no outside knowledge beyond this row.

Answer file: `row,label` (one line per row, labels right / partly / wrong).
"""


def slot_key(attr, tear_map):
    """MultiWOZ 2.2 slot ("domain-slot") of an L2 attribute name: through tear_to_mwoz.json for a TEAR attr, else the
    "<Domain> <slot>" name of gt_ext.slot_name ("Train trainid" -> "train-trainid")."""
    if attr in tear_map:
        return tear_map[attr]
    domain, _, slot = attr.lower().partition(" ")
    return f"{domain}-{slot}"


def l2_group_rows(bundles, gt_levels):
    """One row per (bundle entity, variant label, group) the names rule scores at L2: a group with a name and an L2
    majority attr. `bundles`: list of {ent: EntityData}. Columns: variant, ent, name, description,
    majority_gold_attr (at L2), top_values."""
    rows = []
    for bundle in bundles:
        for ent, led in VD.with_level(bundle, gt_levels, 2).items():
            for label in led.variants:
                rows += [{"variant": label, **{k: r[k] for k in (*RN.JOIN_KEYS, "top_values")}}
                         for r in RN._variant_rows(led, label, {}) if r["name"] and r["majority_gold_attr"]]
    return pd.DataFrame(rows, columns=["variant", *RN.JOIN_KEYS, "top_values"])


def rating_sheet(rows, tear_map, slot_desc, seed=SEED):
    """(rater, key): the blind rater copy (RATER_COLS) and the key file (KEY_COLS). Distinct (ent, name, description,
    majority attr) rows are shuffled with `seed` before the `row` ids are given. slot_desc: {"domain-slot":
    schema description}; a slot that is not in schema.json gets an empty description."""
    keys = rows.groupby(RN.JOIN_KEYS, sort=True).agg(variants=("variant", lambda s: ";".join(sorted(set(s)))),
                                                      n_variants=("variant", "nunique"),
                                                      top_values=("top_values", "first")).reset_index()
    keys = keys.sample(frac=1, random_state=seed, ignore_index=True)
    keys.insert(0, "row", range(len(keys)))
    slots = [slot_key(a, tear_map) for a in keys["majority_gold_attr"]]
    rater = pd.DataFrame({"row": keys["row"], "ent": keys["ent"], "group_name": keys["name"],
                          "group_description": keys["description"], "top_values": keys["top_values"],
                          "l2_attr": keys["majority_gold_attr"], "l2_slot": slots,
                          "l2_slot_description": [slot_desc.get(s, "") for s in slots]})[RATER_COLS]
    return rater, keys[KEY_COLS]
