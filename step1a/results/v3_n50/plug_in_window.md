# C7: chosen Step 2 on predicted entities (50 dialogues)

Step 2 config: `{"normalize": true, "by_type": true, "cannot_link": true, "linkage": "average", "prev_turns": 1, "alpha": 0.2, "t": 0.35, "window": 2, "beta": 0.5, "side": "lr", "F1": 0.8306, "K": 31, "n": 591, "limit": 50, "split": "dev", "ref_F1": 0.8029, "clear_gain": false}`. Stage 1 = k-means k=5 on segments (3 seeds, mean). Booking = (dialogue, segment). B value recall = 0.724. Run 4.0 min.

| Segments | Units | Stage 2 | P | R | F1 | K | vis/hid L1 | vis/hid L2 | vis/hid L3 | End to end |
|---|---|---|---|---|---|---|---|---|---|---|
| 5_25_s_m40 | A gold mentions | original | 0.775 | 0.552 | **0.645** | 125 | 0.636 / 0.695 | 0.625 / 0.702 | 0.632 / 0.662 |  |
| 5_25_s_m40 | A gold mentions | chosen | 0.746 | 0.741 | **0.744** | 36 | 0.747 / 0.624 | 0.741 / 0.751 | 0.750 / 0.724 |  |
| 5_25_s_m40 | B GLiNER 0.5 spans | original | 0.814 | 0.529 | **0.641** | 199 | 0.623 / 0.738 | 0.632 / 0.677 | 0.632 / 0.662 | 0.464 |
| 5_25_s_m40 | B GLiNER 0.5 spans | chosen | 0.761 | 0.525 | **0.621** | 72 | 0.628 / 0.545 | 0.620 / 0.625 | 0.615 / 0.635 | 0.449 |
| turn_m40 | A gold mentions | original | 0.769 | 0.544 | **0.637** | 125 | 0.628 / 0.701 | 0.609 / 0.720 | 0.612 / 0.675 |  |
| turn_m40 | A gold mentions | chosen | 0.736 | 0.741 | **0.739** | 34 | 0.742 / 0.627 | 0.723 / 0.790 | 0.730 / 0.749 |  |
| turn_m40 | B GLiNER 0.5 spans | original | 0.814 | 0.514 | **0.630** | 198 | 0.609 / 0.753 | 0.613 / 0.694 | 0.617 / 0.662 | 0.456 |
| turn_m40 | B GLiNER 0.5 spans | chosen | 0.752 | 0.541 | **0.630** | 71 | 0.635 / 0.573 | 0.612 / 0.702 | 0.608 / 0.685 | 0.456 |
| turn_m30 | A gold mentions | original | 0.787 | 0.520 | **0.626** | 133 | 0.614 / 0.735 | 0.598 / 0.710 | 0.601 / 0.665 |  |
| turn_m30 | A gold mentions | chosen | 0.766 | 0.710 | **0.736** | 41 | 0.737 / 0.698 | 0.720 / 0.791 | 0.736 / 0.733 |  |
| turn_m30 | B GLiNER 0.5 spans | original | 0.832 | 0.498 | **0.623** | 205 | 0.600 / 0.775 | 0.605 / 0.693 | 0.608 / 0.661 | 0.451 |
| turn_m30 | B GLiNER 0.5 spans | chosen | 0.788 | 0.534 | **0.636** | 78 | 0.635 / 0.644 | 0.613 / 0.731 | 0.609 / 0.707 | 0.460 |
| 25_100_s_m45 | A gold mentions | original | 0.759 | 0.527 | **0.622** | 127 | 0.614 / 0.675 | 0.603 / 0.679 | 0.610 / 0.638 |  |
| 25_100_s_m45 | A gold mentions | chosen | 0.701 | 0.672 | **0.686** | 36 | 0.689 / 0.583 | 0.677 / 0.715 | 0.694 / 0.665 |  |
| 25_100_s_m45 | B GLiNER 0.5 spans | original | 0.807 | 0.516 | **0.630** | 200 | 0.614 / 0.711 | 0.618 / 0.674 | 0.616 / 0.662 | 0.456 |
| 25_100_s_m45 | B GLiNER 0.5 spans | chosen | 0.749 | 0.509 | **0.606** | 72 | 0.613 / 0.533 | 0.596 / 0.647 | 0.591 / 0.645 | 0.439 |

