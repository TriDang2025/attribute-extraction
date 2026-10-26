# v2.1 part C: spans clustering variants (50 dev dialogues)

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1124 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 223.000 | 0.578 | 18 | 0.834 | v1/v2: original Step 2, no filter |
| C_b03_k1_flat | 1124 | 0.887 | 0.381 | 0.705 | 0.495 | 0.439 | 57.667 | 0.386 | 10 | 0.834 | left cue beta 0.3 k 1 type off t 0.4 |
| C_b03_k1_type | 1124 | 0.887 | 0.595 | 0.726 | 0.654 | 0.580 | 65.667 | 0.379 | 13 | 0.834 | left cue beta 0.3 k 1 type on t 0.4 |
| C_b03_k2_flat | 1124 | 0.887 | 0.382 | 0.706 | 0.495 | 0.439 | 61.667 | 0.426 | 10 | 0.834 | left cue beta 0.3 k 2 type off t 0.4 |
| C_b03_k2_type | 1124 | 0.887 | 0.608 | 0.694 | 0.648 | 0.575 | 74.000 | 0.405 | 13 | 0.834 | left cue beta 0.3 k 2 type on t 0.4 |
| C_b05_k1_flat | 1124 | 0.887 | 0.158 | 0.927 | 0.270 | 0.239 | 5.000 | 0.000 | 0 | 0.834 | left cue beta 0.5 k 1 type off t 0.4 |
| C_b05_k1_type | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | left cue beta 0.5 k 1 type on t 0.4 |
| C_b05_k2_flat | 1124 | 0.887 | 0.158 | 0.927 | 0.270 | 0.239 | 5.000 | 0.000 | 0 | 0.834 | left cue beta 0.5 k 2 type off t 0.4 |
| C_b05_k2_type | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | left cue beta 0.5 k 2 type on t 0.4 |
| C_b05_k1_type_t03 | 1124 | 0.887 | 0.552 | 0.905 | 0.686 | 0.609 | 27.000 | 0.222 | 7 | 0.834 | left cue beta 0.5 k 1 type on t 0.3 |
| C_b05_k1_type_t05 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | left cue beta 0.5 k 1 type on t 0.5 |
| C_b05_k1_type_cl | 1124 | 0.887 | 0.746 | 0.446 | 0.559 | 0.495 | 102.333 | 0.147 | 17 | 0.834 | left cue beta 0.5 k 1 type on t 0.4 cannot-link |
