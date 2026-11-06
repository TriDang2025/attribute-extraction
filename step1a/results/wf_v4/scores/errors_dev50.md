# Step-4 errors on dev50 (full GT, best-matching design)

Step 3 yes = the input column was already wrong (maps to no GT column, another entity, purity < 0.6, or a duplicate of a larger column with the same GT label).

## a_dev50_s0 (design merged:train+hotel+restaurant, 20 errors)

1. 4.1 real column unused: train:9 is the GT column 'Train price' (train) but was left unused
2. 4.1 real column unused: train:10 is the GT column 'Train confirmed reference' (train) but was left unused
3. 4.1 real column unused: train:11 is the GT column 'Hotel requested stay' (hotel) but was left unused [Step 3: train:11: maps to 'Hotel requested stay' of another entity (hotel)]
4. 4.1 real column unused: train:13 is the GT column 'Train price' (train) but was left unused [Step 3: train:13: duplicate of train:9 (same GT label 'Train price')]
5. 4.1 real column unused: hotel:2 is the GT column 'Hotel address' (hotel) but was left unused
6. 4.1 real column unused: hotel:5 is the GT column 'Hotel requested people' (hotel) but was left unused
7. 4.1 real column unused: hotel:6 is the GT column 'Hotel requested stay' (hotel) but was left unused
8. 4.1 real column unused: hotel:7 is the GT column 'Hotel phone' (hotel) but was left unused
9. 4.1 real column unused: hotel:8 is the GT column 'Hotel type' (hotel) but was left unused [Step 3: hotel:8: purity 0.57 < 0.6]
10. 4.1 real column unused: restaurant:1 is the GT column 'Attraction entrancefee' (attraction) but was left unused [Step 3: restaurant:1: maps to 'Attraction entrancefee' of another entity (attraction)]
11. 4.1 real column unused: restaurant:3 is the GT column 'Restaurant requested people' (restaurant) but was left unused
12. 4.1 real column unused: restaurant:4 is the GT column 'Restaurant requested people' (restaurant) but was left unused [Step 3: restaurant:4: duplicate of restaurant:3 (same GT label 'Restaurant requested people')]
13. 4.1 real column unused: restaurant:18 is the GT column 'Restaurant phone' (restaurant) but was left unused
14. 4.1 noise column placed: 'restaurant phone number' [restaurant:16] in 'restaurant_reservation' maps to no GT column [Step 3: restaurant:16: maps to no GT column]
15. 4.1 duplicate not flagged: restaurant:11 and restaurant:12 are both the GT column 'Restaurant address' in 'restaurant_reservation' and not flagged [Step 3: restaurant:12: duplicate of restaurant:11 (same GT label 'Restaurant address')]
16. 4.3 missing table: GT table 'taxi' (7 columns) has no output table [Step 3: yes]
17. 4.3 missing table: GT table 'attraction' (8 columns) has no output table [Step 3: yes]
18. 4.4 wrong primary key: 'train_journey' (GT 'train') has primary key ['train_journey_id'], GT has ['Train trainid']
19. 4.4 wrong primary key: 'hotel_booking' (GT 'hotel') has primary key ['hotel_booking_id'], GT has ['Hotel name']
20. 4.4 wrong primary key: 'restaurant_reservation' (GT 'restaurant') has primary key ['restaurant_reservation_id'], GT has ['Restaurant name']

## b_dev50_s0 (design main, 34 errors)

