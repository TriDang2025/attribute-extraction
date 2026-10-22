# Step 2 with gold entities fixed (dev, 50 dialogues)

591 verbatim gold mentions, 31 classes, 50 dialogues; units from s1a.gold.mentions_for. Groups = gold entity of the mention; booking = (dialogue, gold entity). Run time 4.5 min.

**Tuning uses the same dialogues it reports on** (t, linkage, alpha, theta are picked by F1 on these mentions), so rows after C2 are optimistic.

Lenient multi-label B-cubed (s1a.metrics.report_block); single F1 = old single-label score on the joined label. vL/hL = F1 on mentions of visible / hidden attributes at TEAR level L. Delta = F1 change vs the previous carried row (ceilings vs C0).

| Stage | Config | P | R | F1 | K | Delta F1 | single F1 | vL1 | hL1 | vL2 | hL2 | vL3 | hL3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C0 | raw strings, average, t=0.4 | 0.822 | 0.597 | 0.692 | 120 |  | 0.684 | 0.683 | 0.777 | 0.667 | 0.773 | 0.668 | 0.732 |
| C1 | string ceiling (normalized string -> majority gold class) | 0.890 | 0.884 | 0.887 | 31 | +0.195 | 0.877 | 0.884 | 0.929 | 0.879 | 0.915 | 0.862 | 0.937 |
| C1 | oracle k per entity (normalized string vectors, average) | 0.392 | 0.839 | 0.534 | 32 | -0.158 | 0.522 | 0.532 | 0.562 | 0.533 | 0.535 | 0.535 | 0.530 |
| C2 | normalized, complete, t=0.4 | 0.853 | 0.601 | 0.705 | 108 | +0.014 | 0.698 | 0.698 | 0.777 | 0.683 | 0.775 | 0.666 | 0.776 |
| C3 | alpha=0.5, complete, t=0.4 | 0.609 | 0.729 | 0.664 | 35 | -0.042 | 0.650 | 0.669 | 0.509 | 0.629 | 0.785 | 0.641 | 0.711 |
| C3 retuned | alpha=0.5, complete, t=0.4 | 0.609 | 0.729 | 0.664 | 35 | +0.000 | 0.650 | 0.669 | 0.509 | 0.629 | 0.785 | 0.641 | 0.711 |
| C4 | + partition by type (alpha=0.5, complete, t=0.4) | 0.728 | 0.737 | 0.732 | 39 | +0.069 | 0.721 | 0.730 | 0.756 | 0.701 | 0.839 | 0.722 | 0.750 |
| C5 | + cannot-link (1965 pairs) | 0.799 | 0.663 | 0.725 | 46 | -0.008 | 0.721 | 0.716 | 0.803 | 0.697 | 0.819 | 0.704 | 0.762 |
| C6 | theta=0.6 (13 merges) | 0.739 | 0.711 | 0.725 | 33 | -0.000 | 0.718 | 0.717 | 0.807 | 0.687 | 0.857 | 0.694 | 0.784 |

Chosen: C4 + partition by type (alpha=0.5, complete, t=0.4) (F1 0.732) -> chosen_step2.json (`s1a.step2.run_best`).

## C2 grid (normalized strings): F1 (K)

| linkage | t=0.2 | t=0.25 | t=0.3 | t=0.35 | t=0.4 | t=0.45 | t=0.5 | t=0.55 | t=0.6 |
|---|---|---|---|---|---|---|---|---|---|
| average | 0.538 (170) | 0.632 (157) | 0.669 (140) | 0.685 (122) | 0.704 (102) | 0.685 (83) | 0.612 (53) | 0.526 (29) | 0.337 (14) |
| complete | 0.498 (177) | 0.589 (162) | 0.638 (145) | 0.676 (126) | 0.705 (108) | 0.704 (94) | 0.696 (74) | 0.624 (49) | 0.592 (35) |
| single | 0.575 (167) | 0.657 (152) | 0.685 (129) | 0.680 (106) | 0.593 (73) | 0.432 (42) | 0.324 (16) | 0.287 (6) | 0.285 (5) |

## C3 context weight alpha

