# U5: assembler repairs in the old Llama chains (wf_v4.2 option B extended, results/wf_v42/t2c_step4_keyed_ext)

Counts are replayed from the cached answers with `s1a/repairs_v43.py` (the typed replay gives the same answers and the same repair totals as `batch_v4.replay` for all 12 chains; the 4.2 renames are counted separately, `batch_v4` does not count them). Types: 4.1 col_*, 4.2 name_renamed, 4.3 new_table_invalid / rel_*, 4.4 key_listed / dup_listed / col_missing / fk_col_added / fk_ref_to_pk; events (not text repairs): unguided_retry, unguided_job, cut_off. Chains of input c1 = all GT columns, input a = Qwen's Step 3 handover.

## Repairs per chain

| chain | ok | name_renamed | new_table_invalid | rel_unknown_table | rel_self | rel_repeat | key_listed | col_missing | fk_col_added | fk_ref_to_pk | unguided_retry | unguided_job | cut_off | total_repairs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c1_dev50_s0 | True | 0 | 6 | 10 | 0 | 0 | 4 | 10 | 0 | 0 | 0 | 0 | 0 | 30 |
| c1_dev50_s1 | True | 0 | 3 | 6 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| c1_dev50_s2 | True | 0 | 3 | 6 | 0 | 0 | 3 | 37 | 0 | 0 | 0 | 0 | 0 | 49 |
| c1_dev50b_s0 | True | 0 | 0 | 0 | 12 | 0 | 4 | 33 | 0 | 0 | 0 | 0 | 0 | 49 |
| c1_dev50b_s1 | True | 0 | 3 | 6 | 0 | 0 | 3 | 33 | 0 | 0 | 0 | 0 | 0 | 45 |
| c1_dev50b_s2 | True | 0 | 3 | 5 | 1 | 0 | 3 | 37 | 0 | 0 | 0 | 0 | 0 | 49 |
| a_dev50_s0 | False | 0 | 0 | 0 | 0 | 9 | 12 | 55 | 14 | 0 | 0 | 0 | 0 | 90 |
| a_dev50_s1 | False | 3 | 6 | 34 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 1 | 43 |
| a_dev50_s2 | False | 0 | 0 | 0 | 0 | 4 | 5 | 55 | 0 | 26 | 0 | 0 | 0 | 90 |
| a_dev50b_s0 | False | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| a_dev50b_s1 | False | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |
| a_dev50b_s2 | False | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 3 |
| ALL_c1 | 6/6 | 0 | 18 | 33 | 13 | 0 | 20 | 150 | 0 | 0 | 0 | 0 | 0 | 234 |
| ALL_a | 0/6 | 7 | 6 | 34 | 0 | 13 | 17 | 110 | 14 | 26 | 5 | 1 | 4 | 227 |

`ok` False = the chain stopped (a/dev50 s0 and s2: 4.4 still fails a validator after the repairs; a/dev50 s1: 4.4 cut off, parse error; a/dev50b: 4.3 cut off). For a stopped chain the counts cover the calls up to the one that stopped it.

## Do the repairs change the scores? (input c1, 6 chains)

Baseline check: replaying with nothing switched off gives the scores of `final/scores.csv` for 12/12 rows (both GT views x 6 chains), same scorer (`scripts/score_v4.py`).

Two ways to leave a repair out: **validators on** (the unrepaired answer must pass the frozen validators, as in the real run) and **validators ignored** (the answer goes to the assembler and the scorer as it is; a failing assembly is `assemble anyway` = no). The 4.4 repair kinds cannot be switched off one by one (one function), so they are switched off together as `all_44`. Means are over the chains the repair applies to, full GT, change vs the old score:

