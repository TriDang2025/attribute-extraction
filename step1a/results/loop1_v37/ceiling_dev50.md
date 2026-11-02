# wf_v3.7 Step 1a ceiling at L2

Set: dev50. Base = the L2 base attributes of each entity (ctx.train at L2: the L1 attributes plus the MultiWOZ 2.2 slots that occur in the set). **present** = some mention with that label is in a Step-1a cluster of the entity. **recoverable** = some single cluster passes the found rule of rules v1 (purity >= 0.6 and coverage >= 10%); measured by scoring identity decisions (every cluster its own attribute, nothing marked) through `rules_groups.found`, with the v1.1 mention classes. Reasons for a non-recoverable attribute: never_found (no mention carries it), mixed_roles (the best cluster's top other attribute is its role partner), diluted (anything else).

| entity | base | present | recoverable | never_found | mixed_roles | diluted |
|---|---|---|---|---|---|---|
| train | 10 | 10/10 (1.000) | 7/10 (0.700) | 0 | 1 | 2 |
| hotel | 14 | 12/14 (0.857) | 9/14 (0.643) | 2 | 0 | 3 |
| restaurant | 16 | 16/16 (1.000) | 13/16 (0.812) | 0 | 0 | 3 |
| total | 40 | 38/40 (0.950) | 29/40 (0.725) | 2 | 1 | 8 |

Total: present 38/40 (0.950), recoverable 29/40 (0.725).

## Non-recoverable attributes

| ent | attribute | present | reason | best cluster | purity | coverage | top other attribute |
|---|---|---|---|---|---|---|---|
| train | Train arrive by | True | mixed_roles | E1#1 | 0.35 | 0.97 | Train leave at |
| train | Train destination | True | diluted | E1#6 | 1.00 | 0.05 | - |
| train | Train requested people | True | diluted | E1#14 | 0.50 | 0.60 | - |
| hotel | Hotel internet | False | never_found | - | 0.00 | 0.00 | - |
| hotel | Hotel parking | False | never_found | - | 0.00 | 0.00 | - |
| hotel | Hotel stars | True | diluted | E0#4 | 0.42 | 0.83 | Hotel requested stay |
| hotel | Hotel type | True | diluted | E0#0 | 0.46 | 1.00 | Hotel name |
| hotel | Hotel postcode | True | diluted | E0#6 | 0.06 | 1.00 | Hotel confirmed reference |
| restaurant | Taxi arrive by | True | diluted | E2#10 | 0.11 | 1.00 | Restaurant requested time |
| restaurant | Taxi leave at | True | diluted | E2#10 | 0.07 | 1.00 | Restaurant requested time |
| restaurant | Taxi phone | True | diluted | E2#14 | 0.33 | 1.00 | Restaurant phone |
