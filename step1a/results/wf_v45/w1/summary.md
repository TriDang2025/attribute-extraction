# wf_v4.4 Step 4 (Llama-3.1-8B)

Scores with the v4.3 scorers (full GT; `scores.csv` has reachable-only too). Counts are summed over the finished chains of a row, F1 values are means. `vote` = the voted schema (one chain per input and set), `single` = the seed chains. GT columns in rest = GT columns held only in a "rest" column.

| input | set | schema | chains finished | table F1 | grouping F1 | GT columns placed | GT columns in rest | PK right (a) | PK right (b) | relationship recall | relationship precision | tables per chain | repairs per chain |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a_llama44 | dev50 | vote | 1/1 | 0.667 | 0.971 | 24/50 (0.480) | 0/50 (0.000) | 0/3 (0.000) | 1/3 (0.333) | n/a | n/a | 4-4 | 0.0 (0-0) |
| a_llama44 | dev50 | single | 3/3 | 0.644 | 0.839 | 74/150 (0.493) | 0/150 (0.000) | 0/9 (0.000) | 3/9 (0.333) | n/a | 0/3 (0.000) | 4-5 | 5.0 (4-7) |
| a_llama44 | dev50b | vote | 1/1 | 0.750 | 0.712 | 34/50 (0.680) | 0/50 (0.000) | 0/3 (0.000) | 0/3 (0.000) | n/a | n/a | 3-3 | 1.0 (1-1) |
| a_llama44 | dev50b | single | 3/3 | 0.672 | 0.675 | 99/152 (0.651) | 0/152 (0.000) | 1/9 (0.111) | 2/9 (0.222) | 0/1 (0.000) | n/a | 3-5 | 7.0 (3-12) |
| a_llama44 | all | vote | 2/2 | 0.708 | 0.842 | 58/100 (0.580) | 0/100 (0.000) | 0/6 (0.000) | 1/6 (0.167) | n/a | n/a | 3-4 | 0.5 (0-1) |
| a_llama44 | all | single | 6/6 | 0.658 | 0.757 | 173/302 (0.573) | 0/302 (0.000) | 1/18 (0.056) | 5/18 (0.278) | 0/1 (0.000) | 0/3 (0.000) | 3-5 | 6.0 (3-12) |
| c1 | dev50 | vote | 1/1 | 0.667 | 0.654 | 33/50 (0.660) | 0/50 (0.000) | 1/3 (0.333) | 1/3 (0.333) | n/a | n/a | 4-4 | 0.0 (0-0) |
| c1 | dev50 | single | 3/3 | 0.613 | 0.686 | 98/150 (0.653) | 0/150 (0.000) | 2/8 (0.250) | 5/8 (0.625) | n/a | n/a | 2-5 | 4.3 (3-6) |
| c1 | dev50b | vote | 1/1 | 0.750 | 0.873 | 33/50 (0.660) | 0/50 (0.000) | 1/3 (0.333) | 1/3 (0.333) | n/a | n/a | 3-3 | 0.0 (0-0) |
| c1 | dev50b | single | 3/3 | 0.690 | 0.801 | 99/150 (0.660) | 0/150 (0.000) | 2/8 (0.250) | 2/8 (0.250) | n/a | n/a | 2-3 | 5.3 (5-6) |
| c1 | all | vote | 2/2 | 0.708 | 0.764 | 66/100 (0.660) | 0/100 (0.000) | 2/6 (0.333) | 2/6 (0.333) | n/a | n/a | 3-4 | 0.0 (0-0) |
| c1 | all | single | 6/6 | 0.652 | 0.743 | 197/300 (0.657) | 0/300 (0.000) | 4/16 (0.250) | 7/16 (0.438) | n/a | n/a | 2-5 | 4.8 (3-6) |

Chains not finished: 0

Repairs (all chains): 66

| type | count |
|---|---|
| p1_entity_name | 33 |
| p2_empty_table | 20 |
| col_name_dup | 11 |
| key_name_renamed | 2 |

| input | set | chains | calls | calls per chain | prompt tokens | output tokens | retried |
|---|---|---|---|---|---|---|---|
| a_llama44 | dev50 | 4 | 22 | 5.5 | 72766 | 1868 | 0 |
| a_llama44 | dev50b | 4 | 17 | 4.2 | 65240 | 1770 | 0 |
| c1 | dev50 | 4 | 18 | 4.5 | 51822 | 1428 | 0 |
| c1 | dev50b | 4 | 17 | 4.2 | 53039 | 1388 | 0 |
