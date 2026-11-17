# Loop 2 (8B design), c_n50b

Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5, min_votes=2.

## Step 1b verdicts (flags are marks; nothing is dropped)

| entity | attributes | flagged | orders answered (verdicts / missing) |
|---|---|---|---|
| train_schedule | 16 | 8 | 3 / 3 |
| accommodation_option | 21 | 6 | 3 / 3 |
| location | 9 | 4 | 3 / 3 |
| establishment | 23 | 5 | 3 / 3 |
| phone_number | 9 | 5 | 3 / 3 |

## Suggested names

| entity | name | votes | result | failed at | reason |
|---|---|---|---|---|---|
| train_schedule | class | 3 | fail | evidence | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | operator | 3 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'time str') |
| train_schedule | route | 3 | fail | evidence | overlap 0.818 >= 0.5 (mostly column 'destination') |
| train_schedule | delay | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | frequency | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | stops | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | train type | 2 | fail | evidence | overlap 0.625 >= 0.5 (mostly column 'time str') |
| train_schedule | platform | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_schedule | arrival station | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_schedule | cancellation policy | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_schedule | change fee | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_schedule | departure station | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_schedule | meal options | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| train_schedule | refund policy | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | amenities | 3 | pass |  | new column amenities |
| accommodation_option | parking | 2 | pass |  | new column amenities |
| accommodation_option | price | 2 | fail | evidence | overlap 0.500 >= 0.5 (mostly column 'num people') |
| accommodation_option | room type | 2 | fail | evidence | overlap 0.857 >= 0.5 (mostly column 'type') |
| accommodation_option | breakfast included | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | checkin time | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | checkout time | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | breakfast | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | dining | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | internet | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | number of rooms | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | price range | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | wifi | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging address | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging checkin date | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging location | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging name | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging rating | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging reference | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| accommodation_option | lodging type | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | directions | 3 | fail | dupcheck | duplicate of address (same name) |
| location | hours of operation | 3 | fail | evidence | no spans |
| location | map | 3 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'address') |
| location | opening hours | 3 | fail | evidence | no spans |
| location | transportation | 2 | fail | evidence | n_dialogues 2 < 3 |
| location | accessibility | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | hours | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | nearest station | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | parking | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | closing time | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | distance | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | hours of business | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | opening time | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | address line 2 | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | city | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | country | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | latitude | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | longitude | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| location | state | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | address | 3 | fail | evidence | overlap 0.733 >= 0.5 (mostly column 'restaurant name') |
| establishment | amenities | 3 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'location str') |
| establishment | hours | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time') |
| establishment | area | 2 | pass |  | new column area |
| establishment | entree fee | 2 | fail | evidence | n_dialogues 1 < 3; support 0.034 < 0.05 |
| establishment | rating | 2 | fail | dupcheck | duplicate of price range (same name) |
| establishment | review | 2 | fail | evidence | n_dialogues 1 < 3; support 0.034 < 0.05 |
| establishment | hours of operation | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time') |
| establishment | parking | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | type | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | opening hours | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | services | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | area of expertise | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | capacity | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| establishment | loan period | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | area code | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | country code | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | extension | 2 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | operator | 2 | fail | evidence | n_dialogues 1 < 3; support 0.048 < 0.05 |
| phone_number | prefix | 2 | fail | evidence | overlap 0.600 >= 0.5 (mostly column 'time str') |
| phone_number | service provider | 2 | pass |  | new column pickup_time |
| phone_number | call date | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | call duration | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | call purpose | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | call status | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | call type | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | caller id | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | caller location | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | caller name | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | caller number | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | account number | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | international dialing code | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | suffix | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | rate | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
| phone_number | type | 1 | fail | vote | suggested in 1 of 3 orders (needs 2) |
