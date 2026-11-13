# wf_v4.3 U4: Step 4 v4.3 (Llama-3.1-8B, small closed questions)

Scores with the T7 scorers (full GT, not reachable-only; `scores.csv` has both). Counts are summed over the finished chains of each row, F1 values are means over them. Chains finished = chains whose p1 and p2 answers parsed and whose assembled schema passed the Step 4 validators.

| input | set | chains finished | table F1 | grouping F1 | GT columns placed | PK right (a) | PK right (b) | relationship recall | relationship precision | tables per chain | repairs per chain |
|---|---|---|---|---|---|---|---|---|---|---|---|
| a | dev50 | 3/3 (1.000) | 0.523 | 0.660 | 63/156 (0.404) | 4/9 (0.444) | 8/9 (0.889) | 0/3 (0.000) | 0/2 (0.000) | 3-8 | 3.3 (1-5) |
| a | dev50b | 3/3 (1.000) | 0.598 | 0.556 | 99/156 (0.635) | 1/8 (0.125) | 8/8 (1.000) | 0/3 (0.000) | n/a | 2-4 | 10.7 (8-13) |
| c1 | dev50 | 3/3 (1.000) | 0.756 | 0.779 | 100/156 (0.641) | 4/11 (0.364) | 11/11 (1.000) | 0/3 (0.000) | n/a | 3-5 | 2.3 (0-4) |
| c1 | dev50b | 3/3 (1.000) | 0.750 | 1.000 | 99/150 (0.660) | 0/9 (0.000) | 9/9 (1.000) | n/a | n/a | 3-3 | 2.7 (0-5) |
| a_llama43 | dev50 | 3/3 (1.000) | 0.594 | 0.621 | 81/152 (0.533) | 4/10 (0.400) | 10/10 (1.000) | 0/1 (0.000) | 0/9 (0.000) | 3-9 | 7.7 (3-11) |
| a_llama43 | dev50b | 3/3 (1.000) | 0.722 | 0.948 | 79/150 (0.527) | 0/9 (0.000) | 9/9 (1.000) | n/a | n/a | 3-4 | 3.3 (0-5) |
| a | all | 6/6 (1.000) | 0.561 | 0.608 | 162/312 (0.519) | 5/17 (0.294) | 16/17 (0.941) | 0/6 (0.000) | 0/2 (0.000) | 2-8 | 7.0 (1-13) |
| c1 | all | 6/6 (1.000) | 0.753 | 0.890 | 199/306 (0.650) | 4/20 (0.200) | 20/20 (1.000) | 0/3 (0.000) | n/a | 3-5 | 2.5 (0-5) |
| a_llama43 | all | 6/6 (1.000) | 0.658 | 0.784 | 160/302 (0.530) | 4/19 (0.211) | 19/19 (1.000) | 0/1 (0.000) | 0/9 (0.000) | 3-9 | 5.5 (0-11) |

Chains not finished: 0

Repairs (all chains): 90

| type | count |
|---|---|
| p2_empty_table | 40 |
| key_name_renamed | 29 |
| col_name_dup | 21 |

Calls (log_v43.call_totals):
- 262 calls (14.6 per chain), prompt tokens 616829 (max per call 9995), output tokens 11246, finish {'stop': 262}, retried 0
- calls per chain: 5-38
