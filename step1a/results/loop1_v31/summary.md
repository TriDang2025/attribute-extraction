# wf_v3.1 pilot summary

Run `results\graph_v22_dev50`. Targets and per-check blocks in scores_<ent>.md; `+namemerge` = same response after merging same-name, same-placement clusters; j_*_desc = GLiNER with the description as label (v2 only); real_acc / noise_rub / role_acc come from the filled name rubric.

| ent | variant | run | merge_pure | merge_frag | split_done | split_side | noise_marked | noise_kept | place_right | recall_after | p1_after | j_right | j_wrong | j_right_desc | j_wrong_desc | real_acc | noise_rub | role_acc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| train | nohints | r1 | 1.000 | 0.500 | 0.000 | n/a | 1.000 | 0 | 0.895 | 0.571 | 0.707 | 0.244 | 0.156 | n/a | n/a | 0.889 | 1.000 | 0.750 |
| train | nohints+namemerge | r1 | 1.000 | 0.500 | 0.000 | n/a | 1.000 | 0 | 0.895 | 0.571 | 0.707 | 0.244 | 0.156 | n/a | n/a | n/a | n/a | n/a |
| train | nohints_long | r1 | n/a | 0.000 | 0.000 | n/a | 0.889 | 1 | 0.895 | 0.571 | 0.713 | 0.078 | 0.114 | n/a | n/a | 0.900 | 0.889 | 0.917 |
| train | nohints_long+namemerge | r1 | 0.000 | 1.000 | 0.000 | n/a | 0.889 | 1 | 0.895 | 0.429 | 0.696 | 0.197 | 0.147 | n/a | n/a | n/a | n/a | n/a |
| train | v2 | r1 | 0.000 | 0.500 | 0.500 | 0.917 | 0.667 | 0 | 0.895 | 0.571 | 0.676 | 0.248 | 0.219 | 0.321 | 0.249 | 0.941 | 0.667 | 0.857 |
| train | v2 | r2 | 0.000 | 0.500 | 0.500 | 0.917 | 0.778 | 0 | 0.895 | 0.429 | 0.688 | 0.221 | 0.194 | 0.321 | 0.259 | 0.938 | 0.700 | 0.857 |
| train | v2+namemerge | r1 | 0.000 | 0.500 | 0.500 | 0.917 | 0.667 | 0 | 0.895 | 0.571 | 0.676 | 0.248 | 0.219 | 0.321 | 0.249 | n/a | n/a | n/a |
| train | v2+namemerge | r2 | 0.000 | 0.500 | 0.500 | 0.917 | 0.778 | 0 | 0.895 | 0.429 | 0.688 | 0.221 | 0.194 | 0.321 | 0.259 | n/a | n/a | n/a |
| train | v2_nocontext | r1 | 0.000 | 1.000 | 0.500 | 0.917 | 0.889 | 0 | 0.895 | 0.286 | 0.718 | 0.182 | 0.189 | 0.667 | 0.281 | 0.812 | 0.667 | 0.714 |
| train | v2_nocontext+namemerge | r1 | 0.000 | 1.000 | 0.500 | 0.917 | 0.889 | 0 | 0.895 | 0.286 | 0.718 | 0.182 | 0.189 | 0.667 | 0.281 | n/a | n/a | n/a |
| hotel | nohints | r1 | n/a | 0.000 | n/a | n/a | 0.000 | 8 | 1.000 | 0.455 | 0.788 | 0.294 | 0.082 | n/a | n/a | 0.789 | 0.000 | n/a |
| hotel | nohints+namemerge | r1 | 1.000 | 0.600 | n/a | n/a | 0.000 | 3 | 1.000 | 0.455 | 0.795 | 0.294 | 0.137 | n/a | n/a | n/a | n/a | n/a |
| hotel | v2 | r1 | 1.000 | 1.000 | n/a | n/a | 0.417 | 0 | 1.000 | 0.727 | 0.882 | 0.153 | 0.171 | 0.367 | 0.231 | 0.786 | 0.333 | n/a |
| hotel | v2 | r2 | 1.000 | 1.000 | n/a | n/a | 0.333 | 1 | 1.000 | 0.727 | 0.883 | 0.144 | 0.163 | 0.381 | 0.286 | 0.688 | 0.267 | n/a |
| hotel | v2+namemerge | r1 | 1.000 | 1.000 | n/a | n/a | 0.417 | 0 | 1.000 | 0.727 | 0.882 | 0.153 | 0.171 | 0.367 | 0.231 | n/a | n/a | n/a |
| hotel | v2+namemerge | r2 | 1.000 | 1.000 | n/a | n/a | 0.333 | 1 | 1.000 | 0.727 | 0.883 | 0.144 | 0.163 | 0.381 | 0.286 | n/a | n/a | n/a |
| hotel | v2_nocontext | r1 | 1.000 | 1.000 | n/a | n/a | 0.667 | 0 | 1.000 | 0.727 | 0.891 | 0.188 | 0.130 | 0.684 | 0.183 | 0.600 | 0.500 | n/a |
| hotel | v2_nocontext+namemerge | r1 | 1.000 | 1.000 | n/a | n/a | 0.667 | 0 | 1.000 | 0.727 | 0.891 | 0.188 | 0.130 | 0.684 | 0.183 | n/a | n/a | n/a |
| restaurant | nohints | r1 | n/a | 0.000 | n/a | n/a | 0.000 | 8 | 0.964 | 0.667 | 0.696 | 0.251 | 0.031 | n/a | n/a | 0.918 | 0.000 | 0.250 |
| restaurant | nohints+namemerge | r1 | 0.500 | 0.456 | n/a | n/a | 0.000 | 7 | 0.964 | 0.583 | 0.649 | 0.255 | 0.076 | n/a | n/a | n/a | n/a | n/a |
| restaurant | v2 | r1 | 0.000 | 0.987 | n/a | n/a | 0.125 | 1 | 0.964 | 0.500 | 0.734 | 0.183 | 0.132 | 0.304 | 0.212 | 0.826 | 0.200 | 0.000 |
| restaurant | v2 | r2 | 0.000 | 1.000 | n/a | n/a | 0.250 | 1 | 0.964 | 0.333 | 0.727 | 0.183 | 0.139 | 0.331 | 0.136 | 0.611 | 0.333 | n/a |
| restaurant | v2+namemerge | r1 | 0.000 | 0.987 | n/a | n/a | 0.125 | 1 | 0.964 | 0.500 | 0.734 | 0.183 | 0.132 | 0.304 | 0.212 | n/a | n/a | n/a |
| restaurant | v2+namemerge | r2 | 0.000 | 1.000 | n/a | n/a | 0.250 | 1 | 0.964 | 0.333 | 0.727 | 0.183 | 0.139 | 0.331 | 0.136 | n/a | n/a | n/a |
| restaurant | v2_nocontext | r1 | 0.000 | 1.000 | n/a | n/a | 0.250 | 3 | 0.964 | 0.500 | 0.734 | 0.215 | 0.111 | 0.381 | 0.130 | 0.783 | 0.222 | n/a |
| restaurant | v2_nocontext+namemerge | r1 | 0.000 | 1.000 | n/a | n/a | 0.250 | 3 | 0.964 | 0.500 | 0.734 | 0.215 | 0.111 | 0.381 | 0.130 | n/a | n/a | n/a |
