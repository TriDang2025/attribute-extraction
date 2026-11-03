# wf_v3.8 W2: wrong merges of A s012 (v2.2) and the J-split parts (v2.3)

Level L2, rules v1.1, A s012 = vote over the 3 orders. Scripts: `scripts/merges_v38.py`, `s1a/merges_v38.py`.

## Answers

**Task 5, why A's merges are wrong.**
- dev50: 8/11 merges wrong: noise 1, wrong_attr 5, wrong_role 2. Source: majority of orders 5, one order 2, vote only 1. Role guard flags 3/8 (role pairs: 2/2 wrong_role; the rest are location / address name pairs) and wrongly flags 0/3 right merges; name merge adds 0 merges.
- dev50b: 6/13 merges wrong: noise 1, wrong_attr 5. Source: majority of orders 6. Role guard flags 2/6 (role pairs: 0/0 wrong_role; the rest are location / address name pairs) and wrongly flags 1/7 right merges; name merge adds 0 merges.

**Task 6, why role-correct stayed the same with v2.3.**
- dev50: role-correct 3/8 on v2.2 and 3/8 on v2.3; the per-attribute cause is the same for 8/8 attributes. The 5 misses on v2.3: not recoverable by step 1a 3, no group has it as majority (recoverable) 2.
- dev50b: role-correct 4/8 on v2.2 and 4/8 on v2.3; the per-attribute cause is the same for 8/8 attributes. The 4 misses on v2.3: not recoverable by step 1a 3, no group has it as majority (recoverable) 1.

## Task 5: wrong merges of A s012 on Step 1a v2.2

Wrong merge = judged merge (>= 2 members with a gold top attribute) whose members disagree on the top L2 attribute (`wrong_attr`) or role slot (`wrong_role`), or whose noise share is >= 20% (`noise`). Step: A's attributes come from the model's own answer (clusters given the same name inside one prompt; A has no neighbourhood groups). The scorer's +namemerge copy of the vote is the only name merge across groups. Source: orders that put all judged members into one group. Guard (name) = role guard on the vote names (members share one name, so it cannot fire); guard (orders) = role guard on any name the cluster got in the 3 orders or the vote.

| set | judged merges | wrong | name merge: extra merges | name merge: extra wrong | right merges the guard (orders) would block |
|---|---|---|---|---|---|
| dev50 | 11 (+2 unjudged) | 8/11 | 0 | 0 | 0/3 |
| dev50b | 13 (+1 unjudged) | 6/13 | 0 | 0 | 1/7 |

Wrong merges per cause (reason x source), with how many each guard would block:

| set | step | reason | source | n | guard_name | guard_orders |
|---|---|---|---|---|---|---|
| dev50 | A prompt | noise | majority of orders | 1 | 0 | 0 |
| dev50 | A prompt | wrong_attr | majority of orders | 3 | 0 | 0 |
| dev50 | A prompt | wrong_attr | one order (A r1) | 1 | 0 | 1 |
| dev50 | A prompt | wrong_attr | vote only | 1 | 0 | 0 |
| dev50 | A prompt | wrong_role | majority of orders | 1 | 0 | 1 |
| dev50 | A prompt | wrong_role | one order (A r1) | 1 | 0 | 1 |
| dev50b | A prompt | noise | majority of orders | 1 | 0 | 0 |
| dev50b | A prompt | wrong_attr | majority of orders | 5 | 0 | 2 |

Per set: dev50: 8 wrong, guard (orders) blocks 3/8; dev50b: 6 wrong, guard (orders) blocks 2/6.

Every wrong merge (members: cluster, top L2 attribute, mentions; odd = members off the plurality attribute):

