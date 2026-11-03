# wf_v3.7 exit bar, A on dev50 v2.3 (L2, rules v1.1)

Bar (RULES_V1_1.md): (a) finds >= 90% of the attributes that Step 1a makes recoverable (ceiling table: some single cluster passes purity >= 0.6 and coverage >= 10%); (b) found attributes change by <= 1 across orders; (c) <= 1.2 columns per found attribute; (d) >= 9 of the 13 noise clusters caught with >= 70% of the noise marks right; (e) beats the LLM-only baseline: **pending the baseline**. A row of several orders shows min-max and passes only when its worst order does. (b) is the range of the found totals over the orders; a vote (A s012) is one result, so (b) is n/a and the orders' range applies.

| run | (a) found of recoverable | (a) share | (b) found total, range | (c) columns per found | (d) noise caught | (d) precision of marks | a | b | c | d | e |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A, 3 orders (A s0 / A s1 / A s2) | 26-28/30 | 0.867-0.933 | 29-31, range 2 | 1.567-1.655 | 8-11/13 | 0.348-0.529 | FAIL | FAIL | FAIL | FAIL | pass: A s012 right names 30 vs baseline union 26 |
| A s012 (vote) | 28/30 | 0.933 | 31 | 1.645 | 11/13 | 0.500 | pass | n/a | FAIL | FAIL | pass: A s012 right names 30 vs baseline union 26 |

## Single runs

| run | found | of which recoverable | found, not recoverable | columns per found | noise caught | marks right |
|---|---|---|---|---|---|---|
| A s0 | 29 | 26/30 (0.867) | 3 | 1.655 | 9/13 (0.692) | 9/17 (0.529) |
| A s1 | 31 | 28/30 (0.933) | 3 | 1.613 | 11/13 (0.846) | 11/21 (0.524) |
| A s2 | 30 | 27/30 (0.900) | 3 | 1.567 | 8/13 (0.615) | 8/23 (0.348) |
| A s012 | 31 | 28/30 (0.933) | 3 | 1.645 | 11/13 (0.846) | 11/22 (0.500) |

- (e): A s012's right names (names L2 rated, summed over entities) must be strictly more than the baseline union's right names of the same set (baseline_v37.csv).
