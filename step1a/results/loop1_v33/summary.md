# wf_v3.3 pilot summary

Run `results\graph_v22_dev50`. C = v3.2 C re-scored from `..\..\attribute-extraction-wf-v3.2\step1a\results\loop1_v32`; E = C prompts + attribute_cue + noise rule + role-aware examples + carry-over, 3-order vote, v3.2 gate and split; E1 = E without carry-over; E2 = E without the cue and noise text; F = E on de-lexicalised text, seed 0, no gate/split, no GLiNER. `+namemerge` = same response after merging same-name, same-placement clusters. P4 cue spread is ON for every variant, C included. Noise labels: gold-share rule (non-gold cluster with < 0.5 of its spans gold = noise, else mixed). Rule-noise clusters relabelled by the LLM jury `results\loop1_v33\jury.csv`. place_base = placement score if every placement were `current entity`; place_current = share of rows placed on the current entity; cue = attribute_cue clusters.

| ent | variant | run | merge_pure | merge_frag | split_done | split_side | noise_marked | noise_kept | place_right | recall_after | p1_after | j_right | j_wrong | j_right_desc | j_wrong_desc | real_acc | noise_rub | role_acc | place_base | place_current | cue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| train | C | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 0.857 | 0 | 0.895 | 0.429 | 0.769 | 0.247 | 0.162 | 0.340 | 0.173 | 0.750 | 0.600 | 0.667 | 0.895 | 1.000 | 0 |
| train | C+namemerge | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 0.857 | 0 | 0.895 | 0.429 | 0.769 | 0.247 | 0.162 | 0.340 | 0.173 | n/a | n/a | n/a | 0.895 | 1.000 | 0 |
| train | E | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 1.000 | 0 | 0.895 | 0.429 | 0.697 | 0.198 | 0.236 | 0.233 | 0.307 | 1.000 | 1.000 | 1.000 | 0.895 | 1.000 | 5 |
| train | E1 | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 1.000 | 0 | 0.895 | 0.429 | 0.697 | 0.224 | 0.220 | 0.484 | 0.257 | 0.909 | 1.000 | 0.667 | 0.895 | 1.000 | 4 |
| train | E2 | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 1.000 | 0 | 0.895 | 0.429 | 0.720 | 0.253 | 0.290 | 0.375 | 0.225 | 0.625 | 1.000 | 0.500 | 0.895 | 1.000 | 0 |
| train | E+namemerge | s012 | 0.000 | 1.000 | 0.500 | 0.917 | 1.000 | 0 | 0.895 | 0.429 | 0.718 | 0.247 | 0.236 | 0.350 | 0.307 | n/a | n/a | n/a | 0.895 | 1.000 | 5 |
| train | E1+namemerge | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 1.000 | 0 | 0.895 | 0.429 | 0.697 | 0.224 | 0.220 | 0.484 | 0.257 | n/a | n/a | n/a | 0.895 | 1.000 | 4 |
| train | E2+namemerge | s012 | 0.000 | 0.500 | 0.500 | 0.917 | 1.000 | 0 | 0.895 | 0.429 | 0.720 | 0.253 | 0.290 | 0.375 | 0.225 | n/a | n/a | n/a | 0.895 | 1.000 | 0 |
| train | F | s0 | 0.000 | 0.500 | 0.000 | n/a | 1.000 | 0 | 0.895 | 0.429 | 0.682 | n/a | n/a | n/a | n/a | 0.667 | 1.000 | 0.667 | 0.895 | 1.000 | 1 |
| train | F+namemerge | s0 | 0.000 | 0.500 | 0.000 | n/a | 1.000 | 0 | 0.895 | 0.429 | 0.682 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.895 | 1.000 | 1 |
| hotel | C | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.500 | 1 | 1.000 | 0.727 | 0.880 | 0.205 | 0.168 | 0.214 | 0.190 | 0.636 | 0.400 | n/a | 1.000 | 1.000 | 0 |
| hotel | C+namemerge | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.500 | 1 | 1.000 | 0.727 | 0.880 | 0.205 | 0.168 | 0.214 | 0.190 | n/a | n/a | n/a | 1.000 | 1.000 | 0 |
| hotel | E | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.875 | 0 | 1.000 | 0.545 | 0.873 | 0.268 | 0.166 | 0.347 | 0.111 | 0.600 | 0.700 | n/a | 1.000 | 1.000 | 4 |
| hotel | E1 | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.875 | 0 | 1.000 | 0.545 | 0.873 | 0.268 | 0.129 | 0.343 | 0.080 | 0.800 | 0.700 | n/a | 1.000 | 1.000 | 4 |
| hotel | E2 | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.500 | 1 | 1.000 | 0.545 | 0.865 | 0.239 | 0.210 | 0.199 | 0.169 | 0.600 | 0.400 | n/a | 1.000 | 1.000 | 0 |
| hotel | E+namemerge | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.875 | 0 | 1.000 | 0.545 | 0.873 | 0.268 | 0.166 | 0.347 | 0.111 | n/a | n/a | n/a | 1.000 | 1.000 | 4 |
| hotel | E1+namemerge | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.875 | 0 | 1.000 | 0.545 | 0.873 | 0.268 | 0.129 | 0.343 | 0.080 | n/a | n/a | n/a | 1.000 | 1.000 | 4 |
| hotel | E2+namemerge | s012 | 1.000 | 0.600 | 1.000 | 0.600 | 0.500 | 1 | 1.000 | 0.545 | 0.865 | 0.239 | 0.210 | 0.199 | 0.169 | n/a | n/a | n/a | 1.000 | 1.000 | 0 |
| hotel | F | s0 | 1.000 | 0.600 | 0.000 | n/a | 0.875 | 1 | 1.000 | 0.364 | 0.819 | n/a | n/a | n/a | n/a | 0.500 | 0.875 | n/a | 1.000 | 1.000 | 3 |
| hotel | F+namemerge | s0 | 1.000 | 0.600 | 0.000 | n/a | 0.875 | 1 | 1.000 | 0.364 | 0.819 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1.000 | 1.000 | 3 |
| restaurant | C | s012 | 0.500 | 0.380 | n/a | n/a | 0.200 | 1 | 0.964 | 0.750 | 0.690 | 0.242 | 0.137 | 0.147 | 0.096 | 0.708 | 0.200 | 0.000 | 0.964 | 1.000 | 0 |
| restaurant | C+namemerge | s012 | 0.500 | 0.380 | n/a | n/a | 0.200 | 1 | 0.964 | 0.750 | 0.690 | 0.242 | 0.151 | 0.147 | 0.129 | n/a | n/a | n/a | 0.964 | 1.000 | 0 |
| restaurant | E | s012 | 0.500 | 0.380 | n/a | n/a | 0.600 | 1 | 0.964 | 0.667 | 0.745 | 0.244 | 0.125 | 0.265 | 0.224 | 0.700 | 0.429 | 0.333 | 0.964 | 1.000 | 1 |
| restaurant | E1 | s012 | 0.000 | 0.380 | n/a | n/a | 0.600 | 1 | 0.964 | 0.583 | 0.721 | 0.246 | 0.116 | 0.233 | 0.174 | 0.737 | 0.429 | 0.500 | 0.964 | 1.000 | 1 |
| restaurant | E2 | s012 | 0.500 | 0.380 | n/a | n/a | 0.200 | 1 | 0.964 | 0.583 | 0.610 | 0.188 | 0.168 | 0.189 | 0.141 | 0.778 | 0.200 | 0.333 | 0.964 | 1.000 | 0 |
| restaurant | E+namemerge | s012 | 0.500 | 0.380 | n/a | n/a | 0.600 | 1 | 0.964 | 0.667 | 0.745 | 0.244 | 0.148 | 0.265 | 0.284 | n/a | n/a | n/a | 0.964 | 1.000 | 1 |
| restaurant | E1+namemerge | s012 | 0.000 | 0.380 | n/a | n/a | 0.600 | 1 | 0.964 | 0.583 | 0.721 | 0.246 | 0.125 | 0.233 | 0.194 | n/a | n/a | n/a | 0.964 | 1.000 | 1 |
| restaurant | E2+namemerge | s012 | 0.500 | 0.380 | n/a | n/a | 0.200 | 1 | 0.964 | 0.583 | 0.610 | 0.188 | 0.210 | 0.189 | 0.196 | n/a | n/a | n/a | 0.964 | 1.000 | 0 |
| restaurant | F | s0 | 0.333 | 0.380 | n/a | n/a | 0.200 | 1 | 0.964 | 0.250 | 0.656 | n/a | n/a | n/a | n/a | 0.727 | 0.333 | 1.000 | 0.964 | 1.000 | 0 |
| restaurant | F+namemerge | s0 | 0.333 | 0.380 | n/a | n/a | 0.200 | 1 | 0.964 | 0.250 | 0.656 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.964 | 1.000 | 0 |

