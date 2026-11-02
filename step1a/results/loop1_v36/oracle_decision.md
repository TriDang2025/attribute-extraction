# wf_v3.6 oracle role split (T14): decision for J

Oracle = the v3.2 C prompt on the cluster table where every two-role cluster is split by gold role (train: 9 clusters; hotel and restaurant have none, so their oracle rows are the C rows). C = the same prompt without the split (v3.2). Found = gold attributes with a group of purity >= 0.6 and coverage >= 10%. Rule: build J only if oracle gains >= 2 attributes at L2 and no entity loses one.

## Level 2

| variant | found train | found hotel | found restaurant | total |
|---|---|---|---|---|
| C s0 | 7/10 | 11/14 | 11/16 | 29/40 |
| Oracle s0 | 9/10 | 11/14 | 11/16 | 31/40 |
| C s1 | 7/10 | 12/14 | 11/16 | 30/40 |
| Oracle s1 | 9/10 | 12/14 | 11/16 | 32/40 |
| C s2 | 6/10 | 12/14 | 11/16 | 29/40 |
| Oracle s2 | 8/10 | 12/14 | 11/16 | 31/40 |
| C s012 | 7/10 | 11/14 | 11/16 | 29/40 |
| Oracle s012 | 9/10 | 11/14 | 11/16 | 31/40 |

Oracle s012 minus C s012: train +2, hotel +0, restaurant +0, total +2. Per order (total): s0 +2, s1 +2, s2 +2.

## Level 1

| variant | found train | found hotel | found restaurant | total |
|---|---|---|---|---|
| C s0 | 3/7 | 9/11 | 9/12 | 21/30 |
| Oracle s0 | 4/7 | 9/11 | 9/12 | 22/30 |
| C s1 | 3/7 | 9/11 | 9/12 | 21/30 |
| Oracle s1 | 4/7 | 9/11 | 9/12 | 22/30 |
| C s2 | 3/7 | 9/11 | 9/12 | 21/30 |
| Oracle s2 | 4/7 | 9/11 | 9/12 | 22/30 |
| C s012 | 3/7 | 9/11 | 9/12 | 21/30 |
| Oracle s012 | 4/7 | 9/11 | 9/12 | 22/30 |

Oracle s012 minus C s012: train +1, hotel +0, restaurant +0, total +1. Per order (total): s0 +1, s1 +1, s2 +1.

**Decision at L2** (build J only if oracle gains >= 2 attributes and no entity loses one): **PASS** (total +2; train +2, hotel +0, restaurant +0)

**Decision at L1** (build J only if oracle gains >= 2 attributes and no entity loses one): **FAIL** (total +1; train +1, hotel +0, restaurant +0) (L1 shown for reference)

