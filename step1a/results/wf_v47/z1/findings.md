# Z1 findings: where loop-2 suggestions are lost (v4.6 files, no calls, no gold)

Files: `z1.md` (stop table, from `scripts/loss_v47.py`), `<set>/loss.csv`, `<set>/overlap.csv` (with manual `tag`), `<set>/vote.csv`.
Tags are mine, judged from the names, spans and values only (no gold).

## Stop points (dev50 | dev50b)

vote 27 | 58, overlap 20 | 16, no spans 10 | 2, too few dialogues 9 | 6, duplicate 1 | 2, merged 0 | 1 (parking -> amenities), added 2 | 3. Total 69 | 88.

## Overlap fails (20 | 16)

| tag | dev50 | dev50b | meaning |
|---|---|---|---|
| wrong spans | 12 | 7 | GLiNER spans do not fit the name; they are the values already in a loop-1 column (e.g. 7 "hours" names in dev50 all find booking times) |
| same info | 7 | 6 | really the same information (check in time = booking day, arrival time = time str, area code = full phone numbers) |
| mixed column | 1 | 3 | real information hidden in a mixed loop-1 column: phone number (in "address"), street address (in "restaurant name"), price range (in "num people"), train id (in "time str") |
| same sentences only | 0 | 0 | the case the overlap rule was feared to kill does not occur |

So the overlap rule is mostly right. Value Jaccard would not separate the cases well: wrong-span names also have low Jaccard (train number 0.24, delay 0.17), so Z2 rule 1 alone would let them through.

## Vote fails (27 | 58): all are exactly 1 of 3 orders

| judged by name | dev50 | dev50b |
|---|---|---|
| real-looking | 12 | 22 |
| synonym of another suggestion (amenity / facilities, hours variants, wifi / internet) | 6 | 5 |
| vague, niche or noise (audio guides, latitude, 14 "call ..." names for the taxi entity named phone_number) | 9 | 31 |

- Descriptions are "..." in 17/27 and 51/58: the Step 1b format bug (Z3 fix) leaves nothing to judge but the name.
- Many vote fails are wording splits, not disagreement: one dev50b order wrote every hotel name with a "lodging_" prefix (7 names), others write checkin time vs check in time. A synonym-aware vote would recover some.
- The entity name drives the suggestions: "phone_number" (GT taxi) gets phone-call fields only.

## What this means for Z2 / Z3

- Biggest real loss: vote 1-of-3 (34 real-looking names) and wrong spans (19), not the overlap rule itself.
- Mixed loop-1 columns hide 4 real attributes; a value-based duplicate check will not free them, because their values sit in that column.
- Empty Step 3 split parts (0 mentions) also show up as columns: 5 | 8 (found in Z0).
