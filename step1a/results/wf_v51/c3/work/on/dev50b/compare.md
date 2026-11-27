# wf_v4.1 main claim: attribute lists on dev50b (gold = L2, rules v1.3)

Found (span) = gold attributes found by the mention labels (rules_groups.found: purity 0.6, coverage 0.10). Found (span + human check) also counts a new item whose name matches a gold attribute of its entity and that is marked real in `human_check_sheet.csv` (blind, shuffled; 0/26 rows checked). New = items whose majority label is empty or no gold attribute.

| source | train found (span) | hotel found (span) | restaurant found (span) | taxi found (span) | all found (span) | all found (span + human check) | new items | new mentions |
|---|---|---|---|---|---|---|---|---|
| loop1 | 6/10 (0.600) | 10/14 (0.714) | 10/11 (0.909) | 3/6 (0.500) | 29/41 (0.707) | 29/41 (0.707) | 18 | 85 |
| loop2 | 6/10 (0.600) | 10/14 (0.714) | 10/11 (0.909) | 4/6 (0.667) | 30/41 (0.732) | 30/41 (0.732) | 26 | 204 |

## Gold attributes found by source

yes = by span; check = only by name match + human check.

| entity | gold attribute | loop1 | loop2 |
|---|---|---|---|
| train | Train arrive by | no | no |
| train | Train confirmed reference | yes | yes |
| train | Train day | yes | yes |
| train | Train departure | no | no |
| train | Train destination | no | no |
| train | Train leave at | no | no |
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
| hotel | Hotel type | no | no |
| hotel | Hotel address | yes | yes |
| hotel | Hotel phone | yes | yes |
| hotel | Hotel postcode | no | no |
| restaurant | Restaurant area | yes | yes |
| restaurant | Restaurant confirmed reference | yes | yes |
| restaurant | Restaurant food | yes | yes |
| restaurant | Restaurant name | yes | yes |
| restaurant | Restaurant price range | yes | yes |
| restaurant | Restaurant requested day | yes | yes |
| restaurant | Restaurant requested people | yes | yes |
| restaurant | Restaurant requested time | yes | yes |
| restaurant | Restaurant address | no | no |
| restaurant | Restaurant phone | yes | yes |
| restaurant | Restaurant postcode | yes | yes |
| taxi | Taxi arrive by | no | no |
| taxi | Taxi departure | yes | yes |
| taxi | Taxi destination | yes | yes |
| taxi | Taxi leave at | no | no |
| taxi | Taxi phone | yes | yes |
| taxi | Taxi type | no | yes |

## Notes

- Gold attributes: train 10, hotel 14, restaurant 11, taxi 6 (total 41); STEP3.md: 29/41 found by the frozen handover.
- Loop 1: 29/41 found by groups (STEP3.md 29/41: equal); 69 columns, 18 new.
- Loop 2: 9 clusters, 9 kept; 105 loop-2 mentions have no GT label, 0 of them in dialogues missing from the spans file (dev50 needs data/mwoz22_spans.csv, not in git: copy it from the wf-v3.6 worktree). Loop 2 = loop 1 + kept clusters.
- TEAR: skipped (no --tear given).
- Spans read: data\mwoz22_spans.csv, results\loop1_v37\dev50b\gt\mwoz22_spans.csv.
- Name-match candidates (count only when marked real): Hotel internet (loop2), Hotel parking (loop2), Hotel price range (loop2).
