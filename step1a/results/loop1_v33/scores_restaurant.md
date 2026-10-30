# Pilot scores

Pilot entity E2. 57 clusters, 12 gold classes (restaurant, taxi).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.500 | 2 | FAIL |
| C+namemerge s012 | 0.500 | 2 | FAIL |
| E s012 | 0.500 | 2 | FAIL |
| E1 s012 | 0.000 | 2 | FAIL |
| E2 s012 | 0.500 | 2 | FAIL |
| E+namemerge s012 | 0.500 | 2 | FAIL |
| E1+namemerge s012 | 0.000 | 2 | FAIL |
| E2+namemerge s012 | 0.500 | 2 | FAIL |
| F s0 | 0.333 | 3 | FAIL |
| F+namemerge s0 | 0.333 | 3 | FAIL |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.380 | 79 | FAIL |
| C+namemerge s012 | 0.380 | 79 | FAIL |
| E s012 | 0.380 | 79 | FAIL |
| E1 s012 | 0.380 | 79 | FAIL |
| E2 s012 | 0.380 | 79 | FAIL |
| E+namemerge s012 | 0.380 | 79 | FAIL |
| E1+namemerge s012 | 0.380 | 79 | FAIL |
| E2+namemerge s012 | 0.380 | 79 | FAIL |
| F s0 | 0.380 | 79 | FAIL |
| F+namemerge s0 | 0.380 | 79 | FAIL |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| C s012 | n/a | 0 |  |
| C+namemerge s012 | n/a | 0 |  |
| E s012 | n/a | 0 |  |
| E1 s012 | n/a | 0 |  |
| E2 s012 | n/a | 0 |  |
| E+namemerge s012 | n/a | 0 |  |
| E1+namemerge s012 | n/a | 0 |  |
| E2+namemerge s012 | n/a | 0 |  |
| F s0 | n/a | 0 |  |
| F+namemerge s0 | n/a | 0 |  |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| C s012 | n/a | 0 |  |
| C+namemerge s012 | n/a | 0 |  |
| E s012 | n/a | 0 |  |
| E1 s012 | n/a | 0 |  |
| E2 s012 | n/a | 0 |  |
| E+namemerge s012 | n/a | 0 |  |
| E1+namemerge s012 | n/a | 0 |  |
| E2+namemerge s012 | n/a | 0 |  |
| F s0 | n/a | 0 |  |
| F+namemerge s0 | n/a | 0 |  |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.200 | 5 | FAIL |
| C+namemerge s012 | 0.200 | 5 | FAIL |
| E s012 | 0.600 | 5 | FAIL |
| E1 s012 | 0.600 | 5 | FAIL |
| E2 s012 | 0.200 | 5 | FAIL |
| E+namemerge s012 | 0.600 | 5 | FAIL |
| E1+namemerge s012 | 0.600 | 5 | FAIL |
| E2+namemerge s012 | 0.200 | 5 | FAIL |
| F s0 | 0.200 | 5 | FAIL |
| F+namemerge s0 | 0.200 | 5 | FAIL |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| C s012 | 1 | 5 | ok |
| C+namemerge s012 | 1 | 5 | ok |
| E s012 | 1 | 5 | ok |
| E1 s012 | 1 | 5 | ok |
| E2 s012 | 1 | 5 | ok |
| E+namemerge s012 | 1 | 5 | ok |
| E1+namemerge s012 | 1 | 5 | ok |
| E2+namemerge s012 | 1 | 5 | ok |
| F s0 | 1 | 5 | ok |
| F+namemerge s0 | 1 | 5 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.964 | 28 | ok |
| C+namemerge s012 | 0.964 | 28 | ok |
| E s012 | 0.964 | 28 | ok |
| E1 s012 | 0.964 | 28 | ok |
| E2 s012 | 0.964 | 28 | ok |
| E+namemerge s012 | 0.964 | 28 | ok |
| E1+namemerge s012 | 0.964 | 28 | ok |
| E2+namemerge s012 | 0.964 | 28 | ok |
| F s0 | 0.964 | 28 | ok |
| F+namemerge s0 | 0.964 | 28 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.750 (before 0.667) | 12 | ok |
| C+namemerge s012 | 0.750 (before 0.667) | 12 | ok |
| E s012 | 0.667 (before 0.667) | 12 | ok |
| E1 s012 | 0.583 (before 0.667) | 12 | FAIL |
| E2 s012 | 0.583 (before 0.667) | 12 | FAIL |
| E+namemerge s012 | 0.667 (before 0.667) | 12 | ok |
| E1+namemerge s012 | 0.583 (before 0.667) | 12 | FAIL |
| E2+namemerge s012 | 0.583 (before 0.667) | 12 | FAIL |
| F s0 | 0.250 (before 0.667) | 12 | FAIL |
| F+namemerge s0 | 0.250 (before 0.667) | 12 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.583 | 12 |  |
| C+namemerge s012 | 0.583 | 12 |  |
| E s012 | 0.417 | 12 |  |
| E1 s012 | 0.417 | 12 |  |
| E2 s012 | 0.417 | 12 |  |
| E+namemerge s012 | 0.417 | 12 |  |
| E1+namemerge s012 | 0.417 | 12 |  |
| E2+namemerge s012 | 0.417 | 12 |  |
| F s0 | 0.250 | 12 |  |
| F+namemerge s0 | 0.250 | 12 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.690 | 154 | ok |
| C+namemerge s012 | 0.690 | 154 | ok |
| E s012 | 0.745 | 154 | ok |
| E1 s012 | 0.721 | 154 | ok |
| E2 s012 | 0.610 | 154 | ok |
| E+namemerge s012 | 0.745 | 154 | ok |
| E1+namemerge s012 | 0.721 | 154 | ok |
| E2+namemerge s012 | 0.610 | 154 | ok |
| F s0 | 0.656 | 154 | ok |
| F+namemerge s0 | 0.656 | 154 | ok |

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
| E+namemerge s012 | 1.000 | 1 |  |
| E1+namemerge s012 | 1.000 | 1 |  |
| E2+namemerge s012 | 1.000 | 1 |  |
| F s0 | 0.500 | 2 |  |
| F+namemerge s0 | 0.500 | 2 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.242 | 10 |  |
| C+namemerge s012 | 0.242 | 10 |  |
| E s012 | 0.244 | 9 |  |
| E1 s012 | 0.246 | 9 |  |
| E2 s012 | 0.188 | 9 |  |
| E+namemerge s012 | 0.244 | 9 |  |
| E1+namemerge s012 | 0.246 | 9 |  |
| E2+namemerge s012 | 0.188 | 9 |  |
| F s0 | n/a |  |  |
| F+namemerge s0 | n/a |  |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.137 | 21 |  |
| C+namemerge s012 | 0.151 | 19 |  |
| E s012 | 0.125 | 13 |  |
| E1 s012 | 0.116 | 14 |  |
| E2 s012 | 0.168 | 15 |  |
| E+namemerge s012 | 0.148 | 11 |  |
| E1+namemerge s012 | 0.125 | 13 |  |
| E2+namemerge s012 | 0.210 | 12 |  |
| F s0 | n/a |  |  |
| F+namemerge s0 | n/a |  |  |

