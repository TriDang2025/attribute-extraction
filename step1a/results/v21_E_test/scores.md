# v2.1 part E: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1008 | 0.883 | 0.856 | 0.531 | 0.655 | 0.579 | 214.667 | 0.606 | 21 | 0.800 | v1/v2: original Step 2, no filter |
| E_AB_type | 856 | 0.881 | 0.860 | 0.605 | 0.710 | 0.625 | 166.333 | 0.521 | 23 | 0.799 | A + B + type |
| E_AB_type_t035 | 856 | 0.881 | 0.880 | 0.564 | 0.687 | 0.605 | 195.667 | 0.577 | 24 | 0.799 | A + B + type, t 0.35 |
| E_AB_type_cue02 | 856 | 0.881 | 0.756 | 0.724 | 0.739 | 0.651 | 107.333 | 0.417 | 18 | 0.799 | A + B + type + cue 0.2 |
