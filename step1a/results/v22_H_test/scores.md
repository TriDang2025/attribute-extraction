# Part H: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H_l1r0_t035 | 856 | 0.881 | 0.850 | 0.643 | 0.732 | 0.644 | 193.667 | 0.613 | 23 | 0.799 | 0.845 | 0.662 | 0.742 | role words left 1 right 0, code shapes, type split, t 0.35 |
