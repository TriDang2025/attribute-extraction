# Loop 2 named probe, c_n50

Labels: `/content/attribute-extraction/step1a/results/wf_v47/z4/run2/dev50/loop2/step1b/labels.json`; run 15 s. Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5.
Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.

| entity | labels | kept | dropped |
|---|---|---|---|
| accommodation | 15 | 6 | 9 |
| train_info | 11 | 2 | 9 |
| food_establishment | 14 | 1 | 13 |
| address | 14 | 0 | 14 |
| location | 12 | 0 | 12 |

| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |
|---|---|---|---|---|---|---|---|---|---|
| L2_accommodation#0 | address | drop | 15 | 8 | 0.435 | 0.486 | 0.80 (area) | ashley hotel, alexander bed and breakfast, centre | overlap 0.800 >= 0.5 (mostly column 'area') |
| L2_accommodation#1 | amenities | keep | 11 | 7 | 0.304 | 0.802 | 0.00 (-) | free parking, free internet, free wifi | all checks passed |
| L2_accommodation#2 | cancellation policy | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_accommodation#3 | check in time | drop | 15 | 13 | 0.565 | 0.867 | 1.00 (day of week) | friday, monday, wednesday | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| L2_accommodation#4 | check out time | drop | 12 | 8 | 0.348 | 0.873 | 1.00 (day of week) | wednesday, monday, saturday | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| L2_accommodation#5 | rating | keep | 13 | 9 | 0.391 | 0.803 | 0.31 (entity) | 4 star, 4 star rating, star rating | all checks passed |
| L2_accommodation#6 | breakfast options | drop | 1 | 1 | 0.043 | - | 1.00 (hotel name) | alexander bed and breakfast | n_dialogues 1 < 3; support 0.043 < 0.05; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| L2_accommodation#7 | internet options | keep | 13 | 9 | 0.391 | 0.870 | 0.08 (location) | free wifi, free internet, cityroomz | all checks passed |
| L2_accommodation#8 | parking options | keep | 7 | 4 | 0.174 | 0.924 | 0.00 (-) | free parking, parking | all checks passed |
| L2_accommodation#9 | pet policy | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_accommodation#10 | breakfast | drop | 3 | 2 | 0.087 | 1.000 | 1.00 (hotel name) | alexander bed and breakfast | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| L2_accommodation#11 | internet | keep | 17 | 11 | 0.522 | 0.863 | 0.06 (location) | free wifi, free internet, cityroomz | all checks passed |
| L2_accommodation#12 | parking | keep | 12 | 8 | 0.348 | 0.935 | 0.00 (-) | free parking, parking | all checks passed |
| L2_accommodation#13 | pets | drop | 1 | 1 | 0.043 | - | 1.00 (hotel name) | the finch | n_dialogues 1 < 3; support 0.043 < 0.05; overlap 1.000 >= 0.5 (mostly column 'hotel name') |
| L2_accommodation#14 | room type | drop | 11 | 8 | 0.391 | 0.641 | 0.73 (entity) | guesthouse, 4 star, 4 star guesthouse | overlap 0.727 >= 0.5 (mostly column 'entity') |
| L2_train_info#0 | mileage limit | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_train_info#1 | route | keep | 13 | 11 | 0.379 | 0.659 | 0.46 (location str) | train, cambridge, ely | all checks passed |
| L2_train_info#2 | train operator | drop | 5 | 4 | 0.138 | 0.622 | 1.00 (time int) | tr1719, tr7604, tr8167 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_train_info#3 | train type | drop | 13 | 10 | 0.345 | 0.640 | 0.54 (time int) | train, the train, tr1719 | overlap 0.538 >= 0.5 (mostly column 'time int') |
| L2_train_info#4 | class | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_train_info#5 | number of stops | drop | 2 | 2 | 0.069 | 0.521 | 0.50 (departure time) | 278 train, there are only 4 train | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'departure time') |
| L2_train_info#6 | seat availability | drop | 1 | 1 | 0.034 | - | 1.00 (time int) | tr7610 | n_dialogues 1 < 3; support 0.034 < 0.05; overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_train_info#7 | arrival location | drop | 17 | 14 | 0.483 | 0.556 | 0.94 (location str) | cambridge, stansted airport, airport | overlap 0.941 >= 0.5 (mostly column 'location str') |
| L2_train_info#8 | train schedule | drop | 7 | 6 | 0.207 | 0.543 | 0.71 (time int) | 21:15, friday, our schedule | overlap 0.714 >= 0.5 (mostly column 'time int') |
| L2_train_info#9 | seating capacity | keep | 5 | 4 | 0.138 | 0.703 | 0.00 (-) | 4 people, 4 seat, 5 people | all checks passed |
| L2_train_info#10 | stops | drop | 2 | 2 | 0.069 | 0.597 | 1.00 (time int) | tr7610, tr9448 | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#0 | capacity | drop | 8 | 7 | 0.200 | 0.768 | 0.88 (time str) | 15 minute, 6 people, 4 people | overlap 0.875 >= 0.5 (mostly column 'time str') |
| L2_food_establishment#1 | hours of operation | drop | 7 | 7 | 0.200 | 0.816 | 1.00 (time int) | 18:00, 09:15, 10:00 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#2 | menu | keep | 8 | 6 | 0.171 | 0.688 | 0.25 (cuisine) | indian food, african food, chinese food | all checks passed |
| L2_food_establishment#3 | rating | drop | 3 | 3 | 0.086 | 0.603 | 1.00 (price) | 3, moderately price, moderately priced | overlap 1.000 >= 0.5 (mostly column 'price') |
| L2_food_establishment#4 | delivery | drop | 2 | 1 | 0.057 | 1.000 | 1.00 (restaurant name) | pizza express | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'restaurant name') |
| L2_food_establishment#5 | outdoor seating | drop | 1 | 1 | 0.029 | - | 1.00 (address) | 4 - 6 rose crescent | n_dialogues 1 < 3; support 0.029 < 0.05; overlap 1.000 >= 0.5 (mostly column 'address') |
| L2_food_establishment#6 | parking | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_food_establishment#7 | takeaway | drop | 17 | 14 | 0.400 | 0.562 | 0.71 (restaurant name) | restaurant, expensive restaurant, taxi | overlap 0.706 >= 0.5 (mostly column 'restaurant name') |
| L2_food_establishment#8 | wheelchair accessibility | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_food_establishment#9 | hours of operation day | drop | 11 | 8 | 0.229 | 0.732 | 1.00 (day of week) | thursday, 18:00, 09:15 | overlap 1.000 >= 0.5 (mostly column 'day of week') |
| L2_food_establishment#10 | hours of operation duration | drop | 8 | 7 | 0.200 | 0.694 | 1.00 (time int) | 15 minute, 09:15, 15:00 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#11 | hours of operation int | drop | 5 | 3 | 0.086 | 0.736 | 1.00 (time int) | 15:00, 09:15, 18:00 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#12 | hours of operation str | drop | 6 | 5 | 0.171 | 0.787 | 1.00 (time int) | 18:00, 09:15, 10:00 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_food_establishment#13 | hours of operation time | drop | 12 | 10 | 0.314 | 0.770 | 1.00 (time int) | 15:15, 18:00, 09:15 | overlap 1.000 >= 0.5 (mostly column 'time int') |
| L2_address#0 | city | drop | 3 | 3 | 0.143 | 0.610 | 1.00 (location abbrev) | cambridge, city, town | overlap 1.000 >= 0.5 (mostly column 'location abbrev') |
| L2_address#1 | country | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_address#2 | latitude | drop | 3 | 3 | 0.143 | 0.586 | 0.67 (postcode) | south, cb11pt | overlap 0.667 >= 0.5 (mostly column 'postcode') |
| L2_address#3 | longitude | drop | 2 | 2 | 0.095 | 1.000 | 0.50 (location) | south | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| L2_address#4 | state | drop | 2 | 2 | 0.095 | 1.000 | 0.50 (location) | south | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'location') |
| L2_address#5 | apartment number | drop | 9 | 9 | 0.429 | 0.430 | 0.78 (address) | 01223314960, 01223364222, 01223446100 | overlap 0.778 >= 0.5 (mostly column 'address') |
| L2_address#6 | floor number | drop | 7 | 7 | 0.333 | 0.403 | 0.71 (address) | 01223364222, 01223446100, 6 saint edward's passage | overlap 0.714 >= 0.5 (mostly column 'address') |
| L2_address#7 | house number | drop | 8 | 7 | 0.333 | 0.432 | 0.75 (address) | 01223314960, 01223364222, 01223446100 | overlap 0.750 >= 0.5 (mostly column 'address') |
| L2_address#8 | zip code | drop | 16 | 9 | 0.429 | 0.426 | 0.69 (address) | cb11ln, postcode, 01223446100 | overlap 0.688 >= 0.5 (mostly column 'address') |
| L2_address#9 | building name | drop | 26 | 11 | 0.524 | 0.420 | 0.92 (location) | emmanuel college, hotel felix whitehouse lane, 6 saint edward's passage | overlap 0.923 >= 0.5 (mostly column 'location') |
| L2_address#10 | postal code type | drop | 16 | 11 | 0.524 | 0.419 | 0.81 (address) | 01223314960, 01223364222, 01223446100 | overlap 0.812 >= 0.5 (mostly column 'address') |
| L2_address#11 | street number | drop | 16 | 10 | 0.476 | 0.414 | 0.81 (address) | 01223314960, 01223364222, 01223446100 | overlap 0.812 >= 0.5 (mostly column 'address') |
| L2_address#12 | neighborhood | drop | 25 | 12 | 0.619 | 0.488 | 0.96 (location) | centre of town, 98 king street, abbey pool | overlap 0.960 >= 0.5 (mostly column 'location') |
| L2_address#13 | street type | drop | 7 | 7 | 0.333 | 0.514 | 0.86 (location) | 98 king street, cherry hinton road, clifton way | overlap 0.857 >= 0.5 (mostly column 'location') |
| L2_location#0 | address | drop | 2 | 2 | 0.200 | 0.370 | 1.00 (attraction name) | all saint church, cambridge towninfo centre | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'attraction name') |
| L2_location#1 | audio guides | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#2 | food options | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#3 | guided tours | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#4 | opening hours | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#5 | parking options | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#6 | restrooms | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#7 | wheelchair accessibility | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#8 | audio descriptions | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#9 | entrance fee | drop | 2 | 1 | 0.100 | 0.819 | 0.50 (attraction name) | entrance fee, free admission | n_dialogues 1 < 3; overlap 0.500 >= 0.5 (mostly column 'attraction name') |
| L2_location#10 | entry fee | drop | 2 | 1 | 0.100 | 0.819 | 0.50 (attraction name) | entrance fee, free admission | n_dialogues 1 < 3; overlap 0.500 >= 0.5 (mostly column 'attraction name') |
| L2_location#11 | special events | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
