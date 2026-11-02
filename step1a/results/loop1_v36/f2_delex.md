# wf_v3.6 F2 (fixed delex) vs E s0 and F re-scored at L2 (rules v1)

- F: broken delex map: it pulled generic words (hotel, restaurant, travel time) from name clusters.
- F2 = the same job set with the fixed delex map (only real entity names: DB names, stations, TR ids; generic words stopped).
- E s0 = same prompt without delex; all three are one order (seed 0), no gate or split.
- Extras = distinct final attributes per kind (T38); the kinds are the GT levels of the attribute's majority label.

| variant | gt_found | gt_partial | extra_L2 | extra_L3 | extra_none | wrong_extra | total |
|---|---|---|---|---|---|---|---|
| E s0 | 15 | 5 | 6 | 0 | 4 | 1 | 31 |
| F2 s0 | 16 | 6 | 6 | 0 | 5 | 3 | 36 |
| F s0 (invalid) | 16 | 4 | 7 | 0 | 4 | 2 | 33 |

## Scores at L2

| variant | found train | found hotel | found restaurant | noise pooled (target >= 0.70) | merge right/judged | names right/base | role right/base | cue request/clusters |
|---|---|---|---|---|---|---|---|---|
| E s0 | 6/10 (0.600) | 6/14 (0.429) | 10/16 (0.625) | 11/12 (0.917) | 9/16 (0.562) | 17/40 (0.425) [8 unrated] | 3/8 (0.375) | 5/12 (0.417) |
| F s0 (invalid) | 7/10 (0.700) | 8/14 (0.571) | 9/16 (0.562) | 11/12 (0.917) | 7/17 (0.412) | 4/40 (0.100) [30 unrated] | 0/8 (0.000) | 3/4 (0.750) |
| F2 s0 | 6/10 (0.600) | 7/14 (0.500) | 11/16 (0.688) | 10/12 (0.833) | 15/18 (0.833) | 9/40 (0.225) [20 unrated] | 0/8 (0.000) | 4/8 (0.500) |
