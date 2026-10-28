# Pilot scores

Pilot entity E0. 31 clusters, 11 gold classes (hotel).

## Merges

### Merge groups whose gold-labelled clusters share one gold_attr
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | 1.000 | 1 | ok |
| v2 r1 | 1.000 | 1 | ok |
| v2 r2 | 1.000 | 1 | ok |
| v2+namemerge r1 | 1.000 | 1 | ok |
| v2+namemerge r2 | 1.000 | 1 | ok |
| v2_nocontext r1 | 1.000 | 1 | ok |
| v2_nocontext+namemerge r1 | 1.000 | 1 | ok |

### Same-class fragment pairs that were merged
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.000 | 10 | FAIL |
| nohints+namemerge r1 | 0.600 | 10 | ok |
| v2 r1 | 1.000 | 10 | ok |
| v2 r2 | 1.000 | 10 | ok |
| v2+namemerge r1 | 1.000 | 10 | ok |
| v2+namemerge r2 | 1.000 | 10 | ok |
| v2_nocontext r1 | 1.000 | 10 | ok |
| v2_nocontext+namemerge r1 | 1.000 | 10 | ok |

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
| nohints r1 | 0.000 | 12 | FAIL |
| nohints+namemerge r1 | 0.000 | 12 | FAIL |
| v2 r1 | 0.417 | 12 | FAIL |
| v2 r2 | 0.333 | 12 | FAIL |
| v2+namemerge r1 | 0.417 | 12 | FAIL |
| v2+namemerge r2 | 0.333 | 12 | FAIL |
| v2_nocontext r1 | 0.667 | 12 | FAIL |
| v2_nocontext+namemerge r1 | 0.667 | 12 | FAIL |

### Noise clusters given keep + a name (count)
Target: <= 2

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 8 | 12 | FAIL |
| nohints+namemerge r1 | 3 | 12 | FAIL |
| v2 r1 | 0 | 12 | ok |
| v2 r2 | 1 | 12 | ok |
| v2+namemerge r1 | 0 | 12 | ok |
| v2+namemerge r2 | 1 | 12 | ok |
| v2_nocontext r1 | 0 | 12 | ok |
| v2_nocontext+namemerge r1 | 0 | 12 | ok |

## Placement

### Clusters placed in the right entity
Target: >= 0.8

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 1.000 | 20 | ok |
| nohints+namemerge r1 | 1.000 | 20 | ok |
| v2 r1 | 1.000 | 20 | ok |
| v2 r2 | 1.000 | 20 | ok |
| v2+namemerge r1 | 1.000 | 20 | ok |
| v2+namemerge r2 | 1.000 | 20 | ok |
| v2_nocontext r1 | 1.000 | 20 | ok |
| v2_nocontext+namemerge r1 | 1.000 | 20 | ok |

## Train attributes

### Strict recall over train gold classes, after (before in the note)
Target: >= before (no loss)

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.455 (before 0.455) | 11 | ok |
| nohints+namemerge r1 | 0.455 (before 0.455) | 11 | ok |
| v2 r1 | 0.727 (before 0.455) | 11 | ok |
| v2 r2 | 0.727 (before 0.455) | 11 | ok |
| v2+namemerge r1 | 0.727 (before 0.455) | 11 | ok |
| v2+namemerge r2 | 0.727 (before 0.455) | 11 | ok |
| v2_nocontext r1 | 0.727 (before 0.455) | 11 | ok |
| v2_nocontext+namemerge r1 | 0.727 (before 0.455) | 11 | ok |

### Same, marked attributes removed
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.455 | 11 |  |
| nohints+namemerge r1 | 0.455 | 11 |  |
| v2 r1 | 0.727 | 11 |  |
| v2 r2 | 0.727 | 11 |  |
| v2+namemerge r1 | 0.727 | 11 |  |
| v2+namemerge r2 | 0.727 | 11 |  |
| v2_nocontext r1 | 0.727 | 11 |  |
| v2_nocontext+namemerge r1 | 0.727 | 11 |  |

### One-to-one precision after
Target: >= 0.6

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.788 | 116 | ok |
| nohints+namemerge r1 | 0.795 | 116 | ok |
| v2 r1 | 0.882 | 116 | ok |
| v2 r2 | 0.883 | 116 | ok |
| v2+namemerge r1 | 0.882 | 116 | ok |
| v2+namemerge r2 | 0.883 | 116 | ok |
| v2_nocontext r1 | 0.891 | 116 | ok |
| v2_nocontext+namemerge r1 | 0.891 | 116 | ok |

## Suggestions

### Followed merge hints that were right (report only)
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | n/a | 0 |  |
| nohints+namemerge r1 | 1.000 | 2 |  |
| v2 r1 | 1.000 | 4 |  |
| v2 r2 | 1.000 | 4 |  |
| v2+namemerge r1 | 1.000 | 4 |  |
| v2+namemerge r2 | 1.000 | 4 |  |
| v2_nocontext r1 | 1.000 | 4 |  |
| v2_nocontext+namemerge r1 | 1.000 | 4 |  |

