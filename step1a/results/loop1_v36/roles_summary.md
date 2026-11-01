# Role words: all cue words vs general words only (wf_v3.6, task 4)

Same data as `results/loop1_v35/roles_summary.md`: gold role = L2 slot of a role pair (train / taxi); two-role cluster = both slots of one pair, each >= 20% of the cluster's labelled mentions. J = nearest cue word among the 3 words before the value. **full** = all of `pilot_input.CUE_ROLES`; **general** = from, after (start) and to, into, by, before (end), no domain word. accuracy = correct / covered, coverage = covered / gold-role mentions; counts are k/n (share).

## Two-role clusters, all entities (9 clusters, 162 gold-role mentions)

| cue words | accuracy | coverage |
|---|---|---|
| full | 118/123 (0.959) | 123/162 (0.759) |
| general | 89/97 (0.918) | 97/162 (0.599) |

## Two-role clusters, train (9 clusters, 162 gold-role mentions)

| cue words | accuracy | coverage |
|---|---|---|
| full | 118/123 (0.959) | 123/162 (0.759) |
| general | 89/97 (0.918) | 97/162 (0.599) |

## All clusters with a gold role (27 clusters, 192 gold-role mentions)

| cue words | accuracy | coverage |
|---|---|---|
| full | 135/143 (0.944) | 143/192 (0.745) |
| general | 104/115 (0.904) | 115/192 (0.599) |

## Each cue word (all clusters with a gold role; the word is the nearest cue word before the value)

| word | kind | side | mentions covered | accuracy |
|---|---|---|---|---|
| depart | domain | start | 0 | 0/0 (n/a) |
| departing | domain | start | 1 | 0/1 (0.000) |
| departs | domain | start | 4 | 4/4 (1.000) |
| leave | domain | start | 7 | 7/7 (1.000) |
| leaving | domain | start | 8 | 8/8 (1.000) |
| arrive | domain | end | 6 | 5/6 (0.833) |
| arrives | domain | end | 7 | 7/7 (1.000) |
| arriving | domain | end | 2 | 2/2 (1.000) |
| after | general | start | 21 | 21/21 (1.000) |
| from | general | start | 32 | 31/32 (0.969) |
| before | general | end | 0 | 0/0 (n/a) |
| by | general | end | 19 | 17/19 (0.895) |
| into | general | end | 1 | 1/1 (1.000) |
| to | general | end | 35 | 32/35 (0.914) |
