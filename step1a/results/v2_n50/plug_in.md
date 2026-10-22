# C7: chosen Step 2 on predicted entities (50 dialogues)

Step 2 config: `{"normalize": true, "alpha": 0.5, "by_type": true, "linkage": "average", "t": 0.45, "cannot_link": true, "F1": 0.8029, "K": 30, "note": "joint re-tune, scratch ablation"}`. Stage 1 = k-means k=5 on segments (3 seeds, mean). Booking = (dialogue, segment). B value recall = 0.724. Run 7.8 min.

| Segments | Units | Stage 2 | P | R | F1 | K | vis/hid L1 | vis/hid L2 | vis/hid L3 | End to end |
|---|---|---|---|---|---|---|---|---|---|---|
| 25_100_m45 | A gold mentions | original | 0.710 | 0.498 | **0.585** | 127 | 0.575 / 0.674 | 0.565 / 0.644 | 0.572 / 0.602 |  |
| 25_100_m45 | A gold mentions | chosen | 0.586 | 0.596 | **0.591** | 36 | 0.588 / 0.577 | 0.589 / 0.595 | 0.604 / 0.559 |  |
| 25_100_m45 | B GLiNER 0.5 spans | original | 0.772 | 0.493 | **0.602** | 201 | 0.584 / 0.700 | 0.588 / 0.654 | 0.585 / 0.637 | 0.435 |
| 25_100_m45 | B GLiNER 0.5 spans | chosen | 0.621 | 0.474 | **0.537** | 59 | 0.543 / 0.468 | 0.547 / 0.494 | 0.560 / 0.469 | 0.389 |
| 50_400 | A gold mentions | original | 0.672 | 0.409 | **0.508** | 137 | 0.490 / 0.691 | 0.478 / 0.593 | 0.468 / 0.570 |  |
| 50_400 | A gold mentions | chosen | 0.523 | 0.443 | **0.479** | 45 | 0.465 / 0.598 | 0.455 / 0.562 | 0.447 / 0.523 |  |
| 50_400 | B GLiNER 0.5 spans | original | 0.733 | 0.435 | **0.546** | 211 | 0.520 / 0.709 | 0.526 / 0.622 | 0.518 / 0.610 | 0.395 |
| 50_400 | B GLiNER 0.5 spans | chosen | 0.611 | 0.404 | **0.486** | 74 | 0.486 / 0.485 | 0.484 / 0.493 | 0.491 / 0.468 | 0.352 |

### 25_100_m45, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 39.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.654 | 0.628 | 0.640 |
| visible_L1 | 553 | 0.669 | 0.616 | 0.641 |
| hidden_L1 | 38 | 0.430 | 0.803 | 0.560 |
| visible_L2 | 462 | 0.649 | 0.637 | 0.643 |
| hidden_L2 | 129 | 0.669 | 0.594 | 0.629 |
| visible_L3 | 397 | 0.694 | 0.631 | 0.661 |
| hidden_L3 | 194 | 0.571 | 0.621 | 0.595 |

Per-class recall: Attraction area 0.72 (13); Attraction name 0.38 (12); Attraction type 0.49 (16); Hotel area 0.66 (15); Hotel confirmed reference 0.67 (16); Hotel name 0.34 (25); Hotel price range 0.86 (13); Hotel requested day 1.00 (18); Hotel requested people 0.26 (20); Hotel requested stay 0.29 (27); Hotel stars 0.50 (21); Hotel type 0.86 (13); Restaurant area 0.95 (36); Restaurant confirmed reference 0.28 (13); Restaurant food 1.00 (25); Restaurant name 0.42 (35); Restaurant price range 0.91 (21); Restaurant requested day 0.77 (16); Restaurant requested people 0.65 (15); Restaurant requested time 0.59 (16); Taxi arrive by 0.56 (3); Taxi departure 0.39 (6); Taxi destination 0.62 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.29 (18); Train day 1.00 (40); Train departure 0.42 (44); Train destination 0.41 (42); Train leave at 1.00 (23); Train requested people 0.39 (24)

