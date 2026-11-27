# Loop 2 (8B design), c_n50b

Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5, min_votes=1.

## Step 1b verdicts (flags are marks; nothing is dropped)

| entity | attributes | flagged | orders answered (verdicts / missing) |
|---|---|---|---|
| train_schedule | 16 | 8 | 3 / 3 |
| accommodation_option | 21 | 6 | 3 / 3 |
| location | 9 | 4 | 3 / 3 |
| establishment | 23 | 6 | 3 / 3 |
| phone_number | 9 | 5 | 3 / 3 |

## Suggested names

| entity | name | votes | result | failed at | reason |
|---|---|---|---|---|---|
| train_schedule | arrival station | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'destination') |
| train_schedule | departure station | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'destination') |
| train_schedule | frequency | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | operator | 3 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'time str') |
| train_schedule | route | 3 | fail | evidence | overlap 0.778 >= 0.5 (mostly column 'destination') |
| train_schedule | class | 2 | fail | evidence | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | train type | 2 | fail | evidence | overlap 0.571 >= 0.5 (mostly column 'time str') |
| train_schedule | mileage limit | 2 | fail | evidence | no spans |
| train_schedule | delay | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | mileage | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| train_schedule | duration | 1 | fail | evidence | overlap 0.966 >= 0.5 (mostly column 'time str') |
| train_schedule | stops | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'destination') |
| accommodation_option | amenities | 3 | pass |  | new column amenities |
| accommodation_option | breakfast | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'location') |
| accommodation_option | cancellation policy | 3 | fail | evidence | no spans |
| accommodation_option | checkin time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'checkin date') |
| accommodation_option | checkout time | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'day') |
| accommodation_option | internet | 3 | pass |  | new column internet |
| accommodation_option | parking | 3 | pass |  | new column parking |
| accommodation_option | price range | 3 | pass |  | new column price_range |
| accommodation_option | payment method | 2 | fail | evidence | no spans |
| accommodation_option | smoking policy | 2 | fail | evidence | no spans |
| accommodation_option | facilities | 1 | pass |  | new column facilities |
| accommodation_option | services | 1 | pass |  | new column services |
| location | capacity | 3 | fail | evidence | no spans |
| location | directions | 3 | fail | dupcheck | duplicate of address (dupcheck, both orders) |
| location | opening hours | 3 | fail | evidence | no spans |
| location | parking | 3 | fail | evidence | n_dialogues 2 < 3 |
| location | accessibility | 2 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'address') |
| location | amenities | 2 | fail | dupcheck | duplicate of entrance fee (dupcheck, both orders) |
| location | distance | 2 | fail | evidence | n_dialogues 2 < 3 |
| location | address | 1 | fail | check | repeats an existing attribute name |
| location | transportation | 1 | fail | evidence | n_dialogues 2 < 3 |
| location | hours of operation | 1 | fail | evidence | no spans |
| location | layout | 1 | fail | evidence | overlap 0.857 >= 0.5 (mostly column 'location') |
| location | size | 1 | fail | evidence | n_dialogues 1 < 3 |
| location | address type | 1 | fail | evidence | overlap 0.800 >= 0.5 (mostly column 'address') |
| location | nearest landmark | 1 | fail | evidence | overlap 0.929 >= 0.5 (mostly column 'location') |
| location | transport links | 1 | fail | evidence | no spans |
| location | wheelchair accessibility | 1 | fail | evidence | no spans |
| establishment | address | 3 | fail | evidence | overlap 0.762 >= 0.5 (mostly column 'restaurant name') |
| establishment | amenities | 3 | fail | evidence | overlap 0.750 >= 0.5 (mostly column 'location str') |
| establishment | hours of operation | 3 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time') |
| establishment | rating | 3 | fail | evidence | overlap 0.857 >= 0.5 (mostly column 'price range') |
| establishment | entertainment options | 2 | fail | evidence | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'restaurant name') |
| establishment | parking | 2 | fail | evidence | no spans |
| establishment | wheelchair accessibility | 2 | fail | evidence | no spans |
| establishment | capacity | 2 | fail | evidence | overlap 0.778 >= 0.5 (mostly column 'num people') |
| establishment | menu | 1 | pass |  | new column cuisine_type |
| establishment | cuisine type | 1 | pass |  | new column cuisine_type |
| establishment | parking options | 1 | fail | evidence | no spans |
| establishment | reservations policy | 1 | fail | evidence | no spans |
| phone_number | call purpose | 2 | fail | evidence | n_dialogues 2 < 3 |
| phone_number | caller location | 2 | fail | evidence | overlap 0.933 >= 0.5 (mostly column 'time str') |
| phone_number | caller name | 2 | fail | evidence | overlap 0.846 >= 0.5 (mostly column 'time str') |
| phone_number | call date | 1 | fail | evidence | overlap 0.800 >= 0.5 (mostly column 'arrival time') |
| phone_number | call duration | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'arrival time') |
| phone_number | call status | 1 | fail | evidence | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'arrival time') |
| phone_number | call type | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | caller id | 1 | fail | evidence | overlap 0.857 >= 0.5 (mostly column 'time str') |
| phone_number | caller number | 1 | fail | evidence | overlap 0.929 >= 0.5 (mostly column 'time str') |
| phone_number | caller type | 1 | fail | evidence | overlap 0.500 >= 0.5 (mostly column 'time str') |
| phone_number | caller s contact method | 1 | fail | evidence | overlap 0.923 >= 0.5 (mostly column 'time str') |
| phone_number | caller s phone number | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | driver s name | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | driver s phone number | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | payment method | 1 | fail | evidence | n_dialogues 1 < 3; support 0.048 < 0.05 |
| phone_number | taxi company name | 1 | fail | evidence | overlap 0.929 >= 0.5 (mostly column 'time str') |
| phone_number | area code | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | country code | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | extension | 1 | fail | evidence | overlap 1.000 >= 0.5 (mostly column 'time str') |
| phone_number | operator | 1 | fail | evidence | overlap 0.600 >= 0.5 (mostly column 'time str') |
| phone_number | rate plan | 1 | fail | evidence | no spans |
| phone_number | status | 1 | fail | evidence | n_dialogues 1 < 3; support 0.048 < 0.05 |
| phone_number | type | 1 | pass |  | new column contact_number |
