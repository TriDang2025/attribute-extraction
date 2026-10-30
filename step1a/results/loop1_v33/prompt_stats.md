# wf_v3.3 pilot prompts (run `results/graph_v22_dev50`, seed 0)

Tokens are estimated as chars / 3.5, plus 300 for the carry block of carry jobs (their `.txt` is written on Colab). k drops 8 -> 6 -> 5 when a nbhd prompt reaches 28000.

| prompt | entity | k | chars | est. tokens | status |
|---|---|---|---|---|---|
| train_e_nbhd0_s0 | E1 | 8 | 10088 | 2882 | ok |
| train_e_nbhd0_s1 | E1 | 8 | 10088 | 2882 | ok |
| train_e_nbhd0_s2 | E1 | 8 | 10088 | 2882 | ok |
| train_e2_nbhd0_s0 | E1 | 8 | 9543 | 2726 | ok |
| train_e2_nbhd0_s1 | E1 | 8 | 9543 | 2726 | ok |
| train_e2_nbhd0_s2 | E1 | 8 | 9543 | 2726 | ok |
| train_f_nbhd0_s0 | E1 | 8 | 10088 | 2882 | ok |
| train_e_nbhd1_s0 | E1 | 8 | 26987 | 8010 | ok |
| train_e_nbhd1_s1 | E1 | 8 | 26987 | 8010 | ok |
| train_e_nbhd1_s2 | E1 | 8 | 26987 | 8010 | ok |
| train_e1_nbhd1_s0 | E1 | 8 | 26971 | 7706 | ok |
| train_e1_nbhd1_s1 | E1 | 8 | 26971 | 7706 | ok |
| train_e1_nbhd1_s2 | E1 | 8 | 26971 | 7706 | ok |
| train_e2_nbhd1_s0 | E1 | 8 | 26442 | 7854 | ok |
| train_e2_nbhd1_s1 | E1 | 8 | 26442 | 7854 | ok |
| train_e2_nbhd1_s2 | E1 | 8 | 26442 | 7854 | ok |
| train_f_nbhd1_s0 | E1 | 8 | 26987 | 8010 | ok |
| hotel_e_nbhd0_s0 | E0 | 8 | 24726 | 7064 | ok |
| hotel_e_nbhd0_s1 | E0 | 8 | 24726 | 7064 | ok |
| hotel_e_nbhd0_s2 | E0 | 8 | 24726 | 7064 | ok |
| hotel_e2_nbhd0_s0 | E0 | 8 | 24181 | 6908 | ok |
| hotel_e2_nbhd0_s1 | E0 | 8 | 24181 | 6908 | ok |
| hotel_e2_nbhd0_s2 | E0 | 8 | 24181 | 6908 | ok |
| hotel_f_nbhd0_s0 | E0 | 8 | 24726 | 7064 | ok |
| hotel_e_nbhd1_s0 | E0 | 8 | 10865 | 3404 | ok |
| hotel_e_nbhd1_s1 | E0 | 8 | 10865 | 3404 | ok |
| hotel_e_nbhd1_s2 | E0 | 8 | 10865 | 3404 | ok |
| hotel_e1_nbhd1_s0 | E0 | 8 | 10849 | 3099 | ok |
| hotel_e1_nbhd1_s1 | E0 | 8 | 10849 | 3099 | ok |
| hotel_e1_nbhd1_s2 | E0 | 8 | 10849 | 3099 | ok |
| hotel_e2_nbhd1_s0 | E0 | 8 | 10320 | 3248 | ok |
| hotel_e2_nbhd1_s1 | E0 | 8 | 10320 | 3248 | ok |
| hotel_e2_nbhd1_s2 | E0 | 8 | 10320 | 3248 | ok |
| hotel_f_nbhd1_s0 | E0 | 8 | 10865 | 3404 | ok |
| restaurant_e_nbhd0_s0 | E2 | 8 | 28680 | 8194 | ok |
| restaurant_e_nbhd0_s1 | E2 | 8 | 28680 | 8194 | ok |
| restaurant_e_nbhd0_s2 | E2 | 8 | 28680 | 8194 | ok |
| restaurant_e2_nbhd0_s0 | E2 | 8 | 28135 | 8038 | ok |
| restaurant_e2_nbhd0_s1 | E2 | 8 | 28135 | 8038 | ok |
| restaurant_e2_nbhd0_s2 | E2 | 8 | 28135 | 8038 | ok |
| restaurant_f_nbhd0_s0 | E2 | 8 | 28680 | 8194 | ok |
| restaurant_e_nbhd1_s0 | E2 | 8 | 15343 | 4683 | ok |
| restaurant_e_nbhd1_s1 | E2 | 8 | 15343 | 4683 | ok |
| restaurant_e_nbhd1_s2 | E2 | 8 | 15343 | 4683 | ok |
| restaurant_e1_nbhd1_s0 | E2 | 8 | 15327 | 4379 | ok |
| restaurant_e1_nbhd1_s1 | E2 | 8 | 15327 | 4379 | ok |
| restaurant_e1_nbhd1_s2 | E2 | 8 | 15327 | 4379 | ok |
| restaurant_e2_nbhd1_s0 | E2 | 8 | 14798 | 4528 | ok |
| restaurant_e2_nbhd1_s1 | E2 | 8 | 14798 | 4528 | ok |
| restaurant_e2_nbhd1_s2 | E2 | 8 | 14798 | 4528 | ok |
| restaurant_f_nbhd1_s0 | E2 | 8 | 15343 | 4683 | ok |
| restaurant_e_nbhd2_s0 | E2 | 8 | 13483 | 4152 | ok |
| restaurant_e_nbhd2_s1 | E2 | 8 | 13483 | 4152 | ok |
| restaurant_e_nbhd2_s2 | E2 | 8 | 13483 | 4152 | ok |
| restaurant_e1_nbhd2_s0 | E2 | 8 | 13467 | 3847 | ok |
| restaurant_e1_nbhd2_s1 | E2 | 8 | 13467 | 3847 | ok |
| restaurant_e1_nbhd2_s2 | E2 | 8 | 13467 | 3847 | ok |
| restaurant_e2_nbhd2_s0 | E2 | 8 | 12938 | 3996 | ok |
| restaurant_e2_nbhd2_s1 | E2 | 8 | 12938 | 3996 | ok |
| restaurant_e2_nbhd2_s2 | E2 | 8 | 12938 | 3996 | ok |
| restaurant_f_nbhd2_s0 | E2 | 8 | 13483 | 4152 | ok |

## Estimated prompt tokens per variant (entity jobs only; gate and split jobs are reused from v3.2)

| entity | variant | calls | est. prompt tokens |
|---|---|---|---|
| train | e | 6 | 32676 |
| train | e1 | 3 | 23118 |
| train | e2 | 6 | 31740 |
| train | f | 2 | 10892 |
| hotel | e | 6 | 31404 |
| hotel | e1 | 3 | 9297 |
| hotel | e2 | 6 | 30468 |
| hotel | f | 2 | 10468 |
| restaurant | e | 9 | 51087 |
| restaurant | e1 | 6 | 24678 |
| restaurant | e2 | 9 | 49686 |
| restaurant | f | 3 | 17029 |