Most confused (gold -> cluster majority): Train destination -> Train departure 18; Train departure -> Train destination 18; Train arrive by -> Train leave at 11; Attraction area -> Restaurant area 11; Hotel name -> Hotel type 9; Restaurant name -> Restaurant price range 8; Restaurant confirmed reference -> Train confirmed reference 7; Attraction name -> Attraction type 6; Hotel requested people -> Hotel requested stay 4; Hotel stars -> Hotel requested stay 4


### 25_100_m45, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 63.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.665 | 0.484 | 0.560 |
| visible_L1 | 355 | 0.683 | 0.491 | 0.571 |
| hidden_L1 | 34 | 0.476 | 0.413 | 0.442 |
| visible_L2 | 317 | 0.676 | 0.499 | 0.574 |
| hidden_L2 | 72 | 0.616 | 0.418 | 0.498 |
| visible_L3 | 289 | 0.710 | 0.507 | 0.592 |
| hidden_L3 | 100 | 0.533 | 0.417 | 0.468 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.38 (12); Attraction type 0.56 (3); Hotel area 0.56 (6); Hotel confirmed reference 0.67 (16); Hotel name 0.50 (23); Hotel price range 0.56 (6); Hotel requested day 1.00 (18); Hotel requested people 0.37 (6); Hotel requested stay 0.47 (19); Hotel stars 0.45 (6); Restaurant area 0.51 (9); Restaurant confirmed reference 0.28 (13); Restaurant food 1.00 (1); Restaurant name 0.23 (27); Restaurant price range 0.41 (8); Restaurant requested day 0.77 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.31 (16); Taxi arrive by 0.56 (3); Taxi departure 0.38 (4); Taxi destination 0.62 (4); Taxi leave at 0.50 (2); Train arrive by 0.40 (11); Train confirmed reference 0.34 (17); Train day 0.52 (40); Train departure 0.49 (41); Train destination 0.48 (38); Train leave at 0.35 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 17; Train destination -> Train departure 16; Train arrive by -> Train leave at 11; Restaurant confirmed reference -> Train confirmed reference 7; Restaurant name -> Restaurant price range 4; Attraction name -> Restaurant area 3; Taxi destination -> Restaurant name 3; Restaurant area -> Attraction name 3; Restaurant name -> Attraction name 3; Hotel confirmed reference -> Train confirmed reference 3

Largest mostly non-gold clusters:

- size 34 (22 non-gold): "abbey pool", "Abbey Pool", "Cherry Hinton", "Cherry Hinton", "centre", "centre", "98 king street", "City Centre", "Cherry Hinton", "Pizza Hut Cherry Hinton", "City Centre", "regent street", "city centre", "centre of town", "centre of town"
- size 30 (16 non-gold): "Pool Way", "43 High Street", "Cocum restaurant", "Cocum restaurant", "Midsummer House", "Peking Restaurant", "Clifton Way", "clifton way", "100 Mill Rd", "pizza express", "panahar", "Panahar", "17 magdalene street", "The cambridge chop house", "17 Magdalene Street City Centre"
- size 27 (16 non-gold): "Whitehill Road", "01223 249955", "Trinity", "Good Luck Chinese Food Takeaway", "01223 244277", "kymmoy", "cheap price range", "hotel", "4 - 6 Rose Crescent", "moderate price range", "Moderate price range", "restaurants", "graffiti", "Graffiti", "Hotel Felix Whitehouse Lane"
- size 22 (19 non-gold): "town", "town", "town", "expensive", "expensive", "expensive", "entrance fee", "entrance fee", "entrance fee", "expensive", "The Place", "expensive price range", "church", "expensive", "expensive price range"
- size 19 (19 non-gold): "01223314960", "07083984796", "01223367660", "01223367660", "01223412299", "01223311911", "07633256482", "15 minutes", "01223315232", "15 minutes", "01223359506", "01223464550", "01223354755", "01223446100", "01223362372"
- size 17 (15 non-gold): "TR1110", "TR6387", "TR6387", "cb23ap", "TR6193", "TR7610", "TR4669", "H4BIFD0U", "TR7604", "TR4202", "TR0032", "TR6838", "TYGH2E4A", "TR7935", "TR3677"
- size 16 (16 non-gold): "5:54", "05:54", "10:54", "13:40", "13:40", "09:35", "6:40", "16:55", "15:40", "22:35", "20:24", "15:50", "13:19", "18:24", "18:24"
- size 14 (14 non-gold): "20:08", "21:21", "21:21", "21:21", "09:52", "17:08", "19:58", "17:55", "21:16", "17:58", "16:07", "16:48", "18:52", "18:52"
- size 14 (8 non-gold): "Corpus Christi", "6 other guests", "Lucky Star", "Lucky Star", "La Raza", "La raza", "Anatolia", "reference number", "anatolia", "travellers rest", "Travellers Rest", "reference number", "Anglia Ruskin Enterprise", "reference number"
- size 12 (12 non-gold): "06:08", "06:43", "10:09", "11:09", "7:08", "09:19", "09:21", "7:16", "7:16", "10:09", "06:08", "5:01"


