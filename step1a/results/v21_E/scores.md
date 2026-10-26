# v2.1 part E: spans clustering variants (50 dev dialogues)

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1124 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 223.000 | 0.578 | 18 | 0.834 | v1/v2: original Step 2, no filter |
| E_AB | 963 | 0.887 | 0.802 | 0.565 | 0.663 | 0.588 | 166.333 | 0.521 | 20 | 0.834 | A + B, no type split |
| E_AB_type | 963 | 0.887 | 0.800 | 0.570 | 0.666 | 0.591 | 174.333 | 0.537 | 20 | 0.834 | A + B + type |
| E_AB_type_t045 | 963 | 0.887 | 0.762 | 0.604 | 0.674 | 0.598 | 143.667 | 0.476 | 17 | 0.834 | A + B + type, t 0.45 |
| E_AB_type_t035 | 963 | 0.887 | 0.817 | 0.541 | 0.651 | 0.577 | 213.667 | 0.615 | 24 | 0.834 | A + B + type, t 0.35 |
| E_AB_type_cue01 | 963 | 0.887 | 0.768 | 0.599 | 0.673 | 0.597 | 151.667 | 0.503 | 17 | 0.834 | A + B + type + cue 0.1 |
| E_AB_type_cue02 | 963 | 0.887 | 0.742 | 0.668 | 0.703 | 0.624 | 112.667 | 0.456 | 15 | 0.834 | A + B + type + cue 0.2 |
| E_AB_type_cue03 | 963 | 0.887 | 0.604 | 0.735 | 0.663 | 0.588 | 58.000 | 0.362 | 12 | 0.834 | A + B + type + cue 0.3 |
| E_AB_type_cl | 963 | 0.887 | 0.826 | 0.369 | 0.510 | 0.453 | 233.333 | 0.560 | 26 | 0.834 | A + B + type + cannot-link |
| E_AB_type_cl_t05 | 963 | 0.887 | 0.781 | 0.378 | 0.509 | 0.452 | 164.667 | 0.376 | 23 | 0.834 | A + B + type + cannot-link, t 0.5 |
| E_AB_type_cue02_cl | 963 | 0.887 | 0.793 | 0.385 | 0.519 | 0.460 | 165.667 | 0.383 | 24 | 0.834 | A + B + type + cue 0.2 + cannot-link |
