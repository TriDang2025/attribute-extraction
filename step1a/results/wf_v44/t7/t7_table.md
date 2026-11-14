# wf_v4.4 T7: which Step 4 change helped (a_llama44, dev50, seed 0)

On = all changes on (seed 0 single schema; the voted schema for `vote`). Off = that change off, the others on (seed 0 single schema; the seed 0 single schema for `vote`). Calls: on = the seed 0 chain of all_on (all chains for `vote`), off = the off run's chain. Full GT.

| change | table F1 on | table F1 off | grouping F1 on | grouping F1 off | GT columns placed on | GT columns placed off | GT in rest on | GT in rest off | PK (a) on | PK (a) off | link recall on | link recall off | calls on | calls off |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entity_hint | 0.750 | 0.727 | 1.000 | 0.305 | 14/50 (0.280) | 18/54 (0.333) | 13/50 (0.260) | 9/54 (0.167) | 1/3 (0.333) | 2/4 (0.500) | n/a | 0/2 (0.000) | 3 | 5 |
| other_choice | 0.750 | 0.667 | 1.000 | 0.733 | 14/50 (0.280) | 24/50 (0.480) | 13/50 (0.260) | 0/50 (0.000) | 1/3 (0.333) | 0/3 (0.000) | n/a | n/a | 3 | 6 |
| key_candidates | 0.750 | 0.750 | 1.000 | 1.000 | 14/50 (0.280) | 15/50 (0.300) | 13/50 (0.260) | 12/50 (0.240) | 1/3 (0.333) | 1/3 (0.333) | n/a | n/a | 3 | 5 |
| code_links | 0.750 | 0.750 | 1.000 | 1.000 | 14/50 (0.280) | 15/50 (0.300) | 13/50 (0.260) | 12/50 (0.240) | 1/3 (0.333) | 1/3 (0.333) | n/a | n/a | 3 | 6 |
| vote | 0.750 | 0.750 | 1.000 | 1.000 | 15/50 (0.300) | 14/50 (0.280) | 12/50 (0.240) | 13/50 (0.260) | 1/3 (0.333) | 1/3 (0.333) | n/a | n/a | 62 | 3 |