| Config | P | R | F1 | K |
|---|---|---|---|---|
| alpha=0.4, complete, t=0.4 | 0.626 | 0.685 | 0.654 | 47 |
| alpha=0.5, complete, t=0.4 | 0.609 | 0.729 | 0.664 | 35 |
| alpha=0.6, complete, t=0.4 | 0.447 | 0.580 | 0.505 | 30 |
| alpha=0.7, complete, t=0.4 | 0.314 | 0.382 | 0.344 | 35 |
| alpha=0.8, complete, t=0.4 | 0.286 | 0.345 | 0.313 | 41 |
| alpha=0.9, complete, t=0.4 | 0.334 | 0.302 | 0.317 | 56 |

## C3 threshold re-tune

| Config | P | R | F1 | K |
|---|---|---|---|---|
| alpha=0.5, complete, t=0.2 | 0.871 | 0.313 | 0.461 | 174 |
| alpha=0.5, complete, t=0.3 | 0.827 | 0.527 | 0.643 | 95 |
| alpha=0.5, complete, t=0.4 | 0.609 | 0.729 | 0.664 | 35 |
| alpha=0.5, complete, t=0.5 | 0.323 | 0.888 | 0.474 | 11 |
| alpha=0.5, complete, t=0.6 | 0.166 | 0.997 | 0.285 | 5 |

## C6 merge threshold theta

| Config | P | R | F1 | K |
|---|---|---|---|---|
| theta=0.6 (13 merges) | 0.739 | 0.711 | 0.725 | 33 |
| theta=0.7 (13 merges) | 0.739 | 0.711 | 0.725 | 33 |
| theta=0.8 (10 merges) | 0.744 | 0.703 | 0.722 | 36 |
| theta=0.9 (4 merges) | 0.767 | 0.679 | 0.720 | 42 |

## C4 typer

Type accuracy vs gold slot type: 1.000 (591 mentions). Expected: day -> day; leave at / arrive by / time -> time; people / stay / stars -> number; reference -> id; else text.

| expected | predicted | n | examples |
|---|---|---|---|

C5 uses 1965 cannot-link pairs (same dialogue and entity, different normalized string).

## Report blocks

### C0 raw strings, average, t=0.4

591 labelled of 591 units, K = 120.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.822 | 0.597 | 0.692 |
| visible_L1 | 553 | 0.828 | 0.582 | 0.683 |
| hidden_L1 | 38 | 0.741 | 0.816 | 0.777 |
| visible_L2 | 462 | 0.821 | 0.561 | 0.667 |
| hidden_L2 | 129 | 0.829 | 0.724 | 0.773 |
| visible_L3 | 397 | 0.839 | 0.554 | 0.668 |
| hidden_L3 | 194 | 0.789 | 0.683 | 0.732 |

Per-class recall: Attraction area 0.49 (13); Attraction name 0.17 (12); Attraction type 0.42 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.10 (16); Hotel name 0.19 (25); Hotel price range 0.50 (13); Hotel requested day 1.00 (18); Hotel requested people 0.99 (20); Hotel requested stay 0.93 (27); Hotel stars 0.99 (21); Hotel type 1.00 (13); Restaurant area 0.48 (36); Restaurant confirmed reference 0.09 (13); Restaurant food 0.45 (25); Restaurant name 0.07 (35); Restaurant price range 0.64 (21); Restaurant requested day 1.00 (16); Restaurant requested people 1.00 (15); Restaurant requested time 1.00 (16); Taxi arrive by 1.00 (3); Taxi departure 0.33 (6); Taxi destination 0.25 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 0.07 (18); Train day 1.00 (40); Train departure 0.27 (44); Train destination 0.41 (42); Train leave at 1.00 (23); Train requested people 0.92 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 26; Hotel stars -> Hotel requested stay 16; Hotel requested people -> Hotel requested stay 14; Train arrive by -> Train leave at 11; Hotel name -> Hotel type 9; Train destination -> Train departure 7; Attraction type -> Attraction area 5; Taxi leave at -> Taxi arrive by 2; Hotel area -> Hotel name 2; Restaurant name -> Restaurant food 1

### C2 normalized, complete, t=0.4

