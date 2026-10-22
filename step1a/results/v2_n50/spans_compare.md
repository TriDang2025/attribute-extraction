# GLiNER vs spaCy spans (50 dialogues)

Gold: 378 verbatim values, 591 verbatim mentions (non-verbatim ones are left out of recall). A span matches a mention when their char spans overlap. spaCy = ner + noun chunks + numbers, overlaps resolved longest-first; GLiNER from cache 25_100_m45. Run 0.7 min.

## P1/P2 Span finding

| Extractor | Spans/dlg | Span precision | Mention recall | Tight mention recall | Value recall | L1 vis / hid | L2 vis / hid | L3 vis / hid |
|---|---|---|---|---|---|---|---|---|
| GLiNER 0.3 | 18.3 | 0.473 | 0.731 | 0.602 | 0.786 | 0.71 / 1.00 | 0.75 / 0.67 | 0.79 / 0.61 |
| GLiNER 0.5 | 14.8 | 0.526 | 0.657 | 0.558 | 0.735 | 0.64 / 0.89 | 0.68 / 0.56 | 0.73 / 0.51 |
| spaCy | 41.4 | 0.279 | 0.983 | 0.648 | 0.992 | 0.98 / 1.00 | 0.99 / 0.96 | 0.99 / 0.97 |
| union(GLiNER 0.5, spaCy) | 41.2 | 0.278 | 0.985 | 0.645 | 0.992 | 0.98 / 1.00 | 0.99 / 0.96 | 0.99 / 0.97 |
| spaCy raw ner | 16.4 | 0.495 | 0.697 | 0.609 | 0.725 | 0.68 / 0.92 | 0.72 / 0.60 | 0.77 / 0.54 |
| spaCy raw np | 36.5 | 0.276 | 0.843 | 0.541 | 0.849 | 0.88 / 0.29 | 0.88 / 0.71 | 0.88 / 0.76 |
| spaCy raw num | 1.5 | 0.137 | 0.017 | 0.017 | 0.024 | 0.02 / 0.03 | 0.00 / 0.06 | 0.01 / 0.04 |

Value recall by class (n = verbatim values):

| Class | n | GLiNER 0.3 | GLiNER 0.5 | spaCy | union(GLiNER 0.5, spaCy) |
|---|---|---|---|---|---|
| Train destination | 27 | 1.00 | 1.00 | 1.00 | 1.00 |
| Train departure | 26 | 1.00 | 1.00 | 1.00 | 1.00 |
| Train day | 26 | 1.00 | 1.00 | 1.00 | 1.00 |
| Restaurant name | 21 | 1.00 | 0.90 | 1.00 | 1.00 |
| Restaurant area | 19 | 0.53 | 0.37 | 1.00 | 1.00 |
| Train confirmed reference | 17 | 1.00 | 0.94 | 1.00 | 1.00 |
| Train leave at | 16 | 1.00 | 0.94 | 1.00 | 1.00 |
| Hotel name | 16 | 1.00 | 1.00 | 1.00 | 1.00 |
| Hotel requested stay | 16 | 1.00 | 1.00 | 1.00 | 1.00 |
| Restaurant food | 16 | 0.06 | 0.06 | 1.00 | 1.00 |
| Restaurant price range | 14 | 0.57 | 0.50 | 0.93 | 0.93 |
| Train requested people | 14 | 0.29 | 0.21 | 1.00 | 1.00 |
| Hotel confirmed reference | 14 | 1.00 | 1.00 | 1.00 | 1.00 |
| Restaurant requested time | 13 | 1.00 | 1.00 | 1.00 | 1.00 |
| Restaurant confirmed reference | 13 | 1.00 | 1.00 | 1.00 | 1.00 |
| Hotel requested people | 12 | 0.58 | 0.42 | 1.00 | 1.00 |
| Hotel requested day | 12 | 1.00 | 1.00 | 1.00 | 1.00 |
| Train arrive by | 10 | 1.00 | 1.00 | 1.00 | 1.00 |
| Attraction area | 10 | 0.20 | 0.20 | 1.00 | 1.00 |
| Restaurant requested people | 10 | 0.30 | 0.30 | 1.00 | 1.00 |
| Attraction type | 8 | 0.25 | 0.25 | 1.00 | 1.00 |
| Attraction name | 8 | 1.00 | 0.88 | 1.00 | 1.00 |
| Restaurant requested day | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| Hotel type | 8 | 0.25 | 0.00 | 1.00 | 1.00 |
| Hotel stars | 8 | 0.62 | 0.50 | 1.00 | 1.00 |
| Hotel area | 7 | 0.57 | 0.29 | 1.00 | 1.00 |
| Hotel price range | 6 | 0.50 | 0.33 | 0.67 | 0.67 |
| Taxi departure | 3 | 1.00 | 0.67 | 1.00 | 1.00 |
| Taxi leave at | 2 | 1.00 | 1.00 | 1.00 | 1.00 |
| Taxi destination | 2 | 1.00 | 1.00 | 1.00 | 1.00 |
| Taxi arrive by | 1 | 1.00 | 1.00 | 1.00 | 1.00 |

