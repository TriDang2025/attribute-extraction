# v2.1 part B: spans clustering variants (50 dev dialogues)

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1124 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 223.000 | 0.578 | 18 | 0.834 | v1/v2: original Step 2, no filter |
| B_codes | 1124 | 0.887 | 0.794 | 0.565 | 0.660 | 0.585 | 175.000 | 0.509 | 16 | 0.834 | codes -> shape text (train id, reference, phone, postcode) |
| B_codes_prices | 1124 | 0.887 | 0.794 | 0.565 | 0.660 | 0.585 | 174.000 | 0.511 | 16 | 0.834 | codes and prices -> shape text |
| B_codes_prices_t05 | 1124 | 0.887 | 0.584 | 0.655 | 0.617 | 0.547 | 91.000 | 0.402 | 11 | 0.834 | codes and prices -> shape text, t=0.5 |