591 labelled of 591 units, K = 108.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.853 | 0.601 | 0.705 |
| visible_L1 | 553 | 0.860 | 0.587 | 0.698 |
| hidden_L1 | 38 | 0.741 | 0.816 | 0.777 |
| visible_L2 | 462 | 0.859 | 0.566 | 0.683 |
| hidden_L2 | 129 | 0.828 | 0.728 | 0.775 |
| visible_L3 | 397 | 0.855 | 0.546 | 0.666 |
| hidden_L3 | 194 | 0.847 | 0.715 | 0.776 |

Per-class recall: Attraction area 0.49 (13); Attraction name 0.17 (12); Attraction type 0.77 (16); Hotel area 0.77 (15); Hotel confirmed reference 0.16 (16); Hotel name 0.19 (25); Hotel price range 0.50 (13); Hotel requested day 1.00 (18); Hotel requested people 0.91 (20); Hotel requested stay 0.92 (27); Hotel stars 0.91 (21); Hotel type 1.00 (13); Restaurant area 0.48 (36); Restaurant confirmed reference 0.14 (13); Restaurant food 0.31 (25); Restaurant name 0.08 (35); Restaurant price range 0.64 (21); Restaurant requested day 1.00 (16); Restaurant requested people 1.00 (15); Restaurant requested time 1.00 (16); Taxi arrive by 1.00 (3); Taxi departure 0.33 (6); Taxi destination 0.25 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 0.10 (18); Train day 1.00 (40); Train departure 0.27 (44); Train destination 0.41 (42); Train leave at 1.00 (23); Train requested people 1.00 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 26; Hotel stars -> Hotel requested stay 16; Hotel requested people -> Hotel requested stay 14; Train arrive by -> Train leave at 11; Train destination -> Train departure 7; Taxi leave at -> Taxi arrive by 2; Hotel area -> Hotel name 2

### chosen C4 + partition by type (alpha=0.5, complete, t=0.4)

591 labelled of 591 units, K = 39.

| Subset | n | P | R | F1 |
|---|---|---|---|---|
| all | 591 | 0.728 | 0.737 | 0.732 |
| visible_L1 | 553 | 0.732 | 0.727 | 0.730 |
| hidden_L1 | 38 | 0.662 | 0.882 | 0.756 |
| visible_L2 | 462 | 0.711 | 0.692 | 0.701 |
| hidden_L2 | 129 | 0.788 | 0.896 | 0.839 |
| visible_L3 | 397 | 0.735 | 0.710 | 0.722 |
| hidden_L3 | 194 | 0.712 | 0.793 | 0.750 |

Per-class recall: Attraction area 0.81 (13); Attraction name 0.22 (12); Attraction type 0.47 (16); Hotel area 1.00 (15); Hotel confirmed reference 1.00 (16); Hotel name 0.38 (25); Hotel price range 1.00 (13); Hotel requested day 1.00 (18); Hotel requested people 1.00 (20); Hotel requested stay 1.00 (27); Hotel stars 1.00 (21); Hotel type 0.50 (13); Restaurant area 0.95 (36); Restaurant confirmed reference 1.00 (13); Restaurant food 0.64 (25); Restaurant name 0.12 (35); Restaurant price range 0.64 (21); Restaurant requested day 1.00 (16); Restaurant requested people 1.00 (15); Restaurant requested time 1.00 (16); Taxi arrive by 1.00 (3); Taxi departure 0.50 (6); Taxi destination 0.62 (4); Taxi leave at 1.00 (2); Train arrive by 1.00 (11); Train confirmed reference 0.51 (18); Train day 1.00 (40); Train departure 0.35 (44); Train destination 0.46 (42); Train leave at 1.00 (23); Train requested people 1.00 (24)

Most confused (gold -> cluster majority): Train departure -> Train destination 30; Restaurant price range -> Restaurant food 16; Hotel stars -> Hotel requested stay 16; Hotel requested people -> Hotel requested stay 14; Hotel type -> Hotel name 13; Train arrive by -> Train leave at 11; Restaurant food -> Restaurant area 6; Train destination -> Train departure 5; Attraction name -> Attraction type 4; Hotel name -> Hotel area 4

