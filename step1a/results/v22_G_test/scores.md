# Part G: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G_w2_t1_04 | 856 | 0.881 | 0.861 | 0.600 | 0.707 | 0.623 | 174.667 | 0.537 | 24 | 0.799 | 0.861 | 0.657 | 0.746 | staged: context w2 t1 0.4, strings t2 0.4 |
