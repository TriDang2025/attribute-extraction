# wf_v3.7 duplicate columns at L2 (rules v1.1)

Column = a distinct output attribute name (case, `_`, `-` and space equal) of a group that is not marked not_attribute / unsure / attribute_cue. Columns per found attribute = the number of distinct column names whose group has that found attribute as majority L2 label (a group with no L2 majority is in no count). Found = purity >= 0.6 and coverage >= 10% (rules v1). Pooled over train, hotel, restaurant.

| variant | found | columns per found attribute (mean) | max | attributes with >= 2 columns |
|---|---|---|---|---|
| A r1 | 31 | 1.677 | 4 | 16 |
| A r2 | 30 | 1.700 | 4 | 15 |
| A s2 | 31 | 1.710 | 4 | 17 |
| A s012 | 31 | 1.742 | 4 | 17 |
| AE s012 | 30 | 1.733 | 4 | 16 |
| Oracle s012 | 31 | 1.548 | 3 | 12 |
| E1 s012 | 29 | 1.345 | 4 | 8 |

## Attributes with 2 or more columns

| variant | ent | attribute | columns |
|---|---|---|---|
| A r1 | train | Train departure | 4: arrival location | departure location | local information center | origin city |
| A r1 | train | Train leave at | 2: arrival time | departure time |
| A r1 | train | Train requested people | 3: number of people | number of tickets | number of trains |
| A r1 | train | Train duration | 2: travel time | travel time minutes |
| A r1 | train | Train price | 2: price per ticket | total fee |
| A r1 | hotel | Hotel area | 3: location | location description | location reference |
| A r1 | hotel | Hotel name | 2: hotel name | specific hotel name |
| A r1 | hotel | Hotel price range | 3: price adjective | price extreme | price range |
| A r1 | hotel | Hotel requested day | 2: date | start date |
| A r1 | hotel | Hotel type | 2: hotel type | star rating |
| A r1 | restaurant | Restaurant area | 2: location | restaurant area |
| A r1 | restaurant | Restaurant food | 2: restaurant food type | restaurant type |
| A r1 | restaurant | Restaurant requested people | 2: number of people | number of results |
| A r1 | restaurant | Restaurant requested time | 2: time for reservation | time for taxi |
| A r1 | restaurant | Restaurant phone | 2: restaurant phone number | taxi phone numbers |
| A r1 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
| A r2 | train | Train departure | 4: arrival location | departure location | local information center | origin city |
| A r2 | train | Train leave at | 2: arrival time | departure time |
| A r2 | train | Train duration | 2: travel time | travel time minutes |
| A r2 | train | Train price | 3: price | price per ticket | total fee |
| A r2 | hotel | Hotel area | 4: hotel location | location | location description | location reference |
| A r2 | hotel | Hotel name | 2: hotel name | specific hotel name |
| A r2 | hotel | Hotel price range | 3: price adjective | price extreme | price range |
| A r2 | hotel | Hotel requested day | 2: date | hotel check in date |
| A r2 | hotel | Hotel type | 2: hotel type | star rating |
| A r2 | restaurant | Restaurant area | 2: location | restaurant location |
| A r2 | restaurant | Restaurant food | 2: restaurant food type | restaurant type |
| A r2 | restaurant | Restaurant requested people | 2: number of people | number of results |
| A r2 | restaurant | Restaurant requested time | 2: time for reservation | time for taxi |
| A r2 | restaurant | Restaurant phone | 2: restaurant phone number | taxi phone numbers |
| A r2 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
| A s2 | train | Train departure | 3: departure station | local information center | origin city |
| A s2 | train | Train leave at | 2: arrival time | departure time |
| A s2 | train | Train requested people | 3: number of people | number of tickets | number of trains |
| A s2 | train | Train duration | 2: travel time | travel time minutes |
| A s2 | train | Train price | 2: price per ticket | total fee |
| A s2 | hotel | Hotel area | 4: hotel location | location | location description | location reference |
| A s2 | hotel | Hotel name | 2: hotel name | specific hotel name |
| A s2 | hotel | Hotel price range | 3: price adjective | price extreme | price range |
| A s2 | hotel | Hotel requested day | 2: date | hotel start date |
| A s2 | hotel | Hotel requested people | 2: hotel number of guests | hotel number of options |
| A s2 | hotel | Hotel type | 2: hotel type | star rating |
| A s2 | restaurant | Restaurant area | 2: location | restaurant location |
| A s2 | restaurant | Restaurant food | 2: restaurant food type | restaurant type |
| A s2 | restaurant | Restaurant requested people | 2: number of people | number of results |
| A s2 | restaurant | Restaurant requested time | 2: time for reservation | time for taxi |
| A s2 | restaurant | Restaurant phone | 2: restaurant phone number | taxi phone numbers |
| A s2 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
| A s012 | train | Train departure | 4: arrival location | departure location | local information center | origin city |
| A s012 | train | Train leave at | 2: arrival time | departure time |
| A s012 | train | Train requested people | 3: number of people | number of tickets | number of trains |
| A s012 | train | Train duration | 2: travel time | travel time minutes |
| A s012 | train | Train price | 2: price per ticket | total fee |
| A s012 | hotel | Hotel area | 4: hotel location | location | location description | location reference |
| A s012 | hotel | Hotel name | 2: hotel name | specific hotel name |
| A s012 | hotel | Hotel price range | 3: price adjective | price extreme | price range |
| A s012 | hotel | Hotel requested day | 2: date | start date |
| A s012 | hotel | Hotel type | 2: hotel type | star rating |
| A s012 | restaurant | Restaurant area | 2: location | restaurant location |
| A s012 | restaurant | Restaurant food | 2: restaurant food type | restaurant type |
| A s012 | restaurant | Restaurant requested people | 2: number of people | number of results |
| A s012 | restaurant | Restaurant requested time | 2: time for reservation | time for taxi |
| A s012 | restaurant | Restaurant address | 2: restaurant address | restaurant area |
| A s012 | restaurant | Restaurant phone | 2: restaurant phone number | taxi phone numbers |
| A s012 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
| AE s012 | train | Train departure | 4: arrival location | departure location | local information center | origin city |
| AE s012 | train | Train leave at | 2: arrival time | departure time |
| AE s012 | train | Train requested people | 3: number of people | number of tickets | number of trains |
| AE s012 | train | Train duration | 2: travel time | travel time minutes |
| AE s012 | train | Train price | 2: price per ticket | total fee |
| AE s012 | hotel | Hotel area | 4: hotel location | location | location description | location reference |
| AE s012 | hotel | Hotel name | 2: hotel name | specific hotel name |
| AE s012 | hotel | Hotel price range | 3: price adjective | price extreme | price range |
| AE s012 | hotel | Hotel requested day | 2: date | start date |
| AE s012 | hotel | Hotel type | 2: hotel type | star rating |
| AE s012 | restaurant | Restaurant area | 2: location | restaurant location |
| AE s012 | restaurant | Restaurant food | 2: restaurant food type | restaurant type |
| AE s012 | restaurant | Restaurant requested people | 2: number of people | number of results |
| AE s012 | restaurant | Restaurant requested time | 2: time for reservation | time for taxi |
| AE s012 | restaurant | Restaurant phone | 2: restaurant phone number | taxi phone numbers |
| AE s012 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
| Oracle s012 | hotel | Hotel area | 3: location | location description | location reference |
| Oracle s012 | hotel | Hotel name | 2: hotel name | specific hotel name |
| Oracle s012 | hotel | Hotel price range | 3: price adjective | price extreme | price range |
| Oracle s012 | hotel | Hotel requested day | 2: date | start date |
| Oracle s012 | hotel | Hotel type | 2: hotel type | star rating |
| Oracle s012 | restaurant | Restaurant area | 3: location | restaurant city | restaurant location |
| Oracle s012 | restaurant | Restaurant food | 3: cuisine type | restaurant food type | restaurant type |
| Oracle s012 | restaurant | Restaurant requested people | 2: number of people | number of results |
| Oracle s012 | restaurant | Restaurant requested time | 2: time for reservation | time for taxi |
| Oracle s012 | restaurant | Restaurant address | 3: address | restaurant address | restaurant location |
| Oracle s012 | restaurant | Restaurant phone | 2: restaurant phone number | taxi phone numbers |
| Oracle s012 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
| E1 s012 | train | Train departure | 4: departure location | destination | local information center | origin city |
| E1 s012 | train | Train duration | 2: travel time | travel time minutes |
| E1 s012 | train | Train price | 2: price | price per ticket |
| E1 s012 | hotel | Hotel name | 2: hotel name | specific hotel name |
| E1 s012 | hotel | Hotel type | 2: hotel type | star rating |
| E1 s012 | restaurant | Restaurant food | 2: restaurant food type | restaurant type |
| E1 s012 | restaurant | Restaurant address | 2: restaurant address | restaurant area |
| E1 s012 | restaurant | Restaurant postcode | 2: postcode | restaurant postcode |
