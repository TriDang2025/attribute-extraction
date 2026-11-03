# wf_v3.7 exit bar, A on dev50 v2.2 (L2, rules v1.1)

Bar (RULES_V1_1.md): (a) finds >= 90% of the attributes that Step 1a makes recoverable (ceiling table: some single cluster passes purity >= 0.6 and coverage >= 10%); (b) found attributes change by <= 1 across orders; (c) <= 1.2 columns per found attribute; (d) >= 9 of the 13 noise clusters caught with >= 70% of the noise marks right; (e) beats the LLM-only baseline: **pending the baseline**. A row of several orders shows min-max and passes only when its worst order does. (b) is the range of the found totals over the orders; a vote (A s012) is one result, so (b) is n/a and the orders' range applies.

| run | (a) found of recoverable | (a) share | (b) found total, range | (c) columns per found | (d) noise caught | (d) precision of marks | a | b | c | d | e |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A, 3 orders (A r1 / A r2 / A s2) | 27/29 | 0.931 | 30-31, range 1 | 1.677-1.710 | 3-9/13 | 0.375-0.643 | pass | pass | FAIL | FAIL | pass: A s012 right names 29 vs baseline union 26 |
| A s012 (vote) | 27/29 | 0.931 | 31 | 1.742 | 10/13 | 0.769 | pass | n/a | FAIL | pass | pass: A s012 right names 29 vs baseline union 26 |

## Single runs

| run | found | of which recoverable | found, not recoverable | columns per found | noise caught | marks right |
|---|---|---|---|---|---|---|
| A r1 | 31 | 27/29 (0.931) | 4 | 1.677 | 9/13 (0.692) | 9/14 (0.643) |
| A r2 | 30 | 27/29 (0.931) | 3 | 1.700 | 9/13 (0.692) | 9/14 (0.643) |
| A s2 | 31 | 27/29 (0.931) | 4 | 1.710 | 3/13 (0.231) | 3/8 (0.375) |
| A s012 | 31 | 27/29 (0.931) | 4 | 1.742 | 10/13 (0.769) | 10/13 (0.769) |

- (e): A s012's right names (names L2 rated, summed over entities) must be strictly more than the baseline union's right names of the same set (baseline_v37.csv).
