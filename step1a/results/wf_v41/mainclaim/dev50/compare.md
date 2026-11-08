# wf_v4.1 main claim: attribute lists on dev50 (gold = L2, rules v1.3)

Found = gold attributes found (rules_groups.found: purity 0.6, coverage 0.10); new = items whose majority label is empty or no gold attribute (to be checked by hand, `human_check_sheet.csv`).

| source | train found | hotel found | restaurant found | all found | new items | new mentions |
|---|---|---|---|---|---|---|
| loop1 | 8/10 (0.800) | 12/14 (0.857) | 11/16 (0.688) | 31/40 (0.775) | 12 | 52 |
| loop2 | 8/10 (0.800) | 12/14 (0.857) | 11/16 (0.688) | 31/40 (0.775) | 15 | 81 |

## Gold attributes found by source

| entity | gold attribute | loop1 | loop2 |
|---|---|---|---|
| train | Train arrive by | no | no |
| train | Train confirmed reference | yes | yes |
| train | Train day | yes | yes |
| train | Train departure | yes | yes |
| train | Train destination | no | no |
| train | Train leave at | yes | yes |
| train | Train requested people | yes | yes |
| train | Train duration | yes | yes |
| train | Train price | yes | yes |
| train | Train trainid | yes | yes |
| hotel | Hotel area | yes | yes |
| hotel | Hotel confirmed reference | yes | yes |
| hotel | Hotel internet | no | no |
| hotel | Hotel name | yes | yes |
| hotel | Hotel parking | no | no |
| hotel | Hotel price range | yes | yes |
| hotel | Hotel requested day | yes | yes |
| hotel | Hotel requested people | yes | yes |
| hotel | Hotel requested stay | yes | yes |
| hotel | Hotel stars | yes | yes |
| hotel | Hotel type | yes | yes |
| hotel | Hotel address | yes | yes |
| hotel | Hotel phone | yes | yes |
| hotel | Hotel postcode | yes | yes |
| restaurant | Restaurant area | yes | yes |
| restaurant | Restaurant confirmed reference | yes | yes |
| restaurant | Restaurant food | yes | yes |
| restaurant | Restaurant name | yes | yes |
| restaurant | Restaurant price range | yes | yes |
| restaurant | Restaurant requested day | yes | yes |
| restaurant | Restaurant requested people | yes | yes |
| restaurant | Restaurant requested time | yes | yes |
| restaurant | Taxi arrive by | no | no |
| restaurant | Taxi departure | no | no |
| restaurant | Taxi destination | no | no |
| restaurant | Taxi leave at | no | no |
| restaurant | Restaurant address | yes | yes |
| restaurant | Restaurant phone | yes | yes |
| restaurant | Restaurant postcode | yes | yes |
| restaurant | Taxi phone | no | no |

## Notes

- Gold attributes: train 10, hotel 14, restaurant 16 (total 40); STEP3.md: 31/40 found by the frozen handover.
- Loop 1: 31/40 found by groups (STEP3.md 31/40: equal); 55 columns, 12 new.
- Loop 2: 25 clusters, 3 kept; 44 loop-2 mentions have no GT label, 0 of them in dialogues missing from the spans file (dev50 needs data/mwoz22_spans.csv, not in git: copy it from the wf-v3.6 worktree). Loop 2 = loop 1 + kept clusters.
- TEAR: skipped (no --tear given).
- Spans read: data\mwoz22_spans.csv, results\loop1_v37\dev50b\gt\mwoz22_spans.csv.
