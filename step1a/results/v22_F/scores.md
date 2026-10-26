# Part F: spans clustering variants

F1/P/R/K = lenient B-cubed vs gold classes, mean of 3 stage-1 seeds; e2e = vrec x F1; attrs = gold classes with a gold-labelled node (of 33); valcov = gold values in a clustered span; P1/R1/F1_1to1 = one-to-one cluster-to-class mapping.

| variant | n_spans | vrec | P | R | F1 | e2e | K | singleton_share | attrs | valcov | P1 | R1 | F1_1to1 | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F_m2 | 963 | 0.887 | 0.779 | 0.578 | 0.664 | 0.589 | 116.667 | 0.276 | 18 | 0.834 | 0.779 | 0.597 | 0.676 | V21 + fold small clusters (< 2) to nearest kept centroid, tau None |
| F_m2_t05 | 963 | 0.887 | 0.781 | 0.577 | 0.663 | 0.588 | 126.333 | 0.346 | 18 | 0.834 | 0.782 | 0.597 | 0.677 | V21 + fold small clusters (< 2) to nearest kept centroid, tau 0.5 |
| F_m2_t06 | 963 | 0.887 | 0.788 | 0.573 | 0.664 | 0.589 | 155.667 | 0.481 | 20 | 0.834 | 0.789 | 0.595 | 0.678 | V21 + fold small clusters (< 2) to nearest kept centroid, tau 0.6 |
| F_m3 | 963 | 0.887 | 0.731 | 0.606 | 0.662 | 0.588 | 72.333 | 0.164 | 12 | 0.834 | 0.736 | 0.622 | 0.674 | V21 + fold small clusters (< 3) to nearest kept centroid, tau None |
| F_m3_t05 | 963 | 0.887 | 0.757 | 0.597 | 0.668 | 0.592 | 105.333 | 0.425 | 17 | 0.834 | 0.771 | 0.613 | 0.683 | V21 + fold small clusters (< 3) to nearest kept centroid, tau 0.5 |
| F_m3_t06 | 963 | 0.887 | 0.779 | 0.590 | 0.671 | 0.595 | 151.333 | 0.562 | 18 | 0.834 | 0.778 | 0.606 | 0.681 | V21 + fold small clusters (< 3) to nearest kept centroid, tau 0.6 |
| F_mean | 963 | 0.887 | 0.719 | 0.639 | 0.677 | 0.600 | 55.667 | 0.125 | 10 | 0.834 | 0.720 | 0.652 | 0.684 | V21 + fold small clusters (< mean) to nearest kept centroid, tau None |
| F_mean_t05 | 963 | 0.887 | 0.748 | 0.619 | 0.677 | 0.601 | 100.000 | 0.485 | 15 | 0.834 | 0.772 | 0.633 | 0.696 | V21 + fold small clusters (< mean) to nearest kept centroid, tau 0.5 |
| F_mean_t06 | 963 | 0.887 | 0.777 | 0.609 | 0.683 | 0.606 | 151.333 | 0.608 | 18 | 0.834 | 0.780 | 0.622 | 0.692 | V21 + fold small clusters (< mean) to nearest kept centroid, tau 0.6 |
| F_m2_t06_bk | 963 | 0.887 | 0.796 | 0.571 | 0.665 | 0.590 | 162.333 | 0.503 | 20 | 0.834 | 0.809 | 0.594 | 0.685 | V21 + fold small clusters (< 2) to nearest kept centroid, tau 0.6, booking constraint |
| F_m3_t06_bk | 963 | 0.887 | 0.793 | 0.580 | 0.670 | 0.595 | 165.333 | 0.572 | 19 | 0.834 | 0.798 | 0.602 | 0.687 | V21 + fold small clusters (< 3) to nearest kept centroid, tau 0.6, booking constraint |
| F_mean_t06_bk | 963 | 0.887 | 0.791 | 0.590 | 0.676 | 0.599 | 166.333 | 0.581 | 19 | 0.834 | 0.791 | 0.610 | 0.689 | V21 + fold small clusters (< mean) to nearest kept centroid, tau 0.6, booking constraint |