### 5_25_s_m40, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 35.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.745 | 0.745 | 0.745 |
| visible_L1 | 553 | 0.763 | 0.733 | 0.748 |
| hidden_L1 | 38 | 0.473 | 0.917 | 0.624 |
| visible_L2 | 462 | 0.758 | 0.727 | 0.742 |
| hidden_L2 | 129 | 0.698 | 0.808 | 0.749 |
| visible_L3 | 397 | 0.779 | 0.724 | 0.751 |
| hidden_L3 | 194 | 0.673 | 0.788 | 0.726 |

Per-class recall: Attraction area 0.69 (13); Attraction name 0.38 (12); Attraction type 0.70 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.59 (16); Hotel name 0.54 (25); Hotel price range 0.86 (13); Hotel requested day 1.00 (18); Hotel requested people 0.45 (20); Hotel requested stay 0.40 (27); Hotel stars 0.73 (21); Hotel type 1.00 (13); Restaurant area 0.99 (36); Restaurant confirmed reference 0.74 (13); Restaurant food 1.00 (25); Restaurant name 0.62 (35); Restaurant price range 0.82 (21); Restaurant requested day 1.00 (16); Restaurant requested people 0.88 (15); Restaurant requested time 1.00 (16); Taxi arrive by 1.00 (3); Taxi departure 0.72 (6); Taxi destination 0.62 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 0.80 (18); Train day 1.00 (40); Train departure 0.44 (44); Train destination 0.42 (42); Train leave at 1.00 (23); Train requested people 0.71 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 18; Train destination -> Train departure 16; Train arrive by -> Train leave at 11; Taxi departure -> Restaurant name 6; Attraction name -> Attraction type 5; Hotel requested stay -> Hotel stars 5; Taxi destination -> Restaurant name 4; Taxi arrive by -> Restaurant requested time 3; Attraction type -> Restaurant price range 3; Train requested people -> Hotel stars 3


### 5_25_s_m40, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 72.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.759 | 0.517 | 0.615 |
| visible_L1 | 355 | 0.768 | 0.523 | 0.622 |
| hidden_L1 | 34 | 0.661 | 0.463 | 0.545 |
| visible_L2 | 317 | 0.765 | 0.511 | 0.613 |
| hidden_L2 | 72 | 0.733 | 0.546 | 0.626 |
| visible_L3 | 289 | 0.771 | 0.502 | 0.608 |
| hidden_L3 | 100 | 0.723 | 0.562 | 0.632 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.26 (12); Attraction type 0.56 (3); Hotel area 1.00 (6); Hotel confirmed reference 0.52 (16); Hotel name 0.36 (23); Hotel price range 0.56 (6); Hotel requested day 1.00 (18); Hotel requested people 0.37 (6); Hotel requested stay 0.44 (19); Hotel stars 0.45 (6); Restaurant area 0.80 (9); Restaurant confirmed reference 0.74 (13); Restaurant food 1.00 (1); Restaurant name 0.19 (27); Restaurant price range 0.41 (8); Restaurant requested day 1.00 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.38 (16); Taxi arrive by 0.56 (3); Taxi departure 0.25 (4); Taxi destination 0.62 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.62 (17); Train day 0.51 (40); Train departure 0.40 (41); Train destination 0.40 (38); Train leave at 0.46 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 21; Train destination -> Train departure 10; Restaurant name -> Restaurant area 5; Attraction type -> Attraction name 3; Taxi destination -> Restaurant area 3; Taxi arrive by -> Restaurant requested time 3; Taxi leave at -> Restaurant requested time 2; Taxi departure -> Restaurant area 2; Taxi departure -> Restaurant name 2; Attraction area -> Attraction name 2

Largest mostly non-gold clusters:

