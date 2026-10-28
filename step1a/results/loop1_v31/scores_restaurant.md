# Pilot scores

Pilot entity E2. 57 clusters, 12 gold classes (restaurant, taxi).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | 0.500 | 2 | FAIL |
| v2 r1 | 0.000 | 1 | FAIL |
| v2 r2 | 0.000 | 1 | FAIL |
| v2+namemerge r1 | 0.000 | 1 | FAIL |
| v2+namemerge r2 | 0.000 | 1 | FAIL |
| v2_nocontext r1 | 0.000 | 1 | FAIL |
| v2_nocontext+namemerge r1 | 0.000 | 1 | FAIL |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.000 | 79 | FAIL |
| nohints+namemerge r1 | 0.456 | 79 | FAIL |
| v2 r1 | 0.987 | 79 | ok |
| v2 r2 | 1.000 | 79 | ok |
| v2+namemerge r1 | 0.987 | 79 | ok |
| v2+namemerge r2 | 1.000 | 79 | ok |
| v2_nocontext r1 | 1.000 | 79 | ok |
| v2_nocontext+namemerge r1 | 1.000 | 79 | ok |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | n/a | 0 |  |
| v2 r1 | n/a | 0 |  |
| v2 r2 | n/a | 0 |  |
| v2+namemerge r1 | n/a | 0 |  |
| v2+namemerge r2 | n/a | 0 |  |
| v2_nocontext r1 | n/a | 0 |  |
| v2_nocontext+namemerge r1 | n/a | 0 |  |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | n/a | 0 |  |
| v2 r1 | n/a | 0 |  |
| v2 r2 | n/a | 0 |  |
| v2+namemerge r1 | n/a | 0 |  |
| v2+namemerge r2 | n/a | 0 |  |
| v2_nocontext r1 | n/a | 0 |  |
| v2_nocontext+namemerge r1 | n/a | 0 |  |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.000 | 8 | FAIL |
| nohints+namemerge r1 | 0.000 | 8 | FAIL |
| v2 r1 | 0.125 | 8 | FAIL |
| v2 r2 | 0.250 | 8 | FAIL |
| v2+namemerge r1 | 0.125 | 8 | FAIL |
| v2+namemerge r2 | 0.250 | 8 | FAIL |
| v2_nocontext r1 | 0.250 | 8 | FAIL |
| v2_nocontext+namemerge r1 | 0.250 | 8 | FAIL |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 8 | 8 | FAIL |
| nohints+namemerge r1 | 7 | 8 | FAIL |
| v2 r1 | 1 | 8 | ok |
| v2 r2 | 1 | 8 | ok |
| v2+namemerge r1 | 1 | 8 | ok |
| v2+namemerge r2 | 1 | 8 | ok |
| v2_nocontext r1 | 3 | 8 | FAIL |
| v2_nocontext+namemerge r1 | 3 | 8 | FAIL |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.964 | 28 | ok |
| nohints+namemerge r1 | 0.964 | 28 | ok |
| v2 r1 | 0.964 | 28 | ok |
| v2 r2 | 0.964 | 28 | ok |
| v2+namemerge r1 | 0.964 | 28 | ok |
| v2+namemerge r2 | 0.964 | 28 | ok |
| v2_nocontext r1 | 0.964 | 28 | ok |
| v2_nocontext+namemerge r1 | 0.964 | 28 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.667 (before 0.667) | 12 | ok |
| nohints+namemerge r1 | 0.583 (before 0.667) | 12 | FAIL |
| v2 r1 | 0.500 (before 0.667) | 12 | FAIL |
| v2 r2 | 0.333 (before 0.667) | 12 | FAIL |
| v2+namemerge r1 | 0.500 (before 0.667) | 12 | FAIL |
| v2+namemerge r2 | 0.333 (before 0.667) | 12 | FAIL |
| v2_nocontext r1 | 0.500 (before 0.667) | 12 | FAIL |
| v2_nocontext+namemerge r1 | 0.500 (before 0.667) | 12 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.667 | 12 |  |
| nohints+namemerge r1 | 0.583 | 12 |  |
| v2 r1 | 0.417 | 12 |  |
| v2 r2 | 0.167 | 12 |  |
| v2+namemerge r1 | 0.417 | 12 |  |
| v2+namemerge r2 | 0.167 | 12 |  |
| v2_nocontext r1 | 0.500 | 12 |  |
| v2_nocontext+namemerge r1 | 0.500 | 12 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.696 | 154 | ok |
| nohints+namemerge r1 | 0.649 | 154 | ok |
| v2 r1 | 0.734 | 154 | ok |
| v2 r2 | 0.727 | 154 | ok |
| v2+namemerge r1 | 0.734 | 154 | ok |
| v2+namemerge r2 | 0.727 | 154 | ok |
| v2_nocontext r1 | 0.734 | 154 | ok |
| v2_nocontext+namemerge r1 | 0.734 | 154 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | 1.000 | 1 |  |
| v2 r1 | 1.000 | 3 |  |
| v2 r2 | 0.750 | 4 |  |
| v2+namemerge r1 | 1.000 | 3 |  |
| v2+namemerge r2 | 0.750 | 4 |  |
| v2_nocontext r1 | 0.750 | 4 |  |
| v2_nocontext+namemerge r1 | 0.750 | 4 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.251 | 5 |  |
| nohints+namemerge r1 | 0.255 | 5 |  |
| v2 r1 | 0.183 | 10 |  |
| v2 r2 | 0.183 | 5 |  |
| v2+namemerge r1 | 0.183 | 10 |  |
| v2+namemerge r2 | 0.183 | 5 |  |
| v2_nocontext r1 | 0.215 | 10 |  |
| v2_nocontext+namemerge r1 | 0.215 | 10 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.031 | 52 |  |
| nohints+namemerge r1 | 0.076 | 21 |  |
| v2 r1 | 0.132 | 15 |  |
| v2 r2 | 0.139 | 12 |  |
| v2+namemerge r1 | 0.132 | 15 |  |
| v2+namemerge r2 | 0.139 | 12 |  |
| v2_nocontext r1 | 0.111 | 17 |  |
| v2_nocontext+namemerge r1 | 0.111 | 17 |  |

