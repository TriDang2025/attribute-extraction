# wf_v3.7 LLM-only baseline at L2

Names rated by two blind raters against the lexically closest L2 slot (lower label wins); counts are summed over train, hotel and restaurant. Definitions: `s1a/baseline_v37.py`. `union` = the distinct names of v0, v1 and v2.

| set | version | right names | partly | wrong attributes | extras with no GT | no support | columns | unrated |
|---|---|---|---|---|---|---|---|---|
| dev50 | union | 26/40 (0.650) | 3 | 5 | 3 | 5 | 43 | 0 |
| dev50 | v0 | 25/40 (0.625) | 2 | 2 | 1 | 3 | 30 | 0 |
| dev50 | v1 | 22/40 (0.550) | 2 | 4 | 2 | 4 | 30 | 0 |
| dev50 | v2 | 20/40 (0.500) | 3 | 5 | 2 | 5 | 30 | 0 |
| dev50b | union | 27/40 (0.675) | 2 | 6 | 2 | 5 | 42 | 0 |
| dev50b | v0 | 21/40 (0.525) | 2 | 5 | 2 | 4 | 30 | 0 |
| dev50b | v1 | 24/40 (0.600) | 2 | 4 | 1 | 4 | 31 | 0 |
| dev50b | v2 | 26/40 (0.650) | 2 | 4 | 0 | 4 | 32 | 0 |

## A at L2 (all_variants_v36.csv, setting `default`, dev50)

| variant | right names (names L2 rated) | found attributes |
|---|---|---|
| A r1 | 30/40 | 31/40 |
| A r2 | 29/40 | 30/40 |
| A s2 | 31/40 | 31/40 |

Partly, wrong, extras, no-support and column counts of A are not in that file; compute them from the A decisions (W1 tables) to compare.
