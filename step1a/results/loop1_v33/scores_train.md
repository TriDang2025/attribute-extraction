# Pilot scores

Pilot entity E1. 29 clusters, 7 gold classes (train).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.000 | 1 | FAIL |
| C+namemerge s012 | 0.000 | 1 | FAIL |
| E s012 | 0.000 | 1 | FAIL |
| E1 s012 | 0.000 | 1 | FAIL |
| E2 s012 | 0.000 | 1 | FAIL |
| E+namemerge s012 | 0.000 | 1 | FAIL |
| E1+namemerge s012 | 0.000 | 1 | FAIL |
| E2+namemerge s012 | 0.000 | 1 | FAIL |
| F s0 | 0.000 | 1 | FAIL |
| F+namemerge s0 | 0.000 | 1 | FAIL |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.500 | 6 | FAIL |
| C+namemerge s012 | 0.500 | 6 | FAIL |
| E s012 | 0.500 | 6 | FAIL |
| E1 s012 | 0.500 | 6 | FAIL |
| E2 s012 | 0.500 | 6 | FAIL |
| E+namemerge s012 | 1.000 | 6 | ok |
| E1+namemerge s012 | 0.500 | 6 | FAIL |
| E2+namemerge s012 | 0.500 | 6 | FAIL |
| F s0 | 0.500 | 6 | FAIL |
| F+namemerge s0 | 0.500 | 6 | FAIL |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.500 | 2 | FAIL |
| C+namemerge s012 | 0.500 | 2 | FAIL |
| E s012 | 0.500 | 2 | FAIL |
| E1 s012 | 0.500 | 2 | FAIL |
| E2 s012 | 0.500 | 2 | FAIL |
| E+namemerge s012 | 0.500 | 2 | FAIL |
| E1+namemerge s012 | 0.500 | 2 | FAIL |
| E2+namemerge s012 | 0.500 | 2 | FAIL |
| F s0 | 0.000 | 2 | FAIL |
| F+namemerge s0 | 0.000 | 2 | FAIL |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.917 | 12 | ok |
| C+namemerge s012 | 0.917 | 12 | ok |
| E s012 | 0.917 | 12 | ok |
| E1 s012 | 0.917 | 12 | ok |
| E2 s012 | 0.917 | 12 | ok |
| E+namemerge s012 | 0.917 | 12 | ok |
| E1+namemerge s012 | 0.917 | 12 | ok |
| E2+namemerge s012 | 0.917 | 12 | ok |
| F s0 | n/a | 0 |  |
| F+namemerge s0 | n/a | 0 |  |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.857 | 7 | ok |
| C+namemerge s012 | 0.857 | 7 | ok |
| E s012 | 1.000 | 7 | ok |
| E1 s012 | 1.000 | 7 | ok |
| E2 s012 | 1.000 | 7 | ok |
| E+namemerge s012 | 1.000 | 7 | ok |
| E1+namemerge s012 | 1.000 | 7 | ok |
| E2+namemerge s012 | 1.000 | 7 | ok |
| F s0 | 1.000 | 7 | ok |
| F+namemerge s0 | 1.000 | 7 | ok |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| C s012 | 0 | 7 | ok |
| C+namemerge s012 | 0 | 7 | ok |
| E s012 | 0 | 7 | ok |
| E1 s012 | 0 | 7 | ok |
| E2 s012 | 0 | 7 | ok |
| E+namemerge s012 | 0 | 7 | ok |
| E1+namemerge s012 | 0 | 7 | ok |
| E2+namemerge s012 | 0 | 7 | ok |
| F s0 | 0 | 7 | ok |
| F+namemerge s0 | 0 | 7 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.895 | 19 | ok |
| C+namemerge s012 | 0.895 | 19 | ok |
| E s012 | 0.895 | 19 | ok |
| E1 s012 | 0.895 | 19 | ok |
| E2 s012 | 0.895 | 19 | ok |
| E+namemerge s012 | 0.895 | 19 | ok |
| E1+namemerge s012 | 0.895 | 19 | ok |
| E2+namemerge s012 | 0.895 | 19 | ok |
| F s0 | 0.895 | 19 | ok |
| F+namemerge s0 | 0.895 | 19 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.429 (before 0.571) | 7 | FAIL |
| C+namemerge s012 | 0.429 (before 0.571) | 7 | FAIL |
| E s012 | 0.429 (before 0.571) | 7 | FAIL |
| E1 s012 | 0.429 (before 0.571) | 7 | FAIL |
| E2 s012 | 0.429 (before 0.571) | 7 | FAIL |
| E+namemerge s012 | 0.429 (before 0.571) | 7 | FAIL |
| E1+namemerge s012 | 0.429 (before 0.571) | 7 | FAIL |
| E2+namemerge s012 | 0.429 (before 0.571) | 7 | FAIL |
| F s0 | 0.429 (before 0.571) | 7 | FAIL |
| F+namemerge s0 | 0.429 (before 0.571) | 7 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.429 | 7 |  |
| C+namemerge s012 | 0.429 | 7 |  |
| E s012 | 0.429 | 7 |  |
| E1 s012 | 0.429 | 7 |  |
| E2 s012 | 0.286 | 7 |  |
| E+namemerge s012 | 0.429 | 7 |  |
| E1+namemerge s012 | 0.429 | 7 |  |
| E2+namemerge s012 | 0.286 | 7 |  |
| F s0 | 0.429 | 7 |  |
| F+namemerge s0 | 0.429 | 7 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.769 | 183 | ok |
| C+namemerge s012 | 0.769 | 183 | ok |
| E s012 | 0.697 | 183 | ok |
| E1 s012 | 0.697 | 183 | ok |
| E2 s012 | 0.720 | 183 | ok |
| E+namemerge s012 | 0.718 | 183 | ok |
| E1+namemerge s012 | 0.697 | 183 | ok |
| E2+namemerge s012 | 0.720 | 183 | ok |
| F s0 | 0.682 | 183 | ok |
| F+namemerge s0 | 0.682 | 183 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 1.000 | 1 |  |
| C+namemerge s012 | 1.000 | 1 |  |
| E s012 | 1.000 | 1 |  |
| E1 s012 | 1.000 | 1 |  |
| E2 s012 | 1.000 | 1 |  |
| E+namemerge s012 | 1.000 | 2 |  |
| E1+namemerge s012 | 1.000 | 1 |  |
| E2+namemerge s012 | 1.000 | 1 |  |
| F s0 | 1.000 | 1 |  |
| F+namemerge s0 | 1.000 | 1 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.247 | 4 |  |
| C+namemerge s012 | 0.247 | 4 |  |
| E s012 | 0.198 | 5 |  |
| E1 s012 | 0.224 | 5 |  |
| E2 s012 | 0.253 | 4 |  |
| E+namemerge s012 | 0.247 | 4 |  |
| E1+namemerge s012 | 0.224 | 5 |  |
| E2+namemerge s012 | 0.253 | 4 |  |
| F s0 | n/a |  |  |
| F+namemerge s0 | n/a |  |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.162 | 17 |  |
| C+namemerge s012 | 0.162 | 17 |  |
| E s012 | 0.236 | 10 |  |
| E1 s012 | 0.220 | 10 |  |
| E2 s012 | 0.290 | 8 |  |
| E+namemerge s012 | 0.236 | 10 |  |
| E1+namemerge s012 | 0.220 | 10 |  |
| E2+namemerge s012 | 0.290 | 8 |  |
| F s0 | n/a |  |  |
| F+namemerge s0 | n/a |  |  |