### 50_400, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 44.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.576 | 0.509 | 0.541 |
| visible_L1 | 553 | 0.583 | 0.488 | 0.531 |
| hidden_L1 | 38 | 0.471 | 0.820 | 0.598 |
| visible_L2 | 462 | 0.557 | 0.479 | 0.515 |
| hidden_L2 | 129 | 0.643 | 0.617 | 0.630 |
| visible_L3 | 397 | 0.592 | 0.437 | 0.503 |
| hidden_L3 | 194 | 0.543 | 0.656 | 0.594 |

Per-class recall: Attraction area 0.73 (13); Attraction name 0.31 (12); Attraction type 0.88 (16); Hotel area 0.66 (15); Hotel confirmed reference 0.31 (16); Hotel name 0.32 (25); Hotel price range 1.00 (13); Hotel requested day 0.45 (18); Hotel requested people 0.20 (20); Hotel requested stay 0.22 (27); Hotel stars 0.45 (21); Hotel type 0.73 (13); Restaurant area 0.66 (36); Restaurant confirmed reference 0.33 (13); Restaurant food 0.62 (25); Restaurant name 0.21 (35); Restaurant price range 0.61 (21); Restaurant requested day 0.77 (16); Restaurant requested people 0.35 (15); Restaurant requested time 0.60 (16); Taxi arrive by 1.00 (3); Taxi departure 0.28 (6); Taxi destination 0.62 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.31 (18); Train day 0.64 (40); Train departure 0.33 (44); Train destination 0.34 (42); Train leave at 1.00 (23); Train requested people 0.43 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 20; Attraction type -> Restaurant food 15; Train arrive by -> Train leave at 11; Attraction area -> Restaurant area 11; Hotel requested day -> Restaurant requested day 8; Train destination -> Train departure 7; Restaurant confirmed reference -> Train confirmed reference 6; Hotel name -> Hotel type 6; Hotel requested people -> Restaurant requested people 6; Attraction name -> Restaurant food 5


