# wf_v3.8 noise misses and false noise marks of A s012 on dev50b

- dev50b (A s012, v2.2): noise caught 5/9; marks 15 = 5 noise + 6 real + 4 mixed + 0 unknown; missed 4 (kinds {'no_l2_label': 4}, kept in all orders 1); guess: checks catch 1/4 misses, rescue 1/10 false marks.
- dev50 (A s012, v2.2, contrast): noise caught 10/13; marks 13 = 10 noise + 2 real + 1 mixed + 0 unknown; missed 3 (kinds {'no_l2_label': 3}, kept in all orders 2); guess: checks catch 2/3 misses, rescue 0/3 false marks.

Noise = the model-free MultiWOZ noise set (rules v1.1, L2): choice mentions, or no L2 label and not a request. A s012 = vote of 3 orders (s0 / s1 / s2). Marked = not_attribute / unsure / attribute_cue. The response has no free-text reason: the only text field is `evidence`, a quoted example, shown where it exists.

## Guesses about the planned evidence checks (not results)

Rules over model-free proxies, thresholds Thresholds(min_mentions=3, min_dialogues=2, min_distinct=2, type_share=0.8, question_share=0.5, neighbour_sim=0.8). example flags: > 50% of mentions inside a question, or dominant value type < 80%. neighbour: cosine to the nearest other kept column >= 0.8 (it would fit that column). counting flags: < 3 mentions, < 2 dialogues, < 2 distinct values, or dominant type < 80%. Missed noise: caught = any check flags it. False mark: rescued = no check flags it. The example proxy does not read the attribute name.

- missed noise clusters: 1/4 probably caught (example 0, neighbour 0, counting 1)
- marked non-noise clusters: 1/10 probably rescued

## Counts per reason

| case type | reason | cases |
|---|---|---|
| marked_not_noise | real_other_domain | 4 |
| marked_not_noise | request_phrases | 3 |
| marked_not_noise | real_tiny | 2 |
| marked_not_noise | mixed_cluster | 1 |
| noise_caught | caught_by_vote | 3 |
| noise_caught | caught_all_orders | 2 |
| noise_missed | vote_lost_mark:no_l2_label | 3 |
| noise_missed | kept_all_orders:no_l2_label | 1 |

## (a) noise clusters caught

### train E0#14: 5 mentions, label noise

- reason: caught: not_attribute; marked in 2/3 orders; no_l2_label 3 ('travel time', 'How many tickets', 'TR 6357').
- share of all noise mentions 0.033 (3 noise mentions: no_l2_label 3); top L2 attribute Train trainid 0.20
- A s012: not_attribute; s0: not_attribute; s1: not_attribute; s2: merge 'travel_time' (2 clusters); evidence Sure! The fare is 12.80 pounds and the [[travel time]] is 49 minutes.
- proxies: distinct 4, dialogues 4, type text 1.00, system turns 0.80, in questions 0.60, nearest column E0#4 (0.81)
- guess: example flag yes, fits neighbour yes, counting flag no; already caught
- example 1: travel time (user): I'd like the price and [[travel time]], please?
- example 2: How many tickets (system): ...depart cambridge Sunday at 8:11 and arrive in Kings Lynn at 8:58. [[How many tickets]] would you like to book?
- example 3: TR 6357 (system): Alright. The price for [[TR 6357]] is 17.90 pounds. Anything else?

### hotel E1#25: 3 mentions, label noise

- reason: caught: not_attribute; marked in 3/3 orders; no_l2_label 3 ('all of them', 'my parents').
- share of all noise mentions 0.033 (3 noise mentions: no_l2_label 3); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: not_attribute; s2: not_attribute; evidence [[all of them]]
- proxies: distinct 2, dialogues 2, type text 1.00, system turns 0.67, in questions 0.00, nearest column E1#4 (0.74)
- guess: example flag no, fits neighbour no, counting flag no; already caught
- example 1: all of them (system): I've found three, [[all of them]] are guesthouses and all of them have free internet and parking. Would you li...
- example 2: my parents (user): ...re of town and want to see if I can find a reasonable room for [[my parents]] to stay while they are visiting.

### hotel E1#26: 3 mentions, label noise

- reason: caught: not_attribute; marked in 3/3 orders; choice 1, no_l2_label 2 ('Just one', 'another area', 'another day').
- share of all noise mentions 0.033 (3 noise mentions: choice 1, no_l2_label 2); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: not_attribute; s2: not_attribute; evidence [[another area]]
- proxies: distinct 3, dialogues 3, type text 1.00, system turns 1.00, in questions 0.67, nearest column E1#5 (0.73)
- guess: example flag yes, fits neighbour no, counting flag no; already caught
- example 1: Just one (system): [[Just one]], the Hobsons House is available.
- example 2: another area (system): Are you sure you don't want me to check [[another area]] for you to stay?
- example 3: another day (system): ...rry, that reservation wasn't available. Perhaps you could book [[another day]], or a different length of stay?

