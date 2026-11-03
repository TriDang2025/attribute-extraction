# wf_v3.8 task 11: the checker against the GT (verdict rule v0, RULES_V1_2.md)

GT kinds (final and prejoin columns of the with-split config): gt = first column (lowest id) of an L2 attribute of the entity (column label real, top attribute in the entity's L2 base); duplicate = a further such column of an attribute that already has one; wrong = wrong entity (label real, attribute of another entity) or noise (label noise, rules v1.1 60%); no_gt = mixed / unknown. rejected = verdict noise or too general; rejected_mixed also counts mixed roles; not_real = any verdict but real (rejected or flagged). The extra row 'duplicate (dashboard def.)' (final columns) counts the duplicates as the dashboard does: for every found attribute, the columns having a group with that majority label beyond the first (a column counts once per attribute); it overlaps the other rows.

## dev50

### final columns

| gt_kind | n | real | unsure | noise | too general | mixed roles | real_share | rejected_share | rejected_mixed_share | not_real_share |
|---|---|---|---|---|---|---|---|---|---|---|
| gt | 30 | 16 | 10 | 1 | 3 | 0 | 0.533 | 0.133 | 0.133 | 0.467 |
| duplicate | 8 | 2 | 2 | 1 | 3 | 0 | 0.250 | 0.500 | 0.500 | 0.750 |
| wrong | 10 | 3 | 2 | 4 | 1 | 0 | 0.300 | 0.500 | 0.500 | 0.700 |
| no_gt | 14 | 1 | 7 | 4 | 2 | 0 | 0.071 | 0.429 | 0.429 | 0.929 |
| duplicate (dashboard def.) | 21 | 7 | 6 | 4 | 4 | 0 | 0.333 | 0.381 | 0.381 | 0.667 |

### prejoin columns

| gt_kind | n | real | unsure | noise | too general | mixed roles | real_share | rejected_share | rejected_mixed_share | not_real_share |
|---|---|---|---|---|---|---|---|---|---|---|
| gt | 30 | 16 | 10 | 1 | 3 | 0 | 0.533 | 0.133 | 0.133 | 0.467 |
| duplicate | 11 | 3 | 3 | 2 | 3 | 0 | 0.273 | 0.455 | 0.455 | 0.727 |
| wrong | 11 | 3 | 2 | 5 | 1 | 0 | 0.273 | 0.545 | 0.545 | 0.727 |
| no_gt | 15 | 0 | 7 | 5 | 3 | 0 | 0.000 | 0.533 | 0.533 | 1.000 |

### Recall guard if rejected columns were removed (final columns)

| row | found_train | found_hotel | found_restaurant | found_total | columns | dup_columns | wrong_columns | extras_no_gt | guard | guard_detail |
|---|---|---|---|---|---|---|---|---|---|---|
| A s012 + dupcheck - noise/too general | 8 | 11 | 11 | 30 | 43 | 8 | 5 | 7 | FAIL | train 8/8, hotel 11/12, restaurant 11/11; below: hotel |
| A s012 + dupcheck - also mixed roles | 8 | 11 | 11 | 30 | 43 | 8 | 5 | 7 | FAIL | train 8/8, hotel 11/12, restaurant 11/11; below: hotel |

**Decision, dev50: keep as a flag for the final review: rejects 5/10 wrong columns (>= half), recall guard FAIL**

## dev50b

### final columns

| gt_kind | n | real | unsure | noise | too general | mixed roles | real_share | rejected_share | rejected_mixed_share | not_real_share |
|---|---|---|---|---|---|---|---|---|---|---|
| gt | 29 | 15 | 11 | 2 | 1 | 0 | 0.517 | 0.103 | 0.103 | 0.483 |
| duplicate | 5 | 1 | 3 | 0 | 1 | 0 | 0.200 | 0.200 | 0.200 | 0.800 |
| wrong | 7 | 2 | 1 | 4 | 0 | 0 | 0.286 | 0.571 | 0.571 | 0.714 |
| no_gt | 10 | 2 | 4 | 0 | 4 | 0 | 0.200 | 0.400 | 0.400 | 0.800 |
| duplicate (dashboard def.) | 12 | 4 | 6 | 0 | 2 | 0 | 0.333 | 0.167 | 0.167 | 0.667 |

### prejoin columns

| gt_kind | n | real | unsure | noise | too general | mixed roles | real_share | rejected_share | rejected_mixed_share | not_real_share |
|---|---|---|---|---|---|---|---|---|---|---|
| gt | 29 | 15 | 9 | 2 | 3 | 0 | 0.517 | 0.172 | 0.172 | 0.483 |
| duplicate | 10 | 1 | 6 | 1 | 2 | 0 | 0.100 | 0.300 | 0.300 | 0.900 |
| wrong | 7 | 2 | 1 | 4 | 0 | 0 | 0.286 | 0.571 | 0.571 | 0.714 |
| no_gt | 10 | 1 | 5 | 0 | 4 | 0 | 0.100 | 0.400 | 0.400 | 0.900 |

### Recall guard if rejected columns were removed (final columns)

| row | found_train | found_hotel | found_restaurant | found_total | columns | dup_columns | wrong_columns | extras_no_gt | guard | guard_detail |
|---|---|---|---|---|---|---|---|---|---|---|
| A s012 + dupcheck - noise/too general | 7 | 9 | 10 | 26 | 39 | 7 | 3 | 6 | FAIL | train 7/8, hotel 9/10, restaurant 10/11; below: train, hotel, restaurant |
| A s012 + dupcheck - also mixed roles | 7 | 9 | 10 | 26 | 39 | 7 | 3 | 6 | FAIL | train 7/8, hotel 9/10, restaurant 10/11; below: train, hotel, restaurant |

**Decision, dev50b: keep as a flag for the final review: rejects 4/7 wrong columns (>= half), recall guard FAIL**