Worst 10 dialogues by mention recall:

- GLiNER 0.3: MUL2408 0.17 (n=6), SNG01922 0.25 (n=4), WOZ20405 0.33 (n=3), WOZ20584 0.33 (n=6), MUL1335 0.50 (n=20), PMUL0598 0.54 (n=13), PMUL0890 0.57 (n=14), SNG01551 0.58 (n=12), PMUL2050 0.60 (n=15), PMUL2628 0.62 (n=8)
- GLiNER 0.5: WOZ20405 0.00 (n=3), MUL2408 0.00 (n=6), SNG01922 0.25 (n=4), WOZ20584 0.33 (n=6), WOZ20631 0.43 (n=7), PMUL3589 0.44 (n=27), PMUL0598 0.46 (n=13), PMUL2050 0.47 (n=15), PMUL4578 0.50 (n=10), SNG01551 0.50 (n=12)
- spaCy: MUL2408 0.83 (n=6), WOZ20631 0.86 (n=7), PMUL4733 0.89 (n=9), PMUL3589 0.93 (n=27), PMUL0890 0.93 (n=14), SNG0840 0.94 (n=16), MUL1440 0.94 (n=17), PMUL0468 0.94 (n=18), MUL1335 0.95 (n=20), PMUL1270 1.00 (n=10)
- union(GLiNER 0.5, spaCy): MUL2408 0.83 (n=6), WOZ20631 0.86 (n=7), PMUL4733 0.89 (n=9), PMUL3589 0.93 (n=27), PMUL0890 0.93 (n=14), SNG0840 0.94 (n=16), PMUL0468 0.94 (n=18), MUL1335 0.95 (n=20), PMUL1270 1.00 (n=10), WOZ20405 1.00 (n=3)

## P3 Values GLiNER 0.5 missed

100 of 378 values missed by GLiNER 0.5; share now covered by spaCy overall, by raw spaCy source, and by the union:

| Group | Missed (of n) | spaCy | ner | np | num | union |
|---|---|---|---|---|---|---|
| all classes | 100 (of 378) | 0.97 | 0.52 | 0.91 | 0.04 | 0.97 |
| food | 15 (of 16) | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 |
| type | 14 (of 16) | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 |
| area | 25 (of 36) | 1.00 | 0.16 | 1.00 | 0.00 | 1.00 |
| price range | 11 (of 20) | 0.73 | 0.00 | 0.73 | 0.00 | 0.73 |
| numbers (people/stay/stars) | 29 (of 55) | 1.00 | 0.93 | 0.83 | 0.14 | 1.00 |

By class:

