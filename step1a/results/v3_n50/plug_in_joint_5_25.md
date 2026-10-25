# C7: chosen Step 2 on predicted entities (50 dialogues)

Step 2 config: `{"normalize": true, "alpha": 0.5, "by_type": true, "linkage": "average", "t": 0.45, "cannot_link": true, "F1": 0.8029, "K": 30, "note": "joint re-tune, scratch ablation"}`. Stage 1 = k-means k=5 on segments (3 seeds, mean). Booking = (dialogue, segment). B value recall = 0.724. Run 0.7 min.

| Segments | Units | Stage 2 | P | R | F1 | K | vis/hid L1 | vis/hid L2 | vis/hid L3 | End to end |
|---|---|---|---|---|---|---|---|---|---|---|
| 5_25_s_m40 | A gold mentions | original | 0.775 | 0.552 | **0.645** | 125 | 0.636 / 0.695 | 0.625 / 0.702 | 0.632 / 0.662 |  |
| 5_25_s_m40 | A gold mentions | chosen | 0.713 | 0.688 | **0.700** | 37 | 0.700 / 0.626 | 0.697 / 0.713 | 0.715 / 0.667 |  |
| 5_25_s_m40 | B GLiNER 0.5 spans | original | 0.814 | 0.529 | **0.641** | 199 | 0.623 / 0.738 | 0.632 / 0.677 | 0.632 / 0.662 | 0.464 |
| 5_25_s_m40 | B GLiNER 0.5 spans | chosen | 0.739 | 0.526 | **0.615** | 71 | 0.626 / 0.493 | 0.620 / 0.592 | 0.638 / 0.549 | 0.445 |

### 5_25_s_m40, A gold mentions, chosen Step 2 (seed 42)

591 labelled of 591 units, K = 36.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.710 | 0.691 | 0.700 |
| visible_L1 | 553 | 0.726 | 0.675 | 0.700 |
| hidden_L1 | 38 | 0.475 | 0.917 | 0.626 |
| visible_L2 | 462 | 0.713 | 0.681 | 0.697 |
| hidden_L2 | 129 | 0.698 | 0.725 | 0.711 |
| visible_L3 | 397 | 0.745 | 0.687 | 0.715 |
| hidden_L3 | 194 | 0.639 | 0.699 | 0.667 |

Per-class recall: Attraction area 0.40 (13); Attraction name 0.26 (12); Attraction type 0.60 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.67 (16); Hotel name 0.50 (25); Hotel price range 1.00 (13); Hotel requested day 1.00 (18); Hotel requested people 0.27 (20); Hotel requested stay 0.29 (27); Hotel stars 0.50 (21); Hotel type 1.00 (13); Restaurant area 0.99 (36); Restaurant confirmed reference 0.74 (13); Restaurant food 1.00 (25); Restaurant name 0.30 (35); Restaurant price range 0.91 (21); Restaurant requested day 1.00 (16); Restaurant requested people 0.88 (15); Restaurant requested time 1.00 (16); Taxi arrive by 1.00 (3); Taxi departure 0.72 (6); Taxi destination 0.62 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 0.71 (18); Train day 1.00 (40); Train departure 0.44 (44); Train destination 0.42 (42); Train leave at 1.00 (23); Train requested people 0.45 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 18; Train destination -> Train departure 16; Train arrive by -> Train leave at 11; Attraction name -> Attraction area 6; Taxi departure -> Restaurant name 6; Restaurant name -> Restaurant price range 5; Taxi destination -> Restaurant name 4; Hotel name -> Hotel type 4; Hotel requested people -> Hotel requested stay 4; Hotel stars -> Hotel requested stay 4


### 5_25_s_m40, B GLiNER 0.5 spans, chosen Step 2 (seed 42)

