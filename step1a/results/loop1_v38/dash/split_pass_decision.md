# wf_v3.8 A s012 without the split pass

Variant: every cluster keeps its A decision (the v3.1 split prompts are not read: `s1a/nosplit_v38.py`); the 3 orders and the vote are rebuilt, nothing else changes. Rule: drop the split pass if the nosplit vote passes the recall guard (RULES_V1_2.md, per entity) and columns per found attribute go down, on both sets.

- dev50: A s012 found 31/40 (train 8/8, hotel 12/12, restaurant 11/11), columns per found 1.742, dup 23, columns 67; nosplit found 24/40 (train 6/8, hotel 8/12, restaurant 10/11; below: train, hotel, restaurant), columns per found 1.083, dup 2, columns 32. Guard FAIL; columns per found down.
- dev50b: A s012 found 29/41 (train 8/8, hotel 10/10, restaurant 11/11), columns per found 1.552, dup 16, columns 56; nosplit found 25/41 (train 7/8, hotel 8/10, restaurant 10/11; below: train, hotel, restaurant), columns per found 1.08, dup 2, columns 35. Guard FAIL; columns per found down.

**Decision: KEEP the split pass.**