## Comparison

| measure | target | C s012 | C+namemerge s012 | E s012 | E1 s012 | E2 s012 | E+namemerge s012 | E1+namemerge s012 | E2+namemerge s012 | F s0 | F+namemerge s0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL |
| merge_frag | >= 0.6 | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 1.000 ok | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL |
| split_done | >= 1.0 | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.000 FAIL | 0.000 FAIL |
| split_side | >= 0.7 | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | n/a | n/a |
| noise_marked | >= 0.7 | 0.857 ok | 0.857 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| noise_kept | <= 2 | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok |
| place_right | >= 0.8 | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok |
| recall_after | >= before (no loss) | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL |
| recall_after_kept | report only | 0.429 | 0.429 | 0.429 | 0.429 | 0.286 | 0.429 | 0.429 | 0.286 | 0.429 | 0.429 |
| p1_after | >= 0.6 | 0.769 ok | 0.769 ok | 0.697 ok | 0.697 ok | 0.720 ok | 0.718 ok | 0.697 ok | 0.720 ok | 0.682 ok | 0.682 ok |
| sugg_right | report only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.247 | 0.247 | 0.198 | 0.224 | 0.253 | 0.247 | 0.224 | 0.253 | n/a | n/a |
| j_wrong | report only | 0.162 | 0.162 | 0.236 | 0.220 | 0.290 | 0.236 | 0.220 | 0.290 | n/a | n/a |

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| C s012 | 0.750 | 12 | 0.600 | 10 | 0.667 | 3 | 1 |
| E s012 | 1.000 | 11 | 1.000 | 7 | 1.000 | 3 | 0 |
| E1 s012 | 0.909 | 11 | 1.000 | 7 | 0.667 | 3 | 1 |
| E2 s012 | 0.625 | 8 | 1.000 | 7 | 0.500 | 2 | 0 |
| F s0 | 0.667 | 9 | 1.000 | 7 | 0.667 | 3 | 0 |