### restaurant E3#19: 7 mentions, label noise

- reason: caught: not_attribute; marked in 1/3 orders; no_l2_label 7 ('table').
- share of all noise mentions 0.077 (7 noise mentions: no_l2_label 7); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: keep 'restaurant_table'; s2: merge 'restaurant_table_size' (3 clusters); evidence I can reserve a [[table]] for you and give you a reservation number
- proxies: distinct 1, dialogues 7, type text 1.00, system turns 0.29, in questions 0.43, nearest column E3#0 (0.66)
- guess: example flag no, fits neighbour no, counting flag yes; already caught
- example 1: table (user): Lets try Hakka,can you book a [[table]] for 8 people at 16:30 on tuesday?

### restaurant E3#24: 5 mentions, label noise

- reason: caught: not_attribute; marked in 1/3 orders; no_l2_label 5 ('reservation number', 'attractions', 'entree fee').
- share of all noise mentions 0.055 (5 noise mentions: no_l2_label 5); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: merge 'restaurant_entree_fee' (2 clusters); s2: merge 'restaurant_entrance_fee' (2 clusters); evidence corpus christi is popular this time of year. The address is at king's parade. The post code cb21rh and the [[entree fee]] is 2 pounds.
- proxies: distinct 4, dialogues 2, type text 1.00, system turns 0.40, in questions 0.40, nearest column E3#5 (0.69)
- guess: example flag no, fits neighbour no, counting flag no; already caught
- example 1: reservation number (system): I can reserve a table for you and give you a [[reservation number]]
- example 2: attractions (user): ... located in the center of town near [[attractions]], hotels and easy access to transportation such as buses an...
- example 3: entree fee (system): ...r this time of year. The address is at king's parade. The post code cb21rh and the [[entree fee]] is 2 pounds.


## (a) noise clusters missed

### train E0#10: 4 mentions, label noise

- reason: missed: marked in only 1/3 orders, vote kept it; s012 = keep 'payment_location'; 100% noise; mentions with no L2 label (generic words, not an attribute value), e.g. 'station'.
- share of all noise mentions 0.044 (4 noise mentions: no_l2_label 4); top L2 attribute none 0.00
- A s012: keep 'payment_location'; s0: not_attribute; s1: keep 'payment_location'; s2: keep 'payment_location'; evidence the total fee is 82.5 GBP payable at the [[station]].
- proxies: distinct 1, dialogues 4, type text 1.00, system turns 1.00, in questions 0.00, nearest column E0#0 (0.65)
- guess: example flag no, fits neighbour no, counting flag yes; would catch yes
- example 1: station (system): ...ooking was successful, the total fee is 31.36 GBP payable at the [[station]] . Reference number is : 8K88DU7K.

### hotel E1#11: 6 mentions, label noise

- reason: missed: marked in only 1/3 orders, vote kept it; s012 = keep 'amenities'; 67% noise; 17% Hotel name; mentions with no L2 label (generic words, not an attribute value), e.g. 'cityroomz', 'room', 'city'.
- share of all noise mentions 0.044 (4 noise mentions: no_l2_label 4); top L2 attribute Hotel name 0.17
- A s012: keep 'amenities'; s0: keep 'amenities'; s1: keep 'room_type'; s2: not_attribute; evidence [[room]]
- proxies: distinct 4, dialogues 6, type text 1.00, system turns 0.50, in questions 0.50, nearest column E1#0 (0.76)
- guess: example flag no, fits neighbour no, counting flag no; would catch no
- example 1: cityroomz (system): i'd like to suggest to you [[cityroomz]]
- example 2: room (system): Yes, that's correct. Would you like to book a [[room]]?
- example 3: city (system): ... that meet your criteria. Do you have a preferred location in the [[city]] so we can narrow down your choices?

### hotel E1#8: 6 mentions, label noise

- reason: missed: marked in only 1/3 orders, vote kept it; s012 = merge 'location' (2 clusters); 67% noise; 17% Hotel area; mentions with no L2 label (generic words, not an attribute value), e.g. 'cambridge', 'The express by holiday inn cambridge', 'north section of Cambridge'.
- share of all noise mentions 0.044 (4 noise mentions: no_l2_label 4); top L2 attribute Hotel area 0.17
- A s012: merge 'location' (2 clusters); s0: merge 'location' (2 clusters); s1: merge 'location' (3 clusters); s2: not_attribute; evidence [[cambridge]]
- proxies: distinct 3, dialogues 6, type text 1.00, system turns 0.17, in questions 0.33, nearest column E1#9 (0.63)
- guess: example flag no, fits neighbour no, counting flag no; would catch no
- example 1: cambridge (user): I am going to [[cambridge]] and need a hotel
- example 2: The express by holiday inn cambridge (system): [[The express by holiday inn cambridge]] is a 2 star hotel in the east area that is expensive. It has wifi and...
- example 3: north section of Cambridge (user): I'm not too concerned about price. Is the Acorn Guest House in the [[north section of Cambridge]]?

