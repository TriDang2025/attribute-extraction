# Part H: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H_l1r0_t035 | 963 | 0.887 | 0.802 | 0.606 | 0.690 | 0.612 | 216.667 | 0.633 | 20 | 0.834 | 0.809 | 0.618 | 0.701 | role words left 1 right 0, code shapes, type split, t 0.35 |
| H_l1r0_t04 | 963 | 0.887 | 0.756 | 0.639 | 0.692 | 0.614 | 162.000 | 0.512 | 17 | 0.834 | 0.758 | 0.623 | 0.684 | role words left 1 right 0, code shapes, type split, t 0.4 |
| H_l1r0_t045 | 963 | 0.887 | 0.735 | 0.716 | 0.726 | 0.644 | 128.333 | 0.481 | 17 | 0.834 | 0.749 | 0.662 | 0.703 | role words left 1 right 0, code shapes, type split, t 0.45 |
| H_l2r0_t035 | 963 | 0.887 | 0.811 | 0.541 | 0.649 | 0.575 | 222.000 | 0.596 | 22 | 0.834 | 0.811 | 0.561 | 0.663 | role words left 2 right 0, code shapes, type split, t 0.35 |
| H_l2r0_t04 | 963 | 0.887 | 0.755 | 0.648 | 0.697 | 0.618 | 172.333 | 0.526 | 19 | 0.834 | 0.736 | 0.601 | 0.662 | role words left 2 right 0, code shapes, type split, t 0.4 |
| H_l2r0_t045 | 963 | 0.887 | 0.697 | 0.703 | 0.700 | 0.621 | 121.333 | 0.434 | 14 | 0.834 | 0.720 | 0.637 | 0.676 | role words left 2 right 0, code shapes, type split, t 0.45 |
| H_l1r1_t035 | 963 | 0.887 | 0.817 | 0.551 | 0.658 | 0.584 | 253.667 | 0.697 | 22 | 0.834 | 0.811 | 0.573 | 0.671 | role words left 1 right 1, code shapes, type split, t 0.35 |
| H_l1r1_t04 | 963 | 0.887 | 0.791 | 0.581 | 0.670 | 0.594 | 199.000 | 0.593 | 20 | 0.834 | 0.793 | 0.587 | 0.674 | role words left 1 right 1, code shapes, type split, t 0.4 |
| H_l1r1_t045 | 963 | 0.887 | 0.752 | 0.670 | 0.708 | 0.628 | 150.333 | 0.523 | 19 | 0.834 | 0.752 | 0.640 | 0.691 | role words left 1 right 1, code shapes, type split, t 0.45 |
| H_l0r1_t035 | 963 | 0.887 | 0.830 | 0.513 | 0.634 | 0.562 | 238.333 | 0.653 | 25 | 0.834 | 0.844 | 0.575 | 0.684 | role words left 0 right 1, code shapes, type split, t 0.35 |
| H_l0r1_t04 | 963 | 0.887 | 0.803 | 0.551 | 0.653 | 0.579 | 192.667 | 0.552 | 23 | 0.834 | 0.810 | 0.590 | 0.683 | role words left 0 right 1, code shapes, type split, t 0.4 |
| H_l0r1_t045 | 963 | 0.887 | 0.777 | 0.600 | 0.677 | 0.601 | 151.667 | 0.477 | 19 | 0.834 | 0.773 | 0.599 | 0.675 | role words left 0 right 1, code shapes, type split, t 0.45 |
