# wf_v3.8 precision dashboard with the duplicate check (L2, rules v1.1, Step 1a v2.2)

## dev50

| row | found train + hotel + rest. = total | cols | cols per found (bar 1.2) | dup cols | wrong cols (entity + noise) | extras no GT | merges right | noise caught | marks right | review edits | recall guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A s012 | 8 + 12 + 11 = 31/40 | 67 | 1.742 (FAIL) | 23 | 11 (2 + 9) | 14 | 3/11 | 10/13 | 10/13 | 34 | pass (train 8/8, hotel 12/12, restaurant 11/11) |
| A s012 + dupcheck | 8 + 12 + 11 = 31/40 | 62 | 1.677 (FAIL) | 21 | 10 (2 + 8) | 13 | 3/11 | 10/13 | 10/13 | 31 | pass (train 8/8, hotel 12/12, restaurant 11/11) |
| A s012 nosplit | 6 + 8 + 10 = 24/40 | 32 | 1.083 (pass) | 2 | 1 (0 + 1) | 6 | 9/18 | 10/13 | 10/13 | 3 | FAIL (train 6/8, hotel 8/12, restaurant 10/11; below: train, hotel, restaurant) |
| A s012 nosplit + dupcheck | 6 + 8 + 10 = 24/40 | 30 | 1.042 (pass) | 1 | 1 (0 + 1) | 6 | 9/18 | 10/13 | 10/13 | 2 | FAIL (train 6/8, hotel 8/12, restaurant 10/11; below: train, hotel, restaurant) |

## dev50b

| row | found train + hotel + rest. = total | cols | cols per found (bar 1.2) | dup cols | wrong cols (entity + noise) | extras no GT | merges right | noise caught | marks right | review edits | recall guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A s012 | 8 + 10 + 11 = 29/41 | 56 | 1.552 (FAIL) | 16 | 7 (1 + 6) | 10 | 7/13 | 5/9 | 5/15 | 23 | pass (train 8/8, hotel 10/10, restaurant 11/11) |
| A s012 + dupcheck | 8 + 10 + 11 = 29/41 | 51 | 1.414 (FAIL) | 12 | 7 (1 + 6) | 10 | 7/13 | 5/9 | 5/15 | 19 | pass (train 8/8, hotel 10/10, restaurant 11/11) |
| A s012 nosplit | 7 + 8 + 10 = 25/41 | 35 | 1.080 (pass) | 2 | 3 (0 + 3) | 7 | 8/15 | 5/9 | 5/15 | 5 | FAIL (train 7/8, hotel 8/10, restaurant 10/11; below: train, hotel, restaurant) |
| A s012 nosplit + dupcheck | 7 + 8 + 10 = 25/41 | 34 | 1.040 (pass) | 1 | 3 (0 + 3) | 6 | 8/15 | 5/9 | 5/15 | 4 | FAIL (train 7/8, hotel 8/10, restaurant 10/11; below: train, hotel, restaurant) |

- Rows with + dupcheck: the dupcheck joins that pass the code check (role pairs by the method's own names) are applied; a joined column keeps all groups of its members under one name (the biggest member's). Found, merges, noise and marks are per group / cluster, so joining does not change them; only columns, columns per found, dup, wrong and extras can change. Recall guard: RULES_V1_2.md.
- Joins: dev50 nosplit: 2 joins, 2 accepted (0 right, 1 wrong, 1 no GT), 0 rejected; dev50 split: 5 joins, 5 accepted (1 right, 2 wrong, 2 no GT), 0 rejected; dev50b nosplit: 1 joins, 1 accepted (0 right, 0 wrong, 1 no GT), 0 rejected; dev50b split: 6 joins, 5 accepted (2 right, 1 wrong, 2 no GT), 1 rejected
