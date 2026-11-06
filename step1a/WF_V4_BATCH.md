# wf_v4 Colab batch (Step 4 chains, dialogues-only schemas, placement)

Model and settings as v3.9: Qwen2.5-32B-Instruct-AWQ (pinned revision, resolved once per run), temperature 0, guided JSON per job schema, batch 64, one A100. Contract of the data: `WF_V4_CONTRACT.md`. Code: `s1a/batch_v4.py` (chains, stages, assembly), `s1a/batch_v4_fake.py` (fake model for tests and the dry run), inputs `s1a/step4_inputs.py`.

## Run
1. Laptop: `python scripts/inputs_v4.py` (inputs, token counts, scores of the no-LLM baselines d and f), `python scripts/batch_build_v4.py` (stage 1), optional `python scripts/dry_run_v4.py` (`results/wf_v4/colab/manifest_summary.md`). Commit and push `results/wf_v4/inputs/` and `results/wf_v4/colab/` on branch `wf-v4`.
2. Colab: `colab/S1A_llm_v4_colab.ipynb`, run all cells (A100). Cell 8 loops the stages: `python scripts/batch_stage_v4.py --dir results/wf_v4/colab --stage K` builds stage K from the responses of the earlier stages, the notebook counts exact tokens (stop above 20,000 for first prompts 4.1 and e, 30,000 for any) and runs it. Cell 9 assembles (`scripts/assemble_v4.py`), cell 11 pushes `results/wf_v4/colab` (`colab/sync.sh`).
3. Laptop: pull, `python scripts/assemble_v4.py --score` (adds `final/scores.csv` and `final/placement_vs_gt.csv`).

## Jobs per stage (calls)
| stage | calls | what |
|---|---|---|
| 1 | 31 | 4.1 of 24 main chains (inputs a, b, c1, c2 x dev50, dev50b x column-order seeds 0, 1, 2) + 1 base chain of the placement test (input a, dev50, seed 0, without the held-out columns); 6 (e) calls (v0 set order, v1, v2 shuffled with seeds 1, 2 x 2 sets) |
| 2, 3, 4 | 25 each | 4.2 name, 4.3 relationships, 4.4 keys and types, for every chain whose earlier answers are valid |
| 5 .. 9 | 2 each | one placement call per held-out column (5: hotel:18, restaurant:10, train:7, train:8, train:14) and mode (with / without the signal card) |
| total | 116 | estimates in `results/wf_v4/colab/manifest_summary.md` |

max_tokens (cap `min(job, 32768 - prompt - 64)` in the notebook): 4.1 6000, 4.2 3000, 4.3 3000, 4.4 6000, e 8000, placement 1000. Families (manifest `family` = `format`): `s4_41 .. s4_44`, `s4_e`, `s4_place` (parsed by `llm_cache.parse_job`).

## Files (`results/wf_v4/colab/`)
`prompts/<job>.txt + .schema.json`, `manifest.json` (stage 1), `manifest_stage<k>.json`, `chains.json` (25 chains: id, input, set, seed, excluded columns), `placement.json` (held-out attributes, columns, steps), `responses/<job>.jsonl`, `chain_status_stage<k>.json`, `final/<run>/{canonical.json, schema.sql, operations.json}`, `final/status.json`. Job names: `<input>_<set>_s<seed>_4<step>`, `e_<set>_<version>`, `place_<sig|nosig>_<step>`.

## Rules
- Column order: seed 0 = input order (handover order = by name; GT inputs by entity then name), seeds 1, 2 shuffle inside each entity block; the later steps keep the order of the 4.1 block.
- A chain stops at its first missing, unparsable or invalid answer (`step4_prompts.validate_*`); it is listed in `chain_status_stage<k>.json` and `final/status.json`. Repairs (counted, in the status): 4.1 columns missing from the answer go to `unused`, a column in two groups keeps its first group; 4.3 relationships and new tables that name unknown tables, repeat or relate a table to itself are dropped. 4.4 is never repaired.
- Placement test (diary task 13): `config/wf_v4_placement.json` (to be approved by the user); the GT is used only to map each held-out GT attribute to the dev50 handover columns that found it (`found_by` of `reachable_dev50.csv`). Held out of the base chain: those columns plus `also_hold_out` (never placed). Order of adding = list order, cumulative; two chains (with / without `data signals:` in the column block). Options P1 existing table, P2 relationship attribute, P3 new table, P4 new relationship, P5 own table with an existing table's columns (skipped in the config; no column is moved by `apply_placement`).
- No prompt names a dataset (checked at write time).
