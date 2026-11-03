# wf_v3.8 Colab batch contract (diary 2 Nov, tasks 7–9)

Model and settings as v3.7: Qwen2.5-32B-Instruct-AWQ, temperature 0, guided JSON per job schema, one A100. All prompts are built on the laptop, committed and pushed before the run; the batch has **one stage** (no job reads another job's output), so it runs in one Colab session.

## Input columns
"Column" is as in `s1a/columns_v37.py` (a distinct output attribute name of an unmarked group, per entity) of **A s012 with the split pass**, Step 1a v2.2, on dev50 and dev50b (loaders: `scripts/score_t14_v37.py` `load_old` / `load_new` key `v22d50b`; Phase 1 reproduced 67 and 56 columns). A column's members = the clusters (and split parts) of its groups; its mentions = their mentions. Task 7 also runs on **A s012 nosplit** (`s1a/nosplit_v38.py`, 32 / 35 columns), as one dashboard row.

Deviation from the diary, on purpose: tasks 8–9 run on the columns **before** the task-7 joins, not after, so the batch has one stage. After task 7 the evidence of a joined column is pooled from its members (support = summed yes / summed asked; neighbour fit recomputed with the joined column's own neighbours, from the same answers where the neighbours are unchanged). A duplicate's nearest neighbour is often its twin, which task 11 counts as a duplicate flag.

## Families
1. **dupcheck** (task 7): one job per entity × set × config (3 × 2 × 2 = 12). Prompt: the entity's final columns only, each with an id, name, description (from A's attribute list; "" if none), role (A gives none: "") and 3 example values (most frequent distinct values). Question: which columns are the same attribute with the same role. Schema `{"joins": [{"columns": [id, ...], "reason": str}]}`. A **code check** (applied when scoring, never in the prompt) rejects any join whose names form a role pair using only the method's own names (`s1a/role_guard.py` word sets: start vs end place, earliest vs latest time); it never reads the GT. Every join and every rejected join is listed.
2. **example** (task 8): one job per column (with-split config, both sets). Up to 10 examples of the column, sampled with seed 0, spread over its member clusters (round-robin, largest first), each shown as the turn text with the value marked `[[value]]`. Question per example: "Does the marked value fit the attribute <name> (<description>)?" Schema `{"answers": [{"id": int, "fits": "yes"|"no"}]}`. Support = yes / answered.
3. **neighbour** (task 9): one job per column. Its 2 nearest other columns of the same entity by cosine of bge-m3 centroids (mean of the column's mention vectors from the run's `vectors.npz`), 5 examples from each, sampled as in 2. Same question about **this** column's name. Neighbour fit = yes / answered; also store which neighbour each example came from, and flag the column when a neighbour that fits (>= 3/5) has a role-partner name (role_guard word sets).

max_tokens: dupcheck 1024; example and neighbour 512. Prompts must stay under 30,000 tokens (dupcheck is the largest).

## Outputs
`results/loop1_v38/colab/{prompts/*.txt + *.schema.json, examples.csv (job, example id, mention_id, cluster_id, column, value, source column), columns.csv (set, config, ent, column id, name, description, members, n mentions, n dialogues, distinct values, value types), manifest.json (family dupcheck | example | neighbour; set; config), prompt_stats.md}`, notebook `colab/S1A_llm_v38_colab.ipynb` (copy of v3.7: branch wf-v3.8, folder loop1_v38, families above, response parsers added to `s1a/llm_cache.parse_job`). Scoring (tasks 10–11) comes after the run.
