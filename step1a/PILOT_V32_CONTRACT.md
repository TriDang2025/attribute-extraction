# wf_v3.2 Step-3 pilot contract (shared by workers W1–W4)

Goal: test the fixes from `report/3_main/studies/step3_llm_pilot_papers.md` as ablation variants on the same 3
pilot entities as wf_v3.1, and record token use for every LLM call.
- Step 1a frozen: run `results/graph_v22_dev50` (spans).
- wf_v3.1 code (`PILOT_V31_CONTRACT.md`) keeps working; `loop1_v31` scores must not change.
- Entities, gold names per entity, examples rendering, placement options, scoring metrics: as in the v3.1 contract.

## Variants (each adds to the previous)
| variant | what | LLM jobs |
|---|---|---|
| A `v2` | wf_v3.1 `v2` r1 + its split pass; read from `results/loop1_v31/responses/`, no new run | – |
| B `nbhd` | neighbourhood prompts (below), format v3, 1 order (seed 0), + v3.1 split pass used as in v3.1 (`require_mixed=False`) | entity × nbhd (s0) |
| C `nbhd_vote3` | B in 3 orders (seeds 0, 1, 2), majority vote per cluster | entity × nbhd × 3 |
| D `full` | C + noise probe + coherence gate (split used only where the gate fails) + top-5 reconcile | C + noise + gate + split + reconcile |

B, C and D share the seed-0 entity jobs; C and D share all three orders (one run, scored several ways).

## Folder `results/loop1_v32/`
```
prompts/<ent>_nbhd<g>_s<seed>.txt / .schema.json   entity jobs (g = 0,1,..; seed = order seed)
prompts/<ent>_noise_<cid>.txt / .schema.json      noise probe, one per cluster (cid "#" -> "-")
prompts/<ent>_gate_<cid>.txt / .schema.json       coherence gate, one per split candidate
prompts/<ent>_split_<cid>.txt / .schema.json      split pass (same text as v3.1 render_split), one per candidate
prompts/<ent>_reconcile_<uid>.txt / .schema.json  stage 2 only, built after stage 1 (uid = unit id, below)
neighbourhoods.csv     ent, entity, nbhd, cluster_id
examples.csv           ex_id, entity, cluster_id, mention_id, variant (as v3.1)
stage2_inputs.json     everything stage 2 needs without the export: per ent {cluster blocks text, split ex ids ->
                       mention ids, cluster -> nbhd}
stage2_vectors.npz     cluster centroids (export.x mean per cluster) and mention vectors of split examples, with ids
manifest.json          jobs (below); stage-2 jobs are appended by `pilot_combine.build_stage2`
prompt_stats.md        chars, est. tokens, exact tokens when known
responses/<job>.jsonl  one llm_cache row per job
```
Manifest job: `{"job", "entity", "ent", "variant": "nbhd|noise|gate|split|reconcile", "run_tag": "s<seed>" or "r1",
"kind": "entity|noise|gate|split|reconcile", "stage": 1|2, "nbhd": int|null, "cluster_id": "", "prompt", "schema",
"max_tokens", "format": "v3|noise|gate|split|reconcile"}`.
Stage 1 = entity, noise, gate, split (all candidates). Stage 2 = reconcile.

## Neighbourhoods (W1)
- Per entity: n clusters → g = ceil(n / 20) groups (train 29 → 2, hotel 31 → 2, restaurant 57 → 3).
- Average-linkage agglomerative clustering on cosine of the cluster centroids (`export.x` mean per cluster), into g
  groups; then rebalance so no group has more than 20 clusters (move the member farthest from its group centroid
  to the nearest group with room). Deterministic; every cluster in exactly one group.
- Outside context: for each group, the 3 clusters from other groups of the same entity nearest to the group
  centroid, one line each: `Elsewhere in this entity (not yours to assign): E2#9: value1, value2, value3`.
- Target: `Aim for about T attributes (between T/2 and 3T/2).` with T = max(1, round(n_group / 3)).
  This ratio is a dev-informed choice; say so in the report.

## Output format v3 (v2 with reason first; W1 schema, W2 parser)
```json
{"attributes": [{"name": "destination_station", "description": "...", "role": "..."}],
 "clusters": [{"cluster_id": "E1#0", "reason": "<= 25 words why", "attribute": "destination_station",
               "evidence": "...", "mixed": false, "placement": "current entity E1"}]}
```
- Same as v2, with `reason` the first property of each cluster object and in `required`. In the JSON schema the
  property order is `cluster_id, reason, attribute, evidence, mixed, placement`.
- `cluster_id` is an enum of that group's ids only.
- The instruction is `INSTRUCTION_V2` plus the reason line and the target line. The v2 text is unchanged otherwise.

## Noise probe (format "noise", stage 1, one per cluster)
- Shows the cluster head plus 6 examples with context, and asks: is this a value a database column would store?
- Output `{"cluster_id": "E1#7", "reason": "...", "verdict": "attribute|noise|unsure", "name": "<snake_case or empty>"}`
  (verdict is an enum; name is the attribute name when the verdict is attribute).
- The prompt says: "If unsure, answer unsure."
- Generic flag (W2, no LLM): a cluster is generic if ≥ 50% of its mentions have a norm_value that also occurs in
  clusters of 2+ other entities of the run.

## Coherence gate (format "gate", stage 1, one per split candidate from `split_candidates(export, entity, min_share=0.0)`)
- The cluster head plus 16 examples. Step 1: summarise in one line what the values are. Step 2: does that summary fit
  all of them as ONE attribute with one role?
