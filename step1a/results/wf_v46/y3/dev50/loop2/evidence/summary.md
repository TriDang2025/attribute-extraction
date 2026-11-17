# Loop 2 named probe, c_n50

Labels: `/content/attribute-extraction/step1a/results/wf_v46/y3/dev50/loop2/step1b/labels.json`; run 15 s. Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5.
Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.

| entity | labels | kept | dropped |
|---|---|---|---|
| accommodation | 7 | 2 | 5 |
| train_info | 8 | 0 | 8 |
| food_establishment | 9 | 0 | 9 |
| address | 8 | 1 | 7 |
| location | 10 | 0 | 10 |

| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |
|---|---|---|---|---|---|---|---|---|---|
| L2_accommodation#0 | address | drop | 9 | 4 | 0.217 | 0.461 | 0.67 (reservation number) | e6uvd9ol, alexander, alexander bed and breakfast | overlap 0.667 >= 0.5 (mostly column 'reservation number') |
| L2_accommodation#1 | amenities | keep | 8 | 5 | 0.217 | 0.789 | 0.00 (-) | free parking, free internet, parking | all checks passed |
| L2_accommodation#2 | check in time | drop | 7 | 6 | 0.261 | 0.888 | 1.00 (day of week) | wednesday, friday, saturday | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| L2_accommodation#3 | check out time | drop | 9 | 8 | 0.348 | 0.877 | 1.00 (day of week) | wednesday, friday, thursday | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| L2_accommodation#4 | rating | keep | 14 | 8 | 0.348 | 0.801 | 0.43 (entity) | 4 star, 4 star rating, 5 star | all checks passed |
| L2_accommodation#5 | room type | drop | 8 | 6 | 0.304 | 0.643 | 0.75 (entity) | guesthouse, 4 star hotel, centre | overlap 0.750 >= 0.5 (mostly column 'entity') |
| L2_accommodation#6 | cancellation policy | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_train_info#0 | route | drop | 4 | 3 | 0.103 | 0.542 | 0.75 (location abbr) | train, cambridge, tr4679 | overlap 0.750 >= 0.5 (mostly column 'location abbr') |
| L2_train_info#1 | train number | drop | 21 | 14 | 0.483 | 0.511 | 0.71 (time int) | 19:30, reference number, 08:30 | overlap 0.714 >= 0.5 (mostly column 'time int') |
| L2_train_info#2 | train type | drop | 11 | 8 | 0.276 | 0.650 | 0.55 (time int) | train, tr1719, tr4679 | overlap 0.545 >= 0.5 (mostly column 'time int') |
| L2_train_info#3 | arrival location | drop | 11 | 9 | 0.310 | 0.487 | 0.91 (location str) | stansted airport, cambridge, 69luuzq7 | overlap 0.909 >= 0.5 (mostly column 'location str') |
| L2_train_info#4 | arrival time | drop | 23 | 16 | 0.552 | 0.758 | 0.96 (time str) | 18:15, 13:15, 08:30 | overlap 0.957 >= 0.5 (mostly column 'time str') |
| L2_train_info#5 | train operator | drop | 4 | 3 | 0.103 | 0.640 | 1.00 (time int) | tr1719, tr8167, tr8598 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_train_info#6 | class | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_train_info#7 | seat availability | drop | 1 | 1 | 0.034 | - | 1.00 (booking id) | rjoua7e1 | n_dialogues 1 < 3; support 0.034 < 0.05; overlap 1.000 >= 0.5 (mostly column 'booking id') |
| L2_food_establishment#0 | hours | drop | 33 | 15 | 0.429 | 0.698 | 1.00 (time int) | 18:00, wednesday, 15 minute | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#1 | hours of business | drop | 13 | 9 | 0.257 | 0.751 | 1.00 (time int) | 18:00, 15:15, 03:15 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#2 | hours of operation | drop | 12 | 7 | 0.229 | 0.737 | 1.00 (time int) | 18:00, 15:15, 03:15 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#3 | hours of operation time | drop | 18 | 11 | 0.371 | 0.761 | 1.00 (time int) | 15:15, 18:00, 17:45 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#4 | hours of service | drop | 4 | 4 | 0.114 | 0.690 | 1.00 (reservation time) | 15 minute, 03:15, 17:45 | overlap 1.000 >= 0.5 (mostly column 'reservation time') |
| L2_food_establishment#5 | hours of work | drop | 2 | 2 | 0.057 | 1.000 | 1.00 (reservation time) | 15 minute | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'reservation time') |
| L2_food_establishment#6 | opening hours | drop | 10 | 7 | 0.200 | 0.784 | 1.00 (time int) | 18:00, 15:15, 03:15 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#7 | hours of opening | drop | 11 | 8 | 0.229 | 0.781 | 1.00 (time int) | 18:00, 15:15, 03:15 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#8 | hours of operation period | drop | 1 | 1 | 0.029 | - | 1.00 (day of week) | thursday | n_dialogues 1 < 3; support 0.029 < 0.05; overlap 1.000 >= 0.5 (mostly column 'day of week') |
| L2_address#0 | city | drop | 5 | 4 | 0.190 | 0.738 | 1.00 (location abbrev) | town, cambridge, city | overlap 1.000 >= 0.5 (mostly column 'location abbrev') |
| L2_address#1 | country | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_address#2 | latitude | drop | 3 | 3 | 0.143 | 0.586 | 0.67 (location) | south, cb11pt | overlap 0.667 >= 0.5 (mostly column 'location') |
| L2_address#3 | longitude | drop | 2 | 2 | 0.095 | 1.000 | 0.50 (location) | south | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| L2_address#4 | state | drop | 2 | 2 | 0.095 | 1.000 | 0.50 (location) | south | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| L2_address#5 | directions | keep | 11 | 8 | 0.381 | 0.533 | 0.45 (address) | address, bar hill, cb30lx | all checks passed |
| L2_address#6 | opening hours | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_address#7 | phone number | drop | 6 | 5 | 0.238 | 0.610 | 0.50 (address) | 01223 244277, 01223314960, 01223364222 | overlap 0.500 >= 0.5 (mostly column 'address') |
| L2_location#0 | address | drop | 2 | 2 | 0.200 | 0.370 | 1.00 (attraction name) | all saint church, cambridge towninfo centre | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'attraction name') |
| L2_location#1 | food options | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#2 | opening hours | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#3 | parking | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#4 | restrooms | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#5 | wheelchair accessibility | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#6 | entry fee | drop | 2 | 1 | 0.100 | 0.819 | 0.50 (attraction name) | entrance fee, free admission | n_dialogues 1 < 3; overlap 0.500 >= 0.5 (mostly column 'attraction name') |
| L2_location#7 | hours of operation | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#8 | phone number | drop | 1 | 1 | 0.100 | - | 1.00 (reference number) | pu74excq | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'reference number') |
| L2_location#9 | website | drop | 2 | 2 | 0.200 | 0.285 | 1.00 (reference number) | cambridge towninfo centre, pu74excq | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'reference number') |
