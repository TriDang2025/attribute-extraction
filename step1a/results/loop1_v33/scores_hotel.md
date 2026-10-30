# Pilot scores

Pilot entity E0. 31 clusters, 11 gold classes (hotel).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| C s012 | 1.000 | 1 | ok |
| C+namemerge s012 | 1.000 | 1 | ok |
| E s012 | 1.000 | 1 | ok |
| E1 s012 | 1.000 | 1 | ok |
| E2 s012 | 1.000 | 1 | ok |
| E+namemerge s012 | 1.000 | 1 | ok |
| E1+namemerge s012 | 1.000 | 1 | ok |
| E2+namemerge s012 | 1.000 | 1 | ok |
| F s0 | 1.000 | 1 | ok |
| F+namemerge s0 | 1.000 | 1 | ok |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.600 | 10 | ok |
| C+namemerge s012 | 0.600 | 10 | ok |
| E s012 | 0.600 | 10 | ok |
| E1 s012 | 0.600 | 10 | ok |
| E2 s012 | 0.600 | 10 | ok |
| E+namemerge s012 | 0.600 | 10 | ok |
| E1+namemerge s012 | 0.600 | 10 | ok |
| E2+namemerge s012 | 0.600 | 10 | ok |
| F s0 | 0.600 | 10 | ok |
| F+namemerge s0 | 0.600 | 10 | ok |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| C s012 | 1.000 | 2 | ok |
| C+namemerge s012 | 1.000 | 2 | ok |
| E s012 | 1.000 | 2 | ok |
| E1 s012 | 1.000 | 2 | ok |
| E2 s012 | 1.000 | 2 | ok |
| E+namemerge s012 | 1.000 | 2 | ok |
| E1+namemerge s012 | 1.000 | 2 | ok |
| E2+namemerge s012 | 1.000 | 2 | ok |
| F s0 | 0.000 | 2 | FAIL |
| F+namemerge s0 | 0.000 | 2 | FAIL |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.600 | 30 | FAIL |
| C+namemerge s012 | 0.600 | 30 | FAIL |
| E s012 | 0.600 | 30 | FAIL |
| E1 s012 | 0.600 | 30 | FAIL |
| E2 s012 | 0.600 | 30 | FAIL |
| E+namemerge s012 | 0.600 | 30 | FAIL |
| E1+namemerge s012 | 0.600 | 30 | FAIL |
| E2+namemerge s012 | 0.600 | 30 | FAIL |
| F s0 | n/a | 0 |  |
| F+namemerge s0 | n/a | 0 |  |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.500 | 8 | FAIL |
| C+namemerge s012 | 0.500 | 8 | FAIL |
| E s012 | 0.875 | 8 | ok |
| E1 s012 | 0.875 | 8 | ok |
| E2 s012 | 0.500 | 8 | FAIL |
| E+namemerge s012 | 0.875 | 8 | ok |
| E1+namemerge s012 | 0.875 | 8 | ok |
| E2+namemerge s012 | 0.500 | 8 | FAIL |
| F s0 | 0.875 | 8 | ok |
| F+namemerge s0 | 0.875 | 8 | ok |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| C s012 | 1 | 8 | ok |
| C+namemerge s012 | 1 | 8 | ok |
| E s012 | 0 | 8 | ok |
| E1 s012 | 0 | 8 | ok |
| E2 s012 | 1 | 8 | ok |
| E+namemerge s012 | 0 | 8 | ok |
| E1+namemerge s012 | 0 | 8 | ok |
| E2+namemerge s012 | 1 | 8 | ok |
| F s0 | 1 | 8 | ok |
| F+namemerge s0 | 1 | 8 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| C s012 | 1.000 | 20 | ok |
| C+namemerge s012 | 1.000 | 20 | ok |
| E s012 | 1.000 | 20 | ok |
| E1 s012 | 1.000 | 20 | ok |
| E2 s012 | 1.000 | 20 | ok |
| E+namemerge s012 | 1.000 | 20 | ok |
| E1+namemerge s012 | 1.000 | 20 | ok |
| E2+namemerge s012 | 1.000 | 20 | ok |
| F s0 | 1.000 | 20 | ok |
| F+namemerge s0 | 1.000 | 20 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.727 (before 0.455) | 11 | ok |
| C+namemerge s012 | 0.727 (before 0.455) | 11 | ok |
| E s012 | 0.545 (before 0.455) | 11 | ok |
| E1 s012 | 0.545 (before 0.455) | 11 | ok |
| E2 s012 | 0.545 (before 0.455) | 11 | ok |
| E+namemerge s012 | 0.545 (before 0.455) | 11 | ok |
| E1+namemerge s012 | 0.545 (before 0.455) | 11 | ok |
| E2+namemerge s012 | 0.545 (before 0.455) | 11 | ok |
| F s0 | 0.364 (before 0.455) | 11 | FAIL |
| F+namemerge s0 | 0.364 (before 0.455) | 11 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.727 | 11 |  |
| C+namemerge s012 | 0.727 | 11 |  |
| E s012 | 0.545 | 11 |  |
| E1 s012 | 0.545 | 11 |  |
| E2 s012 | 0.545 | 11 |  |
| E+namemerge s012 | 0.545 | 11 |  |
| E1+namemerge s012 | 0.545 | 11 |  |
| E2+namemerge s012 | 0.545 | 11 |  |
| F s0 | 0.364 | 11 |  |
| F+namemerge s0 | 0.364 | 11 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.880 | 116 | ok |
| C+namemerge s012 | 0.880 | 116 | ok |
| E s012 | 0.873 | 116 | ok |
| E1 s012 | 0.873 | 116 | ok |
| E2 s012 | 0.865 | 116 | ok |
| E+namemerge s012 | 0.873 | 116 | ok |
| E1+namemerge s012 | 0.873 | 116 | ok |
| E2+namemerge s012 | 0.865 | 116 | ok |
| F s0 | 0.819 | 116 | ok |
| F+namemerge s0 | 0.819 | 116 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 1.000 | 3 |  |
| C+namemerge s012 | 1.000 | 3 |  |
| E s012 | 1.000 | 3 |  |
| E1 s012 | 1.000 | 3 |  |
| E2 s012 | 1.000 | 3 |  |
| E+namemerge s012 | 1.000 | 3 |  |
| E1+namemerge s012 | 1.000 | 3 |  |
| E2+namemerge s012 | 1.000 | 3 |  |
| F s0 | 1.000 | 3 |  |
| F+namemerge s0 | 1.000 | 3 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.205 | 12 |  |
| C+namemerge s012 | 0.205 | 12 |  |
| E s012 | 0.268 | 11 |  |
| E1 s012 | 0.268 | 11 |  |
| E2 s012 | 0.239 | 10 |  |
| E+namemerge s012 | 0.268 | 11 |  |
| E1+namemerge s012 | 0.268 | 11 |  |
| E2+namemerge s012 | 0.239 | 10 |  |
| F s0 | n/a |  |  |
| F+namemerge s0 | n/a |  |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| C s012 | 0.168 | 13 |  |
| C+namemerge s012 | 0.168 | 13 |  |
| E s012 | 0.166 | 5 |  |
| E1 s012 | 0.129 | 7 |  |
| E2 s012 | 0.210 | 10 |  |
| E+namemerge s012 | 0.166 | 5 |  |
| E1+namemerge s012 | 0.129 | 7 |  |
| E2+namemerge s012 | 0.210 | 10 |  |
| F s0 | n/a |  |  |
| F+namemerge s0 | n/a |  |  |

