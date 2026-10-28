# Pilot scores

Pilot entity E1. 29 clusters, 7 gold classes (train).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 1.000 | 1 | ok |
| nohints+namemerge r1 | 1.000 | 1 | ok |
| nohints_long r1 | n/a | 0 |  |
| nohints_long+namemerge r1 | 0.000 | 1 | FAIL |
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
| nohints r1 | 0.500 | 6 | FAIL |
| nohints+namemerge r1 | 0.500 | 6 | FAIL |
| nohints_long r1 | 0.000 | 6 | FAIL |
| nohints_long+namemerge r1 | 1.000 | 6 | ok |
| v2 r1 | 0.500 | 6 | FAIL |
| v2 r2 | 0.500 | 6 | FAIL |
| v2+namemerge r1 | 0.500 | 6 | FAIL |
| v2+namemerge r2 | 0.500 | 6 | FAIL |
| v2_nocontext r1 | 1.000 | 6 | ok |
| v2_nocontext+namemerge r1 | 1.000 | 6 | ok |

## Splits

### Mixed {departure, destination} / {leave at, arrive by} clusters that were split
Target: >= 1.0

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.000 | 2 | FAIL |
| nohints+namemerge r1 | 0.000 | 2 | FAIL |
| nohints_long r1 | 0.000 | 2 | FAIL |
| nohints_long+namemerge r1 | 0.000 | 2 | FAIL |
| v2 r1 | 0.500 | 2 | FAIL |
| v2 r2 | 0.500 | 2 | FAIL |
| v2+namemerge r1 | 0.500 | 2 | FAIL |
| v2+namemerge r2 | 0.500 | 2 | FAIL |
| v2_nocontext r1 | 0.500 | 2 | FAIL |
| v2_nocontext+namemerge r1 | 0.500 | 2 | FAIL |

### Example mentions on the right side of a split
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | n/a | 0 |  |
| nohints_long r1 | n/a | 0 |  |
| nohints_long+namemerge r1 | n/a | 0 |  |
| v2 r1 | 0.917 | 12 | ok |
| v2 r2 | 0.917 | 12 | ok |
| v2+namemerge r1 | 0.917 | 12 | ok |
| v2+namemerge r2 | 0.917 | 12 | ok |
| v2_nocontext r1 | 0.917 | 12 | ok |
| v2_nocontext+namemerge r1 | 0.917 | 12 | ok |

## Noise

