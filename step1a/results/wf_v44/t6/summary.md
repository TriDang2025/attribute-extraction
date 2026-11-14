# wf_v4.4 Step 4 (Llama-3.1-8B)

Scores with the v4.3 scorers (full GT; `scores.csv` has reachable-only too). Counts are summed over the finished chains of a row, F1 values are means. `vote` = the voted schema (one chain per input and set), `single` = the seed chains. GT columns in rest = GT columns held only in a "rest" column.

| input | set | schema | chains finished | table F1 | grouping F1 | GT columns placed | GT columns in rest | PK right (a) | PK right (b) | relationship recall | relationship precision | tables per chain | repairs per chain |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c1 | dev50 | vote | 1/1 | 0.600 | 0.716 | 34/52 (0.654) | 3/52 (0.058) | 1/3 (0.333) | 1/3 (0.333) | 0/1 (0.000) | n/a | 4-4 | 0.0 (0-0) |
| c1 | dev50 | single | 3/3 | 0.640 | 0.812 | 93/152 (0.612) | 14/152 (0.092) | 1/8 (0.125) | 4/8 (0.500) | 0/1 (0.000) | n/a | 2-4 | 5.0 (4-6) |
| c1 | dev50b | vote | 1/1 | 0.500 | 0.663 | 30/50 (0.600) | 5/50 (0.100) | 1/2 (0.500) | 1/2 (0.500) | n/a | n/a | 3-3 | 0.0 (0-0) |
| c1 | dev50b | single | 3/3 | 0.611 | 0.692 | 92/150 (0.613) | 13/150 (0.087) | 2/8 (0.250) | 5/8 (0.625) | n/a | n/a | 3-4 | 4.7 (4-5) |
| c1 | all | vote | 2/2 | 0.550 | 0.690 | 64/102 (0.627) | 8/102 (0.078) | 2/5 (0.400) | 2/5 (0.400) | 0/1 (0.000) | n/a | 3-4 | 0.0 (0-0) |
| c1 | all | single | 6/6 | 0.626 | 0.752 | 185/302 (0.613) | 27/302 (0.089) | 3/16 (0.188) | 9/16 (0.562) | 0/1 (0.000) | n/a | 2-4 | 4.8 (4-6) |

Chains not finished: 0

Repairs (all chains): 29

| type | count |
|---|---|
| p1_entity_name | 18 |
| p2_empty_table | 10 |
| key_name_renamed | 1 |

| input | set | chains | calls | calls per chain | prompt tokens | output tokens | retried |
|---|---|---|---|---|---|---|---|
| c1 | dev50 | 4 | 16 | 4.0 | 50063 | 1361 | 0 |
| c1 | dev50b | 4 | 17 | 4.2 | 51551 | 1358 | 0 |
