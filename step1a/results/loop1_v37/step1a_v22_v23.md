# Step 1a v2.2 vs v2.3 on dev50 and dev50b (wf_v3.7, T9 and T13)

v2.2 = frozen recipe `F_m2_t06_bk`. v2.3 = `V23`: v2.2 with the T26 value-type fix in both type partitions (`value_type_v35`: 8.08GBP, 37.79 GPB, 66 GBP are price; 28-minute, 105 minutes are duration) and the J split of two-role clusters (`s1a/roles_v37.py`: a cluster is split when the cue words put >= 20% of its mentions on each side; mentions with no cue word form their own unknown-role cluster; no gold labels).

Cue words of the J split: general words plus words learned per cluster (T12, `cue_words.md`). No learned word was mapped to a side on dev50 or dev50b (see the empty `learned` column below), so J here = the general cue words. dev50b was used for confirmation only: nothing was tuned on it. The `labels` stage wrote `label_sheet.csv` for the non-gold clusters of each run and it is left unfilled (only the select / schema stages and the old jury / pattern noise kinds need it; rules v1.1 noise does not).

## Recall at K and L2 ceiling

L1 = TEAR gold classes (recall.py with the gold values); L2 = GT level 2 labels on the clustered mentions (`s1a/step1a_v37.py`; strict: some cluster purity >= 0.6; recoverable: or >= 2 mentions inside and purity >= 0.25; present: >= 1 labelled mention inside a cluster). **L2 ceiling** = `ceiling_v37.ceiling_table` (found rule of rules v1.1: a single cluster with purity >= 0.6 and coverage >= 10% of the attribute's mentions; present: some labelled mention is in a cluster of the entity), over the L2 base attributes.

| set | version | K | L1 strict | L1 recoverable | L1 present | L2 strict | L2 recoverable | L2 present | L2 ceiling present | L2 ceiling recoverable |
|---|---|---|---|---|---|---|---|---|---|---|
| dev50 | v2.2 | 163 | 20/33 | 28/33 | 31/33 | 30/40 | 35/40 | 38/40 | 38/40 | 29/40 |
| dev50 | v2.3 | 173 | 20/33 | 28/33 | 31/33 | 30/40 | 35/40 | 38/40 | 38/40 | 30/40 |
| dev50b | v2.2 | 152 | 25/33 | 29/33 | 31/33 | 33/41 | 38/41 | 39/41 | 38/41 | 30/41 |
| dev50b | v2.3 | 168 | 25/33 | 29/33 | 31/33 | 34/41 | 38/41 | 39/41 | 38/41 | 30/41 |

L2 ceiling per entity:

| set | version | train: present / recoverable (of n) | hotel: present / recoverable (of n) | restaurant: present / recoverable (of n) |
|---|---|---|---|---|
| dev50 | v2.2 | 10 / 7 (of 10) | 12 / 9 (of 14) | 16 / 13 (of 16) |
| dev50 | v2.3 | 10 / 8 (of 10) | 12 / 9 (of 14) | 16 / 13 (of 16) |
| dev50b | v2.2 | 10 / 8 (of 10) | 12 / 10 (of 14) | 16 / 12 (of 17) |
| dev50b | v2.3 | 10 / 8 (of 10) | 12 / 10 (of 14) | 16 / 12 (of 17) |

## Run times (wall seconds, CPU laptop)

Export = `export_mentions.py` (GLiNER, bge-m3 encodes, clustering); stages = `graph_run.py` coverage, graph, stability, signals, labels. The v2.2 dev50b export needed fresh GLiNER and bge-m3 encodes; the others read the caches.

| run | export | stages 1-4 |
|---|---|---|
| graph_v22_dev50 | 117 |  |
| graph_v23_dev50 | 20 | 24 |
| graph_v22_dev50b | 948 | 38 |
| graph_v23_dev50b | 20 | 25 |

## J split on dev50

7 clusters split; unknown-part sizes [0, 0, 0, 1, 2, 3, 8]; mentions in the unknown parts 14 of 72 in split clusters.

Clusters are listed as start part; end part; unknown part. l2_labels: the GT L2 labels of the mentions in each part (not used by the split).

| entity | n | start | end | unknown | clusters | learned | l2_labels |
|---|---|---|---|---|---|---|---|
| E1 | 11 | 3 | 5 | 3 | E1#35;E1#0;E1#24 |  | start: Train departure 3; end: Train destination 4, - 1; unknown: Train destination 2, Train departure 1 |
| E1 | 45 | 13 | 24 | 8 | E1#10;E1#3;E1#5 |  | start: Train departure 12, - 1; end: Train destination 17, Train departure 6, - 1; unknown: Train destination 5, Train departure 3 |
| E1 | 2 | 1 | 1 | 0 | E1#7;E1#11 |  | start: Train destination 1; end: Train destination 1 |
| E2 | 4 | 1 | 1 | 2 | E2#29;E2#26;E2#27 |  | start: Taxi departure 1; end: Attraction type 1; unknown: Taxi departure 2 |
| E1 | 4 | 1 | 2 | 1 | E1#22;E1#36;E1#23 |  | start: Train departure 1; end: Train destination 2; unknown: Train departure 1 |
| E1 | 2 | 1 | 1 | 0 | E1#34;E1#29 |  | start: Train departure 1; end: Train destination 1 |
| E1 | 4 | 3 | 1 | 0 | E1#31;E1#32 |  | start: Train departure 3; end: Train destination 1 |

## J split on dev50b

10 clusters split; unknown-part sizes [0, 0, 0, 1, 2, 2, 3, 3, 4, 12]; mentions in the unknown parts 27 of 77 in split clusters.

Clusters are listed as start part; end part; unknown part. l2_labels: the GT L2 labels of the mentions in each part (not used by the split).

| entity | n | start | end | unknown | clusters | learned | l2_labels |
|---|---|---|---|---|---|---|---|
| E0 | 6 | 2 | 4 | 0 | E0#32;E0#1 |  | start: Train departure 2; end: Train destination 4 |
| E0 | 5 | 1 | 1 | 3 | E0#24;E0#2;E0#20 |  | start: - 1; end: - 1; unknown: - 3 |
| E4 | 5 | 1 | 4 | 0 | E4#10;E4#1 |  | start: - 1; end: - 3, Taxi destination 1 |
| E4 | 15 | 3 | 8 | 4 | E4#8;E4#2;E4#4 |  | start: Taxi leave at 3; end: Taxi arrive by 4, Taxi leave at 4; unknown: Taxi arrive by 1, Hotel stars 1, Taxi leave at 1, Restaurant requested time 1 |
| E0 | 23 | 5 | 6 | 12 | E0#11;E0#15;E0#9 |  | start: Train departure 5; end: Train destination 6; unknown: Train destination 6, Train departure 6 |
| E0 | 4 | 1 | 2 | 1 | E0#29;E0#12;E0#30 |  | start: Train departure 1; end: - 1, Train destination 1; unknown: Train departure 1 |
| E0 | 7 | 2 | 2 | 3 | E0#14;E0#21;E0#16 |  | start: Train departure 1, - 1; end: Train destination 2; unknown: Train destination 3 |
| E0 | 5 | 2 | 1 | 2 | E0#19;E0#22;E0#23 |  | start: Train departure 2; end: Train destination 1; unknown: Train destination 1, Train departure 1 |
| E4 | 2 | 1 | 1 | 0 | E4#15;E4#20 |  | start: Taxi departure 1; end: Taxi departure 1 |
| E0 | 5 | 1 | 2 | 2 | E0#25;E0#31;E0#26 |  | start: Train departure 1; end: Train destination 2; unknown: Train departure 1, Train destination 1 |
