# wf_v4.4 T7: which Step 4 change helped (a_llama44, dev50, seed 0)

On = all changes on (seed 0 single schema; the voted schema for `vote`). Off = that change off, the others on (seed 0 single schema; the seed 0 single schema for `vote`). Calls: on = the seed 0 chain of all_on (all chains for `vote`), off = the off run's chain. Full GT.

| change | table F1 on | table F1 off | grouping F1 on | grouping F1 off | GT columns placed on | GT columns placed off | GT in rest on | GT in rest off | PK (a) on | PK (a) off | link recall on | link recall off | calls on | calls off |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entity_hint | n/a | 0.727 | n/a | 0.305 | n/a | 18/54 (0.333) | n/a | 9/54 (0.167) | n/a | 2/4 (0.500) | n/a | 0/2 (0.000) | 3 | 5 |
| other_choice | n/a | 0.667 | n/a | 0.733 | n/a | 24/50 (0.480) | n/a | 0/50 (0.000) | n/a | 0/3 (0.000) | n/a | n/a | 3 | 6 |
| key_candidates | n/a | 0.750 | n/a | 1.000 | n/a | 15/50 (0.300) | n/a | 12/50 (0.240) | n/a | 1/3 (0.333) | n/a | n/a | 3 | 5 |
| code_links | n/a | 0.750 | n/a | 1.000 | n/a | 15/50 (0.300) | n/a | 12/50 (0.240) | n/a | 1/3 (0.333) | n/a | n/a | 3 | 6 |
| vote | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 62 | 3 |