| Class | Missed (of n) | spaCy | ner | np | num | union |
|---|---|---|---|---|---|---|
| Train destination | 0 (of 27) | - | - | - | - | - |
| Train departure | 0 (of 26) | - | - | - | - | - |
| Train day | 0 (of 26) | - | - | - | - | - |
| Restaurant name | 2 (of 21) | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 |
| Restaurant area | 12 (of 19) | 1.00 | 0.25 | 1.00 | 0.00 | 1.00 |
| Train confirmed reference | 1 (of 17) | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 |
| Train leave at | 1 (of 16) | 1.00 | 1.00 | 0.00 | 0.00 | 1.00 |
| Hotel name | 0 (of 16) | - | - | - | - | - |
| Hotel requested stay | 0 (of 16) | - | - | - | - | - |
| Restaurant food | 15 (of 16) | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 |
| Restaurant price range | 7 (of 14) | 0.86 | 0.00 | 0.86 | 0.00 | 0.86 |
| Train requested people | 11 (of 14) | 1.00 | 0.91 | 0.91 | 0.09 | 1.00 |
| Hotel confirmed reference | 0 (of 14) | - | - | - | - | - |
| Restaurant requested time | 0 (of 13) | - | - | - | - | - |
| Restaurant confirmed reference | 0 (of 13) | - | - | - | - | - |
| Hotel requested people | 7 (of 12) | 1.00 | 1.00 | 0.86 | 0.00 | 1.00 |
| Hotel requested day | 0 (of 12) | - | - | - | - | - |
| Train arrive by | 0 (of 10) | - | - | - | - | - |
| Attraction area | 8 (of 10) | 1.00 | 0.12 | 1.00 | 0.00 | 1.00 |
| Restaurant requested people | 7 (of 10) | 1.00 | 1.00 | 0.57 | 0.00 | 1.00 |
| Attraction type | 6 (of 8) | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 |
| Attraction name | 1 (of 8) | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 |
| Restaurant requested day | 0 (of 8) | - | - | - | - | - |
| Hotel type | 8 (of 8) | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 |
| Hotel stars | 4 (of 8) | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 |
| Hotel area | 5 (of 7) | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 |
| Hotel price range | 4 (of 6) | 0.50 | 0.00 | 0.50 | 0.00 | 0.50 |
| Taxi departure | 1 (of 3) | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 |
| Taxi leave at | 0 (of 2) | - | - | - | - | - |
| Taxi destination | 0 (of 2) | - | - | - | - | - |
| Taxi arrive by | 0 (of 1) | - | - | - | - | - |

## P4 Two-stage clustering on each extractor's spans

Segments 25/100 + merge 0.45; stage 1 k-means k=5 (3 seeds); stage 2 agglomerative t=0.4 on bge-m3 of span text. All spans are clustered, matched spans are scored (B-cubed vs class). End-to-end = value recall x attribute F1.

| Extractor | Attr P | Attr R | Attr F1 | K | Non-gold clusters % | Value recall | End-to-end |
|---|---|---|---|---|---|---|---|
| GLiNER 0.3 | 0.758 | 0.462 | 0.574 | 224 | 44 | 0.786 | 0.451 |
| GLiNER 0.5 | 0.772 | 0.493 | 0.602 | 201 | 43 | 0.735 | 0.443 |
| spaCy | 0.726 | 0.401 | 0.516 | 284 | 51 | 0.992 | 0.512 |
| union(GLiNER 0.5, spaCy) | 0.731 | 0.417 | 0.531 | 285 | 52 | 0.992 | 0.526 |

metrics.report_block per extractor:

### GLiNER 0.3

434 labelled of 917 units, K = 230.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 434 | 0.794 | 0.464 | 0.586 |
| visible_L1 | 396 | 0.812 | 0.436 | 0.567 |
| hidden_L1 | 38 | 0.612 | 0.754 | 0.676 |
| visible_L2 | 348 | 0.805 | 0.456 | 0.582 |
| hidden_L2 | 86 | 0.750 | 0.496 | 0.597 |
| visible_L3 | 314 | 0.826 | 0.446 | 0.579 |
| hidden_L3 | 120 | 0.712 | 0.511 | 0.595 |

