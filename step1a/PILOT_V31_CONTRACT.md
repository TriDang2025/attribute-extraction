# wf_v3.1 Step-3 pilot contract (shared by workers W1–W4)

Goal: rerun the Step-3 LLM pilot on 3 predicted entities with a new prompt (v2), better merge hints, a split pass
and stricter scoring. Step 1a stays frozen: run `results/graph_v22_dev50` (spans). wf_v3 code (`LOOP1_CONTRACT.md`)
keeps working; the old `full/nocontext/nohints` prompts and their scores must not change.

## Entities
Pilot entities are found with `pilot_input.find_pilot_entity(mentions, gold)` for gold in `train`, `hotel`,
`restaurant` (dev: E1, E0, E2). The entity tag in file names is the gold name (`train`, `hotel`, `restaurant`).
Gold entities scored per pilot entity: train → [train]; hotel → [hotel]; restaurant → [restaurant, taxi]
(the taxi slots live under the restaurant entity, T3 "wrong entity").

## Folder (`results/loop1_v31/`)
```
prompts/<ent>_<variant>.txt          prompt text
prompts/<ent>_<variant>.schema.json  JSON schema for guided decoding of that prompt
prompts/<ent>_split_<cid>.txt / .schema.json   split-pass prompts (cid with "#" written as "-", e.g. E1-1)
examples.csv                         ex_id, entity, cluster_id, mention_id, variant  (all ex ids used in any prompt)
manifest.json                        list of jobs (below)
prompt_stats.md                      chars, est. tokens, status per prompt
hints.csv                            entity, mode, cluster_id, other, rank, cosine_pct, same_class (offline check)
responses/<ent>_<variant>_<tag>.jsonl   one cache row per job (llm_cache format)
```
Manifest job: `{"job": "<ent>_<variant>_<tag>", "entity": "E1", "ent": "train", "variant": "v2", "run_tag": "r1",
"kind": "entity" | "split", "cluster_id": "" | "E1#1", "prompt": "prompts/...txt", "schema": "prompts/...schema.json",
"max_tokens": int, "format": "v1" | "v2" | "split"}`.

## Variants (kind "entity")
| variant | format | instruction | examples | hints | entities |
|---|---|---|---|---|---|
| nohints | v1 | wf_v3 `INSTRUCTION` unchanged | 8, context | none | all 3 |
| nohints_long | v1 | wf_v3 `INSTRUCTION` | 16, context | none | train only (length control: about the old full prompt's length) |
| v2 | v2 | `INSTRUCTION_V2` | 8, context | none | all 3 |
| v2 (tag r2) | v2 | `INSTRUCTION_V2` | 8, context | none | all 3, cluster order shuffled with seed 1 (r1 keeps id order) |
| v2_hints | v2 | `INSTRUCTION_V2` | 8, context | filtered window hints (one line per cluster, only if any pass) | all 3 |
| v2_nocontext | v2 | `INSTRUCTION_V2` | 8, value only | none | all 3 |

If an estimated prompt is >= 28000 tokens, lower k for that prompt (8 → 6 → 5) and record k in prompt_stats.md.
Placement options and the "Other entities" block are the same as wf_v3 (`option_texts`, `_render_options`).

## Output format v1 (wf_v3, with enums)
Same objects as `llm_cache._ITEM_SCHEMA`, but the per-prompt schema makes `cluster_id` an enum of the entity's
cluster ids, `merge_with` items an enum of those ids, `placement` an enum of the option texts.

## Output format v2 (STAIR idea: write the attribute list first, then assign each cluster)
```json
{"attributes": [{"name": "destination", "description": "where the trip ends", "role": "end point of the trip"}],
 "clusters": [{"cluster_id": "E1#0", "attribute": "destination", "evidence": "I am going to [[Stansted Airport]]",
               "mixed": false, "placement": "current entity E1"}]}
```
- `attributes`: the entity's distinct attributes, each once; names snake_case and role-specific
  (`departure_station` vs `destination_station`, `leave_time` vs `arrive_by_time`).
- `clusters`: one per cluster id (enum). `attribute` is one listed name, or `"not_attribute"` (noise: chit-chat,
  yes/no/ok, booking words, other values that are not database values). Several clusters may share an attribute
  = merge. `mixed` true = the cluster holds 2+ attributes (a split candidate). `placement` enum as v1.
- Schema: `attribute` stays a string (the list is model-written); post-validation maps an unknown name to
  `"unsure"`.
- Adapter (W3) to the v1 decision table: clusters sharing an attribute → action `merge` with `merge_with` the
  others; single → `keep`; `not_attribute` → `not_attribute`; unknown → `unsure`; name/description from the list.
  `mixed` true with a split-pass result `is_mixed` true → action `split` with that result's parts.

## Split pass (kind "split", format "split")
Candidates (W1, `split_candidates(export, entity)`): clusters with >= 8 mentions where >= 15% of the cluster's
instances hold 2+ distinct norm values of that cluster. Every candidate gets one prompt with up to 16 examples
(ex ids `<cid>:s<j>`), asking whether the cluster mixes roles. Output:
`{"cluster_id": "E1#1", "is_mixed": true, "parts": [{"name": "leave_time", "role": "...", "examples": ["E1#1:s0"]}]}`
with `examples` items an enum of that prompt's ex ids. Run for every candidate (not only when v2 said `mixed`);
scoring uses it for v2 variants.

## Hints (W2, `s1a/hints.py`)
`merge_hints(export, entity, mode, window_x=None, k=3) -> {cluster_id: [dict(other, rank, cos, pct)]}`
- `string`: centroids of `export.x` (wf_v3 behaviour, must equal `pilot_score.merge_hints` order).
- `window`: centroids of `window_x` (bge-m3 vectors of each mention's `context` column, same row order as
  `export.ids`), cached at `results/graph_v22_dev50/spans/window_vectors.npz` (ids, x).
- `filtered`: window mode, then drop hub clusters (in more than 2x the mean number of top-k lists) and keep only
  pairs with pct >= 80.
`hint_precision(hints, mentions) -> (n, n_same_class)`: same class = both clusters have a majority gold_attr and
it is equal.

## Scoring (W3)
- Entity-agnostic: gold classes = gold attrs of the entity's gold names; split targets = clusters with >= 8
  mentions and a second gold class >= 0.25 (no train-only kinds).
- `name_merge(dec, mentions)`: an extra "+namemerge" row per response: same normalized name (lowercase, `_`/space
  equal) and same placement in one entity, never in one instance → merged.
- Name rubric sheet `name_rubric.csv`: variant, run_tag, entity, attr_id, name, description, majority_gold_attr,
  top_values, label (gold/valid_new/noise), category (exact/synonym/too_general/wrong_role/wrong/noise_named/
  noise_marked), rater1, rater2, final. Rule in `NAMING_RULE.md`. Name accuracy = exact+synonym, reported
  separately on real (gold, valid_new) and noise clusters. Role accuracy: over attrs whose majority gold attr is
  one of a role pair (departure/destination, leave at/arrive by, in any gold entity).
- GLiNER check label = `name.replace("_", " ")` plus, when given, a second run with the description; report both.

## Tests
Toy tables only. No bge-m3, GLiNER or LLM on real data in tests; workers do not run real data and do not commit.
