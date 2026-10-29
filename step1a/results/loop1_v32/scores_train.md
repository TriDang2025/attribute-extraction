# Pilot scores

Pilot entity E1. 29 clusters, 7 gold classes (train).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.000 | 1 | FAIL |
| A+namemerge r1 | 0.000 | 1 | FAIL |
| B s0 | 0.000 | 1 | FAIL |
| B+namemerge s0 | 0.000 | 1 | FAIL |
| C s012 | 0.000 | 1 | FAIL |
| C+namemerge s012 | 0.000 | 1 | FAIL |
| D s012 | 0.000 | 1 | FAIL |
| D+namemerge s012 | 0.000 | 1 | FAIL |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.500 | 6 | FAIL |
| A+namemerge r1 | 0.500 | 6 | FAIL |
| B s0 | 0.500 | 6 | FAIL |
| B+namemerge s0 | 0.500 | 6 | FAIL |
| C s012 | 0.500 | 6 | FAIL |
| C+namemerge s012 | 0.500 | 6 | FAIL |
| D s012 | 0.500 | 6 | FAIL |
| D+namemerge s012 | 0.500 | 6 | FAIL |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.500 | 2 | FAIL |
| A+namemerge r1 | 0.500 | 2 | FAIL |
| B s0 | 0.500 | 2 | FAIL |
| B+namemerge s0 | 0.500 | 2 | FAIL |
| C s012 | 0.500 | 2 | FAIL |
| C+namemerge s012 | 0.500 | 2 | FAIL |
| D s012 | 0.500 | 2 | FAIL |
| D+namemerge s012 | 0.500 | 2 | FAIL |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.917 | 12 | ok |
| A+namemerge r1 | 0.917 | 12 | ok |
| B s0 | 0.917 | 12 | ok |
| B+namemerge s0 | 0.917 | 12 | ok |
| C s012 | 0.917 | 12 | ok |
| C+namemerge s012 | 0.917 | 12 | ok |
| D s012 | 0.917 | 12 | ok |
| D+namemerge s012 | 0.917 | 12 | ok |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.667 | 9 | FAIL |
| A+namemerge r1 | 0.667 | 9 | FAIL |
| B s0 | 0.889 | 9 | ok |
| B+namemerge s0 | 0.889 | 9 | ok |
| C s012 | 0.778 | 9 | ok |
| C+namemerge s012 | 0.778 | 9 | ok |
| D s012 | 0.000 | 9 | FAIL |
| D+namemerge s012 | 0.000 | 9 | FAIL |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| A r1 | 0 | 9 | ok |
| A+namemerge r1 | 0 | 9 | ok |
| B s0 | 0 | 9 | ok |
| B+namemerge s0 | 0 | 9 | ok |
| C s012 | 0 | 9 | ok |
| C+namemerge s012 | 0 | 9 | ok |
| D s012 | 1 | 9 | ok |
| D+namemerge s012 | 1 | 9 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.895 | 19 | ok |
| A+namemerge r1 | 0.895 | 19 | ok |
| B s0 | 0.895 | 19 | ok |
| B+namemerge s0 | 0.895 | 19 | ok |
| C s012 | 0.895 | 19 | ok |
| C+namemerge s012 | 0.895 | 19 | ok |
| D s012 | 0.895 | 19 | ok |
| D+namemerge s012 | 0.895 | 19 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.571 (before 0.571) | 7 | ok |
| A+namemerge r1 | 0.571 (before 0.571) | 7 | ok |
| B s0 | 0.429 (before 0.571) | 7 | FAIL |
| B+namemerge s0 | 0.429 (before 0.571) | 7 | FAIL |
| C s012 | 0.429 (before 0.571) | 7 | FAIL |
| C+namemerge s012 | 0.429 (before 0.571) | 7 | FAIL |
| D s012 | 0.286 (before 0.571) | 7 | FAIL |
| D+namemerge s012 | 0.286 (before 0.571) | 7 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.571 | 7 |  |
| A+namemerge r1 | 0.571 | 7 |  |
| B s0 | 0.429 | 7 |  |
| B+namemerge s0 | 0.429 | 7 |  |
| C s012 | 0.429 | 7 |  |
| C+namemerge s012 | 0.429 | 7 |  |
| D s012 | 0.286 | 7 |  |
| D+namemerge s012 | 0.286 | 7 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.676 | 183 | ok |
| A+namemerge r1 | 0.676 | 183 | ok |
| B s0 | 0.720 | 183 | ok |
| B+namemerge s0 | 0.720 | 183 | ok |
| C s012 | 0.720 | 183 | ok |
| C+namemerge s012 | 0.720 | 183 | ok |
| D s012 | 0.596 | 183 | FAIL |
| D+namemerge s012 | 0.596 | 183 | FAIL |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 1.000 | 1 |  |
| A+namemerge r1 | 1.000 | 1 |  |
| B s0 | 1.000 | 1 |  |
| B+namemerge s0 | 1.000 | 1 |  |
| C s012 | 1.000 | 1 |  |
| C+namemerge s012 | 1.000 | 1 |  |
| D s012 | 1.000 | 1 |  |
| D+namemerge s012 | 1.000 | 1 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.248 | 5 |  |
| A+namemerge r1 | 0.248 | 5 |  |
| B s0 | 0.233 | 4 |  |
| B+namemerge s0 | 0.233 | 4 |  |
| C s012 | 0.233 | 4 |  |
| C+namemerge s012 | 0.233 | 4 |  |
| D s012 | 0.295 | 5 |  |
| D+namemerge s012 | 0.295 | 5 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.219 | 15 |  |
| A+namemerge r1 | 0.219 | 15 |  |
| B s0 | 0.209 | 13 |  |
| B+namemerge s0 | 0.209 | 13 |  |
| C s012 | 0.162 | 17 |  |
| C+namemerge s012 | 0.162 | 17 |  |
| D s012 | 0.273 | 9 |  |
| D+namemerge s012 | 0.273 | 9 |  |