### restaurant E3#21: 5 mentions, label noise

- reason: missed: kept in all 3 orders; s012 = keep 'reservation_duration'; 100% noise; mentions with no L2 label (generic words, not an attribute value), e.g. '15 minutes', '15'.
- share of all noise mentions 0.055 (5 noise mentions: choice 1, no_l2_label 4); top L2 attribute none 0.00
- A s012: keep 'reservation_duration'; s0: keep 'reservation_duration'; s1: keep 'restaurant_reservation_duration'; s2: keep 'restaurant_table_reservation_duration'; evidence It is booked! Your table will be reserved for [[15 minutes]].
- proxies: distinct 2, dialogues 4, type duration 0.80, system turns 1.00, in questions 0.00, nearest column E3#20 (0.68)
- guess: example flag no, fits neighbour no, counting flag no; would catch no
- example 1: 15 minutes (system): It is booked! Your table will be reserved for [[15 minutes]] and your reference number is VWDBTAYR.
- example 2: 15 (system): There are a total of [[15]] restaurants that are cheap in the centre. Is there another type you would like to ...


## (b) marked clusters that are not noise

### train E0#19: 1 mentions, label real

- reason: false mark: real Train trainid 1.00 cluster with 1 mention(s), marked in 3/3 orders, e.g. 'The TR5933'.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute Train trainid 1.00
- A s012: not_attribute; s0: not_attribute; s1: not_attribute; s2: not_attribute; evidence [[The TR5933]] leaves peterborough at 15:19.
- proxies: distinct 1, dialogues 1, type text 1.00, system turns 1.00, in questions 0.00, nearest column E0#4 (0.60)
- guess: example flag no, fits neighbour no, counting flag yes; would rescue no
- example 1: The TR5933 (system): [[The TR5933]] leaves peterborough at 15:19.

### train E0#2: 5 mentions, label mixed

- reason: false mark: 80% request phrases (questions for a slot, e.g. 'What time of day', 'what day', 'what time'), neither noise nor a value; marked in 2/3 orders, s012 = not_attribute.
- share of all noise mentions 0.011 (1 noise mentions: no_l2_label 1); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: not_attribute; s2: merge 'departure_day' (2 clusters); evidence What day are you traveling?
- proxies: distinct 4, dialogues 4, type text 1.00, system turns 0.80, in questions 0.80, nearest column E0#0 (0.74)
- guess: example flag yes, fits neighbour no, counting flag no; would rescue no
- example 1: What time of day (system): There are several trains headed to broxbourne. [[What time of day]] would you like to leave?
- example 2: what day (system): Okay [[what day]] will you be travelling and what time would you like to travel?
- example 3: what time (user): It might, [[what time]] does the train depart?

### hotel E1#14: 3 mentions, label mixed

- reason: false mark: 100% request phrases (questions for a slot, e.g. 'How many people'), neither noise nor a value; marked in 2/3 orders, s012 = not_attribute.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: keep 'number_of_people'; s2: not_attribute; evidence [[how many people]]
- proxies: distinct 1, dialogues 2, type text 1.00, system turns 1.00, in questions 1.00, nearest column E1#4 (0.78)
- guess: example flag yes, fits neighbour no, counting flag yes; would rescue no
- example 1: How many people (system): [[How many people]] would you like to book for?

### hotel E1#17: 1 mentions, label real

- reason: false mark: values of another domain's attribute (Attraction name 1.00) inside this entity, e.g. 'Downing College'; s012 = not_attribute.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute Attraction name 1.00
- A s012: not_attribute; s0: not_attribute; s1: merge 'hotel_name' (6 clusters); s2: not_attribute; evidence [[Downing College]]
- proxies: distinct 1, dialogues 1, type text 1.00, system turns 1.00, in questions 0.00, nearest column E1#8 (0.56)
- guess: example flag no, fits neighbour no, counting flag yes; would rescue no
- example 1: Downing College (system): The phone of [[Downing College]] is 01223334860. Do you need a place to stay?

### hotel E1#24: 2 mentions, label mixed

