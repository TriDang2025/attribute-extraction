# wf_v3.7 exit bar, A on dev50b v2.3 (L2, rules v1.1)

Bar (RULES_V1_1.md): (a) finds >= 90% of the attributes that Step 1a makes recoverable (ceiling table: some single cluster passes purity >= 0.6 and coverage >= 10%); (b) found attributes change by <= 1 across orders; (c) <= 1.2 columns per found attribute; (d) >= 9 of the 13 noise clusters caught with >= 70% of the noise marks right; (e) beats the LLM-only baseline: **pending the baseline**. A row of several orders shows min-max and passes only when its worst order does. (b) is the range of the found totals over the orders; a vote (A s012) is one result, so (b) is n/a and the orders' range applies.

| run | (a) found of recoverable | (a) share | (b) found total, range | (c) columns per found | (d) noise caught | (d) precision of marks | a | b | c | d | e |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A, 3 orders (A s0 / A s1 / A s2) | 24-28/30 | 0.800-0.933 | 25-30, range 5 | 1.500-1.714 | 5-6/9 | 0.286-0.417 | FAIL | FAIL | FAIL | FAIL | pass: A s012 right names 30 vs baseline union 27 |
| A s012 (vote) | 27/30 | 0.900 | 29 | 1.655 | 6/9 | 0.316 | pass | n/a | FAIL | FAIL | pass: A s012 right names 30 vs baseline union 27 |

## Single runs

| run | found | of which recoverable | found, not recoverable | columns per found | noise caught | marks right |
|---|---|---|---|---|---|---|
| A s0 | 30 | 28/30 (0.933) | 2 | 1.500 | 6/9 (0.667) | 6/20 (0.300) |
| A s1 | 28 | 26/30 (0.867) | 2 | 1.714 | 5/9 (0.556) | 5/12 (0.417) |
| A s2 | 25 | 24/30 (0.800) | 1 | 1.600 | 6/9 (0.667) | 6/21 (0.286) |
| A s012 | 29 | 27/30 (0.900) | 2 | 1.655 | 6/9 (0.667) | 6/19 (0.316) |

- (e): A s012's right names (names L2 rated, summed over entities) must be strictly more than the baseline union's right names of the same set (baseline_v37.csv).
