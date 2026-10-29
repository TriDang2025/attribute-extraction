# Pilot scores

Pilot entity E2. 57 clusters, 12 gold classes (restaurant, taxi).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.000 | 1 | FAIL |
| A+namemerge r1 | 0.000 | 1 | FAIL |
| B s0 | 0.000 | 2 | FAIL |
| B+namemerge s0 | 0.000 | 2 | FAIL |
| C s012 | 0.500 | 2 | FAIL |
| C+namemerge s012 | 0.500 | 2 | FAIL |
| D s012 | 0.500 | 2 | FAIL |
| D+namemerge s012 | 0.500 | 2 | FAIL |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.987 | 79 | ok |
| A+namemerge r1 | 0.987 | 79 | ok |
| B s0 | 0.380 | 79 | FAIL |
| B+namemerge s0 | 0.380 | 79 | FAIL |
| C s012 | 0.380 | 79 | FAIL |
| C+namemerge s012 | 0.380 | 79 | FAIL |
| D s012 | 0.380 | 79 | FAIL |
| D+namemerge s012 | 0.380 | 79 | FAIL |

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
| A r1 | 0.125 | 8 | FAIL |
| A+namemerge r1 | 0.125 | 8 | FAIL |
| B s0 | 0.125 | 8 | FAIL |
| B+namemerge s0 | 0.125 | 8 | FAIL |
| C s012 | 0.125 | 8 | FAIL |
| C+namemerge s012 | 0.125 | 8 | FAIL |
| D s012 | 0.125 | 8 | FAIL |
| D+namemerge s012 | 0.125 | 8 | FAIL |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| A r1 | 1 | 8 | ok |
| A+namemerge r1 | 1 | 8 | ok |
| B s0 | 2 | 8 | ok |
| B+namemerge s0 | 2 | 8 | ok |
| C s012 | 2 | 8 | ok |
| C+namemerge s012 | 2 | 8 | ok |
| D s012 | 1 | 8 | ok |
| D+namemerge s012 | 1 | 8 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.964 | 28 | ok |
| A+namemerge r1 | 0.964 | 28 | ok |
| B s0 | 0.964 | 28 | ok |
| B+namemerge s0 | 0.964 | 28 | ok |
| C s012 | 0.964 | 28 | ok |
| C+namemerge s012 | 0.964 | 28 | ok |
| D s012 | 0.964 | 28 | ok |
| D+namemerge s012 | 0.964 | 28 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.500 (before 0.667) | 12 | FAIL |
| A+namemerge r1 | 0.500 (before 0.667) | 12 | FAIL |
| B s0 | 0.583 (before 0.667) | 12 | FAIL |
| B+namemerge s0 | 0.583 (before 0.667) | 12 | FAIL |
| C s012 | 0.667 (before 0.667) | 12 | ok |
| C+namemerge s012 | 0.667 (before 0.667) | 12 | ok |
| D s012 | 0.417 (before 0.667) | 12 | FAIL |
| D+namemerge s012 | 0.417 (before 0.667) | 12 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.417 | 12 |  |
| A+namemerge r1 | 0.417 | 12 |  |
| B s0 | 0.500 | 12 |  |
| B+namemerge s0 | 0.500 | 12 |  |
| C s012 | 0.500 | 12 |  |
| C+namemerge s012 | 0.500 | 12 |  |
| D s012 | 0.417 | 12 |  |
| D+namemerge s012 | 0.417 | 12 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.734 | 154 | ok |
| A+namemerge r1 | 0.734 | 154 | ok |
| B s0 | 0.667 | 154 | ok |
| B+namemerge s0 | 0.667 | 154 | ok |
| C s012 | 0.671 | 154 | ok |
| C+namemerge s012 | 0.671 | 154 | ok |
| D s012 | 0.630 | 154 | ok |
| D+namemerge s012 | 0.630 | 154 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 1.000 | 3 |  |
| A+namemerge r1 | 1.000 | 3 |  |
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
| A r1 | 0.270 | 10 |  |
| A+namemerge r1 | 0.270 | 10 |  |
| B s0 | 0.220 | 12 |  |
| B+namemerge s0 | 0.220 | 12 |  |
| C s012 | 0.226 | 11 |  |
| C+namemerge s012 | 0.226 | 11 |  |
| D s012 | 0.191 | 9 |  |
| D+namemerge s012 | 0.191 | 9 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| A r1 | 0.156 | 15 |  |
| A+namemerge r1 | 0.156 | 15 |  |
| B s0 | 0.122 | 20 |  |
| B+namemerge s0 | 0.143 | 17 |  |
| C s012 | 0.128 | 20 |  |
| C+namemerge s012 | 0.142 | 18 |  |
| D s012 | 0.209 | 11 |  |
| D+namemerge s012 | 0.209 | 11 |  |

## Comparison

| measure | target | A r1 | A+namemerge r1 | B s0 | B+namemerge s0 | C s012 | C+namemerge s012 | D s012 | D+namemerge s012 |
|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL |
| merge_frag | >= 0.6 | 0.987 ok | 0.987 ok | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL | 0.380 FAIL |
| split_done | >= 1.0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| noise_marked | >= 0.7 | 0.125 FAIL | 0.125 FAIL | 0.125 FAIL | 0.125 FAIL | 0.125 FAIL | 0.125 FAIL | 0.125 FAIL | 0.125 FAIL |
| noise_kept | <= 2 | 1 ok | 1 ok | 2 ok | 2 ok | 2 ok | 2 ok | 1 ok | 1 ok |
| place_right | >= 0.8 | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok |
| recall_after | >= before (no loss) | 0.500 FAIL | 0.500 FAIL | 0.583 FAIL | 0.583 FAIL | 0.667 ok | 0.667 ok | 0.417 FAIL | 0.417 FAIL |
| recall_after_kept | report only | 0.417 | 0.417 | 0.500 | 0.500 | 0.500 | 0.500 | 0.417 | 0.417 |
| p1_after | >= 0.6 | 0.734 ok | 0.734 ok | 0.667 ok | 0.667 ok | 0.671 ok | 0.671 ok | 0.630 ok | 0.630 ok |
| sugg_right | report only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.270 | 0.270 | 0.220 | 0.220 | 0.226 | 0.226 | 0.191 | 0.191 |
| j_wrong | report only | 0.156 | 0.156 | 0.122 | 0.143 | 0.128 | 0.142 | 0.209 | 0.209 |

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| A r1 | 0.826 | 23 | 0.200 | 5 | 0.000 | 2 | 0 |
| B s0 | 0.852 | 27 | 0.143 | 7 | 0.500 | 2 | 0 |
| C s012 | 0.786 | 28 | 0.143 | 7 | 0.000 | 3 | 0 |
| D s012 | 0.941 | 17 | 0.200 | 5 | 1.000 | 2 | 0 |