- size 27 (17 non-gold): "06:08", "06:43", "10:54", "13:00", "13:00", "10:09", "21:00", "09:35", "17:00", "11:00", "11:00", "7:08", "19:30", "7:16", "10:09"
- size 18 (18 non-gold): "20:08", "5:54", "05:54", "09:52", "17:08", "11:09", "21:29", "11:32", "19:58", "09:19", "11:06", "11:54", "17:55", "22:35", "17:58"
- size 18 (18 non-gold): "07083984796", "01223367660", "01223367660", "01223412299", "01223311911", "07032807056", "07633256482", "01223315232", "One", "one", "01223359506", "01223464550", "01223354755", "01223362372", "01223276182"
- size 17 (15 non-gold): "43 High Street", "64 Cherry Hinton Road", "100 Mill Rd", "regent street", "17 magdalene street", "30 Bridge Street", "17 Magdalene Street City Centre", "30 Bridge Street City Centre", "huntingdon road", "12 St. Johns Street", "Histon Road", "6 Lensfield Road", "68 Histon Road", "7 Milton Street", "7 Milton Road"
- size 17 (12 non-gold): "Cherry Hinton", "Cherry Hinton", "Bedouin", "bedouin", "Lucky Star", "Lucky Star", "Pizza Hut Cherry Hinton", "entrance fee", "La Raza", "La raza", "reference number", "reference number", "Chesterton", "The Nirala", "the Nirala"
- size 15 (8 non-gold): "astroturf pitch", "town", "town", "town", "Broughton house gallery", "Emmanuel College", "Emmanuel College", "bar hill", "hotel", "Cherry Hinton Hall", "south side of town", "restaurants", "Anglia Ruskin Enterprise", "Ballare", "Ballare"
- size 14 (13 non-gold): "Pool Way", "Corpus Christi", "saint andrew's street", "Clifton Way", "clifton way", "viking way", "The Place", "alexander bed and breakfast", "museum", "Hotel Felix Whitehouse Lane Huntingdon Road", "East Road", "Downing Street", "6 Saint Edward's Passage", "heidelberg gardens"
- size 14 (10 non-gold): "Whitehill Road", "centre", "centre", "98 king street", "01223 244277", "The Whale of a Time", "The Whale of a Time", "Cineworld Cinema", "centre of town", "Cherry Hinton Water Play", "Fen Causeway", "Fen Causeway", "Hotel Felix Whitehouse Lane", "Centre area"
- size 14 (14 non-gold): "21:21", "21:21", "13:40", "13:40", "21:21", "6:40", "09:21", "7:16", "15:40", "21:16", "17:01", "15:50", "13:19", "18:24"
- size 14 (8 non-gold): "6 other guests", "riverboat Georgina", "downing college", "4 - 6 Rose Crescent", "Anatolia", "anatolia", "Anatolia", "travellers rest", "Travellers Rest", "the ugly duckling", "table", "Your table", "table", "table"


### turn_m40, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 34.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.698 | 0.705 | 0.701 |
| visible_L1 | 553 | 0.711 | 0.692 | 0.701 |
| hidden_L1 | 38 | 0.515 | 0.886 | 0.651 |
| visible_L2 | 462 | 0.693 | 0.661 | 0.677 |
| hidden_L2 | 129 | 0.716 | 0.860 | 0.781 |
| visible_L3 | 397 | 0.716 | 0.650 | 0.681 |
| hidden_L3 | 194 | 0.661 | 0.817 | 0.731 |

Per-class recall: Attraction area 0.62 (13); Attraction name 0.38 (12); Attraction type 0.70 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.88 (16); Hotel name 0.66 (25); Hotel price range 0.86 (13); Hotel requested day 1.00 (18); Hotel requested people 0.39 (20); Hotel requested stay 0.38 (27); Hotel stars 0.78 (21); Hotel type 1.00 (13); Restaurant area 0.80 (36); Restaurant confirmed reference 0.48 (13); Restaurant food 0.92 (25); Restaurant name 0.57 (35); Restaurant price range 0.82 (21); Restaurant requested day 0.50 (16); Restaurant requested people 0.44 (15); Restaurant requested time 0.53 (16); Taxi arrive by 1.00 (3); Taxi departure 0.28 (6); Taxi destination 1.00 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 1.00 (18); Train day 1.00 (40); Train departure 0.44 (44); Train destination 0.42 (42); Train leave at 1.00 (23); Train requested people 0.84 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 18; Train destination -> Train departure 16; Train arrive by -> Train leave at 11; Restaurant requested day -> Hotel requested day 8; Attraction name -> Attraction type 5; Hotel requested stay -> Hotel stars 5; Restaurant requested people -> Hotel requested people 4; Restaurant confirmed reference -> Hotel confirmed reference 4; Taxi destination -> Hotel type 4; Restaurant name -> Hotel type 3


