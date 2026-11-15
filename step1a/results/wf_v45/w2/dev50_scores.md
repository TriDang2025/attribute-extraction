# W2 dev50 check: one command on raw dev50 vs the frozen runs

Command run: `results/wf_v45/w2/n50` (Colab 2026-11-15, Llama-3.1-8B, Step 4 = v4.3, set c_n50 = the 50 dev50 dialogues as raw text).

## Step 1a-2
Laptop run on the raw text: mentions, clusters and entities equal `results/graph_v22_dev50` row for row (963 mentions, 163 clusters); the
A prompts of train / hotel / restaurant equal the frozen T1B prompts byte for byte. Without gold, all 5 predicted entities go on: hotel,
train, restaurant, attraction (E3) and attraction_2 (E4, 4 mentions).

## Step 3 (L2 found, dev50 GT, scored on the laptop)

| run | found train | found hotel | found restaurant | found L2 | final columns | duplicate columns | noise columns |
|---|---|---|---|---|---|---|---|
| frozen v4.4 T4 (dev50) | 8 | 11 | 12 | 31/40 | 58 | 32 | 3 |
| command on raw dev50 | 8 | 11 | 12 | 31/40 | 61 | 34 | 3 |

Plus 16 columns for attraction and attraction_2 (no GT). Scoring note: `step3_post_v43.score` rebuilds the columns from the answers and
stops when they differ from `columns.json`; on the laptop the rebuild moves a few mentions between two columns (train booking id /
reference number, restaurant address / phone number) for the frozen T4 run too, so both rows are scored with the saved `columns.json`
(this reproduces the frozen 31/40 and 27/41 exactly).

## Step 4 (v4.3, single seed chains, dev50, full GT, corrected scorer)

| run | input | table F1 | grouping F1 | GT columns placed | PK right a / b | links | tables per chain | calls | prompt tokens |
|---|---|---|---|---|---|---|---|---|---|
| frozen v4.3 (wf_v43 u4, rescored) | a_llama43 | 0.622 | 0.625 | 80/156 (0.513) | 6/11 / 11/11 | 0/3 | 3-9 | n/a | n/a |
| command on raw dev50 | a_llama44, 5 entities | 0.600 | 1.000 | 76/150 (0.507) | 0/9 / 9/9 | n/a | 5 | 51 | 156,474 |

Differences and reasons:
- 5 tables instead of 3-4: attraction and attraction_2 are tables of their own (no gold to drop them), so table precision is 3/5.
- The input is Step 3 v4.4 (a_llama44), the frozen v4.3 score is on a_llama43; v4.3 Step 4 had not run on a_llama44 before.
- PK rule a drops from 6/11 to 0/9 (not explained yet).

## Cost of the command (n50)
Step 3: 572 calls, 424,470 / 22,264 tokens; Step 4: 51 calls, 156,474 / 2,497 tokens; total 623 calls, 580,944 / 24,761 tokens, 0 retries.
Model load 254.7 s; LLM time 57 s (batched); Step 1a-2 on the laptop CPU 1,102 s.
