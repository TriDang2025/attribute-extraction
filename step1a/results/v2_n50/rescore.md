# Step 1a rescoring under the v2 protocol (dev, 50 dialogues)

Two stages (k-means k=5 on segments, then agglomerative cosine/average at t=0.4), mean over 3 k-means seeds. B = GLiNER spans at threshold 0.5 from the entity_seg cache. Run time 1.2 min.

Rows: old = one unit per gold value, spans.match, single-label B-cubed; E1 = match_all (a span takes every overlapping mention's attributes; strict on the joined label); E2 = class merge (Restaurant confirmed name -> Restaurant name; Hotel confirmed name -> Hotel name) + lenient multi-label B-cubed; E3 = span recall on verbatim mentions only; E4 = every verbatim mention is a unit (strict on the joined label); all = E1-E4, lenient. Span recall: old = share of located gold values matched (each once); E3/all = mention / value level.

Old-protocol check against results/n50/entity_seg.md: 50/400 A 0.470 vs 0.470 ok; 50/400 B 0.530 vs 0.530 ok; 25/100 +merge 0.45 A 0.549 vs 0.549 ok; 25/100 +merge 0.45 B 0.583 vs 0.583 ok.

| Config | Row | Units | Units/dlg | Scored | K | P | R | F1 | Span recall | F1 vis/hid L1 | F1 vis/hid L2 | F1 vis/hid L3 | Ambig % | >1 label % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 50/400 | old | A | 8.9 | 444 | 134 | 0.614 | 0.381 | **0.470** |  | 0.448 / 0.636 | 0.442 / 0.558 | 0.430 / 0.543 |  |  |
| 50/400 | E2 | A | 8.9 | 444 | 134 | 0.656 | 0.379 | **0.481** |  | 0.458 / 0.636 | 0.454 / 0.558 | 0.442 / 0.543 |  |  |
| 50/400 | E4 | A | 11.8 | 591 | 137 | 0.646 | 0.428 | **0.515** |  | 0.498 / 0.691 | 0.490 / 0.582 | 0.481 / 0.566 | 3.4 | 6.8 |
| 50/400 | all | A | 11.8 | 591 | 137 | 0.672 | 0.409 | **0.508** |  | 0.490 / 0.691 | 0.478 / 0.593 | 0.468 / 0.570 | 3.4 | 2.0 |
| 50/400 | old | B | 15.0 | 260 | 203 | 0.715 | 0.421 | **0.530** | 0.59 | 0.501 / 0.657 | 0.512 / 0.600 | 0.496 / 0.608 |  | 0.0 |
| 50/400 | E1 | B | 15.0 | 398 | 203 | 0.701 | 0.458 | **0.554** |  | 0.534 / 0.684 | 0.538 / 0.621 | 0.526 / 0.622 | 3.3 | 8.0 |
| 50/400 | E2 | B | 15.0 | 260 | 203 | 0.715 | 0.413 | **0.524** |  | 0.494 / 0.657 | 0.504 / 0.600 | 0.487 / 0.608 |  | 0.0 |
| 50/400 | E3 | B | 15.0 | 260 | 203 | 0.715 | 0.421 | **0.530** | 0.67 / 0.73 | 0.501 / 0.657 | 0.512 / 0.600 | 0.496 / 0.608 |  | 0.0 |
| 50/400 | all | B | 15.0 | 398 | 203 | 0.734 | 0.433 | **0.545** | 0.67 / 0.73 | 0.521 / 0.684 | 0.523 / 0.629 | 0.513 / 0.621 | 3.3 | 1.8 |
| 25/100 +merge 0.45 | old | A | 8.9 | 444 | 120 | 0.641 | 0.480 | **0.549** |  | 0.540 / 0.596 | 0.536 / 0.591 | 0.533 / 0.576 |  |  |
| 25/100 +merge 0.45 | E2 | A | 8.9 | 444 | 120 | 0.685 | 0.479 | **0.563** |  | 0.554 / 0.596 | 0.553 / 0.591 | 0.551 / 0.576 |  |  |
| 25/100 +merge 0.45 | E4 | A | 11.8 | 591 | 127 | 0.680 | 0.509 | **0.582** |  | 0.573 / 0.674 | 0.566 / 0.631 | 0.573 / 0.595 | 3.4 | 6.8 |
| 25/100 +merge 0.45 | all | A | 11.8 | 591 | 127 | 0.710 | 0.498 | **0.585** |  | 0.575 / 0.674 | 0.565 / 0.644 | 0.572 / 0.602 | 3.4 | 2.0 |
| 25/100 +merge 0.45 | old | B | 14.8 | 261 | 201 | 0.762 | 0.473 | **0.583** | 0.59 | 0.567 / 0.649 | 0.581 / 0.591 | 0.573 / 0.604 |  | 0.0 |
| 25/100 +merge 0.45 | E1 | B | 14.8 | 389 | 201 | 0.735 | 0.509 | **0.602** |  | 0.586 / 0.700 | 0.591 / 0.641 | 0.590 / 0.628 | 2.1 | 7.7 |
| 25/100 +merge 0.45 | E2 | B | 14.8 | 261 | 201 | 0.762 | 0.465 | **0.577** |  | 0.559 / 0.649 | 0.574 / 0.591 | 0.564 / 0.604 |  | 0.0 |
| 25/100 +merge 0.45 | E3 | B | 14.8 | 261 | 201 | 0.762 | 0.473 | **0.583** | 0.66 / 0.72 | 0.567 / 0.649 | 0.581 / 0.591 | 0.573 / 0.604 |  | 0.0 |
| 25/100 +merge 0.45 | all | B | 14.8 | 389 | 201 | 0.772 | 0.493 | **0.602** | 0.66 / 0.72 | 0.584 / 0.700 | 0.588 / 0.654 | 0.585 / 0.637 | 2.1 | 1.5 |

Span recall (value level) on visible / hidden attributes, all rows: 50/400: L1 0.71 / 0.97, L2 0.75 / 0.64, L3 0.80 / 0.58; 25/100 +merge 0.45: L1 0.71 / 0.93, L2 0.74 / 0.65, L3 0.79 / 0.58

## Gold mentions

591 verbatim mentions (11.8 per dialogue, 3.4% ambiguous), 26 non-verbatim values. Non-verbatim by attribute: Hotel internet 7, Hotel parking 5, Restaurant price range 4, Hotel name 2, Hotel area 1, Taxi departure 1, Train confirmed reference 1, Hotel price range 1, Train requested people 1, Restaurant name 1, Hotel confirmed name 1, Restaurant confirmed name 1, Train leave at 1, Hotel requested people 1, Hotel type 1.

## Report blocks (all rows, k-means seed 42)

### 50/400, A

591 labelled of 591 units, K = 134.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.703 | 0.440 | 0.541 |
| visible_L1 | 553 | 0.710 | 0.417 | 0.525 |
| hidden_L1 | 38 | 0.615 | 0.772 | 0.684 |
| visible_L2 | 462 | 0.702 | 0.390 | 0.502 |
| hidden_L2 | 129 | 0.710 | 0.616 | 0.660 |
| visible_L3 | 397 | 0.721 | 0.369 | 0.488 |
| hidden_L3 | 194 | 0.667 | 0.585 | 0.623 |

Per-class recall: Attraction area 0.39 (13); Attraction name 0.14 (12); Attraction type 0.42 (16); Hotel area 0.66 (15); Hotel confirmed reference 0.09 (16); Hotel name 0.15 (25); Hotel price range 0.50 (13); Hotel requested day 0.45 (18); Hotel requested people 0.43 (20); Hotel requested stay 0.46 (27); Hotel stars 0.88 (21); Hotel type 0.73 (13); Restaurant area 0.34 (36); Restaurant confirmed reference 0.09 (13); Restaurant food 0.28 (25); Restaurant name 0.06 (35); Restaurant price range 0.39 (21); Restaurant requested day 0.77 (16); Restaurant requested people 0.50 (15); Restaurant requested time 0.60 (16); Taxi arrive by 1.00 (3); Taxi departure 0.22 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.07 (18); Train day 0.95 (40); Train departure 0.18 (44); Train destination 0.31 (42); Train leave at 1.00 (23); Train requested people 0.58 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 20; Train arrive by -> Train leave at 11; Attraction area -> Restaurant area 11; Train destination -> Train departure 9; Hotel requested people -> Restaurant requested people 8; Hotel requested day -> Restaurant requested day 8; Hotel requested stay -> Hotel stars 7; Hotel name -> Hotel type 7; Hotel requested people|Hotel requested stay -> Hotel stars 6; Attraction type -> Restaurant area 5
Bootstrap 95% CI of F1 (dialogues): 0.517-0.563.

### 50/400, B

398 labelled of 750 units, K = 198.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 398 | 0.753 | 0.443 | 0.558 |
| visible_L1 | 362 | 0.766 | 0.412 | 0.536 |
| hidden_L1 | 36 | 0.616 | 0.759 | 0.680 |
| visible_L2 | 329 | 0.757 | 0.416 | 0.537 |
| hidden_L2 | 69 | 0.732 | 0.575 | 0.644 |
| visible_L3 | 300 | 0.766 | 0.400 | 0.526 |
| hidden_L3 | 98 | 0.711 | 0.576 | 0.636 |

Per-class recall: Attraction area 0.30 (2); Attraction name 0.16 (11); Attraction type 0.68 (5); Hotel area 1.00 (2); Hotel confirmed reference 0.09 (16); Hotel name 0.14 (23); Hotel price range 1.00 (5); Hotel requested day 0.45 (18); Hotel requested people 0.36 (7); Hotel requested stay 0.49 (16); Hotel stars 0.50 (6); Restaurant area 0.41 (19); Restaurant confirmed reference 0.09 (13); Restaurant food 1.00 (1); Restaurant name 0.07 (28); Restaurant price range 1.00 (6); Restaurant requested day 0.77 (16); Restaurant requested people 0.28 (5); Restaurant requested time 0.60 (16); Taxi arrive by 1.00 (3); Taxi departure 0.22 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.07 (18); Train day 0.95 (40); Train departure 0.18 (44); Train destination 0.33 (39); Train leave at 1.00 (21); Train requested people 0.50 (2)

Most confused (gold -> cluster majority): Train departure -> Train destination 20; Train arrive by -> Train leave at 11; Hotel requested day -> Restaurant requested day 8; Train destination -> Train departure 7; Taxi arrive by -> Restaurant requested time 3; Taxi leave at -> Restaurant requested time 2; Taxi destination -> Restaurant name 2; Hotel requested people -> Hotel requested stay 2; Attraction name -> Train departure 2; Hotel stars -> Hotel requested stay 2

Largest mostly non-gold clusters:

- size 88 (54 non-gold): "20:30", "06:08", "20:08", "20:45", "5:54", "05:54", "06:43", "21:21", "23:21", "21:21", "11:30", "10:54", "13:15", "13:40", "23:40"
- size 18 (12 non-gold): "expensive", "expensive", "expensive", "cheap", "price range", "cheap price range", "expensive", "expensive price range", "expensive", "moderate price range", "Moderate price range", "expensive price range", "moderately priced", "expensive price range", "moderately priced"
- size 13 (13 non-gold): "TR7213", "TR9448", "TR9448", "TR9016", "TR9016", "TR9016", "TR9016", "TR6838", "TR6838", "TR7935", "TR5921", "TR5921", "TR5921"
- size 12 (12 non-gold): "01223 249955", "01223367660", "01223367660", "01223 244277", "01223311911", "01223315232", "01223359506", "01223464550", "01223446100", "01223362372", "01223364222", "01223 360966"
- size 10 (10 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "8.08GBP", "64.64 GBP", "10.10 pounds", "7.84 GBP", "14.08 pounds", "10.56 GBP", "10.10 pounds"
- size 9 (9 non-gold): "07083984796", "01223412299", "07032807056", "07633256482", "01223354755", "01223276182", "07629102425", "01223355017", "07242149665"
- size 8 (8 non-gold): "TR1110", "TR1719", "TR7604", "TR1755", "TR4202", "TR0032", "TR1871", "TR0017"
- size 8 (6 non-gold): "Cherry Hinton", "Cherry Hinton", "Cherry Hinton", "Cherry Hinton", "Cherry Hinton Water Play", "Cherry Hinton Hall", "Cherry Hinton Road", "Cherry Hinton Water Play"
- size 7 (6 non-gold): "2 pound fee", "2.50 pound fee", "1 pound fee", "entrance fee", "entrance fee", "entrance fee", "entrance fee"
- size 7 (7 non-gold): "49 minutes", "49 minutes", "28-minute", "105 minute", "105 minutes", "38 minute", "105 minutes"
Bootstrap 95% CI of F1 (dialogues): 0.530-0.583.

### 25/100 +merge 0.45, A

591 labelled of 591 units, K = 131.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.750 | 0.509 | 0.607 |
| visible_L1 | 553 | 0.761 | 0.493 | 0.598 |
| hidden_L1 | 38 | 0.594 | 0.754 | 0.665 |
| visible_L2 | 462 | 0.753 | 0.479 | 0.585 |
| hidden_L2 | 129 | 0.741 | 0.619 | 0.674 |
| visible_L3 | 397 | 0.783 | 0.483 | 0.597 |
| hidden_L3 | 194 | 0.683 | 0.564 | 0.618 |

Per-class recall: Attraction area 0.38 (13); Attraction name 0.14 (12); Attraction type 0.27 (16); Hotel area 0.66 (15); Hotel confirmed reference 0.09 (16); Hotel name 0.16 (25); Hotel price range 0.43 (13); Hotel requested day 1.00 (18); Hotel requested people 0.89 (20); Hotel requested stay 0.80 (27); Hotel stars 0.98 (21); Hotel type 0.86 (13); Restaurant area 0.47 (36); Restaurant confirmed reference 0.08 (13); Restaurant food 0.45 (25); Restaurant name 0.06 (35); Restaurant price range 0.62 (21); Restaurant requested day 0.77 (16); Restaurant requested people 0.65 (15); Restaurant requested time 0.59 (16); Taxi arrive by 0.56 (3); Taxi departure 0.33 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 0.70 (11); Train confirmed reference 0.06 (18); Train day 1.00 (40); Train departure 0.21 (44); Train destination 0.31 (42); Train leave at 1.00 (23); Train requested people 0.58 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 23; Hotel stars -> Hotel requested stay 16; Hotel requested people -> Hotel requested stay 13; Attraction area -> Restaurant area 11; Train destination -> Train departure 10; Train arrive by -> Train leave at 9; Hotel name -> Hotel type 8; Attraction type -> Restaurant area 5; Taxi departure -> Attraction type 3; Hotel requested stay -> Train requested people 2
Bootstrap 95% CI of F1 (dialogues): 0.580-0.632.

### 25/100 +merge 0.45, B

389 labelled of 740 units, K = 206.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 389 | 0.803 | 0.505 | 0.620 |
| visible_L1 | 355 | 0.820 | 0.479 | 0.605 |
| hidden_L1 | 34 | 0.628 | 0.770 | 0.692 |
| visible_L2 | 317 | 0.816 | 0.488 | 0.610 |
| hidden_L2 | 72 | 0.747 | 0.579 | 0.652 |
| visible_L3 | 289 | 0.832 | 0.482 | 0.610 |
| hidden_L3 | 100 | 0.718 | 0.570 | 0.636 |

Per-class recall: Attraction area 0.50 (2); Attraction name 0.14 (12); Attraction type 0.56 (3); Hotel area 0.56 (6); Hotel confirmed reference 0.09 (16); Hotel name 0.16 (23); Hotel price range 0.72 (6); Hotel requested day 1.00 (18); Hotel requested people 0.58 (6); Hotel requested stay 0.80 (19); Hotel stars 0.95 (6); Restaurant area 0.51 (9); Restaurant confirmed reference 0.08 (13); Restaurant food 1.00 (1); Restaurant name 0.07 (27); Restaurant price range 0.78 (8); Restaurant requested day 0.77 (16); Restaurant requested people 1.00 (4); Restaurant requested time 0.59 (16); Taxi arrive by 0.56 (3); Taxi departure 0.38 (4); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.07 (17); Train day 1.00 (40); Train departure 0.22 (41); Train destination 0.34 (38); Train leave at 1.00 (21); Train requested people 0.33 (3)

Most confused (gold -> cluster majority): Train departure -> Train destination 22; Train arrive by -> Train leave at 11; Train destination -> Train departure 7; Hotel stars -> Hotel requested stay 3; Taxi arrive by -> Restaurant requested time 2; Attraction area -> Restaurant area 2; Taxi leave at -> Restaurant requested time 1; Restaurant name -> Restaurant food 1; Taxi arrive by -> Train leave at 1; Hotel requested people -> Restaurant requested people 1

Largest mostly non-gold clusters:

- size 94 (60 non-gold): "20:30", "06:08", "20:08", "5:54", "05:54", "06:43", "21:21", "23:21", "21:21", "20:45", "11:30", "10:54", "13:15", "13:40", "23:40"
- size 20 (20 non-gold): "01223 249955", "01223314960", "07083984796", "01223367660", "01223367660", "01223 244277", "01223412299", "01223311911", "07633256482", "01223315232", "01223359506", "01223464550", "01223354755", "01223446100", "01223362372"
- size 18 (11 non-gold): "expensive", "expensive", "expensive", "cheap price range", "expensive", "expensive price range", "expensive", "moderate price range", "Moderate price range", "expensive price range", "expensive", "moderately priced", "expensive price range", "moderately priced", "moderately priced"
- size 15 (8 non-gold): "centre", "centre", "City Centre", "City Centre", "city centre", "centre of town", "centre of town", "centre of town", "City Centre", "10 Homerton Street City Centre", "city centre", "City Centre", "Centre area", "City Centre", "town center"
- size 12 (12 non-gold): "TR7213", "TR1110", "TR9016", "TR9016", "TR9016", "TR9016", "TR7610", "TR7935", "TR5713", "TR5921", "Train TR5921", "Train TR5921"
- size 12 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "8.08GBP", "66 GBP", "10.10 pounds", "7.84 GBP", "66 GBP", "14.08 pounds", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 9 (7 non-gold): "Cherry Hinton", "Cherry Hinton", "Cherry Hinton", "Pizza Hut Cherry Hinton", "64 Cherry Hinton Road", "Cherry Hinton Water Play", "Cherry Hinton Hall", "Cherry Hinton Road", "Cherry Hinton Water Play"
- size 8 (7 non-gold): "2 pound fee", "2.50 pound fee", "1 pound fee", "entrance fee", "entrance fee", "entrance fee", "entrance fee", "entrance fee"
- size 8 (7 non-gold): "Cambridge", "Cambridge", "Cambridge Belfry", "Cambridge", "Cambridge", "Cambridge", "Cambridge", "Cambridge"
- size 6 (6 non-gold): "49 minutes", "49 minutes", "28-minute", "38 minute", "105 minutes", "105 minutes"
Bootstrap 95% CI of F1 (dialogues): 0.596-0.642.