- reason: false mark: 100% request phrases (questions for a slot, e.g. 'What day'), neither noise nor a value; marked in 3/3 orders, s012 = not_attribute.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute none 0.00
- A s012: not_attribute; s0: not_attribute; s1: not_attribute; s2: not_attribute; evidence [[What day]]
- proxies: distinct 1, dialogues 2, type text 1.00, system turns 1.00, in questions 1.00, nearest column E1#5 (0.72)
- guess: example flag yes, fits neighbour no, counting flag yes; would rescue no
- example 1: What day (system): [[What day]] will you be checking in, and how many will you stay for? I assume it is for 2 people?

### restaurant E3#14: 2 mentions, label real

- reason: false mark: values of another domain's attribute (Attraction type 1.00) inside this entity, e.g. '13 colleges'; s012 = not_attribute.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute Attraction type 1.00
- A s012: not_attribute; s0: not_attribute; s1: merge 'restaurant_reference_number' (2 clusters); s2: not_attribute; evidence There are [[13 colleges]] in the centre of town.
- proxies: distinct 1, dialogues 2, type number 1.00, system turns 1.00, in questions 0.00, nearest column E3#15 (0.56)
- guess: example flag no, fits neighbour no, counting flag yes; would rescue no
- example 1: 13 colleges (system): I have [[13 colleges]] available in the centre. Did yo have one particular in mind?

### restaurant E3#23: 6 mentions, label mixed

- reason: false mark: mixed cluster (top Restaurant requested day 0.33, 17% noise); marked in 1/3 orders, e.g. 'same day', 'What day', 'what time'.
- share of all noise mentions 0.011 (1 noise mentions: no_l2_label 1); top L2 attribute Restaurant requested day 0.33
- A s012: not_attribute; s0: not_attribute; s1: merge 'restaurant_reservation_day' (2 clusters); s2: merge 'restaurant_reservation_date' (2 clusters); evidence I would like to arrive at the restaurant no later than [[ten o'clock]] a.m.
- proxies: distinct 5, dialogues 4, type text 1.00, system turns 0.33, in questions 0.33, nearest column E3#12 (0.74)
- guess: example flag no, fits neighbour no, counting flag no; would rescue yes
- example 1: same day (user): Yes. I need a table for 8 people at 16:15 on the [[same day]].
- example 2: What day (system): ...y to make that reservation for you. [[What day]] are you looking to eat on, how many are in your party, and wh...
- example 3: what time (system): ...ion for you. What day are you looking to eat on, how many are in your party, and [[what time]] would you like?

### restaurant E3#36: 1 mentions, label real

- reason: false mark: values of another domain's attribute (Attraction type 1.00) inside this entity, e.g. 'college'; s012 = not_attribute.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute Attraction type 1.00
- A s012: not_attribute; s0: not_attribute; s1: merge 'restaurant_location' (4 clusters); s2: not_attribute; evidence I would like to visit a [[college]] in the same area as the noodle bar, can you find me one?
- proxies: distinct 1, dialogues 1, type text 1.00, system turns 0.00, in questions 1.00, nearest column E3#15 (0.59)
- guess: example flag yes, fits neighbour no, counting flag yes; would rescue no
- example 1: college (user): I would like to visit a [[college]] in the same area as the noodle bar, can you find me one?

### restaurant E3#39: 1 mentions, label real

- reason: false mark: values of another domain's attribute (Attraction entrancefee 1.00) inside this entity, e.g. '2 pounds'; s012 = not_attribute.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute Attraction entrancefee 1.00
- A s012: not_attribute; s0: not_attribute; s1: merge 'restaurant_entree_fee' (2 clusters); s2: merge 'restaurant_entrance_fee' (2 clusters); evidence corpus christi is popular this time of year. The address is at king's parade. The post code cb21rh and the entree fee is [[2 pounds]].
- proxies: distinct 1, dialogues 1, type price 1.00, system turns 1.00, in questions 0.00, nearest column E3#20 (0.69)
- guess: example flag no, fits neighbour no, counting flag yes; would rescue no
- example 1: 2 pounds (system): ...r this time of year. The address is at king's parade. The post code cb21rh and the entree fee is [[2 pounds]].

### restaurant E3#43: 1 mentions, label real

- reason: false mark: real Restaurant food 1.00 cluster with 1 mention(s), marked in 2/3 orders, e.g. 'four cheap Indian places'.
- share of all noise mentions 0.000 (0 noise mentions); top L2 attribute Restaurant food 1.00
- A s012: not_attribute; s0: not_attribute; s1: keep 'restaurant_price_range'; s2: not_attribute; evidence There are [[four cheap Indian places]], three in city centre, and one on the north end.
- proxies: distinct 1, dialogues 1, type text 1.00, system turns 1.00, in questions 0.00, nearest column E3#1 (0.57)
- guess: example flag no, fits neighbour no, counting flag yes; would rescue no
- example 1: four cheap Indian places (system): There are [[four cheap Indian places]], three in city centre, and one on the north end.