### turn_m40, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 73.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.727 | 0.526 | 0.611 |
| visible_L1 | 355 | 0.730 | 0.522 | 0.609 |
| hidden_L1 | 34 | 0.688 | 0.576 | 0.627 |
| visible_L2 | 317 | 0.719 | 0.489 | 0.582 |
| hidden_L2 | 72 | 0.763 | 0.689 | 0.724 |
| visible_L3 | 289 | 0.720 | 0.479 | 0.575 |
| hidden_L3 | 100 | 0.745 | 0.665 | 0.703 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.26 (12); Attraction type 0.56 (3); Hotel area 1.00 (6); Hotel confirmed reference 0.88 (16); Hotel name 0.38 (23); Hotel price range 0.56 (6); Hotel requested day 1.00 (18); Hotel requested people 0.37 (6); Hotel requested stay 0.44 (19); Hotel stars 0.45 (6); Restaurant area 0.80 (9); Restaurant confirmed reference 0.48 (13); Restaurant food 1.00 (1); Restaurant name 0.22 (27); Restaurant price range 0.41 (8); Restaurant requested day 0.50 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.24 (16); Taxi arrive by 1.00 (3); Taxi departure 0.25 (4); Taxi destination 1.00 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 1.00 (17); Train day 0.51 (40); Train departure 0.40 (41); Train destination 0.40 (38); Train leave at 0.46 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 21; Train destination -> Train departure 10; Restaurant requested day -> Hotel requested day 8; Restaurant confirmed reference -> Hotel confirmed reference 4; Taxi destination -> Hotel name 4; Attraction type -> Attraction name 3; Restaurant requested people -> Hotel requested stay 3; Taxi arrive by -> Restaurant requested time 3; Restaurant name -> Hotel name 2; Taxi leave at -> Restaurant requested time 2

Largest mostly non-gold clusters:

- size 27 (17 non-gold): "06:08", "06:43", "10:54", "13:00", "13:00", "10:09", "21:00", "09:35", "17:00", "11:00", "11:00", "7:08", "19:30", "7:16", "10:09"
- size 18 (18 non-gold): "20:08", "5:54", "05:54", "09:52", "17:08", "11:09", "21:29", "11:32", "19:58", "09:19", "11:06", "11:54", "17:55", "22:35", "17:58"
- size 17 (9 non-gold): "07083984796", "07032807056", "07633256482", "15 minutes", "15 minutes", "4 nights", "4 nights", "1 night", "3 nights", "07629102425", "4 nights", "01223355017", "4 nights", "4 nights", "15 minutes"
- size 15 (8 non-gold): "astroturf pitch", "town", "town", "town", "Broughton house gallery", "Emmanuel College", "Emmanuel College", "bar hill", "hotel", "Cherry Hinton Hall", "south side of town", "restaurants", "Anglia Ruskin Enterprise", "Ballare", "Ballare"
- size 15 (14 non-gold): "43 High Street", "100 Mill Rd", "regent street", "17 magdalene street", "4 - 6 Rose Crescent", "30 Bridge Street", "17 Magdalene Street City Centre", "30 Bridge Street City Centre", "huntingdon road", "12 St. Johns Street", "6 Lensfield Road", "68 Histon Road", "7 Milton Street", "7 Milton Road", "12 Market Hill"
- size 15 (11 non-gold): "Cherry Hinton", "Cherry Hinton", "expensive", "expensive", "expensive", "Pizza Hut Cherry Hinton", "cheap price range", "expensive price range", "expensive", "expensive price range", "expensive", "expensive price range", "expensive price range", "Chesterton", "Chesterton"
- size 14 (10 non-gold): "Whitehill Road", "centre", "centre", "98 king street", "01223 244277", "The Whale of a Time", "The Whale of a Time", "Cineworld Cinema", "centre of town", "Cherry Hinton Water Play", "Fen Causeway", "Fen Causeway", "Hotel Felix Whitehouse Lane", "Centre area"
- size 14 (14 non-gold): "21:21", "21:21", "13:40", "13:40", "21:21", "6:40", "09:21", "7:16", "15:40", "21:16", "17:01", "15:50", "13:19", "18:24"
- size 13 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "66 GBP", "64 GBP", "10.10 pounds", "7.84 GBP", "66 GBP", "14.08 pounds", "6 GBP", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 13 (11 non-gold): "abbey pool", "Abbey Pool", "Trinity", "Cherry Hinton", "entrance fee", "entrance fee", "park", "Cherry Hinton Water Play", "Cherry Hinton Road", "parks", "park", "entrance fee", "entrance fee"