1. 4.1 real column unused: hotel:2 is the GT column 'Hotel address' (hotel) but was left unused
2. 4.1 real column unused: hotel:7 is the GT column 'Hotel phone' (hotel) but was left unused
3. 4.1 real column unused: hotel:8 is the GT column 'Hotel type' (hotel) but was left unused [Step 3: hotel:8: purity 0.57 < 0.6]
4. 4.1 real column unused: hotel:11 is the GT column 'Hotel postcode' (hotel) but was left unused
5. 4.1 real column unused: restaurant:1 is the GT column 'Attraction entrancefee' (attraction) but was left unused [Step 3: restaurant:1: maps to 'Attraction entrancefee' of another entity (attraction)]
6. 4.1 real column unused: restaurant:3 is the GT column 'Restaurant requested people' (restaurant_booking) but was left unused
7. 4.1 real column unused: restaurant:4 is the GT column 'Restaurant requested people' (restaurant_booking) but was left unused [Step 3: restaurant:4: duplicate of restaurant:3 (same GT label 'Restaurant requested people')]
8. 4.1 real column unused: restaurant:6 is the GT column 'Restaurant postcode' (restaurant) but was left unused
9. 4.1 real column unused: restaurant:8 is the GT column 'Restaurant confirmed reference' (restaurant_booking) but was left unused
10. 4.1 duplicate not flagged: train:1 and train:3 are both the GT column 'Train departure' in 'train_journey' and not flagged [Step 3: train:1: purity 0.48 < 0.6]
11. 4.1 column in wrong table: 'arrival_time' [train:2] is the GT column 'Train leave at' (GT table train) but sits in 'train_time_details' (no GT table) [Step 3: train:2: duplicate of train:4 (same GT label 'Train leave at')]
12. 4.1 column in wrong table: 'departure_time' [train:4] is the GT column 'Train leave at' (GT table train) but sits in 'train_time_details' (no GT table)
13. 4.1 noise column placed: 'time_query' [train:12] in 'train_time_details' maps to no GT column [Step 3: train:12: maps to no GT column]
14. 4.1 column in wrong table: 'travel_time' [train:16] is the GT column 'Train duration' (GT table train) but sits in 'train_time_details' (no GT table)
15. 4.1 duplicate not flagged: train:2 and train:4 are both the GT column 'Train leave at' in 'train_time_details' and not flagged [Step 3: train:2: duplicate of train:4 (same GT label 'Train leave at')]
16. 4.1 noise column placed: 'number_of_tickets' [train:7] in 'train_booking_details' maps to no GT column [Step 3: train:7: maps to no GT column]
17. 4.1 column in wrong table: 'price_per_ticket' [train:9] is the GT column 'Train price' (GT table train) but sits in 'train_booking_details' (matched to train_booking)
18. 4.1 column in wrong table: 'total_fee' [train:13] is the GT column 'Train price' (GT table train) but sits in 'train_booking_details' (matched to train_booking) [Step 3: train:13: duplicate of train:9 (same GT label 'Train price')]
19. 4.1 column in wrong table: 'train_id' [train:14] is the GT column 'Train trainid' (GT table train) but sits in 'train_booking_details' (matched to train_booking) (copy; also correctly in 'train_journey')
20. 4.1 duplicate not flagged: train:9 and train:13 are both the GT column 'Train price' in 'train_booking_details' and not flagged [Step 3: train:13: duplicate of train:9 (same GT label 'Train price')]
21. 4.1 column in wrong table: 'hotel_name' [hotel:4] is the GT column 'Hotel name' (GT table hotel) but sits in 'hotel_booking' (matched to hotel_booking) (copy; also correctly in 'hotel_location_price')
22. 4.1 noise column placed: 'restaurant_phone_number' [restaurant:16] in 'restaurant_details' maps to no GT column [Step 3: restaurant:16: maps to no GT column]
23. 4.1 duplicate not flagged: restaurant:11 and restaurant:12 are both the GT column 'Restaurant address' in 'restaurant_details' and not flagged [Step 3: restaurant:12: duplicate of restaurant:11 (same GT label 'Restaurant address')]
24. 4.1 column in wrong table: 'taxi_phone_numbers' [restaurant:18] is the GT column 'Restaurant phone' (GT table restaurant) but sits in 'reservation_details' (matched to restaurant_booking)
25. 4.1 column in wrong table: 'price_range' [restaurant:7] is the GT column 'Restaurant price range' (GT table restaurant) but sits in 'restaurant_price_food' (no GT table)
26. 4.1 column in wrong table: 'restaurant_food_type' [restaurant:13] is the GT column 'Restaurant food' (GT table restaurant) but sits in 'restaurant_price_food' (no GT table) [Step 3: restaurant:13: purity 0.50 < 0.6]
27. 4.3 missing table: GT table 'taxi' (7 columns) has no output table [Step 3: yes]
28. 4.3 missing table: GT table 'attraction' (8 columns) has no output table [Step 3: yes]
29. 4.3 extra table: output table 'train_time_details' matches no GT table
30. 4.3 extra table: output table 'restaurant_price_food' matches no GT table
31. 4.3 extra link: link train_booking_details -> train_time_details touches a table that matches no GT table
32. 4.3 extra link: link restaurant_details -> restaurant_price_food touches a table that matches no GT table
33. 4.4 wrong primary key: 'restaurant_details' (GT 'restaurant') has primary key ['restaurant_id'], GT has ['Restaurant name']
34. 4.4 wrong type: 'taxi_phone_numbers' [restaurant:18] in 'reservation_details' is text, GT 'Restaurant phone' is number

## Counts by step and by Step-3 error of the input column

| run | step | Step 3 yes | Step 3 no | all |
|---|---|---|---|---|
| a_dev50_s0 | 4.1 | 7 | 8 | 15 |
| a_dev50_s0 | 4.3 | 2 | 0 | 2 |
| a_dev50_s0 | 4.4 | 0 | 3 | 3 |
| a_dev50_s0 | all | 9 | 11 | 20 |
| b_dev50_s0 | 4.1 | 13 | 13 | 26 |
| b_dev50_s0 | 4.3 | 2 | 4 | 6 |
| b_dev50_s0 | 4.4 | 0 | 2 | 2 |
| b_dev50_s0 | all | 15 | 19 | 34 |
