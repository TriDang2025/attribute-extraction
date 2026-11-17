# Loop 2 named probe, c_n50b

Labels: `/content/attribute-extraction/step1a/results/wf_v46/y3/dev50b/loop2/step1b/labels.json`; run 12 s. Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5.
Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.

| entity | labels | kept | dropped |
|---|---|---|---|
| train_schedule | 7 | 0 | 7 |
| accommodation_option | 4 | 2 | 2 |
| location | 5 | 1 | 4 |
| establishment | 8 | 2 | 6 |
| phone_number | 6 | 1 | 5 |

| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |
|---|---|---|---|---|---|---|---|---|---|
| L2_train_schedule#0 | class | drop | 1 | 1 | 0.056 | - | 1.00 (time str) | tr2289 | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#1 | operator | drop | 4 | 4 | 0.222 | 0.605 | 0.75 (time str) | tr0545, tr2874, tr6357 | overlap 0.750 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#2 | route | drop | 11 | 6 | 0.333 | 0.451 | 0.82 (destination) | birmingham new street, cambridge, destination | overlap 0.818 >= 0.5 (mostly column 'destination') |
| L2_train_schedule#3 | delay | drop | 12 | 8 | 0.444 | 0.759 | 1.00 (time str) | 05:11, 05:58, 07:00 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#4 | frequency | drop | 29 | 13 | 0.722 | 0.677 | 1.00 (time str) | tuesday, saturday, thursday | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#5 | stops | drop | 5 | 5 | 0.278 | 0.520 | 1.00 (time str) | peterborough, tr4170, tr6357 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#6 | train type | drop | 8 | 6 | 0.333 | 0.587 | 0.62 (time str) | train, tr0545, tr2874 | overlap 0.625 >= 0.5 (mostly column 'time str') |
| L2_accommodation_option#0 | amenities | keep | 15 | 8 | 0.320 | 0.681 | 0.13 (location part) | parking, free parking, free internet | all checks passed |
| L2_accommodation_option#1 | parking | keep | 20 | 15 | 0.600 | 0.937 | 0.05 (location part) | free parking, parking | all checks passed |
| L2_accommodation_option#2 | price | drop | 16 | 9 | 0.360 | 0.750 | 0.50 (num people) | price range, cheap, expensive price range | overlap 0.500 >= 0.5 (mostly column 'num people') |
| L2_accommodation_option#3 | room type | drop | 14 | 10 | 0.400 | 0.628 | 0.86 (type) | guesthouse, hotel, cb13js | overlap 0.857 >= 0.5 (mostly column 'type') |
| L2_location#0 | directions | keep | 12 | 5 | 0.333 | 0.690 | 0.17 (address) | address, postcode, phone number | all checks passed |
| L2_location#1 | hours of operation | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#2 | map | drop | 8 | 3 | 0.200 | 0.416 | 0.75 (address) | address unit su43, area, cb223ae | overlap 0.750 >= 0.5 (mostly column 'address') |
| L2_location#3 | opening hours | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#4 | transportation | drop | 2 | 2 | 0.133 | 0.622 | 0.00 (-) | parking, train | n_dialogues 2 < 3 |
| L2_establishment#0 | address | drop | 15 | 9 | 0.310 | 0.468 | 0.73 (restaurant name) | address, 1 a.w, 4h1drif8 | overlap 0.733 >= 0.5 (mostly column 'restaurant name') |
| L2_establishment#1 | amenities | drop | 3 | 2 | 0.069 | 0.589 | 1.00 (location str) | attraction, centre, hotel | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'location str') |
| L2_establishment#2 | hours | drop | 30 | 14 | 0.483 | 0.700 | 1.00 (time) | 12:45, friday, 13:15 | overlap 1.000 >= 0.5 (mostly column 'time') |
| L2_establishment#3 | area | keep | 12 | 9 | 0.310 | 0.640 | 0.42 (location str) | centre of town, north side of town, specific area | all checks passed |
| L2_establishment#4 | entree fee | drop | 3 | 1 | 0.034 | 0.639 | 0.33 (entrance fee) | entrance fee, 2 pound | n_dialogues 1 < 3; support 0.034 < 0.05 |
| L2_establishment#5 | rating | keep | 8 | 7 | 0.241 | 0.720 | 0.25 (price range) | great, awesome, excellent | all checks passed |
| L2_establishment#6 | review | drop | 1 | 1 | 0.034 | - | 0.00 (-) | book for me | n_dialogues 1 < 3; support 0.034 < 0.05 |
| L2_establishment#7 | hours of operation | drop | 14 | 11 | 0.379 | 0.775 | 1.00 (time) | 12:45, 16:15, 05:45 | overlap 1.000 >= 0.5 (mostly column 'time') |
| L2_phone_number#0 | area code | drop | 12 | 11 | 0.571 | 0.713 | 1.00 (time str) | 07048450899, 07128258422, 07267142867 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#1 | country code | drop | 9 | 8 | 0.429 | 0.713 | 1.00 (time str) | 07267142867, 07340953955, 07481840729 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#2 | extension | drop | 6 | 6 | 0.286 | 0.719 | 1.00 (time str) | 07340953955, 07546403281, 07635928440 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#3 | operator | drop | 1 | 1 | 0.048 | - | 0.00 (-) | red tesla | n_dialogues 1 < 3; support 0.048 < 0.05 |
| L2_phone_number#4 | prefix | drop | 5 | 4 | 0.190 | 0.528 | 0.60 (time str) | 07340953955, 07635928440, 07901807088 | overlap 0.600 >= 0.5 (mostly column 'time str') |
| L2_phone_number#5 | service provider | keep | 6 | 5 | 0.286 | 0.554 | 0.17 (departure time) | taxi, a white audi, ask | all checks passed |
