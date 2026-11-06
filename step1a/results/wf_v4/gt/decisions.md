# wf_v4 decisions (user, 2026-11-06: "Accept defaults")

## GT questions (gt_questions.md)
- **Type "unknown"** (Hotel internet, Hotel parking, both confirmed name columns, Attraction openhours): not scored for type.
- **Taxi and attraction:** kept in the full GT only. They are unreachable, so they are dropped from the reachable-only GT.
- **"Hotel/Restaurant confirmed name":** they stay GT link columns. They are dropped when the booking columns fold into the place table.
- **Columns with 0 mentions** (Hotel internet, Hotel parking, Attraction openhours): kept in the GT.
- **Soft links** (taxi departure and destination → place names): a predicted one counts as right; a missing one is not counted.
- **Shared value sets:** not scored. An extra lookup table counts as an unmatched table.
- **Designs:** the scorer takes the best of the 8 acceptable designs, by grouping F1 and then table F1.

## Rubric (report/3_main/wf_v4/grading_rubric_v1.md)
- Approved as written, with questions 7 and 8 (taxi, attraction) kept.

## Task 13 held-out attributes (config/wf_v4_placement.json), added in this order
1. P1: Hotel stars.
2. P2: Restaurant requested time.
3. P3: Train requested people. Train confirmed reference is also held out.
4. P4: Train trainid.

P5 is skipped, because the GT allows booking columns in the place table.