### turn_m30, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 43.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.738 | 0.647 | 0.689 |
| visible_L1 | 553 | 0.751 | 0.633 | 0.687 |
| hidden_L1 | 38 | 0.548 | 0.846 | 0.666 |
| visible_L2 | 462 | 0.738 | 0.619 | 0.673 |
| hidden_L2 | 129 | 0.736 | 0.747 | 0.742 |
| visible_L3 | 397 | 0.759 | 0.616 | 0.680 |
| hidden_L3 | 194 | 0.695 | 0.710 | 0.702 |

Per-class recall: Attraction area 0.51 (13); Attraction name 0.24 (12); Attraction type 0.60 (16); Hotel area 0.68 (15); Hotel confirmed reference 0.60 (16); Hotel name 0.44 (25); Hotel price range 0.74 (13); Hotel requested day 0.65 (18); Hotel requested people 0.22 (20); Hotel requested stay 0.26 (27); Hotel stars 0.29 (21); Hotel type 0.86 (13); Restaurant area 0.80 (36); Restaurant confirmed reference 0.64 (13); Restaurant food 0.92 (25); Restaurant name 0.74 (35); Restaurant price range 0.82 (21); Restaurant requested day 0.62 (16); Restaurant requested people 0.56 (15); Restaurant requested time 0.78 (16); Taxi arrive by 1.00 (3); Taxi departure 0.28 (6); Taxi destination 0.62 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 1.00 (18); Train day 0.95 (40); Train departure 0.36 (44); Train destination 0.35 (42); Train leave at 1.00 (23); Train requested people 0.84 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 22; Train arrive by -> Train leave at 11; Train destination -> Train departure 10; Hotel stars -> Hotel requested stay 5; Hotel confirmed reference -> Restaurant confirmed reference 4; Hotel requested day -> Restaurant requested day 4; Attraction name -> Attraction type 3; Attraction type -> Restaurant price range 3; Hotel requested people -> Hotel requested stay 3; Hotel area -> Taxi destination 3


### turn_m30, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 85.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.779 | 0.497 | 0.606 |
| visible_L1 | 355 | 0.777 | 0.493 | 0.604 |
| hidden_L1 | 34 | 0.792 | 0.532 | 0.636 |
| visible_L2 | 317 | 0.768 | 0.469 | 0.582 |
| hidden_L2 | 72 | 0.827 | 0.619 | 0.708 |
| visible_L3 | 289 | 0.767 | 0.456 | 0.572 |
| hidden_L3 | 100 | 0.813 | 0.614 | 0.699 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.15 (12); Attraction type 1.00 (3); Hotel area 0.56 (6); Hotel confirmed reference 0.60 (16); Hotel name 0.45 (23); Hotel price range 0.50 (6); Hotel requested day 0.65 (18); Hotel requested people 0.23 (6); Hotel requested stay 0.48 (19); Hotel stars 0.36 (6); Restaurant area 0.80 (9); Restaurant confirmed reference 0.64 (13); Restaurant food 1.00 (1); Restaurant name 0.19 (27); Restaurant price range 0.41 (8); Restaurant requested day 0.62 (16); Restaurant requested people 0.38 (4); Restaurant requested time 0.31 (16); Taxi arrive by 1.00 (3); Taxi departure 0.25 (4); Taxi destination 0.62 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 1.00 (17); Train day 0.48 (40); Train departure 0.38 (41); Train destination 0.40 (38); Train leave at 0.46 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 20; Train destination -> Train departure 11; Restaurant name -> Restaurant area 5; Hotel confirmed reference -> Restaurant confirmed reference 4; Hotel requested day -> Restaurant requested day 4; Taxi leave at -> Taxi arrive by 2; Attraction name -> Hotel name 2; Attraction name -> Attraction type 1; Restaurant food -> Restaurant price range 1; Taxi departure -> Restaurant area 1

Largest mostly non-gold clusters:

