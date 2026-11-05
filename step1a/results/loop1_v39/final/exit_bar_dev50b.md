# wf_v3.9 exit bar, final setting on dev50b (L2, rules v1.1; guard RULES_V1_2.md)

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
