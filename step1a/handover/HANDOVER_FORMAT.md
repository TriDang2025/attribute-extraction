# Step 1a to Step 3 handover (wf_v3.9 final setting)

Files: `handover/{dev50,dev50b}/{train,hotel,restaurant}.json`, written by `scripts/final_v39.py` (pure helpers `s1a/handover_v39.py`, test `tests/test_handover_v39.py`). One file per entity of one set. The setting: A s012 (3-order vote) + split pass + reconcile joins both candidate orders agree on + duplicate-check joins both reconcile orders unite (role-pair block applies) + evidence cards as flags only (no column is removed by a verdict). The GT is never in these files.

## File
| field | type | meaning |
|---|---|---|
| set, entity | str | `dev50` / `dev50b`; `train` / `hotel` / `restaurant` |
| stage1_entity | str | the stage-1 entity id of the run (`E1`, ...) |
| setting | str | the setting above |
| clusters | [str] | every cluster id of the entity |
| columns | [column] | the final columns |
| dropped | [dropped] | clusters A s012 marked, not columns |
| counts | dict | columns, mentions_in_columns, dropped_clusters, dropped_mentions |

## column
| field | type | meaning |
|---|---|---|
| id, name, description, role | int, str, str, str | name = the biggest member's; description = the A attribute description, else the split-pass role of a part; role = the A attribute's role (first order that gave one), else the split-pass role of a part; "" if none |
| value_type | {dominant, share, counts} | `value_types.value_type_v35` of the mention texts |
| n_mentions, n_dialogues | int | |
| mention_ids | [int] | each mention id is in at most one column or dropped cluster of the entity |
| top_values | [str] | the 3 most frequent normalised values |
| placement | str | the most common A placement of the member clusters |
| members | [{cluster, group, part, mentions}] | member clusters; `part` is the split-part id (`E1#3/0`) when the member is a part of a split cluster, else null; a split cluster can sit in several columns, each through its parts |
| origin | {groups, from_columns, reconcile_parts_moved_in, duplicate_check_joined} | how the column came about (group ids, v3.8 batch columns it was made of, parts joined by reconcile, columns united by the duplicate check) |
| evidence | {support, neighbour_fit, neighbours, mixed_roles, null_reason, pooled, from_columns} | the v3.8 card (answers of the Qwen example and neighbour checks). `support` / `neighbour_fit` = {yes, n, share} or null (see `null_reason`: no example answers, no neighbour answers, no mention). `pooled` = true when the column is not exactly one v3.8 batch column: the answers of the columns it was made of (`from_columns`) are summed, and the neighbours are the two nearest final columns (an answer count n = 0 means no job asked about that neighbour) |
| verdict | str | verdict rule v0: real, unsure, noise, too general, mixed roles |
| flags | {noise, too_general, mixed_roles, keep_apart} | verdict flags (information only); keep_apart = [{a, b, cos}] keep-apart pairs (`results/loop1_v39/p2/keep_apart.csv`) with both clusters in this column |

## dropped
`{cluster, action, reason, wrong_entity_placement, name, evidence, placement, n_mentions, mention_ids}`: clusters A s012 marked `not_attribute`, `unsure` or `attribute_cue`. `wrong_entity_placement` is true when the model's own placement names another entity (information only, from the model, not the GT). Every cluster of `clusters` is in at least one column or dropped, never both.

## Example (shortened)
```json
{"id": 4, "name": "departure time", "description": "the time at which the train departs", "role": "start of the journey",
 "value_type": {"dominant": "time", "share": 1.0, "counts": {"time": 62}}, "n_mentions": 62, "n_dialogues": 23,
 "top_values": ["12:00", "13:15", "15:45"], "placement": "current entity E1",
 "members": [{"cluster": "E1#1", "group": "E1#1/0", "part": "E1#1/0", "mentions": 61},
             {"cluster": "E1#9", "group": "E1#9", "part": null, "mentions": 1}],
 "mention_ids": [3, 7, 40],
 "origin": {"groups": ["E1#1/0", "E1#9"], "from_columns": ["departure time"], "reconcile_parts_moved_in": [], "duplicate_check_joined": []},
 "evidence": {"support": {"yes": 4, "n": 10, "share": 0.4}, "neighbour_fit": {"yes": 2, "n": 8, "share": 0.25},
              "neighbours": [{"columns": ["arrival time"], "yes": 2, "n": 5}], "mixed_roles": false, "null_reason": "",
              "pooled": false, "from_columns": ["departure time"]},
 "verdict": "unsure", "flags": {"noise": false, "too_general": false, "mixed_roles": false, "keep_apart": []}}
```
