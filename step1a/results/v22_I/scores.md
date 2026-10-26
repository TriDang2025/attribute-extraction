# Part I: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I_ch_t04_k2 | 963 | 0.887 | 0.747 | 0.670 | 0.707 | 0.627 | 114.333 | 0.400 | 15 | 0.834 | 0.756 | 0.648 | 0.698 | multi-view distances, CH view-quality weights, threshold t 0.4, window k 2 |
| I_ch_lj_k2 | 963 | 0.887 | 0.983 | 0.142 | 0.248 | 0.220 | 805.000 | 0.984 | 31 | 0.834 | 0.957 | 0.181 | 0.305 | multi-view distances, CH view-quality weights, Log-Jump K, window k 2 |
| I_w07_t04_k2 | 963 | 0.887 | 0.759 | 0.643 | 0.696 | 0.617 | 132.667 | 0.485 | 16 | 0.834 | 0.761 | 0.628 | 0.688 | multi-view distances, fixed weights 0.7/0.3, threshold t 0.4, window k 2 |
| I_w07_lj_k2 | 963 | 0.887 | 0.980 | 0.141 | 0.247 | 0.219 | 816.000 | 0.987 | 31 | 0.834 | 0.958 | 0.185 | 0.311 | multi-view distances, fixed weights 0.7/0.3, Log-Jump K, window k 2 |
| I_w05_t04_k2 | 963 | 0.887 | 0.646 | 0.698 | 0.671 | 0.595 | 86.333 | 0.372 | 11 | 0.834 | 0.658 | 0.601 | 0.628 | multi-view distances, fixed weights 0.5/0.5, threshold t 0.4, window k 2 |
| I_w05_lj_k2 | 963 | 0.887 | 0.983 | 0.139 | 0.244 | 0.217 | 826.000 | 0.983 | 31 | 0.834 | 0.956 | 0.177 | 0.299 | multi-view distances, fixed weights 0.5/0.5, Log-Jump K, window k 2 |
| I_ch_t04_k3 | 963 | 0.887 | 0.765 | 0.619 | 0.684 | 0.607 | 139.000 | 0.460 | 16 | 0.834 | 0.751 | 0.599 | 0.666 | multi-view distances, CH view-quality weights, threshold t 0.4, window k 3 |
| I_ch_lj_k3 | 963 | 0.887 | 0.985 | 0.102 | 0.185 | 0.164 | 841.000 | 0.983 | 31 | 0.834 | 0.955 | 0.130 | 0.229 | multi-view distances, CH view-quality weights, Log-Jump K, window k 3 |
