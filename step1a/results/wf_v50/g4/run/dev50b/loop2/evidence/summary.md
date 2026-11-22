# Loop 2 named probe, c_n50b

Labels: `/content/attribute-extraction/step1a/results/wf_v47/z4/run1/dev50b/loop2/step1b/labels.json`; run 21 s. Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5.
Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.

| entity | labels | kept | dropped |
|---|---|---|---|
| train_schedule | 12 | 0 | 12 |
| accommodation_option | 12 | 6 | 6 |
| location | 15 | 2 | 13 |
| establishment | 12 | 2 | 10 |
| phone_number | 23 | 1 | 22 |

| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |
|---|---|---|---|---|---|---|---|---|---|
| L2_train_schedule#0 | arrival station | drop | 29 | 16 | 0.889 | 0.537 | 1.00 (destination) | cambridge, broxbourne, stevenage | overlap 1.000 >= 0.5 (mostly column 'destination') |
| L2_train_schedule#1 | departure station | drop | 34 | 16 | 0.889 | 0.586 | 1.00 (destination) | cambridge, broxbourne, peterborough | overlap 1.000 >= 0.5 (mostly column 'destination') |
| L2_train_schedule#2 | frequency | drop | 29 | 13 | 0.722 | 0.677 | 1.00 (time str) | tuesday, saturday, thursday | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#3 | operator | drop | 4 | 4 | 0.222 | 0.605 | 0.75 (time str) | tr0545, tr2874, tr6357 | overlap 0.750 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#4 | route | drop | 9 | 6 | 0.333 | 0.454 | 0.78 (destination) | birmingham new street, cambridge, destination | overlap 0.778 >= 0.5 (mostly column 'destination') |
| L2_train_schedule#5 | class | drop | 1 | 1 | 0.056 | - | 1.00 (time str) | tr2289 | n_dialogues 1 < 3; overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#6 | train type | drop | 7 | 6 | 0.333 | 0.582 | 0.57 (time str) | train, tr0545, tr2874 | overlap 0.571 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#7 | mileage limit | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_train_schedule#8 | delay | drop | 11 | 6 | 0.333 | 0.721 | 1.00 (time str) | 05:11, 05:58, 07:00 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#9 | mileage | drop | 4 | 3 | 0.167 | 0.553 | 1.00 (time str) | 05:11, 05:58, 17.90 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#10 | duration | drop | 29 | 12 | 0.667 | 0.652 | 0.97 (time str) | 16:15, 49 minute, thursday | overlap 0.966 >= 0.5 (mostly column 'time str') |
| L2_train_schedule#11 | stops | drop | 3 | 3 | 0.167 | 0.646 | 1.00 (destination) | peterborough, birmingham new street | overlap 1.000 >= 0.5 (mostly column 'destination') |
| L2_accommodation_option#0 | amenities | keep | 10 | 5 | 0.200 | 0.641 | 0.10 (type) | parking, free internet, 3 star | all checks passed |
| L2_accommodation_option#1 | breakfast | drop | 3 | 3 | 0.120 | 0.762 | 1.00 (location) | alexander bed and breakfast, carolina bed and breakfast, the alexander bed and breakfast | overlap 1.000 >= 0.5 (mostly column 'location') |
| L2_accommodation_option#2 | cancellation policy | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_accommodation_option#3 | checkin time | drop | 12 | 10 | 0.400 | 0.773 | 1.00 (checkin date) | wednesday, friday, thursday | overlap 1.000 >= 0.5 (mostly column 'checkin date') |
| L2_accommodation_option#4 | checkout time | drop | 12 | 11 | 0.440 | 0.789 | 1.00 (day) | wednesday, friday, sunday | overlap 1.000 >= 0.5 (mostly column 'day') |
| L2_accommodation_option#5 | internet | keep | 19 | 12 | 0.480 | 0.865 | 0.00 (-) | free wifi, wifi, free internet | all checks passed |
| L2_accommodation_option#6 | parking | keep | 21 | 15 | 0.600 | 0.939 | 0.05 (location part) | free parking, parking | all checks passed |
| L2_accommodation_option#7 | price range | keep | 23 | 14 | 0.560 | 0.867 | 0.35 (num people) | price range, moderately priced, moderate price range | all checks passed |
| L2_accommodation_option#8 | payment method | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_accommodation_option#9 | smoking policy | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_accommodation_option#10 | facilities | keep | 11 | 6 | 0.240 | 0.562 | 0.36 (location) | parking, 3 star, a and b guest house | all checks passed |
| L2_accommodation_option#11 | services | keep | 11 | 7 | 0.280 | 0.773 | 0.00 (-) | free parking, free wifi, free internet | all checks passed |
| L2_location#0 | capacity | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#1 | directions | keep | 15 | 8 | 0.533 | 0.600 | 0.33 (address) | address, postcode, phone number | all checks passed |
| L2_location#2 | opening hours | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#3 | parking | drop | 3 | 2 | 0.133 | 0.765 | 0.33 (location) | free parking, park, parking | n_dialogues 2 < 3 |
| L2_location#4 | accessibility | drop | 2 | 2 | 0.133 | 0.498 | 0.50 (address) | parking, wollaston road | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'address') |
| L2_location#5 | amenities | keep | 5 | 3 | 0.267 | 0.610 | 0.40 (location) | local attraction, multiple sport type attraction, multiple type of attraction | all checks passed |
| L2_location#6 | distance | drop | 2 | 2 | 0.133 | 0.467 | 0.00 (-) | almost 80, south | n_dialogues 2 < 3 |
| L2_location#7 | transportation | drop | 2 | 2 | 0.133 | 0.622 | 0.00 (-) | parking, train | n_dialogues 2 < 3 |
| L2_location#8 | hours of operation | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#9 | layout | drop | 7 | 6 | 0.400 | 0.674 | 0.86 (location) | centre, centre area, city centre | overlap 0.857 >= 0.5 (mostly column 'location') |
| L2_location#10 | size | drop | 1 | 1 | 0.067 | - | 0.00 (-) | almost 80 | n_dialogues 1 < 3 |
| L2_location#11 | address type | drop | 25 | 11 | 0.733 | 0.444 | 0.80 (address) | cb23bu, postcode, saint andrew's street | overlap 0.800 >= 0.5 (mostly column 'address') |
| L2_location#12 | nearest landmark | drop | 14 | 5 | 0.333 | 0.406 | 0.93 (location) | architecture, babraham, castle gallery | overlap 0.929 >= 0.5 (mostly column 'location') |
| L2_location#13 | transport links | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_location#14 | wheelchair accessibility | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_establishment#0 | address | drop | 21 | 12 | 0.414 | 0.474 | 0.76 (restaurant name) | address, c.b 2, 1 a.w | overlap 0.762 >= 0.5 (mostly column 'restaurant name') |
| L2_establishment#1 | amenities | drop | 4 | 3 | 0.103 | 0.531 | 0.75 (location str) | attraction, centre, gastropub | overlap 0.750 >= 0.5 (mostly column 'location str') |
| L2_establishment#2 | hours of operation | drop | 12 | 10 | 0.345 | 0.759 | 1.00 (time) | 05:45, 10:30, 12:45 | overlap 1.000 >= 0.5 (mostly column 'time') |
| L2_establishment#3 | rating | drop | 7 | 6 | 0.207 | 0.737 | 0.86 (price range) | moderately priced, expensive price range, great | overlap 0.857 >= 0.5 (mostly column 'price range') |
| L2_establishment#4 | entertainment options | drop | 2 | 2 | 0.069 | 0.399 | 1.00 (restaurant name) | attraction, loch fyne | n_dialogues 2 < 3; overlap 1.000 >= 0.5 (mostly column 'restaurant name') |
| L2_establishment#5 | parking | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_establishment#6 | wheelchair accessibility | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_establishment#7 | capacity | drop | 9 | 7 | 0.241 | 0.760 | 0.78 (num people) | 8 people, 1 person, 15 minute | overlap 0.778 >= 0.5 (mostly column 'num people') |
| L2_establishment#8 | menu | keep | 6 | 4 | 0.138 | 0.692 | 0.00 (-) | gastropub food, british food, european food | all checks passed |
| L2_establishment#9 | cuisine type | keep | 18 | 10 | 0.345 | 0.629 | 0.06 (entity) | indian food, italian, gastropub food | all checks passed |
| L2_establishment#10 | parking options | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_establishment#11 | reservations policy | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_phone_number#0 | call purpose | drop | 3 | 2 | 0.095 | 0.745 | 0.00 (-) | goodbye, thank you for calling | n_dialogues 2 < 3 |
| L2_phone_number#1 | caller location | drop | 15 | 11 | 0.571 | 0.561 | 0.93 (time str) | 07048450899, 07267142867, 07340953955 | overlap 0.933 >= 0.5 (mostly column 'time str') |
| L2_phone_number#2 | caller name | drop | 13 | 10 | 0.524 | 0.647 | 0.85 (time str) | i, 07048450899, 07128258422 | overlap 0.846 >= 0.5 (mostly column 'time str') |
| L2_phone_number#3 | call date | drop | 5 | 4 | 0.190 | 0.671 | 0.80 (arrival time) | 11:45, 14:45, 19:15 | overlap 0.800 >= 0.5 (mostly column 'arrival time') |
| L2_phone_number#4 | call duration | drop | 9 | 8 | 0.381 | 0.827 | 1.00 (arrival time) | 10:45, 11:45, 12:45 | overlap 1.000 >= 0.5 (mostly column 'arrival time') |
| L2_phone_number#5 | call status | drop | 2 | 2 | 0.095 | 0.495 | 0.50 (arrival time) | 14:45, goodbye | n_dialogues 2 < 3; overlap 0.500 >= 0.5 (mostly column 'arrival time') |
| L2_phone_number#6 | call type | drop | 5 | 5 | 0.238 | 0.720 | 1.00 (time str) | 07267142867, 07609996919, 07635928440 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#7 | caller id | drop | 14 | 11 | 0.571 | 0.667 | 0.86 (time str) | 07048450899, 07128258422, 07267142867 | overlap 0.857 >= 0.5 (mostly column 'time str') |
| L2_phone_number#8 | caller number | drop | 14 | 11 | 0.571 | 0.648 | 0.93 (time str) | 07048450899, 07128258422, 07267142867 | overlap 0.929 >= 0.5 (mostly column 'time str') |
| L2_phone_number#9 | caller type | drop | 16 | 9 | 0.476 | 0.564 | 0.50 (time str) | i, you, 07048450899 | overlap 0.500 >= 0.5 (mostly column 'time str') |
| L2_phone_number#10 | caller s contact method | drop | 13 | 11 | 0.571 | 0.657 | 0.92 (time str) | 07048450899, 07128258422, 07267142867 | overlap 0.923 >= 0.5 (mostly column 'time str') |
| L2_phone_number#11 | caller s phone number | drop | 12 | 11 | 0.571 | 0.713 | 1.00 (time str) | 07048450899, 07128258422, 07267142867 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#12 | driver s name | drop | 5 | 5 | 0.238 | 0.722 | 1.00 (time str) | 07048450899, 07128258422, 07481840729 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#13 | driver s phone number | drop | 13 | 11 | 0.571 | 0.679 | 1.00 (time str) | 07048450899, 07128258422, 07267142867 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#14 | payment method | drop | 1 | 1 | 0.048 | - | 0.00 (-) | red tesla | n_dialogues 1 < 3; support 0.048 < 0.05 |
| L2_phone_number#15 | taxi company name | drop | 14 | 11 | 0.619 | 0.591 | 0.93 (time str) | 07048450899, 07128258422, 07267142867 | overlap 0.929 >= 0.5 (mostly column 'time str') |
| L2_phone_number#16 | area code | drop | 12 | 11 | 0.571 | 0.713 | 1.00 (time str) | 07048450899, 07128258422, 07267142867 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#17 | country code | drop | 9 | 8 | 0.429 | 0.713 | 1.00 (time str) | 07267142867, 07340953955, 07481840729 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#18 | extension | drop | 11 | 10 | 0.524 | 0.715 | 1.00 (time str) | 07048450899, 07128258422, 07340953955 | overlap 1.000 >= 0.5 (mostly column 'time str') |
| L2_phone_number#19 | operator | drop | 5 | 4 | 0.190 | 0.474 | 0.60 (time str) | 07128258422, 07635928440, ask | overlap 0.600 >= 0.5 (mostly column 'time str') |
| L2_phone_number#20 | rate plan | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2_phone_number#21 | status | drop | 1 | 1 | 0.048 | - | 0.00 (-) | booking | n_dialogues 1 < 3; support 0.048 < 0.05 |
| L2_phone_number#22 | type | keep | 8 | 7 | 0.381 | 0.614 | 0.12 (arrival time) | taxi, black ford, blue ford | all checks passed |