- dev50 train `arrival_location` (wrong_role, noise 0.043, 4 members, one order (A r1), guard orders YES E1#0+E1#11;E1#11+E1#24;E1#11+E1#25): E1#0 Train destination (11) *odd*; E1#11 Train departure (8); E1#24 Train departure (2); E1#25 Train departure (2)
- dev50 train `departure_location` (wrong_role, noise 0.056, 6 members, majority of orders, guard orders YES E1#19+E1#27;E1#21+E1#27;E1#23+E1#27;E1#27+E1#28;E1#27+E1#6): odd members: E1#6 Train destination (2)
- dev50 hotel `hotel_location` (noise, noise 0.25, 2 members, majority of orders, guard orders no): E0#10 Hotel area (6); E0#7 Hotel area (2)
- dev50 hotel `hotel_number_of_guests` (wrong_attr, noise 0.059, 2 members, majority of orders, guard orders no): E0#11 Hotel requested people (12); E0#2 Hotel requested stay (5) *odd*
- dev50 hotel `hotel_name` (wrong_attr, noise 0.043, 10 members, majority of orders, guard orders no): odd members: E0#21 Hotel address (2)
- dev50 restaurant `restaurant_name` (wrong_attr, noise 0.037, 24 members, vote only, guard orders no): odd members: E2#13 Taxi destination (1); E2#26 Taxi departure (4); E2#44 Restaurant address (2); E2#51 Taxi departure (2)
- dev50 restaurant `restaurant_location` (wrong_attr, noise 0.056, 3 members, majority of orders, guard orders no): E2#15 Restaurant area (27); E2#32 Restaurant area (5); E2#50 Restaurant address (4) *odd*
- dev50 restaurant `restaurant_address` (wrong_attr, noise 0.0, 9 members, one order (A r1), guard orders YES E2#2+E2#27;E2#23+E2#27;E2#27+E2#31;E2#27+E2#36;E2#27+E2#46;E2#27+E2#49;E2#27+E2#52;E2#27+E2#54): odd members: E2#27 Attraction address (1)
- dev50b hotel `location` (noise, noise 0.2, 2 members, majority of orders, guard orders no): E1#12 Hotel area (14); E1#8 Hotel area (6)
- dev50b hotel `start_date` (wrong_attr, noise 0.05, 2 members, majority of orders, guard orders no): E1#19 Restaurant requested time (1) *odd*; E1#5 Hotel requested day (19)
- dev50b hotel `address` (wrong_attr, noise 0.143, 6 members, majority of orders, guard orders YES E1#20+E1#21;E1#21+E1#23;E1#21+E1#28;E1#21+E1#29;E1#21+E1#30): odd members: E1#20 Restaurant address (1); E1#21 Restaurant address (1)
- dev50b restaurant `restaurant_name` (wrong_attr, noise 0.056, 14 members, majority of orders, guard orders no): odd members: E3#37 Taxi departure (1)
- dev50b restaurant `area` (wrong_attr, noise 0.083, 3 members, majority of orders, guard orders no): E3#16 Restaurant area (7); E3#34 Restaurant address (1) *odd*; E3#9 Attraction area (4) *odd*
- dev50b restaurant `restaurant_address` (wrong_attr, noise 0.0, 5 members, majority of orders, guard orders YES E3#30+E3#33;E3#30+E3#38;E3#30+E3#47;E3#30+E3#7;E3#33+E3#38;E3#33+E3#47;E3#33+E3#7;E3#38+E3#47;E3#38+E3#7;E3#47+E3#7): odd members: E3#38 Attraction address (1)

## Task 6: what A named J's parts (v2.3)

- **dev50**: J made 7 splits; A saw 7 of them (the other 0 are in stage-1 entities that A is not run on). Verdicts: kept apart 5/7, one role only 2/7. Part clusters with a gold role: 17; vote name on the right side 14/17, on the wrong side 1/17 (by part, vote name: end: right 6, wrong 0, other 0; start: right 5, wrong 1, other 1; unknown: right 3, wrong 0, other 1), no side word 1/17, unnamed (marked) 1/17; right side per order s0/s1/s2: 14/14/13 of 17. Part clusters re-joined by the vote: 4/18 (across roles: 0 splits).
- **dev50b**: J made 10 splits; A saw 7 of them (the other 3 are in stage-1 entities that A is not run on). Verdicts: kept apart 4/7, one role only 1/7, re-merged across roles 2/7. Part clusters with a gold role: 17; vote name on the right side 15/17, on the wrong side 2/17 (by part, vote name: end: right 6, wrong 0, other 0; start: right 6, wrong 0, other 0; unknown: right 3, wrong 2, other 0), no side word 0/17, unnamed (marked) 0/17; right side per order s0/s1/s2: 15/16/14 of 17. Part clusters re-joined by the vote: 8/20 (across roles: 2 splits).
- dev50 wrong merges: v2.2 8/11, v2.3 7/11 {'wrong_attr': 4, 'wrong_role': 2, 'noise': 1}; found (A s012) v2.2 31 vs v2.3 31; the name merge adds 0 merges on v2.3.
- dev50b wrong merges: v2.2 6/13, v2.3 5/11 {'wrong_attr': 4, 'wrong_role': 1}; found (A s012) v2.2 29 vs v2.3 29; the name merge adds 0 merges on v2.3.

Role-correct (A s012, names rated, one group rated right per attribute) per role base attribute:

- dev50 v2.2: role-correct 3/8 (train 3/4, restaurant/taxi 0/4)
- dev50 v2.3: role-correct 3/8 (train 3/4, restaurant/taxi 0/4)
- dev50b v2.2: role-correct 4/8 (train 4/4, restaurant/taxi 0/4)
- dev50b v2.3: role-correct 4/8 (train 4/4, restaurant/taxi 0/4)

| set | ent | attr | found | recoverable | best_name | best_purity | best_coverage | cause |
|---|---|---|---|---|---|---|---|---|
| dev50 | train | Train arrive by | False | False | departure_time | 0.36 | 0.69 | not recoverable by step 1a |
| dev50 | train | Train departure | True | True | departure_location | 0.9 | 0.62 | right |
| dev50 | train | Train destination | True | True | arrival_location | 0.74 | 0.76 | right |
| dev50 | train | Train leave at | True | True | arrival_time | 0.68 | 0.33 | right |
| dev50 | restaurant | Taxi arrive by | False | False | time_for_taxi | 0.38 | 1.0 | not recoverable by step 1a |
| dev50 | restaurant | Taxi departure | False | True | restaurant_name | 0.25 | 0.14 | no group has it as majority (recoverable) |
| dev50 | restaurant | Taxi destination | False | True | restaurant_type | 0.06 | 0.25 | no group has it as majority (recoverable) |
| dev50 | restaurant | Taxi leave at | False | False | time_for_taxi | 0.25 | 1.0 | not recoverable by step 1a |
| dev50b | train | Train arrive by | True | False | arrival_time | 0.88 | 0.28 | right |
| dev50b | train | Train departure | True | True | departure_location | 0.93 | 0.59 | right |
| dev50b | train | Train destination | True | True | destination | 0.83 | 0.8 | right |
| dev50b | train | Train leave at | False | False | departure_time | 0.51 | 0.95 | right |
| dev50b | restaurant | Taxi arrive by | False | False | restaurant_reservation_date | 0.05 | 1.0 | not recoverable by step 1a |
| dev50b | restaurant | Taxi departure | False | True | restaurant_name | 0.06 | 1.0 | no group has it as majority (recoverable) |
| dev50b | restaurant | Taxi destination | False | False | restaurant_name | 0.06 | 1.0 | not recoverable by step 1a |
| dev50b | restaurant | Taxi leave at | False | False | restaurant_reservation_time | 0.05 | 1.0 | not recoverable by step 1a |

Same table for v2.2 (cause only): dev50 Train arrive by: not recoverable by step 1a; dev50 Train departure: right; dev50 Train destination: right; dev50 Train leave at: right; dev50 Taxi arrive by: not recoverable by step 1a; dev50 Taxi departure: no group has it as majority (recoverable); dev50 Taxi destination: no group has it as majority (recoverable); dev50 Taxi leave at: not recoverable by step 1a; dev50b Train arrive by: right; dev50b Train departure: right; dev50b Train destination: right; dev50b Train leave at: right; dev50b Taxi arrive by: not recoverable by step 1a; dev50b Taxi departure: no group has it as majority (recoverable); dev50b Taxi destination: not recoverable by step 1a; dev50b Taxi leave at: not recoverable by step 1a
