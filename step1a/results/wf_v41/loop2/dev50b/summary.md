# Loop 2 named probe, dev50b

Labels: `results/wf_v41/step1b/labels_dev50b.json`; run 121 s. Config: k=40, threshold=0.3, min_dialogues=3, min_support=0.05, max_overlap=0.5.
Keep rule: n_dialogues >= min_dialogues and support >= min_support and overlap < max_overlap.

| entity | labels | kept | dropped |
|---|---|---|---|
| train | 2 | 0 | 2 |
| hotel | 2 | 2 | 0 |
| restaurant | 1 | 0 | 1 |

| id | label | keep | mentions | dialogues | support | cohesion | overlap (column) | top values | reason |
|---|---|---|---|---|---|---|---|---|---|
| L2:train#0 | ticket class | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
| L2:train#1 | return ticket | drop | 7 | 5 | 0.278 | 0.513 | 0.86 (train id) | cl4v2583, tl4r46ys, tr2289 | overlap 0.857 >= 0.5 (mostly column 'train id') |
| L2:hotel#0 | free parking | keep | 21 | 14 | 0.560 | 0.947 | 0.05 (amenities) | free parking, parking, free internet and parking | all checks passed |
| L2:hotel#1 | free wifi | keep | 17 | 10 | 0.400 | 0.920 | 0.00 (-) | free wifi, wifi, free internet | all checks passed |
| L2:restaurant#0 | vegetarian options | drop | 0 | 0 | 0.000 | - | 0.00 (-) |  | no spans |
