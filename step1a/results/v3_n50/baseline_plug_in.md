# C7: chosen Step 2 on predicted entities (50 dialogues)

Step 2 config: `{"normalize": true, "alpha": 0.5, "by_type": true, "linkage": "average", "t": 0.45, "cannot_link": true, "F1": 0.8029, "K": 30, "note": "joint re-tune, scratch ablation"}`. Stage 1 = k-means k=5 on segments (3 seeds, mean). Booking = (dialogue, segment). B value recall = 0.724. Run 14.8 min.

| Segments | Units | Stage 2 | P | R | F1 | K | vis/hid L1 | vis/hid L2 | vis/hid L3 | End to end |
|---|---|---|---|---|---|---|---|---|---|---|
| 25_100_s_m45 | A gold mentions | original | 0.759 | 0.527 | **0.622** | 127 | 0.614 / 0.675 | 0.603 / 0.679 | 0.610 / 0.638 |  |
| 25_100_s_m45 | A gold mentions | chosen | 0.683 | 0.652 | **0.667** | 37 | 0.667 / 0.597 | 0.661 / 0.688 | 0.678 / 0.641 |  |
| 25_100_s_m45 | B GLiNER 0.5 spans | original | 0.807 | 0.516 | **0.630** | 200 | 0.614 / 0.711 | 0.618 / 0.674 | 0.616 / 0.662 | 0.456 |
| 25_100_s_m45 | B GLiNER 0.5 spans | chosen | 0.716 | 0.505 | **0.592** | 72 | 0.602 / 0.486 | 0.591 / 0.594 | 0.605 / 0.553 | 0.429 |

### 25_100_s_m45, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 38.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.658 | 0.613 | 0.635 |
| visible_L1 | 553 | 0.670 | 0.600 | 0.633 |
| hidden_L1 | 38 | 0.488 | 0.794 | 0.604 |
| visible_L2 | 462 | 0.655 | 0.594 | 0.623 |
| hidden_L2 | 129 | 0.669 | 0.679 | 0.674 |
| visible_L3 | 397 | 0.686 | 0.596 | 0.638 |
| hidden_L3 | 194 | 0.600 | 0.647 | 0.622 |

Per-class recall: Attraction area 0.28 (13); Attraction name 0.24 (12); Attraction type 0.46 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.60 (16); Hotel name 0.51 (25); Hotel price range 1.00 (13); Hotel requested day 1.00 (18); Hotel requested people 0.27 (20); Hotel requested stay 0.31 (27); Hotel stars 0.50 (21); Hotel type 1.00 (13); Restaurant area 0.80 (36); Restaurant confirmed reference 0.44 (13); Restaurant food 0.92 (25); Restaurant name 0.24 (35); Restaurant price range 0.91 (21); Restaurant requested day 0.53 (16); Restaurant requested people 0.49 (15); Restaurant requested time 0.62 (16); Taxi arrive by 0.56 (3); Taxi departure 0.50 (6); Taxi destination 0.38 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.80 (18); Train day 1.00 (40); Train departure 0.43 (44); Train destination 0.40 (42); Train leave at 1.00 (23); Train requested people 0.33 (24)

Most confused (gold -> cluster majority): Train destination -> Train departure 18; Train departure -> Train destination 17; Train arrive by -> Train leave at 11; Attraction name -> Attraction area 6; Restaurant requested day -> Hotel requested day 6; Restaurant name -> Restaurant price range 5; Hotel name -> Hotel type 5; Restaurant confirmed reference -> Hotel confirmed reference 4; Attraction type -> Restaurant name 4; Hotel requested people -> Hotel requested stay 4