Per-class recall: Attraction area 0.24 (3); Attraction name 0.12 (13); Attraction type 0.68 (5); Hotel area 0.38 (8); Hotel confirmed reference 0.09 (16); Hotel name 0.10 (24); Hotel price range 0.55 (7); Hotel requested day 1.00 (18); Hotel requested people 0.43 (12); Hotel requested stay 0.64 (21); Hotel stars 0.56 (9); Hotel type 1.00 (2); Restaurant area 0.35 (14); Restaurant confirmed reference 0.08 (13); Restaurant food 1.00 (1); Restaurant name 0.07 (33); Restaurant price range 0.80 (9); Restaurant requested day 0.77 (16); Restaurant requested people 0.50 (6); Restaurant requested time 0.59 (16); Taxi arrive by 0.56 (3); Taxi departure 0.33 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 1.00 (11); Train confirmed reference 0.06 (18); Train day 1.00 (40); Train departure 0.23 (42); Train destination 0.31 (42); Train leave at 1.00 (23); Train requested people 0.17 (6)

Most confused (gold -> cluster majority): Train departure -> Train destination 24; Train arrive by -> Train leave at 11; Train destination -> Train departure 7; Taxi arrive by -> Restaurant requested time 2; Hotel type -> Hotel name 2; Attraction area -> Restaurant area 2; Attraction name -> Train destination 2; Hotel stars -> Hotel requested stay 2; Taxi leave at -> Restaurant requested time 1; Restaurant name -> Restaurant food 1

Largest mostly non-gold clusters:

- size 97 (61 non-gold): "20:30", "06:08", "20:08", "20:45", "5:54", "05:54", "06:43", "21:21", "23:21", "21:21", "20:45", "11:30", "10:54", "13:15", "13:40"
- size 25 (25 non-gold): "TR7213", "TR1110", "TR9016", "TR6387", "TR9016", "TR6387", "TR9016", "TR9016", "TR6193", "TR1719", "TR7610", "TR7610", "TR4669", "TR8167", "TR9693"
- size 24 (16 non-gold): "expensive", "expensive", "expensive", "expensive", "cheap", "cheap price range", "expensive", "expensive price range", "expensive", "moderate price range", "Moderate price range", "expensive price range", "expensive", "moderately priced", "expensive price range"
- size 20 (20 non-gold): "01223 249955", "01223314960", "07083984796", "01223367660", "01223367660", "01223 244277", "01223412299", "01223311911", "07633256482", "01223315232", "01223359506", "01223464550", "01223354755", "01223446100", "01223362372"
- size 18 (10 non-gold): "centre", "centre", "center", "City Centre", "City Centre", "city centre", "centre of town", "centre of town", "centre of town", "centre area", "City Centre", "10 Homerton Street City Centre", "city centre", "City Centre", "Centre area"
- size 18 (12 non-gold): "cheaper price range", "moderate price range", "cheap price range", "cheap", "cheap", "reasonable price", "moderate price range", "moderate price range", "moderate price range", "moderate price", "inexpensive", "moderately priced", "expensive price range", "moderately-priced", "moderately priced"
- size 13 (12 non-gold): "10.10 pounds", "12.80 pounds", "8.08 pounds", "8.08GBP", "66 GBP", "10.10 pounds", "40.4 GBP", "7.84 GBP", "66 GBP", "14.08 pounds", "10.56 GBP", "49.5 GBP", "10.10 pounds"
- size 10 (9 non-gold): "entrance fee", "2 pound fee", "2.50 pound fee", "1 pound fee", "entrance fee", "entrance fee", "entrance fee", "entrance fee", "entrance fee", "entrance fee"
- size 10 (7 non-gold): "city stop restaurant", "Peking Restaurant", "Restaurant Two", "Peking Restaurant", "restaurants", "British restaurant", "Chinese restaurant", "british food", "restaurant", "restaurant alimentum"
- size 10 (10 non-gold): "station", "station", "station", "station", "station", "station", "local restaurant", "restaurant", "station", "station"


### GLiNER 0.5

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


### spaCy

578 labelled of 2069 units, K = 293.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 578 | 0.764 | 0.404 | 0.528 |
| visible_L1 | 540 | 0.775 | 0.381 | 0.511 |
| hidden_L1 | 38 | 0.608 | 0.719 | 0.659 |
| visible_L2 | 455 | 0.760 | 0.388 | 0.514 |
| hidden_L2 | 123 | 0.780 | 0.462 | 0.580 |
| visible_L3 | 391 | 0.787 | 0.386 | 0.518 |
| hidden_L3 | 187 | 0.717 | 0.440 | 0.546 |

