# T8: small checks (v4.3 results, wf_v4.4 diary)

## 1. The 9th table

`MAX_TABLES = 8` caps the pass-1 table names only (`step4_v43.p1_names`, line 224). The final schema adds one link table for every pair that Llama answers `many_to_many` (`step4_v43.build_answers`, `new_tables.append(...)`, line 310, after the cap). A link table is not a repair and not a key table. Tables per chain (`links` = tables with description "Links X and Y."):

| chain | tables | pass1 | cap_kept | dropped_empty | kept_pass1 | links | over_cap |
|---|---|---|---|---|---|---|---|
| a_dev50_s0 | 3 | 5 | 5 | 2 | 3 |  | False |
| a_dev50_s1 | 8 | 8 | 8 | 0 | 8 |  | False |
| a_dev50_s2 | 8 | 8 | 8 | 0 | 8 |  | False |
| a_dev50b_s0 | 2 | 8 | 8 | 6 | 2 |  | False |
| a_dev50b_s1 | 4 | 8 | 8 | 4 | 4 |  | False |
| a_dev50b_s2 | 3 | 8 | 8 | 5 | 3 |  | False |
| a_llama43_dev50_s0 | 3 | 3 | 3 | 0 | 3 |  | False |
| a_llama43_dev50_s1 | 7 | 8 | 8 | 1 | 7 |  | False |
| a_llama43_dev50_s2 | 9 | 8 | 8 | 1 | 7 | hotel_reference, restaurant_reference | True |
| a_llama43_dev50b_s0 | 4 | 8 | 8 | 4 | 4 |  | False |
| a_llama43_dev50b_s1 | 3 | 3 | 3 | 0 | 3 |  | False |
| a_llama43_dev50b_s2 | 3 | 6 | 6 | 3 | 3 |  | False |
| c1_dev50_s0 | 5 | 8 | 8 | 3 | 5 |  | False |
| c1_dev50_s1 | 3 | 6 | 6 | 3 | 3 |  | False |
| c1_dev50_s2 | 3 | 3 | 3 | 0 | 3 |  | False |
| c1_dev50b_s0 | 3 | 6 | 6 | 3 | 3 |  | False |
| c1_dev50b_s1 | 3 | 3 | 3 | 0 | 3 |  | False |
| c1_dev50b_s2 | 3 | 8 | 8 | 5 | 3 |  | False |

**a_llama43_dev50_s2**: pass 1 gave 8 names (cap 8), 1 table(s) got no column in pass 2 and were dropped (p2_empty_table), leaving 7; the pair questions answered many_to_many twice and added the link tables hotel_reference, restaurant_reference: 7 + 2 = 9.

## 2. GPU minutes per job (batch_seconds / batch_size)

### u0

| stage | jobs | no_seconds | retried | lost | seconds | est_lost_seconds | minutes | mean_job_seconds |
|---|---|---|---|---|---|---|---|---|
| step3 A answers | 18 | 0 | 3 | 3 | 150.7 | 25.1 | 2.93 | 8.37 |
| step3 split | 54 | 0 | 42 | 42 | 81.4 | 22.3 | 1.73 | 1.51 |
| step3 reconcile | 258 | 0 | 0 | 0 | 8.6 | 0.0 | 0.14 | 0.03 |
| step3 dupcheck | 12 | 0 | 1 | 1 | 9.2 | 0.4 | 0.16 | 0.77 |

Total 4.96 min over 342 timed jobs (unknown estimates count 0); batch-once estimate of cost_v43: 4.25 min.

Per set: step3 A answers dev50 1.4 min; step3 A answers dev50b 1.53 min; step3 split dev50 0.76 min; step3 split dev50b 0.97 min; step3 reconcile dev50 0.07 min; step3 reconcile dev50b 0.07 min; step3 dupcheck dev50 0.04 min; step3 dupcheck dev50b 0.12 min

### u2

| stage | jobs | no_seconds | retried | lost | seconds | est_lost_seconds | minutes | mean_job_seconds |
|---|---|---|---|---|---|---|---|---|
| step3 A answers | 0 | 18 | 0 | 0 | 0 | 0.0 | 0.0 |  |
| step3 names | 138 | 0 | 138 | 138 | 108.3 |  | 1.81 | 0.78 |
| step3 split | 54 | 0 | 42 | 42 | 44.1 | 13.4 | 0.96 | 0.82 |
| step3 reconcile | 218 | 0 | 0 | 0 | 7.1 | 0.0 | 0.12 | 0.03 |
| step3 dupcheck | 12 | 0 | 2 | 2 | 18.4 | 2.3 | 0.35 | 1.54 |

Total 3.24 min over 422 timed jobs (unknown estimates count 0); batch-once estimate of cost_v43: 1.72 min.

Per set: step3 A answers dev50 0.0 min; step3 A answers dev50b 0.0 min; step3 names dev50 0.94 min; step3 names dev50b 0.86 min; step3 split dev50 0.51 min; step3 split dev50b 0.44 min; step3 reconcile dev50 0.05 min; step3 reconcile dev50b 0.06 min; step3 dupcheck dev50 0.12 min; step3 dupcheck dev50b 0.23 min

### u4

| stage | jobs | no_seconds | retried | lost | seconds | est_lost_seconds | minutes | mean_job_seconds |
|---|---|---|---|---|---|---|---|---|
| step4 pass 1 (tables) | 18 | 0 | 0 | 0 | 11.7 | 0.0 | 0.2 | 0.65 |
| step4 pass 2 (assign) | 18 | 0 | 0 | 0 | 35.8 | 0.0 | 0.6 | 1.99 |
| step4 pairs (links) | 151 | 0 | 0 | 0 | 15.8 | 0.0 | 0.26 | 0.1 |
| step4 keys | 75 | 0 | 0 | 0 | 7.9 | 0.0 | 0.13 | 0.11 |

Total 1.19 min over 262 timed jobs (unknown estimates count 0); batch-once estimate of cost_v43: 1.19 min.

Per set: step4 pass 1 (tables) dev50 0.1 min; step4 pass 1 (tables) dev50b 0.1 min; step4 pass 2 (assign) dev50 0.3 min; step4 pass 2 (assign) dev50b 0.3 min; step4 pairs (links) dev50 0.2 min; step4 pairs (links) dev50b 0.07 min; step4 keys dev50 0.08 min; step4 keys dev50b 0.05 min

`lost` = retried jobs whose guided share is missing in the v4.3 rows (the kept row is the single unguided retry); `est_lost_seconds` = lost x mean seconds of the stage's other rows, empty = unknown (every job of the stage was retried, so its guided batch time is not in any row). The minutes are therefore a lower bound for the names stage. The v4.4 backend (`log_v44.VllmBackend44`) keeps both calls.

## 3. Model loading time

not logged (file `results/wf_v44/model_load.json`)