## Verification

### Mean Jaccard of right names
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.294 | 6 |  |
| nohints+namemerge r1 | 0.294 | 6 |  |
| v2 r1 | 0.153 | 11 |  |
| v2 r2 | 0.144 | 10 |  |
| v2+namemerge r1 | 0.153 | 11 |  |
| v2+namemerge r2 | 0.144 | 10 |  |
| v2_nocontext r1 | 0.188 | 11 |  |
| v2_nocontext+namemerge r1 | 0.188 | 11 |  |

### Mean Jaccard of wrong names
Target: report only

| response | value | n | status |
|---|---|---|---|
| nohints r1 | 0.082 | 20 |  |
| nohints+namemerge r1 | 0.137 | 12 |  |
| v2 r1 | 0.171 | 13 |  |
| v2 r2 | 0.163 | 15 |  |
| v2+namemerge r1 | 0.171 | 13 |  |
| v2+namemerge r2 | 0.163 | 15 |  |
| v2_nocontext r1 | 0.130 | 9 |  |
| v2_nocontext+namemerge r1 | 0.130 | 9 |  |

## Comparison

| measure | target | nohints r1 | nohints+namemerge r1 | v2 r1 | v2 r2 | v2+namemerge r1 | v2+namemerge r2 | v2_nocontext r1 | v2_nocontext+namemerge r1 |
|---|---|---|---|---|---|---|---|---|---|
| merge_pure | >= 0.8 | n/a | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| merge_frag | >= 0.6 | 0.000 FAIL | 0.600 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| split_done | >= 1.0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| split_side | >= 0.7 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| noise_marked | >= 0.7 | 0.000 FAIL | 0.000 FAIL | 0.417 FAIL | 0.333 FAIL | 0.417 FAIL | 0.333 FAIL | 0.667 FAIL | 0.667 FAIL |
| noise_kept | <= 2 | 8 FAIL | 3 FAIL | 0 ok | 1 ok | 0 ok | 1 ok | 0 ok | 0 ok |
| place_right | >= 0.8 | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok | 1.000 ok |
| recall_after | >= before (no loss) | 0.455 ok | 0.455 ok | 0.727 ok | 0.727 ok | 0.727 ok | 0.727 ok | 0.727 ok | 0.727 ok |
| recall_after_kept | report only | 0.455 | 0.455 | 0.727 | 0.727 | 0.727 | 0.727 | 0.727 | 0.727 |
| p1_after | >= 0.6 | 0.788 ok | 0.795 ok | 0.882 ok | 0.883 ok | 0.882 ok | 0.883 ok | 0.891 ok | 0.891 ok |
| sugg_right | report only | n/a | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| j_right | report only | 0.294 | 0.294 | 0.153 | 0.144 | 0.153 | 0.144 | 0.188 | 0.188 |
| j_wrong | report only | 0.082 | 0.137 | 0.171 | 0.163 | 0.171 | 0.163 | 0.130 | 0.130 |

## Context (v2 r1 vs v2_nocontext r1)

Expected: clearly lower without context.

| measure | v2 | v2_nocontext | delta |
|---|---|---|---|
| merge_pure | 1.000 | 1.000 | 0.000 |
| merge_frag | 1.000 | 1.000 | 0.000 |
| split_done | n/a | n/a | n/a |
| split_side | n/a | n/a | n/a |
| noise_marked | 0.417 | 0.667 | 0.250 |
| noise_kept | 0.000 | 0.000 | 0.000 |
| place_right | 1.000 | 1.000 | 0.000 |
| recall_after | 0.727 | 0.727 | 0.000 |
| recall_after_kept | 0.727 | 0.727 | 0.000 |
| p1_after | 0.882 | 0.891 | 0.009 |
| sugg_right | 1.000 | 1.000 | 0.000 |
| j_right | 0.153 | 0.188 | 0.035 |
| j_wrong | 0.171 | 0.130 | -0.041 |

## Stability (v2 r1 vs r2, report only)

Clusters with a different action, merge_with or name: 0.903 (n=31)

## Name rubric (NAMING_RULE.md)

| response | real name accuracy | n | noise marked | n | role accuracy | n | wrong_role |
|---|---|---|---|---|---|---|---|
| nohints r1 | 0.789 | 19 | 0.000 | 7 | n/a | 0 | 0 |
| v2 r1 | 0.786 | 14 | 0.333 | 15 | n/a | 0 | 0 |
| v2 r2 | 0.688 | 16 | 0.267 | 15 | n/a | 0 | 0 |
| v2_nocontext r1 | 0.600 | 15 | 0.500 | 16 | n/a | 0 | 0 |