### 25_100_s_m45, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 71.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.685 | 0.488 | 0.570 |
| visible_L1 | 355 | 0.697 | 0.495 | 0.579 |
| hidden_L1 | 34 | 0.555 | 0.417 | 0.476 |
| visible_L2 | 317 | 0.693 | 0.480 | 0.567 |
| hidden_L2 | 72 | 0.651 | 0.527 | 0.582 |
| visible_L3 | 289 | 0.709 | 0.489 | 0.579 |
| hidden_L3 | 100 | 0.615 | 0.487 | 0.543 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.31 (12); Attraction type 0.56 (3); Hotel area 0.56 (6); Hotel confirmed reference 0.41 (16); Hotel name 0.50 (23); Hotel price range 0.56 (6); Hotel requested day 1.00 (18); Hotel requested people 0.37 (6); Hotel requested stay 0.44 (19); Hotel stars 0.45 (6); Restaurant area 0.56 (9); Restaurant confirmed reference 0.44 (13); Restaurant food 1.00 (1); Restaurant name 0.29 (27); Restaurant price range 0.41 (8); Restaurant requested day 0.53 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.38 (16); Taxi arrive by 0.33 (3); Taxi departure 0.38 (4); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 0.40 (11); Train confirmed reference 0.79 (17); Train day 0.52 (40); Train departure 0.46 (41); Train destination 0.46 (38); Train leave at 0.46 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 18; Train destination -> Train departure 15; Restaurant requested day -> Hotel requested day 6; Train arrive by -> Train leave at 5; Restaurant confirmed reference -> Hotel confirmed reference 4; Attraction type -> Attraction name 3; Train leave at -> Train arrive by 3; Restaurant name -> Hotel name 2; Taxi arrive by -> Restaurant requested time 2; Taxi departure -> Restaurant area 2

Largest mostly non-gold clusters:

- size 17 (17 non-gold): "06:08", "06:43", "10:09", "09:35", "17:08", "11:09", "7:08", "09:19", "09:21", "7:16", "7:16", "10:09", "06:08", "22:35", "5:01"
- size 17 (17 non-gold): "20:08", "21:21", "21:21", "13:40", "13:40", "21:21", "09:52", "6:40", "19:58", "11:54", "15:40", "21:16", "17:58", "15:50", "13:19"
- size 15 (14 non-gold): "6 other guests", "reference number", "riverboat Georgina", "same day", "reference number", "Gonville Place", "reference number", "reference number", "what day", "reference number", "table", "table", "same day", "same day", "what day"
- size 13 (13 non-gold): "TR1110", "TR6387", "TR6387", "TR6193", "TR4669", "TR8598", "TR7604", "TR4202", "TR0032", "TR7935", "TR3677", "TR4679", "TR5921"
- size 13 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "66 GBP", "64 GBP", "10.10 pounds", "7.84 GBP", "66 GBP", "14.08 pounds", "6 GBP", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 13 (13 non-gold): "43 High Street", "Bedouin", "bedouin", "clifton way", "100 Mill Rd", "regent street", "huntingdon road", "Ugly Duckling", "Histon Road", "6 Lensfield Road", "68 Histon Road", "7 Milton Street", "7 Milton Road"
- size 13 (10 non-gold): "Cherry Hinton", "Cherry Hinton", "expensive", "expensive", "expensive", "64 Cherry Hinton Road", "expensive price range", "expensive", "expensive price range", "expensive", "expensive price range", "expensive price range", "Great"
- size 13 (13 non-gold): "07083984796", "01223367660", "01223367660", "01223412299", "01223311911", "07633256482", "15 minutes", "01223315232", "01223464550", "01223354755", "01223362372", "01223276182", "15 minutes"
- size 12 (9 non-gold): "astroturf pitch", "Corpus Christi", "98 king street", "Cherry Hinton", "bar hill", "The Junction", "Cherry Hinton Hall", "nightclubs", "East Road", "Downing Street", "Ballare", "Ballare"
- size 11 (10 non-gold): "Trinity", "Lucky Star", "entrance fee", "entrance fee", "Cineworld Cinema", "hotel", "restaurants", "Mumford theatre", "entrance fee", "entrance fee", "entrance fee"