### 50_400, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 74.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.649 | 0.428 | 0.516 |
| visible_L1 | 355 | 0.662 | 0.429 | 0.520 |
| hidden_L1 | 34 | 0.518 | 0.421 | 0.464 |
| visible_L2 | 317 | 0.657 | 0.423 | 0.515 |
| hidden_L2 | 72 | 0.613 | 0.451 | 0.520 |
| visible_L3 | 289 | 0.684 | 0.424 | 0.523 |
| hidden_L3 | 100 | 0.549 | 0.441 | 0.489 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.38 (12); Attraction type 0.56 (3); Hotel area 1.00 (6); Hotel confirmed reference 0.28 (16); Hotel name 0.57 (23); Hotel price range 0.56 (6); Hotel requested day 0.45 (18); Hotel requested people 0.19 (6); Hotel requested stay 0.20 (19); Hotel stars 0.29 (6); Restaurant area 0.51 (9); Restaurant confirmed reference 0.33 (13); Restaurant food 1.00 (1); Restaurant name 0.24 (27); Restaurant price range 0.41 (8); Restaurant requested day 0.77 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.27 (16); Taxi arrive by 0.56 (3); Taxi departure 0.25 (4); Taxi destination 0.62 (4); Taxi leave at 0.50 (2); Train arrive by 0.40 (11); Train confirmed reference 0.36 (17); Train day 0.49 (40); Train departure 0.45 (41); Train destination 0.43 (38); Train leave at 0.39 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 15; Train destination -> Train departure 13; Hotel requested day -> Restaurant requested day 8; Restaurant confirmed reference -> Train confirmed reference 6; Train arrive by -> Train leave at 5; Restaurant confirmed reference -> Hotel confirmed reference 5; Train leave at -> Train arrive by 5; Hotel confirmed reference -> Train confirmed reference 4; Attraction name -> Restaurant area 3; Attraction type -> Attraction name 3

Largest mostly non-gold clusters:

- size 30 (18 non-gold): "abbey pool", "Abbey Pool", "Cherry Hinton", "Cherry Hinton", "centre", "centre", "City Centre", "Cherry Hinton", "Pizza Hut Cherry Hinton", "City Centre", "regent street", "city centre", "The Junction", "centre of town", "centre of town"
- size 27 (24 non-gold): "NewMarket Road", "C.B 1", "town", "town", "town", "expensive", "expensive", "expensive", "kymmoy", "entrance fee", "entrance fee", "entrance fee", "expensive", "The Place", "expensive price range"
- size 20 (17 non-gold): "TR1110", "TR6387", "TR6387", "cb11ln", "cb11ln", "TR6193", "TR7610", "TR4669", "TR8598", "H4BIFD0U", "H4BIFD0U", "TR7604", "TR4202", "TR0032", "TR6838"
- size 19 (13 non-gold): "07083984796", "01223412299", "07032807056", "07633256482", "15 minutes", "2 nights", "15 minutes", "2 nights", "5 nights", "01223354755", "01223276182", "3 nights", "two nights", "15 minutes", "07629102425"
- size 17 (16 non-gold): "20:08", "21:21", "21:21", "21:21", "09:52", "17:08", "6:40", "19:58", "11:06", "17:55", "21:16", "17:58", "17:30", "16:07", "16:48"
- size 17 (16 non-gold): "Pool Way", "43 High Street", "Bedouin", "bedouin", "Clifton Way", "clifton way", "100 Mill Rd", "viking way", "park", "Cherry Hinton Road", "parks", "park", "Kings Lynn", "Ugly Duckling", "lion yard"
- size 15 (14 non-gold): "Whitehill Road", "01223 249955", "saint andrew's street", "01223 244277", "bar hill", "17 magdalene street", "4 - 6 Rose Crescent", "30 Bridge Street", "Fen Causeway", "Fen Causeway", "30 Bridge Street City Centre", "6 Saint Edward's Passage", "heidelberg gardens", "01223 360966", "12 Market Hill"
- size 15 (12 non-gold): "6 other guests", "riverboat Georgina", "downing college", "same day", "reference number", "reference number", "17.89", "Anatolia", "37.79 GPB", "reference number", "table", "reference number", "what day", "table", "table"
- size 14 (12 non-gold): "01223367660", "01223367660", "01223311911", "8", "01223315232", "two", "01223359506", "01223464550", "3", "01223446100", "01223362372", "44", "01223364222", "4"
- size 13 (9 non-gold): "Saint John", "Peking Restaurant", "Thanh binh", "thanh binh", "hotel", "Anatolia", "Peking Restaurant", "restaurants", "anatolia", "travellers rest", "reference number", "Anglia Ruskin Enterprise", "restaurant"


