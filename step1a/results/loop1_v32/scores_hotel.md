# Pilot scores

Pilot entity E0. 31 clusters, 11 gold classes (hotel).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| A r1 | 1.000 | 1 | ok |
| A+namemerge r1 | 1.000 | 1 | ok |
| B s0 | 1.000 | 1 | ok |
| B+namemerge s0 | 1.000 | 1 | ok |
| C s012 | 1.000 | 1 | ok |
| C+namemerge s012 | 1.000 | 1 | ok |
| D s012 | 1.000 | 1 | ok |
| D+namemerge s012 | 1.000 | 1 | ok |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| A r1 | 1.000 | 10 | ok |
| A+namemerge r1 | 1.000 | 10 | ok |
| B s0 | 0.600 | 10 | ok |
| B+namemerge s0 | 0.600 | 10 | ok |
| C s012 | 0.600 | 10 | ok |
| C+namemerge s012 | 0.600 | 10 | ok |
| D s012 | 0.600 | 10 | ok |
| D+namemerge s012 | 0.600 | 10 | ok |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| A r1 | n/a | 0 |  |
| A+namemerge r1 | n/a | 0 |  |
| B s0 | n/a | 0 |  |
| B+namemerge s0 | n/a | 0 |  |
| C s012 | n/a | 0 |  |
| C+namemerge s012 | n/a | 0 |  |
| D s012 | n/a | 0 |  |
| D+namemerge s012 | n/a | 0 |  |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| A r1 | n/a | 0 |  |
| A+namemerge r1 | n/a | 0 |  |
| B s0 | n/a | 0 |  |
| B+namemerge s0 | n/a | 0 |  |
| C s012 | n/a | 0 |  |
| C+namemerge s012 | n/a | 0 |  |
| D s012 | n/a | 0 |  |
| D+namemerge s012 | n/a | 0 |  |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.417 | 12 | FAIL |
| A+namemerge r1 | 0.417 | 12 | FAIL |
| B s0 | 0.333 | 12 | FAIL |
| B+namemerge s0 | 0.333 | 12 | FAIL |
| C s012 | 0.417 | 12 | FAIL |
| C+namemerge s012 | 0.417 | 12 | FAIL |
| D s012 | 0.083 | 12 | FAIL |
| D+namemerge s012 | 0.083 | 12 | FAIL |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| A r1 | 0 | 12 | ok |
| A+namemerge r1 | 0 | 12 | ok |
| B s0 | 1 | 12 | ok |
| B+namemerge s0 | 1 | 12 | ok |
| C s012 | 1 | 12 | ok |
| C+namemerge s012 | 1 | 12 | ok |
| D s012 | 2 | 12 | ok |
| D+namemerge s012 | 2 | 12 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| A r1 | 1.000 | 20 | ok |
| A+namemerge r1 | 1.000 | 20 | ok |
| B s0 | 1.000 | 20 | ok |
| B+namemerge s0 | 1.000 | 20 | ok |
| C s012 | 1.000 | 20 | ok |
| C+namemerge s012 | 1.000 | 20 | ok |
| D s012 | 1.000 | 20 | ok |
| D+namemerge s012 | 1.000 | 20 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.727 (before 0.455) | 11 | ok |
| A+namemerge r1 | 0.727 (before 0.455) | 11 | ok |
| B s0 | 0.727 (before 0.455) | 11 | ok |
| B+namemerge s0 | 0.727 (before 0.455) | 11 | ok |
| C s012 | 0.727 (before 0.455) | 11 | ok |
| C+namemerge s012 | 0.727 (before 0.455) | 11 | ok |
| D s012 | 0.545 (before 0.455) | 11 | ok |
| D+namemerge s012 | 0.545 (before 0.455) | 11 | ok |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.727 | 11 |  |
| A+namemerge r1 | 0.727 | 11 |  |
| B s0 | 0.727 | 11 |  |
| B+namemerge s0 | 0.727 | 11 |  |
| C s012 | 0.727 | 11 |  |
| C+namemerge s012 | 0.727 | 11 |  |
| D s012 | 0.545 | 11 |  |
| D+namemerge s012 | 0.545 | 11 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.882 | 116 | ok |
| A+namemerge r1 | 0.882 | 116 | ok |
| B s0 | 0.881 | 116 | ok |
| B+namemerge s0 | 0.881 | 116 | ok |
| C s012 | 0.880 | 116 | ok |
| C+namemerge s012 | 0.880 | 116 | ok |
| D s012 | 0.906 | 116 | ok |
| D+namemerge s012 | 0.906 | 116 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 1.000 | 4 |  |
| A+namemerge r1 | 1.000 | 4 |  |
| B s0 | 1.000 | 3 |  |
| B+namemerge s0 | 1.000 | 3 |  |
| C s012 | 1.000 | 3 |  |
| C+namemerge s012 | 1.000 | 3 |  |
| D s012 | 1.000 | 3 |  |
| D+namemerge s012 | 1.000 | 3 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.227 | 11 |  |
| A+namemerge r1 | 0.227 | 11 |  |
| B s0 | 0.207 | 12 |  |
| B+namemerge s0 | 0.207 | 12 |  |
| C s012 | 0.207 | 12 |  |
| C+namemerge s012 | 0.207 | 12 |  |
| D s012 | 0.265 | 9 |  |
| D+namemerge s012 | 0.265 | 9 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.171 | 13 |  |
| A+namemerge r1 | 0.171 | 13 |  |
| B s0 | 0.168 | 13 |  |
| B+namemerge s0 | 0.168 | 13 |  |
| C s012 | 0.168 | 13 |  |
| C+namemerge s012 | 0.168 | 13 |  |
| D s012 | 0.194 | 12 |  |
| D+namemerge s012 | 0.194 | 12 |  |

