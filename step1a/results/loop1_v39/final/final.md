# wf_v3.9 final setting scored once per set (L2, rules v1.3 over v1.2, Step 1a v2.2)

Final setting = A s012 (3-order vote) + split pass + reconcile joins both candidate orders agree on + duplicate-check joins both reconcile orders unite (same set of A s012 groups; applied on the agreed columns; role-pair block applies) + the v3.8 checker as a flag only (no column is removed). Decisions, found and noise marks are those of A s012; only the columns change.

## Rows

| set | row | found_total | gold_total | columns | columns_per_found | dup_columns | wrong_columns | extras_no_gt | review_edits | guard | guard_detail | role_pure | role_columns | marks13_right | marks13_n | wrong_entity_dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | A s012 | 31 | 40 | 67 | 1.742 | 23 | 11 | 14 | 34 | pass | train 8/8, hotel 12/12, restaurant 11/11 | 2 | 11 | 10 | 12 | 1 |
| dev50 | Final v3.9 | 31 | 40 | 55 | 1.516 | 16 | 8 | 10 | 24 | pass | train 8/8, hotel 12/12, restaurant 11/11 | 2 | 10 | 10 | 12 | 1 |
| dev50b | A s012 | 29 | 41 | 56 | 1.552 | 16 | 7 | 10 | 23 | pass | train 8/8, hotel 10/10, restaurant 11/11 | 3 | 9 | 8 | 11 | 4 |
| dev50b | Final v3.9 | 29 | 41 | 47 | 1.345 | 10 | 6 | 7 | 16 | pass | train 8/8, hotel 10/10, restaurant 11/11 | 3 | 7 | 8 | 11 | 4 |

## Duplicate-check joins that survive the both-orders rule

A join is kept when both reconcile orders' duplicate checks (after cleaning and the code check on their own columns) unite exactly the same set of A s012 groups. It is then applied on the agreed-reconcile columns (every column holding one of its groups is joined), checked for role pairs, and judged by the GT as in v3.8 (right = same L2 attribute and role).

| set | rc0 joins | rc0 after code check | rc1 joins | rc1 after code check | same groups in both | on agreed columns | role-pair blocked | kept | kept right | kept wrong | kept no_gt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | 4 | 4 | 4 | 4 | 2 | 2 | 0 | 2 | 1 | 0 | 1 |
| dev50b | 9 | 9 | 6 | 5 | 3 | 3 | 0 | 3 | 1 | 1 | 1 |

Per entity: `dup_survival.csv`.

## Exit bar (RULES_V1_1.md, a)-(e)

### dev50

Bar (RULES_V1_1.md): (a) finds >= 90% of the attributes that Step 1a makes recoverable (ceiling table: some single cluster passes purity >= 0.6 and coverage >= 10%); (b) found attributes change by <= 1 across orders; (c) <= 1.2 columns per found attribute; (d) >= 9 of the 13 noise clusters caught with >= 70% of the noise marks right; (e) beats the LLM-only baseline: **pending the baseline**. A row of several orders shows min-max and passes only when its worst order does. (b) is the range of the found totals over the orders; a vote (A s012) is one result, so (b) is n/a and the orders' range applies.

| run | (a) found of recoverable | (a) share | (b) found total, range | (c) columns per found | (d) noise caught | (d) precision of marks | a | b | c | d | e |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A, 3 orders (A r1 / A r2 / A s2) | 27/29 | 0.931 | 30-31, range 1 | 1.677-1.710 | 3-9/13 | 0.375-0.643 | pass | pass | FAIL | FAIL | n/a (orders not scored here) |
| A s012 (vote) | 27/29 | 0.931 | 31 | 1.742 | 10/13 | 0.769 | pass | n/a | FAIL | pass | pass: right names 29 vs baseline union 26 |
| Final v3.9 | 27/29 | 0.931 | 31 | 1.516 | 10/13 | 0.769 | pass | n/a | FAIL | pass | pass: right names 27 vs baseline union 26 |

## Single runs