## Comparison

| measure | target | C s012 | C+namemerge s012 | E s012 | E1 s012 | E2 s012 | E+namemerge s012 | E1+namemerge s012 | E2+namemerge s012 | F s0 | F+namemerge s0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.000 FAIL | 0.500 FAIL | 0.500 FAIL | 0.000 FAIL | 0.500 FAIL | 0.333 FAIL | 0.333 FAIL |
| merge_frag | >= 0.6 | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL |
| split_done | >= 1.0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| noise_marked | >= 0.7 | 0.200 FAIL | 0.200 FAIL | 0.600 FAIL | 0.600 FAIL | 0.200 FAIL | 0.600 FAIL | 0.600 FAIL | 0.200 FAIL | 0.200 FAIL | 0.200 FAIL |
| noise_kept | <= 2 | 1 ok | 1 ok | 1 ok | 1 ok | 1 ok | 1 ok | 1 ok | 1 ok | 1 ok | 1 ok |
| place_right | >= 0.8 | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok |
| recall_after | >= before (no loss) | 0.750 ok | 0.750 ok | 0.667 ok | 0.583 FAIL | 0.583 FAIL | 0.667 ok | 0.583 FAIL | 0.583 FAIL | 0.250 FAIL | 0.250 FAIL |
| recall_after_kept | report only | 0.583 | 0.583 | 0.417 | 0.417 | 0.417 | 0.417 | 0.417 | 0.417 | 0.250 | 0.250 |
| p1_after | >= 0.6 | 0.690 ok | 0.690 ok | 0.745 ok | 0.721 ok | 0.610 ok | 0.745 ok | 0.721 ok | 0.610 ok | 0.656 ok | 0.656 ok |
| sugg_right | report only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.500 | 0.500 |
| j_right | report only | 0.242 | 0.242 | 0.244 | 0.246 | 0.188 | 0.244 | 0.246 | 0.188 | n/a | n/a |
| j_wrong | report only | 0.137 | 0.151 | 0.125 | 0.116 | 0.168 | 0.148 | 0.125 | 0.210 | n/a | n/a |

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| C s012 | 0.708 | 24 | 0.200 | 5 | 0.000 | 3 | 0 |
| E s012 | 0.700 | 20 | 0.429 | 7 | 0.333 | 3 | 0 |
| E1 s012 | 0.737 | 19 | 0.429 | 7 | 0.500 | 2 | 0 |
| E2 s012 | 0.778 | 18 | 0.200 | 5 | 0.333 | 3 | 0 |
| F s0 | 0.727 | 11 | 0.333 | 3 | 1.000 | 1 | 0 |