Per-class recall: Attraction area 0.37 (13); Attraction name 0.12 (13); Attraction type 0.18 (16); Hotel area 0.48 (15); Hotel confirmed reference 0.09 (16); Hotel name 0.08 (30); Hotel price range 0.82 (8); Hotel requested day 0.91 (18); Hotel requested people 0.44 (20); Hotel requested stay 0.40 (27); Hotel stars 0.45 (21); Hotel type 0.72 (13); Restaurant area 0.37 (36); Restaurant confirmed reference 0.07 (14); Restaurant food 0.52 (25); Restaurant name 0.07 (33); Restaurant price range 0.41 (18); Restaurant requested day 0.40 (16); Restaurant requested people 0.31 (15); Restaurant requested time 0.53 (16); Taxi arrive by 0.33 (3); Taxi departure 0.22 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 0.70 (11); Train confirmed reference 0.08 (18); Train day 1.00 (40); Train departure 0.20 (46); Train destination 0.31 (42); Train leave at 1.00 (23); Train requested people 0.21 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 23; Attraction area -> Restaurant area 11; Hotel type -> Hotel stars 10; Train destination -> Train departure 10; Train arrive by -> Train leave at 9; Restaurant price range -> Restaurant food 8; Hotel name -> Hotel stars 4; Restaurant requested day -> Restaurant requested time 3; Attraction name -> Train departure 2; Hotel stars -> Hotel requested stay 2

Largest mostly non-gold clusters:

- size 94 (66 non-gold): "expensive restaurant", "food type", "food type", "that restaurant", "indian food", "restaurant", "food", "city stop restaurant", "restaurant", "african food", "one African restuarant", "expensive restaurant", "restaurant", "international food", "food"
- size 92 (92 non-gold): "their address", "address", "postcode", "Their postcode", "address", "phone number", "postcode", "It's address", "their postcode", "their phone number", "Their phone number", "postcode", "postcode", "contact number", "Their phone number"
- size 91 (90 non-gold): "train", "that train", "train", "train", "10 trains", "train", "two trains", "train ID", "train ID", "trainID", "earlier train", "train", "train", "19 trains", "airport"
- size 91 (56 non-gold): "20:30", "06:08", "20:08", "20:45", "5:54", "05:54", "06:43", "21:21", "23:21", "21:21", "20:45", "11:30", "10:54", "13:15", "13:40"
- size 69 (65 non-gold): "town", "town", "venue", "town", "town", "Which area", "town", "museum", "place", "town", "town", "place", "town", "place", "that area"
- size 64 (35 non-gold): "guesthouse", "guesthouse", "hotel", "hotel", "one cheap and one expensive hotel", "guesthouse", "hotel", "two guesthouses", "4 star", "How about the Ashley Hotel", "star rating", "ashley hotel", "2 stars", "hotel", "hotel"
- size 48 (48 non-gold): "duration", "your specified time", "today", "a great day", "that day", "every hour", "what day", "today", "today", "wonderful day", "day", "time", "today", "a wonderful day", "what day"
- size 36 (29 non-gold): "today", "Good day", "monday", "Monday", "special occasion", "today", "nice day", "today", "Sunday", "Thursday", "a different day", "time", "Thursday", "a different day", "your time"
- size 31 (23 non-gold): "ticket", "how many tickets", "ticket", "that ticket", "your ticket", "how many seats", "each ticket", "how many tickets", "seats", "4 seats", "seats", "7 tickets", "ticket", "4 tickets", "seats"
- size 31 (31 non-gold): "your needs", "your current criteria", "your criteria", "different criteria", "information", "information", "problem", "your stay", "those criteria", "your needs", "your search", "your requirements", "fact", "your criteria", "confusion"


### union(GLiNER 0.5, spaCy)

572 labelled of 2060 units, K = 291.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 572 | 0.767 | 0.418 | 0.541 |
| visible_L1 | 534 | 0.778 | 0.396 | 0.525 |
| hidden_L1 | 38 | 0.609 | 0.719 | 0.660 |
| visible_L2 | 449 | 0.769 | 0.406 | 0.532 |
| hidden_L2 | 123 | 0.760 | 0.460 | 0.573 |
| visible_L3 | 385 | 0.797 | 0.407 | 0.539 |
| hidden_L3 | 187 | 0.704 | 0.439 | 0.541 |

