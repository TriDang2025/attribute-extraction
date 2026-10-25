# C7: chosen Step 2 on predicted entities (50 dialogues)

Step 2 config (spans): `{"normalize": true, "alpha": 0.5, "by_type": true, "linkage": "average", "t": 0.45, "cannot_link": true, "F1": 0.8029, "K": 30, "note": "joint re-tune, scratch ablation"}`; (gold mentions): `{"normalize": true, "by_type": true, "cannot_link": true, "linkage": "average", "prev_turns": 1, "alpha": 0.2, "t": 0.35, "window": 2, "beta": 0.5, "side": "lr", "F1": 0.8306, "K": 31, "n": 591, "limit": 50, "split": "dev", "ref_F1": 0.8029, "clear_gain": false}`. Stage 1 = k-means k=5 on segments (3 seeds, mean). Booking = (dialogue, segment). B value recall = 0.887. Run 16.3 min.

| Segments | Units | Stage 2 | P | R | F1 | K | vis/hid L1 | vis/hid L2 | vis/hid L3 | End to end |
|---|---|---|---|---|---|---|---|---|---|---|
| 5_25_s_m40 | A gold mentions | original | 0.775 | 0.552 | **0.645** | 125 | 0.636 / 0.695 | 0.625 / 0.702 | 0.632 / 0.662 |  |
| 5_25_s_m40 | A gold mentions | chosen | 0.746 | 0.741 | **0.744** | 36 | 0.747 / 0.624 | 0.741 / 0.751 | 0.750 / 0.724 |  |
| 5_25_s_m40 | B GLiNER 0.5 spans | original | 0.809 | 0.495 | **0.614** | 223 | 0.597 / 0.715 | 0.594 / 0.687 | 0.607 / 0.628 | 0.545 |
| 5_25_s_m40 | B GLiNER 0.5 spans | chosen | 0.725 | 0.437 | **0.546** | 104 | 0.557 / 0.411 | 0.546 / 0.544 | 0.574 / 0.481 | 0.484 |

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

491 labelled of 1124 units, K = 105.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 491 | 0.730 | 0.433 | 0.544 |
| visible_L1 | 453 | 0.747 | 0.441 | 0.555 |
| hidden_L1 | 38 | 0.522 | 0.339 | 0.411 |
| visible_L2 | 395 | 0.732 | 0.435 | 0.546 |
| hidden_L2 | 96 | 0.721 | 0.426 | 0.535 |
| visible_L3 | 343 | 0.758 | 0.460 | 0.573 |
| hidden_L3 | 148 | 0.663 | 0.371 | 0.476 |

Per-class recall: Attraction area 0.20 (11); Attraction name 0.20 (13); Attraction type 0.21 (12); Hotel area 0.38 (11); Hotel confirmed reference 0.67 (16); Hotel name 0.19 (23); Hotel price range 0.63 (9); Hotel requested day 1.00 (18); Hotel requested people 0.52 (16); Hotel requested stay 0.36 (17); Hotel stars 0.33 (10); Hotel type 0.49 (6); Restaurant area 0.21 (32); Restaurant confirmed reference 0.74 (13); Restaurant food 0.18 (8); Restaurant name 0.13 (33); Restaurant price range 0.38 (9); Restaurant requested day 1.00 (16); Restaurant requested people 0.50 (11); Restaurant requested time 0.59 (16); Taxi arrive by 0.33 (3); Taxi departure 0.22 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 0.36 (11); Train confirmed reference 0.64 (18); Train day 0.74 (40); Train departure 0.27 (44); Train destination 0.35 (41); Train leave at 0.37 (23); Train requested people 0.34 (10)

Most confused (gold -> cluster majority): Train departure -> Train destination 21; Train destination -> Train departure 11; Restaurant name -> Restaurant area 8; Train arrive by -> Train leave at 6; Attraction type -> Attraction name 4; Train leave at -> Train arrive by 4; Taxi departure -> Restaurant name 3; Taxi destination -> Restaurant name 3; Taxi arrive by -> Restaurant requested time 3; Restaurant food -> Restaurant name 3

Largest mostly non-gold clusters:

- size 34 (26 non-gold): "I", "I", "I", "I", "I", "I", "I", "I", "I", "Ely", "ely", "i", "I", "I", "I"
- size 25 (16 non-gold): "9 H.X", "Center", "Taj Tandoori", "Taj Tandoori", "centre", "Somewhere in the centre", "I", "I", "I", "i", "I", "I", "centre", "They", "centre"
- size 23 (19 non-gold): "phone number", "phone number", "phone number", "phone number", "riverboat Georgina", "entry fee", "contact number", "Contact number", "phone number", "Restaurant Two Two", "phone number", "phone number", "their phone number", "phone number", "table"
- size 23 (12 non-gold): "restaurant", "restaurant", "city stop restaurant", "The restaurant", "Pizza Hut", "pizza express", "pizza express", "panahar", "Panahar", "turkish food restaurant", "restaurant", "The restaurant", "turkish restaurants", "restaurant", "restaurant"
- size 21 (13 non-gold): "Bedouin", "bedouin", "south", "another part of town", "north", "3 Turkish restaurants", "hotel", "hotel", "south", "graffiti", "Graffiti", "graffiti", "night", "same day", "what time"
- size 19 (12 non-gold): "Cherry Hinton", "Cherry Hinton", "City Centre", "Cherry Hinton", "City Centre", "Downing College", "downing college", "city centre", "City Centre", "City Centre", "City Centre", "City Centre", "city centre", "Chesterton", "Chesterton"
- size 19 (19 non-gold): "07083984796", "01223367660", "01223367660", "01223412299", "01223311911", "07032807056", "07633256482", "15 minutes", "01223315232", "15 minutes", "01223359506", "01223464550", "01223354755", "01223362372", "01223276182"
- size 18 (18 non-gold): "address", "address", "address", "address", "reference number", "address", "address", "address", "reference number", "address", "reference number", "reference number", "reference number", "address", "reference number"
- size 18 (10 non-gold): "C.B 1", "Cocum restaurant", "Cocum restaurant", "price range", "Lucky Star", "Lucky Star", "entrance fee", "cheap price range", "price range", "Indian", "price range", "british food", "The oak bistro", "Indian food", "price ranges"
- size 17 (12 non-gold): "postcode", "postcode", "postcode", "postcode", "postcode", "Thanh binh", "thanh binh", "Both", "postcode", "4 - 6 Rose Crescent", "Anatolia", "Thanh Binh", "Italian", "anatolia", "Anatolia"


