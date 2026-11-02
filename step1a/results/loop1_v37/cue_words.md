# Cue words: general only (a) vs general + learned per cluster (b) (wf_v3.7, T12)

Data and scoring as `results/loop1_v36/roles_summary.md`: gold role = L2 slot of a role pair (train / taxi); two-role cluster = both slots of one pair, each >= 20% of the cluster's labelled mentions (the 9 train clusters of dev50). J = nearest cue word among the 3 words before the value. accuracy = correct / covered, coverage = covered / gold-role mentions.

**(a)** general words only: from, after (start); to, into, by, before (end).

**(b)** (a) plus words learned per cluster, no gold role used:
1. candidate = the word just before a mention; kept for a cluster when splitting the cluster by it leaves two parts that are each >= 20% of the cluster's mentions;
2. its side comes from the general cue words: among the mentions it precedes, take the side given by the nearest general cue word in the 3 words before the value (e.g. "from the" -> the word "the" gets evidence for the start side); the word takes the majority side when >= 2 mentions give evidence, they are >= 20% of the mentions the word precedes, and the majority is >= 80% of them; otherwise it is not used;
3. J side of a mention = nearest word of the 3 before the value in (a) plus the cluster's learned words of that side.

**(b0)** the first version of the mapping rule, without the 20% evidence share (a word needed only 2 mentions with side evidence): shown for comparison, it was replaced by (b) before the choice.

The gold roles are used only to pick the two-role clusters and to score; the learning never sees them.

## Two-role clusters, train (9 clusters)

| cue words | accuracy | coverage |
|---|---|---|
| (a) general | 89/97 (0.918) | 97/162 (0.599) |
| (b) general + learned | 89/97 (0.918) | 97/162 (0.599) |
| (b0) first mapping rule | 102/139 (0.734) | 139/162 (0.858) |

## All clusters with a gold role (27 clusters)

| cue words | accuracy | coverage |
|---|---|---|
| (a) general | 104/115 (0.904) | 115/192 (0.599) |
| (b) general + learned | 104/115 (0.904) | 115/192 (0.599) |
| (b0) first mapping rule | 117/157 (0.745) | 157/192 (0.818) |

**Choice: (b)** ((b) when its accuracy >= (a)'s, on the two-role train clusters).

## Learned words per cluster (candidates that pass the share rule)

| cluster | word | mentions with the word | cluster size | evidence start | evidence end | side |
|---|---|---|---|---|---|---|
| E1#1 | at | 44 | 89 | 0 | 2 | not used |
| E1#11 | leaving | 3 | 8 | 0 | 0 | not used |
| E1#13 | 5 | 1 | 5 | 0 | 0 | not used |
| E1#13 | are | 1 | 5 | 0 | 0 | not used |
| E1#21 | leaves | 1 | 4 | 0 | 0 | not used |
| E1#24 | via | 1 | 2 | 0 | 1 | not used |
