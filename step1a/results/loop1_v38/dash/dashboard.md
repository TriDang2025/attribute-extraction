# wf_v3.8 precision dashboard (L2, rules v1.1, Step 1a v2.2)

## dev50

| row | found train + hotel + rest. = total | cols | cols per found (bar 1.2) | dup cols | wrong cols (entity + noise) | extras no GT | merges right | noise caught | marks right | review edits | recall guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A s012 | 8 + 12 + 11 = 31/40 | 67 | 1.742 (FAIL) | 23 | 11 (2 + 9) | 14 | 3/11 | 10/13 | 10/13 | 34 | pass (train 8/8, hotel 12/12, restaurant 11/11) |
| A s012 nosplit | 6 + 8 + 10 = 24/40 | 32 | 1.083 (pass) | 2 | 1 (0 + 1) | 6 | 9/18 | 10/13 | 10/13 | 3 | FAIL (train 6/8, hotel 8/12, restaurant 10/11; below: train, hotel, restaurant) |
| A, 3 orders (range) | 7-8 + 12 + 11 = 30-31/40 | 62-71 | 1.677-1.710 (FAIL) | 21-22 | 10-15 (2 + 8-13) | 13-15 | 3-4/11 | 3-9/13 | 3-9/8-14 | 31-37 | n/a (worst order per entity: train 7, hotel 12, restaurant 11) |
| A, 3 orders nosplit (range) | 6-7 + 7-9 + 10 = 24-26/40 | 30-33 | 1.000-1.125 (pass) | 0-3 | 0-2 (0 + 0-2) | 3-6 | 8-9/17-18 | 3-9/13 | 3-9/8-14 | 1-5 | n/a (worst order per entity: train 6, hotel 7, restaurant 10) |
| A r1 | 8 + 12 + 11 = 31/40 | 62 | 1.677 (FAIL) | 21 | 10 (2 + 8) | 13 | 3/11 | 9/13 | 9/14 | 31 | pass (train 8/8, hotel 12/12, restaurant 11/11) |
| A r2 | 7 + 12 + 11 = 30/40 | 64 | 1.700 (FAIL) | 21 | 10 (2 + 8) | 15 | 4/11 | 9/13 | 9/14 | 31 | FAIL (train 7/8, hotel 12/12, restaurant 11/11; below: train) |
| A s2 | 8 + 12 + 11 = 31/40 | 71 | 1.710 (FAIL) | 22 | 15 (2 + 13) | 15 | 4/11 | 3/13 | 3/8 | 37 | pass (train 8/8, hotel 12/12, restaurant 11/11) |
| A r1 nosplit | 6 + 8 + 10 = 24/40 | 30 | 1.042 (pass) | 1 | 0 (0 + 0) | 6 | 8/18 | 9/13 | 9/14 | 1 | FAIL (train 6/8, hotel 8/12, restaurant 10/11; below: train, hotel, restaurant) |
| A r2 nosplit | 7 + 9 + 10 = 26/40 | 30 | 1.000 (pass) | 0 | 1 (0 + 1) | 3 | 9/17 | 9/13 | 9/14 | 1 | FAIL (train 7/8, hotel 9/12, restaurant 10/11; below: train, hotel, restaurant) |
| A s2 nosplit | 7 + 7 + 10 = 24/40 | 33 | 1.125 (pass) | 3 | 2 (0 + 2) | 6 | 8/17 | 3/13 | 3/8 | 5 | FAIL (train 7/8, hotel 7/12, restaurant 10/11; below: train, hotel, restaurant) |

## dev50b

| row | found train + hotel + rest. = total | cols | cols per found (bar 1.2) | dup cols | wrong cols (entity + noise) | extras no GT | merges right | noise caught | marks right | review edits | recall guard |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A s012 | 8 + 10 + 11 = 29/41 | 56 | 1.552 (FAIL) | 16 | 7 (1 + 6) | 10 | 7/13 | 5/9 | 5/15 | 23 | pass (train 8/8, hotel 10/10, restaurant 11/11) |
| A s012 nosplit | 7 + 8 + 10 = 25/41 | 35 | 1.080 (pass) | 2 | 3 (0 + 3) | 7 | 8/15 | 5/9 | 5/15 | 5 | FAIL (train 7/8, hotel 8/10, restaurant 10/11; below: train, hotel, restaurant) |
| A, 3 orders (range) | 7 + 6-11 + 11 = 24-29/41 | 49-57 | 1.429-1.483 (FAIL) | 11-14 | 6-11 (1-2 + 5-9) | 8-9 | 5-7/12-15 | 3-6/9 | 3-6/7-17 | 18-25 | n/a (worst order per entity: train 7, hotel 6, restaurant 11) |
| A, 3 orders nosplit (range) | 5-6 + 6-9 + 8-10 = 20-24/41 | 30-34 | 1.000 (pass) | 0 | 2-5 (0 + 2-5) | 5-7 | 6-9/14-17 | 3-6/9 | 3-6/7-17 | 2-5 | n/a (worst order per entity: train 5, hotel 6, restaurant 8) |
| A s0 | 7 + 10 + 11 = 28/41 | 50 | 1.429 (FAIL) | 12 | 6 (1 + 5) | 8 | 5/12 | 6/9 | 6/17 | 18 | FAIL (train 7/8, hotel 10/10, restaurant 11/11; below: train) |
| A s1 | 7 + 11 + 11 = 29/41 | 57 | 1.483 (FAIL) | 14 | 11 (2 + 9) | 9 | 7/15 | 3/9 | 3/7 | 25 | FAIL (train 7/8, hotel 11/10, restaurant 11/11; below: train) |
| A s2 | 7 + 6 + 11 = 24/41 | 49 | 1.458 (FAIL) | 11 | 8 (1 + 7) | 9 | 7/13 | 4/9 | 4/16 | 19 | FAIL (train 7/8, hotel 6/10, restaurant 11/11; below: train, hotel) |
| A s0 nosplit | 6 + 8 + 8 = 22/41 | 31 | 1.000 (pass) | 0 | 2 (0 + 2) | 7 | 6/14 | 6/9 | 6/17 | 2 | FAIL (train 6/8, hotel 8/10, restaurant 8/11; below: train, hotel, restaurant) |
| A s1 nosplit | 5 + 9 + 10 = 24/41 | 34 | 1.000 (pass) | 0 | 5 (0 + 5) | 5 | 7/17 | 3/9 | 3/7 | 5 | FAIL (train 5/8, hotel 9/10, restaurant 10/11; below: train, hotel, restaurant) |
| A s2 nosplit | 5 + 6 + 9 = 20/41 | 30 | 1.000 (pass) | 0 | 3 (0 + 3) | 7 | 9/16 | 4/9 | 4/16 | 3 | FAIL (train 5/8, hotel 6/10, restaurant 9/11; below: train, hotel, restaurant) |

- Columns = distinct normalised output names of unmarked groups. Columns per found attribute = columns whose group majority is a found attribute / found attributes (t14.md). Duplicate columns = sum over found attributes of (columns - 1). Wrong columns = columns with label noise (>= 60% noise mentions) + columns with label real whose top attribute is another entity's. Extras with no GT = columns with no L2 attribute at >= 60% and not noise (mixed / unknown). Review edits = duplicate + wrong columns. Merges: rules v1.1 merge rule, judged merges only. Noise: the model-free noise set; marks right = marked clusters that are noise. Recall guard: RULES_V1_2.md per entity; range rows are n/a (the guard is on the vote).
- Orders: dev50 = A r1 / A r2 / A s2, dev50b = A s0 / A s1 / A s2.