## Comparison

| measure | target | A r1 | A+namemerge r1 | B s0 | B+namemerge s0 | C s012 | C+namemerge s012 | D s012 | D+namemerge s012 |
|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| merge_frag | >= 0.6 | 1.000 ok | 1.000 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok | 0.600 ok |
| split_done | >= 1.0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| noise_marked | >= 0.7 | 0.417 FAIL | 0.417 FAIL | 0.333 FAIL | 0.333 FAIL | 0.417 FAIL | 0.417 FAIL | 0.083 FAIL | 0.083 FAIL |
| noise_kept | <= 2 | 0 ok | 0 ok | 1 ok | 1 ok | 1 ok | 1 ok | 2 ok | 2 ok |
| place_right | >= 0.8 | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| recall_after | >= before (no loss) | 0.727 ok | 0.727 ok | 0.727 ok | 0.727 ok | 0.727 ok | 0.727 ok | 0.545 ok | 0.545 ok |
| recall_after_kept | report only | 0.727 | 0.727 | 0.727 | 0.727 | 0.727 | 0.727 | 0.545 | 0.545 |
| p1_after | >= 0.6 | 0.882 ok | 0.882 ok | 0.881 ok | 0.881 ok | 0.880 ok | 0.880 ok | 0.906 ok | 0.906 ok |
| sugg_right | report only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.227 | 0.227 | 0.207 | 0.207 | 0.207 | 0.207 | 0.265 | 0.265 |
| j_wrong | report only | 0.171 | 0.171 | 0.168 | 0.168 | 0.168 | 0.168 | 0.194 | 0.194 |

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| A r1 | 0.786 | 14 | 0.333 | 15 | n/a | 0 | 0 |
| B s0 | 0.647 | 17 | 0.267 | 15 | n/a | 0 | 0 |
| C s012 | 0.647 | 17 | 0.312 | 16 | n/a | 0 | 0 |
| D s012 | 0.909 | 11 | 0.091 | 11 | n/a | 0 | 0 |