Per-class recall: Attraction area 0.37 (13); Attraction name 0.12 (13); Attraction type 0.18 (16); Hotel area 0.48 (15); Hotel confirmed reference 0.09 (16); Hotel name 0.09 (26); Hotel price range 0.82 (8); Hotel requested day 0.91 (18); Hotel requested people 0.44 (20); Hotel requested stay 0.40 (27); Hotel stars 0.45 (21); Hotel type 0.72 (13); Restaurant area 0.37 (36); Restaurant confirmed reference 0.08 (13); Restaurant food 0.48 (25); Restaurant name 0.07 (34); Restaurant price range 0.77 (18); Restaurant requested day 0.40 (16); Restaurant requested people 0.31 (15); Restaurant requested time 0.53 (16); Taxi arrive by 0.33 (3); Taxi departure 0.22 (6); Taxi destination 0.25 (4); Taxi leave at 0.50 (2); Train arrive by 0.70 (11); Train confirmed reference 0.08 (18); Train day 1.00 (40); Train departure 0.21 (44); Train destination 0.31 (42); Train leave at 1.00 (23); Train requested people 0.20 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 23; Attraction area -> Restaurant area 11; Hotel type -> Hotel stars 10; Train destination -> Train departure 10; Train arrive by -> Train leave at 9; Hotel name -> Hotel stars 4; Restaurant requested day -> Restaurant requested time 3; Restaurant name -> Restaurant food 2; Hotel area -> Train requested people 2; Attraction name -> Train departure 2

Largest mostly non-gold clusters:

- size 92 (92 non-gold): "their address", "address", "postcode", "Their postcode", "address", "phone number", "postcode", "It's address", "their postcode", "their phone number", "Their phone number", "postcode", "postcode", "contact number", "Their phone number"
- size 91 (56 non-gold): "20:30", "06:08", "20:08", "20:45", "5:54", "05:54", "06:43", "21:21", "23:21", "21:21", "20:45", "11:30", "10:54", "13:15", "13:40"
- size 90 (89 non-gold): "train", "that train", "train", "train", "10 trains", "train", "two trains", "train ID", "train ID", "trainID", "earlier train", "train", "train", "19 trains", "airport"
- size 83 (63 non-gold): "food type", "food type", "that restaurant", "indian food", "restaurant", "food", "city stop restaurant", "restaurant", "african food", "one African restuarant", "restaurant", "international food", "food", "How about Chinese food", "the Peking Restaurant"
- size 64 (35 non-gold): "guesthouse", "guesthouse", "hotel", "hotel", "one cheap and one expensive hotel", "guesthouse", "hotel", "two guesthouses", "4 star", "How about the Ashley Hotel", "star rating", "ashley hotel", "2 stars", "hotel", "hotel"
- size 62 (58 non-gold): "town", "town", "venue", "town", "town", "Which area", "town", "museum", "place", "place", "town", "place", "that area", "museums", "town"
- size 48 (48 non-gold): "duration", "your specified time", "today", "a great day", "that day", "every hour", "what day", "today", "today", "wonderful day", "day", "time", "today", "a wonderful day", "what day"
- size 36 (29 non-gold): "today", "Good day", "monday", "Monday", "special occasion", "today", "nice day", "today", "Sunday", "Thursday", "a different day", "time", "Thursday", "a different day", "your time"
- size 31 (23 non-gold): "ticket", "how many tickets", "ticket", "that ticket", "your ticket", "how many seats", "each ticket", "how many tickets", "seats", "4 seats", "seats", "7 tickets", "ticket", "4 tickets", "seats"
- size 31 (31 non-gold): "your needs", "your current criteria", "your criteria", "different criteria", "information", "information", "problem", "your stay", "those criteria", "your needs", "your search", "your requirements", "fact", "your criteria", "confusion"



## P5

FrameNet frame elements as a further span source (typed, schema-free) is later work.