### Noise clusters marked not_attribute/unsure
Target: >= 0.7

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 1.000 | 9 | ok |
| nohints+namemerge r1 | 1.000 | 9 | ok |
| nohints_long r1 | 0.889 | 9 | ok |
| nohints_long+namemerge r1 | 0.889 | 9 | ok |
| v2 r1 | 0.667 | 9 | FAIL |
| v2 r2 | 0.778 | 9 | ok |
| v2+namemerge r1 | 0.667 | 9 | FAIL |
| v2+namemerge r2 | 0.778 | 9 | ok |
| v2_nocontext r1 | 0.889 | 9 | ok |
| v2_nocontext+namemerge r1 | 0.889 | 9 | ok |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0 | 9 | ok |
| nohints+namemerge r1 | 0 | 9 | ok |
| nohints_long r1 | 1 | 9 | ok |
| nohints_long+namemerge r1 | 1 | 9 | ok |
| v2 r1 | 0 | 9 | ok |
| v2 r2 | 0 | 9 | ok |
| v2+namemerge r1 | 0 | 9 | ok |
| v2+namemerge r2 | 0 | 9 | ok |
| v2_nocontext r1 | 0 | 9 | ok |
| v2_nocontext+namemerge r1 | 0 | 9 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.895 | 19 | ok |
| nohints+namemerge r1 | 0.895 | 19 | ok |
| nohints_long r1 | 0.895 | 19 | ok |
| nohints_long+namemerge r1 | 0.895 | 19 | ok |
| v2 r1 | 0.895 | 19 | ok |
| v2 r2 | 0.895 | 19 | ok |
| v2+namemerge r1 | 0.895 | 19 | ok |
| v2+namemerge r2 | 0.895 | 19 | ok |
| v2_nocontext r1 | 0.895 | 19 | ok |
| v2_nocontext+namemerge r1 | 0.895 | 19 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.571 (before 0.571) | 7 | ok |
| nohints+namemerge r1 | 0.571 (before 0.571) | 7 | ok |
| nohints_long r1 | 0.571 (before 0.571) | 7 | ok |
| nohints_long+namemerge r1 | 0.429 (before 0.571) | 7 | FAIL |
| v2 r1 | 0.571 (before 0.571) | 7 | ok |
| v2 r2 | 0.429 (before 0.571) | 7 | FAIL |
| v2+namemerge r1 | 0.571 (before 0.571) | 7 | ok |
| v2+namemerge r2 | 0.429 (before 0.571) | 7 | FAIL |
| v2_nocontext r1 | 0.286 (before 0.571) | 7 | FAIL |
| v2_nocontext+namemerge r1 | 0.286 (before 0.571) | 7 | FAIL |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.571 | 7 |  |
| nohints+namemerge r1 | 0.571 | 7 |  |
| nohints_long r1 | 0.571 | 7 |  |
| nohints_long+namemerge r1 | 0.429 | 7 |  |
| v2 r1 | 0.571 | 7 |  |
| v2 r2 | 0.429 | 7 |  |
| v2+namemerge r1 | 0.571 | 7 |  |
| v2+namemerge r2 | 0.429 | 7 |  |
| v2_nocontext r1 | 0.286 | 7 |  |
| v2_nocontext+namemerge r1 | 0.286 | 7 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.707 | 183 | ok |
| nohints+namemerge r1 | 0.707 | 183 | ok |
| nohints_long r1 | 0.713 | 183 | ok |
| nohints_long+namemerge r1 | 0.696 | 183 | ok |
| v2 r1 | 0.676 | 183 | ok |
| v2 r2 | 0.688 | 183 | ok |
| v2+namemerge r1 | 0.676 | 183 | ok |
| v2+namemerge r2 | 0.688 | 183 | ok |
| v2_nocontext r1 | 0.718 | 183 | ok |
| v2_nocontext+namemerge r1 | 0.718 | 183 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | 1.000 | 1 |  |
| nohints_long r1 | n/a | 0 |  |
| nohints_long+namemerge r1 | 1.000 | 2 |  |
| v2 r1 | 1.000 | 1 |  |
| v2 r2 | 1.000 | 1 |  |
| v2+namemerge r1 | 1.000 | 1 |  |
| v2+namemerge r2 | 1.000 | 1 |  |
| v2_nocontext r1 | 1.000 | 2 |  |
| v2_nocontext+namemerge r1 | 1.000 | 2 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.244 | 2 |  |
| nohints+namemerge r1 | 0.244 | 2 |  |
| nohints_long r1 | 0.078 | 9 |  |
| nohints_long+namemerge r1 | 0.197 | 4 |  |
| v2 r1 | 0.248 | 5 |  |
| v2 r2 | 0.221 | 4 |  |
| v2+namemerge r1 | 0.248 | 5 |  |
| v2+namemerge r2 | 0.221 | 4 |  |
| v2_nocontext r1 | 0.182 | 3 |  |
| v2_nocontext+namemerge r1 | 0.182 | 3 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.156 | 16 |  |
| nohints+namemerge r1 | 0.156 | 16 |  |
| nohints_long r1 | 0.114 | 20 |  |
| nohints_long+namemerge r1 | 0.147 | 15 |  |
| v2 r1 | 0.219 | 15 |  |
| v2 r2 | 0.194 | 15 |  |
| v2+namemerge r1 | 0.219 | 15 |  |
| v2+namemerge r2 | 0.194 | 15 |  |
| v2_nocontext r1 | 0.189 | 16 |  |
| v2_nocontext+namemerge r1 | 0.189 | 16 |  |

