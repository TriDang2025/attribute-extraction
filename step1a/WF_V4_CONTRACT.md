# wf_v4 contract: Step 4 (schema creation)

Diary 5 Nov 2026, tasks 0–16. Branch `wf-v4`, from `wf-v3.9` (9f77ea3). Step 1a (wf_v2.2), Step 3 (wf_v3.9, `STEP3.md`) and rules v1.3 stay frozen. The GT is for scoring only, except in the upper-bound inputs c1 and c2.

## Inputs
- **Step-3 handover:** `handover/{dev50,dev50b}/{train,hotel,restaurant}.json` (format in `handover/HANDOVER_FORMAT.md`).
- **Mentions:** `results/graph_v22_{set}/spans/mentions.csv`, loaded with `s1a/mentions.load`. The columns `mention_id`, `dialogue_id` and `instance_id` (one predicted entity segment) carry `norm_value`.
- **GT per mention:** `gt_levels.csv`, column `gt_L2`, with values that are GT attribute names such as "Train leave at".
  - dev50: `results/loop1_v35/gt_levels.csv`
  - dev50b: `results/loop1_v37/dev50b/gt/gt_levels.csv`
- **Schema GT v1:** `gt/schema_gt_v1.yaml`, made by the user. **Do not change its design.**

## Ids
- A Step-3 column id is `"<entity>:<id>"`, for example `"train:4"`, where `<id>` is `columns[].id` in the handover file of that set.
- A column the model adds (a new id or link column) has `source: null` and `new: true`.

## Canonical schema JSON
Written by `s1a/step4_sql.py` from the final Step-4 answer and from the (e) answer. Also written for the GT, the flat baseline (d) and the signals-only schema (f). Read by `s1a/step4_score.py`.

```json
{"tables": [{"name": "train", "description": "...", "row": "one train",
   "columns": [{"name": "train id", "type": "id", "source": "train:7", "new": false, "gt": null}],
   "primary_key": ["train id"],
   "foreign_keys": [{"columns": ["train id"], "ref_table": "train", "ref_columns": ["train id"]}]}],
 "relationships": [{"from": "train_booking", "to": "train", "kind": "one_to_many", "reason": "..."}],
 "unused": [{"source": "train:9", "reason": "..."}],
 "duplicate_flags": [{"source": "train:3", "duplicate_of": "train:4"}]}
```

- **`gt`:** an optional direct GT column name. When it is set, the scorer uses it instead of mapping `source` (used for the GT itself, c1/c2 and the rated (e) columns).
- **`relationships`:** "from" is the table that refers (many side), "to" is the table it refers to. `kind` is `one_to_many` or `many_to_many`.
- **Types:** one of `text, integer, decimal, time, day, date, boolean, id, duration, price`.

## Output folders
`results/wf_v4/{gt,signals,inputs,colab,scores,grading}/`
