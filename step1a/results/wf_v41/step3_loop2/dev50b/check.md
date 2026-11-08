# Step 3 naming for loop 2, dev50b

Frozen Step 3 A prompt (pilot_input.INSTRUCTION_V2 + render_v2 + schema_v2), orders s0 / s1 / s2, no frozen code changed. Tokens are chars / 3.5.

| job | entity | k | clusters | chars | est. prompt tokens | status |
|---|---|---|---|---|---|---|
| hotel_a_l2_dev50b_s0 | E1 (hotel) | 8 | 2 | 6870 | 1962 | ok |
| hotel_a_l2_dev50b_s1 | E1 (hotel) | 8 | 2 | 6870 | 1962 | ok |
| hotel_a_l2_dev50b_s2 | E1 (hotel) | 8 | 2 | 6870 | 1962 | ok |

| cluster | label | loop-2 keep | mentions | distinct values | reason |
|---|---|---|---|---|---|
| L2:hotel#0 | free parking | keep | 21 | 3 | all checks passed |
| L2:hotel#1 | free wifi | keep | 17 | 3 | all checks passed |

Clusters in clusters.json: 5; sent to Step 3: 2 (kept only).
