# wf_v3.9 batch scores (L2, rules v1.3 over v1.2, Step 1a v2.2)

Rows are the A s012 vote with changes on the columns only (found and merges are per group, so they do not change unless a part's group changes column). Review edits = duplicate + wrong columns. Role-pure = role-pure columns / role columns (RULES_V1_3.md 1). Marks 1.3 = noise marks right / marks counted (2a: a question cluster marked noise is right when the variant has no attribute_cue label; 2b: other-domain clusters marked noise leave the count, shown as wrong entity dropped; A-cue: a question cluster is right only when marked attribute_cue). Recall guard: RULES_V1_2.md per entity.

## Summary

- T4 reconcile: ADOPT. Main row = joins both orders agree on. Orders agree on 65/79 (0.823) parts. Review edits: dev50 34 -> 25; dev50b 23 -> 19. Recall guard passes on both sets.
  Join quality (rc0 joined parts): dev50 8 right, 5 wrong, 7 no GT of 20; dev50b 4 right, 4 wrong, 5 no GT of 13. Review edits count duplicate and wrong columns; a wrong join does not lower found, so read the right / wrong split next to it.
- T5 reconcile + duplicate check: rc0 ADOPT, rc1 ADOPT. Columns per found: dev50 rc0 1.387, rc1 1.419; dev50b rc0 1.276, rc1 1.310 (bar <= 1.2, not met on either set).
- T8 A-cue s012: do not adopt. Marks right (rules 1.3): dev50 10/12 -> 10/15; dev50b 8/11 -> 10/13.

## Step 0

188 responses for 188 jobs. Problems: hotel_acue_dev50_s2: finish stop, errors ["clusters[13] attribute 'hotel_phone_number' not in the attribute list"]; dupcheck_dev50b_rc1_hotel: finish stop, errors ['joins[2] needs a list of >= 2 distinct columns', 'joins[3] needs a list of >= 2 distinct columns'].
Handled: dupcheck_dev50b_rc1_hotel: 2 joins with fewer than 2 distinct columns dropped (parse errors 2), 2 kept. A-cue parse repairs: [{'variant': 'A-cue s2', 'ent': 'hotel', 'job': 'hotel_acue_dev50_s2', 'repaired_names': ['hotel_phone_number']}].

## Dashboard rows

### dev50

| set | row | found_total | gold_total | columns | columns_per_found | dup_columns | wrong_columns | extras_no_gt | review_edits | guard | role_pure | role_columns | marks13_right | marks13_n | wrong_entity_dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 | 31 | 40 | 67 | 1.742 | 23 | 11 | 14 | 34 | pass | 2 | 11 | 10 | 12 | 1 |
| dev50 | A s012 + dupcheck | 31 | 40 | 62 | 1.677 | 21 | 10 | 13 | 31 | pass | 2 | 9 | 10 | 12 | 1 |
| dev50 | A s012 + reconcile rc0 | 31 | 40 | 55 | 1.484 | 15 | 8 | 11 | 23 | pass | 2 | 10 | 10 | 12 | 1 |
| dev50 | A s012 + reconcile rc1 | 31 | 40 | 56 | 1.516 | 16 | 8 | 10 | 24 | pass | 2 | 10 | 10 | 12 | 1 |
| dev50 | A s012 + reconcile (both orders) | 31 | 40 | 57 | 1.548 | 17 | 8 | 11 | 25 | pass | 2 | 10 | 10 | 12 | 1 |
| dev50 | A s012 + reconcile rc0 + dupcheck | 31 | 40 | 51 | 1.387 | 12 | 7 | 10 | 19 | pass | 2 | 10 | 10 | 12 | 1 |
| dev50 | A s012 + reconcile rc1 + dupcheck | 31 | 40 | 52 | 1.419 | 13 | 7 | 10 | 20 | pass | 2 | 10 | 10 | 12 | 1 |
| dev50 | A-cue s0 | 30 | 40 | 66 | 1.700 | 21 | 14 | 13 | 35 | FAIL | 4 | 12 | 9 | 17 | 1 |
| dev50 | A-cue s1 | 30 | 40 | 61 | 1.633 | 19 | 10 | 12 | 29 | FAIL | 3 | 11 | 11 | 16 | 1 |
| dev50 | A-cue s2 | 31 | 40 | 67 | 1.677 | 21 | 15 | 11 | 36 | pass | 4 | 13 | 6 | 11 | 2 |
| dev50 | A-cue s012 | 31 | 40 | 68 | 1.710 | 22 | 13 | 13 | 35 | pass | 3 | 12 | 10 | 15 | 2 |

### dev50b

| set | row | found_total | gold_total | columns | columns_per_found | dup_columns | wrong_columns | extras_no_gt | review_edits | guard | role_pure | role_columns | marks13_right | marks13_n | wrong_entity_dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev50b | A s012 | 29 | 41 | 56 | 1.552 | 16 | 7 | 10 | 23 | pass | 3 | 9 | 8 | 11 | 4 |
| dev50b | A s012 + dupcheck | 29 | 41 | 51 | 1.414 | 12 | 7 | 10 | 19 | pass | 3 | 8 | 8 | 11 | 4 |
| dev50b | A s012 + reconcile rc0 | 29 | 41 | 49 | 1.448 | 13 | 7 | 8 | 20 | pass | 3 | 8 | 8 | 11 | 4 |
| dev50b | A s012 + reconcile rc1 | 29 | 41 | 50 | 1.483 | 14 | 6 | 10 | 20 | pass | 3 | 8 | 8 | 11 | 4 |
| dev50b | A s012 + reconcile (both orders) | 29 | 41 | 50 | 1.448 | 13 | 6 | 8 | 19 | pass | 3 | 8 | 8 | 11 | 4 |
| dev50b | A s012 + reconcile rc0 + dupcheck | 29 | 41 | 40 | 1.276 | 8 | 7 | 6 | 15 | pass | 2 | 6 | 8 | 11 | 4 |
| dev50b | A s012 + reconcile rc1 + dupcheck | 29 | 41 | 45 | 1.310 | 9 | 6 | 9 | 15 | pass | 3 | 7 | 8 | 11 | 4 |
| dev50b | A-cue s0 | 29 | 41 | 54 | 1.414 | 12 | 8 | 8 | 20 | pass | 5 | 9 | 10 | 13 | 4 |
| dev50b | A-cue s1 | 28 | 41 | 55 | 1.500 | 14 | 9 | 8 | 23 | FAIL | 3 | 8 | 9 | 13 | 3 |
| dev50b | A-cue s2 | 28 | 41 | 56 | 1.536 | 15 | 7 | 10 | 22 | FAIL | 3 | 8 | 6 | 8 | 2 |
| dev50b | A-cue s012 | 29 | 41 | 56 | 1.483 | 14 | 7 | 9 | 21 | pass | 3 | 9 | 10 | 13 | 4 |

## T4: reconcile

Main row: **A s012 + reconcile (both orders)** = a part joins a column only when both candidate orders chose the same column (chosen before reading any result: the answers are order-sensitive in earlier batches, so the intersection is the cautious reading and needs no tie rule). The per-order rows rc0 and rc1 are shown above. Every join judged as in v3.8 (the part alone against the chosen column: right = same L2 attribute and same role; wrong = noise, other attribute or mixed role; no GT = a side has no L2 attribute). Blocked = a role pair by names (code check).

| set | order | parts | joined | joined right | joined wrong | joined no_gt | blocked | none | agree | agree_share |
|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | rc0 | 47 | 20 | 8 | 5 | 7 | 0 | 27 | 43/47 | 0.915 |
| dev50 | rc1 | 47 | 17 | 6 | 4 | 7 | 0 | 30 | 43/47 | 0.915 |
| dev50b | rc0 | 32 | 13 | 4 | 4 | 5 | 0 | 19 | 22/32 | 0.688 |
| dev50b | rc1 | 32 | 11 | 2 | 3 | 6 | 0 | 21 | 22/32 | 0.688 |

Joins both orders agree on (the main row's joins), by GT status:

| set | joins | right | wrong | no_gt |
|---|---|---|---|---|
| dev50 | 16 | 6 | 4 | 6 |
| dev50b | 7 | 2 | 2 | 3 |

Every join is in `reconcile_joins.csv`.

- dev50: review edits 34 -> 25, columns 67 -> 57 (columns per found 1.742 -> 1.548), found 31 -> 31, recall guard pass (train 8/8, hotel 12/12, restaurant 11/11): pass.
- dev50b: review edits 23 -> 19, columns 56 -> 50 (columns per found 1.552 -> 1.448), found 29 -> 29, recall guard pass (train 8/8, hotel 10/10, restaurant 11/11): pass.

**Decision T4: ADOPT reconcile** (rule: recall guard passes and review edits go down on both sets, main row).

## T5: reconcile + duplicate check

- rc0, dev50: review edits 34 -> 19, columns 67 -> 51 (columns per found 1.742 -> 1.387), found 31 -> 31, recall guard pass (train 8/8, hotel 12/12, restaurant 11/11): pass. Columns per found 1.387 (bar <= 1.2: not met); v3.8 dupcheck alone: review edits 31, columns per found 1.677.
- rc1, dev50: review edits 34 -> 20, columns 67 -> 52 (columns per found 1.742 -> 1.419), found 31 -> 31, recall guard pass (train 8/8, hotel 12/12, restaurant 11/11): pass. Columns per found 1.419 (bar <= 1.2: not met); v3.8 dupcheck alone: review edits 31, columns per found 1.677.
- rc0, dev50b: review edits 23 -> 15, columns 56 -> 40 (columns per found 1.552 -> 1.276), found 29 -> 29, recall guard pass (train 8/8, hotel 10/10, restaurant 11/11): pass. Columns per found 1.276 (bar <= 1.2: not met); v3.8 dupcheck alone: review edits 19, columns per found 1.414.
- rc1, dev50b: review edits 23 -> 15, columns 56 -> 45 (columns per found 1.552 -> 1.310), found 29 -> 29, recall guard pass (train 8/8, hotel 10/10, restaurant 11/11): pass. Columns per found 1.310 (bar <= 1.2: not met); v3.8 dupcheck alone: review edits 19, columns per found 1.414.

**Decision T5: rc0 ADOPT, rc1 ADOPT** (same rule per order).

## T8: A-cue

Cue marks against the request GT (rules 2a: question cluster = at least 60% request mentions):

| set | row | marks13_right | marks13_n | wrong_entity_dropped | cue_marks | cue_question | cue_other_domain | questions | questions_cue | questions_noise | questions_column | noise_caught | noise_n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 | 10 | 12 | 1 | 0 | 0 | 0 | 4 | 0 | 0 | 4 | 10 | 13 |
| dev50 | A-cue s0 | 9 | 17 | 1 | 1 | 1 | 0 | 4 | 1 | 0 | 3 | 8 | 13 |
| dev50 | A-cue s1 | 11 | 16 | 1 | 1 | 1 | 0 | 4 | 1 | 1 | 2 | 10 | 13 |
| dev50 | A-cue s2 | 6 | 11 | 2 | 3 | 2 | 0 | 4 | 2 | 0 | 2 | 4 | 13 |
| dev50 | A-cue s012 | 10 | 15 | 2 | 1 | 1 | 0 | 4 | 1 | 0 | 3 | 9 | 13 |
| dev50b | A s012 | 8 | 11 | 4 | 0 | 0 | 0 | 4 | 0 | 3 | 1 | 5 | 9 |
| dev50b | A-cue s0 | 10 | 13 | 4 | 6 | 4 | 0 | 4 | 4 | 0 | 0 | 6 | 9 |
| dev50b | A-cue s1 | 9 | 13 | 3 | 6 | 4 | 0 | 4 | 4 | 0 | 0 | 5 | 9 |
| dev50b | A-cue s2 | 6 | 8 | 2 | 4 | 3 | 0 | 4 | 3 | 0 | 1 | 3 | 9 |
| dev50b | A-cue s012 | 10 | 13 | 4 | 6 | 4 | 0 | 4 | 4 | 0 | 0 | 6 | 9 |

- dev50: marks right 10/12 -> 10/15, recall guard pass: not met.
- dev50b: marks right 8/11 -> 10/13, recall guard pass: pass.

**Decision T8: DO NOT ADOPT A-cue** (rule: noise marks right up on both sets against A s012 under v1.3, and the recall guard passes).

## Tokens (exact)

| family | calls | prompt tokens | per call | output tokens | per call | est. prompt (chars/3.5) |
|---|---|---|---|---|---|---|
| reconcile | 158 | 92,616 | 586 | 6,488 | 41 | 97,642 |
| a_cue | 18 | 202,042 | 11,224 | 54,641 | 3,035 | 179,211 |
| dupcheck_rc | 12 | 8,766 | 730 | 645 | 53 | 8,068 |
| total | 188 | 303,424 | 1,613 | 61,774 | 328 | 284,921 |
