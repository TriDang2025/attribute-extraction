# Role evidence (wf_v3.5 T15, T16)

Gold role = L2 slot of a role pair (train/taxi). Two-role cluster = both slots of one pair, each >= 20% of the cluster's labelled mentions. J = cue word (from/leave... start, to/arrive/by... end) among the 3 words before the value. Context split = KMeans k=2 on bge-m3 of the turn with the value as [V], split when silhouette >= 0.25; each part takes its own majority gold role (upper bound: it uses the gold labels). accuracy = correct / covered, coverage = covered / gold-role mentions.

## Two-role clusters, all entities (9 clusters, 162 gold-role mentions)

- J: accuracy 118/123 (0.959), coverage 123/162 (0.759)
- context split: accuracy 97/162 (0.599), coverage 162/162 (1.000); clusters split 1

## Two-role clusters, train (9 clusters, 162 gold-role mentions)

- J: accuracy 118/123 (0.959), coverage 123/162 (0.759)
- context split: accuracy 97/162 (0.599), coverage 162/162 (1.000); clusters split 1

## All clusters with a gold role (27 clusters, 192 gold-role mentions)

- J: accuracy 135/143 (0.944), coverage 143/192 (0.745)
- context split: accuracy 124/192 (0.646), coverage 192/192 (1.000); clusters split 3

## Per two-role cluster

| cluster_id | pair | n_gold_role_j | accuracy_j | coverage_j | split | silhouette | accuracy_ctx | acc_nosplit |
|---|---|---|---|---|---|---|---|---|
| E1#0 | departure/destination | 10 | 1.000 | 0.900 | False | 0.115 | 0.600 | 0.600 |
| E1#1 | leave at/arrive by | 87 | 0.982 | 0.632 | False | 0.097 | 0.644 | 0.644 |
| E1#11 | departure/destination | 8 | 1.000 | 0.875 | False | 0.114 | 0.625 | 0.625 |
| E1#13 | leave at/arrive by | 2 | nan | 0.000 | True | 0.437 | 0.500 | 0.500 |
| E1#21 | departure/destination | 4 | 1.000 | 0.750 | False | 0.172 | 0.500 | 0.500 |
| E1#24 | departure/destination | 2 | 0.500 | 1.000 | False | nan | 0.500 | 0.500 |
| E1#25 | departure/destination | 2 | 1.000 | 1.000 | False | nan | 0.500 | 0.500 |
| E1#27 | departure/destination | 4 | 1.000 | 1.000 | False | 0.200 | 0.750 | 0.750 |
| E1#3 | departure/destination | 43 | 0.927 | 0.953 | False | 0.071 | 0.512 | 0.512 |