## Comparison

| measure | target | nohints r1 | nohints+namemerge r1 | v2 r1 | v2 r2 | v2+namemerge r1 | v2+namemerge r2 | v2_nocontext r1 | v2_nocontext+namemerge r1 |
|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | n/a | 0.500 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL |
| merge_frag | >= 0.6 | 0.000 FAIL | 0.456 FAIL | 0.987 ok | 1.000 ok | 0.987 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| split_done | >= 1.0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| noise_marked | >= 0.7 | 0.000 FAIL | 0.000 FAIL | 0.125 FAIL | 0.250 FAIL | 0.125 FAIL | 0.250 FAIL | 0.250 FAIL | 0.250 FAIL |
| noise_kept | <= 2 | 8 FAIL | 7 FAIL | 1 ok | 1 ok | 1 ok | 1 ok | 3 FAIL | 3 FAIL |
| place_right | >= 0.8 | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok | 0.964 ok |
| recall_after | >= before (no loss) | 0.667 ok | 0.583 FAIL | 0.500 FAIL | 0.333 FAIL | 0.500 FAIL | 0.333 FAIL | 0.500 FAIL | 0.500 FAIL |
| recall_after_kept | report only | 0.667 | 0.583 | 0.417 | 0.167 | 0.417 | 0.167 | 0.500 | 0.500 |
| p1_after | >= 0.6 | 0.696 ok | 0.649 ok | 0.734 ok | 0.727 ok | 0.734 ok | 0.727 ok | 0.734 ok | 0.734 ok |
| sugg_right | report only | n/a | 1.000 | 1.000 | 0.750 | 1.000 | 0.750 | 0.750 | 0.750 |
| j_right | report only | 0.251 | 0.255 | 0.183 | 0.183 | 0.183 | 0.183 | 0.215 | 0.215 |
| j_wrong | report only | 0.031 | 0.076 | 0.132 | 0.139 | 0.132 | 0.139 | 0.111 | 0.111 |

## Context (v2 r1 vs v2_nocontext r1)

Expected: clearly lower without context.

| measure | v2 | v2_nocontext | delta |
|---|---|---|---|
| merge_pure | 0.000 | 0.000 | 0.000 |
| merge_frag | 0.987 | 1.000 | 0.013 |
| split_done | n/a | n/a | n/a |
| split_side | n/a | n/a | n/a |
| noise_marked | 0.125 | 0.250 | 0.125 |
| noise_kept | 1.000 | 3.000 | 2.000 |
| place_right | 0.964 | 0.964 | 0.000 |
| recall_after | 0.500 | 0.500 | 0.000 |
| recall_after_kept | 0.417 | 0.500 | 0.083 |
| p1_after | 0.734 | 0.734 | 0.000 |
| sugg_right | 1.000 | 0.750 | -0.250 |
| j_right | 0.183 | 0.215 | 0.032 |
| j_wrong | 0.132 | 0.111 | -0.021 |

## Stability (v2 r1 vs r2, report only)

Clusters with a different action, merge_with or name: 0.807 (n=57)

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| nohints r1 | 0.918 | 49 | 0.000 | 8 | 0.250 | 4 | 0 |
| v2 r1 | 0.826 | 23 | 0.200 | 5 | 0.000 | 2 | 0 |
| v2 r2 | 0.611 | 18 | 0.333 | 6 | n/a | 0 | 0 |
| v2_nocontext r1 | 0.783 | 23 | 0.222 | 9 | n/a | 0 | 0 |
