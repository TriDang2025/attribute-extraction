# wf_v3.5 Colab batch (prepared 2026-10-31, not run)

Build: `python scripts/pilot_build_v35.py` -> `results/loop1_v35/colab/{prompts/, manifest.json, neighbourhoods.csv, examples.csv, prompt_stats.md}` and `results/loop1_v35/oracle_clusters.csv`. Notebook: `colab/S1A_llm_v35_colab.ipynb` (branch `wf-v3.5`, A100, push with `bash colab/sync.sh push-results "v3.5 batch responses" loop1_v35/colab`). Every job is format v3 (T8: v2) with guided JSON, temperature 0.

## Jobs (28 calls)
| family | jobs | what |
|---|---|---|
| t8 | `restaurant_v2_r2_rerun` | T8: the v3.1 job `restaurant_v2_r2` again. Same prompt (sha256 equals the v3.1 row, LF), same schema, `run_tag` r2, format v2. It had 6 parse errors ("attribute not in the attribute list"). |
| oracle | `train_oracle_nbhd{0,1}_s{0,1,2}` (6) | T14: v3.2 C prompts (no cue rule, no role examples, plain picker) on the cluster table where every two-role cluster is split by gold role (`<cid>.a` first slot of the pair, `<cid>.b` second). Only train has two-role clusters (9: E1#0, 1, 3, 11, 13, 21, 24, 25, 27). Neighbourhoods are recomputed on the new table (train 29 -> 38 clusters, groups 18 + 20). |
| g | `{train,hotel,restaurant}_g_nbhd{g}_s{0,1,2}` (21) | T18-T20 on the v3.2 C prompt, 3 orders: role-aware example picker on (T19), mixed instruction replaced (T18), optional `role_examples` schema field. Groups: train 2, hotel 2, restaurant 3 (as v3.2). |

Mapping back: `oracle_clusters.csv` has `mention_id, entity, orig_cluster_id, oracle_cluster_id, gold_role`. The eval scores the oracle decisions per `oracle_cluster_id` and joins to `orig_cluster_id` through it.

## Estimated calls and tokens (chars / 3.5; output = v3.2 C tokens per cluster x clusters, +40 per two-role cluster in g; T8 output = its earlier answer)
| family | entity | calls | prompt tokens | output tokens |
|---|---|---|---|---|
| t8 | restaurant | 1 | 13917 | 4471 |
| oracle | train | 6 | 34764 | 9855 |
| g | train | 6 | 31389 | 8601 |
| g | hotel | 6 | 30117 | 8481 |
| g | restaurant | 9 | 48699 | 14535 |
| total | | 28 | 158886 | 45943 |

Largest prompt: 8132 est. tokens (restaurant g group 0), far under the 30000 stop in the notebook. Exact counts come from the notebook's cell 5 and the per-row `prompt_tokens`. Run time is not estimated.

## The three changes in code
- **T18** `pilot_input.INSTRUCTION_V35G` (the v3 text with the "mixed" sentence replaced by one that asks for `role_examples`: attribute name + example ids per role), flag `render_v3(role_examples=True)` and `schema_v3(role_examples=True)`. The schema field is optional (not in `required`); its example ids are an enum of the examples shown. Defaults leave the v3.2 prompts and schemas untouched: tested, and all 21 v3.2 C prompts and schemas are reproduced byte for byte by the default path (checked once on the real data, LF text).
- **T19** the g builder passes `roles` (left words) to `build_input`, which turns on the existing `CUE_ROLES` picker. `prompt_stats.md` lists, for each two-role cluster, how many shown examples have each gold role: all 18 role slots show at least 1 (shown versus mentions, for example E1#1 leave at 5/56). The check uses gold roles only to report; gold never enters a prompt.
- **T20** `pilot_input.render_reconcile_v35` (candidate and unit with description and role, plus the rule "never merge across a role pair: departure/destination, leave at/arrive by, location/address") and `s1a/role_guard.py` (`forbidden_merge`, `filter_reconcile_answers`: sets a forbidden `same_as` to "none" before `pilot_combine.apply_reconcile`). No reconcile job is in this batch: reconcile prompts depend on stage-1 answers and on the v3.2 noise and gate jobs. To build them later: `pilot_combine.build_stage2(out_dir, render=functools.partial(...render_reconcile_v35, roles=...))`, with `roles` {norm_name: role} read from the entity answers' `attributes[].role`; then `filter_reconcile_answers` on the answers.
