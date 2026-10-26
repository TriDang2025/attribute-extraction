# v2.1 part A: spans clustering variants (50 dev dialogues)

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1124 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 223.000 | 0.578 | 18 | 0.834 | v1/v2: original Step 2, no filter |
| A_stop | 1043 | 0.887 | 0.816 | 0.495 | 0.616 | 0.547 | 217.667 | 0.564 | 20 | 0.834 | drop pronouns / fillers |
| A_slots | 1042 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 217.667 | 0.596 | 18 | 0.834 | drop slot names |
| A_stop_slots | 963 | 0.887 | 0.816 | 0.495 | 0.616 | 0.547 | 212.333 | 0.582 | 20 | 0.834 | stop + slot names |
| A_stop_slots_s06 | 843 | 0.834 | 0.810 | 0.521 | 0.635 | 0.529 | 196.333 | 0.604 | 20 | 0.773 | stop + slot names + score >= 0.6 |
| A_s06 | 974 | 0.834 | 0.791 | 0.510 | 0.620 | 0.517 | 206.333 | 0.599 | 20 | 0.773 | GLiNER score >= 0.6 only |
