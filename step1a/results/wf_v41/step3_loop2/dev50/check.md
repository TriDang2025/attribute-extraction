# Step 3 naming for loop 2, dev50

Frozen Step 3 A prompt (pilot_input.INSTRUCTION_V2 + render_v2 + schema_v2), orders s0 / s1 / s2, no frozen code changed. Tokens are chars / 3.5.

| job | entity | k | clusters | chars | est. prompt tokens | status |
|---|---|---|---|---|---|---|
| train_a_l2_dev50_s0 | E1 (train) | 8 | 1 | 3446 | 984 | ok |
| train_a_l2_dev50_s1 | E1 (train) | 8 | 1 | 3446 | 984 | ok |
| train_a_l2_dev50_s2 | E1 (train) | 8 | 1 | 3446 | 984 | ok |
| hotel_a_l2_dev50_s0 | E0 (hotel) | 8 | 2 | 6924 | 1978 | ok |
| hotel_a_l2_dev50_s1 | E0 (hotel) | 8 | 2 | 6924 | 1978 | ok |
| hotel_a_l2_dev50_s2 | E0 (hotel) | 8 | 2 | 6924 | 1978 | ok |

| cluster | label | loop-2 keep | mentions | distinct values | reason |
|---|---|---|---|---|---|
| L2:train#6 | passenger type | keep | 3 | 2 | all checks passed |
| L2:hotel#2 | internet access | keep | 16 | 4 | all checks passed |
| L2:hotel#3 | parking available | keep | 10 | 2 | all checks passed |

Clusters in clusters.json: 25; sent to Step 3: 3 (kept only).