| run | found | of which recoverable | found, not recoverable | columns per found | noise caught | marks right |
|---|---|---|---|---|---|---|
| A r1 | 31 | 27/29 (0.931) | 4 | 1.677 | 9/13 (0.692) | 9/14 (0.643) |
| A r2 | 30 | 27/29 (0.931) | 3 | 1.700 | 9/13 (0.692) | 9/14 (0.643) |
| A s2 | 31 | 27/29 (0.931) | 4 | 1.710 | 3/13 (0.231) | 3/8 (0.375) |
| A s012 | 31 | 27/29 (0.931) | 4 | 1.742 | 10/13 (0.769) | 10/13 (0.769) |
| Final v3.9 | 31 | 27/29 (0.931) | 4 | 1.516 | 10/13 (0.769) | 10/13 (0.769) |

- (e): right names = names L2 rated, summed over the entities (score_levels, as scripts/score_t14_v37.py). Final v3.9: a group renamed by a join has a name+description that was never rated and counts as not right (unrated = not right), so its right-names count is a lower bound (only groups whose name changed lose their rating); the right names of A s012 are the exact ones.
- (d) uses the v1.1 / v1.2 marks (noise_v36.noise_l2_rows, as every earlier exit bar); the v1.3 marks are in final.md.
- (b): A's three orders range over the orders; the vote and the final are one result each, so (b) is n/a for them.


### dev50b

Bar (RULES_V1_1.md): (a) finds >= 90% of the attributes that Step 1a makes recoverable (ceiling table: some single cluster passes purity >= 0.6 and coverage >= 10%); (b) found attributes change by <= 1 across orders; (c) <= 1.2 columns per found attribute; (d) >= 9 of the 13 noise clusters caught with >= 70% of the noise marks right; (e) beats the LLM-only baseline: **pending the baseline**. A row of several orders shows min-max and passes only when its worst order does. (b) is the range of the found totals over the orders; a vote (A s012) is one result, so (b) is n/a and the orders' range applies.

| run | (a) found of recoverable | (a) share | (b) found total, range | (c) columns per found | (d) noise caught | (d) precision of marks | a | b | c | d | e |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A, 3 orders (A s0 / A s1 / A s2) | 23-27/30 | 0.767-0.900 | 24-29, range 5 | 1.429-1.483 | 3-6/9 | 0.250-0.429 | FAIL | FAIL | FAIL | FAIL | n/a (orders not scored here) |
| A s012 (vote) | 27/30 | 0.900 | 29 | 1.552 | 5/9 | 0.333 | pass | n/a | FAIL | FAIL | pass: right names 32 vs baseline union 27 |
| Final v3.9 | 27/30 | 0.900 | 29 | 1.345 | 5/9 | 0.333 | pass | n/a | FAIL | FAIL | pass: right names 31 vs baseline union 27 |

## Single runs

| run | found | of which recoverable | found, not recoverable | columns per found | noise caught | marks right |
|---|---|---|---|---|---|---|
| A s0 | 28 | 26/30 (0.867) | 2 | 1.429 | 6/9 (0.667) | 6/17 (0.353) |
| A s1 | 29 | 27/30 (0.900) | 2 | 1.483 | 3/9 (0.333) | 3/7 (0.429) |
| A s2 | 24 | 23/30 (0.767) | 1 | 1.458 | 4/9 (0.444) | 4/16 (0.250) |
| A s012 | 29 | 27/30 (0.900) | 2 | 1.552 | 5/9 (0.556) | 5/15 (0.333) |
| Final v3.9 | 29 | 27/30 (0.900) | 2 | 1.345 | 5/9 (0.556) | 5/15 (0.333) |

- (e): right names = names L2 rated, summed over the entities (score_levels, as scripts/score_t14_v37.py). Final v3.9: a group renamed by a join has a name+description that was never rated and counts as not right (unrated = not right), so its right-names count is a lower bound (only groups whose name changed lose their rating); the right names of A s012 are the exact ones.
- (d) uses the v1.1 / v1.2 marks (noise_v36.noise_l2_rows, as every earlier exit bar); the v1.3 marks are in final.md.
- (b): A's three orders range over the orders; the vote and the final are one result each, so (b) is n/a for them.