| off | chains | pass validators | assemble anyway | mean d_table_f1 | mean d_placement | mean d_gt_columns_placed | mean d_grouping_f1 | mean d_pk_right |
|---|---|---|---|---|---|---|---|---|
| all_44 | 6 | 0 | 6 | -0.486 | 0.122 | -0.481 | 0.187 | -0.167 |
| new_table_invalid | 5 | 0 | 5 | -0.1 | 0.0 | -0.092 | 0.0 | 0.0 |
| rel_unknown_table | 5 | 0 | 5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| all_44+new_table_invalid+rel_unknown_table | 4 | 0 | 4 | -0.375 | 0.122 | -0.382 | 0.187 | -0.167 |
| rel_self | 2 | 0 | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| all_44+rel_self | 1 | 0 | 1 | -0.667 |  | -0.66 |  |  |
| all_44+new_table_invalid+rel_self+rel_unknown_table | 1 | 0 | 1 | -0.75 |  | -0.7 |  |  |

Reading: with the validators on, 0 of the c1 chains pass without the 4.4 repairs (0/6) or without the 4.3 repairs (0/5 for rel_unknown_table): the frozen validators reject the raw answers (unknown tables in 4.3; columns missing or a key also listed as a column in 4.4), so the repairs decide whether a chain is scored at all. With the validators ignored: dropping 4.3 relationships (rel_*) changes no score; keeping the invalid new tables (new_table_invalid) changes table F1 by -0.1 on average (one chain, c1_dev50b_s1); not repairing 4.4 (mostly col_missing: 150 columns put back) lowers table F1 by -0.486 and the share of GT columns placed by -0.481, because tables without their columns no longer match the GT tables. The placement score (right place among placed columns) goes up by 0.122 only because fewer columns are placed, so it is not a gain. Conclusion: yes, the 4.4 repairs (col_missing above all) carry the old c1 scores; the 4.3 drops are harmless. Detail with both GT views and more metrics: `ablation_old.csv`.
## Three example repairs

- **c1_dev50_s0, rel_unknown_table (step 4.3)**
  - raw answer: `{ "relationships": [ {"from": "train_booking", "to": "train", "kind": "one_to_many", "reason": "A train is booked many times."}, {"from": "train_booking", "to": `
  - code: relationship 'train_booking' -> 'train' names a table that no 4.2 group produced; repair_43 dropped it

- **c1_dev50_s0, col_missing (step 4.4)**
  - raw answer: `{ "tables": { "train_booking": { "primary_key": "new", "new_id_name": "train_booking id", "columns": [ {"column": "new:train_booking id", "na`
  - code: table 'train_booking' lacks columns of its 4.1 group in the answer; repair_44 added ['gt:21', 'gt:22', 'gt:23', 'gt:24', 'gt:35', 'gt:36', 'gt:37'] (names from the input, types from the value type)

- **a_dev50_s1, name_renamed (step 4.2)**
  - raw answer: `"description": "the type of food served by the restaurant", "row": "one food type" }, "G40": { "name": "postcode", "description": "the postcode of the restaurant", "row": "one postcode" }, "G41": { "nam`
  - code: two groups got the table name 'postcode'; keyed_v42._unique_names kept the first and renamed the second to ['postcode_g40']


## v4.3 side by side (old = all 12 chains above, new = results/wf_v43/u4/**/repairs.json)

| type | step | old | new |
|---|---|---|---|
| name_renamed | 4.2 | 7 | 0 |
| new_table_invalid | 4.3 | 24 | 0 |
| rel_unknown_table | 4.3 | 67 | 0 |
| rel_self | 4.3 | 13 | 0 |
| rel_repeat | 4.3 | 13 | 0 |
| key_listed | 4.4 | 37 | 0 |
| col_missing | 4.4 | 260 | 0 |
| fk_col_added | 4.4 | 14 | 0 |
| fk_ref_to_pk | 4.4 | 26 | 0 |
| unguided_retry | event | 5 | 0 |
| unguided_job | event | 1 | 0 |
| cut_off | event | 4 | 0 |
| col_name_dup | ? | 0 | 42 |
| key_name_renamed | ? | 0 | 58 |
| p2_empty_table | ? | 0 | 80 |
| total |  | 471 | 180 |