- Output `{"cluster_id", "summary", "coherent": true|false}`. The prompt says: "If unsure, answer coherent true."

## Reconcile (format "reconcile", stage 2)
- Units: after the C-vote and the name merge, one unit per final attribute (uid `a<k>`) and one per split part
  of a gate-failed, is_mixed cluster (uid `<cid>-p<j>`).
- A unit's vector is the mean of its clusters' centroids, or of its split-example mention vectors (from
  stage2_vectors.npz).
- Candidates are the 5 nearest other attribute units of the same entity by cosine (fewer if there are not 5).
- Prompt: the unit's name, description and 6 example lines, then the candidates as `name: description`.
- Output `{"unit_id", "reason", "same_as": "<candidate name>|none"}`, with `same_as` an enum of the candidate
  names + "none".
- `same_as` a name means the unit merges into that attribute. "none" means it stays its own attribute. A split
  part with "none" becomes a new attribute.
- Units with 0 candidates get no job.

## Combine rules (W2, `s1a/pilot_combine.py`)
- B, one order:
  - parse each group response (v3), map it to the v2 decision table with `pilot_verify.decisions_from_v2` (per group),
    and concatenate the groups;
  - then run `pilot_score.name_merge` over the whole entity, which joins the same name across groups.
- Vote (C, D): for each cluster, take the normalized attribute name (`pilot_verify.norm_name`, `not_attribute`
  included) in each of the 3 orders. The majority wins; a 3-way tie falls back to seed 0, and the tie count is kept.
  - Agreement = (number of orders that agree with the winner) / 3, reported as a mean and as the share at 3/3.
  - The winner's description and placement come from the lowest seed with that name. `mixed` is a majority too.
- D noise: final `not_attribute` if any of these holds:
  - probe = noise;
  - vote = not_attribute and probe ≠ attribute;
  - generic and probe ≠ attribute. **Dropped 2026-10-29:** the flag marked 8 dev clusters, 5 of them gold
    attributes (days, area, train departure/destination), so it is reported only (`GENERIC_IN_NOISE = False`).
  Otherwise, a vote of not_attribute with probe = attribute becomes the cluster's own attribute: named by the
  probe's `name`. These are counted as "noise rescued".
- D split: a cluster is split only if the gate says `coherent: false` and its split result says `is_mixed`. Its parts
  come from the v3.1-style split result.
- D reconcile: apply `same_as` merges (union-find). The final decision table goes to the unchanged scorer.

## Token stats (W3 table, W4 fields)
- Every response row gets `prompt_tokens` (`len(out.prompt_token_ids)`), `output_tokens`
  (`len(out.outputs[0].token_ids)`) and `batch_seconds` (wall time of the batch it ran in) plus `batch_size`.
- Old rows without these fields: estimate them with `est_tokens(prompt text)` and `len(raw) / 3.5`, flagged
  `estimated`.
- Table per entity and variant: calls, prompt tokens, output tokens, total, ×A, and strict recall per 100K total
  tokens. Variant costs:
  - B = seed-0 entity jobs + all split jobs;
  - C = 3 orders + all splits;
  - D = 3 orders + noise + gate + the split jobs whose gate failed + reconcile.
- Write it to `summary.md` and to `tokens.csv`.

## Tests
Toy tables only. No bge-m3, GLiNER or LLM on real data in tests; workers do not run real data and do not commit.

## Module API (fixed names; W2 writes them, W3 and W4 call them)
`s1a/pilot_combine.py`, plain Python (pandas, numpy, no GPU and no export needed, so it runs on Colab):
- `load_jobs(out_dir) -> list[dict]` reads the manifest; `load_obj(out_dir, job) -> dict | None` returns the parsed
  response (`llm_cache.parse_job`), or None if missing or failed.
- `decisions_b(out_dir, ent, seed=0, split_results=None) -> DataFrame`: the v2 decision table of the group
  responses of one order, concatenated (before the name merge; W3 applies `name_merge`).
- `vote(tables: list[DataFrame]) -> (DataFrame, dict)`: the voted decision table, plus stats {agree_mean,
  agree_full_share, ties}.
- `generic_flags(mentions, run_entities) -> set[cluster_id]`.
- `apply_noise(dec, probe: {cid: obj}, generic: set) -> (DataFrame, dict)`: stats {marked_by_probe, by_vote,
  by_generic, rescued}.
- `apply_gate(dec, gate: {cid: obj}, split_results) -> DataFrame`: the split only where the gate fails.
- `build_stage2(out_dir) -> list[dict]`: from the stage-1 responses plus `stage2_inputs.json` and
  `stage2_vectors.npz`, writes the reconcile prompts and schemas, appends their jobs (stage 2) to manifest.json,
  and returns the new jobs. Deterministic; rerunning it rewrites the same files and adds no duplicate jobs.
- `apply_reconcile(dec, units, answers) -> DataFrame`.
`decisions_d(out_dir, ent) -> (DataFrame, stats)` chains vote → noise → gate → reconcile for the eval.
W1's `pilot_build_v32.py` writes `stage2_inputs.json` and `stage2_vectors.npz` in the shape W2 reads; W1 and W2
agree on it through this contract:
- `stage2_inputs.json`: `{ent: {"entity": "E1", "clusters": {cid: {"head": str, "lines": [6 example lines]}},
  "split_examples": {cid: {ex_id: line}}, "options": [placement texts]}}`;
- `stage2_vectors.npz`: `cluster_ids`, `cluster_x` (centroids, float32), `ex_ids` (`<cid>:s<j>`), `ex_x`.
