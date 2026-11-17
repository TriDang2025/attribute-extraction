# Loop 2 (8B design), c_n50

Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5, min_votes=2.

## Step 1b verdicts (flags are marks; nothing is dropped)

| entity | attributes | flagged | orders answered (verdicts / missing) |
|---|---|---|---|
| accommodation | 23 | 9 | 3 / 3 |
| train_info | 21 | 8 | 3 / 3 |
| food_establishment | 19 | 6 | 3 / 3 |
| address | 13 | 10 | 3 / 3 |
| location | 2 | 1 | 3 / 3 |

## Suggested names

| entity | name | votes | result | failed at | reason |
|---|---|---|---|---|---|
| accommodation | address | 3 | fail | evidence | overlap 0.667 >= 0.5 (mostly column 'reservation number') |
| accommodation | amenities | 3 | pass |  | new column amenities |
| accommodation | check in time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| accommodation | check out time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| accommodation | rating | 3 | pass |  | new column star_rating |
| accommodation | room type | 2 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'entity') |
| accommodation | cancellation policy | 2 | fail | evidence | no spans |
| accommodation | amenity | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation | description | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation | type | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation | facilities | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation | services | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation | breakfast included | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_info | route | 3 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'location abbr') |
| train_info | train number | 3 | fail | evidence | overlap 0.714 >= 0.5 (mostly column 'time int') |
| train_info | train type | 3 | fail | evidence | overlap 0.545 >= 0.5 (mostly column 'time int') |
| train_info | arrival location | 2 | fail | evidence | overlap 0.909 >= 0.5 (mostly column 'location str') |
| train_info | arrival time | 2 | fail | evidence | overlap 0.957 >= 0.5 (mostly column 'time str') |
| train_info | train operator | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| train_info | class | 2 | fail | evidence | no spans |
| train_info | seat availability | 2 | fail | evidence | n_dialogues 1 < 3; support 0.034 < 0.05; overlap 1.000 >= 0.5 (mostly column 'booking id') |
| train_info | boarding time | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_info | fare type | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_info | arrival station | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_info | stops | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| food_establishment | hours | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of business | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of operation | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of operation time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of service | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'reservation time') |
| food_establishment | hours of work | 3 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'reservation time') |
| food_establishment | opening hours | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of opening | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time int') |
| food_establishment | hours of operation period | 2 | fail | evidence | n_dialogues 1 < 3; support 0.029 < 0.05; overlap 1.000 >= 0.5 (mostly column 'day of week') |
| food_establishment | hours of operation duration | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| food_establishment | capacity | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| food_establishment | rating | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| food_establishment | business hours | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| food_establishment | service hours | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | city | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'location abbrev') |
| address | country | 3 | fail | evidence | no spans |
| address | latitude | 3 | fail | evidence | overlap 0.667 >= 0.5 (mostly column 'location') |
| address | longitude | 3 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| address | state | 3 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| address | directions | 2 | fail | dupcheck | duplicate of address (same name) |
| address | opening hours | 2 | fail | evidence | no spans |
| address | phone number | 2 | fail | evidence | overlap 0.500 >= 0.5 (mostly column 'address') |
| address | map | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | nearest landmark | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | apartment number | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | building name | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | floor | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | house number | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | parking | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| address | website | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | address | 3 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'attraction name') |
| location | food options | 3 | fail | evidence | no spans |
| location | opening hours | 3 | fail | evidence | no spans |
| location | parking | 3 | fail | evidence | no spans |
| location | restrooms | 3 | fail | evidence | no spans |
| location | wheelchair accessibility | 3 | fail | evidence | no spans |
| location | entry fee | 2 | fail | evidence | n_dialogues 1 < 3; overlap 0.500 >= 0.5 (mostly column 'attraction name') |
| location | hours of operation | 2 | fail | evidence | no spans |
| location | phone number | 2 | fail | evidence | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'reference number') |
| location | website | 2 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'reference number') |
| location | audio descriptions | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | audio guides | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | entrance fee | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | guided tours | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