## Tokens

Per entity and variant ("all" = sum). x_A is n/a (no A in this run). recall = strict recall_after of the +namemerge row; est = some counts estimated. C = 3 orders + all splits (v3.2); E, E1, E2 = entity jobs + all gate jobs + split jobs of failed gates (E1 = `e` group-0 jobs + `e1` jobs); F = `f` jobs.

| ent | variant | calls | prompt tok | output tok | total | x A | recall | recall per 100K tok | est |
|---|---|---|---|---|---|---|---|---|---|
| train | C | 18 | 44665 | 9160 | 53825 | n/a | 0.429 | 0.796 |  |
| train | E | 22 | 73415 | 13847 | 87262 | n/a | 0.429 | 0.491 |  |
| train | E1 | 22 | 73055 | 13212 | 86267 | n/a | 0.429 | 0.497 |  |
| train | E2 | 22 | 64233 | 12592 | 76825 | n/a | 0.429 | 0.558 |  |
| train | F | 2 | 20193 | 4471 | 24664 | n/a | 0.429 | 1.738 |  |
| hotel | C | 15 | 38331 | 10139 | 48470 | n/a | 0.727 | 1.500 |  |
| hotel | E | 20 | 57895 | 13261 | 71156 | n/a | 0.545 | 0.767 |  |
| hotel | E1 | 20 | 57521 | 13281 | 70802 | n/a | 0.545 | 0.770 |  |
| hotel | E2 | 20 | 43539 | 9571 | 53110 | n/a | 0.545 | 1.027 |  |
| hotel | F | 2 | 17518 | 3838 | 21356 | n/a | 0.364 | 1.703 |  |
| restaurant | C | 19 | 59578 | 16281 | 75859 | n/a | 0.750 | 0.989 |  |
| restaurant | E | 23 | 85762 | 19493 | 105255 | n/a | 0.667 | 0.633 |  |
| restaurant | E1 | 23 | 81086 | 18793 | 99879 | n/a | 0.583 | 0.584 |  |
| restaurant | E2 | 23 | 64464 | 15776 | 80240 | n/a | 0.583 | 0.727 |  |
| restaurant | F | 3 | 17680 | 4719 | 22399 | n/a | 0.250 | 1.116 |  |
| all | C | 52 | 142574 | 35580 | 178154 | n/a | n/a | n/a |  |
| all | E | 65 | 217072 | 46601 | 263673 | n/a | n/a | n/a |  |
| all | E1 | 65 | 211662 | 45286 | 256948 | n/a | n/a | n/a |  |
| all | E2 | 65 | 172236 | 37939 | 210175 | n/a | n/a | n/a |  |
| all | F | 7 | 55391 | 13028 | 68419 | n/a | n/a | n/a |  |

