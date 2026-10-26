# v2.1 part D: spans clustering variants (50 dev dialogues)

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1124 | 0.887 | 0.809 | 0.495 | 0.614 | 0.545 | 223.000 | 0.578 | 18 | 0.834 | v1/v2: original Step 2, no filter |
| D_a02_nocl_t035 | 1124 | 0.887 | 0.763 | 0.539 | 0.632 | 0.560 | 183.000 | 0.527 | 19 | 0.834 | {"alpha": 0.2, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.35} |
| D_a02_nocl_t045 | 1124 | 0.887 | 0.615 | 0.733 | 0.669 | 0.593 | 74.000 | 0.360 | 13 | 0.834 | {"alpha": 0.2, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.45} |
| D_a02_nocl_t055 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | {"alpha": 0.2, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.55} |
| D_a02_cl_t035 | 1124 | 0.887 | 0.825 | 0.356 | 0.497 | 0.441 | 247.333 | 0.510 | 25 | 0.834 | {"alpha": 0.2, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.35} |
| D_a02_cl_t045 | 1124 | 0.887 | 0.765 | 0.405 | 0.530 | 0.470 | 147.333 | 0.304 | 22 | 0.834 | {"alpha": 0.2, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.45} |
| D_a02_cl_t055 | 1124 | 0.887 | 0.732 | 0.442 | 0.551 | 0.489 | 102.000 | 0.137 | 15 | 0.834 | {"alpha": 0.2, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.55} |
| D_a05_nocl_t035 | 1124 | 0.887 | 0.576 | 0.857 | 0.689 | 0.611 | 37.333 | 0.162 | 8 | 0.834 | {"alpha": 0.5, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.35} |
| D_a05_nocl_t045 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | {"alpha": 0.5, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.45} |
| D_a05_nocl_t055 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | {"alpha": 0.5, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.55} |
| D_a05_cl_t035 | 1124 | 0.887 | 0.730 | 0.437 | 0.546 | 0.485 | 117.333 | 0.186 | 20 | 0.834 | {"alpha": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.35} |
| D_a05_cl_t045 | 1124 | 0.887 | 0.725 | 0.437 | 0.546 | 0.484 | 104.333 | 0.133 | 17 | 0.834 | {"alpha": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.45} |
| D_a05_cl_t055 | 1124 | 0.887 | 0.725 | 0.437 | 0.546 | 0.484 | 104.333 | 0.133 | 17 | 0.834 | {"alpha": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.55} |
| D_win_nocl_t035 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.35, "window": 2} |
| D_win_nocl_t045 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.45, "window": 2} |
| D_win_nocl_t055 | 1124 | 0.887 | 0.550 | 0.912 | 0.686 | 0.609 | 23.000 | 0.130 | 5 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.55, "window": 2} |
| D_win_cl_t035 | 1124 | 0.887 | 0.759 | 0.466 | 0.577 | 0.512 | 105.000 | 0.143 | 15 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.35, "window": 2} |
| D_win_cl_t045 | 1124 | 0.887 | 0.759 | 0.466 | 0.577 | 0.512 | 105.000 | 0.143 | 15 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.45, "window": 2} |
| D_win_cl_t055 | 1124 | 0.887 | 0.759 | 0.466 | 0.577 | 0.512 | 105.000 | 0.143 | 15 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.55, "window": 2} |
| D_a0_nocl_t030 | 1124 | 0.887 | 0.826 | 0.459 | 0.590 | 0.523 | 308.000 | 0.675 | 23 | 0.834 | {"by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.3} |
| D_a0_nocl_t040 | 1124 | 0.887 | 0.791 | 0.512 | 0.621 | 0.551 | 201.000 | 0.505 | 21 | 0.834 | {"by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.4} |
| D_a0_nocl_t050 | 1124 | 0.887 | 0.727 | 0.653 | 0.688 | 0.610 | 107.333 | 0.411 | 14 | 0.834 | {"by_type": true, "cannot_link": false, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.5} |
| D_a0_cl_t040 | 1124 | 0.887 | 0.823 | 0.334 | 0.475 | 0.421 | 264.667 | 0.517 | 26 | 0.834 | {"by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "t": 0.4} |
| D_win_cl_t065 | 1124 | 0.887 | 0.759 | 0.466 | 0.577 | 0.512 | 105.000 | 0.143 | 15 | 0.834 | {"alpha": 0.2, "beta": 0.5, "by_type": true, "cannot_link": true, "linkage": "average", "normalize": true, "prev_turns": 1, "side": "lr", "t": 0.65, "window": 2} |
