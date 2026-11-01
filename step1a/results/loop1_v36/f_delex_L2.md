# wf_v3.6 task 11: F de-lexicalisation re-scored at L2 (rules v1)

- F: broken delex map: it pulled generic words (hotel, restaurant, travel time) from name clusters.
- E s0 = same prompt without delex; both are one order (seed 0), no gate or split.
- Extras = distinct final attributes per kind (T38); the kinds are the GT levels of the attribute's majority label.

| variant | gt_found | gt_partial | extra_L2 | extra_L3 | extra_none | wrong_extra | total |
|---|---|---|---|---|---|---|---|
| F s0 (invalid) | 16 | 4 | 7 | 0 | 4 | 2 | 33 |
| E s0 | 15 | 5 | 6 | 0 | 4 | 1 | 31 |

## Scores at L2

| variant | found train | found hotel | found restaurant | noise pooled (target >= 0.70) | merge right/judged | names right/base | role right/base | cue request/clusters |
|---|---|---|---|---|---|---|---|---|
| E s0 | 2/7 (0.286) | 6/11 (0.545) | 7/12 (0.583) | 9/12 (0.750) | 5/8 (0.625) +8 unjudged | 7/30 (0.233) [16 unrated] | 2/8 (0.250) | n/a |
| F s0 (invalid) | 3/7 (0.429) | 6/11 (0.545) | 7/12 (0.583) | 9/12 (0.750) | 6/11 (0.545) +6 unjudged | 3/30 (0.100) [30 unrated] | 0/8 (0.000) | n/a |
