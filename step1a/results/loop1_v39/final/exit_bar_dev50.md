# wf_v3.9 exit bar, final setting on dev50 (L2, rules v1.1; guard RULES_V1_2.md)

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
