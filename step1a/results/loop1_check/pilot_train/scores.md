# Pilot scores

Pilot entity E1. 29 clusters, 7 train gold classes.

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| full r1 | n/a | 0 |  |
| full r2 | n/a | 0 |  |
| nocontext r1 | n/a | 0 |  |
| nohints r1 | 1.000 | 1 | ok |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.000 | 6 | FAIL |
| full r2 | 0.000 | 6 | FAIL |
| nocontext r1 | 0.000 | 6 | FAIL |
| nohints r1 | 0.500 | 6 | FAIL |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.000 | 2 | FAIL |
| full r2 | 0.000 | 2 | FAIL |
| nocontext r1 | 0.000 | 2 | FAIL |
| nohints r1 | 0.000 | 2 | FAIL |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| full r1 | n/a | 0 |  |
| full r2 | n/a | 0 |  |
| nocontext r1 | n/a | 0 |  |
| nohints r1 | n/a | 0 |  |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.000 | 9 | FAIL |
| full r2 | 0.000 | 9 | FAIL |
| nocontext r1 | 0.111 | 9 | FAIL |
| nohints r1 | 1.000 | 9 | ok |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| full r1 | 9 | 9 | FAIL |
| full r2 | 9 | 9 | FAIL |
| nocontext r1 | 8 | 9 | FAIL |
| nohints r1 | 0 | 9 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.895 | 19 | ok |
| full r2 | 0.895 | 19 | ok |
| nocontext r1 | 0.895 | 19 | ok |
| nohints r1 | 0.895 | 19 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.571 (before 0.571) | 7 | ok |
| full r2 | 0.571 (before 0.571) | 7 | ok |
| nocontext r1 | 0.571 (before 0.571) | 7 | ok |
| nohints r1 | 0.571 (before 0.571) | 7 | ok |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.571 | 7 |  |
| full r2 | 0.571 | 7 |  |
| nocontext r1 | 0.571 | 7 |  |
| nohints r1 | 0.571 | 7 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.713 | 183 | ok |
| full r2 | 0.713 | 183 | ok |
| nocontext r1 | 0.713 | 183 | ok |
| nohints r1 | 0.707 | 183 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| full r1 | n/a | 0 |  |
| full r2 | n/a | 0 |  |
| nocontext r1 | n/a | 0 |  |
| nohints r1 | n/a | 0 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.167 | 11 |  |
| full r2 | 0.167 | 11 |  |
| nocontext r1 | 0.326 | 2 |  |
| nohints r1 | 0.361 | 4 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| full r1 | 0.083 | 18 |  |
| full r2 | 0.083 | 18 |  |
| nocontext r1 | 0.093 | 27 |  |
| nohints r1 | 0.110 | 14 |  |

## Comparison

| measure | target | full r1 | full r2 | nocontext r1 | nohints r1 |
|---|---|---|---|---|---|
| merge_pure | >= 0.8 | n/a | n/a | n/a | 1.000 ok |
| merge_frag | >= 0.6 | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.500 FAIL |
| split_done | >= 1.0 | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a |
| noise_marked | >= 0.7 | 0.000 FAIL | 0.000 FAIL | 0.111 FAIL | 1.000 ok |
| noise_kept | <= 2 | 9 FAIL | 9 FAIL | 8 FAIL | 0 ok |
| place_right | >= 0.8 | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok |
| recall_after | >= before (no loss) | 0.571 ok | 0.571 ok | 0.571 ok | 0.571 ok |
| recall_after_kept | report only | 0.571 | 0.571 | 0.571 | 0.571 |
| p1_after | >= 0.6 | 0.713 ok | 0.713 ok | 0.713 ok | 0.707 ok |
| sugg_right | report only | n/a | n/a | n/a | n/a |
| j_right | report only | 0.167 | 0.167 | 0.326 | 0.361 |
| j_wrong | report only | 0.083 | 0.083 | 0.093 | 0.110 |

## Context (full r1 vs nocontext r1)

Expected: clearly lower without context.

| measure | full | nocontext | delta |
|---|---|---|---|
| merge_pure | n/a | n/a | n/a |
| merge_frag | 0.000 | 0.000 | 0.000 |
| split_done | 0.000 | 0.000 | 0.000 |
| split_side | n/a | n/a | n/a |
| noise_marked | 0.000 | 0.111 | 0.111 |
| noise_kept | 9.000 | 8.000 | -1.000 |
| place_right | 0.895 | 0.895 | 0.000 |
| recall_after | 0.571 | 0.571 | 0.000 |
| recall_after_kept | 0.571 | 0.571 | 0.000 |
| p1_after | 0.713 | 0.713 | 0.000 |
| sugg_right | n/a | n/a | n/a |
| j_right | 0.167 | 0.326 | 0.159 |
| j_wrong | 0.083 | 0.093 | 0.009 |

## Stability (full r1 vs r2, report only)

Clusters with a different action, merge_with or name: 0.000 (n=29)