389 labelled of 740 units, K = 71.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.740 | 0.527 | 0.616 |
| visible_L1 | 355 | 0.761 | 0.533 | 0.627 |
| hidden_L1 | 34 | 0.525 | 0.466 | 0.493 |
| visible_L2 | 317 | 0.754 | 0.527 | 0.621 |
| hidden_L2 | 72 | 0.679 | 0.528 | 0.594 |
| visible_L3 | 289 | 0.774 | 0.542 | 0.637 |
| hidden_L3 | 100 | 0.644 | 0.487 | 0.554 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.29 (12); Attraction type 0.56 (3); Hotel area 0.56 (6); Hotel confirmed reference 0.67 (16); Hotel name 0.27 (23); Hotel price range 0.56 (6); Hotel requested day 1.00 (18); Hotel requested people 0.37 (6); Hotel requested stay 0.44 (19); Hotel stars 0.45 (6); Restaurant area 0.56 (9); Restaurant confirmed reference 0.74 (13); Restaurant food 1.00 (1); Restaurant name 0.32 (27); Restaurant price range 0.41 (8); Restaurant requested day 1.00 (16); Restaurant requested people 0.62 (4); Restaurant requested time 0.62 (16); Taxi arrive by 0.56 (3); Taxi departure 0.38 (4); Taxi destination 0.25 (4); Taxi leave at 1.00 (2); Train arrive by 0.40 (11); Train confirmed reference 0.70 (17); Train day 0.52 (40); Train departure 0.49 (41); Train destination 0.44 (38); Train leave at 0.46 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 17; Train destination -> Train departure 14; Train arrive by -> Train leave at 5; Taxi arrive by -> Restaurant requested time 3; Train leave at -> Train arrive by 3; Restaurant name -> Restaurant price range 3; Taxi leave at -> Restaurant requested time 2; Taxi departure -> Restaurant area 2; Taxi destination -> Restaurant name 2; Restaurant confirmed reference -> Train confirmed reference 2

Largest mostly non-gold clusters:

- size 19 (19 non-gold): "07083984796", "01223367660", "01223367660", "01223412299", "01223311911", "07032807056", "07633256482", "15 minutes", "01223315232", "15 minutes", "01223359506", "01223464550", "01223354755", "01223362372", "01223276182"
- size 17 (15 non-gold): "TR1110", "TR6387", "TR6387", "TR6193", "TR7610", "TR4669", "TR8598", "TR7604", "GJ3062PE", "TR4202", "TR0032", "TR6838", "TR7935", "TR3677", "GGE66KI2"
- size 14 (14 non-gold): "20:08", "21:21", "21:21", "21:21", "09:52", "17:08", "19:58", "17:55", "21:16", "17:58", "16:07", "16:48", "18:52", "18:52"
- size 14 (10 non-gold): "43 High Street", "Midsummer House", "south side of town", "south side of town", "100 Mill Rd", "regent street", "17 magdalene street", "30 Bridge Street", "17 Magdalene Street City Centre", "30 Bridge Street City Centre", "12 St. Johns Street", "7 Milton Street", "7 Milton Road", "12 Market Hill"
- size 13 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "66 GBP", "64 GBP", "10.10 pounds", "7.84 GBP", "66 GBP", "14.08 pounds", "6 GBP", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 13 (13 non-gold): "5:54", "05:54", "10:54", "13:40", "13:40", "09:35", "6:40", "11:54", "16:55", "15:40", "22:35", "15:50", "13:19"
- size 13 (10 non-gold): "expensive", "expensive", "expensive", "kymmoy", "expensive", "expensive price range", "expensive", "expensive price range", "expensive", "expensive price range", "expensive price range", "Great", "cheap"
- size 12 (12 non-gold): "06:08", "06:43", "10:09", "11:09", "7:08", "09:19", "09:21", "7:16", "7:16", "10:09", "06:08", "5:01"
- size 12 (10 non-gold): "astroturf pitch", "Trinity", "Cherry Hinton", "entrance fee", "entrance fee", "Cineworld Cinema", "hotel", "Cherry Hinton Hall", "restaurants", "Mumford theatre", "entrance fee", "entrance fee"
- size 11 (11 non-gold): "Pool Way", "98 king street", "Clifton Way", "clifton way", "viking way", "The Junction", "nightclubs", "Hotel Felix Whitehouse Lane Huntingdon Road", "East Road", "Downing Street", "lion yard"


