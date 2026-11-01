# wf_v3.6 model-free noise at L2 (noise_kind=mwoz)

A mention is noise iff it is a choice mention, or it has no label at the level and is not a request mention (a question phrase in a turn with a request act for the cluster's domain). A request mention with no label is neither noise nor an attribute. A cluster is noise when >= 60% of its counted mentions are noise (Q2 rule). Compared with the rules v1 default at L1 (pattern noise kinds; labels = TEAR gold); label_L2 = the same default rules on L2 labels.

| entity | clusters | noise L1 default | noise L2 default | noise L2 mwoz | changed (mwoz vs L1) |
|---|---|---|---|---|---|
| train | 29 | 5 | 5 | 4 | 3 |
| hotel | 31 | 5 | 5 | 6 | 5 |
| restaurant | 57 | 4 | 2 | 3 | 5 |
| all | 117 | 14 | 12 | 13 | 13 |

## Clusters that changed (13)

| ent | cluster | n | L1 | mwoz | top values | why |
|---|---|---|---|---|---|---|
| train | E1#12 | 6 | noise | mixed | how many ticket|how many seat|how many train ticket|there are only 4 train | L1 default: noise share 1.00 (cue 5, noise 1); mwoz L2: noise share 0.17 (noise 1, request 5) |
| train | E1#15 | 18 | unknown | noise | station|airport|train|park | L1 default: noise share nan (unlabeled 18); mwoz L2: noise share 0.83 (labelled 2, noise 15, request 1) |
| train | E1#7 | 9 | noise | mixed | what day|what time | L1 default: noise share 1.00 (cue 9); mwoz L2: noise share 0.00 (request 9) |
| hotel | E0#12 | 11 | noise | mixed | how many day|what day|same day|another day | L1 default: noise share 1.00 (cue 7, noise 3, unlabeled 1); mwoz L2: noise share 0.18 (labelled 2, noise 2, request 7) |
| hotel | E0#19 | 1 | real | noise | tr8167 | L1 default: noise share 0.00 (real_extra 1); mwoz L2: noise share 1.00 (noise 1) |
| hotel | E0#2 | 5 | noise | mixed | how many people|several|4 other people | L1 default: noise share 0.80 (cue 3, labelled 1, noise 1); mwoz L2: noise share 0.20 (labelled 1, noise 1, request 3) |
| hotel | E0#27 | 1 | unknown | noise | main restaurant | L1 default: noise share nan (unlabeled 1); mwoz L2: noise share 1.00 (noise 1) |
| hotel | E0#29 | 1 | unknown | noise | fewer night | L1 default: noise share nan (unlabeled 1); mwoz L2: noise share 1.00 (noise 1) |
| restaurant | E2#29 | 4 | real | noise | 15 minute | L1 default: noise share 0.00 (real_extra 4); mwoz L2: noise share 1.00 (noise 4) |
| restaurant | E2#42 | 4 | unknown | noise | table|your table | L1 default: noise share nan (unlabeled 4); mwoz L2: noise share 1.00 (noise 4) |
| restaurant | E2#45 | 2 | noise | real | ugly duckling|the ugly duckling | L1 default: noise share 1.00 (noise 1, unlabeled 1); mwoz L2: noise share 0.00 (labelled 2) |
| restaurant | E2#48 | 4 | noise | mixed | same day|what time|what day | L1 default: noise share 1.00 (cue 2, noise 2); mwoz L2: noise share 0.50 (labelled 1, noise 2, request 1) |
| restaurant | E2#6 | 4 | noise | mixed | 01223 249955|their phone number|01223 360966|taxi contact number | L1 default: noise share 1.00 (noise 1, unlabeled 3); mwoz L2: noise share 0.50 (labelled 2, noise 2) |