## Comparison

| measure | target | A r1 | A+namemerge r1 | B s0 | B+namemerge s0 | C s012 | C+namemerge s012 | D s012 | D+namemerge s012 |
|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL |
| merge_frag | >= 0.6 | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL |
| split_done | >= 1.0 | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL |
| split_side | >= 0.7 | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok |
| noise_marked | >= 0.7 | 0.667 FAIL | 0.667 FAIL | 0.889 ok | 0.889 ok | 0.778 ok | 0.778 ok | 0.000 FAIL | 0.000 FAIL |
| noise_kept | <= 2 | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 1 ok | 1 ok |
| place_right | >= 0.8 | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok |
| recall_after | >= before (no loss) | 0.571 ok | 0.571 ok | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.429 FAIL | 0.286 FAIL | 0.286 FAIL |
| recall_after_kept | report only | 0.571 | 0.571 | 0.429 | 0.429 | 0.429 | 0.429 | 0.286 | 0.286 |
| p1_after | >= 0.6 | 0.676 ok | 0.676 ok | 0.720 ok | 0.720 ok | 0.720 ok | 0.720 ok | 0.596 FAIL | 0.596 FAIL |
| sugg_right | report only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.248 | 0.248 | 0.233 | 0.233 | 0.233 | 0.233 | 0.295 | 0.295 |
| j_wrong | report only | 0.219 | 0.219 | 0.209 | 0.209 | 0.162 | 0.162 | 0.273 | 0.273 |

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| A r1 | 0.941 | 17 | 0.667 | 9 | 0.857 | 7 | 1 |
| B s0 | 0.824 | 17 | 0.889 | 9 | 0.750 | 8 | 2 |
| C s012 | 0.765 | 17 | 0.583 | 12 | 0.750 | 8 | 2 |
| D s012 | 1.000 | 8 | 0.000 | 6 | 1.000 | 3 | 0 |