- size 27 (17 non-gold): "06:08", "06:43", "10:54", "13:00", "13:00", "10:09", "21:00", "09:35", "17:00", "11:00", "11:00", "7:08", "19:30", "7:16", "10:09"
- size 18 (18 non-gold): "20:08", "5:54", "05:54", "09:52", "17:08", "11:09", "21:29", "11:32", "19:58", "09:19", "11:06", "11:54", "17:55", "22:35", "17:58"
- size 16 (15 non-gold): "43 High Street", "64 Cherry Hinton Road", "100 Mill Rd", "regent street", "17 magdalene street", "30 Bridge Street", "17 Magdalene Street City Centre", "30 Bridge Street City Centre", "huntingdon road", "12 St. Johns Street", "Histon Road", "6 Lensfield Road", "68 Histon Road", "7 Milton Street", "7 Milton Road"
- size 15 (11 non-gold): "Cherry Hinton", "Cherry Hinton", "expensive", "expensive", "expensive", "Pizza Hut Cherry Hinton", "cheap price range", "expensive price range", "expensive", "expensive price range", "expensive", "expensive price range", "expensive price range", "Chesterton", "Chesterton"
- size 14 (14 non-gold): "21:21", "21:21", "13:40", "13:40", "21:21", "6:40", "09:21", "7:16", "15:40", "21:16", "17:01", "15:50", "13:19", "18:24"
- size 13 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "66 GBP", "64 GBP", "10.10 pounds", "7.84 GBP", "66 GBP", "14.08 pounds", "6 GBP", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 13 (8 non-gold): "town", "town", "town", "Broughton house gallery", "Emmanuel College", "Emmanuel College", "01223 244277", "hotel", "Cherry Hinton Hall", "south side of town", "restaurants", "Anglia Ruskin Enterprise", "Museum of Archaeology and Anthropology"
- size 12 (11 non-gold): "centre", "centre", "98 king street", "saint andrew's street", "Clifton Way", "clifton way", "centre of town", "Fen Causeway", "Fen Causeway", "Centre area", "6 Saint Edward's Passage", "lion yard"
- size 12 (9 non-gold): "07083984796", "07032807056", "07633256482", "15 minutes", "4 nights", "2 nights", "07629102425", "01223355017", "3 nights", "3 nights", "15 minutes", "07242149665"
- size 11 (11 non-gold): "TR1110", "TR9016", "TR9016", "TR9016", "TR9016", "TR7610", "TR8598", "TR7604", "TR4202", "TR0032", "TR4679"


### 25_100_s_m45, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 37.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.668 | 0.630 | 0.649 |
| visible_L1 | 553 | 0.683 | 0.620 | 0.650 |
| hidden_L1 | 38 | 0.449 | 0.776 | 0.569 |
| visible_L2 | 462 | 0.666 | 0.599 | 0.631 |
| hidden_L2 | 129 | 0.675 | 0.743 | 0.708 |
| visible_L3 | 397 | 0.695 | 0.598 | 0.643 |
| hidden_L3 | 194 | 0.614 | 0.696 | 0.652 |

Per-class recall: Attraction area 0.52 (13); Attraction name 0.31 (12); Attraction type 0.30 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.52 (16); Hotel name 0.60 (25); Hotel price range 0.86 (13); Hotel requested day 1.00 (18); Hotel requested people 0.45 (20); Hotel requested stay 0.44 (27); Hotel stars 0.73 (21); Hotel type 1.00 (13); Restaurant area 0.80 (36); Restaurant confirmed reference 0.44 (13); Restaurant food 0.72 (25); Restaurant name 0.24 (35); Restaurant price range 0.82 (21); Restaurant requested day 0.53 (16); Restaurant requested people 0.49 (15); Restaurant requested time 0.62 (16); Taxi arrive by 0.56 (3); Taxi departure 0.39 (6); Taxi destination 0.38 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.80 (18); Train day 1.00 (40); Train departure 0.43 (44); Train destination 0.40 (42); Train leave at 1.00 (23); Train requested people 0.58 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 17; Train destination -> Train departure 16; Train arrive by -> Train leave at 11; Restaurant requested day -> Hotel requested day 6; Restaurant name -> Restaurant food 6; Attraction name -> Attraction type 5; Hotel requested stay -> Hotel stars 5; Attraction type -> Attraction area 4; Restaurant confirmed reference -> Hotel confirmed reference 4; Restaurant requested people -> Hotel requested people 3


