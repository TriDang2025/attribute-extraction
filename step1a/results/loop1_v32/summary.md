# wf_v3.2 pilot summary

Run `results\graph_v22_dev50`. A = v3.1 v2 r1 + split pass (from `results\loop1_v31`), B = nbhd seed 0, C = nbhd vote over 3 orders, D = C + noise + gate + reconcile; `+namemerge` = same response after merging same-name, same-placement clusters. Per-check blocks in scores_<ent>.md; real_acc / noise_rub / role_acc come from the filled name rubric.

| ent | variant | run | merge_pure | merge_frag | split_done | split_side | noise_marked | noise_kept | place_right | recall_after | p1_after | j_right | j_wrong | j_right_desc | j_wrong_desc | real_acc | noise_rub | role_acc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| train | A | r1 | 0.000 | 0.500 | 0.500 | 0.917 | 0.667 | 0 | 0.895 | 0.571 | 0.676 | 0.248 | 0.219 | 0.321 | 0.249 | 0.941 | 0.667 | 0.857 |
| train | A+namemerge | r1 | 0.000 | 0.500 | 0.500 | 0.917 | 0.667 | 0 | 0.895 | 0.571 | 0.676 | 0.248 | 0.219 | 0.321 | 0.249 | n/a | n/a | n/a |
| train | B | s0 | 0.000 | 0.500 | 0.500 | 0.917 | 0.889 | 0 | 0.895 | 0.429 | 0.720 | 0.233 | 0.209 | 0.340 | 0.288 | 0.824 | 0.889 | 0.750 |
| train | B+namemerge | s0 | 0.000 | 0.500 | 0.500 | 0.917 | 0.889 | 0 | 0.895 | 0.429 | 0.720 | 0.233 | 0.209 | 0.340 | 0.288 | n/a | n/a | n/a |
| train | C | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 0.778 | 0 | 0.895 | 0.429 | 0.720 | 0.233 | 0.162 | 0.340 | 0.173 | 0.765 | 0.583 | 0.750 |
| train | C+namemerge | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 0.778 | 0 | 0.895 | 0.429 | 0.720 | 0.233 | 0.162 | 0.340 | 0.173 | n/a | n/a | n/a |
| train | D | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 0.000 | 1 | 0.895 | 0.286 | 0.596 | 0.295 | 0.273 | 0.291 | 0.515 | 1.000 | 0.000 | 1.000 |
| train | D+namemerge | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 0.000 | 1 | 0.895 | 0.286 | 0.596 | 0.295 | 0.273 | 0.291 | 0.515 | n/a | n/a | n/a |
| hotel | A | r1 | 1.000 | 1.000 | n/a | n/a | 0.417 | 0 | 1.000 | 0.727 | 0.882 | 0.227 | 0.171 | 0.367 | 0.231 | 0.786 | 0.333 | n/a |
| hotel | A+namemerge | r1 | 1.000 | 1.000 | n/a | n/a | 0.417 | 0 | 1.000 | 0.727 | 0.882 | 0.227 | 0.171 | 0.367 | 0.231 | n/a | n/a | n/a |
| hotel | B | s0 | 1.000 | 0.600 | n/a | n/a | 0.333 | 1 | 1.000 | 0.727 | 0.881 | 0.207 | 0.168 | 0.234 | 0.190 | 0.647 | 0.267 | n/a |
| hotel | B+namemerge | s0 | 1.000 | 0.600 | n/a | n/a | 0.333 | 1 | 1.000 | 0.727 | 0.881 | 0.207 | 0.168 | 0.234 | 0.190 | n/a | n/a | n/a |
| hotel | C | s012 | 1.000 | 0.600 | n/a | n/a | 0.417 | 1 | 1.000 | 0.727 | 0.880 | 0.207 | 0.168 | 0.214 | 0.190 | 0.647 | 0.312 | n/a |
| hotel | C+namemerge | s012 | 1.000 | 0.600 | n/a | n/a | 0.417 | 1 | 1.000 | 0.727 | 0.880 | 0.207 | 0.168 | 0.214 | 0.190 | n/a | n/a | n/a |
| hotel | D | s012 | 1.000 | 0.600 | n/a | n/a | 0.083 | 2 | 1.000 | 0.545 | 0.906 | 0.265 | 0.194 | 0.227 | 0.157 | 0.909 | 0.091 | n/a |
| hotel | D+namemerge | s012 | 1.000 | 0.600 | n/a | n/a | 0.083 | 2 | 1.000 | 0.545 | 0.906 | 0.265 | 0.194 | 0.227 | 0.157 | n/a | n/a | n/a |
| restaurant | A | r1 | 0.000 | 0.987 | n/a | n/a | 0.125 | 1 | 0.964 | 0.500 | 0.734 | 0.270 | 0.156 | 0.304 | 0.212 | 0.826 | 0.200 | 0.000 |
| restaurant | A+namemerge | r1 | 0.000 | 0.987 | n/a | n/a | 0.125 | 1 | 0.964 | 0.500 | 0.734 | 0.270 | 0.156 | 0.304 | 0.212 | n/a | n/a | n/a |
| restaurant | B | s0 | 0.000 | 0.380 | n/a | n/a | 0.125 | 2 | 0.964 | 0.583 | 0.667 | 0.220 | 0.122 | 0.150 | 0.078 | 0.852 | 0.143 | 0.500 |
| restaurant | B+namemerge | s0 | 0.000 | 0.380 | n/a | n/a | 0.125 | 2 | 0.964 | 0.583 | 0.667 | 0.220 | 0.143 | 0.150 | 0.120 | n/a | n/a | n/a |
| restaurant | C | s012 | 0.500 | 0.380 | n/a | n/a | 0.125 | 2 | 0.964 | 0.667 | 0.671 | 0.226 | 0.128 | 0.147 | 0.096 | 0.786 | 0.143 | 0.000 |
| restaurant | C+namemerge | s012 | 0.500 | 0.380 | n/a | n/a | 0.125 | 2 | 0.964 | 0.667 | 0.671 | 0.226 | 0.142 | 0.147 | 0.129 | n/a | n/a | n/a |
| restaurant | D | s012 | 0.500 | 0.380 | n/a | n/a | 0.125 | 1 | 0.964 | 0.417 | 0.630 | 0.191 | 0.209 | 0.196 | 0.224 | 0.941 | 0.200 | 1.000 |
| restaurant | D+namemerge | s012 | 0.500 | 0.380 | n/a | n/a | 0.125 | 1 | 0.964 | 0.417 | 0.630 | 0.191 | 0.209 | 0.196 | 0.224 | n/a | n/a | n/a |

