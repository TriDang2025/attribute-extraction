# wf_v3.5 Colab batch prompts (run `results/graph_v22_dev50`, seed 0)

Tokens are estimated as chars / 3.5 (T8: its own prompt file); k drops 8 -> 6 -> 5 when a nbhd prompt reaches 28000. Output tokens: v3.2 C tokens per cluster of the entity x clusters of the group, plus 40 per two-role cluster in g; T8: its earlier answer, raw chars / 3.5.

| prompt | entity | k | chars | est. prompt tokens | est. output tokens | status |
|---|---|---|---|---|---|---|
| restaurant_v2_r2_rerun | E2 | - | 48711 | 13917 | 4471 | ok |
| train_oracle_nbhd0_s0 | E1 | 8 | 14434 | 4124 | 1556 | ok |
| train_oracle_nbhd0_s1 | E1 | 8 | 14434 | 4124 | 1556 | ok |
| train_oracle_nbhd0_s2 | E1 | 8 | 14434 | 4124 | 1556 | ok |
| train_oracle_nbhd1_s0 | E1 | 8 | 26125 | 7464 | 1729 | ok |
| train_oracle_nbhd1_s1 | E1 | 8 | 26125 | 7464 | 1729 | ok |
| train_oracle_nbhd1_s2 | E1 | 8 | 26125 | 7464 | 1729 | ok |
| train_g_nbhd0_s0 | E1 | 8 | 9870 | 2820 | 978 | ok |
| train_g_nbhd0_s1 | E1 | 8 | 9870 | 2820 | 978 | ok |
| train_g_nbhd0_s2 | E1 | 8 | 9870 | 2820 | 978 | ok |
| train_g_nbhd1_s0 | E1 | 8 | 26753 | 7643 | 1889 | ok |
| train_g_nbhd1_s1 | E1 | 8 | 26753 | 7643 | 1889 | ok |
| train_g_nbhd1_s2 | E1 | 8 | 26753 | 7643 | 1889 | ok |
| hotel_g_nbhd0_s0 | E0 | 8 | 24508 | 7002 | 1824 | ok |
| hotel_g_nbhd0_s1 | E0 | 8 | 24508 | 7002 | 1824 | ok |
| hotel_g_nbhd0_s2 | E0 | 8 | 24508 | 7002 | 1824 | ok |
| hotel_g_nbhd1_s0 | E0 | 8 | 10631 | 3037 | 1003 | ok |
| hotel_g_nbhd1_s1 | E0 | 8 | 10631 | 3037 | 1003 | ok |
| hotel_g_nbhd1_s2 | E0 | 8 | 10631 | 3037 | 1003 | ok |
| restaurant_g_nbhd0_s0 | E2 | 8 | 28462 | 8132 | 1700 | ok |
| restaurant_g_nbhd0_s1 | E2 | 8 | 28462 | 8132 | 1700 | ok |
| restaurant_g_nbhd0_s2 | E2 | 8 | 28462 | 8132 | 1700 | ok |
| restaurant_g_nbhd1_s0 | E2 | 8 | 15109 | 4316 | 1700 | ok |
| restaurant_g_nbhd1_s1 | E2 | 8 | 15109 | 4316 | 1700 | ok |
| restaurant_g_nbhd1_s2 | E2 | 8 | 15109 | 4316 | 1700 | ok |
| restaurant_g_nbhd2_s0 | E2 | 8 | 13249 | 3785 | 1445 | ok |
| restaurant_g_nbhd2_s1 | E2 | 8 | 13249 | 3785 | 1445 | ok |
| restaurant_g_nbhd2_s2 | E2 | 8 | 13249 | 3785 | 1445 | ok |

## Estimated calls and tokens per family

| family | calls | est. prompt tokens | est. output tokens |
|---|---|---|---|
| t8 | 1 | 13917 | 4471 |
| oracle | 6 | 34764 | 9855 |
| g | 21 | 110205 | 31617 |
| total | 28 | 158886 | 45943 |

## T19: examples shown per gold role of each two-role cluster (g prompts, shown / mentions with that role)

| cluster | gold role | shown / total | status |
|---|---|---|---|
| E1#0 | departure | 3 / 4 | ok |
| E1#0 | destination | 4 / 6 | ok |
| E1#1 | leave at | 5 / 56 | ok |
| E1#1 | arrive by | 2 / 31 | ok |
| E1#11 | departure | 5 / 5 | ok |
| E1#11 | destination | 3 / 3 | ok |
| E1#13 | leave at | 1 / 1 | ok |
| E1#13 | arrive by | 1 / 1 | ok |
| E1#21 | departure | 2 / 2 | ok |
| E1#21 | destination | 2 / 2 | ok |
| E1#24 | departure | 1 / 1 | ok |
| E1#24 | destination | 1 / 1 | ok |
| E1#25 | departure | 1 / 1 | ok |
| E1#25 | destination | 1 / 1 | ok |
| E1#27 | departure | 3 / 3 | ok |
| E1#27 | destination | 1 / 1 | ok |
| E1#3 | departure | 3 / 21 | ok |
| E1#3 | destination | 3 / 22 | ok |
