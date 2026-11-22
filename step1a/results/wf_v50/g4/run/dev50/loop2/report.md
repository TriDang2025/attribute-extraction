# Loop 2 (8B design), c_n50

Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5, min_votes=1.

## Step 1b verdicts (flags are marks; nothing is dropped)

| entity | attributes | flagged | orders answered (verdicts / missing) |
|---|---|---|---|
| accommodation | 23 | 11 | 3 / 3 |
| train_info | 21 | 6 | 3 / 3 |
| food_establishment | 19 | 7 | 3 / 3 |
| address | 13 | 6 | 3 / 3 |
| location | 2 | 1 | 3 / 3 |

## Suggested names

| entity | name | votes | result | failed at | reason |
|---|---|---|---|---|---|
| accommodation | address | 3 | fail | evidence | overlap 0.800 >= 0.5 (mostly column 'area') |
| accommodation | amenities | 3 | pass |  | new column amenities |
| accommodation | cancellation policy | 3 | fail | evidence | no spans |
| accommodation | check in time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| accommodation | check out time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| accommodation | rating | 3 | pass |  | new column rating |
| accommodation | breakfast options | 2 | fail | evidence | n_dialogues 1 < 3; support 0.043 < 0.05; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| accommodation | internet options | 1 | pass |  | new column internet_options |
| accommodation | parking options | 1 | pass |  | new column parking_options |
| accommodation | pet policy | 1 | fail | evidence | no spans |
| accommodation | breakfast | 1 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| accommodation | internet | 1 | pass |  | new column internet |
| accommodation | parking | 1 | pass |  | new column parking |
| accommodation | pets | 1 | fail | evidence | n_dialogues 1 < 3; support 0.043 < 0.05; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| accommodation | room type | 1 | fail | evidence | overlap 0.727 >= 0.5 (mostly column 'entity') |
| train_info | mileage limit | 3 | fail | evidence | no spans |
| train_info | route | 3 | fail | dupcheck | duplicate of departure station (same name) |
| train_info | train operator | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| train_info | train type | 3 | fail | evidence | overlap 0.538 >= 0.5 (mostly column 'time int') |
| train_info | class | 2 | fail | evidence | no spans |
| train_info | number of stops | 1 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'departure time') |
| train_info | seat availability | 1 | fail | evidence | n_dialogues 1 < 3; support 0.034 < 0.05; overlap 1.000 >= 0.5 (mostly column 'time int') |
| train_info | arrival location | 1 | fail | evidence | overlap 0.941 >= 0.5 (mostly column 'location str') |
| train_info | train schedule | 1 | fail | evidence | overlap 0.714 >= 0.5 (mostly column 'time int') |
| train_info | seating capacity | 1 | pass |  | new column seating_capacity |
| train_info | stops | 1 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | capacity | 3 | fail | evidence | overlap 0.875 >= 0.5 (mostly column 'time str') |
| food_establishment | hours of operation | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | menu | 3 | pass |  | new column menu_type |
| food_establishment | rating | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'price') |
| food_establishment | delivery | 2 | fail | evidence | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'restaurant name') |
| food_establishment | outdoor seating | 2 | fail | evidence | n_dialogues 1 < 3; support 0.029 < 0.05; overlap 1.000 >= 0.5 (mostly column 'address') |
| food_establishment | parking | 2 | fail | evidence | no spans |
| food_establishment | takeaway | 2 | fail | evidence | overlap 0.706 >= 0.5 (mostly column 'restaurant name') |
| food_establishment | wheelchair accessibility | 2 | fail | evidence | no spans |
| food_establishment | hours of operation day | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| food_establishment | hours of operation day of week | 1 | fail | check | name longer than 4 words |
| food_establishment | hours of operation duration | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of operation int | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of operation str | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of operation time | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| address | city | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'location abbrev') |
| address | country | 3 | fail | evidence | no spans |
| address | latitude | 3 | fail | evidence | overlap 0.667 >= 0.5 (mostly column 'postcode') |
| address | longitude | 3 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| address | state | 3 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| address | apartment number | 2 | fail | evidence | overlap 0.778 >= 0.5 (mostly column 'address') |
| address | floor number | 2 | fail | evidence | overlap 0.714 >= 0.5 (mostly column 'address') |
| address | house number | 2 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'address') |
| address | zip code | 2 | fail | evidence | overlap 0.688 >= 0.5 (mostly column 'address') |
| address | building name | 1 | fail | evidence | overlap 0.923 >= 0.5 (mostly column 'location') |
| address | postal code type | 1 | fail | evidence | overlap 0.812 >= 0.5 (mostly column 'address') |
| address | street number | 1 | fail | evidence | overlap 0.812 >= 0.5 (mostly column 'address') |
| address | neighborhood | 1 | fail | evidence | overlap 0.960 >= 0.5 (mostly column 'location') |
| address | street type | 1 | fail | evidence | overlap 0.857 >= 0.5 (mostly column 'location') |
| location | address | 3 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'attraction name') |
| location | audio guides | 3 | fail | evidence | no spans |
| location | food options | 3 | fail | evidence | no spans |
| location | guided tours | 3 | fail | evidence | no spans |
| location | opening hours | 3 | fail | evidence | no spans |
| location | parking options | 3 | fail | evidence | no spans |
| location | restrooms | 3 | fail | evidence | no spans |
| location | wheelchair accessibility | 3 | fail | evidence | no spans |
| location | audio descriptions | 2 | fail | evidence | no spans |
| location | entrance fee | 2 | fail | evidence | n_dialogues 1 < 3; overlap 0.500 >= 0.5 (mostly column 'attraction name') |
| location | entry fee | 1 | fail | evidence | n_dialogues 1 < 3; overlap 0.500 >= 0.5 (mostly column 'attraction name') |
| location | special events | 1 | fail | evidence | no spans |
