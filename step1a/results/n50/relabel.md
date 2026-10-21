# Value clusters scored against attribute, entity and slot

444 value units. Gold classes: attribute 35, entity 5, slot 19

k-means on raw bge-m3 vectors, k = number of classes of the target label, mean B-cubed F1 (NMI) over 3 seeds. Each row's clustering is scored against all three labels.

| Variant | k (target) | vs attribute | vs entity | vs slot |
|---|---|---|---|---|
| value | 5 (entity) | 0.269 (0.50) | 0.345 (0.12) | 0.427 (0.56) |
| value | 19 (slot) | 0.398 (0.66) | 0.192 (0.20) | 0.526 (0.70) |
| value | 35 (attribute) | 0.375 (0.66) | 0.133 (0.23) | 0.440 (0.67) |
| window | 5 (entity) | 0.245 (0.50) | 0.534 (0.43) | 0.351 (0.48) |
| window | 19 (slot) | 0.300 (0.56) | 0.333 (0.44) | 0.295 (0.48) |
| window | 35 (attribute) | 0.289 (0.56) | 0.212 (0.41) | 0.256 (0.48) |
| turn | 5 (entity) | 0.238 (0.47) | 0.468 (0.33) | 0.383 (0.50) |
| turn | 19 (slot) | 0.296 (0.55) | 0.267 (0.36) | 0.325 (0.50) |
| turn | 35 (attribute) | 0.284 (0.56) | 0.186 (0.37) | 0.259 (0.49) |

## Two-stage: entity group first, then value strings inside each group

Mean over 3 k-means seeds for the Chroma grouping. No gold k is used in stage 2.

| Stage 1 | Stage 2 threshold | K | vs attribute F1 (NMI) | vs entity F1 | vs slot F1 |
|---|---|---|---|---|---|
| oracle entity (gold) | 0.3 | 147 | 0.627 (0.82) | 0.172 | 0.489 |
| oracle entity (gold) | 0.4 | 120 | 0.662 (0.82) | 0.203 | 0.514 |
| oracle entity (gold) | 0.5 | 74 | 0.612 (0.78) | 0.397 | 0.493 |
| Chroma chunk cluster (k-means k=5) | 0.3 | 163 | 0.459 (0.74) | 0.121 | 0.408 |
| Chroma chunk cluster (k-means k=5) | 0.4 | 134 | 0.470 (0.73) | 0.136 | 0.428 |
| Chroma chunk cluster (k-means k=5) | 0.5 | 87 | 0.431 (0.65) | 0.264 | 0.418 |
