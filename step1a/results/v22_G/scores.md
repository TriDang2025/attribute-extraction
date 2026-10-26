# Part G: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1124 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 223.000 | 0.578 | 18 | 0.834 | 0.794 | 0.517 | 0.626 | v1/v2: original Step 2, no filter |
| v2.1 | 963 | 0.887 | 0.800 | 0.570 | 0.666 | 0.591 | 174.333 | 0.537 | 20 | 0.834 | 0.810 | 0.592 | 0.684 | A + B + type |
| G_w2_t1_02 | 963 | 0.887 | 0.923 | 0.280 | 0.429 | 0.381 | 463.667 | 0.795 | 30 | 0.834 | 0.905 | 0.387 | 0.542 | staged: context w2 t1 0.2, strings t2 0.4 |
| G_w2_t1_03 | 963 | 0.887 | 0.806 | 0.538 | 0.645 | 0.572 | 238.667 | 0.654 | 23 | 0.834 | 0.800 | 0.570 | 0.666 | staged: context w2 t1 0.3, strings t2 0.4 |
| G_w2_t1_04 | 963 | 0.887 | 0.800 | 0.579 | 0.672 | 0.596 | 180.333 | 0.569 | 20 | 0.834 | 0.813 | 0.600 | 0.690 | staged: context w2 t1 0.4, strings t2 0.4 |
| G_w3_t1_02 | 963 | 0.887 | 0.933 | 0.212 | 0.345 | 0.306 | 546.667 | 0.793 | 29 | 0.834 | 0.901 | 0.314 | 0.465 | staged: context w3 t1 0.2, strings t2 0.4 |
| G_w3_t1_03 | 963 | 0.887 | 0.846 | 0.417 | 0.559 | 0.496 | 321.667 | 0.707 | 24 | 0.834 | 0.830 | 0.492 | 0.618 | staged: context w3 t1 0.3, strings t2 0.4 |
| G_w3_t1_04 | 963 | 0.887 | 0.802 | 0.579 | 0.673 | 0.597 | 185.000 | 0.578 | 20 | 0.834 | 0.813 | 0.600 | 0.691 | staged: context w3 t1 0.4, strings t2 0.4 |
| G_turn_t1_02 | 963 | 0.887 | 0.914 | 0.166 | 0.281 | 0.249 | 568.667 | 0.824 | 30 | 0.834 | 0.850 | 0.255 | 0.392 | staged: context turn t1 0.2, strings t2 0.4 |
| G_turn_t1_03 | 963 | 0.887 | 0.841 | 0.440 | 0.578 | 0.513 | 363.000 | 0.701 | 27 | 0.834 | 0.834 | 0.481 | 0.610 | staged: context turn t1 0.3, strings t2 0.4 |
| G_turn_t1_04 | 963 | 0.887 | 0.801 | 0.560 | 0.659 | 0.585 | 200.667 | 0.599 | 20 | 0.834 | 0.808 | 0.582 | 0.676 | staged: context turn t1 0.4, strings t2 0.4 |
| G_w2_t1_03_m3 | 963 | 0.887 | 0.798 | 0.557 | 0.656 | 0.582 | 201.333 | 0.589 | 21 | 0.834 | 0.801 | 0.584 | 0.675 | staged: context w2 t1 0.3, strings t2 0.4, min ctx size 3 |
| G_turn_t1_03_m3 | 963 | 0.887 | 0.838 | 0.447 | 0.583 | 0.517 | 348.000 | 0.685 | 27 | 0.834 | 0.836 | 0.489 | 0.618 | staged: context turn t1 0.3, strings t2 0.4, min ctx size 3 |