### 25_100_s_m45, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 72.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.741 | 0.493 | 0.592 |
| visible_L1 | 355 | 0.744 | 0.500 | 0.598 |
| hidden_L1 | 34 | 0.709 | 0.429 | 0.534 |
| visible_L2 | 317 | 0.738 | 0.476 | 0.579 |
| hidden_L2 | 72 | 0.753 | 0.569 | 0.648 |
| visible_L3 | 289 | 0.738 | 0.467 | 0.572 |
| hidden_L3 | 100 | 0.751 | 0.570 | 0.648 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.19 (12); Attraction type 0.56 (3); Hotel area 1.00 (6); Hotel confirmed reference 0.60 (16); Hotel name 0.38 (23); Hotel price range 0.56 (6); Hotel requested day 1.00 (18); Hotel requested people 0.37 (6); Hotel requested stay 0.44 (19); Hotel stars 0.45 (6); Restaurant area 0.80 (9); Restaurant confirmed reference 0.44 (13); Restaurant food 1.00 (1); Restaurant name 0.25 (27); Restaurant price range 0.41 (8); Restaurant requested day 0.53 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.25 (16); Taxi arrive by 0.33 (3); Taxi departure 0.38 (4); Taxi destination 0.38 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.79 (17); Train day 0.51 (40); Train departure 0.40 (41); Train destination 0.40 (38); Train leave at 0.46 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 21; Train destination -> Train departure 10; Restaurant requested day -> Hotel requested day 6; Restaurant confirmed reference -> Hotel confirmed reference 4; Restaurant requested people -> Hotel requested stay 3; Attraction type -> Attraction name 2; Restaurant name -> Hotel price range 2; Taxi destination -> Restaurant name 2; Taxi arrive by -> Restaurant requested time 2; Taxi departure -> Restaurant area 2

Largest mostly non-gold clusters:

- size 16 (10 non-gold): "astroturf pitch", "town", "town", "town", "Emmanuel College", "Emmanuel College", "Cherry Hinton", "The Place", "church", "Cherry Hinton Water Play", "Cherry Hinton Water Play", "south side of town", "museum", "East Road", "Downing Street"
- size 16 (15 non-gold): "43 High Street", "cambridge leisure park", "100 Mill Rd", "regent street", "17 magdalene street", "4 - 6 Rose Crescent", "30 Bridge Street", "17 Magdalene Street City Centre", "30 Bridge Street City Centre", "huntingdon road", "12 St. Johns Street", "6 Lensfield Road", "68 Histon Road", "7 Milton Street", "7 Milton Road"
- size 16 (16 non-gold): "21:21", "21:21", "13:40", "13:40", "21:21", "6:40", "09:21", "7:16", "15:40", "21:16", "17:01", "15:50", "13:19", "18:24", "18:24"
- size 15 (15 non-gold): "06:08", "06:43", "10:09", "09:35", "7:08", "11:32", "19:58", "11:06", "7:16", "10:09", "06:08", "22:35", "5:01", "16:07", "18:52"
- size 14 (14 non-gold): "TR7213", "TR6387", "TR6387", "TR6193", "TR1719", "TR4669", "TR8598", "TR7604", "TR1755", "TR7935", "TR3677", "TR5713", "TR4679", "TR5921"
- size 14 (10 non-gold): "Cherry Hinton", "Cherry Hinton", "expensive", "expensive", "expensive", "Pizza Hut Cherry Hinton", "cheap price range", "expensive price range", "expensive", "expensive price range", "expensive", "expensive price range", "expensive price range", "Great"
- size 14 (13 non-gold): "reference number", "riverboat Georgina", "same day", "reference number", "Gonville Place", "reference number", "reference number", "what day", "reference number", "table", "table", "same day", "same day", "what day"
- size 13 (13 non-gold): "20:08", "5:54", "05:54", "10:54", "09:52", "17:08", "11:09", "21:29", "09:19", "11:54", "17:58", "16:48", "18:52"
- size 13 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "66 GBP", "64 GBP", "10.10 pounds", "7.84 GBP", "66 GBP", "14.08 pounds", "6 GBP", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 13 (8 non-gold): "C.B 1", "Lucky Star", "clifton way", "entrance fee", "La Raza", "La raza", "reference number", "reference number", "Chesterton", "The Nirala", "the Nirala", "reference number", "Chesterton"