## Tokens

Per entity and variant ("all" = sum). x A = total tokens over those of A; recall = strict recall_after of the +namemerge row; est = some counts estimated (est_tokens of the prompt, len(raw) / 3.5). B = seed-0 entity jobs + all split jobs; C = 3 orders + all splits; D = 3 orders + noise + gate + split jobs of failed gates + reconcile.

| ent | variant | calls | prompt tok | output tok | total | x A | recall | recall per 100K tok | est |
|---|---|---|---|---|---|---|---|---|---|
| train | A | 13 | 20725 | 3083 | 23808 | 1.000 | 0.571 | 2.400 | yes |
| train | B | 14 | 23051 | 3911 | 26962 | 1.132 | 0.429 | 1.590 |  |
| train | C | 18 | 44665 | 9160 | 53825 | 2.261 | 0.429 | 0.796 |  |
| train | D | 77 | 74954 | 11826 | 86780 | 3.645 | 0.286 | 0.329 |  |
| hotel | A | 10 | 18670 | 3664 | 22334 | 1.000 | 0.727 | 3.256 | yes |
| hotel | B | 11 | 19163 | 4952 | 24115 | 1.080 | 0.727 | 3.016 |  |
| hotel | C | 15 | 38331 | 10139 | 48470 | 2.170 | 0.727 | 1.500 |  |
| hotel | D | 78 | 69541 | 12921 | 82462 | 3.692 | 0.545 | 0.661 |  |
| restaurant | A | 11 | 25112 | 5521 | 30633 | 1.000 | 0.500 | 1.632 | yes |
| restaurant | B | 13 | 27468 | 6510 | 33978 | 1.109 | 0.583 | 1.717 |  |
| restaurant | C | 19 | 59578 | 16281 | 75859 | 2.476 | 0.667 | 0.879 |  |
| restaurant | D | 105 | 101932 | 19912 | 121844 | 3.978 | 0.417 | 0.342 |  |
| all | A | 34 | 64507 | 12268 | 76775 | 1.000 | n/a | n/a | yes |
| all | B | 38 | 69682 | 15373 | 85055 | 1.108 | n/a | n/a |  |
| all | C | 52 | 142574 | 35580 | 178154 | 2.320 | n/a | n/a |  |
| all | D | 260 | 246427 | 44659 | 291086 | 3.791 | n/a | n/a |  |

## Stats

### train
- Order agreement (C and D share the 3 orders): agree_mean 0.816, agree_full_share 0.552, ties 3
- D noise and vote stats: agree_mean 0.816, agree_full_share 0.552, ties 3, marked_by_probe 0, by_vote 0, by_generic 0, rescued 8, generic_flagged 3, gate_failed 4, split 4, reconcile_answers 26, reconcile_stale 0, reconcile_merged 13
- D gate: candidates 12, gate-failed 4, split applied 4
### hotel
- Order agreement (C and D share the 3 orders): agree_mean 0.774, agree_full_share 0.484, ties 5
- D noise and vote stats: agree_mean 0.774, agree_full_share 0.484, ties 5, marked_by_probe 0, by_vote 1, by_generic 0, rescued 7, generic_flagged 3, gate_failed 5, split 5, reconcile_answers 27, reconcile_stale 0, reconcile_merged 7
- D gate: candidates 9, gate-failed 5, split applied 5
### restaurant
- Order agreement (C and D share the 3 orders): agree_mean 0.830, agree_full_share 0.667, ties 10
- D noise and vote stats: agree_mean 0.830, agree_full_share 0.667, ties 10, marked_by_probe 2, by_vote 0, by_generic 0, rescued 2, generic_flagged 2, gate_failed 4, split 4, reconcile_answers 25, reconcile_stale 0, reconcile_merged 8
- D gate: candidates 10, gate-failed 4, split applied 4