## Comparison

| measure | target | nohints r1 | nohints+namemerge r1 | nohints_long r1 | nohints_long+namemerge r1 | v2 r1 | v2 r2 | v2+namemerge r1 | v2+namemerge r2 | v2_nocontext r1 | v2_nocontext+namemerge r1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | 1.000 ok | 1.000 ok | n/a | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL |
| merge_frag | >= 0.6 | 0.500 FAIL | 0.500 FAIL | 0.000 FAIL | 1.000 ok | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 1.000 ok | 1.000 ok |
| split_done | >= 1.0 | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.000 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL | 0.500 FAIL |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok | 0.917 ok |
| noise_marked | >= 0.7 | 1.000 ok | 1.000 ok | 0.889 ok | 0.889 ok | 0.667 FAIL | 0.778 ok | 0.667 FAIL | 0.778 ok | 0.889 ok | 0.889 ok |
| noise_kept | <= 2 | 0 ok | 0 ok | 1 ok | 1 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok | 0 ok |
| place_right | >= 0.8 | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok | 0.895 ok |
| recall_after | >= before (no loss) | 0.571 ok | 0.571 ok | 0.571 ok | 0.429 FAIL | 0.571 ok | 0.429 FAIL | 0.571 ok | 0.429 FAIL | 0.286 FAIL | 0.286 FAIL |
| recall_after_kept | report only | 0.571 | 0.571 | 0.571 | 0.429 | 0.571 | 0.429 | 0.571 | 0.429 | 0.286 | 0.286 |
| p1_after | >= 0.6 | 0.707 ok | 0.707 ok | 0.713 ok | 0.696 ok | 0.676 ok | 0.688 ok | 0.676 ok | 0.688 ok | 0.718 ok | 0.718 ok |
| sugg_right | report only | n/a | 1.000 | n/a | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.244 | 0.244 | 0.078 | 0.197 | 0.248 | 0.221 | 0.248 | 0.221 | 0.182 | 0.182 |
| j_wrong | report only | 0.156 | 0.156 | 0.114 | 0.147 | 0.219 | 0.194 | 0.219 | 0.194 | 0.189 | 0.189 |

## Context (v2 r1 vs v2_nocontext r1)

Expected: clearly lower without context.

| measure | v2 | v2_nocontext | delta |
|---|---|---|---|
| merge_pure | 0.000 | 0.000 | 0.000 |
| merge_frag | 0.500 | 1.000 | 0.500 |
| split_done | 0.500 | 0.500 | 0.000 |
| split_side | 0.917 | 0.917 | 0.000 |
| noise_marked | 0.667 | 0.889 | 0.222 |
| noise_kept | 0.000 | 0.000 | 0.000 |
| place_right | 0.895 | 0.895 | 0.000 |
| recall_after | 0.571 | 0.286 | -0.286 |
| recall_after_kept | 0.571 | 0.286 | -0.286 |
| p1_after | 0.676 | 0.718 | 0.041 |
| sugg_right | 1.000 | 1.000 | 0.000 |
| j_right | 0.248 | 0.182 | -0.066 |
| j_wrong | 0.219 | 0.189 | -0.029 |

## Stability (v2 r1 vs r2, report only)

Clusters with a different action, merge_with or name: 0.621 (n=29)

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| nohints r1 | 0.889 | 9 | 1.000 | 9 | 0.750 | 4 | 0 |
| nohints_long r1 | 0.900 | 20 | 0.889 | 9 | 0.917 | 12 | 1 |
| v2 r1 | 0.941 | 17 | 0.667 | 9 | 0.857 | 7 | 1 |
| v2 r2 | 0.938 | 16 | 0.700 | 10 | 0.857 | 7 | 1 |
| v2_nocontext r1 | 0.812 | 16 | 0.667 | 12 | 0.714 | 7 | 2 |
