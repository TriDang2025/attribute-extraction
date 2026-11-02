# wf_v3.7 train stability: Oracle and C over 3 orders (L2, rules v1.1)

Train only. Group agreement = `agreement=split` (mean over clusters of orders that agree with the most common choice / 3). Role-pair flip: see `s1a/stability_v37.py`. Side of a mention = the role slot of the pair that is the majority L2 label of its final group (other: no group, a marked group, or a majority that is no slot of the pair); sides of a cluster = the set of its mentions' sides; a cluster flips between two orders when its sides differ.

| variant | agree groups | agree noise | agree names | two-role clusters flipping (>= 1 pair of orders) | flips (cluster x pair of orders) |
|---|---|---|---|---|---|
| C | 0.611 | 0.920 | 0.889 | 3/9 | 6/27 |
| Oracle | 0.846 | 0.956 | 0.833 | 3/9 | 6/27 |

## C: sides per order of the two-role clusters

| cluster | pair | s0 | s1 | s2 | flips |
|---|---|---|---|---|---|
| E1#0 | departure/destination | departure | destination | departure | 2/3 |
| E1#1 | leave at/arrive by | leave at | leave at | leave at | 0/3 |
| E1#11 | departure/destination | departure | departure | departure | 0/3 |
| E1#13 | leave at/arrive by | other | other | other | 0/3 |
| E1#21 | departure/destination | departure | destination | departure | 2/3 |
| E1#24 | departure/destination | departure | destination | departure | 2/3 |
| E1#25 | departure/destination | departure | departure | departure | 0/3 |
| E1#27 | departure/destination | departure | departure | departure | 0/3 |
| E1#3 | departure/destination | departure+destination | departure+destination | departure+destination | 0/3 |

## Oracle: sides per order of the two-role clusters

| cluster | pair | s0 | s1 | s2 | flips |
|---|---|---|---|---|---|
| E1#0 | departure/destination | departure+destination | departure+destination | departure+destination | 0/3 |
| E1#1 | leave at/arrive by | arrive by+leave at | arrive by+leave at | leave at | 2/3 |
| E1#11 | departure/destination | departure+destination | departure+destination | departure+destination | 0/3 |
| E1#13 | leave at/arrive by | other | other | leave at+other | 2/3 |
| E1#21 | departure/destination | departure+destination | departure+destination | departure+destination | 0/3 |
| E1#24 | departure/destination | destination | destination | destination | 0/3 |
| E1#25 | departure/destination | departure+destination | departure+destination | departure+destination | 0/3 |
| E1#27 | departure/destination | departure+destination | departure+destination | departure+destination | 0/3 |
| E1#3 | departure/destination | departure+destination | departure+destination | departure | 2/3 |

- Two-role train clusters of dev50 at L2: 9. Oracle splits each of them by gold role (so every Oracle side that is a gold role is an upper bound); C does not.