## Stats

### train
- C: agree_mean 0.816, agree_full_share 0.552, ties 3
- E: agree_mean 0.782, agree_full_share 0.483, ties 4, gate_failed 4, cue 5, split 2
- E1: agree_mean 0.793, agree_full_share 0.552, ties 5, gate_failed 4, cue 4, split 2
- E2: agree_mean 0.851, agree_full_share 0.655, ties 3, gate_failed 4, cue 0, split 2
- F: agree_mean 1.000, agree_full_share 1.000, ties 0, gate_failed 0, cue 1, split 0
- v3.2 gate: candidates 12, gate-failed 4
### hotel
- C: agree_mean 0.774, agree_full_share 0.484, ties 5
- E: agree_mean 0.634, agree_full_share 0.129, ties 7, gate_failed 5, cue 4, split 4
- E1: agree_mean 0.720, agree_full_share 0.290, ties 4, gate_failed 5, cue 4, split 4
- E2: agree_mean 0.742, agree_full_share 0.323, ties 3, gate_failed 5, cue 0, split 5
- F: agree_mean 1.000, agree_full_share 1.000, ties 0, gate_failed 0, cue 3, split 0
- v3.2 gate: candidates 9, gate-failed 5
### restaurant
- C: agree_mean 0.830, agree_full_share 0.667, ties 10
- E: agree_mean 0.830, agree_full_share 0.579, ties 5, gate_failed 4, cue 1, split 3
- E1: agree_mean 0.836, agree_full_share 0.614, ties 6, gate_failed 4, cue 1, split 3
- E2: agree_mean 0.854, agree_full_share 0.737, ties 10, gate_failed 4, cue 0, split 4
- F: agree_mean 1.000, agree_full_share 1.000, ties 0, gate_failed 0, cue 0, split 0
- v3.2 gate: candidates 10, gate-failed 4

