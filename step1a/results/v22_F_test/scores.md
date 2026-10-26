# Part F: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F_m2_t06_bk | 856 | 0.881 | 0.846 | 0.608 | 0.707 | 0.623 | 153.333 | 0.481 | 23 | 0.799 | 0.850 | 0.661 | 0.744 | V21 + fold small clusters (< 2) to nearest kept centroid, tau 0.6, booking constraint |
