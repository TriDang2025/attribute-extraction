# Part J: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1008 | 0.883 | 0.856 | 0.531 | 0.655 | 0.579 | 214.667 | 0.606 | 21 | 0.800 | 0.837 | 0.577 | 0.683 | v1/v2: original Step 2, no filter |
| v2.1 | 856 | 0.881 | 0.860 | 0.605 | 0.710 | 0.625 | 166.333 | 0.521 | 23 | 0.799 | 0.861 | 0.658 | 0.746 | A + B + type |
| J_Hl1r0_t035_fm2_06bk | 856 | 0.881 | 0.831 | 0.649 | 0.729 | 0.642 | 160.667 | 0.503 | 21 | 0.799 | 0.828 | 0.668 | 0.740 | H l1r0_t035 + fold 2, tau 0.6, booking |
| J_Hl0r1_t04_fm2_06bk | 856 | 0.881 | 0.864 | 0.578 | 0.692 | 0.610 | 162.333 | 0.457 | 25 | 0.799 | 0.864 | 0.639 | 0.735 | H l0r1_t04 + fold 2, tau 0.6, booking |