## Comparison

| measure | target | C s012 | C+namemerge s012 | E s012 | E1 s012 | E2 s012 | E+namemerge s012 | E1+namemerge s012 | E2+namemerge s012 | F s0 | F+namemerge s0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| merge_frag | >= 0.6 | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok |
| split_done | >= 1.0 | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 0.000 FAIL | 0.000 FAIL |
| split_side | >= 0.7 | 0.600 FAIL | 0.600 FAIL | 0.600 FAIL | 0.600 FAIL | 0.600 FAIL | 0.600 FAIL | 0.600 FAIL | 0.600 FAIL | n/a | n/a |
| noise_marked | >= 0.7 | 0.500 FAIL | 0.500 FAIL | 0.875 ok | 0.875 ok | 0.500 FAIL | 0.875 ok | 0.875 ok | 0.500 FAIL | 0.875 ok | 0.875 ok |
| noise_kept | <= 2 | 1 ok | 1 ok | 0 ok | 0 ok | 1 ok | 0 ok | 0 ok | 1 ok | 1 ok | 1 ok |
| place_right | >= 0.8 | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| recall_after | >= before (no loss) | 0.727 ok | 0.727 ok | 0.545 ok | 0.545 ok | 0.545 ok | 0.545 ok | 0.545 ok | 0.545 ok | 0.364 FAIL | 0.364 FAIL |
| recall_after_kept | report only | 0.727 | 0.727 | 0.545 | 0.545 | 0.545 | 0.545 | 0.545 | 0.545 | 0.364 | 0.364 |
| p1_after | >= 0.6 | 0.880 ok | 0.880 ok | 0.873 ok | 0.873 ok | 0.865 ok | 0.873 ok | 0.873 ok | 0.865 ok | 0.819 ok | 0.819 ok |
| sugg_right | report only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.205 | 0.205 | 0.268 | 0.268 | 0.239 | 0.268 | 0.268 | 0.239 | n/a | n/a |
| j_wrong | report only | 0.168 | 0.168 | 0.166 | 0.129 | 0.210 | 0.166 | 0.129 | 0.210 | n/a | n/a |

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| C s012 | 0.636 | 11 | 0.400 | 10 | n/a | 0 | 0 |
| E s012 | 0.600 | 10 | 0.700 | 10 | n/a | 0 | 0 |
| E1 s012 | 0.800 | 10 | 0.700 | 10 | n/a | 0 | 0 |
| E2 s012 | 0.600 | 10 | 0.400 | 10 | n/a | 0 | 0 |
| F s0 | 0.500 | 8 | 0.875 | 8 | n/a | 0 | 0 |
