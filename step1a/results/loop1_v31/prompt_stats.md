# wf_v3.1 pilot prompts (run `results/graph_v22_dev50`, seed 0)

Tokens are estimated as chars / 3.5; k drops 8 -> 6 -> 5 when a prompt reaches 28000.

| prompt | entity | k | chars | est. tokens | status |
|---|---|---|---|---|---|
| train_nohints | E1 | 8 | 31914 | 9118 | ok |
| train_nohints_long | E1 | 16 | 44156 | 12616 | ok |
| train_v2 | E1 | 8 | 32252 | 9214 | ok |
| train_v2_r2 | E1 | 8 | 32252 | 9214 | ok |
| train_v2_nocontext | E1 | 8 | 8148 | 2328 | ok |
| train_split_E1-0 | E1 | 16 | 2950 | 842 | ok |
| train_split_E1-1 | E1 | 16 | 4201 | 1200 | ok |
| train_split_E1-2 | E1 | 16 | 4101 | 1171 | ok |
| train_split_E1-3 | E1 | 16 | 3599 | 1028 | ok |
| train_split_E1-4 | E1 | 16 | 3735 | 1067 | ok |
| train_split_E1-5 | E1 | 16 | 3529 | 1008 | ok |
| train_split_E1-7 | E1 | 16 | 2345 | 670 | ok |
| train_split_E1-8 | E1 | 16 | 2421 | 691 | ok |
| train_split_E1-10 | E1 | 16 | 4117 | 1176 | ok |
| train_split_E1-11 | E1 | 16 | 2423 | 692 | ok |
| train_split_E1-14 | E1 | 16 | 2963 | 846 | ok |
| train_split_E1-15 | E1 | 16 | 3922 | 1120 | ok |
| hotel_nohints | E0 | 8 | 30514 | 8718 | ok |
| hotel_v2 | E0 | 8 | 30852 | 8814 | ok |
| hotel_v2_r2 | E0 | 8 | 30852 | 8814 | ok |
| hotel_v2_nocontext | E0 | 8 | 8018 | 2290 | ok |
| hotel_split_E0-0 | E0 | 16 | 4100 | 1171 | ok |
| hotel_split_E0-1 | E0 | 16 | 4544 | 1298 | ok |
| hotel_split_E0-4 | E0 | 16 | 4279 | 1222 | ok |
| hotel_split_E0-5 | E0 | 16 | 4210 | 1202 | ok |
| hotel_split_E0-6 | E0 | 16 | 4205 | 1201 | ok |
| hotel_split_E0-8 | E0 | 16 | 4032 | 1152 | ok |
| hotel_split_E0-11 | E0 | 16 | 3218 | 919 | ok |
| hotel_split_E0-12 | E0 | 16 | 3259 | 931 | ok |
| hotel_split_E0-14 | E0 | 16 | 2663 | 760 | ok |
| restaurant_nohints | E2 | 8 | 48373 | 13820 | ok |
| restaurant_v2 | E2 | 8 | 48711 | 13917 | ok |
| restaurant_v2_r2 | E2 | 8 | 48711 | 13917 | ok |
| restaurant_v2_nocontext | E2 | 8 | 11484 | 3281 | ok |
| restaurant_split_E2-0 | E2 | 16 | 3965 | 1132 | ok |
| restaurant_split_E2-7 | E2 | 16 | 4150 | 1185 | ok |
| restaurant_split_E2-9 | E2 | 16 | 3149 | 899 | ok |
| restaurant_split_E2-10 | E2 | 16 | 4335 | 1238 | ok |
| restaurant_split_E2-11 | E2 | 16 | 4443 | 1269 | ok |
| restaurant_split_E2-12 | E2 | 16 | 4257 | 1216 | ok |
| restaurant_split_E2-14 | E2 | 16 | 4095 | 1170 | ok |
| restaurant_split_E2-15 | E2 | 16 | 3703 | 1058 | ok |
| restaurant_split_E2-17 | E2 | 16 | 4415 | 1261 | ok |
| restaurant_split_E2-19 | E2 | 16 | 2685 | 767 | ok |
